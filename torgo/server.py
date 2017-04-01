#coding:utf-8

'''
Created on 2017年1月9日
@author: shuai.chen
'''

from __future__ import absolute_import

import os
from multiprocessing import cpu_count
from abc import ABCMeta,abstractmethod

import tornado
from tornado.netutil import bind_sockets
from tornado.web import Application
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import options
from tornado.tcpserver import TCPServer

from .msetting import settings
from .session.manager import SessionManager
from .connection import Connection

class FunctionException(Exception):
    pass

class App(Application):
    """
    application
    """
    
    def __init__(self, **kwargs):
        app_settings = dict(
            template_path=settings.TEMPLATE_PATH,
            static_path=settings.STATIC_PATH,
            cookie_secret=settings.COOKIE_SECRET,
            xsrf_cookies=settings.XSRF_COOKIES,
            debug=settings.DEBUG
        )
        app_settings.update(kwargs)     
        super(App, self).__init__(handlers=self.load_urls(), **app_settings)     
        
        #session register
        sc = settings.SESSION 
        if sc.get("open",False):
            self.session_manager = SessionManager(sc.get('storage'),sc.get('secret'),sc.get('timeout'))
            
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

class TTCPServer(TCPServer):
    '''
    base type of TCPServer that override handle_stream method here
    in order to maintain the connection between servers
    through IOStream.
    '''
    
    def __new__(cls, *args, **kwargs):
        if len(Connection.handler_mappings) <= 0:
            Connection.handler_mappings = cls.load_urls()
        return TCPServer.__new__(cls, *args, **kwargs)

    def handle_stream(self, stream, address):
        Connection(address=address, stream=stream, io_loop=self.io_loop)   
        
    @staticmethod
    def load_urls():
        '''
        load urls
        ''' 
        apps = settings.APPS
        mappings = {}
        for a in apps:
            m = __import__("%s.urls" % a, globals={}, locals={}, fromlist=['urls'])
            for cmdId, handler in m.urls:
                mappings[cmdId] = handler
        return mappings      
    
class BaseServer(object): 
    
    __metaclass__ = ABCMeta   

    def __init__(self, process_num=0, init_method=None, **kwargs):
        '''
        @param process_num: 启动进程数
        @param init_method: init method
        '''
        #设置环境变量
        os.environ.setdefault(settings._SETTINGS_MODULE_ENVIRON, options.settings) 

        if init_method is not None:
            if not hasattr(init_method,'__call__'):
                raise FunctionException("'%s' is not a function" % init_method)
                        
        self.process_num = process_num
        self.init_method = init_method  
        self.kwargs = kwargs
    
    @abstractmethod    
    def start(self):
        raise NotImplementedError    
        
    def intialize(self):
        if self.init_method is not None:
            self.init_method()       

    def setProcessNum(self, num=0):
        '''
        set process num
        '''
        if num >= 0 and num <= cpu_count():
            self.process_num = num
                  
    def setInitMethod(self, method):
        '''
        set init method
        '''
        if not hasattr(method,'__call__'):
            raise FunctionException("'%s' is not a function" % method)
        self.init_method = method
            
class HttpServer(BaseServer):
    """
    @example:
        server = HttpServer()
        server.setInitMethod(func)
        server.start()     
    """
    
    def start(self):
        '''
        start server
        '''
        application = App(**self.kwargs)
        server = HTTPServer(application)  
        if settings.MULTI_PROCESS:
            server.bind(options.port)
            server.start(self.process_num)
        else:
            server.listen(options.port)  
        
        self.intialize()
        IOLoop.instance().start()       

class TcpServer(BaseServer):    
    """
    @example:
        server = TcpServer()
        server.setInitMethod(func)
        server.start()     
    """
            
    def start(self):
        '''
        start server
        '''
        server = TTCPServer(**self.kwargs)
        if settings.MULTI_PROCESS:
            server.bind(options.port)
            server.start(self.process_num)
            for advanced_port in settings.ADVANCED_SERVER_PORT:
                # bind more port if set
                tornado.process.fork_processes(self.process_num)
                sockets = bind_sockets(advanced_port)
                server.add_sockets(sockets)
        else:
            server.listen(options.port)
            
        self.intialize()
        IOLoop.instance().start()  
