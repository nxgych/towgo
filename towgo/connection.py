#coding:utf-8

'''
@author: shuai.chen
Created on 2017年3月26日
'''
from __future__ import absolute_import

import logging

from concurrent.futures.thread import ThreadPoolExecutor
from tornado import gen
from tornado.concurrent import run_on_executor
from tornado.iostream import StreamClosedError

from twisted.internet import threads, protocol

from .msetting import settings
from .handler import TcpHandler, Request, Result

logger = logging.getLogger(__name__)

class TornadoConnection(object):
    '''
    Tornado TCP Connection is the base Class for server and client communication.
    Each connection between Server and client-server will be
    maintained by a `Connection` instance.
    Connection will read the request from IOStream and handle
    the requests.
    When a request handling is over, the Connection will automatically
    read the stream to get the next request.
    '''

    #async thread pool executor
    executor = ThreadPoolExecutor(settings.THREAD_POOL_SIZE)
        
    #handler mappings
    handler_mappings = {}
    #clients record
    clients = {}

    def __init__(self, stream, address, io_loop):
        TornadoConnection.clients[address] = self
        
        self._stream = stream
        self._address = address
        self.io_loop = io_loop
        
        self._stream.set_close_callback(self.on_close)
        self.read_request()

        logger.info("Connection created: %s" % str(address))

    def read_request(self):
        try:
            # delimiter : \0
            self._stream.read_until("\0", self.handle_request)
        except StreamClosedError,e:
            raise e

    def write(self, message):
        try:
            self._stream.write(message)
        except StreamClosedError, e:
            logger.warn("Stream closed!")    
        except Exception, e:
            raise e
        
    @gen.coroutine
    def handle_request(self, data):
        request = Request(address=self._address, body=data)
        cmdId = request.cmdId
        handler = self.handler_mappings.get(cmdId)
        
        if not handler:
            self.write(Result(cmdId,'Unknown handler!')())
        else:
            handler_instance = handler(request)
    
            if isinstance(handler_instance,TcpHandler):
                res = yield gen.Task(self.get_response, handler_instance)
                self.write(res)
            else:
                self.write(Result(cmdId,'Illegal request!')())       

        self.read_request()
    
    @run_on_executor    
    def get_response(self, instance):  
        return instance.execute()    

    def on_close(self):
        logger.info("Connection closed: %s" % str(self._address))
        TornadoConnection.clients.pop(self._address)
    
    @classmethod    
    def get_client(cls, address): 
        return cls.clients.get(address)   

class TwistedConnection(protocol.ProcessProtocol):
    '''
    twisted tcp process protocol
    '''

    #handler mappings
    handler_mappings = {}
    #clients record
    clients = {}
             
    def __init__(self):
        self.client_ip = None
    
    def connectionMade(self):
        self.client_ip = self.transport.getPeer()
        logger.info("Connection created: %s" % str(self.client_ip))

        if len(TwistedConnection.clients) >= self.factory.clients_max:
            self.client_ip = None
            self.transport.loseConnection()
            logger.warn("More than %d connections!" % self.factory.clients_max)
        else:
            TwistedConnection.clients[self.client_ip] = self
    
    def connectionLost(self, reason):
        logger.info("Connection closed: %s" % str(self.client_ip))
        if self.client_ip is not None:
            TwistedConnection.clients.pop(self.client_ip)
    
    def dataReceived(self, data):
        request = Request(address=self.client_ip, body=data)
        cmdId = request.cmdId
        handler = self.handler_mappings.get(cmdId)

        def error(failure):
            logger.error(failure)
            self.write(Result(cmdId,'Handler error!')()) 
                    
        if not handler:
            self.write(Result(cmdId,'Unknown handler!')())
        else:
            handler_instance = handler(request)   
            if isinstance(handler_instance, TcpHandler):               
                d = threads.deferToThread(handler_instance.execute)
                d.addCallback(self.write).addErrback(error)
            else:
                self.write(Result(cmdId,'Illegal request!')())              
                                
    def write(self, data):
        self.transport.write(data)    

    @classmethod    
    def get_client(cls, client_ip): 
        return cls.clients.get(client_ip)    
