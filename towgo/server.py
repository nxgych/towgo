#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017年1月9日
@author: shuai.chen
'''

from __future__ import absolute_import

import os, sys
from multiprocessing import cpu_count
from abc import ABCMeta,abstractmethod

import tornado
from tornado.netutil import bind_sockets
from tornado.web import Application
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import options
from tornado.tcpserver import TCPServer
from tornado.web import url

from twisted.python import log
from twisted.internet.protocol import ServerFactory
from twisted.web import server
from twisted.internet import reactor

from .msetting import settings
from .session.manager import SessionManager
from .handler import TornadoRootHandler, TwistedRootHandler
from .connection import TornadoConnection, TwistedConnection

class FunctionException(Exception):
    pass

class TornadoApp(Application):
    """
    tornado application
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
        super(TornadoApp, self).__init__(handlers=self.load_urls(), **app_settings)     
        
        #session register
        self.session_manager = None
        sc = settings.SESSION 
        if sc.get("open",False):
            self.session_manager = SessionManager(sc.get('storage'),sc.get('secret'),sc.get('timeout'))
            
    @staticmethod
    def load_urls():
        '''
        load urls
        ''' 
        apps = settings.APPS
        urls = [url(r'/', TornadoRootHandler)]
        for a in apps:
            m = __import__("%s.urls" % a, globals={}, locals={}, fromlist=['urls'])
            urls.extend([url(p,h) for p,h in m.urls])
        return urls  

class TornadoTCPServer(TCPServer):
    '''
    base type of TCPServer that override handle_stream method here
    in order to maintain the connection between servers
    through IOStream.
    '''
    
    def __new__(cls, *args, **kwargs):
        TornadoConnection.handler_mappings = cls.load_urls()
        return TCPServer.__new__(cls, *args, **kwargs)

    def handle_stream(self, stream, address):
        TornadoConnection(address=address, stream=stream, io_loop=self.io_loop)   
        
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

class TwistedSite(object):
    '''
    twisted http site
    '''
    
    def __new__(cls, *args, **kwargs):
        return cls.load_urls()
    
    @staticmethod
    def load_urls():
        root = TwistedRootHandler()
        apps = settings.APPS
        for a in apps:
            m = __import__("%s.urls" % a, globals={}, locals={}, fromlist=['urls'])
            for path, handler in m.urls:
                root.putChild(path, handler)
        return server.Site(root)

class TwistedServerFactory(ServerFactory):
    '''
    twisted tcp server factory
    '''
 
    protocol = TwistedConnection

    def __init__(self, *args, **kwargs):
        TwistedConnection.handler_mappings = self.load_urls()
        self.clients_max = kwargs.get('clients_max',10000)    
        
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
        
    def initialize(self):
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

class TornadoTcpServer(BaseServer):    
    """
    @server:
        server = TornadoTcpServer()
        server.setInitMethod(func)
        server.start()   
        
    @client:
        import socket 
        import json 
          
        HOST = '127.0.0.1'    # The remote host  
        PORT = 7777           # The same port as used by the server  
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        s.connect((HOST, PORT))  
        
        data = json.dumps({"cmdId":1}) + "\0"  # json string end with '\0'
        s.sendall(data)  
        
        result = s.recv(65535)  
        print 'received:', repr(result)  
        
        s.close()       
    """
    
    def _start(self, server):
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
            
        self.initialize()
        IOLoop.instance().start() 
                    
    def start(self):
        '''
        start server
        '''
        server = TornadoTCPServer(**self.kwargs)
        self._start(server)  

class TornadoHttpServer(TornadoTcpServer):
    """
    @server:
        server = TornadoHttpServer()
        server.setInitMethod(func)
        server.start()     
    """
    
    def __init__(self, ssl_options=None):
        self.ssl_options = ssl_options
    
    def start(self):
        '''
        start server
        '''
        application = TornadoApp(**self.kwargs)
        server = HTTPServer(application, ssl_options=self.ssl_options)  
        self._start(server)

class TwistedTcpServer(BaseServer):
    """
    single process twisted tcp server
    @server:
        server = TwistedTcpServer()
        server.setInitMethod(func)
        server.start()   
        
    @client:
        import socket 
        import json 
          
        HOST = '127.0.0.1'    # The remote host  
        PORT = 7777           # The same port as used by the server  
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        s.connect((HOST, PORT))  
        
        data = json.dumps({"cmdId":1})  # json string 
        s.sendall(data)  
        
        result = s.recv(65535)  
        print 'received:', repr(result)  
        
        s.close()       
    """
    
    def _start(self, factory):
        log.startLogging(sys.stdout)
        reactor.suggestThreadPoolSize(settings.THREAD_POOL_SIZE)
        reactor.callWhenRunning(self.initialize)   
        reactor.listenTCP(options.port, factory)
        reactor.run()
                    
    def start(self):
        '''
        start server
        '''
        factory = TwistedServerFactory(**self.kwargs)
        self._start(factory)      

class TwistedHttpServer(TwistedTcpServer):      
    """
    single process twisted http server
    @server:
        server = TwistedHttpServer()
        server.setInitMethod(func)
        server.start()     
    """
    
    def start(self):
        '''
        start server    
        '''
        factory = TwistedSite()
        self._start(factory)   
