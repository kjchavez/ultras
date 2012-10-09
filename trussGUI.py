# Truss Solver GUI
from helperfunctions import *
from truss import *
from tkinter import *
from constants import *
from designspace import DesignSpace
from graphics import *
import pickle

class App:
    def __init__(self, master):
        """
        This is the highest class in the hierarchy. It maintains a reference to the
        main data structure that this GUI is manipulating. All other classes keep a reference to
        their parent and can access the Truss via this class.
        """
        self.master = master
        
        # Instantiate data structure
        self.truss = Truss()

        # Graphics
        self.frame = Frame(master,width=WINDOW_WIDTH,height=WINDOW_HEIGHT)
        self.designSpace = DesignSpace(self)
        #self.infoPane = InfoPane(self)
        self.toolbar = Toolbar(self)

        # Menu
        TopMenu(self)

        # Display
        self.toolbar.frame.grid(row=0,column=0)
        self.frame.pack()

        # Event Binding
        root.bind("<Control-g>",self.designSpace.toggleSnap)

        # Current filename
        self.fileName = None
        
    def addMember(self,joint1,joint2):
        self.truss.addMember(joint1,joint2)

    def addJoint(self,x,y):
        pass

    def clearTruss(self):
        self.truss = Truss()
        self.designSpace.clear()

    def reanalyzeTruss(self):
        self.truss.setUnsolved()
        self.updateTrussSolution()
        self.solveTruss()

    def solveTruss(self):
        if not self.truss.isSolved and self.truss.isDeterminate():
            self.truss.analyze()
            self.updateTrussSolution()

    def updateTrussSolution(self):
            for member in self.truss.getMembers():
                member.graphic.update()

##            for joint in self.truss.getJoints():
##                joint.graphic.update()
            if self.truss.fixedJoint:
                self.truss.fixedJoint.graphic.update()
                
            if self.truss.rollerJoint:
                self.truss.rollerJoint.graphic.update()

    def saveas(self):
        fileName = filedialog.asksaveasfilename(defaultextension='.txt',filetypes=[('Text Files', '.txt')])
        #print(fileName)
        if fileName:
            #print("yes filename")
            self.save(fileName)
            self.fileName = fileName
        # Since the current truss has links to TK classes that cannot be pickled, we need a data structure that preserves the essence of the truss but is simpler

    def save(self,fileName=None):
        if fileName:
            self.truss.save(fileName)
            self.designSpace.statusBar.setTempText("  Saved.")  # Two spaces before saved are INTENTIONAL
            self.master.after(1000,self.designSpace.statusBar.update)
        elif self.fileName:
            self.truss.save(self.fileName)
            self.designSpace.statusBar.setTempText("  Saved.") 
            self.master.after(1000,self.designSpace.statusBar.update)
        else:
            self.saveas()


    def saveEventHandle(self,event):
        self.save()

    def openEventHandle(self,event):
        self.load()

    def load(self):
        fileName = filedialog.askopenfilename(defaultextension='.txt',filetypes=[('Text Files','.txt')])
        if fileName:
            print(fileName)
            self.fileName = fileName
            loadFile = open(fileName,mode='rb')
            abstractTruss = pickle.load(loadFile)
            loadFile.close()
            self.clearTruss()
            
            generatedJoints = {}
            for jointID in abstractTruss['nodes']:
                x,y = abstractTruss['nodes'][jointID]
                newJoint = self.truss.addJoint(x,y)
                newJoint.graphic = JointGraphic(self.designSpace.canvas,newJoint)
                newJoint.loadLine = None
                generatedJoints[jointID] = newJoint

            print(generatedJoints)

            for memberID in abstractTruss['edges']:
                startJointID,endJointID = memberID
                startJoint = generatedJoints[startJointID]
                endJoint = generatedJoints[endJointID]
                newMember = self.truss.addMember(startJoint,endJoint)
                newMember.graphic = MemberGraphic(self.designSpace.canvas,newMember)

            if abstractTruss['fixed joint']:
                self.designSpace.currentJoint = generatedJoints[abstractTruss['fixed joint']]
                self.designSpace.selectFixedJoint()
                
            if abstractTruss['roller joint']:
                self.designSpace.currentJoint = generatedJoints[abstractTruss['roller joint']]
                self.designSpace.selectRollerJoint()

            for jointID in abstractTruss['loads']:
                joint = generatedJoints[jointID]
                fx, fy = abstractTruss['loads'][jointID]
                jx, jy = joint.getLoc()
                cx, cy = rectifyPos((jx,jy),self.designSpace.canvas)
                joint.loadLine = LoadGraphic(self.designSpace.canvas,\
                                             joint,\
                                             cx+fx/LOAD_SCALE_FACTOR,\
                                             cy-fy/LOAD_SCALE_FACTOR)
                joint.loadLine.makeInactive()
                self.truss.setExternalLoad(joint,fx,fy)

            
            self.solveTruss()
            for joint in self.truss.getJoints():
                joint.graphic.update()

            self.designSpace.mjCount.setText(" ("+str(len(self.truss.getJoints()))+" Joints / "+str(len(self.truss.getMembers()))+" Members)")


class Toolbar():
    def __init__(self,master):
        # Keep reference to parent class, NOT widget
        self.master = master
        
        self.frame = Frame(master.frame,bg=TOOLBAR_FRAME_COLOR,width=WINDOW_WIDTH,height=TOOLBAR_FRAME_HEIGHT)

        # Buttons, rudimentary appearance for now...

        # Transitions the DesignSpace into its add joints and members mode. This is default.
        addJointMemberButton = Button(self.frame,text="Create",width=TOOLBAR_BUTTON_WIDTH,command=self.master.designSpace.enterCreateMode)
        addJointMemberButton.grid(row=0,column=0)

        # Transitions the DesignSpace into its delete joint mode
        moveJointButton = Button(self.frame,text="Move",width=TOOLBAR_BUTTON_WIDTH,command=self.master.designSpace.enterMoveJointMode)
        moveJointButton.grid(row=0,column=2)

        # Transitions the DesignSpace into its remove joint mode
        removeJointButton = Button(self.frame,text="Destroy",width=TOOLBAR_BUTTON_WIDTH,command=self.master.designSpace.enterDestroyMode)
        removeJointButton.grid(row=0,column=1)

        fixedJointButton = Button(self.frame,text="Fixed Joint",width=TOOLBAR_BUTTON_WIDTH,command=self.master.designSpace.enterFixedJointMode)
        fixedJointButton.grid(row=0,column=3)

        rollerJointButton = Button(self.frame,text="Roller Joint",width=TOOLBAR_BUTTON_WIDTH,command=self.master.designSpace.enterRollerJointMode)
        rollerJointButton.grid(row=0,column=4)

        addLoadButton = Button(self.frame,text="Add/Edit Loads",width=TOOLBAR_BUTTON_WIDTH,command=self.master.designSpace.enterAddLoadMode)
        addLoadButton.grid(row=0,column=5)

##        saveButton = Button(self.frame,text="Save",width=TOOLBAR_BUTTON_WIDTH,command=self.master.save)
##        saveButton.grid(row=0,column=6)
##
##        loadButton = Button(self.frame,text="Load",width=TOOLBAR_BUTTON_WIDTH,command=self.master.load)
##        loadButton.grid(row=0,column=7)

        clearButton = Button(self.frame,text="Clear",width=TOOLBAR_BUTTON_WIDTH,command=self.master.clearTruss)
        clearButton.grid(row=0,column=6)

        solveButton = Button(self.frame,text="Solve",width=TOOLBAR_BUTTON_WIDTH,command=self.master.solveTruss)
        solveButton.grid(row=0,column=7)


class TopMenu():
    def __init__(self,master):
        self.master = master
        #menubar = Menu(master.master)
        menubar = Menu(root)

        # File Menu
        fileMenu = Menu(menubar,tearoff=0)
        fileMenu.add_command(label="Save",command=self.master.save,accelerator="Ctrl-S")
        fileMenu.add_command(label="Save As",command=self.master.saveas)
        fileMenu.add_command(label="Open",command=self.master.load,accelerator="Ctr-O")

        # Event Bindings for the file Menu
        self.master.master.bind("<Control-s>",self.master.saveEventHandle)
        self.master.master.bind("<Control-o>",self.master.openEventHandle)

        # Edit Menu
        editMenu = Menu(menubar,tearoff=0)
        modeMenu = Menu(editMenu,tearoff=0)
        modeMenu.add_command(label="Create",underline=1, command=self.master.designSpace.enterCreateMode, accelerator="Ctrl-C")
        modeMenu.add_command(label="Destroy",underline=1, command=self.master.designSpace.enterDestroyMode, accelerator="Ctrl-D")
        modeMenu.add_command(label="Move",underline=1, command=self.master.designSpace.enterMoveJointMode, accelerator="Ctrl-M")
        modeMenu.add_command(label="Add Loads",underline=1, command=self.master.designSpace.enterAddLoadMode, accelerator="Ctrl-L")
        modeMenu.add_command(label="Fixed Joint",underline=1, command=self.master.designSpace.enterFixedJointMode, accelerator="Ctrl-F")
        modeMenu.add_command(label="Roller Joint",underline=1, command=self.master.designSpace.enterRollerJointMode, accelerator="Ctrl-R")

        # Bind the key press events to the menu commands
        self.master.master.bind("<Control-c>",self.master.designSpace.enterCreateMode)
        self.master.master.bind("<Control-d>",self.master.designSpace.enterDestroyMode)
        self.master.master.bind("<Control-m>",self.master.designSpace.enterMoveJointMode)
        self.master.master.bind("<Control-l>",self.master.designSpace.enterAddLoadMode)
        self.master.master.bind("<Control-f>",self.master.designSpace.enterFixedJointMode)
        self.master.master.bind("<Control-r>",self.master.designSpace.enterRollerJointMode)

        
        editMenu.add_cascade(label="Modes",menu=modeMenu)
        editMenu.add_command(label="Clear",command=self.master.clearTruss)
        editMenu.add_command(label="Solve",command=self.master.solveTruss)

        # Option Menu
        optionMenu = Menu(menubar,tearoff=0)
        optionMenu.add_command(label="Toggle Snap",command=self.master.designSpace.toggleSnap,accelerator="Ctrl-G")
        #optionMenu.add_command(label="Preferences",command=lambda: None)

        # Grid Spacing Options
        gridMenu = Menu(optionMenu,tearoff=0)
        gridMenu.add_command(label="Small  ("+str(SMALL_GRID_SPACING)+" pixels)", command=self.master.designSpace.smallGrid)
        gridMenu.add_command(label="Medium ("+str(MED_GRID_SPACING)+" pixels)", command=self.master.designSpace.mediumGrid)
        gridMenu.add_command(label="Large  ("+str(LARGE_GRID_SPACING)+" pixels)", command=self.master.designSpace.largeGrid)
        gridMenu.add_command(label="Off",command=self.master.designSpace.eraseGrid)

        optionMenu.add_cascade(label="Grid",menu=gridMenu)
        
        
        menubar.add_cascade(label="File",menu=fileMenu)
        menubar.add_cascade(label="Edit",menu=editMenu)
        menubar.add_cascade(label="Options",menu=optionMenu)

        # Display Menu
        #master.master.config(menu=menubar)
        root.config(menu=menubar)

root = Tk()
root.minsize(width=WINDOW_WIDTH,height=WINDOW_HEIGHT)
root.title("ULTRAS - Truss Design and Analysis")
root.resizable(width=False,height=False)

app = App(root)


root.mainloop()
        

        
