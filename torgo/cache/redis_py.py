#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on 2016年4月22日
@author: shuai.chen
'''

import redis

from torgo.msetting import settings


class Connection(object):
    """
    redis connection class
    """
    _pools = {}

    def __new__(cls, rdb='default', *args, **kwargs):
        if rdb not in cls._pools:
            cls._pools[rdb] = cls.connect(rdb, **kwargs)
        return super(Connection, cls).__new__(cls)
    
    def __init__(self,rdb='default', *args, **kwargs):
        self.rdb = rdb
        self._connection = redis.Redis(connection_pool = self._pools[rdb])  
        
    @staticmethod
    def connect(rdb, **kwargs):
        try:
            config = kwargs or settings.REDIS[rdb]
            return redis.ConnectionPool(**config)
        except:
            raise
       
    def get_conn(self):
        if not self._pools[self.rdb]:
            return None
        return self._connection
    