import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
from PySide2 import QtCore, QtWidgets, QtGui

class TreeItem(QtGui.QStandardItem):
    
    def __init__(self, text, item):
        
        super().__init__()
        
        self.setEditable(False)
        self.setText(text)
        self.setData(item)
        self.setDropEnabled(False)
        
        self.font = QtGui.QFont("Noto Sans", 12, 600, False)
        self.setFont(self.font)
        
class TreeModel(QtGui.QStandardItemModel):
    
    def __init__(self):
        
        super().__init__()
        
        self.oldList = []
        self.newList = []
        self.root = self.invisibleRootItem()

class Window(QtWidgets.QWidget):

    def __init__(self):
        
        super().__init__()

        self.setWindowFlags(QtGui.Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Inbetweener")
        self.resize(500, 500)
        
        self.font = QtGui.QFont("Noto Sans", 12, 300, False)
        self.setFont(self.font)
        
        self.selection = None
        self.selCbId = om.MEventMessage.addEventCallback("SelectionChanged", self.updateList)

        self.windowLayout = QtWidgets.QVBoxLayout(self)

        self.topLayout = QtWidgets.QHBoxLayout(self)
        self.refreshBtn = QtWidgets.QPushButton("Refresh", self)
        self.refreshBtn.clicked.connect(self.updateList)
        self.topLayout.addWidget(self.refreshBtn)
        
        self.topLayout.addStretch()

        self.selTree = QtWidgets.QTreeView()
        self.selTree.setMaximumHeight(300)
        self.selTree.setHeaderHidden(True)
        
        self.selTreeModel = TreeModel()
        self.selTreeSel = QtCore.QItemSelectionModel(self.selTreeModel)
        
        self.updateList()
                
        self.selTree.setModel(self.selTreeModel)
        self.selTree.setSelectionModel(self.selTreeSel)
        self.selTree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.onSliderChange)
        
        self.windowLayout.addLayout(self.topLayout)
        self.windowLayout.addWidget(self.selTree)
        self.windowLayout.addWidget(self.slider)
        self.windowLayout.addStretch()
        
    def closeEvent(self, event):
        
        om.MMessage.removeCallback(self.selCbId)
        event.accept()
    
    def initSelTree(self):
        
        self.selTreeRoot = self.selTreeModel.invisibleRootItem()
        self.selection = om.MGlobal.getActiveSelectionList()
        selectionIt = om.MItSelectionList(self.selection)
        for sel in selectionIt:
            
            node = sel.getDependNode()
            
            if oma.MAnimUtil.isAnimated(node):
                
                animObj = TreeItem(node, str(sel.getDagPath()), True)
                self.selTreeRoot.appendRow(animObj)
                plugs = oma.MAnimUtil.findAnimatedPlugs(node)
                
                for plug in plugs:
                    
                    animPlug = TreeItem(plug, str(plug.partialName(useLongNames=True)), True)
                    animObj.appendRow(animPlug)          
    
    def updateList(self, *args, **kwargs):
        
        #Store old list
        self.selTreeModel.oldList = self.selTreeModel.newList[:]
        #Get new list
        selection = om.MGlobal.getActiveSelectionList()
            
        #Find diff
        addList = []
        removeList = []
        
        for obj in om.MItSelectionList(selection):
            
            node = obj.getDependNode()
            
            if oma.MAnimUtil.isAnimated(node):

                nodeFn = om.MFnDependencyNode(node)
                contains = False
            
                for item in self.selTreeModel.oldList:
                
                    if item.data() == node:
                    
                        contains = True
                        break
                
                if not contains:
                
                    animObj = TreeItem(str(nodeFn.name()), node)
                    
                    plugs = oma.MAnimUtil.findAnimatedPlugs(node)
                    
                    for plug in plugs:
                        
                        animObj.appendRow(TreeItem(plug.partialName(useLongNames=True), plug))

                    addList.append(animObj)
            
        for item in self.selTreeModel.oldList:
            
            contains = False
            
            for obj in om.MItSelectionList(selection):
                
                if obj.getDependNode() == item.data():
                    
                    contains = True
                    break
                
            if not contains:
                
                removeList.append(item)

        #Delete removed      
        for item in removeList:
            
            self.selTreeModel.root.removeRow(self.selTreeModel.indexFromItem(item).row())
            self.selTreeModel.newList.remove(item)

        #Add new
        for item in addList:
            
            self.selTreeModel.root.appendRow(item)
            self.selTreeModel.newList.append(item)
        

    def onSliderChange(self):
        
        self.func(self.slider.value())   
        
    def func(self, val):
    
        time = oma.MAnimControl.currentTime() #current playhead time
        
        for index in self.selTreeSel.selectedIndexes():
                
            item = self.selTreeModel.itemFromIndex(index)
            plug = item.data()
            #Operate on the curve which effects the plug
            curve = oma.MAnimUtil.findAnimation(plug)
            curveFn = oma.MFnAnimCurve(curve[0])
                
            start = 0
            end = 0
            index = curveFn.findClosest(time)
            
            #Calculate which keyframe the playhead is closest to
            if curveFn.input(index) < time:
                    
                start = index
                end = index + 1
                
            elif curveFn.input(index) > time:
                
                start = index - 1
                end = index
                        
            else:
                        
                start = index - 1
                end = index + 1
                    
            #Get the value of the start and end frame
            startV = curveFn.value(start)
            endV = curveFn.value(end)
                    
            #Calculate inbetween and set resulting key
            resV = startV + (val/99) * (endV - startV)
            curveFn.addKey(time, resV)
                
    
window = Window()
window.show()