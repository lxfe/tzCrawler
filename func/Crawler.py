# usr/bin/python
# -*- coding:utf-8 -*-
'''
The crawler main
Author:Tzboy
From:RZYC
Create time:2017-12-07 
'''
import BaseUtil as baseUtil
from pyquery import PyQuery as pq
import os
import time
import sys

reload(sys)
sys.setdefaultencoding("utf-8")

class Crawler(object):
    
    def __init__(self,target_list=[]):
        self.target_list = target_list
    
    # 从目标池中抽取目标
    def getTarget(self):
        if len(self.target_list)>0:
            target = self.target_list.pop(0)
            return target
        else:
                return ""
        
    # 分析数据采集页面
    def analysisPageInfo(self,target,url):
        info_rule = target.get("data_rule").get("info_rule")
        baseUtil.log("Load url")
        try:
            baseUtil.driver.get(url)
        except Exception:
            baseUtil.log("Load Time out,will return!")
            return None
        baseUtil.log("Loaded url")
        time.sleep(6)
        # 评论采集-数据加载  START
        comment_rule = target.get("comment_rule")
        if int(comment_rule.get("need_comment"))==1:
            if int(comment_rule.get("comment_page_type"))==2:
                for i in xrange(int(comment_rule.get("max_comment_page"))):
                    # 判断 当有按钮时  点击按钮 没有按钮时 滚动
                    try:
                        if comment_rule.get('comment_page_key') and len(baseUtil.driver.find_elements_by_css_selector(comment_rule.get("comment_page_key"))) ==0:
                            js="var p = document.body.scrollTop=100000"
                            baseUtil.driver.execute_script(js)
                            baseUtil.log("Auth Comment scrollTop")
                        else:
                            baseUtil.driver.find_element_by_css_selector(comment_rule.get("comment_page_key")).click()
                            baseUtil.log("Click Comment scrollTop")
                    except:
                        baseUtil.log("No found Click target for "+comment_rule.get('comment_page_key'))
                    time.sleep(2);
        else:
            baseUtil.log("Skip Commont!")
        # 评论采集-数据加载  END
        html = baseUtil.driver.page_source
        doc = pq(html)
        save_data = {}
        save_data['href']=url
        save_data['crawler_time']=int(time.time())
        save_data['site_name'] = target.get('target_name')
        save_data['site_id'] = target.get('id')
        save_data['source_type'] = target.get('source_type')
        # 数据采集
        for k,v in info_rule.items():
            k_v = None
            k_v_find = doc.find(v.get("find"))
            if v.get("getType")=='text':
                k_v = k_v_find.text()
            elif v.get("getType")=='attr':
                if v.get("attr_key"):
                    k_v = k_v_find.attr(v.get("attr_key"))
                else:
                    baseUtil.log("[ERROR]:data rule is error  target is :"+target.get("target_url"))
            elif v.get("getType") == 'html':
                k_v = k_v_find.html()
            
            if v.get("formart")=='time_0' and k_v!='':
                k_v = time.mktime(time.strptime(k_v, "%Y-%m-%d %H:%M"))                
            elif v.get("formart")=='time_1' and k_v!='':
                k_v = time.mktime(time.strptime(k_v, "%Y-%m-%d %H:%M:%S"))
            elif v.get("formart")=='time_2' and k_v!='':
                k_v = time.mktime(time.strptime(k_v, "%Y-%m-%d"))
            elif v.get("formart")=='time_3' and k_v!='':
                k_v = int(k_v)/1000
            elif v.get("formart")=='time_4' and k_v!='':
                k_v = k_v.replace('年','-')
                k_v = k_v.replace('月','-')
                k_v = k_v.replace('日','')
                k_v = time.mktime(time.strptime(k_v, "%Y-%m-%d %H:%M:%S"))
            elif v.get("formart")=='time_5' and k_v!='':
                k_v = time.mktime(time.strptime(k_v, "%Y/%m/%d %H:%M"))
            elif v.get("formart")=='time_6' and k_v!='':
                k_v = k_v.replace('年','-')
                k_v = k_v.replace('月','-')
                k_v = k_v.replace('日','')
                k_v = time.mktime(time.strptime(k_v, "%Y-%m-%d%H:%M"))
            elif v.get("formart")=='str_int' and k_v!='':
                k_v = filter(lambda ch: ch in'0123456789.',k_v)
            elif v.get("formart")=='formart_url' and k_v!='':
                k_v = baseUtil.formartURL(target.get("target_url"),k_v);
            save_data[k] = k_v
        # 评论数据采集
        save_data['comments'] = []
        if int(comment_rule.get("need_comment"))==1:
            comment_lines = doc.find(comment_rule.get('comment_line'))
            for comment_line in comment_lines.items():
                comment_line_data = {}
                for k,comment in comment_rule.get("info_rule").items():
                    if k and comment.get("find"):
                        comment_find = comment_line.find(comment.get("find"))
                        c_v = None
                        if comment.get("getType")=='text':
                            c_v = comment_find.text()
                        elif comment.get("getType")=='attr':
                            if comment.get("attr_key"):
                                c_v = comment_find.attr(comment.get("attr_key"))
                            else:
                                baseUtil.log("[ERROR]:Comment rule is error  target is :"+target.get("target_url"))
                        elif comment.get("getType") == 'html':
                            c_v = comment_find.html()
                        
                        if comment.get("formart")=='formart_url' and c_v!='':
                            c_v = baseUtil.formartURL(target.get("target_url"),c_v);                    
                        comment_line_data[k] = c_v
                comment_line_data['crawler_time'] = time.time()
                save_data['comments'].append(comment_line_data)
                
        if save_data['content']:
            save_data['create_time'] = save_data.get('create_time') and int(save_data.get('create_time')) or int(time.time())
            baseUtil.saveData(target,save_data)
        
    # 分析站点 爬取目标数据采集页面
    def getAnalysisHtml(self,target):
        baseUtil.log("Analysis begin…………")
        info_urls = []
        # 分页类型 2||3 为滚动加载  加载完分页数据之后再抽取页面源代码
        if int(target.get("page_type"))==1 or int(target.get("page_type"))==2:
            url_params_str = baseUtil.formartParamsToUrl(target.get('url_params'))
            print target.get("target_url")
            baseUtil.driver.get(target.get("target_url")+url_params_str)
            time.sleep(16);
            baseUtil.log("Get html…………")
            try:
                for i in xrange(target.get('max_crawler_page')):
                    #分页类型2 不会有加载更多的点击按钮 所以直接滚动
                    if int(target.get("page_type"))==1:
                        js="var p = document.body.scrollTop=100000"
                        baseUtil.driver.execute_script(js)
                        baseUtil.log("Auth scrollTop");
                    else:
                        # 判断 当有按钮时  点击按钮 没有按钮时 滚动
                        if len(baseUtil.driver.find_elements_by_css_selector(target.get("page_params_key"))) ==0:
                            js="var p = document.body.scrollTop=100000"
                            baseUtil.driver.execute_script(js)
                            baseUtil.log("Auth scrollTop");
                        else:
                            baseUtil.driver.find_element_by_css_selector(target.get("page_params_key")).click()
                            baseUtil.log("Click scrollTop");
                    time.sleep(6)
            except:
                baseUtil.log('[ERROR] not found scroll selector');
            #获取加载分页后的源代码
            html = baseUtil.driver.page_source
            #print html
            doc = pq(html)
            if target.get('data_rule').get('get_info_address_type') == 'tag_href':
                datas_href_items = doc.find(target.get('data_rule').get('get_info_address_value'))
                for data_href in datas_href_items.items():
                    info_urls.append(data_href.attr("href"))
        # 分页类型为1 需要循环加载分页页面 并单独抽取源代码
        elif int(target.get("page_type"))==0:
            url_params = target.get('url_params')
            for i in xrange(target.get('max_crawler_page')):
                url_params[target.get('page_params_key')]=i
                url_params_str = baseUtil.formartParamsToUrl(url_params)                
                baseUtil.driver.get(target.get("target_url")+url_params_str)
                time.sleep(6);
                baseUtil.log("Get html…………")                
                #获取加载分页后的源代码
                html = baseUtil.driver.page_source
                doc = pq(html)
                if target.get('data_rule').get('get_info_address_type') == 'tag_href':
                    datas_href_items = doc.find(target.get('data_rule').get('get_info_address_value'))
                    for data_href in datas_href_items.items():
                        info_urls.append(data_href.attr("href"))
        for i in xrange(0,len(info_urls)):
            info_url = info_urls[i]
            host = baseUtil.getHostInURL(target.get("target_url"))
            if "http" in info_url:
                info_url_host = baseUtil.getHostInURL(info_url)
                if info_url_host.find(info_url_host) == -1:
                    continue
            elif info_url[:2]=='//':
                info_url = "http:"+""+info_url
            elif info_url[:1]=='/':
                info_url = "http://"+host+""+info_url
            else:
                info_url = "http://"+""+info_url
            baseUtil.log("target_url:"+info_url);
            if baseUtil.checkRepeat(info_url):
                baseUtil.log("Pass checkRepeat");
                self.analysisPageInfo(target,info_url)
                time.sleep(2)
    
    def crawler_run(self,target):
        baseUtil.simulationLogin(target['headers'],target['login_info'])
        self.getAnalysisHtml(target) 
        
    # 对单目标进行爬取
    def crawler(self):
        hasUrl = True
        while hasUrl:
            target = self.getTarget()
            # 判断是否已经取完目标
            if target != "":
                # 预登录处理
                self.crawler_run(target);
            else:
                hasUrl = False
        baseUtil.log("Crawler is over!!!!!!!!!!!!!");