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
from itertools import cycle
import sys
import getopt
import time
import random
import threading
import logging

TRYING  = 1
OK      = 2
EXIT    = 3
ALREADY = 4
FAILED  = 5
OUT     = 6


logging.basicConfig(level=logging.INFO,
    format='[%(levelname)s] %(asctime)s %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S')


class Listener:
    '''
    观察者，抽象类
    '''
    def __init__(self, name=None, tester=None):
        self.name = name
        if tester:
            tester.register(self)

    def notify(self, event):
        if event[0] == TRYING:
            logging.info('Use %s' % event[1])
        elif event[0] == OK:
            logging.info('Connected to %s' % event[1])
        elif event[0] == EXIT:
            logging.warning('Exit by user')
        elif event[0] == FAILED:
            logging.error('Unable to connect: %s' % event[1])
        elif event[0] == OUT:
            logging.critical('Accounts are used up.')


class TerminateListener(Listener):
    '''
    响应事件之后结束程序
    '''
    def notify(self, event):
        if event[0] == OK:
            sys.exit(0)
        elif event[0] in (EXIT, ALREADY, OUT):
            sys.exit(1)


class AnimListener(Listener):
    '''
    收到OK消息之后放文本动画
    '''
    def __init__(self, name=None, tester=None):
        Listener.__init__(self, name, tester)
        if tester:
            self.interval = tester.interval
        else:
            self.interval = 0

        self._t = None

    def notify(self, event):
        pass
        # TODO 实现动画效果
        #def anim(interval):
        #    sys.stdout.flush()  # for Cmder
        #    while detect_connect_status():
        #        sys.stdout.write('.')
        #        sys.stdout.flush()  # for Cmder
        #        # Animation
        #        for i, ch in enumerate(cycle(['|', '/', '-', '\\'])):
        #            sys.stdout.write(ch)
        #            sys.stdout.flush()
        #            time.sleep(0.1)
        #            sys.stdout.write("\b")
        #            sys.stdout.flush()
        #            if i >= interval*10 - 1:
        #                break
        #    print

        #if event[0] == OK:
        #    # 开始放动画
        #    if self._t is None:
        #        self._t = threading.Thread(target=anim, args=(self.interval,))
        #        self._t.start()
        #else:
        #    # 停止动画
        #    if self._t:
        #        self._t.


class Tester:
    def __init__(self, records=[], interval=30, forcestart=False):
        self.listeners = []
        self.records = records
        self.interval = interval
        self.forcestart = forcestart

    def register(self, listener):
        self.listeners.append(listener)

    def unregister(self, listener):
        self.listeners.remove(listener)

    def notify_listeners(self, event):
        for listener in self.listeners:
            listener.notify(event)

    def shuffle(self):
        random.shuffle(self.records)

    def work(self):
        if detect_connect_status() and not self.forcestart:
            logging.warning('Connected')
            return True

        crawler = get_login_crawler()
        if crawler is None:
            logging.error('Unable to detect auth servers.')
            return False
        else:
            logging.info(crawler)

        for record in self.records:
            if detect_authserver() is None:
                logging.error('Network changed')
                return False

            while detect_connect_status():
                time.sleep(self.interval)

            try:
                record = record.splitlines()[0]
                user, passkey = record.split(',')
            except ValueError:
                continue

            self.notify_listeners([TRYING, user])

            crawler.set_login(user, passkey)

            try:
                if crawler.login():
                    self.notify_listeners([OK, user])
                    while detect_connect_status():
                        time.sleep(self.interval)
            except KeyboardInterrupt:
                self.notify_listeners([EXIT])
                return True
            except Exception as e:
                self.notify_listeners([FAILED, e.message])
        else:
            self.notify_listeners([OUT])
            return False


def load_from_file(filename):
    with open(filename, 'r') as f:
        return f.readlines()


def textmode(filename, interval=30, force=False, randommode=False, watchmode=False):
    records = load_from_file(filename)
    tester = Tester(records, interval, force)
    if watchmode:
        listener = Listener('listener', tester)
        anim = AnimListener('anim', tester)
    else:
        listener = TerminateListener('listener', tester)

    if randommode:
        tester.shuffle()

    tester.work()


def guimode(filename, interval=30, force=False, randommode=False, watchmode=False):
    # TODO 图形界面
    pass


def usage():
    print("Usage: %s [OPTION]" % sys.argv[0])
    print("""
    -e, --file      Use another config file (Def. accounts.lst)
    -w, --watch     Watch and try to reconnect
    -f, --force     Force start whether Internet is connected
    -i, --interval  Interval (def. 30)
    -r, --random    Try random one
    -g, --gui       GUI mode
    -h, --help      give this help list
""")


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'e:wi:rfhg',
                                   ['file=', 'watch', 'interval=', 'random', 'force', 'help', 'gui'])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    filen      = 'accounts.lst'
    watchmode  = False
    interval   = 30
    randommode = False
    force      = False
    gui        = False

    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        elif o in ('-e', '--file'):
            filen = a
        elif o in ('-w', '--watch'):
            watchmode = True
        elif o in ('-i', '--interval'):
            interval = float(a)
        elif o in ('-r', '--random'):
            randommode = True
        elif o in ('-f', '--force'):
            force = True
        elif o in ('-g', '--gui'):
            gui = True

    if gui:
        guimode(filen, interval, force, randommode, watchmode)
    else:
        textmode(filen, interval, force, randommode, watchmode)
