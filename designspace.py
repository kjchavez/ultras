from tkinter import *
from constants import *
from graphics import *
from helperfunctions import *
from dialogs import *


""" -------------------------------------------------------------------
    Class: DesignSpace
    Description: Canvas widget with extra functionality for manipulating
                joints and members. The DesignSpace can operate in one
                of several different modes:

                'add jm'      -  Default mode, clicking on whitespace adds
                                a joint. Clicking on joint and dragging adds
                                members.
                                
                'move joints'   - Joints can be dragged around
                                
                'remove joints' - Clicking on joints deletes them and all
                                connected members. Clicking elsewhere does
                                nothing.

                'remove members' - To be implemented...

                'fixed joint'   - Clicking on a joint selects it as a fixed joint

                'roller joint'  - Clicking on a joint selects it as a roller joint
                
                'add loads'  -  Click and drag from a joint to add a load
"""
### Could potentially use a dictionary to map item handles to actual classes.
### That way, access to the current object would be as simple as
### dict.get(self.canvas.find_withtag(CURRENT),None) and then I would have the
### XGraphic class for whatever it is, joint, member, or load!

class DesignSpace():
    def __init__(self,master,gridSpacing = MED_GRID_SPACING):
        self.master = master
        self.canvas = Canvas(master.frame,width=DESIGNSPACE_WIDTH, \
                             height=DESIGNSPACE_HEIGHT, \
                             bg='white')
        self.canvas.grid(row=1,column=0)#,sticky=E+W+N+S)

        # Objects dictionary key = item handle number, value = graphic class
        self.objects = {}
        
        # Draw grid lines
        self.gridSpacing = gridSpacing
        self.drawGrid()

        # Draw status text
        self.statusBar = StatusGraphic(self.canvas,0,DESIGNSPACE_HEIGHT,SW)
        self.statusBar.setText("  Creating...")

        # Draw member/joint count text
        self.mjCount = StatusGraphic(self.canvas,DESIGNSPACE_WIDTH,DESIGNSPACE_HEIGHT,SE,text=" (0 Joints / 0 Members)")
        
        # Event Bindings
        self.canvas.bind("<Button-1>",self.mouseClickB1)
        self.canvas.bind("<Button-3>",self.mouseClickB3)
        self.canvas.bind("<B1-Motion>",self.mouseMotionB1)
        self.canvas.bind("<ButtonRelease-1>",self.mouseRelease)
        self.canvas.bind("<Motion>", self.mouseMotion)
        self.canvas.bind("<Leave>",self.mouseExit)


        # Handles for manipulating joints
        self.currentJoint = None    # Multipurpose handle, re-assigned at every mouse click
        self.prevJoint = None       # Used while adding members

        # Current Mode Flag
        self.mode = "create"

        # Snapping to grid?
        self.isSnapping = True
        
        # Handles for Special Graphics
        self.memberLine = None
        self.jointShadow = None

        # Right Click Menu
        self.rcJointMenu = self.rightClickMenu("joint")
        self.rcMemberMenu = self.rightClickMenu("member")
        self.rcNothingMenu = self.rightClickMenu("free space")

    def eraseGrid(self):
        self.canvas.delete('grid')

    def drawGrid(self):
        # Draw grid lines 
        for x in range (0,int(self.canvas['width']),self.gridSpacing): 
            self.canvas.create_line(x,0,x,int(self.canvas['height']),fill=GRID_COLOR,tags='grid') 
        for y in range(0,int(self.canvas['height']),self.gridSpacing): 
            self.canvas.create_line(0,y,int(self.canvas['width']),y,fill=GRID_COLOR,tags='grid')

        self.canvas.lower('grid')

    def mouseExit(self,event):
        self.canvas.delete(self.jointShadow)
        self.jointShadow = None

    def trussCoor(self,cx,cy):
        return (cx, int(self.canvas['height']) - cy)

    def canvasCoor(self,tx,ty):
            return (tx, int(self.canvas['height']) - ty)


    def addJoint(self,event):
        """ Draw a joint and canvasx and canvasy
        """
        #print(event.x,event.y, self.canvas.canvasx(event.x),self.canvas.canvasy(event.y)) # for debugging
        cx = self.canvas.canvasx(event.x,gridspacing=(self.gridSpacing if self.isSnapping else None))
        cy = self.canvas.canvasy(event.y,gridspacing=(self.gridSpacing if self.isSnapping else None))
        trussX,trussY = rectifyPos((cx,cy),self.canvas)
        newJoint = self.master.truss.addJoint(trussX,trussY)
        newJoint.graphic = JointGraphic(self.canvas,newJoint)
        newJoint.loadLine = None

        self.mjCount.setText(" ("+str(len(self.master.truss.getJoints()))+" Joints / "+str(len(self.master.truss.getMembers()))+" Members)")

        self.master.reanalyzeTruss()
        #print(self.master.truss)

    def deleteCurrentJoint(self):
        wasSolved = self.master.truss.isSolved
        
        self.currentJoint.graphic.delete()
        for member in self.currentJoint.getMembers():
            member.graphic.delete()
        self.master.truss.deleteJoint(self.currentJoint)
        if self.currentJoint.loadLine:
            self.currentJoint.loadLine.delete()

        if wasSolved:
            # print("truss was solved")
            self.master.truss.setUnsolved()
            for member in self.master.truss.getMembers():
                # print("processing",str(member))
                member.graphic.update()
            self.master.solveTruss()

        self.mjCount.setText(" ("+str(len(self.master.truss.getJoints()))+" Joints / "+str(len(self.master.truss.getMembers()))+" Members)")


    def deleteCurrentMember(self):
        wasSolved = self.master.truss.isSolved
        
        self.currentMember.graphic.delete()
        self.master.truss.deleteMember(self.currentMember)

        if wasSolved:
            # print("truss was solved")
            self.master.truss.setUnsolved()
            for member in self.master.truss.getMembers():
                # print("processing",str(member))
                member.graphic.update()
            self.master.solveTruss()

        self.mjCount.setText(" ("+str(len(self.master.truss.getJoints()))+" Joints / "+str(len(self.master.truss.getMembers()))+" Members)")

    def deleteCurrentLoad(self):
        self.master.truss.setExternalLoad(self.currentJoint) # Resets the load to (0,0)
        if self.currentJoint.loadLine:
            self.currentJoint.loadLine.delete()

        self.master.reanalyzeTruss()

    def mouseMotion(self,event):
        if self.mode == "create":
            X, Y = self.canvas.canvasx(event.x,gridspacing=(self.gridSpacing if self.isSnapping else None)), self.canvas.canvasy(event.y,gridspacing=(self.gridSpacing if self.isSnapping else None))
            if self.jointShadow:
                self.canvas.coords(self.jointShadow,(X-JOINT_SIZE/2,Y-JOINT_SIZE/2,X+JOINT_SIZE/2,Y+JOINT_SIZE/2))#,fill='gray75')
            else:
                self.jointShadow = self.canvas.create_oval(X-JOINT_SIZE/2,Y-JOINT_SIZE/2,X+JOINT_SIZE/2,Y+JOINT_SIZE/2,fill='gray85',outline="")

    def mouseClickB1(self,event):
        # These lines are executed for every mouse click, regardless of the mode of the Design Space
        # This is to ensure that self.currentJoint is always the last joint clicked on.
        trussX,trussY = rectifyPos((event.x,event.y),self.canvas)
        self.currentJoint = self.master.truss.getNearbyJoint(trussX,trussY,rng=JOINT_SIZE)
        self.currentMember = self.master.truss.getNearbyMember(trussX,trussY,rng=JOINT_SIZE)
        #print("CURRENT CLICK:",trussX,trussY)
        #print(self.canvas.gettags(CURRENT))

        # Default is to add a new joint if user clicks on whitespace
        if not self.currentJoint and self.mode == "create":
           self.addJoint(event)
           return
        
        # If DesignSpace is in delete mode, and user clicks on a joint or member, delete it
        if self.mode == "destroy":
            if self.currentJoint:
                self.deleteCurrentJoint()
            elif self.currentMember:
                self.deleteCurrentMember()

        # If DesignSpace is in fixed joint mode
        if self.currentJoint and self.mode == "fixed joint":
            self.selectFixedJoint()

        # If DesignSpace is in roller joint mode
        if self.currentJoint and self.mode == "roller joint":
            self.selectRollerJoint()

    def mouseClickB3(self,event):
        trussX,trussY = rectifyPos((event.x,event.y),self.canvas)
        self.currentJoint = self.master.truss.getNearbyJoint(trussX,trussY,rng=JOINT_SIZE)
        self.currentMember = self.master.truss.getNearbyMember(trussX,trussY,rng=JOINT_SIZE)

        if self.currentJoint:
            self.postRCJointMenu(event)
        elif self.currentMember:
            self.postRCMemberMenu(event)
        else:
            self.postRCNothingMenu(event)

    def postRCJointMenu(self,event):
        self.rcJointMenu.post(event.x_root,event.y_root)
    def postRCMemberMenu(self,event):
        self.rcMemberMenu.post(event.x_root,event.y_root)
    def postRCNothingMenu(self,event):
        self.rcNothingMenu.post(event.x_root,event.y_root)

    def rightClickMenu(self,obj):
            # Obj should either be 'joint' or 'member'
            rcMenu = Menu(self.master.master, tearoff=0)
            if obj == 'joint':
                rcMenu.add_command(label="Remove Joint",command=self.deleteCurrentJoint)
                rcMenu.add_command(label="Mark as Fixed",command=self.selectFixedJoint)
                rcMenu.add_command(label="Mark as Roller",command=self.selectRollerJoint)
                rcMenu.add_command(label="Remove Load",command=self.deleteCurrentLoad)
                rcMenu.add_command(label="Move Joint",command=self.enterMoveJointMode)
            if obj == "member":
                rcMenu.add_command(label="Remove Member",command=self.deleteCurrentMember)
            if obj == "free space":
                rcMenu.add_command(label="Toggle Snapping",command=self.toggleSnap)
                gridSubMenu = Menu(rcMenu,tearoff=0)
                gridSubMenu.add_command(label="Small",command=self.smallGrid)
                gridSubMenu.add_command(label="Medium",command=self.mediumGrid)
                gridSubMenu.add_command(label="Large",command=self.largeGrid)
                gridSubMenu.add_command(label="Off",command=self.eraseGrid)
                rcMenu.add_cascade(label="Grid Size",menu=gridSubMenu)
                modeMenu = Menu(rcMenu,tearoff=0)
                modeMenu.add_command(label="Create",underline=1, command=self.enterCreateMode, accelerator="Ctrl-C")
                modeMenu.add_command(label="Destroy",underline=1, command=self.enterDestroyMode, accelerator="Ctrl-D")
                modeMenu.add_command(label="Move",underline=1, command=self.enterMoveJointMode, accelerator="Ctrl-M")
                modeMenu.add_command(label="Add Loads",underline=1, command=self.enterAddLoadMode, accelerator="Ctrl-L")
                modeMenu.add_command(label="Fixed Joint",underline=1, command=self.enterFixedJointMode, accelerator="Ctrl-F")
                modeMenu.add_command(label="Roller Joint",underline=1, command=self.enterRollerJointMode, accelerator="Ctrl-R")
                rcMenu.add_cascade(label="Switch Mode",menu=modeMenu)

            return rcMenu


    def mouseMotionB1(self,event):
        # Moving Joints
        if self.currentJoint and self.mode == "move joints":
            self.moveJoint(event)
            return

        # Adding Members
        if self.currentJoint and self.mode == "create":
            if self.prevJoint and (self.prevJoint != self.currentJoint):  # If the previous joint is not None and it is not equal to the currentJoint
                self.addMember()

            self.prevJoint = self.currentJoint
            
            trussX, trussY = rectifyPos((event.x,event.y),self.canvas)
            possibleNewJoint = self.master.truss.getNearbyJoint(trussX,trussY,rng=JOINT_SIZE)

            if possibleNewJoint is not None:
                self.currentJoint = possibleNewJoint

            # Graphics
            self.canvas.delete(self.memberLine)
            if self.prevJoint:
                self.memberLine = self.canvas.create_line(self.canvasCoor(self.prevJoint.getX(),self.prevJoint.getY()),(event.x,event.y),fill=MEMBER_ACTIVE_COLOR)

            return

        # Adding Loads
        if self.currentJoint and self.mode == "add loads":
            cx = self.canvas.canvasx(event.x,gridspacing=(self.gridSpacing if self.isSnapping else None))
            cy = self.canvas.canvasy(event.y,gridspacing=(self.gridSpacing if self.isSnapping else None))
            if self.currentJoint.loadLine:
                self.currentJoint.loadLine.moveTo(cx,cy)
            else:
                self.currentJoint.loadLine = LoadGraphic(self.canvas,self.currentJoint,cx,cy)

            trussDX, trussDY = self.currentJoint.loadLine.getDX(),-self.currentJoint.loadLine.getDY()
            self.master.truss.setExternalLoad(self.currentJoint, \
                                              LOAD_SCALE_FACTOR *(trussDX), \
                                              LOAD_SCALE_FACTOR *(trussDY))
            self.currentJoint.graphic.update()
            #print(self.master.truss)
            self.master.solveTruss()


    def mouseRelease(self,event):
        if self.mode == "create":
            self.prevJoint = None
            self.canvas.delete(self.memberLine)
            self.memberLine = None
            return

        if self.mode == "add loads" and self.currentJoint:
            if self.currentJoint.loadLine:
                self.currentJoint.loadLine.makeInactive()

    

    def addMember(self):
        newMember = self.master.truss.addMember(self.prevJoint,self.currentJoint)
        if newMember:
            newMember.graphic = MemberGraphic(self.canvas,newMember)
            newMember.startJoint.graphic.update()
            newMember.endJoint.graphic.update()
        #print(self.master.truss) #for debugging
            self.master.reanalyzeTruss()

        self.mjCount.setText(" ("+str(len(self.master.truss.getJoints()))+" Joints / "+str(len(self.master.truss.getMembers()))+" Members)")
        
                
    def moveJoint(self,event):
        cx = self.canvas.canvasx(event.x,gridspacing=(self.gridSpacing if self.isSnapping else None))
        cy = self.canvas.canvasy(event.y,gridspacing=(self.gridSpacing if self.isSnapping else None))
        trussX,trussY = self.trussCoor(cx,cy)
        self.master.truss.moveJointTo(self.currentJoint,trussX,trussY)

        # Update attached members first...
        for member in self.currentJoint.getMembers():
            member.graphic.update()

        # Then update joint so it will be on top layer
        self.currentJoint.graphic.update()

        #Then update any loadLine associated with the joint
        if self.currentJoint.loadLine:
            self.currentJoint.loadLine.update()

        # Analyze Truss again
        self.master.solveTruss()

    def clear(self):
        self.canvas.delete('truss')
        self.mjCount.setText(" ("+str(len(self.master.truss.getJoints()))+" Joints / "+str(len(self.master.truss.getMembers()))+" Members)")

    def selectFixedJoint(self,event=None):
        if self.master.truss.markFixedJoint(self.currentJoint):
            self.currentJoint.graphic.changeColor(FIXED_JOINT_COLOR)
            # print(self.master.truss) #for debugging
            self.master.reanalyzeTruss()

    def selectRollerJoint(self):
        #askAngleDialog = RollerJointDialog(self.canvas)
        #print(self.master.result)
        if self.master.truss.markRollerJoint(self.currentJoint):#,angleOfSurface=askAngleDialog.result):
            self.currentJoint.graphic.changeColor(ROLLER_JOINT_COLOR)
            # print(self.master.truss)
            self.master.reanalyzeTruss()

    def enterDestroyMode(self,event=None):
        self.mode = "destroy"
        self.statusBar.setText("  Destroying...")

    def enterCreateMode(self,event=None):
        self.mode = "create"
        self.statusBar.setText("  Creating...")
        # Note, adding joints/members is the default mode

    def enterMoveJointMode(self,event=None):
        self.mode = "move joints"
        self.statusBar.setText("  Moving Joints...")

    def enterFixedJointMode(self,event=None):
        self.mode = "fixed joint"
        self.statusBar.setText("  Select Fixed Joint...")

    def enterRollerJointMode(self,event=None):
        self.mode = "roller joint"
        self.statusBar.setText("  Select Roller Joint...")

    def enterAddLoadMode(self,event=None):
        self.mode = "add loads"
        self.statusBar.setText("  Add Loads...")

    def enterSnapMode(self,event=None):
        self.isSnapping = True
        #print("snapping")

    def exitSnapMode(self,event=None):
        self.isSnapping = False
        #print("not snapping")

    def toggleSnap(self,event=None):
        self.isSnapping = not self.isSnapping

    def smallGrid(self):
        self.gridSpacing = SMALL_GRID_SPACING
        self.eraseGrid()
        self.drawGrid()

    def mediumGrid(self):
        self.gridSpacing = MED_GRID_SPACING
        self.eraseGrid()
        self.drawGrid()
        
    def largeGrid(self):
        self.gridSpacing = LARGE_GRID_SPACING
        self.eraseGrid()
        self.drawGrid()

