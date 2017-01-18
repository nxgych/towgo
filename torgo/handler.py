#coding:utf-8

'''
Created on 2017年1月4日
@author: shuai.chen
'''

import traceback
from abc import ABCMeta

from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor

from tornado import escape
from tornado import gen
from tornado.web import RequestHandler
from tornado.web import asynchronous
from tornado.web import HTTPError

from torgo.msetting import settings
from torgo.log.log_util import CommonLog


class AsyncHandler(RequestHandler):
    '''
    async base handler
    '''
    
    __metaclass__ = ABCMeta
    
    executor = ThreadPoolExecutor(settings.ASYNC_THREAD_POOL)

    @asynchronous
    @gen.coroutine
    def get(self):
        try:
            result = yield self._async_execute_get() 
            self.write(result) 
        except:
            class_name = self.__class__.__name__.split('_')[0]
            CommonLog.error("%s error: %s" % (class_name, traceback.format_exc()))
            self.write("server error!")  
        finally:
            if not self._finished: self.finish()    
                  
    @asynchronous
    @gen.coroutine
    def post(self):
        try:
            result = yield self._async_execute_post() 
            self.write(result) 
        except:
            class_name = self.__class__.__name__.split('_')[0]
            CommonLog.error("%s error: %s" % (class_name, traceback.format_exc()))
            self.write("server error!")  
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
                
    def get_body_params(self):
        """
        get post params as json
        """
        try:
            body = self.request.body
            return escape.json_decode(body) if body else {}
        except:
            CommonLog.error('body parse error:'+traceback.format_exc())
            raise Exception("params error")
        