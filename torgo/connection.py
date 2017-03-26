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

from .msetting import settings
from .handler import TcpHandler, Request

logger = logging.getLogger(__name__)

class Connection(object):
    '''
    TCP Connection is the base Class for server and client communication.
    Each connection between Server and client-server will be
    maintained by a `Connection` instance.
    Connection will read the request from IOStream and handle
    the requests.
    When a request handling is over, the Connection will automatically
    read the stream to get the next request.
    '''

    #async thread pool executor
    executor = ThreadPoolExecutor(settings.ASYNC_THREAD_POOL)
        
    #handler mappings
    handler_mappings = {}

    #clients record
    clients = {}

    def __init__(self, stream, address, io_loop):
        Connection.clients[address] = self
        
        self._stream = stream
        self._address = address
        self.io_loop = io_loop
        
        self._stream.set_close_callback(self.on_close)
        self.read_request()
        
        logger.info("New Connection from server: %s" % address)

    def read_request(self):
        try:
            self._stream.read_until('\n', self.handle_request)
        except StreamClosedError,e:
            raise e

    def write(self, message):
        try:
            self._stream.write(message)
        except Exception, e:
            raise e
        
    @gen.coroutine
    def handle_request(self, data):
        tmp_body = data[:-1]

        request = Request(address=self._address, body=tmp_body)
        cmdId = request.cmdId
        handler = self.handler_mappings.get(cmdId)
        
        if not handler:
            self.write("Unknown handler!")
        else:
            handler_instance = handler(request)
    
            if isinstance(handler_instance,TcpHandler):
                res = yield gen.Task(self.get_response, handler_instance)
                self.write(res)
            else:
                self.write("Illegal request!")        

        self.read_request()
    
    @run_on_executor    
    def get_response(self, instance):  
        return instance.process()    

    def on_close(self):
        logger.info("Server connection has been closed: %s" % self._address)
        Connection.clients.pop(self._address)
        