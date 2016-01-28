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
AUTHSERVERS = ['http://172.16.4.3', 'http://222.195.191.230']
KEYWORDS = {
    AUTHSERVERS[0]: '172.16.4.3',
    AUTHSERVERS[1]: '222.195.191.230'
    }


def detect_authserver():
    '''
    探测所处网络所使用的认证环境。返回认证页面网址或“unknown”
    '''
    for srv in AUTHSERVERS:
        try:
            response = urllib2.urlopen(srv, timeout=1)
            if KEYWORDS[srv] in response.read():
                return srv
        except Exception as e:
            pass
    else:
        return 'unknown'


def get_login_crawler(username = '', password = ''):
    '''
    根据网络环境选用合适的爬虫。
    '''
    auth = detect_authserver()

    if auth == 'unknown':
        return None
    else:
        return {
            AUTHSERVERS[0]: WifiAuthCrawler(username, password),
            AUTHSERVERS[1]: EthAuthCrawler(username, password)
        }[auth]


def detect_connect_status():
    '''
    检测网络连接状态。假设数字石大需要认证之后才能访问，而且网站从不抽风。
    '''
    try:
        response = urllib2.urlopen('http://i.upc.edu.cn', timeout=0.5)
        return '数字石大 | Digitalized DCP' in response.read()
    except Exception:
        return False


class Crawler:
    '''
    用于登录的爬虫，抽象类
    '''
    def __init__(self, username='', password=''):
        self.username = username
        self.password = password

        cj = cookielib.LWPCookieJar()
        cookie_support = urllib2.HTTPCookieProcessor(cj)
        self._opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
        #urllib2.install_opener(opener)

    def set_login(self, username, password):
        '''
        设置用户名和密码。
        '''
        self.username = username
        self.password = password

    def login(self):
        raise NotImplementedError

    def logout(self):
        raise NotImplementedError


class BadPasswordError(Exception):
    '''
    用户名密码错误
    '''
    def __init__(self, count=0):
        self.count = count
        if self.count < 0:
            self.message = 'Account is locked.'
        elif self.count == 0:
            self.message = 'Wrong username or password.'
        else:
            self.message = 'Wrong username or password. Count = %d.' % self.count

    def count(self):
        '''
        返回登录错误次数。仅适用于自助服务网站。
        '''
        return self.count


def new_error(klass, message, doc):
    '''
    根据提示语创建一个异常对象
    '''
    return type(klass, (Exception,), {'message': message, '__doc__': doc})

UserOccupiedError = new_error('UserOccupiedError', 'The account is being used now.',
                              '账号已被使用')
UserRapedError    = new_error('UserRapedError', 'Good good study, day day, up.',
                              '“上课时间不能上网”')
NoMoneyError      = new_error('NoMoneyError', 'You have no money.',
                              '欠费停机')
AlreadyLoginError = new_error('AlreadyLoginError', 'Already login',
                              '已经登录但仍然尝试进行认证')
Error             = new_error('Error', 'Unknown Error', '错误')


class WifiAuthCrawler(Crawler):
    '''
    名字为“UPC”的无线热点的认证。
    '''
    LOGIN  = 'http://172.16.4.3'
    POST   = 'http://172.16.4.3'
    LOGOUT = 'http://172.16.4.3/F.htm'

    def login(self):
        '''
        登录。登录成功返回True，否则引发异常。
        '''
        # 检查是否已经登录了
        response = self._opener.open(self.LOGIN, timeout=1)
        if 'javascript:wc()' in response.read():
            raise AlreadyLoginError()

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

        request = urllib2.Request(self.POST, post_data, headers)
        response = self._opener.open(request)
        text = response.read()
        if "window.location='1.htm'" in text:
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
                raise Error()

    def logout(self):
        '''
        注销。成功则返回True。
        '''
        response = self._opener.open(self.LOGOUT, timeout=1)
        return 'Msg=14' in response.read()


class EthAuthCrawler(Crawler):
    '''
    校园网认证。用于宿舍插网线。
    '''
    LOGIN  = 'http://222.195.191.230:801/eportal/?c=ACSetting&a=Login&wlanuserip=null&wlanacip=null&wlanacname=null&port=&iTermType=1&session=null'
    POST   = 'http://222.195.191.230:801/eportal/?c=ACSetting&a=Login&wlanuserip=null&wlanacip=null&wlanacname=null&port=&iTermType=1&session=null'
    LOGOUT = 'http://222.195.191.230:801/eportal/?c=ACSetting&a=Logout&wlanuserip=null&wlanacip=null&wlanacname=null&port=&iTermType=1&session=null'

    def login(self):
        '''
        登录。登录成功返回True，否则引发异常。
        '''
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

        request = urllib2.Request(self.POST, post_data, headers)
        response = self._opener.open(request)
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
                raise Error()

    def logout(self):
        '''
        注销。成功则返回True。
        '''
        response = self._opener.open(self.LOGOUT)
        return 'Logout successfully' in response.read()


# 强制离线
class SelfServiceCrawler(Crawler):
    '''
    用于抓取自助服务系统网站的爬虫。
    '''
    BASEURL = 'http://self.upc.edu.cn/Self/'
    LOGIN = 'http://self.upc.edu.cn/Self/nav_login'
    POST = 'http://self.upc.edu.cn/Self/LoginAction.action'
    LOGOUT = 'http://self.upc.edu.cn/Self/LogoutAction.action'

    def login(self):
        '''
        登录到自助服务系统
        '''
        # 加载页面上的验证码，否则无法登录
        response = self._opener.open(self.LOGIN)
        self._opener.open(self.BASEURL + 'RandomCodeAction.action?randomNum=0.20741149433888495')
        text = response.read()
        checkcode = re.search('var checkcode="(\d*)"', text).group(1)

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

        request = urllib2.Request(self.POST, post_data, headers)
        response = self._opener.open(request)
        text = response.read()

        if '账号被锁定' in text:
            raise BadPasswordError(-1)
        if '账号或密码出现错误' in text:
            raise BadPasswordError()
        if '登录密码不正确' in text:
            count = re.search('您已输错(\d*)次', text).group(1)
            raise BadPasswordError(count)

        return True

    def logout(self):
        '''
        从自助服务中注销。
        '''
        self._opener.open(self.LOGOUT)

    def offline(self, all_in_one=True):
        '''
        在自助服务系统中强制下线。若all_in_one为True，那么就无须手动调用登录和注销过程。
        '''
        if all_in_one:
            self.login()

        # 到“强制离线”页面找已登录设备
        response = self._opener.open(self.BASEURL + 'nav_offLine')
        text = response.read()

        # 获取网号登录的 ID
        session_id = re.search('<td style="display:none;">(\d*)</td>', text)
        if session_id is not None:
            session_id = session_id.group(1)
            self._opener.open(self.BASEURL + 'tooffline?t=0.20741149433888495&fldsessionid=' + session_id)

        if all_in_one:
            self.logout()


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

    c = get_login_crawler()
    if c is None:
        print 'Are you in UPC?'
        sys.exit(2)

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
            f.offline()
        except Exception as e:
            print e

    # 用网号登录
    if login and c.login():
        print 'Login successful.'


if __name__ == '__main__':
    main()
