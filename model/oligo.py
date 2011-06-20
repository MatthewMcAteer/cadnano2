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
oligo.py
Created by Nick Conway on 2011-01-26.
"""

class Oligo(object):
    """Stores color and sequence information"""
    def __init__(self, part):
        """"""
        self._part = part
        self._color = self._part.palette().color[0]
        self._part.palette().shuffle()
        
    def color(self):
        """
        """
        return self._color
        
    def setColor(self,color):
        """
        """
        self._color = color
        
# end class


class OligoBank(object):
    """Stores color and sequence information"""
    def __init__(self, part):
        self._oligos = {}
        self._part = part
        
    def __getitem__(self, i):
        """
        """
        c = self._oligos.get(i, None)
        if c == None:
            c = self._oligos[i] = Oligo(part)
        # end if
        return c
        
    def shuffle(self):
        self._oligos.clear()
        
# end class