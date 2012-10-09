# Truss Solver Dialogs
from tkinter import *

class RollerJointDialog(simpledialog.Dialog):
    def __init__(self,master):
        self.angle = StringVar()
        self.angle.set('h')
        simpledialog.Dialog.__init__(self,master,title="Roller Joint Angle")


        
    def body(self,master):
        Radiobutton(master,text="Horizontal",variable=self.angle,value='h').grid(row=0,column=0,sticky=W)
        Radiobutton(master,text="Vertical",variable=self.angle,value='v').grid(row=1,column=0,sticky=W)
        Radiobutton(master,text="Custom",variable=self.angle,value='c').grid(row=2,column=0,sticky=W)
        Label(text="Angle: ").grid(row=3,column=0,sticky=E)
        self.angleEntry = Entry(master)
        self.angleEntry.grid(row=3,column=1)

    def validate(self):
        if self.angle.get() == 'h':
            self.result = 0
            print('returning from validate')
            return 1

        if self.angle.get() == 'v':
            self.result = 90
            return True

        if self.angle.get() == 'c':
            try:
                customAngle = int(self.angleEntry.get())
                self.result = customAngle
                return True
            except ValueError:
                messagebox.showwarning("Invalid Angle", \
                                         "Illegal custom angle, please try again")
                return False

        return False

    def apply(self):
        pass
            
        
        
