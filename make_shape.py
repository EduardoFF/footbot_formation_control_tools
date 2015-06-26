#!/usr/bin/env python
"""
     make_shape - computes the poses for a given set of robots in order
                  to accomplish a geometric shape

    Copyright (C) 2014 Eduardo Feo
     
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import lcm
from waypointlist import timestamped_waypoint_list_t as waypoint_list
from waypointlist import timestamped_waypoint_t as waypoint
import sys
import time
import optparse
import math

valid_shapes = ['square', 'arc', 'triangle']
help_msg = dict()
help_msg['square'] = "help"
help_msg['arc'] = "help"
help_msg['triangle'] = "help"


def print_help_shapes(shape=None):
    global help_msg
    if not shape or shape not in valid_shapes:
        print "valid shapes: ",
        for s in valid_shapes:
            print s,
        print ""
    
    print help_msg[shape]

"""
make a square with a given number of robots and specified lattice
"""
def make_square(n_robots, side_len):
    if n_robots % 4 :
        print "Error: number of robots should be multiple of 4"
        print_help_shapes('square')
    points = [(0,0),(0,1),(1,0),(1,1)]

    m = (n_robots - 4)/4
    offset = 1.0/(m+1)
    for i in range(1,m+1):
        for j in range(4):
            (x1,y1) = points[j]
            (x2,y2) = points[(j+1)%4]
            (nx,ny) = (x1*offset + x2*(1-offset),
                       y1*offset + y2*(1-offset) )
            points.append((nx,ny))

    """ center in (0,0) """
    for i in range(len(points)):
        (x,y) = points[i]
        points[i] = (x-0.5, y-0.5)

    """ scale """
    for i in range(len(points)):
        (x,y) = points[i]
        points[i] = (x*side_len, y*side_len)
        
    return points
"""
make a square with a given number of robots and specified lattice
"""
def make_triangle(n_robots, side_len):
    if n_robots % 3 :
        print "Error: number of robots should be multiple of 3"
        print_help_shapes('triangle')
    points = [(0,0),(0,1),(0.5, math.atan(math.pi/3.0))]

    m = (n_robots - 3)/3
    offset = 1.0/(m+1)
    for i in range(1,m+1):
        for j in range(3):
            (x1,y1) = points[j]
            (x2,y2) = points[(j+1)%3]
            (nx,ny) = (x1*offset + x2*(1-offset),
                       y1*offset + y2*(1-offset) )
            points.append((nx,ny))

    """ center in (0,0) """
    cx, cy = math.cos(math.pi/3.0)/3.0, (1+math.sin(math.pi/3.0)/3.0)
    for i in range(len(points)):
        (x,y) = points[i]
        points[i] = (x-cx, y-cy)

    """ scale """
    for i in range(len(points)):
        (x,y) = points[i]
        points[i] = (x*side_len, y*side_len)
    

    
    return points


"""
do an arc with radius from alpha to beta (alpha < beta) 
"""
def make_arc(n_robots, radius, alpha, beta):
    points = []
    points.append( (radius*math.cos(math.radians(alpha)), radius*math.sin(math.radians(alpha))) )
    m = (n_robots - 2)
    if m > 0:
        dd = (beta - alpha) / (m+1 )
        for i in range(1,m+1):
            points.append( (radius*math.cos(math.radians(alpha+dd*i)), radius*math.sin(math.radians(alpha+dd*i))))
    points.append( (radius*math.cos(math.radians(beta)), radius*math.sin( math.radians(beta) )) )
    return points
    

def translate(P, (x,y)):
    for i in range(len(P)):
        (px,py) = P[i]
        P[i] = (px+x, py+y)
    return P
        

def point_to(P, (x,y)):
    angles = []
    for i in range(len(P)):
        (px,py) = P[i]
        (bx, by) = (x - px, y- py)
        (ax, ay) = (1,0)
        signed_angle = math.atan2(by,bx) - math.atan2(ay,ax)
        angles.append(math.degrees(signed_angle))
    return angles


def send_robots(ids, coordinates, ori, channel, timestamp):

    for i in range(len(ids)):
        robotid = ids[i]
        x,y = coordinates[i]


        """  --- no z --- """
        o = ori[i]
        channel = options.channel
        lc = lcm.LCM("udpm://239.255.76.67:7667?ttl=1") 

        msg = waypoint_list()
        msg.timestamp = float(timestamp)*1e3
        msg.robotid = robotid
        msg.n = 1
        wp = waypoint()

        wp.timestamp =float(timestamp)*1e3
        """ in mm """
        wp.position = [x*1000,y*1000,-1]
        wp.orientation = [o,0,0,0]
        wps=[wp]
        msg.waypoints = wps
        lc.publish(channel, msg.encode())

    

parser = optparse.OptionParser(usage="usage: %prog [options] id x y o",
                               version="%prog 1.0")

parser.add_option("-c", "--channel",
                  default="TARGET",
                  help="lcm channel")
parser.add_option("-t", "--timestamp",
                  default=0,
                  help="msg (and pose) timestamp as absolute time - requires sync clocks")

parser.add_option("-p", "--pos",
                  nargs=2,
                  default=None,
                  action='append',
                  help="")

parser.add_option("-r", "--reference",
                  nargs=2,
                  default=None,
                  action='append',
                  help="")


parser.add_option("-s", "--shape",
                  default='square',
                  help="")

parser.add_option("-l", "--length",
                  default=1,
                  help="")

parser.add_option("-a", "--alpha",
                  default=0,
                  help="")

parser.add_option("-b", "--beta",
                  default=180,
                  help="")


parser.add_option("-n", "--number",
                  default=0,
                  help="")


(options, args) = parser.parse_args()

if len(args) < 0:
    print "mandatory arguments missing (",len(args),")"
    parser.print_help()
    exit(-1)

if options.shape not in valid_shapes:
    print "ERROR: invalid shape"
    print_help_shapes()

pos = (0,0)
if options.pos == None:
    print "position not given, using (0,0)"
else:
    if not len(options.pos):
        print "position not given or invalid, using (0,0)"
    else:
        (x,y) = options.pos[0]
        pos = (float(x), float(y))
    
ref_point = (0,0)
if options.reference == None:
    print "reference position not given, using (0,0)"
else:
    if not len(options.reference):
        print "reference position not given or invalid, using (0,0)"
    else:
        (x,y) = options.reference[0]
        ref_point = (float(x), float(y))



print "SHAPE: ",options.shape
print "LENGTH",options.length
print "NUMBER OF ROBOTS",options.number
print "POSITION",pos
print "POINTING TO REFERENCE_POSITION",ref_point

robot_ids = [int(a) for a in args]
if len(robot_ids) != int(options.number):
    print "ERROR: invalid number of robot ids - expecting ",\
        int(options.number),"got",len(robot_ids)
    exit(1)

print "USING ROBOTS: ", robot_ids
P = []
angles = []
if options.shape == "square":
    l = float(options.length)
    n = int(options.number)
    P = make_square(n,l)
    P = translate(P, pos)
    angles = point_to(P, ref_point)
    print P
    print angles
if options.shape == "arc":
    rad = float(options.length)
    n = int(options.number)
    alpha = float(options.alpha)
    beta = float(options.beta)
    P = make_arc(n,rad,alpha, beta)
    P = translate(P, pos)
    angles = point_to(P, ref_point)
    print P
    print angles

if options.shape == "triangle":
    l = float(options.length)
    n = int(options.number)
    P = make_triangle(n,l)
    P = translate(P, pos)
    angles = point_to(P, ref_point)
    print P
    print angles


send_robots(robot_ids, P, angles,
            options.channel, options.timestamp)




exit(1)

