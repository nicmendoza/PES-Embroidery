import svgpathtools
from PES_Emb_mathutils import *
from PES_render_utils import *
from PES import *
import re
import numpy

def loadVectorGraphic(filename):
    svg = None
    attributes = None
    try:
        svg, attributes = svgpathtools.svg2paths(filename)
    except:
        print("Couldn't load SVG file. Perhaps it doesn't exist?")

    return svg, attributes

def getColorOfPathAtIndex(attributes, index):
    color = (0, 0, 0)

    if attributes is None:
        return color

    try:
        m = re.search("fill:#(\S{6})", attributes[index]["style"])
        last = m.group(1)
        r = int(last[0:2], 16)
        g = int(last[2:4], 16)
        b = int(last[4:6], 16)
        color = (r, g, b)
    except:
        None

    return color

def makeStitchLines(shape, fillColor=(0,0,0), threadWidth=2, slope=1, debug=False):
    """

    :type shape: svgpathtools.CubicBezier
    """
    stitchLines = []

    # Draw the shape
    GenericRenderer.globalRenderer.addPath(shape, 50, 120, 255)

    # Get the bounds of the shape
    left, right, bottom, top = shape.bbox()
    width = right - left
    height = top - bottom
    center = complex( (left + right) / 2, (top + bottom) / 2)
    # Draw the bounding box
    GenericRenderer.globalRenderer.addLine(Line(  start=complex(left,top)  ,end=complex(right,top) ), 0, 255, 255)
    GenericRenderer.globalRenderer.addLine(Line(start=complex(right, top), end=complex(right, bottom)), 0, 255, 255)
    GenericRenderer.globalRenderer.addLine(Line(start=complex(right, bottom), end=complex(left, bottom)), 0, 255, 255)
    GenericRenderer.globalRenderer.addLine(Line(start=complex(left, bottom), end=complex(left, top)), 0, 255, 255)
    GenericRenderer.globalRenderer.addPoint(center, 0, 255, 255)

    # Intersect a line with the given angle over and over
    #  to find where stitches should start/end.
    # If the shape isn't convex, the line might intersect
    #  more than once but should always intersect an even
    #  number of times (as long as the shape is closed.)

    # Place the intersection line at various points along
    # a straight path that has the opposite slope.
    # The path should cross through the center of the bounding-
    #  box square.
    intersectionPath = InfLine(m=slope, center=center)
    GenericRenderer.globalRenderer.addLine(
        Line(start=complex(1000, intersectionPath.y_for_x(1000)),
             end=complex(-1000, intersectionPath.y_for_x(-1000)) ), 0, 255, 0)
    intersectionPath.invertSlope()
    GenericRenderer.globalRenderer.addLine(
        Line(start=complex(1000, intersectionPath.y_for_x(1000)),
             end=complex(-1000, intersectionPath.y_for_x(-1000))), 0, 255, 0)

    intersectionPath = getIntersectionPathFromBox(intersectionPath, left, right, top, bottom)

    GenericRenderer.globalRenderer.addLine(intersectionPath, 255, 255, 0)

    #print("Start and end points: {}, {}".format(p1,p2))
    #intersectionPath = intersectionPath.to_svg_Line(center=center, length=intersectionLineLength)

    # Make sure we cover everything based on the thread width.
    # Line objects can be enumerated from 0 < t < 1
    # Depending on the Line's length, we need to increment t
    # by a value such that we move threadWidth each time.
    totalIntersections = int((intersectionPath.length() / threadWidth)) + 1
    pathLength = intersectionPath.length()
    tIncrementAmount = pathLength / float(totalIntersections)
    # Get the max length of the intersection lines we'll need
    intersectionLineLength = getBoxDiagonalLength(left, right, top, bottom)

    print("Performing up to {} intersections along path: {}".format(totalIntersections, intersectionPath))
    print("(From {} to {})".format(intersectionPath.point(0), intersectionPath.point(1.0)))

    # for s in shape:
    #     for x in range(0, totalIntersections):
    #         center = intersectionPath.point((tIncrementAmount * x) / pathLength)
    #         GenericRenderer.globalRenderer.addPoint(center, 255, 255, 0)
    #         i = InfLine(m=slope, center=center)
    #         # Convert it to a bezier line
    #         l = i.to_svg_Line(center=center, length=3000)
    #         intersections = shape.intersect(l)
    #         for i in intersections:
    #             GenericRenderer.globalRenderer.addPoint(i[0][1].point(i[0][0]), 255, 0, 255)
    #             GenericRenderer.globalRenderer.addPoint(i[0][1].point(i[0][2]), 255, 0, 255)
    #
    #         print(intersections)
    # return []

    for x in range(0, totalIntersections):
        # Get a new (infinite) line using the point at the current t value
        #  as the center
        center = intersectionPath.point((tIncrementAmount * x) / pathLength)
        GenericRenderer.globalRenderer.addPoint(center, 255, 255, 0)
        i = InfLine(m=slope, center=center)
        # Convert it to a bezier line
        l = i.to_svg_Line(center=center, length=intersectionLineLength)
        #GenericRenderer.globalRenderer.addLine(l, 255, 255, 255)

        # Intersect with the shape
        intersections = shape.intersect(l)
        if len(intersections) % 2 is not 0:
            s = "Number of intersections should always be even (its {} ). Make sure all shapes are closed shapes.".format(len(intersections))
            if debug:
                print(s)
            else:
                raise Exception(s)

        intersectionPoints = []
        # Get the intersection points and order them by location
        #  on the intersection line.
        for i in range(0, len( intersections )):
            p1 = l.point(intersections[i][1][0])
            intersectionPoints.append(p1)

        def dist1(p):
            return getDistanceBetweenPoints(p, l.start)

        intersectionPoints.sort(key=dist1)

        if debug:
            print("{} intersection points for this iteration.".format(len(intersectionPoints)))
            for i in intersectionPoints:
                GenericRenderer.globalRenderer.addPoint(i, 255, 0, 255)

        genericColors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255), (255, 255, 0), (255, 0, 255)]

        # Iterate through the intersections to find where to put stitches
        for i in range(0, len( intersectionPoints )/2):
            start = intersectionPoints[i*2]
            end = intersectionPoints[(i*2)+1]

            # Create a stitch for the given start and end points
            stitchLine = Line(start=start, end=end)

            stitchLines.append(stitchLine)

            # Draw debug lines
            if debug:
                GenericRenderer.globalRenderer.addLine(stitchLine, genericColors[i%6][0], genericColors[i%6][1], genericColors[i%6][2])
            else:
                GenericRenderer.globalRenderer.addLine(stitchLine, fillColor[0], fillColor[1], fillColor[2])



    return stitchLines

def invertLine(line):
    return Line(start=line.end, end=line.start)

def endWithinStart(l1, l2, dist):
    p1 = l1.end
    p2 = l2.start
    return math.sqrt( math.pow(p1.real - p2.real, 2) + math.pow(p1.imag - p2.imag, 2) ) <= dist

# Take all the stitches we created and actually make
#  a continuous set of commands for the machine to follow.
def createStitchRoutine(basicLines, fillColors, threadWidth=2):

    maxDist = math.sqrt(2 * math.pow(threadWidth,2))

    shapeLineGroups = []
    # For each set of lines corresponding to each SVG shape...
    for shapeLines in basicLines:
        # Find an order of lines that works with (relatively) minimum jumping.
        # This requires us to group lines by continuity
        lineGroups = []
        shapeLineGroups.append(lineGroups)

        for ungroupedLine in shapeLines:
            # Remove lines that are super short (less than 0.5mm)
            if ungroupedLine.length() < 5.0:
                continue

            # Does the line connect to any of the current groups?
            foundGroup = None
            for lineGroup in lineGroups:
                lastLine = lineGroup[-1]
                # Is the start of this line near the end of the last one?
                if endWithinStart(lastLine, ungroupedLine, maxDist):
                    foundGroup = lineGroup
                    break
                # Try switching the start and end points of the line.
                ungroupedLine = invertLine(ungroupedLine)
                if endWithinStart(lastLine, ungroupedLine, maxDist):
                    foundGroup = lineGroup

            # Did we find a group that works?
            if foundGroup is not None:
                foundGroup.append(ungroupedLine)
            else:
                # Start a new group
                newGroup = [ungroupedLine]
                lineGroups.append(newGroup)

    # Add color change, convert lines to stitches and add jump commands
    allStitches = []

    for i, shapeLineGroup in enumerate(shapeLineGroups):
        # Create the color change command.
        fillColor = fillColors[i]
        colorData = PES.getClosestColor(fillColor)

        colorChange = ColorChange(colorIndex=colorData[0])
        allStitches.append(colorChange)

        for singleLineGroup in shapeLineGroup:
            # Was the last command a stitch?
            if isinstance(allStitches[-1], Stitch):
                lastStitch = allStitches[-1]
                # Is the distance greater than the minimum?
                if endWithinStart(lastStitch.line, singleLineGroup[0], maxDist) is not True:
                    # Jump to the location of this shape.
                    jump = Stitch( line=Line(start=lastStitch.line.end,  end=singleLineGroup[0].start) )
                    jump.type = Stitch.TYPE_JUMP
                    allStitches.append(jump)

            for singleLine in singleLineGroup:
                # Do I really need to do two stitches per stitch or just one?
                # Maybe I can add different modes for this.
                s = Stitch(singleLine)
                allStitches.append(s)

    print("Created {} stitches.".format(len(allStitches)))
    return allStitches

def renderPECCommands(PECCommands):
    GenericRenderer.globalRenderer.clearAll()

    currentColor = ("None", 0,0,0)
    for command in PECCommands:
        if isinstance(command, Stitch):
            if command.type is Stitch.TYPE_JUMP:
                GenericRenderer.globalRenderer.addLine(command.line, 255, 255, 255)
            else:
                # Regular stitch
                GenericRenderer.globalRenderer.addLine(command.line, currentColor[1], currentColor[2], currentColor[3])
        if isinstance(command, ColorChange):
            currentColor = PES.colors[command.colorIndex]
