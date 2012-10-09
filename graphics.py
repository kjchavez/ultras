# Graphic Elements for the DesignSpace
from constants import *
from helperfunctions import *
from tkinter import *
import numpy as np

class MemberGraphic:
    def __init__(self,canvas,member,color=MEMBER_COLOR):
        self.member = member
        self.canvas = canvas
        self.color = color
        self.draw()

    def update(self):
        self.delete()
        self.draw()

    def draw(self):
        if self.member.force:
            color = TENSION_COLOR if self.member.force > 0 else COMPRESSION_COLOR
        else:
            color = self.color
            
        self.image = self.canvas.create_line(rectifyCoords(self.member.getCoords(),self.canvas),fill=color,smooth=True,width=1,tags=('member','truss'))
        if self.member.force:
            labelCoords = rectifyCoords(self.member.getCoords(),self.canvas)
            labelX = (labelCoords[0] + labelCoords[2]) / 2
            labelY = (labelCoords[1] + labelCoords[3]) / 2
            text = "  " + (str(round(self.member.force,2)))

            # Select an appropriate anchor so the label doesn't end up on top of the member's image
            if self.member.getDX() == 0:
                anchor = E
            else:
                tan = self.member.getDY() / self.member.getDX()
                if tan > 0:
                    anchor = SE
                else:
                    anchor = NE
            

            textcolor = TENSION_TEXT_COLOR if self.member.force > 0 else COMPRESSION_TEXT_COLOR
                
            self.label = self.canvas.create_text((labelX,labelY),text=text,anchor=anchor,tags=('member','truss'),fill=textcolor)
        else:
            self.label = None
        
    def delete(self):
        self.canvas.delete(self.image)
        self.canvas.delete(self.label)

class JointGraphic:
    def __init__(self,canvas,joint,color=JOINT_COLOR):
        self.joint = joint
        self.canvas = canvas
        self.canvasHeight = int(canvas['height'])
        self.color = color
        self.forceX = None
        self.forceY = None
        self.forceRoller = None
        self.isLabeled = True # Labeling System isn't perfected yet...
        self.draw(self.canvas)

    def update(self):
        self.delete()
        self.draw(self.canvas)

    def draw(self,canvas):
        canvasX = self.joint.getX()
        canvasY = int(canvas['height']) - self.joint.getY()
        self.image = canvas.create_oval(canvasX-JOINT_SIZE/2,canvasY-JOINT_SIZE/2,canvasX+JOINT_SIZE/2,canvasY+JOINT_SIZE/2,fill=self.color,tags=('joint','truss'))

        if self.isLabeled:
            lx, ly = self.findBestLabelDir()
            # print(lx,ly)
            self.label = self.canvas.create_text((canvasX+lx*20,canvasY+ly*20),text=self.joint.id,tags=('joint','truss'))
        else:
            self.label = None

        if self.joint.isFixed and (self.joint.fixedX or self.joint.fixedY): #If the truss has been solved for these forces
            self.forceX = LoadGraphic(canvas,self.joint,self.joint.getX()+self.joint.fixedX/LOAD_SCALE_FACTOR,int(canvas['height'])-self.joint.getY(),color=FIXED_FORCE_COLOR)
            self.forceY = LoadGraphic(canvas,self.joint,self.joint.getX(),int(canvas['height'])-(self.joint.getY()+self.joint.fixedY/LOAD_SCALE_FACTOR),color=FIXED_FORCE_COLOR)

        if self.joint.isRoller and self.joint.rollerX:
            self.forceRoller = LoadGraphic(canvas,self.joint,self.joint.getX()-self.joint.rollerX/LOAD_SCALE_FACTOR,\
                                           self.canvasHeight-(self.joint.getY()-self.joint.rollerY/LOAD_SCALE_FACTOR),color=ROLLER_FORCE_COLOR,arrow=FIRST)
    def delete(self):
        self.canvas.delete(self.image)
        self.canvas.delete(self.label)
        if self.forceX:
            self.forceX.delete()
            self.forceY.delete()
        if self.forceRoller:
            self.forceRoller.delete()


    def changeColor(self,newColor):
        self.color = newColor
        self.update()

    def findBestLabelDir(self):
        x = 0.0
        for fx in self.joint.forcesX:
            if fx != 'constant':
                x -= self.joint.forcesX[fx]
                
        if self.joint.forcesX['constant'] != 0:
            # print("counting external")
            x -= self.joint.forcesX['constant']/np.sqrt(self.joint.forcesX['constant']**2+self.joint.forcesY['constant']**2)
            x /= len(self.joint.forcesX)
        else:
            x /= max((len(self.joint.forcesX)-1),1)

        y = 0.0
        for fy in self.joint.forcesY:
            if fy != 'constant':
                y += self.joint.forcesY[fy]
                
        if self.joint.forcesY['constant'] != 0:
            y += self.joint.forcesY['constant']/np.sqrt(self.joint.forcesX['constant']**2+self.joint.forcesY['constant']**2)
            y /= len(self.joint.forcesY)
        else:
            y /= max((len(self.joint.forcesY)-1),1)

        if not x and not y:
            x, y = (0,-1) # Label should go right above the image
        #print(x,y)
        return (x/np.sqrt(x**2+y**2),y/np.sqrt(x**2+y**2))
    
class LoadGraphic:
    def __init__(self,canvas,joint,endX,endY,color=LOAD_ACTIVE_COLOR,arrow=LAST):
        self.canvas = canvas
        self.joint = joint
        startX, startY = rectifyPos(self.joint.getLoc(),self.canvas)
        self.dx = endX - startX   
        self.dy = endY - startY
        self.color = color
        self.arrow = arrow
        #self.image = None
        self.draw()

    def update(self):
        self.delete()
        self.draw()

    def draw(self):
        length = np.sqrt(self.dx**2 + self.dy**2)
        magnitudeForce = round(LOAD_SCALE_FACTOR * length,2)

        if length != 0:
            if length < MINIMUM_ARROW_LENGTH:
                    dx = (self.dx/length)*MINIMUM_ARROW_LENGTH
                    dy = (self.dy/length)*MINIMUM_ARROW_LENGTH
            else:
                    dx = self.dx
                    dy = self.dy

            startX, startY = rectifyPos(self.joint.getLoc(),self.canvas)
            textX, textY = startX+dx+(LOAD_LABEL_OFFSET+10*abs(self.dx/length))*(self.dx/length),startY+dy+(LOAD_LABEL_OFFSET+5*abs(self.dy/length))*(self.dy/length)
                
            self.image = self.canvas.create_line(rectifyPos(self.joint.getLoc(),self.canvas),(startX+dx,startY+dy),fill=self.color,arrow=self.arrow,tags=('load','truss'))

            self.label = self.canvas.create_text((textX,textY),text=str(magnitudeForce)+' N',tags=('load','truss'))

        else:
            self.image = None
            self.label = None

    def delete(self):
        self.canvas.delete(self.image)
        self.canvas.delete(self.label)

    def moveTo(self,newX,newY):
        startX, startY = rectifyPos(self.joint.getLoc(),self.canvas)        
        self.dx,self.dy = newX - startX, newY - startY
        self.update()

    def getDX(self):
        return self.dx

    def getDY(self):
        return self.dy

    def makeInactive(self):
        self.color = LOAD_COLOR
        self.update()


class StatusGraphic:
    def __init__(self,canvas,x,y,anchor,text="",color=STATUS_TEXT_COLOR):
        self.canvas = canvas
        self.pos = (x,y)
        self.anchor = anchor
        self.text = text
        self.color = STATUS_TEXT_COLOR
        self.image = None
        self.draw(self.canvas)

    def update(self):
        self.delete()
        self.draw(self.canvas)

    def draw(self,canvas):
        self.image = canvas.create_text(self.pos,text=self.text,anchor=self.anchor,fill=self.color,tags="status")

    def delete(self):
        self.canvas.delete(self.image)

    def setText(self,newText):
        self.text = newText
        self.update()

    def setTempText(self,tempText):
        self.delete()
        self.image = self.canvas.create_text(self.pos,text=tempText,anchor=self.anchor,fill=self.color,tags="status")


    def changeColor(self,newColor):
        self.color = newColor
        self.update()

    

