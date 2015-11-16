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

# 对账号列表进行逐个测试
# 如果已停机或者密码错误，删除这个账号
# 如果连接成功，判断是否已经连上网

from DrUPC import *
import sys
import getopt


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


def start_test(filename):
    crawler = get_crawler()
    if crawler is True or crawler is False:
        return crawler

    with open(filename, 'r') as f:
        for record in f:
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
                    return True
            except Exception, e:
                print 'Failed: ', e

    print 'Oops! No accounts can be used!'
    return False


if __name__ == '__main__':
    fn = sys.argv[1] if len(sys.argv)>1 else 'accounts.lst'
    start_test(fn)
