#coding:utf-8

'''
Created on 2017年1月9日
@author: shuai.chen
'''

from __future__ import absolute_import

import os
from multiprocessing import cpu_count

from tornado.web import Application
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import options

from .msetting import settings
from .session.manager import SessionManager

class FunctionException(Exception):
    pass

class App(Application):
    """
    application
    """
    
    def __init__(self):
        app_settings = dict(
            template_path=settings.TEMPLATE_PATH,
            static_path=settings.STATIC_PATH,
            cookie_secret=settings.COOKIE_SECRET,
            xsrf_cookies=settings.XSRF_COOKIES,
            debug=settings.DEBUG
        )     
        super(App, self).__init__(handlers=self.load_urls(), **app_settings)     
        
        #session register
        sc = settings.SESSION 
        if sc["open"]:
            self.session_manager = SessionManager(sc['storage'],sc['secret'],sc['timeout'])
            
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
    
    def __init__(self, process_num=0, init_method=None):
        '''
        @param process_num: 启动进程数
        @param init_method: init method
        '''
        #设置环境变量
        os.environ.setdefault(settings._SETTINGS_MODULE_ENVIRON, options.settings) 

        if init_method is not None:
            if not hasattr(init_method,'__call__'):
                raise FunctionException("'%s' is not a function" % init_method)
                        
        self.__process_num = process_num
        self.__init_method = init_method  
    
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

    def setProcessNum(self, num=0):
        '''
        set process num
        '''
        if num >= 0 and num <= cpu_count():
            self.__process_num = num
                  
    def setInitMethod(self, method):
        '''
        set init method
        '''
        if not hasattr(method,'__call__'):
            raise FunctionException("'%s' is not a function" % method)
        self.__init_method = method
            