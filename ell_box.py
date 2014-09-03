#!/usr/bin/env python

# We will use the inkex module with the predefined Effect base class.
import inkex
# The simplestyle module provides functions for style parsing.
#from simplestyle import *
import simplestyle
from math import *
from collections import namedtuple
import traceback

objStyle = simplestyle.formatStyle(
    {'stroke': '#000000',
    'stroke-width': '0.1',
    'fill': 'none'
    })

def draw_SVG_square((w,h), (x,y), parent):
    attribs = {
        'style': objStyle,
        'height': str(h),
        'width': str(w),
        'x': str(x),
        'y': str(y)
    }
    inkex.etree.SubElement(parent, inkex.addNS('rect', 'svg'), attribs)

def draw_SVG_ellipse((rx, ry), center, parent, start_end=(0, 2*pi), transform=''):
    ell_attribs = {'style': objStyle,
        inkex.addNS('cx', 'sodipodi'): str(center.x),
        inkex.addNS('cy', 'sodipodi'): str(center.y),
        inkex.addNS('rx', 'sodipodi'): str(rx),
        inkex.addNS('ry', 'sodipodi'): str(ry),
        inkex.addNS('start', 'sodipodi'): str(start_end[0]),
        inkex.addNS('end', 'sodipodi'): str(start_end[1]),
        inkex.addNS('open', 'sodipodi'): 'true',  #all ellipse sectors we will draw are open
        inkex.addNS('type', 'sodipodi'): 'arc',
        'transform': transform
    }
    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), ell_attribs)


def draw_SVG_arc((rx, ry), x_axis_rot):
    arc_attribs = {'style': objStyle,
        'rx': str(rx),
        'ry': str(ry),
        'x-axis-rotation': str(x_axis_rot),
        'large-arc': '',
        'sweep': '',
        'x': '',
        'y': ''
        }
        #name='part'
    style = {'stroke': '#000000', 'fill': 'none'}
    drw = {'style':simplestyle.formatStyle(style),inkex.addNS('label','inkscape'):name,'d':XYstring}
    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), drw)
    inkex.addNS('', 'svg')

def draw_SVG_text((cx, cy), txt, parent):
    text = inkex.etree.Element(inkex.addNS('text', 'svg'))
    text.text = txt
    text.set('x', str(cx))
    text.set('y', str(cy))
    style = {'text-align': 'center', 'text-anchor': 'middle'}
    text.set('style', formatStyle(style))
    parent.append(text)


def SVG_move_to(x, y):
    return "M %d %d" % (x, y)


def SVG_line_to(x, y):
    return "L %d %d" % (x, y)


def SVG_arc_to(rx, ry, x, y):
    la = sw = 0
    return "A %d %d 0 %d %d" % (rx, ry, la, sw, x, y)


def SVG_path(components):
    return '<path d="' + ' '.join(components) + '">'


def SVG_curve(parent, segments, style, closed=True):
    #pathStr = 'M '+ segments[0]
    pathStr = ' '.join(segments)
    if closed:
        pathStr += ' z'
    attributes = {
      'style': style,
      'd': pathStr}
    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), attributes)

#draw an SVG line segment between the given (raw) points
def draw_SVG_line( (x1, y1), (x2, y2), parent):
    line_attribs = {'style': objStyle,
                    'd': 'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2)}

    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), line_attribs)


def _makeCurvedSurface(center, (w, h), cutDist, hCutCount, thickness, parent):
    wCutCount = int(floor(w / cutDist))
    if wCutCount % 2 == 0:
        wCutCount += 1    # make sure we have an odd number of cuts
    wCutDist = w / wCutCount
    cutLength = h / hCutCount - cutDist
    notchEdges = [0]

    for i in range(wCutCount):
        if i % 2 == 1:  # make a notch here
            inset = thickness
        else:
            inset = 0

        x1 = (center.x + i * wCutDist)
        notchEdges.append(x1)
        draw_SVG_line((x1, center.y + inset), (x1 + wCutDist, center.y + inset), parent)
        draw_SVG_line((x1, center.y + h - inset), (x1 + wCutDist, center.y + h - inset), parent)

        if i > 0:
            draw_SVG_line((x1, center.y), (x1, center.y + cutLength / 2), parent)
            draw_SVG_line((x1, center.y + h), (x1, center.y + h - cutLength / 2), parent)

            for j in range(hCutCount - 1):
                y = center.y + cutLength / 2 + cutDist + j * (cutLength + cutDist)
                draw_SVG_line((x1, y), (x1, y + cutLength), parent)

        x2 = (center.x + i * wCutDist + wCutDist / 2)
        for j in range(hCutCount):
            y = center.y + cutDist / 2 + j * (cutLength + cutDist)
            cl = cutLength
            if j == 0:  # first row
                y += inset
                cl -= inset
            elif j == hCutCount - 1:  # last row
                cl -= inset

            draw_SVG_line((x2, y), (x2, y + cl), parent)

    #draw_SVG_square((w, h), origin, parent)
    draw_SVG_line((center.x, center.y), (center.x, center.y + h), parent)
    draw_SVG_line((center.x + w, center.y), (center.x + w, center.y + h), parent)
    notchEdges.append(w)
    return notchEdges

class Ellipse():
    nrPoints = 1000 #used for piecewise linear circumference calculation (ellipse circumference is tricky to calculate)

    def __init__(self, w, h):
        self.h = h
        self.w = w
        EllipsePoint = namedtuple('EllipsePoint', 'angle coord cDist')
        self.ellData = [EllipsePoint(0, Coordinate(w/2, 0), 0)] # (angle, x, y, cumulative distance from angle = 0)
        angle = 0
        self.angleStep = 2 * pi / self.nrPoints
        #note: the render angle (ra) corresponds to the angle from the ellipse center (ca) according to:
        # ca = atan(w/h * tan(ra))
        for i in range(self.nrPoints):
            angle += self.angleStep
            prev = self.ellData[-1]
            x, y = w / 2 * cos(angle), h / 2 * sin(angle)
            self.ellData.append(EllipsePoint(angle, Coordinate(x, y), prev.cDist + sqrt((prev.coord.x - x)**2 + (prev.coord.y - y)**2)))
        self.circumference = self.ellData[-1].cDist
        inkex.debug("circ: %d" % self.circumference)

    def rAngle(self, a):
        """Convert an angle measured from ellipse center to the angle used to generate ellData (used for lookups)"""
        cf = 0
        if a > pi / 2:
            cf = pi
        if a > 3 * pi / 2:
            cf = 2 * pi
        return atan(self.w / self.h * tan(a)) + cf

    def coordinatesFromAngle(self, angle):
        """Coordinate of the point at angle."""
        # uses linear interpolation but just calculating it would be better
        i = int(angle / self.angleStep)
        p = angle % self.angleStep
        #l = self.ellData[i + 1][3] - self.ellData[i][3]
        c1 = self.ellData[i].coord
        c2 = self.ellData[i + 1].coord
        return c1 * p + c2 * (1 - p)

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
        #inkex.debug('angle: ' + str(a2) + ' rAngle: ' + str(self.rAngle(a2))+ ' idx: '+ str(i2))
        return len

    def angleFromDist(self, startAngle, relDist):
        """Returns the angle that you get when starting at startAngle and moving a distance (dist) in CCW direction"""
        si = int(self.rAngle(startAngle) / self.angleStep)
        p = self.rAngle(startAngle) % self.angleStep

        l = self.ellData[si + 1].cDist - self.ellData[si].cDist
        #inkex.debug("si %d, p %f, l %f" % (si, p, l))

        startDist = self.ellData[si].cDist + p * l

        absDist = relDist + startDist

        #check if we pass through zero
        #inkex.debug("relDist %f" % relDist)
        #dist -= p * l
        if absDist > self.ellData[-1].cDist:  # wrap around zero angle
            absDist -= self.ellData[-1].cDist
        #inkex.debug("abs dist %f" % absDist)

        # binary search
        iMin = 0
        iMax = self.nrPoints
        count = 0
        while iMax - iMin > 1:
            count += 1
            iHalf = iMin + (iMax - iMin) // 2
            if self.ellData[iHalf].cDist < absDist:
                iMin = iHalf
            else:
                iMax = iHalf

            #inkex.debug("min: %d, max:%d"%(iMin, iMax))
        stepDist = self.ellData[iMax].cDist - self.ellData[iMin].cDist
        #inkex.debug("angle:%f, angle/step:%f, step dist:%f, abs dist:%f, dist at last step%f"%(self.ellData[iMin][0], self.angleStep, stepDist, absDist, self.ellData[iMin].cDist))
        return self.ellData[iMin].angle + self.angleStep * (absDist - self.ellData[iMin].cDist)/stepDist


class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Coordinate(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Coordinate(self.x - other.x, self.y - other.y)

    def __mul__(self, factor):
        return Coordinate(self.x * factor, self.y * factor)

    def __div__(self, quotient):
        return Coordinate(self.x / quotient, self.y / quotient)


class EllipticalBox(inkex.Effect):
    """
    Creates a new layer with the drawings for a parametrically generaded box.
    """
    def __init__(self):
        inkex.Effect.__init__(self)

        self.OptionParser.add_option('-t', '--thickness', action = 'store',
          type = 'float', dest = 'thickness', default = '3.0',
          help = 'Material thickness')

        self.OptionParser.add_option('-x', '--width', action = 'store',
          type = 'float', dest = 'width', default = '3.0',
          help = 'Box width')

        self.OptionParser.add_option('-z', '--heigth', action = 'store',
          type = 'float', dest = 'heigth', default = '10.0',
          help = 'Box heigth')

        self.OptionParser.add_option('-y', '--depth', action = 'store',
          type = 'float', dest = 'depth', default = '3.0',
          help = 'Box depth')

        self.OptionParser.add_option('-d', '--cut_dist', action = 'store',
          type = 'float', dest = 'cut_dist', default = '1.5',
          help = 'Distance between cuts on the wrap around. Note that this value will change slightly to evenly fill up the available space.')

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


    def effect(self):
        """
        Draws as basic elliptical box, based on provided parameters
        """

        # convert units
        unit = 'mm'
        H = inkex.unittouu(str(self.options.heigth) + unit)
        W = inkex.unittouu(str(self.options.width) + unit)
        D = inkex.unittouu(str(self.options.depth) + unit)
        thickness = inkex.unittouu(str(self.options.thickness) + unit)
        cutDist = inkex.unittouu(str(self.options.cut_dist) + unit)
        cutNr = self.options.cut_nr

        # input sanity check
        error = False
        if min(H, W, D) == 0:
            inkex.errormsg(_('Error: Dimensions must be non zero'))
            error = True

        if cutNr < 1:
            inkex.errormsg(_('Error: Number of cuts should be at least 1'))
            error = True
        if error:
            exit()

        svg = self.document.getroot()
        docWidth = inkex.unittouu(svg.get('width'))
        docHeigth = inkex.unittouu(svg.attrib['height'])

        layer = inkex.etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'Elliptical Box')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

        # elliptical sides
        elCenter = Coordinate(docWidth / 2, 2 * D + H / 2)
        #draw_SVG_ellipse((W / 2, H / 2), elCenter, layer)
        #draw_SVG_ellipse((W / 2 + thickness, H / 2 + thickness), elCenter, layer, (0, pi/4))

        ell1 = Ellipse(W, H)
        ell2 = Ellipse(W + 2 * thickness, H + 2 * thickness)

        #body and lid
        lidAngleRad = self.options.lid_angle * 2 * pi / 360
        lidStartAngle = pi / 2 - lidAngleRad / 2
        lidEndAngle = pi / 2 + lidAngleRad / 2

        lidLength = ell1.distFromAngles(lidStartAngle, lidEndAngle)
        bodyLength = ell1.distFromAngles(lidEndAngle, lidStartAngle)
        inkex.debug('lid start: %f, end: %f, calc. end:%f'% (lidStartAngle*360/2/pi, lidEndAngle*360/2/pi, ell1.angleFromDist(lidStartAngle, lidLength)*360/2/pi))

        bodyNotches = _makeCurvedSurface(Coordinate(0, 0), (bodyLength, D), cutDist, cutNr, thickness, layer)
        lidNotches = _makeCurvedSurface(Coordinate(0, D), (lidLength, D), cutDist, cutNr, thickness, layer)

        for n in range(len(bodyNotches) - 1):
            if n % 2 == 0:
                outset = 0
            else:
                outset = thickness
            startA = ell1.angleFromDist(lidEndAngle, bodyNotches[n])
            endA = ell1.angleFromDist(lidEndAngle, bodyNotches[n + 1])
            draw_SVG_ellipse((W / 2 + outset, H / 2 + outset), elCenter, layer, (startA, endA))
            cfa1 = ell1.coordinatesFromAngle(endA)
            c1 = elCenter + cfa1
            c2 = elCenter + ell2.coordinatesFromAngle(endA)
            draw_SVG_line((c1.x, c1.y), (c2.x, c2.y), layer)

# Create effect instance and apply it.
effect = EllipticalBox()
effect.affect()
