# usr/bin/python
# -*- coding:utf-8 -*-
'''
Common Func
Author:Tzboy
From:RZYC
Create time:2017-12-06
'''
import sys
import os
import time
import json
from Mysql import Mysql
import MySQLdb
import re
import urllib
# selenium needs driver  from  https://github.com/mozilla/geckodriver/releases
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import jieba

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append("..")
driver = webdriver.PhantomJS()

def get_path():  
    p=os.path.split(os.path.realpath(__file__))  # ('D:\\workspace\\python\\src\\mysql', 'dao.py') 
    #p=os.path.split(p[0])
    if not p:  
        os.mkdir(p)  
    return p[0]

def log(log_con):
    print log_con
    time_local = time.localtime(time.time())
    dt = time.strftime("%Y-%m-%d",time_local)    
    logpath = get_path()+'/../log/'+dt+'.log'
    file_dir = os.path.split(logpath)[0]
    #判断文件路径是否存在，如果不存在，则创建，此处是创建多级目录
    if not os.path.isdir(file_dir):
        os.makedirs(file_dir)
    #然后再判断文件是否存在，如果不存在，则创建
    if not os.path.exists(logpath ):
        os.system(r'touch %s' % logpath)
    f=open(logpath,'a')
    f.write('[rt_crawler'+str(os.getpid())+']:'+str(log_con))
    f.write('\n')
    f.close()    
'''
文章性质分析（情感类型）：
v1.0 词语包含处理
return 0中性 1正面 2负面
'''
def emotionType(words):
    mysql = Mysql()
    article_config = mysql.getOne("SELECT * from tb_article_config where ac_id=1")
    mysql.dispose()
    words_positive = article_config.get("ac_words_positive",'').split(",")#正面
    words_negative = article_config.get("ac_words_negative",'').split(",")#负面
    type = 0;
    if len(words)>0:
        negaCheck = list(set(words).intersection(set(words_negative)))
        if len(negaCheck)>0:
            type=2
        elif len(list(set(words).intersection(set(words_positive)))):
            type=1
    return type
'''
数据存储
'''
def saveData(target,info):
    comments = info.pop('comments')
    mysql = Mysql()
    if(target.get('check_repeat_type')=='url&title'):
        checkRepeat_title = mysql.getAll("SELECT id from tb_article where title='"+info.get('title')+"'")   
        if len(checkRepeat_title) > 0:
            mysql.dispose()
            return False
    log("SegmentedWords start:")
    words_title = segmentedWords(info.get('title'))
    words_content = segmentedWords(info.get('content_text'))
    words = list(set(words_title+words_content))
    log("SegmentedWords end;")
    insert_set_str = "set emotion_type = "+str(emotionType(words))+","
    info['content'] = unicode(info.get('content').encode("utf-8"));
    for k,v in info.items():
        insert_set_str = insert_set_str+" `"+str(k)+"`= '%s'," %(MySQLdb.escape_string(str(v).encode('utf-8')),)
        
    log("start:"+str(time.time()))
    # 1==1:
    try:
        print insert_set_str
        article_id = mysql.insertOne("insert into tb_article "+str(insert_set_str[:-1]))
        article_id = str(article_id)
        # 评论插入
        if len(comments)>0:
            for c_i in xrange(len(comments)):
                insert_comment_str = "set article_id = "+article_id+","
                for c_k,c_v in comments[c_i].items():
                    insert_comment_str = insert_comment_str+" `"+c_k+"`='%s',"%(MySQLdb.escape_string(str(c_v).encode('utf-8')),)
                mysql.insertOne("insert into tb_article_comment "+insert_comment_str[:-1])
        # 分词插入
        for i in xrange(len(words)):
            if words[i]!='':
                findwords = mysql.getOne("SELECT * from tb_words where w_name='%s'" %(MySQLdb.escape_string(words[i]),))
                if len(findwords)>0:
                    w_a_ids_str = findwords.get("w_a_ids")
                    w_a_ids = w_a_ids_str.split(',')
                    w_a_ids.append(article_id)
                    w_a_ids_str = ','.join(w_a_ids)
                    mysql.update("update tb_words set `w_a_ids`='"+MySQLdb.escape_string(w_a_ids_str)+"',`w_num`="+str(len(w_a_ids))+" where `w_id`="+str(findwords.get('w_id')))
                else:
                    w_a_ids = []
                    w_a_ids.append(article_id)
                    w_a_ids_str = ','.join(w_a_ids)                
                    w_id = mysql.insertOne("insert into tb_words set `w_name`='"+MySQLdb.escape_string(words[i])+"',`w_a_ids`="+w_a_ids_str+",`w_num`="+str(len(w_a_ids)))                                
        mysql.end('commit')
    except Exception as e:
        log("[ERROR]saveData is error:");
        log(e)
        mysql.end()
    log("end:"+str(time.time()))
    mysql.dispose()        
'''
分词器
'''
def segmentedWords(str_data):
    words = []
    try:
        if str_data!=None and str_data!='':
            words = list(jieba.cut_for_search(str_data))
    except Exception as e:
        log("[ERROR]:segmentedWords is error")
        log(e)
    return words

'''
获取爬取目标的配置（DB）
'''
def getDBTargetList():
    mysql = Mysql()
    target_data_list = mysql.getAll("SELECT * from tb_crawler_config where status=1 order by id asc")
    mysql.dispose()
    target_data_list = list(target_data_list)
    for i in xrange(len(target_data_list)):
        target_data_list[i]['headers'] = json.loads(target_data_list[i]['headers'])
        target_data_list[i]['login_info'] = json.loads(target_data_list[i]['login_info'])
        target_data_list[i]['data_rule'] = json.loads(target_data_list[i]['data_rule'])
        target_data_list[i]['url_params'] = json.loads(target_data_list[i]['url_params'])
        target_data_list[i]['comment_rule'] = json.loads(target_data_list[i]['comment_rule'])
    return target_data_list;

'''
重URL中匹配域名
'''
def getHostInURL(url=""):
    host=""
    try:
        proto, rest = urllib.splittype(url)  
        host, rest = urllib.splithost(rest)
    except:
        log("[ERROR]getHostInURL is error for "+url)
    return host
'''
自动格式化URL
'''
def formartURL(hosturl,url):
    res_url = url
    if url and hosturl:
        host = getHostInURL(hosturl)
        if "http" in url:
            return res_url
        elif url[:2]=='//':
            res_url = "http:"+""+url
        elif url[:1]=='/':
            res_url = "http://"+host+""+url
        else:
            res_url = "http://"+""+url
    return res_url
'''
Href去重
'''
def checkRepeat(url=''):
    try:
        mysql = Mysql()
        target_data_list = mysql.getAll("SELECT id from tb_article where href='"+url+"'")
        mysql.dispose()        
        if len(target_data_list) > 0:
            return False
        else:
            return True
    except Exception as e:
        log("[ERROR]checkRepeat is error for "+url)
        log(str(e))
        return False

'''
模拟登录
'''
def simulationLogin(headers,login_info={}):
    global driver
    
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    if len(headers)<0:
        dcap["phantomjs.page.settings.userAgent"] = ("Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36")        
    else:
        for k,v in headers.items():
            dcap["phantomjs.page.settings."+k] = (v)
    driver = webdriver.PhantomJS(executable_path = '/usr/local/bin/phantomjs',desired_capabilities=dcap)
    driver.set_window_size('480','800')
    driver.set_page_load_timeout(30)
    # 判断是否需要预登陆
    if int(login_info.get('need_login'))==1:
        try:
            login_url = login_info.get('url')
            log("[login]Will Login to "+login_url)
            driver.get(login_url);
            log("[loging...]Get logined page sleep(10s)")
            time.sleep(10);
            log("[loging...]Page loaded")
            log("[loging...]input from")
            parmas_len = len(login_info.get("params"))
            for i in xrange(parmas_len):
                param = login_info.get("params")[i]
                if param.get('type') == 'set':
                    if param.get('selector') == 'id':
                        driver.find_element_by_id(param.get('key')).clear()
                        driver.find_element_by_id(param.get('key')).send_keys(param.get('value'))
                    else:
                        driver.find_element_by_css_selector(param.get('key')).clear()
                        driver.find_element_by_css_selector(param.get('key')).send_keys(param.get('value'))                        
                elif param.get('type') == 'click':
                    if param.get('selector') == 'id':
                        driver.find_element_by_id(param.get('key')).click()
                    else:
                        driver.find_element_by_css_selector(param.get('key')).click()
            
            log("[loging...]submit form sleep(10s)")
            time.sleep(10);
            log("[loging...]Logined!")
        except Exception as e:
            log("[ERROR]:Login is False")
            log(str(e))
    else:
        log("Not need login")



# 小工具
def formartParamsToUrl(dict_data):
    params_str = "?"
    for k,v in dict_data.items():
        params_str = params_str+k+"="+str(v)+"&"
    return params_str[:-1]