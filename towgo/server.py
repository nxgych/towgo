#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017年1月9日
@author: shuai.chen
'''

from __future__ import absolute_import

import os, sys
from os import environ
from sys import executable
from socket import AF_INET  
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
            xsrf_cookies=settings.TORNADO_XSRF_COOKIES,
            debug=settings.TORNADO_DEBUG
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
        return TCPServer.__new__(cls)

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
    
    def __new__(cls):
        return cls.load_urls()
    
    @staticmethod
    def load_urls():
        root = TwistedRootHandler()
        apps = settings.APPS
        for a in apps:
            m = __import__("%s.urls" % a, globals={}, locals={}, fromlist=['urls'])
            for path, handler in m.urls:
                root.putChild(path.encode('UTF8'), handler)
        return server.Site(root)

class TwistedTCPFactory(ServerFactory):
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

    def __init__(self):
        #设置环境变量
        os.environ.setdefault(settings._SETTINGS_MODULE_ENVIRON, options.settings) 
                        
        self.process_num = cpu_count()
        self.init_method = None
    
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
        self.process_num = min(num, cpu_count())
                  
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

    def __init__(self, **kwargs):
        super(TornadoTcpServer, self).__init__()
        self.server_frame = "tornado"
        self.kwargs = kwargs
                    
    def start(self):
        '''
        start server
        '''
        server = TornadoTCPServer(**self.kwargs)
        self._start(server)  

    def _start(self, server):
        if settings.MULTI_PROCESS:
            server.bind(options.port)
            server.start(self.process_num)
            for advanced_port in settings.TORNADO_ADVANCED_SERVER_PORT:
                # bind more port if set
                tornado.process.fork_processes(self.process_num)
                sockets = bind_sockets(advanced_port)
                server.add_sockets(sockets)
        else:
            server.listen(options.port)
            
        self.initialize()
        IOLoop.instance().start() 
        
class TornadoHttpServer(TornadoTcpServer):
    """
    @server:
        server = TornadoHttpServer()
        server.setInitMethod(func)
        server.start()     
    """
        
    def start(self):
        '''
        start server
        '''
        ssl_options = self.kwargs.pop('ssl_options', None)
        application = TornadoApp(**self.kwargs)
        server = HTTPServer(application, ssl_options=ssl_options)  
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
    
    def __init__(self, *args, **kwargs):
        super(TwistedTcpServer, self).__init__()
        self.server_frame = "twisted"
        self.factory = TwistedTCPFactory(*args, **kwargs)
                    
    def start(self):
        '''
        start server
        '''
        log.startLogging(sys.stdout)
        reactor.suggestThreadPoolSize(settings.THREAD_POOL_SIZE)
        reactor.callWhenRunning(self.initialize)
        
        if settings.MULTI_PROCESS:
            args = sys.argv
            fd = int(args[-1]) if args[-1].isdigit() else None
            
            if fd is None:
                sargs = [arg for arg in args[1:] if arg.startswith('--')]
                # Create a new listening port and several other processes to help out.                                                                     
                port = reactor.listenTCP(options.port, self.factory)
                for _ in range(self.process_num):
                    reactor.spawnProcess(
                            None, executable, [executable, args[0]] + sargs + [str(port.fileno())],
                        childFDs={0: 0, 1: 1, 2: 2, port.fileno(): port.fileno()},
                        env=environ)
            else:
                # Another process created the port, just start listening on it.                                                                            
                port = reactor.adoptStreamPort(fd, AF_INET, self.factory)
        else:
            reactor.listenTCP(options.port, self.factory) 
                   
        #run    
        reactor.run()   

class TwistedHttpServer(TwistedTcpServer):      
    """
    single process twisted http server
    @server:
        server = TwistedHttpServer()
        server.setInitMethod(func)
        server.start()     
    """

    def __init__(self, *args, **kwargs):
        super(TwistedHttpServer, self).__init__(*args, **kwargs)
        self.factory = TwistedSite()
        