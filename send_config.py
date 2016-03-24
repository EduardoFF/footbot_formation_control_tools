#!/usr/bin/env python
"""
   send_config.py - publish config msg using lcm
   
    Copyright (C) 2015 Eduardo Feo
     
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
from configmsg import config_msg_t as config_msg
import sys
import time
from optparse import OptionParser


if __name__ == '__main__':
    """ main """
    parser = OptionParser(usage="usage: %prog [options] filename",
                                   version="%prog 1.0")
    parser.add_option("-f", "--file",
                      default=None,
                      help="file containing a config msg per line")

    (options, args) = parser.parse_args()

    lc = lcm.LCM("udpm://239.255.76.67:7667?ttl=1") 


    if options.file != None:
        for line in open(options.file).readlines():
            s = line.split()
            rid = int(s[0])
            timestamp = int(s[1])
            cmd = " ".join(s[2:])
            msg = config_msg()
            msg.robotid = rid
            msg.timestamp = timestamp
            msg.msg = cmd
            lc.publish("CONFIG", msg.encode())
    else:
        if len(args) < 3:
            print "Invalid number of arguments ", len(sys.argv)
            print args
            exit(1)
        rid = int(args[0])
        timestamp = int(args[1])
        cmd = " ".join(args[2:])
        msg = config_msg()
        msg.robotid = rid
        msg.timestamp = timestamp
        msg.msg = cmd
        lc.publish("CONFIG", msg.encode())


