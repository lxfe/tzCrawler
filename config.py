# usr/bin/python
# -*- coding:utf-8 -*-
'''
Setting up the configuration of the XX and getting these configurations
Author:Tzboy
From:RZYC
Create time:2017-12-06
'''
baseConfig = {
    # DB Configs
    'db':{
        'host':'127.0.0.1',
        'user':'root',
        'pwd':'tzboy',
        'name':'db_tz_crawler',#数据库名
        'port':3306
    }, 
}

def getConfig(keyname=''):
    global baseConfig
    if keyname=='':
        return baseConfig
    else:
        try:
            return baseConfig[keyname]
        except:
            return []
    
