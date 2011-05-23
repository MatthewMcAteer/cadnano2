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
pathhelix.py
Created by Shawn on 2011-01-27.
"""

from exceptions import AttributeError, ValueError
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QLine, QRectF
from PyQt4.QtGui import QBrush
from PyQt4.QtGui import QGraphicsItem
from PyQt4.QtGui import QGraphicsSimpleTextItem
from PyQt4.QtGui import QPainter, QPainterPath
from PyQt4.QtGui import QPen, QDrag, QUndoCommand
import ui.styles as styles
from model.enum import EndType, LatticeType, StrandType, Parity
from model.virtualhelix import VirtualHelix
from handles.breakpointhandle import BreakpointHandle
from mmayacadnano.pathhelix3d import PathHelix3D  # For Campbell
from weakref import ref


class PathHelix(QGraphicsItem):
    """
    PathHelix is the primary "view" of the VirtualHelix data.
    It manages the ui interactions from the user, such as
    dragging breakpoints or crossovers addition/removal,
    and updates the data model accordingly.

    parent should be set to...
    """
    minorGridPen = QPen(styles.minorgridstroke, 1)
    majorGridPen = QPen(styles.majorgridstroke, 2)
    scafPen = QPen(styles.scafstroke, 0)
    nobrush = QBrush(Qt.NoBrush)
    baseWidth = styles.PATH_BASE_WIDTH

    def __init__(self, vhelix, position, parent):
        super(PathHelix, self).__init__(parent)
        self.setAcceptHoverEvents(True)  # for pathtools
        self._vhelix = vhelix
        self._parity = self._vhelix.parity()
        self._scafBreakpointHandles = []
        self._stapBreakpointHandles = []
        self._scafXoverHandles = []
        self._stapXoverHandles = []
        self.scafLines = []
        self.setPos(position)
        self.minorGridPainterPath = self.getMinorGridPainterPath()
        self.majorGridPainterPath = self.getMajorGridPainterPath()
        self.setParentItem(parent)
        # for precrossover
        if parent.crossSectionType == LatticeType.Honeycomb:
            self.step = 21
        elif parent.crossSectionType == LatticeType.Square:
            self.step = 32
        self.pathController = parent.pathController  # assumes parent is phg
        self.setZValue(styles.ZPATHHELIX)
        self.rect = QRectF()
        self.updateRect()
        # Here's where cadnano gets the reference to mMaya's 3D equivalent
        # of the PathHelix (while passing a handy reference to itself)
        self.PathHelix3D = PathHelix3D(self)  # For Campbell
    # end def

    def vhelix(self):
        return self._vhelix

    def number(self):
        return self._vhelix.number()

    def row(self):
        return self._vhelix.row()

    def col(self):
        return self._vhelix.col()

    def parity(self):
        return self._parity

    def updateRect(self):
        """Sets rect width to reflect number of bases in vhelix. Sets
        rect height to the width of two bases (one for scaffold and
        one for staple)"""
        canvasSize = self._vhelix.part().getNumBases()
        self.rect.setWidth(self.baseWidth * canvasSize)
        self.rect.setHeight(2 * self.baseWidth)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        painter.setBrush(self.nobrush)
        painter.setPen(self.minorGridPen)
        painter.drawPath(self.minorGridPainterPath)  # Minor grid lines
        painter.setPen(self.majorGridPen)
        painter.drawPath(self.majorGridPainterPath)  # Major grid lines
        painter.setPen(self.scafPen)
        painter.drawLines(self.scafLines)  # Scaffold lines
    # end def

    def getMinorGridPainterPath(self):
        """
        Returns a QPainterPath object for the minor grid lines.
        The path also includes a border outline and a midline for
        dividing scaffold and staple bases.
        """
        path = QPainterPath()
        canvasSize = self._vhelix.part().getNumBases()
        # border
        path.addRect(0, 0, self.baseWidth * canvasSize, 2 * self.baseWidth)
        # minor tick marks
        for i in range(canvasSize):
            if (i % 7 != 0):
                x = round(self.baseWidth*i) + .5
                path.moveTo(x, 0)
                path.lineTo(x, 2 * self.baseWidth)
        # staple-scaffold divider
        path.moveTo(0, self.baseWidth)
        path.lineTo(self.baseWidth * canvasSize, self.baseWidth)
        return path

    def getMajorGridPainterPath(self):
        """
        Returns a QPainterPath object for the major grid lines.
        This is separated from the minor grid lines so different
        pens can be used for each.
        """
        path = QPainterPath()
        canvasSize = self._vhelix.part().getNumBases()
        # major tick marks
        for i in range(0, canvasSize + 1, 7):
            x = round(self.baseWidth*i) + .5
            path.moveTo(x, .5)
            path.lineTo(x, 2 * self.baseWidth - .5)
        return path
    # end def

    def hoverEnterEvent(self, event):
        if self.pathController.toolUse == True:
            self.pathController.toolHoverEnter(self,event)
        else:
            QGraphicsItem.hoverEnterEvent(self,event)
    # end def
    
    def hoverLeaveEvent(self, event):
        if self.pathController.toolUse == True:
            self.pathController.toolHoverLeave(self,event)
        else:
            QGraphicsItem.hoverLeaveEvent(self,event)
    # end def
    
    def hoverMoveEvent(self, event):
        if self.pathController.toolUse == True:
            self.pathController.toolHoverMove(self,event)
        else:
            QGraphicsItem.hoverMoveEvent(self,event)
    # end def

    def mousePressEvent(self, event):
        """Activate this item as the current helix"""
        if self.pathController.toolUse == True:
            self.pathController.toolPress(self,event)
        eventIndex = int(event.pos().x() / styles.PATH_BASE_WIDTH)
        self.updateAsActiveHelix(eventIndex)
    # end def

    def hidePreXoverHandles(self):
        pass
    # end def

    def addBreakpointHandle(self, bh, strandType):
        """addScaffoldBreakHandle gets called by PathHelixGroup
        when the handles are changed (e.g. by sliceHelixClickedSlot
        or when a crossover is added)."""
        if strandType == StrandType.Scaffold:
            self._scafBreakpointHandles.append(bh)
        elif strandType == StrandType.StrandType:
            self._stapBreakpointHandles.append(bh)
        else:
            raise AttributeError("strandType not recognized.")
    # end def

    def addXoverHandle(self, xh, strandType):
        """addXoverHandle gets called by PathHelixGroup
        when the handles are changed (e.g. by sliceHelixClickedSlot
        or when a crossover is added)."""
        if strandType == StrandType.Scaffold:
            self._scafXoverHandles.append(xh)
        elif strandType == StrandType.StrandType:
            self._stapXoverHandles.append(xh)
        else:
            raise AttributeError("strandType not recognized.")
    # end def

    def removeXoverHandle(self, xh, strandType):
        """addXoverHandle gets called by PathHelixGroup
        when the handles are changed (e.g. by sliceHelixClickedSlot
        or when a crossover is added)."""
        if strandType == StrandType.Scaffold:
            self._scafXoverHandles.remove(xh)
        elif strandType == StrandType.StrandType:
            self._stapXoverHandles.remove(xh)
        else:
            raise AttributeError("strandType not recognized.")
    # end def

    def updateAsActiveHelix(self, index):
        if self.parentItem().activeHelix != None:  # deactivate old
            self.parentItem().activeHelix.hidePreXoverHandles()
        # end if
        self.parentItem().activeHelix = self  # activate new
        self._vhelix.updatePreCrossoverPositions(index)
        self.parentItem().notifyPreCrossoverGroupAfterUpdate(self._vhelix)
        self.update(self.boundingRect())
    # end def

    def refreshBreakpoints(self, strandType):
        """docstring for refreshBreakpoints"""
        if strandType == StrandType.Scaffold:
            handles = self._scafBreakpointHandles
            ends5p = self.vhelix().getScaffold5PrimeEnds()
            ends3p = self.vhelix().getScaffold3PrimeEnds()
            for bh in self._scafBreakpointHandles:
                bh.destroy()
            self._scafBreakpointHandles = []
        # end if
        elif strandType == StrandType.Staple:
            handles = self._stapBreakpointHandles
            ends5p = self.vhelix().getStaple5PrimeEnds()
            ends3p = self.vhelix().getStaple3PrimeEnds()
            for bh in self._stapBreakpointHandles:
                bh.destroy()
            self._stapBreakpointHandles = []
        # end elif
        else:
            raise AttributeError("StrandType not recognized")
        # end else
        for baseIndex in ends5p:
            bh = BreakpointHandle(self.vhelix(), EndType.FivePrime,\
                                  strandType, baseIndex, parent=self)
            self.addBreakpointHandle(bh, strandType)
        # end for
        for baseIndex in ends3p:
            bh = BreakpointHandle(self.vhelix(), EndType.ThreePrime,\
                                  strandType, baseIndex, parent=self)
            self.addBreakpointHandle(bh, strandType)
        # end for
        self.updateDragBounds(strandType)
    # end def

    def updateDragBounds(self, strandType):
        """Sorts a list of all breakpoint and crossover handles, and then
        iterates over those handles and sets dragging boundaries for
        breakpoint handles."""
        if strandType == StrandType.Scaffold:
            handles = sorted(self._scafBreakpointHandles +\
                             self._scafXoverHandles,\
                             key=lambda handle: handle.baseIndex)
        elif strandType == StrandType.Staple:
            handles = sorted(self._stapBreakpointHandles +\
                             self._stapXoverHandles,\
                             key=lambda handle: handle.baseIndex)
        else:
            raise AttributeError("StrandType not recognized")
        count = len(handles)
        if count == 0:
            return
        maxIndex = self._vhelix.part().getNumBases() - 1
        if count == 1:
            handles[0].setDragBounds(0, maxIndex)
        else:
            handles[0].setDragBounds(0, handles[1].baseIndex - 1)
            for i in range(len(handles[1:-1])):
                handles[i].setDragBounds(handles[i - 1].baseIndex + 1,\
                                         handles[i + 1].baseIndex - 1)
            handles[count - 1].setDragBounds(\
                               handles[count - 2].baseIndex + 1, maxIndex)
    # end def

    def getYoffset(self, strandType):
        """
        This function returns the appropriate Y offset according to the
        rule that even-parity staples and odd-parity scaffolds run in the
        negative-z direction and are drawn in the lower half of the
        path helix grid.
        """
        if (self._parity == Parity.Even and strandType == StrandType.Staple):
            return self.baseWidth + (self.baseWidth >> 1)
        if (self._parity == Parity.Odd and strandType == StrandType.Scaffold):
            return self.baseWidth + (self.baseWidth >> 1)
        else:
            return self.baseWidth >> 1

    def redrawLines(self, strandType):
        """Draw horizontal lines where non-breakpoint, non-crossover strand
           is present"""
        endpoints = []
        if strandType == StrandType.Scaffold:
            handles = sorted(self._scafBreakpointHandles +\
                             self._scafXoverHandles,\
                             key=lambda handle: handle.baseIndex)
        elif strandType == StrandType.Staple:
            handles = sorted(self._stapBreakpointHandles +\
                             self._stapXoverHandles,\
                             key=lambda handle: handle.baseIndex)
        else:
            raise AttributeError
        count = len(handles)
        if count == 0:
            return
        if count % 2 == 1:
            print ' '.join(["%d" % h.baseIndex for h in handles])
            raise ValueError("%d handles" % count)  # should always be even
        else:
            for i in range(0, len(handles), 2):
                # collect endpoints
                endpoints.append([handles[i].baseIndex,\
                                  handles[i + 1].baseIndex])

        self.scafLines = []  # get rid of old points
        y = self.getYoffset(strandType)  # determine y offset
        for [startIndex, endIndex] in endpoints:
            x1 = (startIndex * self.baseWidth) + (self.baseWidth >> 1)
            x2 = (endIndex * self.baseWidth) + (self.baseWidth >> 1)
            self.scafLines.append(QLine(x1, y, x2, y))  # create QLine list
        # end for
        self.update(self.rect)
        self.PathHelix3D.updateDNA(strandType, endpoints)

    def strandIsTop(self, strandType):
        return self.evenParity() and strandType==StrandType.Scaffold\
           or not self.evenParity() and strandType == StrandType.Staple
    
    def baseLocation(self, strandType, baseIdx, center=False):
        """Returns the coordinates of the upper left corner of the base
        referenced by strandType and baseIdx. If center=True, returns the
        center of the base instead of the upper left corner."""
        if self.strandIsTop(strandType):
            y = 0
        else:
            y = self.baseWidth
        x = baseIdx*self.baseWidth
        if center:
            y += self.baseWidth/2
            x += self.baseWidth/2
        return (x,y)

# end class
