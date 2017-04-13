#coding:utf-8

'''
Created on 2017年1月4日
@author: shuai.chen
'''

from __future__ import absolute_import

import os

from .logger import Logger
from towgo.msetting import settings

class InitException(Exception):  
    """
    初始化异常
    """
    def __init__(self,ft,allows):
        super(InitException,self).__init__()
        self.ft = ft
        self.allows = allows  
    
    def __str__(self):
        return "'{0}' not in {1}".format(self.ft,str(self.allows))
  
    
class Log(object):
    '''
    @example:
        log = Log('文件名').get_logger()
        log.info('---')
    '''
    
    LOGS = {}
    
    def __new__(cls, ft, *args, **kwargs):
        if ft not in cls.LOGS:
            log_config = settings.LOG
            files = log_config['files']
            if ft not in files:
                raise InitException(ft,files)
            
            path = log_config['path']
            if not os.path.exists(path):
                os.mkdir(path)
            
            fn = os.path.join(path,"{0}.{1}".format(ft,"log"))
            cls.LOGS[ft] = Logger(
                                  ft,fn,files[ft],
                                  log_config.get("when","MIDNIGHT"),
                                  log_config.get('backup_count',10),
                                  log_config.get("suffix","%Y-%m-%d"),
                                  log_config.get('console',False)
                                  )
        return super(Log, cls).__new__(cls)    

    def __init__(self, ft, *args, **kwargs):
        self._ft = ft
        
    def get_logger(self):   
        logger = self.LOGS[self._ft]
        return logger.get_logger()


class CommonLog(object):
    """
    常用日志: 
        仅支持info、error、debug
    其他日志文件使用:
        log = Log('文件名').get_logger()
        log.info('---')
    """

    info = Log('info').get_logger().info
    error = Log('error').get_logger().error
    debug = Log('debug').get_logger().debug
        