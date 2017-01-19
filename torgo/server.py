#coding:utf-8

'''
Created on 2017年1月9日
@author: shuai.chen
'''

from __future__ import absolute_import

from multiprocessing import cpu_count

from tornado.web import Application
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import options

from .msetting import settings

class FunctionException(Exception):
    pass

class App(Application):
    """
    application
    """
    
    def __init__(self):
        super(App, self).__init__(handlers=self.load_urls(), debug=False)   
    
    @staticmethod
    def load_urls():
        '''
        load urls
        ''' 
        apps = settings.APPS
        urls = []
        for a in apps:
            m = __import__("%s.urls" % a, globals={}, locals={}, fromlist=['urls'])
            urls.extend(m.urls)
        return urls  
    
    
class Server(object):
    
    def __init__(self):
        self.__init_method = None  
        self.__process_num = 0
    
    def start(self):
        '''
        start server
        '''
        application = App()
        server = HTTPServer(application)  
        if settings.MULTI_PROCESS:
            server.bind(options.port)
            server.start(self.__process_num)
        else:
            server.listen(options.port)  
        
        self.intialize()
        IOLoop.instance().start()  
        
    def intialize(self):
        if self.__init_method is not None:
            self.__init_method()       
      
    def setInitMethod(self, method):
        if not hasattr(method,'__call__'):
            raise FunctionException("'%s' is not a function" % method)
        self.__init_method = method
    
    def setProcessNum(self, num=0):
        if num >= 0 and num <= cpu_count():
            self.__process_num = num
            