import maya.api.OpenMaya as om
from src.i4m_util import AnimCacheHolder

class InterpolateCmd(om.MPxCommand):
    
    kPluginCmdName = "i4m_cmd"
    
    @staticmethod
    def creator():
        
        return InterpolateCmd()
    
    def __init__(self):
        
        om.MPxCommand.__init__(self)
        
    def isUndoable(self):
        
        return True
    
    def doIt(self, args):
        
        self.animCache = AnimCacheHolder.animCache
    
    def redoIt(self):
        
        self.animCache.redoIt()
        
    def undoIt(self):
        
        self.animCache.undoIt()