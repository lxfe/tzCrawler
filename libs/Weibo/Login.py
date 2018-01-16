import weiboLogin
import urllib2
import re
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

def login():
    username = '18380473385'
    pwd = 'tanzhen&19940808'      #我的新浪微博的用户名和密码
    weibologin = weiboLogin.WeiboLogin(username, pwd)   #调用模拟登录程序
    if weibologin.Login():
        print "登陆成功..！"  #此处没有出错则表示登录成功
    else:
        print "登录失败"

login()
print urllib2.urlopen('http://weibo.com').read()