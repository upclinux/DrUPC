#!/usr/bin/env python
# coding=utf-8

# DrUPC   Copyright (C) 2015  vjudge1 (vjudge404@gmail.com)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
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

# 注意：
# 172.19.255.150 是 UPC 的认证。在其他环境下能 ping 通但是连不通
# 222.195.191.231 是宿舍网口的认证，没有做屏蔽所以在连 UPC 时也能访问
# 因此 172 那个必须放在 222 前面
authServers = ['http://172.19.255.150', 'http://222.195.191.231']
keywords = {
    authServers[0]: 'Android',
    authServers[1]: '222.195.191.231'
    }

# 根据所给的认证服务器进行探测，能够访问而且有对应关键词的第一个服务器即认证服务器
def detectAuthServer():
    for srv in authServers:
        try:
            response = urllib2.urlopen(srv, timeout=1)

            if keywords[srv] in response.read():
                return srv
        except Exception, e:
            pass
    else:
        return 'unknown'

# 检测连接状态 (假设度娘从不抽风)
def detectConnectStatus():
    try:
        response = urllib2.urlopen('https://www.baidu.com', timeout=0.5)
        return '百度' in response.read()
    except urllib2.URLError, e:
        return False

class crawler:

    def __init__(self, username='', password=''):
        self.username = username
        self.password = password

    def setLogin(self, username, password):
        self.username = username
        self.password = password

    def login(self):
        return False


# 登录到 UPC
class wifiAuthCrawler(crawler):

    def __init__(self, username='', password=''):
        crawler.__init__(self, username, password)
        self.loginPage = 'http://172.19.255.150'
        self.postPage = 'http://172.19.255.150'
        self.logoutPage = 'http://172.19.255.150/F.htm'

    def login(self):
        # 检查是否已经登录了
        response = urllib2.urlopen(self.loginPage, timeout=1)
        if 'javascript:wc()' in response.read():
            raise Exception('Already login.')

        headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',  
            'Referer' : 'http://172.19.255.150'
            }
        ps = 1
        pid = '1'
        calg = '12345678'
        upass = hashlib.md5(pid + self.password + calg).hexdigest() + calg + pid
        
        postData = {
            'DDDDD': self.username,
            'upass': upass,
            'R1': '0',
            'R2': '1',
            'para': '00',
            '0MKKey': '123456'
            }
        postData = urllib.urlencode(postData)

        request = urllib2.Request(self.postPage, postData, headers)
        response = urllib2.urlopen(request)
        text = response.read()
        if 'http://v.upc.edu.cn' in text:
            return True
        else:
            code = int(re.search('Msg=(\d*)', text).group(1))
            try:
                errorText = {
                    1:'Wrong username or password',
                    2:'The account is being used now.',
                    3:'Can\'t connect while having a class.',
                    5:'You have no money.',
                    11:'Can\'t connect while having a class.'
                    }[code]
            except:
                errorText = 'Unknow error.'
            finally:
                raise Exception(errorText)

    # 注销
    def logout(self):
        response = urllib2.urlopen(self.logoutPage, timeout=1)
        return 'Msg=14' in response.read()


# 校园网
class ethAuthCrawler(crawler):

    def __init__(self, username='', password=''):
        crawler.__init__(self, username, password)
        self.loginPage = 'http://222.195.191.231:801/eportal/?c=ACSetting&a=Login&wlanuserip=null&wlanacip=null&wlanacname=null&port=&iTermType=1&session=null'
        self.postPage = 'http://222.195.191.231:801/eportal/?c=ACSetting&a=Login&wlanuserip=null&wlanacip=null&wlanacname=null&port=&iTermType=1&session=null'
        self.logoutPage = 'http://222.195.191.231:801/eportal/?c=ACSetting&a=Logout&wlanuserip=null&wlanacip=null&wlanacname=null&port=&iTermType=1&session=null'
    
    def login(self):
        # 检查是否已经登录了
        # 备注：宿舍网没有能直接表示是否已经登录的东西
        #response = urllib2.urlopen(self.loginPage, timeout=1)
        #if 'javascript:wc()' in response.read():
        #    raise Exception('Already login.')

        headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',  
            'Referer' : 'http://222.195.191.231/a70.htm'
            }
        
        postData = {
            'DDDDD': self.username + '@upc',
            'upass': self.password,
            'R1': '0',
            'R2': '',
            'R6': '0',
            'para': '00',
            '0MKKey': '123456'
            }
        postData = urllib.urlencode(postData)

        request = urllib2.Request(self.postPage, postData, headers)
        response = urllib2.urlopen(request)
        text = response.read()
        if 'successfully logged' in text:
            return True
        else:
            code = int(re.search('Msg=(\d*)', text).group(1))
            try:
                errorText = {
                    1:'Wrong username or password',
                    2:'The account is being used now.',
                    3:'Can\'t connect while having a class.',
                    5:'You have no money.',
                    11:'Can\'t connect while having a class.'
                    }[code]
            except:
                errorText = 'Unknow error.'
            finally:
                raise Exception(errorText)

    def logout(self):
        response = urllib2.urlopen(self.logoutPage)
        return 'Logout successfully' in response.read()


# 强制离线
class selfServiceCrawler(crawler):

    def __init__(self, username='', password=''):
        crawler.__init__(self, username, password)
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
            'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',  
            'Referer' : 'http://self.upc.edu.cn/Self/nav_login'
            }
        postData = {
            'account' : self.username,
            'password' : hashlib.md5(self.password).hexdigest(),
            'code' : '',
            'checkcode' : checkcode,
            'Submit' : '登 录Login'
            }
        postData = urllib.urlencode(postData)

        request = urllib2.Request(self.postPage, postData, headers)
        response = urllib2.urlopen(request)
        text = response.read()

        if '账号被锁定' in text:
            raise Exception('Your account is locked in 30 minutes!')
        if '账号或密码出现错误' in text:
            raise Exception('Wrong username or password!')
        if '登录密码不正确' in text:
            count = re.search('您已输错(\d*)次', text).group(1)
            raise Exception('Wrong username or password! Count = %s' % count)

        # 到“强制离线”页面找已登录设备
        response = urllib2.urlopen(self.baseUrl + 'nav_offLine')
        text = response.read()

        # 获取网号登录的 ID
        sessionId = re.search('<td style="display:none;">(\d*)</td>', text)
        if sessionId != None:
            sessionId = sessionId.group(1)
            response = urllib2.urlopen(self.baseUrl + 'tooffline?t=0.20741149433888495&fldsessionid=' + sessionId)
        
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
                ['login','kill','logout','user','pass','status','help'])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    for o,a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        elif o in ('-s', '--status'):
            print "Auth:", detectAuthServer()
            print "Internet:", detectConnectStatus()
            sys.exit()
        elif o in ('-e', '--login'):
            login = True
        elif o in ('-k', '--kill'):
            force = True
        elif o in ('-x', '--logout'):
            logout = True
        elif o in ('-u', '--user'):
            user = a
        elif o in ('-p', '--password'):
            password = a

    # Set up a cookie processor
    cj = cookielib.LWPCookieJar()
    cookieSupport = urllib2.HTTPCookieProcessor(cj)
    opener = urllib2.build_opener(cookieSupport, urllib2.HTTPHandler)
    urllib2.install_opener(opener)

    auth = detectAuthServer()

    if auth == 'unknown':
        print 'Are you in UPC?'
        sys.exit(2)
    else:
        c = {
              authServers[0]: wifiAuthCrawler(), 
              authServers[1]: ethAuthCrawler()
            }[auth]

    # 如果什么参数都没敲
    if not (login or logout or force):
        if detectConnectStatus():
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

        c.setLogin(user, password)

    # 强制离线
    if force:
        try:
            f = selfServiceCrawler(user, password)
            f.logout()
        except Exception, e:
            print e

    # 用网号登录
    if login and c.login():
        print 'Login successful.'
            

if __name__ == '__main__':
    main()
