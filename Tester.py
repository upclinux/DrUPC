#!/usr/bin/env python
# coding=utf-8

# DrUPC   Copyright (C) 2015  vjudge1 (vjudge404@gmail.com)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from DrUPC import *
import sys
import getopt
import time
import random

filen = 'accounts.lst'
watchmode = False
interval = 30
randommode = False


def get_crawler():
    if detect_connect_status():
        return True

    auth = detect_authserver()
    if auth == authServers[0]:
        return WifiAuthCrawler()
    elif auth == authServers[1]:
        return EthAuthCrawler()
    else:
        print 'Unknown Network'
        return False


def watch():
    time.sleep(interval)
    return detect_connect_status()


def start_test(filename):
    crawler = get_crawler()
    if type(crawler) is bool:
        return crawler

    with open(filename, 'r') as f:
        if randommode:
            records = f.readlines()
            random.shuffle(records)
        else:
            records = f

        for record in records:
            try:
                record = record.splitlines()[0]
                user, passkey = record.split(',')
            except ValueError:
                continue

            print 'Trying %s...' % user,

            crawler.set_login(user, passkey)

            try:
                if crawler.login():
                    print 'OK'

                    if watchmode:
                        sys.stdout.write('Watching.')
                        sys.stdout.flush()  # for Cmder
                        while watch():
                            sys.stdout.write('.')
                            sys.stdout.flush()  # for Cmder
                        print    
                        print '%s is Dead.' % user
                    else:        
                        return True

            except KeyboardInterrupt:
                print 'Exit'
                return True
            except Exception, e:
                print 'Failed: ', e

    print 'Oops! No accounts can be used!'
    return False


def usage():
    print("Usage: %s [OPTION]" % sys.argv[0])
    print("""
    -f, --file      Use another config file (Def. accounts.lst)
    -w, --watch     Watch and try to reconnect
    -i, --interval  Interval (def. 30)
    -r, --random    Try random one
    -h, --help      give this help list
""")


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'f:wi:rh',
                                   ['file=','watch','interval=','random','help'])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        elif o in ('-f', '--file'):
            filen = a
        elif o in ('-w', '--watch'):
            watchmode = True
        elif o in ('-i', '--interval'):
            interval = a
        elif o in ('-r', '--random'):
            randommode = True

    if start_test(filen):
        sys.exit(0)
    else:    
        sys.exit(1)
