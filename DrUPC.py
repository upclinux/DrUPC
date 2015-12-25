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

import HTMLParser
import urlparse
import urllib
import urllib2
import cookielib
import string
import re
import hashlib
import getopt
import sys
import getpass
import time

# 注意：
# 172.16.4.3 是 UPC 的认证。在其他环境下能 ping 通但是连不通
# 222.195.191.230 是宿舍网口的认证，没有做屏蔽所以在连 UPC 时也能访问
# 如果在办公区用，请将 230 改成 231
# 因此 172 那个必须放在 222 前面
authServers = ['http://172.16.4.3', 'http://222.195.191.230']
keywords = {
    authServers[0]: '172.16.4.3',
    authServers[1]: '222.195.191.230'
    }


# 根据所给的认证服务器进行探测，能够访问而且有对应关键词的第一个服务器即认证服务器
def detect_authserver():
    for srv in authServers:
        try:
            response = urllib2.urlopen(srv, timeout=1)
            if keywords[srv] in response.read():
                return srv
        except Exception, e:
            pass
    else:
        return 'unknown'


# 检测连接状态 (假设数字石大从不抽风)
def detect_connect_status():
    try:
        response = urllib2.urlopen('http://i.upc.edu.cn', timeout=0.5)
        return '数字石大' in response.read()
    except Exception:
        return False


class Crawler:

    def __init__(self, username='', password=''):
        self.username = username
        self.password = password

        cj = cookielib.LWPCookieJar()
        cookie_support = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
        urllib2.install_opener(opener)

    def set_login(self, username, password):
        self.username = username
        self.password = password

    def login(self):
        return False


# 用户名密码错误
class BadPasswordError(Exception):
    def __init__(self, count=0):
        self.count = count
    def count(self):
        return self.count
    def __str__(self):
        if self.count < 0:
            return 'Account is locked.'
        elif self.count == 0:
            return 'Wrong username or password.'
        else:
            return 'Wrong username or password. Count = %d.' % self.count
            


# 账号已经被使用（即使显示成功登录也需要去认证）
class UserOccupiedError(Exception):
    def __str__(self):
        return 'The account is being used now.'


# “上课时间不能上网”
class UserRapedError(Exception):
    def __str__(self):
        return 'Good good study, day day up.'


# 欠费停机
class NoMoneyError(Exception):
    def __str__(self):
        return 'You have no money.'


# 已经登录
class AlreadyLoginError(Exception):
    def __str__(self):
        return 'Already logined.'


# 登录到 UPC
class WifiAuthCrawler(Crawler):

    def __init__(self, username='', password=''):
        Crawler.__init__(self, username, password)
        self.loginPage = 'http://172.16.4.3'
        self.postPage = 'http://172.16.4.3'
        self.logoutPage = 'http://172.16.4.3/F.htm'

    def login(self):
        # 检查是否已经登录了
        response = urllib2.urlopen(self.loginPage, timeout=1)
        if 'javascript:wc()' in response.read():
            raise AlreadyLoginError('Already login.')

        headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
            'Referer' : 'http://172.16.4.3'
            }
        ps = 1
        pid = '1'
        calg = '12345678'
        upass = hashlib.md5(pid + self.password + calg).hexdigest() + calg + pid

        post_data = {
            'DDDDD': self.username,
            'upass': upass,
            'R1': '0',
            'R2': '1',
            'para': '00',
            '0MKKey': '123456'
            }
        post_data = urllib.urlencode(post_data)

        request = urllib2.Request(self.postPage, post_data, headers)
        response = urllib2.urlopen(request)
        text = response.read()
        if 'http://v.upc.edu.cn' in text:
            time.sleep(0.5)
            if detect_connect_status():
                return True
            else:
                raise UserOccupiedError()
        elif re.search('msga=.*?VLANID', text):
            raise UserRapedError()
        else:
            code = int(re.search('Msg=(\d*)', text).group(1))
            if code == 1:
                raise BadPasswordError()
            elif code == 2:
                raise UserOccupiedError()
            elif code == 3 or code == 11:
                raise UserRapedError()
            elif code == 5:
                raise NoMoneyError()
            else:
                raise Exception('Unknown Error')

    # 注销
    def logout(self):
        response = urllib2.urlopen(self.logoutPage, timeout=1)
        return 'Msg=14' in response.read()


# 校园网
class EthAuthCrawler(Crawler):

    def __init__(self, username='', password=''):
        Crawler.__init__(self, username, password)
        self.loginPage = 'http://222.195.191.230:801/eportal/?c=ACSetting&a=Login&wlanuserip=null&wlanacip=null&wlanacname=null&port=&iTermType=1&session=null'
        self.postPage = 'http://222.195.191.230:801/eportal/?c=ACSetting&a=Login&wlanuserip=null&wlanacip=null&wlanacname=null&port=&iTermType=1&session=null'
        self.logoutPage = 'http://222.195.191.230:801/eportal/?c=ACSetting&a=Logout&wlanuserip=null&wlanacip=null&wlanacname=null&port=&iTermType=1&session=null'

    def login(self):
        # 检查是否已经登录了
        # 备注：宿舍网没有能直接表示是否已经登录的东西
        # response = urllib2.urlopen(self.loginPage, timeout=1)
        # if 'javascript:wc()' in response.read():
        #     raise Exception('Already login.')
        if detect_connect_status():
            raise AlreadyLoginError()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
            'Referer': 'http://222.195.191.230/a70.htm'
            }

        post_data = {
            'DDDDD': self.username + '@upc',
            'upass': self.password,
            'R1': '0',
            'R2': '',
            'R6': '0',
            'para': '00',
            '0MKKey': '123456'
            }
        post_data = urllib.urlencode(post_data)

        request = urllib2.Request(self.postPage, post_data, headers)
        response = urllib2.urlopen(request)
        text = response.read()
        if 'successfully logged' in text:
            if detect_connect_status():
                return True
            else:
                raise UserOccupiedError()
        elif re.search('msga=.*?VLANID', text):
            raise UserRapedError()
        else:
            code = int(re.search('Msg=(\d*)', text).group(1))
            if code == 1:
                raise BadPasswordError()
            elif code == 2:
                raise UserOccupiedError()
            elif code == 3 or code == 11:
                raise UserRapedError()
            elif code == 5:
                raise NoMoneyError()
            else:
                raise Exception('Unknown Error')

    def logout(self):
        response = urllib2.urlopen(self.logoutPage)
        return 'Logout successfully' in response.read()


# 强制离线
class SelfServiceCrawler(Crawler):

    def __init__(self, username='', password=''):
        Crawler.__init__(self, username, password)
        self.baseUrl = 'http://self.upc.edu.cn/Self/'
        self.loginPage = 'http://self.upc.edu.cn/Self/nav_login'
        self.postPage = 'http://self.upc.edu.cn/Self/LoginAction.action'
        self.logoutPage = 'http://self.upc.edu.cn/Self/LogoutAction.action'

    def logout(self):
        response = urllib2.urlopen(self.loginPage)
        text = response.read()

        checkcode = re.search('var checkcode="(\d*)"', text).group(1)

        # 加载验证码否则无法正确登录
        response = urllib2.urlopen(self.baseUrl + 'RandomCodeAction.action?randomNum=0.20741149433888495')

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
            'Referer': 'http://self.upc.edu.cn/Self/nav_login'
            }
        post_data = {
            'account': self.username,
            'password': hashlib.md5(self.password).hexdigest(),
            'code': '',
            'checkcode': checkcode,
            'Submit': '登 录Login'
            }
        post_data = urllib.urlencode(post_data)

        request = urllib2.Request(self.postPage, post_data, headers)
        response = urllib2.urlopen(request)
        text = response.read()

        if '账号被锁定' in text:
            raise BadPasswordError(-1)
        if '账号或密码出现错误' in text:
            raise BadPasswordError()
        if '登录密码不正确' in text:
            count = re.search('您已输错(\d*)次', text).group(1)
            raise BadPasswordError(count)

        # 到“强制离线”页面找已登录设备
        response = urllib2.urlopen(self.baseUrl + 'nav_offLine')
        text = response.read()

        # 获取网号登录的 ID
        session_id = re.search('<td style="display:none;">(\d*)</td>', text)
        if session_id is not None:
            session_id = session_id.group(1)
            response = urllib2.urlopen(self.baseUrl + 'tooffline?t=0.20741149433888495&fldsessionid=' + session_id)

        response = urllib2.urlopen(self.logoutPage)
        response.read()


def usage():
    print("Usage: %s [OPTION]" % sys.argv[0])
    print("""
    -e, --login     login
    -k, --kill      force to logout using self.upc.edu.cn
    -x, --logout    logout
    -u, --user      specify user name
    -p, --pass      specify the password
    -s, --status    print the status
    -h, --help      give this help list

If no options given, this program will enter interactive mode.""")


def main():
    user = ''
    password = ''
    login = False
    logout = False
    force = False

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'ekxu:p:sh',
                                   ['login', 'kill', 'logout', 'user=', 'pass=', 'status', 'help'])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        elif o in ('-s', '--status'):
            print "Auth:", detect_authserver()
            print "Internet:", detect_connect_status()
            sys.exit()
        elif o in ('-e', '--login'):
            login = True
        elif o in ('-k', '--kill'):
            force = True
        elif o in ('-x', '--logout'):
            logout = True
        elif o in ('-u', '--user'):
            user = a
        elif o in ('-p', '--pass'):
            password = a

    # Set up a cookie processor
    # cj = cookielib.LWPCookieJar()
    # cookie_support = urllib2.HTTPCookieProcessor(cj)
    # opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
    # urllib2.install_opener(opener)

    auth = detect_authserver()

    if auth == 'unknown':
        print 'Are you in UPC?'
        sys.exit(2)
    else:
        c = {
              authServers[0]: WifiAuthCrawler(),
              authServers[1]: EthAuthCrawler()
            }[auth]

    # 如果什么参数都没敲
    if not (login or logout or force):
        if detect_connect_status():
            print 'Internet Connected. Logout [y/N]?'
            logout = raw_input() in ('y', 'Y')
            login = False
            force = False
        else:
            login = True

    if logout:
        print 'Logout: %s' % c.logout()

    # 获取完整登录信息
    if login or force:
        if user == '':
            print 'Username:',
            user = raw_input()
        if password == '':
            password = getpass.getpass('Password: ')

        c.set_login(user, password)

    # 强制离线
    if force:
        try:
            print 'Force logout'
            f = SelfServiceCrawler(user, password)
            f.logout()
        except Exception, e:
            print e

    # 用网号登录
    if login and c.login():
        print 'Login successful.'


if __name__ == '__main__':
    main()
