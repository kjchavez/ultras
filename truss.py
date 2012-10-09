import numpy as np
import pickle

class Joint(object):
    def __init__(self,x,y):
        self.location = [x,y]
        self.members = []
        self.forcesX = {"constant": 0.0}
        self.forcesY = {"constant": 0.0}
        self.neighborJoints = []

        # Flags for Fixed / Roller
        self.isFixed = False
        self.isRoller = False

    def move(self, dx, dy):
        self.location[0] += dx
        self.location[1] += dy

        self.updateForces()

    def updateForces(self):
        for member in self.members:
            # For the system of linear equations 
            self.forcesX[member] = member.getDX(self) / member.getLength()  # Cosine
            self.forcesY[member] = member.getDY(self) / member.getLength()  # Sine        


    def addMember(self, member):
        if member not in self.members:
            self.members.append(member)
            neighborJoint = member.getOtherJoint(self)
            if neighborJoint:
                self.neighborJoints.append(neighborJoint)
                
            # For the system of linear equations 
            self.forcesX[member] = member.getDX(self) / member.getLength()  # Cosine
            self.forcesY[member] = member.getDY(self) / member.getLength()  # Sine

    def deleteMember(self,member):
        if member in self.members:
            self.members.remove(member)
            self.neighborJoints.remove(member.getOtherJoint(self))
            self.updateForces()
            
    def addForce(self, forceX, forceY):
        self.forcesX["constant"] += forceX
        self.forcesY["constant"] += forceY

    def setForce(self,forceX,forceY):
        self.forcesX["constant"] = forceX
        self.forcesY["constant"] = forceY

    def makeFixed(self):
        self.forcesX["fixedX"] = 1.0
        self.forcesY["fixedY"] = 1.0
        self.isFixed = True
        self.fixedX = None #Unknown, will be set once truss is solved
        self.fixedY = None
        pass

    def makeNotFixed(self):
        if "fixedX" in self.forcesX:
            del self.forcesX["fixedX"]
        if "fixedY" in self.forcesY:
            del self.forcesY["fixedY"]
            
        self.isFixed = False
        del self.fixedX
        del self.fixedY

    def makeRoller(self,angleOfSurface=0):
        """
        Parameters:
            angleOfSurface - the orientation of the surface (in degrees from horizontal) on which the roller rests
        """
        self.forcesX["roller"] = np.cos(np.radians(angleOfSurface + 90))
        self.forcesY["roller"] = np.sin(np.radians(angleOfSurface + 90))

        self.isRoller = True
        self.rollerX = None #Unknown, will be set once truss is solved
        self.rollerY = None
        
        self.rollerAngle = angleOfSurface + 90

    def makeNotRoller(self):
        if "roller" in self.forcesX:
            del self.forcesX["roller"]
        if "roller" in self.forcesY:
            del self.forcesY["roller"]

        self.isRoller = False
        del self.rollerX
        del self.rollerY
            
    def getX(self):
        return self.location[0]

    def getY(self):
        return self.location[1]

    def getLoc(self):
        return self.location

    def getMembers(self):
        return self.members

    def getLoadMag(self):
        loadX = self.forcesX.get('constant',0.0)
        loadY = self.forcesY.get('constant',0.0)
        return np.sqrt(loadX**2+loadY**2)

    def isNeighbor(self, otherJoint):
        """
        Returns whether or not otherJoint is connected to this joint by one of its members
        """
        return (otherJoint in self.neighborJoints)

    def getNeighbors(self):
        return self.neighborJoints

    def __str__(self):
        stringDisplay = "Joint " + self.id + " (%.2f, %.2f) :\n" % (self.location[0], self.location[1])
        stringDisplay += "-"*20 + '\n'
        stringDisplay += "Members: "
        for member in self.members:
            stringDisplay += member.name + '  '
        stringDisplay += '\n'
        stringDisplay += "Forces X: "
        for forceSource in self.forcesX:
            stringDisplay += "(" + str(self.forcesX[forceSource])+"*"+str(forceSource)+") "
        stringDisplay += '\n'
        stringDisplay += "Forces Y: "
        for forceSource in self.forcesY:
            stringDisplay += "(" + str(self.forcesY[forceSource])+"*"+str(forceSource)+") "
        return stringDisplay        


class Member(object):
    def __init__(self,startJoint,endJoint):
        self.startJoint = startJoint
        self.endJoint = endJoint
        self.update()

        # This force will be set once the truss is solved and every time it's changed, goes back to None.
        self.force = None
        

    def __str__(self):
        return self.startJoint.id + self.endJoint.id

    def getCoords(self):
        return (self.startJoint.getX(),self.startJoint.getY(),self.endJoint.getX(),self.endJoint.getY())

    def getDX(self, referenceJoint=None):
        """
        If getDX computes dx then there is no need to really store dx as a local variable
        return self.dx if (referenceJoint == self.startJoint) else -self.dx
        """
        if not referenceJoint:
            return self.endJoint.getX() - self.startJoint.getX()
        
        if referenceJoint in (self.startJoint, self.endJoint):
            return self.getOtherJoint(referenceJoint).getX() - referenceJoint.getX()

    def getDY(self, referenceJoint=None):
        """
        If getDY computes dy then there is no need to really store dy as a local variable
        return self.dy if (referenceJoint == self.startJoint) else -self.dy
        """
        if not referenceJoint:
            return self.endJoint.getY()-self.startJoint.getY()
        
        if referenceJoint in (self.startJoint, self.endJoint):
            return self.getOtherJoint(referenceJoint).getY() - referenceJoint.getY()

    def getD(self, referenceJoint):
        """
        This function implements the convention of defining tension as a positive value and
        compression as a negative value. It defines all forces as acting away from a joint.
        Like rays of sunshine.
        """
        if referenceJoint in (self.startJoint, self.endJoint):
            return (self.getDX(referenceJoint),self.getDY(referenceJoint))
        
    def getLength(self):
        return np.sqrt(self.getDX(self.startJoint)**2 + self.getDY(self.startJoint)**2)

    def getCenter(self):
        return (self.startJoint.getX()+self.endJoint.getX())/2, \
               (self.startJoint.getY()+self.endJoint.getY())/2

    def update(self):
        self.dx = self.endJoint.getX() - self.startJoint.getX()
        self.dy = self.endJoint.getY() - self.startJoint.getY()
        self.length = np.sqrt(self.dx**2 + self.dy**2)

    def getOtherJoint(self,joint):
        if joint == self.startJoint:
            return self.endJoint
        elif joint == self.endJoint:
            return self.startJoint
        else:
            return None


class Truss(object):
    def __init__(self,name=""):
        self.joints = []
        self.members = []
        self.name = name

        # Keep track of names for joints
        self.index = 0
        self.labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        # If we have more than 52 joints in the truss, labels will wrap around to the beginning

        # Track other important properties of the truss
        self.hasFixedJoint = False
        self.hasRollerJoint = False
        self.isSolved = False
        self.forces = {}
        self.fixedJoint = None
        self.rollerJoint = None

    def __str__(self):
        displayString = "Truss " + self.name + '\n'
        displayString += "="*30 + '\n'
        displayString += "Number of Joints: %d\n" % len(self.joints)
        displayString += "Number of Members: %d\n" % len(self.members)
        displayString += "Statically Determinate: %s\n\n" % ('Yes' if self.isDeterminate() else 'No')
        for joint in self.joints:
            displayString += str(joint) + '\n\n'

        return displayString

    def isDeterminate(self):
        """
        Returns whether or not the truss is statically determinate by checking that m + 3 = 2j
        Point of Inquiry: Is this the only way for a truss to be determinate?
        """
        return ((len(self.joints) * 2) == (len(self.members) + 3) and self.hasFixedJoint and self.hasRollerJoint)

    def addJoint(self, x, y):
        """
        Creates and adds a new joint to the truss, assigning it an id as specified by the truss's list of
        labels. Returns the newJoint.
        """
        newJoint = Joint(x,y)

        # Give joints IDs for labeling and saving purposes
        newJoint.id = self.labels[self.index]
        self.index += 1

        # If we have run out of labels, start reusing them
        # Note that this will cause problems with saving and opening
        # trusses with more than 52 joints and should be improved
        if self.index == len(self.labels):
            self.index = 0
        
        self.joints.append(newJoint)

        # Truss has been modified, solution no longer valid.
        self.setUnsolved()
        
        return newJoint

    def deleteJoint(self,joint):
        if joint in self.joints:
            neighbors = joint.getNeighbors()
            for j in neighbors:
                for member in joint.getMembers():
                    j.deleteMember(member)    # If member is not attached to j, this line does nothing
                j.updateForces()

            for member in joint.getMembers():
                self.members.remove(member)
                
            self.joints.remove(joint)

            # Truss has been modified, solution no longer valid.
            self.setUnsolved()

    def addMember(self, joint1, joint2):
        if (joint1 in self.joints) and (joint2 in self.joints):
            # Only add the new member if it doesn't already exist
            if not joint1.isNeighbor(joint2):
                newMember = Member(joint1, joint2)

                # Give members names for reference and displaying
                newMember.name = joint1.id + joint2.id

                # Add the member to the truss's list of members
                self.members.append(newMember)
                
                # Add the member to both joints
                joint1.addMember(newMember)
                joint2.addMember(newMember)
                return newMember
                
        # else RaiseError

    def deleteMember(self,member):
        if member in self.members:
            member.startJoint.deleteMember(member)
            member.endJoint.deleteMember(member)
            self.members.remove(member)
            

    def moveJoint(self, joint, dx, dy):
        if joint in self.joints:
            joint.move(dx, dy)
            for member in joint.getMembers():
                member.getOtherJoint(joint).updateForces()

            # Truss has been modified, solution no longer valid.
            self.setUnsolved()
        #else RaiseError

    def moveJointTo(self,joint,x,y):
        self.moveJoint(joint,x-joint.getX(),y-joint.getY())

        # Truss has been modified, solution no longer valid.
        self.setUnsolved()

    def addExternalLoad(self, joint, loadx=0, loady=0,loadmag=0,angle=0,form='rect'):
        if joint not in self.joints:
            return 
            # RaiseError
            
        if form == 'rect':
            joint.addForce(loadx, loady)

            # Truss has been modified, solution no longer valid.
            self.setUnsolved()
            
            return "Added (%.2f %.2f) at Joint %s" % (loadx, loady, joint.id)

        if form == 'polar':
            loadx = loadmag*np.cos(np.radians(angle))
            loady = loadmag*np.sin(np.radians(angle))
            joint.addForce(loadx, loady)

            # Truss has been modified, solution no longer valid.
            self.setUnsolved()
            return "Added (%.2f %.2f) at Joint %s" % (loadx, loady, joint.id)

    def setExternalLoad(self,joint,loadx=0, loady=0,loadmag=0,angle=0,form='rect'):
        if form == 'polar':
            loadx = loadmag*np.cos(np.radians(angle))
            loady = loadmag*np.sin(np.radians(angle))

        joint.setForce(loadx,loady)
        # Truss has been modified, solution no longer valid.
        self.setUnsolved()

    def markFixedJoint(self,joint):
        """ Returns a bool indicating whether or not a joint was successfully marked as a
            fixed joint. """
        if joint not in self.joints:
            return False
            # RaiseError
            
        if self.hasFixedJoint:
            return False
            pass # RaiseError
        
        joint.makeFixed()
        self.fixedJoint = joint
        self.hasFixedJoint = True
        return True

    def markRollerJoint(self,joint,angleOfSurface=0):
        """ Returns a bool indicating whether or not a joint was successfully marked as a
            roller joint. """
        if joint not in self.joints:
            return False
            # RaiseError
            
        # If the truss already has a roller joint return a warning, but still proceed.
        if self.hasRollerJoint:
            return False
            # RaiseError
        
        joint.makeRoller(angleOfSurface)
        self.rollerJoint = joint
        self.hasRollerJoint = True
        return True
            

    def analyze(self):
        """
        Generates a system of linear equations by using the method of joints. Then feeds these linear
        equations into a linear algebra module from NumPy which solves for the forces in the members.
        """

        # Define our unknowns. For a properly defined truss we will have M + 3 unknowns
        unknowns = []
        for member in self.members:
            unknowns.append(member)
        unknowns.append("roller")
        unknowns.append("fixedX")
        unknowns.append("fixedY")

        # Collect 2 Equations from each joint.
        #       - equations is a matrix of coefficients
        #       - sol is the solution vector formed from the constants in the equations
        equations = []
        sol = []
        for joint in self.joints:
            eqX = []
            eqY = []
            for variable in unknowns:
                eqX.append(joint.forcesX.get(variable, 0.0))
                eqY.append(joint.forcesY.get(variable, 0.0))
                
            equations.append(eqX)
            sol.append(-joint.forcesX.get("constant", 0.0))

            equations.append(eqY)
            sol.append(-joint.forcesY.get("constant", 0.0))

        try:
            # Solve the system of linear equations
            a = np.array(equations)
            b = np.array(sol)
            x = np.linalg.solve(a,b)
            self.forces = dict(zip(unknowns, x))
            
        except np.linalg.LinAlgError:
            # For debugging
            print("LinAlgError: Matrix is singular or not square")
            print(a)
            print(b)
            return False
        

        self.setSolved()
        return True

    def setSolved(self):
        """ Handles all the details after the truss has been successfully analyzed
            This involves setting the force in each member and setting the fixed forces
            and roller forces in the appropriate joints. It also changes the isSolved
            flag to true.
        """
        self.isSolved = True
        for member in self.members:
            member.force = self.forces[member]
            
        self.fixedJoint.fixedX = self.forces["fixedX"]
        self.fixedJoint.fixedY = self.forces["fixedY"]
        self.rollerJoint.rollerX = self.forces["roller"]*np.cos(np.radians(self.rollerJoint.rollerAngle))
        self.rollerJoint.rollerY = self.forces["roller"]*np.sin(np.radians(self.rollerJoint.rollerAngle))

    def setUnsolved(self):
        """ Usually called when some change has been made to the truss that renders its
            previous solution invalid. Changes the isSolved flag, clears the forces dictionary
            and sets the force in each member to None. 
        """
        if self.isSolved:
            self.isSolved = False
            self.forces = {}
            for member in self.members:
                member.force = None     # None can be interpreted as unknown


    def getNearbyJoint(self, x, y, rng=2):
        """ Returns a joint that is within a certain range of (x,y)
        """
        for joint in self.joints:
            if joint.getX() < x + rng and \
               joint.getX() > x - rng and \
               joint.getY() < y + rng and \
               joint.getY() > y - rng:

                return joint

        return None

    def getNearbyMember(self, x, y, rng=10):
        for member in self.members:
            startX,startY,endX,endY = member.getCoords()

            if abs(member.getDX()) > abs(member.getDY()):
                if x > min(startX,endX) and x < max(startX,endX):
                    if member.getDX() != 0:
                        slope = member.getDY() / member.getDX()
                    else:
                        slope = 0
                    if y < startY + slope*(x - startX) + rng and \
                       y > startY + slope*(x - startX) - rng:
                        return member
            else:
                if y > min(startY,endY) and y < max(startY,endY):
                    if member.getDY() != 0:
                        slope = member.getDX() / member.getDY()
                    else:
                        slope = 0
                    if x < startX + slope*(y - startY) + rng and \
                       x > startX + slope*(y - startY) - rng:
                        return member

        return None
        
    def getMembers(self):
        return self.members

    def getJoints(self):
        return self.joints

    def getForce(self,key):
        return self.forces[key]
        # If key is not in self.forces, raise Error

    def displaySolution(self, precision=2):
        """
        Displays the solution in an easy to interpret manner if the truss has been solved.
        The precision of the forces is set by default to 2 decimal places, but may be adjusted
        when more precision is needed. This is simply to keep the display clean.
        """
        if self.isSolved:
            print("Solution\n"+"="*30)
            for forceSource in self.forces:
                print("%s -> %s" % (str(forceSource).ljust(10), round(self.forces[forceSource],precision)))
            print('\n')
            return True

        else:
            return False

    def save(self,filename):
        #Encode the truss in the bare essentials. Location of nodes and which nodes are connected
        abstractTruss = {'nodes': {}, 'edges': [], 'fixed joint': "", 'roller joint': "", 'loads':{} }
        
        for joint in self.joints:
            abstractTruss['nodes'][joint.id] = joint.getLoc()
            if joint.forcesX["constant"] or joint.forcesY["constant"]:
                abstractTruss['loads'][joint.id] = (joint.forcesX['constant'],joint.forcesY['constant'])
                
        for member in self.members:
            abstractTruss['edges'].append(str(member))

        if self.fixedJoint:
            abstractTruss['fixed joint'] = self.fixedJoint.id

        if self.rollerJoint:
            abstractTruss['roller joint'] = self.rollerJoint.id

        

        saveFile = open(filename,'wb')
        pickle.dump(abstractTruss, saveFile)
        saveFile.close()
        

def main():
##    # Instantiate a truss
##    truss = Truss()
##
##    # Add some pin joints at (0,0) (10,0) and (10,10)
##    truss.addJoint(0,0)
##    truss.addJoint(10,0)
##    truss.addJoint(10,10)
##
##    # Add members between all three joints
##    jointA = truss.getNearbyJoint(0,0)
##    jointB = truss.getNearbyJoint(10,0)
##    jointC = truss.getNearbyJoint(10,10)
##
##    truss.addMember(jointA,jointB)
##    truss.addMember(jointB,jointC)
##    truss.addMember(jointC,jointA)
##    truss.addMember(jointA,jointC)  # Try adding a member that already exists, shouldn't add anything
##
##    print(truss.addExternalLoad(jointA, 10, 20))
##    #print(truss.addExternalLoad(jointB, loadmag=20, angle=45, form='polar'))
##
##    truss.markFixedJoint(jointC)
##    truss.markRollerJoint(jointB, angleOfSurface=90)
##
##    # Display Truss
##    print(truss)
##
##    # Move joint
##    truss.moveJoint(jointA,5,5)
##    #print(truss)
##
##    # Solve Truss
##    truss.analyze()
##    truss.displaySolution()

    # Create Truss from E14 project
    truss1 = Truss()
    
    jointA = truss1.addJoint(0,0)
    jointB = truss1.addJoint(8,0)
    jointC = truss1.addJoint(16,0)    
    jointD = truss1.addJoint(24,0)
    jointE = truss1.addJoint(4,6)
    jointF = truss1.addJoint(12,4)
    jointG = truss1.addJoint(20,6)

    truss1.addMember(jointA,jointB)
    truss1.addMember(jointA,jointE)
    truss1.addMember(jointB,jointC)
    truss1.addMember(jointC,jointD)
    truss1.addMember(jointE,jointF)
    truss1.addMember(jointE,jointB)
    truss1.addMember(jointF,jointC)
    truss1.addMember(jointF,jointG)
    truss1.addMember(jointC,jointG)
    truss1.addMember(jointG,jointD)
    truss1.addMember(jointB,jointF)

    truss1.markFixedJoint(jointA)
    truss1.markRollerJoint(jointD)
    
    truss1.addExternalLoad(jointB,0,-16.5)
    truss1.addExternalLoad(jointC,0,-16.5)

    print(truss1)
    truss1.analyze()
    truss1.displaySolution()
    
if __name__ == "__main__":
    main()
    
