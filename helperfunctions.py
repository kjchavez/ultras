# Helper Functions that are used across multiple classes


""" -------------------------------------------------------------
    rectifyCoords
    -------------------------------------------------------------
    coords - a 4-tuple two point coordinates of the form (x1,y1,x2,y2)
    canvas - a Tkinter Canvas widget on which these coordinates are

    Returns the coordinates with the Y-axis inverted based on the canvas
    height. This is useful for converting between truss and canvas coords.
"""        
def rectifyCoords(coords,canvas):
    canvasHeight = int(canvas['height'])
    return coords[0],canvasHeight-coords[1],coords[2],canvasHeight-coords[3]


""" --------------------------------------------------------------------
    rectifyPos
    --------------------------------------------------------------------
    Same as rectifyCoords except takes a 2-tuple, (x, y)
"""
def rectifyPos(pos,canvas):
    return pos[0],int(canvas['height'])-pos[1]
