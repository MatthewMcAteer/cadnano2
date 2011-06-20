# The MIT License
#
# Copyright (c) 2011 Wyss Institute at Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# http://www.opensource.org/licenses/mit-license.php

"""
virtualhelix.py
Created by Nick Conway on 2011-06-17.
"""
import sys
from exceptions import AttributeError, IndexError
from itertools import product
from .enum import LatticeType, Parity, StrandType, BreakType
from .enum import Crossovers, EndType
from PyQt4.QtCore import pyqtSignal, QObject, QTimer
from PyQt4.QtGui import QUndoCommand, QUndoStack, QColor
from .base import Base
from .oligo import Oligo, OligoBank
from util import *
from cadnano import app
from random import Random
import re


class VirtualHelix(QObject):
    """Stores staple and scaffold routing information."""
    prohibitSingleBaseCrossovers = True
    
    basesModified = pyqtSignal()
    dimensionsModified = pyqtSignal()

    def __init__(self, numBases=21, idnum=0, incompleteArchivedDict=None):
        super(VirtualHelix, self).__init__()
        # Row, col are always owned by the parent part;
        # they cannot be specified in a meaningful way
        # for a detached helix (part==None). Only dnaparts
        # get to modify these.
        self._row = None
        self._col = None
        # If self._part exists, it owns self._number
        # in that only it may modify it through the
        # private interface. The public interface for
        # setNumber just routes the call to the parent
        # dnapart if one is present. If self._part == None
        # the vhelix owns self._number and may modify it.
        self._number = idnum
        # Attaching to a part via setPart gives the part ownership of
        # the above three properties (it asks part to set them,
        # self should no longer modify _row, _col, or _number)
        self._part = None
        # The base arrays are owned entirely by virtualhelix
        self._stapleBases = {}
        self._scaffoldBases = {}
        # As is the floatingXoverBase if there is one
        self.floatingXoverBase = None
        
        """
        This is for loops and skips.
        a dictionary for loops and skips is added
        for loops and skips
        of the form { index: count }
        + count indicates loop 
        - count indicates skip
        """
        self._stapleLoops = {}
        self._scaffoldLoops = {}
        
        # setSandboxed(True) gives self a private undo stack
        # in order to insulate undo/redo on the receiver
        # from global undo/redo (so that if a haywire tool
        # using undo() and redo() to give a live preview of
        # tho tool's effect calls undo() a million times it
        # doesn't make the document disappear). setSandboxed(False)
        # then clears _privateUndoStack at which point self
        # goes back to using the part / document undo stack.
        self._privateUndoStack = None
        self._sandboxed = False
        # numBases is a simulated property that corresponds to the
        # length of _stapleBases and _scaffoldBases
        if incompleteArchivedDict:
            numBases = len(re.split('\s+',\
                                    incompleteArchivedDict['staple'])) - 1
        self.setNumBases(numBases, notUndoable=True)
        
        # During a single UndoCommand, many basesModified signals can be generated.
        # basesModifiedVHs stores a set of VH that will setHasBeenModified
        # upon a call to emitBasesModifiedIfNeeded.
        self.basesModifiedVHs = set()
        
        def part(self):
            return self._part

    def _setPart(self, newPart, coords, num):
        """Should only be called by dnapart. Use dnapart's
        addVirtualHelixAt to add a virtualhelix to a dnapart."""
        (self._row, self._col) = coords
        if self._part and self._part.getVirtualHelix(coords):
            self._part.addVirtualHelixAt(coords, None)
        self._number = num
        self._part = newPart
        self.setNumBases(newPart.numBases(), notUndoable=True)
        # Command line convenience for -i mode
        if app().v != None:
            app().v[self.number()] = self

    def palette(self):
        return self.part().palette()

    def numBases(self):
        return len(self._stapleBases)
        
    def setNumBases(self, newNumBases, notUndoable=False):
        newNumBases = int(newNumBases)
        assert(newNumBases >= 0)
        oldNB = self.numBases()
        if self.part():
            assert(self.part().numBases() == newNumBases)
        if newNumBases == oldNB:
            return
        if newNumBases > oldNB:
            c = self.SetNumBasesCommand(self, newNumBases)
            if notUndoable:
                c.redo()
            else:
                self.undoStack().push(c)
        if newNumBases < oldNB:
            c0 = self.ClearStrandCommand(self, StrandType.Scaffold,\
                                         newNumBases, oldNB)
            c1 = self.ClearStrandCommand(self, StrandType.Staple,\
                                         newNumBases, oldNB)
            c2 = self.SetNumBasesCommand(self, newNumBases)
            if notUndoable:
                c0.redo()
                c1.redo()
                c2.redo()
            else:
                u = self.undoStack()
                u.beginMacro("Changing the number of bases")
                u.push(c0)
                u.push(c1)
                u.push(c2)
                u.endMacro()
    # end def
        
    def number(self):
        """return VirtualHelix number"""
        return self._number
    # end def
    
    def setNumber(self, newNumber):
        if self.part():
            self.part().renumberVirtualHelix(self, newNumber)
        else:
            self._number = newNumber
    # end def
    
    def selected(self):
        return self in self.part().selection()
    # end def
    
    # dnapart owns its selection, so look there for related
    # event emission
    def setSelected(self, willBeSelected):
        currentSelection = self.part().selection()
        selected = self in currentSelection
        needsSelecting = willBeSelected and not selected
        needsDeselectig = not willBeSelected and selected
        if needsSelecting:
            # We're modifying part()'s selection
            # object beneath it. I won't tell it
            # if you don't. Safety would demand
            # selection() returns a copy.
            currentSelection.append(self)
        elif needsDeselectig:
            currentSelection.remove(self)
        self.part().setSelection(currentSelection)
    # end def

    def coord(self):
        return (self._row, self._col)
    # end def

    def evenParity(self):
        """
        returns True or False
        """
        if self._part:
            return self._part.virtualHelixParityEven(self)
        else:
            return self._number % 2 == 0
    # end def
    
    def directionOfStrandIs5to3(self, strandtype):
        """
        method to determine 5' to 3' or 3' to 5'
        """
        if self.evenParity() and strandtype == StrandType.Scaffold:
            return True
        elif not self.evenParity() and strandtype == StrandType.Staple:
            return True
        else:
            return False
    # end def

    def row(self):
        """return VirtualHelix helical-axis row"""
        return self._row
    # end def

    def col(self):
        """return VirtualHelix helical-axis column"""
        return self._col
    # end def
    
    def _strand(self, strandType):
        """The returned strand should be considered privately
        mutable"""
        if strandType == StrandType.Scaffold:
            return self._scaffoldBases
        elif strandType == StrandType.Staple:
            return self._stapleBases
        else:
            raise IndexError("%s is not Scaffold=%s or Staple=%s"%(strandType, StrandType.Scaffold, StrandType.Staple))
            
    def _loop(self, strandType):
        """The returned loop list should be considered privately
        mutable"""
        if strandType == StrandType.Scaffold:
            return self._scaffoldLoops
        elif strandType == StrandType.Staple:
            return self._stapleLoops
        else:
            raise IndexError("%s is not Scaffold=%s or Staple=%s"%(strandType, StrandType.Scaffold, StrandType.Staple))
    # end def
    
    ############################## Access to Bases ###########################
    def hasBaseAt(self, strandType, index):
        """Returns true if a base is present at index on strand strandtype."""
        base = self._baseAt(strandType, index)
        if not base:
            return False
        else:
            return not base.isEmpty()

    def validatedBase(self, strandType, index, raiseOnErr=False):
        """Makes sure the basespec (strandType,index) is valid
        and raises or returns (None, None) according to raiseOnErr if
        it isn't valid"""
        if strandType != StrandType.Scaffold and \
                                            strandType != StrandType.Staple:
            if raiseOnErr:
                raise IndexError("Base (strand:%s index:%i) Not Valid" % \
                                                        (strandType, index))
            return (None, None)
        index = int(index)
        if index < 0 or index > self.numBases() - 1:
            if raiseOnErr:
                raise IndexError("Base (strand:%s index:%i) Not Valid" % \
                                                        (strandType, index))
            return (None, None)
        return (strandType, index)

    def _baseAt(self, strandType, index, raiseOnErr=False):
        strandType, index = \
                self.validatedBase(strandType, index, raiseOnErr=raiseOnErr)
        if strandType == None:
            return None
        else:
            # return 5' BaseNode object rather than the 
            # nonexistent base if it exists
            last_key_index = 0
            last_basenode = None
            returnval = None
            for key_index, basenode in self._strand(strandType).iteritems():
                if last_basenode != None:
                    end_0 = last_basenode.isEnd()
                    end_1 = basenode.isEnd()
                    
                    # first test to see if it is a 3' to 5' skip break if
                    # even parity 5' to 3' skip for odd parity
                    if ( self.evenParity() and (end_0 == 3 and end_1 == 5)) or \
                        ( not self.evenParity() and (end_0 == 5 and end_1 == 3)):
                            last_basenode = baseNode 
                            last_key_index = key_index
                    # end if
                    else: 
                        if last_key_index < index and index < key_index:
                            returnval = last_basenode
                            break
                        else: 
                            last_basenode = baseNode 
                            last_key_index = key_index 
                    # Now check                  
        return returnval
    # end def
    