#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017年1月9日
@author: shuai.chen
'''

import os

#--------------------------required configuration below-------------------------
PROJECT_PATH = os.path.dirname(os.path.dirname(__file__))

#settings环境变量，请勿修改
_SETTINGS_MODULE_ENVIRON = "TOWGO_SETTINGS"

MULTI_PROCESS = True   #multiple process if true 
THREAD_POOL_SIZE = 50   #async thread pool size or twisted thread pool size

#static path
STATIC_PATH = os.path.join(PROJECT_PATH,'static')

#templates path
TEMPLATE_PATH = os.path.join(PROJECT_PATH,'templates')

#tornado advanced port
TORNADO_ADVANCED_SERVER_PORT = ()

COOKIE_SECRET = "TOWGO_COOKIE_SECRET"
#tornado xsrf configuration
TORNADO_XSRF_COOKIES = False
#tornado debug switch
TORNADO_DEBUG = False

#default is False. True:use mako template, False:use tornado template
TORNADO_USE_MAKO = False

#mako templates
MAKO = {
    "directories": [TEMPLATE_PATH], 
    "filesystem_checks": False,
    "collection_size": 500        
}

#session configuration
SESSION = {
    "open":False, #是否开启session
    "storage":"towgo.cache.local_cache.LocalCache",
    "secret":"TOWGO_SESSION_SECRET",
    "timeout": 7*24*3600
}

#log configuration
LOG = {        
    "path":os.path.join(PROJECT_PATH,'logs'), #日志文件路径
    "files":{'info':"INFO",'error':"ERROR",'debug':"DEBUG"}, #{filename:level}
    "when":"MIDNIGHT", #切换周期
    "suffix":"%Y-%m-%d", #根据切换周期添加的文件后缀
    "backup_count":10,  #日志文件存放期限（day）
    "console":False,    #是否开启日志在控制台输出
}

#app register
APPS = ()

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

#codis configuration
CODIS={
       "default":{
           "zookeeper_address":"127.0.0.1:2181", #zookeeper 地址
           "zookeeper_path":"/jodis/cache", 
           "db":0   #redis db
       }
}

#sqldb pool
SQLDB_POOL = {
            "mincached": 1,
            "maxcached": 5,
            "maxconnections": 100,
            "blocking": True
}
#sqlalchemy
SQLALCHEMY = {
              "echo":False,
              "pool_size":100,
              "pool_recycle":3600,
              "max_overflow":10,
}
#Mysql configuration
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

#Hbase configuration
HBASE = {
    "default":{
        "host":"127.0.0.1",
        "port":9090
    }     
}

#Elasticsearch configuration
ES = {
    "default":{
        "nodes":[{"host":"127.0.0.1","port":9200}],
        "sniffer_timeout":60,
        "timeout":20
    }
}
