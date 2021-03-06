#!/usr/bin/python
import sys
sys.path.insert(0,'..')
from cadnano import app
from model.virtualhelix import VirtualHelix
from model.enum import StrandType
from code import interact

print "vh = VirtualHelix(numBases=8, idnum=0)"
vh = VirtualHelix(numBases=8, idnum=0)
print repr(repr(vh)) + "\n\n"

print "vh.connectStrand(StrandType.Scaffold,2,6)"
print "vh.connectStrand(StrandType.Staple,0,7)"
vh.connectStrand(StrandType.Scaffold,2,6)
vh.connectStrand(StrandType.Staple,0,7)
print repr(repr(vh)) + "\n\n"

print "vh.clearStrand(StrandType.Scaffold, 3.5, 4.5)"
print "vh.clearStrand(StrandType.Staple, 2.5, 5.5)"
vh.clearStrand(StrandType.Scaffold, 3.5, 4.5)
vh.clearStrand(StrandType.Staple, 2.5, 5.5)
print repr(repr(vh))
print "vh.undoStack().undo()"
vh.undoStack().undo()
print repr(repr(vh))
print "vh.clearStrand(StrandType.Staple, 3, 5)"
vh.clearStrand(StrandType.Staple, 3, 5)
print repr(repr(vh)) + "\n\n"

print "vh1 = VirtualHelix(numBases=5, idnum=1)"
print "vh1.connectStrand(StrandType.Staple, 0, 4)"
vh1 = VirtualHelix(numBases=5, idnum=1)
vh1.connectStrand(StrandType.Staple, 0, 4)
print repr(repr(vh))
print repr(repr(vh1)) + "\n\n"

print "vh.installXoverFrom3To5(StrandType.Staple, 2, vh1, 2)"
vh.installXoverFrom3To5(StrandType.Staple, 2, vh1, 2)
print repr(repr(vh))
print repr(repr(vh1))
# interact(local=locals())


print ""
print ""
print "="*10 + 'Now It\'s Undo Time!' + "="*10
print ""
print ""


# Normally a VirtualHelix gets its undo stack from
# its parent part, which gets it from the parent document.
# However, vh and vh1 are orphaned VirtualHelices and so
# they spawn their own separate undo stacks. We must therefore
# be careful to invoke them in the opposite order to which they
# had commands pushed, whereas normally we could just
# document.undo() again and again.
print "vh.undoStack().undo()"
vh.undoStack().undo()
print repr(repr(vh))
print repr(repr(vh1)) + "\n\n"

print "vh1.undoStack().undo()"
vh1.undoStack().undo()
print repr(repr(vh))
print repr(repr(vh1)) + "\n\n"

print "vh.undoStack().undo()"
vh.undoStack().undo()
print repr(repr(vh)) + "\n\n"

print "vh.undoStack().undo()"
vh.undoStack().undo()
print repr(repr(vh)) + "\n\n"

print "vh.undoStack().undo()"
vh.undoStack().undo()
print repr(repr(vh)) + "\n\n"

print "vh.undoStack().undo()"
vh.undoStack().undo()
print repr(repr(vh)) + "\n\n"



print "="*10 + 'Observe the undo stack not losing information' + "="*10
print ""
print ""


print "vh.connectStrand(StrandType.Scaffold, 2, 4)"
print "vh.connectStrand(StrandType.Scaffold, 0, 7)"
print "vh.undoStack().undo()"
vh.connectStrand(StrandType.Scaffold, 2, 4)
vh.connectStrand(StrandType.Scaffold, 0, 7)
vh.undoStack().undo()
print repr(repr(vh)) + "\n\n"
