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

import Tkinter as tk
import ttk
import tkMessageBox
import DrUPC
try:
    # TODO 完成GUI模式
    #import Tester
    Tester = None
except ImportError as e:
    Tester = None
import sys

if DrUPC.detect_authserver() == 'unknown':
    tkMessageBox.showwarning('DrUPC', '请连接到石油大学的网络上面。')
    sys.exit(2)

if DrUPC.detect_connect_status:
    tkMessageBox.showinfo('DrUPC', '你现在已经连接到互联网了。')

try:
    user, password = '', ''
    with open('user.cfg', 'r') as f:
        user = f.readline().rstrip()
        password = f.readline().rstrip()
except Exception:
    pass

root = tk.Tk()
root.title('DrUPC')

ttk.Label(root, text='用户名:').pack()
user_text = ttk.Entry(root)
user_text.insert(0, user)
user_text.pack()
ttk.Label(root, text='密码:').pack()
user_pass = ttk.Entry(root, text=password)
user_pass.insert(0, password)
user_pass.pack()

def login1():
    user = user_text.get()
    password = user_pass.get()

    try:
        if DrUPC.get_login_crawler(user, password).login():
            tkMessageBox.showinfo('DrUPC', '连接成功')
        with open('user.cfg', 'w') as f:
            f.write('%s\n%s\n' % (user, password))
    except Exception as e:
        tkMessageBox.showerror('DrUPC', '发生错误：' + e.message)

def login2():
    user = user_text.get()
    password = user_pass.get()

    try:
        DrUPC.SelfServiceCrawler(user, password).offline()
        if DrUPC.get_login_crawler(user, password).login():
            tkMessageBox.showinfo('DrUPC', '连接成功')
        with open('user.cfg', 'w') as f:
            f.write('%s\n%s\n' % (user, password))
    except Exception as e:
        tkMessageBox.showerror('DrUPC', '发生错误：' + e.message)

def grand():
    Tester.guimode()

ttk.Button(root, text='普通登录', command=login1).pack()
ttk.Button(root, text='强制离线后登录', command=login2).pack()
if Tester:
    ttk.Button(root, text='Grand模式', command=grand).pack()
ttk.Button(root, text='退出', command=lambda: root.quit()).pack()

root.mainloop()
