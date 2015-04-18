#!/usr/bin/env python

import os
import random

from sys import argv

from subprocess import Popen, call, PIPE

# Console colors
W = '\033[0m'   # white (normal)
R = '\033[31m'  # red
G = '\033[32m'  # green
O = '\033[33m'  # orange

if os.getuid() != 0:
    print R+' [!]'+O+' ERROR:'+G+' macanony'+O+' must be run as '+R+'root'+W
    print R+' [!]'+O+' login as root ('+W+'su root'+O+') or try '+W+'sudo ./macanony.py'+W
    exit(1)

DN = open(os.devnull, 'w')


def help():
    print 'MacAnonymize 1.0'
    print 'Usage:'
    print '  -i <iface>\t\tinterface to anonymize'
    print '  -a\t\t\tanonymize all interface'
    print
    print 'EXAMPLE'
    print '  macanony -i eth0'


def handle_args():
    args = argv[1:]
    if args.count('-h') + args.count('--help') + args.count('?') + args.count('-help') > 0 or len(args) == 0:
        help()
        exit(0)

    for i in xrange(0, len(args)):
        if args[i] == '-i':
            mac_anonymize(args[i + 1])
            exit(0)
        elif args[i] == '-a':
            for i in get_ifaces():
                mac_anonymize(i)
            exit(0)


def get_ifaces():
    proc = Popen(['ifconfig'], stdout=PIPE, stderr=DN)
    iface = ''
    ifaces = []
    for line in proc.communicate()[0].split('\n'):
        if len(line) == 0:
            continue
        if ord(line[0]) != 32:
            iface = line[: line.find(' ')]
            if iface.startswith('eth') or iface.startswith('wlan'):
                ifaces.append(iface)
    return ifaces


def get_mac_address(iface):
    """
                Returns MAC address of "iface".
    """
    proc = Popen(['ifconfig', iface], stdout=PIPE, stdin=DN)
    proc.wait()
    mac = ''
    first_line = proc.communicate()[0].split('\n')[0]
    for word in first_line.split(' '):
        if word != '':
            mac = word
    if mac.find('-') != -1:
        mac = mac.replace('-', ':')
    return mac


def generate_random_mac(old_mac):
    """
                Generates a random MAC address.
                Keeps the same vender (first 6 chars) of the old MAC address (old_mac).
                Returns string in format old_mac[0:9] + :XX:XX:XX where X is random hex
    """
    random.seed()
    new_mac = old_mac[:8].lower().replace('-', ':')
    for i in xrange(0, 6):
        if i % 2 == 0:
            new_mac += ':'
        new_mac += '0123456789abcdef'[random.randint(0, 15)]

    if new_mac == old_mac:
        generate_random_mac(old_mac)
    return new_mac


def mac_anonymize(iface):
    """
            Changes MAC address of 'iface' to a random MAC.
            Only randomize the last 6 digits of the MAC, so the vender stays the same.
    """
    old_mac = get_mac_address(iface)
    new_mac = generate_random_mac(old_mac)

    call(['ifconfig', iface, 'down'])

    print "changing %s's MAC from %s to %s..." % (G+iface+W, G+old_mac+W, O+new_mac+W)

    proc = Popen(['ifconfig', iface, 'hw', 'ether', new_mac], stdout=PIPE, stderr=DN)
    proc.wait()
    call(['ifconfig', iface, 'up'], stdout=DN, stderr=DN)
    print 'done'


if __name__ == '__main__':
    handle_args()