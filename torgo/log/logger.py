#coding:utf-8

'''
Created on 2017年1月4日
@author: shuai.chen
'''

import logging

from mlogger import MultiProcessTimedRotatingFileHandler

class Logger(object):
    
    suffix = "%Y-%m-%d"
    fmt = "[%(asctime)s]-%(filename)s:%(lineno)s-%(levelname)s - %(message)s"
          
    def __init__(self, ft, log_file, level, backup_count=10, console=False):
        """
        @param param: 
            log_file:日志文件
            console:是否需要控制台输出
        """
        self.logger = logging.getLogger(ft)     
           
        self.initialize(log_file, backup_count, console)    
        self.set_level(level)   

    def initialize(self,fname,backup_count,console):      
        filehandle = MultiProcessTimedRotatingFileHandler(fname,"MIDNIGHT",1,
                                                backupCount=backup_count,encoding="utf-8")
        filehandle.suffix = self.suffix         
        formatter = logging.Formatter(fmt=self.fmt)
        filehandle.setFormatter(formatter)
        self.logger.addHandler(filehandle)  
    
        if console:
            consolehandle = logging.StreamHandler() 
            consolehandle.setFormatter(formatter)            
            self.logger.addHandler(consolehandle)          
   
    def get_logger(self):
        return self.logger
           
    def set_level(self, level):
        logger_level = getattr(logging, level, logging.INFO)
        self.logger.setLevel(logger_level) 
        