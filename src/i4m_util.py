import maya.api.OpenMayaAnim as oma

class AnimCacheHolder():
    
    animCache = 0
    
    @staticmethod
    def setAnimCache(cache: oma.MAnimCurveChange):
        
        AnimCacheHolder.animCache = cache