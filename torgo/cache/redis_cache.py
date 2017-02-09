#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on 2016年4月21日
@author: shuai.chen
'''

import cPickle as pickle

from redis_py import RedisConn


class Cache(object):

    def __init__(self, rdb='default'):
        self.conn = RedisConn(rdb).get_conn()
    
    def get_conn(self):
        return self.conn
    
    def __set(self,key,value,expire=0,add_only=False):
        """
        REDIS set
        @param param: 
            key: KEY
            value: VALUE
            expire:生命期   单位s
            add_only:是否只增加不覆盖   默认覆盖
        """
        if expire > 0:
            if add_only:
                added = self.conn.setnx(key, value)
                if added:
                    self.conn.expire(key, expire)
                return added
            return self.conn.setex(key, value, expire)            
        else:
            if add_only:
                return self.conn.setnx(key, value)
            return self.conn.set(key, value)            

    def set(self, key, value, expire=0):
        """
            设置string型数据
        """
        return self.__set(key, value, expire)    

    def get(self, key):
        """
            获取string型 数据
        """
        return self.conn.get(key)
    
    def set_obj(self, key, data, expire=0):
        """
            存储 PYTHON 对象   
        """
        if data is None:
            return False
        val = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
        return self.__set(key, val, expire)
        
    def get_obj(self, key):  
        """
            获取 PYTHON 对象    
        """  
        val = self.conn.get(key)
        if val is None:
            return None
        return pickle.loads(val) 
