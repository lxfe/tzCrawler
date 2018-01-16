# usr/bin/python
# -*- coding:utf-8 -*-
import MySQLdb
import sys

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append("..")
import config
'''
pip intall mysql-python ERROR:
Command "python setup.py egg_info" failed with error code 1 in /tmp/pip-build-M2mlzM/mysql-python/
do:
apt-get install libmysqlclient-dev
'''
class db(object):
    def __init__(self):
        # 打开数据库连接
        db_config = config.getConfig('db');
        self.db = MySQLdb.connect(db_config.get('host'),db_config.get('user'),db_config.get('pwd'),db_config.get('name'),db_config.get('port'),charset='utf8')
        # 使用cursor()方法获取操作游标 
        self.cursor = self.db.cursor(cursorclass = MySQLdb.cursors.DictCursor)
        
    def select_db(self,table,field="*",condition=''):
        try:
            sql = 'select %s from %s '%(field,table)
            if condition!='':
                sql = sql + " where "+condition
            # 执行SQL语句
            self.cursor.execute(sql)
            # 获取所有记录列表
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            print "[ERROR]Mysql sql Error:"
            print e
            return None
        self.db.close();