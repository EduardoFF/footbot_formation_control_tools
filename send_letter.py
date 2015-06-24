#!/usr/bin/python
import sys
import lcm as lcmengine
from poselcm import pose_list_t, pose_t
from xml.dom import minidom
import time
import threading
import math
import os
import re
import numpy
import hungarian
from waypointlist import timestamped_waypoint_list_t as waypoint_list
from waypointlist import timestamped_waypoint_t as waypoint

import tty, termios
""" if we use simulation, we create
    a socket to synchronize ns3 and the solver
    """
sim_socket_addr = '/tmp/rnp_sim.socket'

nodes = {}
node_by_id = {}

robots = []

USE_LAP =   True

lcm = None
subscription = None
done = False

isSim = False
current_sim_time = None
current_sim_time_LOCK = threading.Lock()

SCALE=0.5

OX=0
OY=0
hdy = 0.4
h_ox = 4.8
h_oy = -1.2
home = [(h_ox*(1.0/SCALE),(h_oy+j*hdy)*(1.0/SCALE)) for j in  range(12)]

letters = {}
""":-) """
smiley=[]
last_sent = {}
def getCh():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def getTime():
    if not isSim:
        return time.time()
    else:
        rettime = None
        current_sim_time_LOCK.acquire()
        rettime = current_sim_time
        current_sim_time_LOCK.release()
        return rettime

def send_smiley_1():
    wps= [ (0.5,2),\
          (1,1.5),\
          (2,1),\
          (3,1),\
          (4,1.5),\
          (4.5,2),\
          (2.5,3),\
          (1,4.5),\
          (4,4.5)]
    send_wps(wps)


def send_smiley_2():
    wps= [ (0.5,2),\
          (1,1.5),\
          (2,1),\
          (3,1),\
          (4,1.5),\
          (4.5,2),\
          (2.5,3),\
          (1,4.5),\
          (1,5.2),\
          (4,4.5),\
         (4,5.2)]
    send_wps(wps)

def send_smiley_3():
    wps= [ (0.5,2),\
          (1,1.5),\
          (2,1),\
          (3,1),\
          (4,1.5),\
          (4.5,2),\
          (2.5,2.7),\
          (2.5,3.3),\
          (1,4.5),\
          (1,5.2),\
          (4,4.5),\
         (4,5.2)]
    send_wps(wps)


class Node:
    def __init__(self, nid):
        self.nid = nid
        self.x = 0
        self.y = 0
    def set_pos(self, _x,_y):
        self.x = _x
        self.y = _y

def my_track_handler(channel, data):
    global nodes
    verbose=False
    msg = pose_list_t.decode(data)
    if verbose:
        print("Received message on channel \"%s\"" % channel)
        print("number of posess: %d" % len(msg.poses))
        print("")
    for pose in msg.poses:
        #pose = pose_t.decode(p)
        [x,y,z] = pose.position
        rid = pose.robotid
        if rid in robots:
            nodes[rid].set_pos(x,y)
#        if robot_to_ix.has_key(rid):
 #           rix = robot_to_ix[rid]
            if verbose:
                print "robot ",rid,"  pos ",x,y
#            nodes[rix].set_pos(x, y)

def configureScenario(cfile):
    global robots, sn_ix, bs_ix,rn_ix
    global ip_to_robot, mac_to_robot

    xmldoc = minidom.parse(cfile)
    itemlist = xmldoc.getElementsByTagName('robot') 
    print len(itemlist)
    for s in itemlist :
        rid = int(s.attributes['robotid'].value)
        n = Node(rid)
        nodes[rid]=n
        robots.append(rid)
def init_lcm():
    global lcm, subscription
    lcm = lcmengine.LCM("udpm://239.255.76.67:7667?ttl=1")
    subscription = lcm.subscribe("TRACK", my_track_handler)

def listen():
    global done
    while True:
        lcm.handle_timeout(1000)
        if done:
            return
        #print "nomsg"

def dist( (xi,yi), (xj,yj) ):
    return ((xi-xj)**2 + (yi-yj)**2)**0.5


def greedy_AP(relays, locs):
    robot_to_loc = {}
    loc_to_robot = {}
    free_relays = list(relays.keys())
    for (loc_ix,loc_xy) in locs.items():
        """ find the closest one """
        closest_rix = -1
        closest_dist = 100000
        (rpos_x,rpos_y)=loc_xy
        for rix in free_relays:
            (nx,ny) = relays[rix]
            d = dist( (nx,ny), (rpos_x,rpos_y))
            if closest_rix == -1 or d < closest_dist:
                closest_rix = rix
                closest_d = d
            print "sending ",closest_rix,"to",loc_xy
        robot = closest_rix
        robot_to_loc[robot] = loc_ix
        loc_to_robot["r%d"%(loc_ix)] = closest_rix
        free_relays.remove(closest_rix)
    return loc_to_robot,robot_to_loc

def LAP(relays, locs):
    """ return values """
    robot_to_loc = {}
    loc_to_robot={}
    """ we need to make arrays and then retrieve the 
    key values """
    locix_to_key = {}
    relayix_to_key={}
    relay_l = []
    loc_l = []
    if len(relays) < len(locs):
        print "WTF? locs > relays", len(locs), len(relays)
        return loc_to_robot, robot_to_loc
    n=max(len(relays),len(locs))
    a = numpy.zeros(shape=(n,n))
    i=0
    for (rix, (rpos_x, rpos_y)) in relays.items():
        relayix_to_key[i] = rix
        j=0
        for (lix, (loc_x,loc_y)) in locs.items():
            if i==0:
                locix_to_key[j]=lix
            d = dist( (rpos_x,rpos_y), (loc_x,loc_y))
            a[i][j]=d
            j+=1
        """ fill remaining with 0 """
        while j<n:
            a[i][j] = 0
            j+=1
        i+=1
    print "doing LAP nrelays ",len(relays),"nlocs",len(locs)
    print a
    [col, row] = hungarian.lap(a)
    print "relay ",relays
    print "locs ",locs
    print "col ",col
    print "row ",row
    for i in range(n):
        rix=relayix_to_key[i]
        if col[i] >= len(locs):
            print "warning: THIS SHOULD NOT HAPPEN"
            continue
        locix=locix_to_key[col[i]]
        robot_to_loc[rix]=locix
        loc_to_robot[locix] = rix

    return loc_to_robot,robot_to_loc

def move_letter(dx,dy):
    global last_sent
    now_sent = {}
    for (rid, (x,y)) in last_sent.items():
        nx = x+dx
        ny = y+dy
        msg = waypoint_list()
        msg.timestamp = int(getTime() * 1e6)
        msg.robotid = rid
        msg.n = 1
        wps=[]
        wp = waypoint()
        wp.timestamp = 0
        wp.position = [1000*nx,1000*ny,0]
        wp.orientation = [0,0,0,1]
        wps=[wp]
        msg.waypoints = wps
        print "sending ",rid,"to",nx,ny
        now_sent[rid]=(nx,ny)
        lcm.publish("TARGET", msg.encode())
    last_sent = now_sent

def send_letter(letter):
    global  letters
    wps = letters[letter]
    if not len(wps):
        return
    send_wps(wps)

def send_wps(wps):
    global  last_sent
    """ assign relay to positions, if any"""
    robot_to_loc = {}
    loc_to_robot={}
    """ locs: loc_ix -> (x,y) """
    locs={}

    dummy=[]
    """ HACK ALERT!: add dummy locs """
    dummy.append((-2,-2))
    dummy.append((-2, 6))
#    dummy.append(( 5,-2))
#    dummy.append(( 5, 6))
    dummy.append((-2.5,-2))
    dummy.append((-2.5, 6))
#    dummy.append(( 6,-2))
#    dummy.append(( 6, 6))
    dummy.append((-3,-2))
    dummy.append((-3, 6))
    if len(wps) > len(robots):
        print "not enough robots: need ",len(wps),"have",len(robots)
        return
    if len(wps) < len(robots):
        j=0
        while len(wps) < len(robots):
            wps.append( dummy[j])
            j+=1
    for i in range(len(wps)):
        """ candidate loc index """
        rpos = wps[i]
        (rpos_x,rpos_y)=rpos
        locs[i]=(rpos_x*SCALE, rpos_y*SCALE)
    """ rns: node_id -> (x,y) """
    rns={}
    for rix in robots:
        nx,ny = nodes[rix].x, nodes[rix].y
        rns[rix]=(nx,ny)

    if USE_LAP:
        loc_to_robot,robot_to_loc = LAP(rns,locs)
    else:
        """ greedy assignment """
        loc_to_robot,robot_to_loc = greedy_AP(rns,locs)

    print "assignemnt loc_to_robot: ", loc_to_robot
    print "assignemnt robot to loc ", robot_to_loc
    last_sent = {}
    for (rid, loc) in robot_to_loc.items():
        (x,y) = locs[loc]
        msg = waypoint_list()
        msg.timestamp = int(getTime() * 1e6)
        msg.robotid = rid
        msg.n = 1
        wps=[]
        wp = waypoint()
        wp.timestamp = 0
        wp.position = [1000*x,1000*y,0]
        wp.orientation = [0,0,0,1]
        wps=[wp]
        msg.waypoints = wps
        print "sending ",rid,"to",x,y
        """ if is not dummy (NOTE: dummy assumed to be negative x)"""
        if x>-0.5:
            last_sent[rid]=(x,y)
        lcm.publish("TARGET", msg.encode())


def makeSimSocket():
    global sim_sock, sim_socket_addr
    try:
        os.unlink(sim_socket_addr)
    except OSError:
        if os.path.exists(sim_socket_addr):
            raise
    sim_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    """ Bind the socket to the port"""
    print >>sys.stderr, 'starting up on %s' % sim_socket_addr
    sim_sock.bind(sim_socket_addr)

    """ Listen for incoming connections """
    sim_sock.listen(1)


def load_letters(cfile):
    global letters
    f = open(cfile)
    lines = f.readlines()
    ix=0
    row=0
    coos = []
    for line in lines:
        if len(line)==1:
            ix+=1
            coos=list()
            row=0
            continue
        if len(line) != 5:
            print "wtf line has length ",len(line),line
            continue
        for col in range(4):
            if line[col] == '#':
                coos.append((col,4-row))
        row+=1
        if row==5:
            c=chr(ord('a')+ix)
            letters[c] = coos
    print "letters loaded "
    for (l, wps) in  letters.items():
        print l,":", wps, len(wps)


def print_letters_by_size():
    by_size={}
    for (c,wps) in letters.items():
        if by_size.has_key(len(wps)):
            by_size[len(wps)].append(c)
        else:
            by_size[len(wps)]=[c]
    print by_size


if __name__ == "__main__":
    scenario = sys.argv[1]

    configureScenario(scenario)
    n = len(robots)
    AX = 5
    AY = 5

    init_lcm()
    tid = threading.Thread(target=listen)
    tid.start()
    time.sleep(2)

    load_letters(sys.argv[2])

    print_letters_by_size()
    isSim=False
    if len(sys.argv) > 3:
        isSim=(sys.argv[3]=="sim")
        makeSimSocket()

    #word = 'abcde'
    word = None

    ix=0
    if not isSim:
        """ compute solutions iteratively """
        try:
            if not word:
                print "input letter (. to exit)"
                while True:
                    c = getCh()
                    if c in letters.keys():
                        send_letter(c)
                    else:
                        if c == '.':
                            break
                        if c=='>':
                            move_letter(0.5,0)
                        elif c=='<':
                            move_letter(-0.5,0)
                        elif c == ':':
                            move_letter(0,-0.5)
                        elif c == '"':
                            move_letter(0,0.5)
                        elif c==')':
                            send_smiley_1()
                        elif c=='_':
                            send_smiley_2()
                        elif c=='+':
                            send_smiley_3()
                        elif c=='~':
                            send_wps(home[:len(robots)])

                        else:
                            print "Invalid command ",c
            else:
                while True:
                    time.sleep(30)
                    send_letter(word[ix])
                    ix+=1
                    if ix >= len(word):
                        """ cycle """
                        ix=0
        except KeyboardInterrupt:
            pass
        done = True

    print "I'm done, closing LCM connection"
    tid.join()
    lcm.unsubscribe(subscription)
