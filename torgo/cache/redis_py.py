#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on 2016年4月22日
@author: shuai.chen
'''

import redis
import traceback

from torgo.log.log_util import CommonLog


class RedisConn(object):
    """
    redis connection class
    """

    _pools = {}

    def __new__(cls, rdb='default', *args, **kwargs):
        if rdb not in cls._pools:
            cls._pools[rdb] = cls.connect(rdb, **kwargs)
        return super(RedisConn, cls).__new__(cls)
    
    def __init__(self,rdb='default', *args, **kwargs):
        self.rdb = rdb
        self._connection = redis.Redis(connection_pool = self._pools[rdb])  
        
    @staticmethod
    def connect(rdb, **kwargs):
        try:
            return redis.ConnectionPool(**kwargs)
        except:
            CommonLog.error('redis connect error:'+traceback.format_exc())
       
    def get_conn(self):
        if not self._pools[self.rdb]:
            return None
        return self._connection
    