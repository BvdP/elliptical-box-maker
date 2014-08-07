#!/usr/bin/env python

# We will use the inkex module with the predefined Effect base class.
import inkex
# The simplestyle module provides functions for style parsing.
#from simplestyle import *
import simplestyle
from math import *

objStyle = simplestyle.formatStyle(
    {'stroke'  : '#000000',
    'stroke-width'  : '0.1',
    'fill'          : 'none'
    })

def draw_SVG_square((w,h), (x,y), parent):
    attribs = {
        'style'     : objStyle,
        'height'    : str(h),
        'width'     : str(w),
        'x'         : str(x),
        'y'         : str(y)
    }
    circ = inkex.etree.SubElement(parent, inkex.addNS('rect','svg'), attribs )

def draw_SVG_ellipse((rx, ry), (cx, cy), parent, start_end=(0, 2*pi), transform='' ):
    ell_attribs = {'style':objStyle,
        inkex.addNS('cx','sodipodi')        :str(cx),
        inkex.addNS('cy','sodipodi')        :str(cy),
        inkex.addNS('rx','sodipodi')        :str(rx),
        inkex.addNS('ry','sodipodi')        :str(ry),
        inkex.addNS('start','sodipodi')     :str(start_end[0]),
        inkex.addNS('end','sodipodi')       :str(start_end[1]),
        inkex.addNS('open','sodipodi')      :'true',    #all ellipse sectors we will draw are open
        inkex.addNS('type','sodipodi')      :'arc',
        'transform'                         :transform
    }
    ell = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), ell_attribs )


def draw_SVG_arc((rx, ry), x_axis_rot):
    arc_attribs = {'style': objStyle,
        'rx' : str(rx),
        'ry' : str(ry),
        'x-axis-rotation': str(x_axis_rot),
        'large-arc': '',
        'sweep': '',
        'x': '',
        'y': ''
        }
        #name='part'
    style = { 'stroke': '#000000', 'fill': 'none' }
    drw = {'style':simplestyle.formatStyle(style),inkex.addNS('label','inkscape'):name,'d':XYstring}
    inkex.etree.SubElement(parent, inkex.addNS('path','svg'), drw )
    inkex.addNS('','svg')


def SVG_arc_to():
    pass

def SVG_line_segment():
    pass

def SVG_curve(parent, segments, style, closed=True):
    pathStr = 'M '+ segments[0]
    if closed:
        pathStr += ' z'
    attributes = {
      'style': simplestyle.formatStyle(style),
      'd'    : pathStr}
    path = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), attributes )

#draw an SVG line segment between the given (raw) points
def draw_SVG_line( (x1, y1), (x2, y2),  name, parent):
    line_attribs = {'style' : objStyle,
                    inkex.addNS('label','inkscape') : name,
                    'd' : 'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2)}

    line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )

class Ellipse():
    nrPoints = 1000 #used for piecewise linear circumference calculation (ellipse circumference is tricky to calculate)

    def __init__(self, w, h):
        self.h = h
        self.w = w
        inkex.debug('dimensions ' + str(w) + ' ' + str(h))
        self.ellData = [(0, w/2, 0, 0)] # (angle, x, y, cumulative distance from angle = 0)
        angle = 0
        self.angleStep = 2 * pi / self.nrPoints
        #note: the render angle (ra) corresponds to the angle from the ellipse center (ca) according to:
        # ca = atan(w/h * tan(ra))
        for i in range(self.nrPoints):
            angle += self.angleStep
            prev = self.ellData[-1]
            x, y = w/2 * cos(angle), h/2 * sin(angle)
            self.ellData.append((angle, x, y, prev[3] + sqrt((prev[1] - x)**2 + (prev[2] - y)**2)))
        self.circumference = self.ellData[-1][3]

    def rAngle(self, a):
        """Convert an angle measured from ellipse center to the angle used to generate ellData (used for lookups)"""
        cf = 0
        if a > pi / 2 :
            cf = pi
        if a > 3 * pi / 2:
            cf = 2 * pi

        return atan(self.w / self.h * tan(a)) + cf

    def distFromAngles(self, a1, a2):
        """Distance accross the surface from point at angle a2 to point at angle a2. Measured in CCW sense."""
        i1 = int(self.rAngle(a1) / self.angleStep)
        i2 = int(self.rAngle(a2) / self.angleStep)
        if a1 < a2:
            len = self.ellData[i2][3] - self.ellData[i1][3]
        else:
            len = self.circumference + self.ellData[i2][3] - self.ellData[i1][3]
        inkex.debug('angle: ' + str(a2) + ' rAngle: ' + str(self.rAngle(a2))+ ' idx: '+ str(i2))
        return len

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

        self.OptionParser.add_option('-c', '--cut_length', action = 'store',
          type = 'float', dest = 'cut_length', default = '30.0',
          help = 'Length of cuts on the wrap around.')

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
        W = self.options.width
        H = self.options.heigth
        D = self.options.depth
        thickness = self.options.thickness

        # input sanity check
        error = False
        if min(H, W, D)==0:
            inkex.errormsg(_('Error: Dimensions must be non zero'))
            error = True

        if error: exit()

        # convert units
        unit = 'mm'
        H = inkex.unittouu( str(H)  + unit )
        W = inkex.unittouu( str(W)  + unit )
        D = inkex.unittouu( str(D)  + unit )
        cutDist = inkex.unittouu( str(self.options.cut_dist)  + unit )
        cutLength = inkex.unittouu( str(self.options.cut_length)  + unit )

        svg = self.document.getroot()
        docWidth  = inkex.unittouu(svg.get('width'))
        docHeigth = inkex.unittouu(svg.attrib['height'])

        layer = inkex.etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'Elliptical Box')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

        # elliptical sides
        elCenter = (docWidth / 2, docHeigth / 2)
        draw_SVG_ellipse((W / 2, H / 2), elCenter, layer)
        draw_SVG_ellipse((W / 2 + thickness, H / 2 + thickness), elCenter, layer)
        el = Ellipse(W, H)

        #body and lid
        lidAngleRad = self.options.lid_angle * 2 * pi / 360
        lidStartAngle = pi / 2 - lidAngleRad / 2
        lidEndAngle = pi / 2 + lidAngleRad / 2
        lidLength = el.distFromAngles(lidStartAngle, lidEndAngle)
        lidCutCount = floor(lidLength / cutDist)
        if lidCutCount % 2 == 0:
            lidCutCount += 1    # make sure we have an odd number of cuts
        lidCutDist = lidLength / lidCutCount
        bodyLength = el.distFromAngles(lidEndAngle, lidStartAngle)
        bodyCutCount = int(floor(bodyLength / cutDist))
        if bodyCutCount % 2 == 0:
            bodyCutCount += 1   # same as for the lid: odd number
        bodyCutDist = bodyLength / bodyCutCount

        bodyOrigin = (0, 0)
        for i in range(bodyCutCount):
            x = (bodyOrigin[0] + i * bodyCutDist)
            draw_SVG_line((x, bodyOrigin[1]),(x, bodyOrigin[1] + cutLength/2),'',layer)
        draw_SVG_square((bodyLength, D), bodyOrigin, layer)
        lidOrigin = (0, D)
        draw_SVG_square((lidLength, D), lidOrigin, layer)

        inkex.debug('lid %d body %d'%(lidLength, bodyLength))
        #inkex.debug(inkex.uutounit(el.distFromAngles(5 * pi/6, pi/6), 'cm'))
        #Create text element
        # text = inkex.etree.Element(inkex.addNS('text','svg'))
        # text.text = 'Hello %s!' % (what)
        # text.set('x', str(docWidth / 2))
        # text.set('y', str(docHeight / 2))
        # style = {'text-align' : 'center', 'text-anchor': 'middle'}
        # text.set('style', formatStyle(style))
        # layer.append(text)

# Create effect instance and apply it.
effect = EllipticalBox()
effect.affect()