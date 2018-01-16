# usr/bin/python
# -*- coding:utf-8 -*-
import func.BaseUtil as baseUtil
import time
from func import Crawler
from multiprocessing import Pool
import os
import sys
import atexit
import signal 

#def crawler_pool(this,target):
    #print 'Pool run: %s',(target['target_name'],);
    #this.crawler_run(target);
    
#def crawler_run():
    #target_list = baseUtil.getDBTargetList()
    #cr = Crawler.Crawler();
    #p = Pool(1)
    #for i in xrange(len(target_list)):
        #p.apply_async(crawler_pool, args=(cr,target_list[i],))
    #print('Waiting for all subprocesses done...')
    #p.close()
    #p.join()
def crawler_run():
    #baseUtil.log('is run');
    while True:
        target_list = baseUtil.getDBTargetList()
        #print target_list
        crawler = Crawler.Crawler(target_list)
        crawler.crawler()

if __name__ == '__main__':
    #with daemon.DaemonContext():
    crawler_run()