#coding:utf-8

'''
Created on 2017年1月4日
@author: shuai.chen
'''

from __future__ import absolute_import

import json
import time
from abc import ABCMeta,abstractmethod

from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor

from tornado import escape
from tornado import gen
from tornado.web import RequestHandler
from tornado.web import asynchronous
from tornado.web import HTTPError

from .msetting import settings
from .session.manager import Session

class AsyncHandler(RequestHandler):
    '''
    async base http handler
    @example:
        class TestHandler(AsyncHandler):  
            def _post(self):
                pass    
    '''
    
    __metaclass__ = ABCMeta
    
    executor = ThreadPoolExecutor(settings.ASYNC_THREAD_POOL)

    def __init__(self, *args, **kwargs):
        super(AsyncHandler, self).__init__(*args, **kwargs)
        #set session
        if settings.SESSION.get('open',False):
            self.session = Session(self.application.session_manager, self)
    
    @asynchronous
    @gen.coroutine
    def get(self):
        try:
            yield self._async_execute_get() 
        except:
            raise 
        finally:
            if not self._finished: self.finish()    
                  
    @asynchronous
    @gen.coroutine
    def post(self):
        try:
            yield self._async_execute_post() 
        except:
            raise
        finally:
            if not self._finished: self.finish()    
             
    @run_on_executor
    def _async_execute_get(self):
        return self._get()

    @run_on_executor
    def _async_execute_post(self):
        return self._post()
        
    def _get(self):
        raise HTTPError(405)

    def _post(self):
        raise HTTPError(405)
                   
    def prepare(self):
        super(AsyncHandler, self).prepare()    

    def get_session(self, key=None):
        '''
        get from session
        '''
        if key is not None:
            return self.session.get(str(key))
        return self.session.get(self.session.session_id)
    
    def set_session(self, obj=None, key=None):
        '''
        put into session
        '''
        if key is not None:
            self.session[str(key)] = obj
        else:
            self.session[self.session.session_id] = obj
        self.session.save()
                    
    def get_body_params(self):
        """
        get post params as json
        """
        try:
            body = self.request.body
            return escape.json_decode(body) if body else {}
        except:
            raise Exception("params error")
        
class AsyncHttpHandler(AsyncHandler):
    """
    async base http handler
    """      

class TcpHandler(object):
    
    __metaclass__ = ABCMeta
    
    def __init__(self,request):
        """
        TCP base handler
        """
        if isinstance(request, Request):
            self.request = request
        else:
            raise TypeError 

    @abstractmethod
    def process(self):
        '''
        This method needs to be overridden.
        '''
        raise NotImplementedError     

class Request(object):
    
    def __init__(self, address=None, body=None):
        """
        TCP request
        """
        self.address = address
        self.body = json.loads(body) if body is not None else {}
        
        self.cmdId = self.body.get('cmdId')
        self.timestamp = int(self.body.get('timestamp', time.time()*1000))
        self.params = self.body.get('params',{})

    def as_json(self):
        return json.dumps({'address':self.address, 'body':self.body})
        