import maya.api.OpenMaya as om
from src.i4m_cmd import InterpolateCmd
from src.i4m_util import AnimCacheHolder

def maya_useNewAPI():

    pass

def initializePlugin(plugin):
    
    pluginFn = om.MFnPlugin(plugin)
    try:
        
        pluginFn.registerCommand(InterpolateCmd.kPluginCmdName, InterpolateCmd.creator)
        AnimCacheHolder.setAnimCache(0)
        
        
    except:
        
        om.MGlobal.displayError("Failed to load Interpolate4M")
        raise
    
def uninitializePlugin(plugin):
    
    pluginFn = om.MFnPlugin(plugin)
    try:
        
        pluginFn.deregisterCommand(InterpolateCmd.kPluginCmdName)
        
    except:
        
        om.MGlobal.displayError("Failed to unload Interpolate4M")
        raise