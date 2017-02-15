#coding:utf-8

'''
Created on 2017年1月5日
@author: shuai.chen
'''

import os

#--------------------------basic configuration below-------------------------
PROJECT_PATH = os.path.dirname(os.path.dirname(__file__))

MULTI_PROCESS = True
ASYNC_THREAD_POOL = 50

#debug
DEBUG = False

#static path
STATIC_PATH = os.path.join(PROJECT_PATH,'static')

#templates path
TEMPLATE_PATH = os.path.join(PROJECT_PATH,'templates')

#xsrf configuration
XSRF_COOKIES = False
COOKIE_SECRET = "TORGO_COOKIE_SECRET"

#session configuration
SESSION = {
    "open":False, #是否开启session           
    "storage":"torgo.cache.redis_cache.Cache",
    "secret":"TORGO_SESSION_SECRET",
    "timeout": 7*24*3600
}

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

#--------------------------optional configuration below-------------------------

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

#sqlalchemy & mysql configuration
SQLALCHEMY = {
              "echo":False,
              "pool_size":100,
              "pool_recycle":3600,
              "max_overflow":10,
}
MYSQL = {         
        "default":{
                 "host":"127.0.0.1",
                 "port":3306,
                 "username":"root",
                 "password":"root",
                 "database":"dbname",
                 "query":{'charset':'utf8'}
        }       
}

#hbase configuration
HBASE = {
    "host":"127.0.0.1",
    "port":9090     
}

#elasticsearch configuration
ES = {
    "nodes":[{"host":"127.0.0.1","port":9200}],
    "sniffer_timeout":60,
    "timeout":20
}