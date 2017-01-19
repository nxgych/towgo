#coding:utf-8

'''
Created on 2017年1月5日
@author: shuai.chen
'''

import os

PROJECT_PATH = os.path.dirname(os.path.dirname(__file__))

MULTI_PROCESS = True
ASYNC_THREAD_POOL = 50

#log configuration
LOG = {        
    "path":os.path.join(PROJECT_PATH,'logs'),
    "files":{'info':"INFO",'error':"ERROR",'debug':"DEBUG"}, #{filename:level}
    "suffix":"log",
    "console":False,    #是否开启日志在控制台输出
    "backup_count":10,  #日志文件存放期限（day）
}

#app register
APPS = ('app',)

#redis configuration
REDIS = {
    "default":{
        "host":"127.0.0.1",
        "port":6379,
        "db":0,
        "password":"",
        "max_connections":100   
    }   
}