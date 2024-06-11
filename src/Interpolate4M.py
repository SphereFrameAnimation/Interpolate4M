import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
from PySide2 import QtCore, QtWidgets, QtGui

#Get maya main window
mayaApp = QtWidgets.QApplication.instance()
mainWindow = 0

for qw in mayaApp.topLevelWidgets():
    
    if(qw.objectName() == "MayaWindow"):
        
        mainWindow = qw
        break

#Custom item for tree view
class TreeItem(QtGui.QStandardItem):
    
    def __init__(self, text, item):
        
        super().__init__()
        
        self.setEditable(False)
        self.setText(text)
        self.setData(item)
        self.setDropEnabled(False)
        
        self.font = QtGui.QFont("Noto Sans", 12, 600, False)
        self.setFont(self.font)
        
#Custom TreeModel including data to simplify updating the tree on refresh
class TreeModel(QtGui.QStandardItemModel):
    
    def __init__(self):
        
        super().__init__()
        
        self.oldList = []
        self.newList = []
        self.root = self.invisibleRootItem()

#Interpolate4M window
class Window(QtWidgets.QWidget):

    def __init__(self):
        
        super().__init__(mainWindow)

        #Window setup
        self.setWindowFlags(QtGui.Qt.Window)
        self.setWindowTitle("Inbetweener")
        self.resize(500, 500)
        
        #Window font
        self.font = QtGui.QFont("Noto Sans", 12, 300, False)
        self.setFont(self.font)
        
        #Callback for updating list on selection change
        self.selCbId = om.MEventMessage.addEventCallback("SelectionChanged", self.updateList)

        #Window layout
        self.windowLayout = QtWidgets.QVBoxLayout(self)

        #Top bar buttons
        self.topLayout = QtWidgets.QHBoxLayout(self)
        self.refreshBtn = QtWidgets.QPushButton("Refresh", self)
        self.refreshBtn.clicked.connect(self.updateList)
        self.topLayout.addWidget(self.refreshBtn)
        
        self.topLayout.addStretch()

        #Selection tree for selecting objects and animatable plugs
        self.selTree = QtWidgets.QTreeView()
        self.selTree.setMaximumHeight(300)
        self.selTree.setHeaderHidden(True)
        
        self.selTreeModel = TreeModel()
        self.selTreeSel = QtCore.QItemSelectionModel(self.selTreeModel)
                
        self.selTree.setModel(self.selTreeModel)
        self.selTree.setSelectionModel(self.selTreeSel)
        self.selTree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        #Slider for setting inbetweens
        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.onSliderChange)
        
        #Add widgets and layouts to main window layout
        self.windowLayout.addLayout(self.topLayout)
        self.windowLayout.addWidget(self.selTree)
        self.windowLayout.addWidget(self.slider)
        self.windowLayout.addStretch()
        
        #Update the selection tree when window opens
        self.updateList()
        
    #Run when the window is closed to clean up the callback
    def closeEvent(self, event):
        
        om.MMessage.removeCallback(self.selCbId)
        event.accept()         
    
    #Function for updating the selection tree
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
                
                node = obj.getDependNode()
                if node == item.data() and oma.MAnimUtil.isAnimated(node):
                    
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
        

    #Run when slider's value is changed
    def onSliderChange(self):
        
        self.doInbetween(self.slider.value())   
        
    #Sets the inbetween keyframe
    def doInbetween(self, val):
    
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
            resV = startV + (val/self.slider.maximum()) * (endV - startV)
            curveFn.addKey(time, resV)

#Construct and show window
if mainWindow != 0:
    
    window = Window()
    window.show()