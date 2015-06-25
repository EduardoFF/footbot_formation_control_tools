#!/usr/bin/env python
"""
   waypoint_sendlist_bm - publish timestamped waypoint list from bonnmotion traces
   
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

parser = optparse.OptionParser(usage="usage: %prog [options] id x y o",
                               version="%prog 1.0")
parser.add_option("-c", "--channel",
                  default="TARGET",
                  help="lcm channel")
parser.add_option("-t", "--timestamp",
                  default=0,
                  help="msg (and pose) timestamp")

(options, args) = parser.parse_args()
if len(args) != 4:
    print "mandatory arguments missing (",len(args),")"
    parser.print_help()
    exit(-1)


robotid = int(args[0])
x = float(args[1])
y = float(args[2])
"""  --- no z --- """
o = float(args[3])
channel = options.channel
lc = lcm.LCM("udpm://239.255.76.67:7667?ttl=1") 

msg = waypoint_list()
msg.timestamp = float(options.timestamp)*1e3
msg.robotid = robotid
msg.n = 1
wp = waypoint()
""" in milliseconds """
print options.timestamp

wp.timestamp =float(options.timestamp)*1e3
""" in mm """
wp.position = [x,y,-1]
wp.orientation = [o,0,0,0]
wps=[wp]
msg.waypoints = wps
lc.publish(options.channel, msg.encode())
