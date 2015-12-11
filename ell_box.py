#!/usr/bin/env python

import Inkscape_helper.inkscape_helper as doc
from math import *
from collections import namedtuple

#Note: keep in mind that SVG coordinates start in the top-left corner i.e. with an inverted y-axis

# first define some SVG primitives (we do not use them all so a cleanup may be in order)
objStyle = doc.default_style
greenStyle = doc.mark_style


def _makeCurvedSurface(topLeft, w, h, cutSpacing, hCutCount, thickness, parent, invertNotches = False, centralRib = False):
    group = doc.group(parent)
    width = doc.Coordinate(w, 0)
    height = doc.Coordinate(0, h)
    wCutCount = int(floor(w / cutSpacing))
    if wCutCount % 2 == 0:
        wCutCount += 1    # make sure we have an odd number of cuts
    xCutDist = w / wCutCount
    xSpacing = doc.Coordinate(xCutDist, 0)
    ySpacing = doc.Coordinate(0, cutSpacing)
    cut = height / hCutCount - ySpacing
    plateThickness = doc.Coordinate(0, thickness)
    notchEdges = [0]
    topHCuts = []
    bottomHCuts = []

    for cutIndex in range(wCutCount):
        if (cutIndex % 2 == 1) != invertNotches:  # make a notch here
            inset = plateThickness
        else:
            inset = doc.Coordinate(0, 0)

        # A-column of cuts
        aColStart = topLeft + xSpacing * cutIndex
        notchEdges.append((aColStart - topLeft).x)

        if cutIndex > 0: # no cuts at x == 0
            doc.draw_line(group, aColStart, aColStart + cut / 2)
            for j in range(hCutCount - 1):
                pos = aColStart + cut / 2 + ySpacing + (cut + ySpacing) * j
                doc.draw_line(group, pos, pos + cut)
            doc.draw_line(group, aColStart + height - cut / 2, aColStart + height)

        # B-column of cuts, offset by half the cut length; these cuts run in the opposite direction
        bColStart = topLeft + xSpacing * cutIndex + xSpacing / 2
        for j in reversed(range(hCutCount)):
            end = bColStart + ySpacing / 2 + (cut + ySpacing) * j
            start = end + cut
            if centralRib and hCutCount % 2 == 0 and cutIndex % 2 == 1:
                holeTopLeft = start + (ySpacing - plateThickness - xSpacing) / 2
                if j == hCutCount // 2 - 1:
                    start -= plateThickness / 2
                    doc.draw_line(group, holeTopLeft + plateThickness + xSpacing, holeTopLeft + plateThickness)
                    doc.draw_line(group, holeTopLeft, holeTopLeft + xSpacing)
                elif j == hCutCount // 2:
                    end += plateThickness / 2
            if j == 0:  # first row
                end += inset
            elif j == hCutCount - 1:  # last row
                start -= inset
            doc.draw_line(group, start, end)

        #horizontal cuts (should be done last)
        topHCuts.append((aColStart + inset, aColStart + inset + xSpacing))
        bottomHCuts.append((aColStart + height - inset, aColStart + height - inset + xSpacing))

    # draw the outline
    for c in reversed(bottomHCuts):
        doc.draw_line(group, c[1], c[0])
    doc.draw_line(group, topLeft + height, topLeft)
    for c in topHCuts:
        doc.draw_line(group, c[0], c[1])
    doc.draw_line(group, topLeft + width, topLeft + width + height)

    notchEdges.append(w)
    return notchEdges

def _makeNotchedEllipse(center, ellipse, startAngle, thickness, notches, parent, invertNotches):
    startAngle += pi # rotate 180 degrees to put the lid on the topside
    c2 = ellipse.notchCoordinate(ellipse.rAngle(startAngle), thickness)
    a1 = atan2((ellipse.w/2 + thickness) * c2.y, (ellipse.h/2 + thickness) * c2.x)
    for n in range(1, len(notches) - 1):
        startA = ellipse.angleFromDist(startAngle, notches[n])
        endA = ellipse.angleFromDist(startAngle, notches[n + 1])
        c1 = center + ellipse.coordinateFromAngle(endA)
        c2 = ellipse.notchCoordinate(endA, thickness)

        a2 = atan2((ellipse.w/2 + thickness) * c2.y, (ellipse.h/2 + thickness) * c2.x)

        c2 += center
        if (n % 2 == 1) != invertNotches:
            doc.draw_ellipse(parent, ellipse.w / 2, ellipse.h / 2, center, (startA, endA))
            doc.draw_line(parent, c1, c2)
        else:
            doc.draw_ellipse(parent, ellipse.w / 2 + thickness, ellipse.h / 2 + thickness, center, (a1, a2))
            doc.draw_line(parent, c2, c1)

        a1 = a2

class Ellipse():
    nrPoints = 1000 #used for piecewise linear circumference calculation (ellipse circumference is tricky to calculate)
    # approximate circumfere: c = pi * (3 * (a + b) - sqrt(10 * a * b + 3 * (a ** 2 + b ** 2)))

    def __init__(self, w, h):
        self.h = h
        self.w = w
        EllipsePoint = namedtuple('EllipsePoint', 'angle coord cDist')
        self.ellData = [EllipsePoint(0, doc.Coordinate(w/2, 0), 0)] # (angle, x, y, cumulative distance from angle = 0)
        angle = 0
        self.angleStep = 2 * pi / self.nrPoints
        #note: the render angle (ra) corresponds to the angle from the ellipse center (ca) according to:
        # ca = atan(w/h * tan(ra))
        for i in range(self.nrPoints):
            angle += self.angleStep
            prev = self.ellData[-1]
            x, y = w / 2 * cos(angle), h / 2 * sin(angle)
            self.ellData.append(EllipsePoint(angle, doc.Coordinate(x, y), prev.cDist + hypot(prev.coord.x - x, prev.coord.y - y)))
        self.circumference = self.ellData[-1].cDist
        #inkex.debug("circ: %d" % self.circumference)

    def rAngle(self, a):
        """Convert an angle measured from ellipse center to the angle used to generate ellData (used for lookups)"""
        cf = 0
        if a > pi / 2:
            cf = pi
        if a > 3 * pi / 2:
            cf = 2 * pi
        return atan(self.w / self.h * tan(a)) + cf

    def coordinateFromAngle(self, angle):
        """Coordinate of the point at angle."""
        return doc.Coordinate(self.w / 2 * cos(angle), self.h / 2 * sin(angle))

    def notchCoordinate(self, angle, notchHeight):
        """Coordinate for a notch at the given angle. The notch is perpendicular to the ellipse."""
        angle %= (2 * pi)
        #some special cases to avoid divide by zero:
        if angle == 0:
            return (0, doc.Coordinate(self.w / 2 + notchHeight, 0))
        elif angle == pi:
            return (pi, doc.Coordinate(-self.w / 2 - notchHeight, 0))
        elif angle == pi / 2:
            return(pi / 2, doc.Coordinate(0, self.h / 2 + notchHeight))
        elif angle == 3 * pi / 2:
            return(3 * pi / 2, doc.Coordinate(0, -self.h / 2 - notchHeight))

        x = self.w / 2 * cos(angle)
        derivative = self.h / self.w * -x / sqrt((self.w / 2) ** 2 - x ** 2)
        if angle > pi:
            derivative = -derivative

        normal = -1 / derivative
        nAngle = atan(normal)
        if angle > pi / 2 and angle < 3 * pi / 2:
            nAngle += pi

        nCoordinate = self.coordinateFromAngle(angle) + doc.Coordinate(cos(nAngle), sin(nAngle)) * notchHeight
        return nCoordinate


    def distFromAngles(self, a1, a2):
        """Distance accross the surface from point at angle a2 to point at angle a2. Measured in CCW sense."""
        i1 = int(self.rAngle(a1) / self.angleStep)
        p1 = self.rAngle(a1) % self.angleStep
        l1 = self.ellData[i1 + 1].cDist - self.ellData[i1].cDist
        i2 = int(self.rAngle(a2) / self.angleStep)
        p2 = self.rAngle(a2) % self.angleStep
        l2 = self.ellData[i2 + 1].cDist - self.ellData[i2].cDist
        if a1 <= a2:
            len = self.ellData[i2].cDist - self.ellData[i1].cDist + l2 * p2 - l1 * p1
        else:
            len = self.circumference + self.ellData[i2].cDist - self.ellData[i1].cDist
        return len

    def angleFromDist(self, startAngle, relDist):
        """Returns the angle that you get when starting at startAngle and moving a distance (dist) in CCW direction"""
        si = int(self.rAngle(startAngle) / self.angleStep)
        p = self.rAngle(startAngle) % self.angleStep

        l = self.ellData[si + 1].cDist - self.ellData[si].cDist

        startDist = self.ellData[si].cDist + p * l

        absDist = relDist + startDist

        if absDist > self.ellData[-1].cDist:  # wrap around zero angle
            absDist -= self.ellData[-1].cDist

        iMin = 0
        iMax = self.nrPoints
        count = 0
        while iMax - iMin > 1:  # binary search
            count += 1
            iHalf = iMin + (iMax - iMin) // 2
            if self.ellData[iHalf].cDist < absDist:
                iMin = iHalf
            else:
                iMax = iHalf

        stepDist = self.ellData[iMax].cDist - self.ellData[iMin].cDist
        return self.ellData[iMin].angle + self.angleStep * (absDist - self.ellData[iMin].cDist)/stepDist


class EllipticalBox(doc.Effect):
    """
    Creates a new layer with the drawings for a parametrically generaded box.
    """
    def __init__(self):
        doc.Effect.__init__(self)
        self.knownUnits = ['in', 'pt', 'px', 'mm', 'cm', 'm', 'km', 'pc', 'yd', 'ft']

        self.OptionParser.add_option('-u', '--unit', action = 'store',
          type = 'string', dest = 'unit', default = 'mm',
          help = 'Unit, should be one of ')

        self.OptionParser.add_option('-t', '--thickness', action = 'store',
          type = 'float', dest = 'thickness', default = '3.0',
          help = 'Material thickness')

        self.OptionParser.add_option('-x', '--width', action = 'store',
          type = 'float', dest = 'width', default = '3.0',
          help = 'Box width')

        self.OptionParser.add_option('-z', '--height', action = 'store',
          type = 'float', dest = 'height', default = '10.0',
          help = 'Box height')

        self.OptionParser.add_option('-y', '--depth', action = 'store',
          type = 'float', dest = 'depth', default = '3.0',
          help = 'Box depth')

        self.OptionParser.add_option('-d', '--cut_dist', action = 'store',
          type = 'float', dest = 'cut_dist', default = '1.5',
          help = 'Distance between cuts on the wrap around. Note that this value will change slightly to evenly fill up the available space.')

        self.OptionParser.add_option('--auto_cut_dist', action = 'store',
          type = 'inkbool', dest = 'auto_cut_dist', default = 'false',
          help = 'Automatically set the cut distance based on the curvature.')

        self.OptionParser.add_option('-c', '--cut_nr', action = 'store',
          type = 'int', dest = 'cut_nr', default = '3',
          help = 'Number of cuts across the depth of the box.')

        self.OptionParser.add_option('-a', '--lid_angle', action = 'store',
          type = 'float', dest = 'lid_angle', default = '120',
          help = 'Angle that forms the lid (in degrees, measured from centerpoint of the ellipse)')

        self.OptionParser.add_option('-b', '--body_ribcount', action = 'store',
          type = 'int', dest = 'body_ribcount', default = '0',
          help = 'Number of ribs in the body')

        self.OptionParser.add_option('-l', '--lid_ribcount', action = 'store',
          type = 'int', dest = 'lid_ribcount', default = '0',
          help = 'Number of ribs in the lid')

        self.OptionParser.add_option('-n', '--invert_lid_notches', action = 'store',
          type = 'inkbool', dest = 'invert_lid_notches', default = 'false',
          help = 'Invert the notch pattern on the lid (to prevent sideways motion)')

        self.OptionParser.add_option('-r', '--central_rib_lid', action = 'store',
          type = 'inkbool', dest = 'centralRibLid', default = 'false',
          help = 'Create a central rib in the lid')

        self.OptionParser.add_option('-R', '--central_rib_body', action = 'store',
          type = 'inkbool', dest = 'centralRibBody', default = 'false',
          help = 'Create a central rib in the body')

    def effect(self):
        """
        Draws as basic elliptical box, based on provided parameters
        """

        # input sanity check
        error = False
        if min(self.options.height, self.options.width, self.options.depth) == 0:
            inkex.errormsg('Error: Dimensions must be non zero')
            error = True

        if self.options.cut_nr < 1:
            inkex.errormsg('Error: Number of cuts should be at least 1')
            error = True

        if (self.options.centralRibLid or self.options.centralRibBody) and self.options.cut_nr % 2 == 1:
            inkex.errormsg('Error: Central rib is only valid with an even number of cuts')
            error = True

        if self.options.unit not in self.knownUnits:
            inkex.errormsg('Error: unknown unit. '+ self.options.unit)
            error = True

        if error:
            exit()


        # convert units
        unit = self.options.unit
        H = self.unittouu(str(self.options.height) + unit)
        W = self.unittouu(str(self.options.width) + unit)
        D = self.unittouu(str(self.options.depth) + unit)
        thickness = self.unittouu(str(self.options.thickness) + unit)
        cutSpacing = self.unittouu(str(self.options.cut_dist) + unit)
        cutNr = self.options.cut_nr

        svg = self.document.getroot()
        docWidth = self.unittouu(svg.get('width'))
        docHeigh = self.unittouu(svg.attrib['height'])

        layer = doc.layer(svg, 'Elliptical Box')

        ell = Ellipse(W, H)

        #body and lid
        lidAngleRad = self.options.lid_angle * 2 * pi / 360
        lidStartAngle = pi / 2 - lidAngleRad / 2
        lidEndAngle = pi / 2 + lidAngleRad / 2

        lidLength = ell.distFromAngles(lidStartAngle, lidEndAngle)
        bodyLength = ell.distFromAngles(lidEndAngle, lidStartAngle)

        # do not put elements right at the edge of the page
        xMargin = 3
        yMargin = 3
        bodyNotches = _makeCurvedSurface(doc.Coordinate(xMargin, yMargin), bodyLength, D, cutSpacing, cutNr, thickness, layer, False, self.options.centralRibBody)
        lidNotches = _makeCurvedSurface(doc.Coordinate(xMargin, D + 2 * yMargin), lidLength, D, cutSpacing, cutNr, thickness, layer, not self.options.invert_lid_notches, self.options.centralRibLid)
        a1 = lidEndAngle

        # create elliptical sides
        sidesGrp = doc.group(layer)

        elCenter = doc.Coordinate(xMargin + thickness + W / 2, 2 * D + H / 2 + thickness + 3 * yMargin)

        # indicate the division between body and lid
        if self.options.invert_lid_notches:
            doc.draw_line(sidesGrp, elCenter, elCenter + ell.coordinateFromAngle(ell.rAngle(lidStartAngle + pi)), greenStyle)
            doc.draw_line(sidesGrp, elCenter, elCenter + ell.coordinateFromAngle(ell.rAngle(lidEndAngle + pi)), greenStyle)
        else:
            angleA = ell.angleFromDist(lidStartAngle, lidNotches[2])
            angleB = ell.angleFromDist(lidStartAngle, lidNotches[-2])

            doc.draw_line(sidesGrp, elCenter, elCenter + ell.coordinateFromAngle(angleA + pi), greenStyle)
            doc.draw_line(sidesGrp, elCenter, elCenter + ell.coordinateFromAngle(angleB + pi), greenStyle)

        _makeNotchedEllipse(elCenter, ell, lidEndAngle, thickness, bodyNotches, sidesGrp, False)
        _makeNotchedEllipse(elCenter, ell, lidStartAngle, thickness, lidNotches, sidesGrp, not self.options.invert_lid_notches)

        # ribs
        spacer = doc.Coordinate(0, 10)
        innerRibCenter = doc.Coordinate(xMargin + thickness + W / 2, 2 * D +  1.5 * (H + 2 *thickness) + 4 * yMargin)
        innerRibGrp = doc.group(layer)

        outerRibCenter = doc.Coordinate(2 * xMargin + 1.5 * (W + 2 * thickness) , 2 * D + 1.5 * (H + 2 * thickness) + 4 * yMargin)
        outerRibGrp = doc.group(layer)


        if self.options.centralRibLid:

            _makeNotchedEllipse(innerRibCenter, ell, lidStartAngle, thickness, lidNotches, innerRibGrp, False)
            _makeNotchedEllipse(outerRibCenter, ell, lidStartAngle, thickness, lidNotches, outerRibGrp, True)

        if self.options.centralRibBody:
            _makeNotchedEllipse(innerRibCenter + spacer, ell, lidEndAngle, thickness, bodyNotches, innerRibGrp, False)
            _makeNotchedEllipse(outerRibCenter + spacer, ell, lidEndAngle, thickness, bodyNotches, outerRibGrp, True)

        if self.options.centralRibLid or self.options.centralRibBody:
            doc.draw_text(sidesGrp, elCenter, 'side (duplicate this)')
            doc.draw_text(innerRibGrp, innerRibCenter, 'inside rib')
            doc.draw_text(outerRibGrp, outerRibCenter, 'outside rib')

# Create effect instance and apply it.
effect = EllipticalBox()
effect.affect()
