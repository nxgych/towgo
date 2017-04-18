#coding:utf-8

'''
Created on 2017年1月4日
@author: shuai.chen
'''

from __future__ import absolute_import

import time
import datetime
from abc import ABCMeta,abstractmethod

from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor

from tornado import escape
from tornado import gen
from tornado.web import RequestHandler
from tornado.web import asynchronous
from tornado.web import HTTPError
from tornado.httputil import format_timestamp

from twisted.internet import threads
from twisted.web import server
from twisted.web.resource import Resource, NoResource
from twisted.web.util import redirectTo
from mako.lookup import TemplateLookup

from .session.manager import Session
from .session.manager import SessionManager
from .msetting import settings
from .utils import TowgoException

class TornadoHttpHandler(RequestHandler):
    '''
    tornado async http base handler
    @example:
        class TestHandler(TornadoHttpHandler):  
            def _post(self):
                return 'hello world'   
    '''
    
    __metaclass__ = ABCMeta
    
    executor = ThreadPoolExecutor(settings.THREAD_POOL_SIZE)

    def __init__(self, *args, **kwargs):
        super(TornadoHttpHandler, self).__init__(*args, **kwargs)
        
        #set session
        if self.application.session_manager is not None:
            self.session = Session(self.application.session_manager, self)
        else:
            self.session = None    
    
    @asynchronous
    @gen.coroutine
    def get(self):
        try:
            result = yield self._async_execute_get()
            if result is not None:
                self.finish(result)
        except:
            raise
        finally:
            if not self._finished: self.finish()            
                  
    @asynchronous
    @gen.coroutine
    def post(self):
        try:
            result = yield self._async_execute_post()
            if result is not None:
                self.finish(result)
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
        '''
        http get method
        '''        
        raise HTTPError(405)

    def _post(self):
        '''
        http post method
        '''        
        raise HTTPError(405)
                   
    def prepare(self):
        '''Called at the beginning of a request before  `_get`/`_post`'''
        super(TornadoHttpHandler, self).prepare()    

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
        '''
        get post body params
        '''
        try:
            body = self.request.body
            return escape.json_decode(body) if body else {}
        except:
            raise TowgoException("Params error!")    

#session configuration
sc = settings.SESSION 

class TwistedHttpHandler(Resource):
    '''
    twisted async http base handler
    @example:
        class TestHandler(TwistedHttpHandler):  
            def _post(self):
                return 'hello, world!'    
    '''
        
    _lookup = TemplateLookup(output_encoding='utf-8', encoding_errors='replace', **settings.MAKO)
    
    #session register
    session_manager = None 
    if sc.get("open",False):
        session_manager = SessionManager(sc.get('storage'),sc.get('secret'),sc.get('timeout'))
                    
    def __init__(self):
        Resource.__init__(self)
        self.request = None
        self.session = None
                    
    def _set_request(self, request):
        self.request = request    
        self.request.setHeader("Content-Type","text/html; charset=utf-8")
        #set session
        if self.session_manager is not None:
            self.session = Session(self.session_manager, self)
                
    def write(self, context):
        '''write result'''
        self.request.write(context)  
        self.request.finish()   
        
    def error(self, failure):   
        self.request.write(failure)  
        self.request.finish()  

    def render_GET(self, request):
        self._set_request(request)
        d = threads.deferToThread(self.get)
        d.addCallback(self.write) 
        d.addErrback(self.error)         
        return server.NOT_DONE_YET

    def render_POST(self, request):
        self._set_request(request)
        d = threads.deferToThread(self.post)
        d.addCallback(self.write)  
        d.addErrback(self.error)     
        return server.NOT_DONE_YET
    
    def prepare(self):
        '''Called at the beginning of a request before  `_get`/`_post`'''
        pass
    
    def get(self):
        result = self.prepare()
        if result is not None:
            return result
        return self._get()

    def post(self):
        result = self.prepare()
        if result is not None:
            return result
        return self._post()

    def redirect(self, url):
        '''redirect url'''
        return redirectTo(url, self.request)
        
    def _get(self):
        '''
        http get method
        '''
        return "method '_get' : NotImplementedError"
        
    def _post(self):
        '''
        http post method
        '''        
        return "method '_post' : NotImplementedError"

    def getChild(self, path, request):
        return self
    
    def render_string(self, template_name, **kwargs):
        '''
        @param template_name: template file name
        Renders the mako template with the given arguments as the response
        '''
        template = self._lookup.get_template(template_name) 
        return template.render_unicode(**kwargs).encode('utf-8','replace')
        
    def get_argument(self, name, default=None):   
        arg = self.request.args.get(name) 
        return arg[0] if arg else default
    
    def get_arguments(self, name, default=[]):
        return self.request.args.get(name, default) 

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
    
    def get_secure_cookie(self, key):
        if self.request is None:
            return None
        return self.request.getCookie(key)
    
    def set_secure_cookie(self, key, value, expires_days=30):
        if self.request is not None:
            expires = datetime.datetime.utcnow() + datetime.timedelta(days=expires_days)
            self.request.addCookie(key, value, expires=format_timestamp(expires))
                    
    def get_body_params(self):
        '''
        get post body params
        ''' 
        try:
            body = self.request.content.read()
            return escape.json_decode(body) if body else {}
        except:
            raise TowgoException("Illegal JSON string!")  

class TwistedRootHandler(TwistedHttpHandler):

    def _get(self):
        return "Welcome to use towgo!"

    def _post(self):
        return self._get()
            
    def getChild(self, path, request):
        path = request.path
        if path == '/':
            return self
        if path in self.children:
            resource = self.children.get(path)
            return resource()
        return NoResource()    
    
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

    def prepare(self):
        pass

    @abstractmethod
    def process(self):
        '''
        This method needs to be overridden.
        '''
        raise NotImplementedError     
    
    def execute(self):
        result = self.prepare()
        if result is not None:
            return result
        return self.process()
            
class Request(object):
    
    def __init__(self, address=None, body=None):
        """
        TCP request
        @param body: request data as a JSON string and end with '\0'
            {
                "cmdId" : 1,  #required
                "timestamp" : 1231312131231,  #option,  ms
                "params" : { } #option 
            }\0    
        """
        self.address = address
        if not body:
            self.body  = {}
        else:    
            try:
                self.body = escape.json_decode(body[:-1] if body.endswith('\0') else body) 
            except:
                raise TowgoException("Illegal JSON string!")    
                    
        self.cmdId = self.body.get('cmdId')
        if self.cmdId is None:
            raise TowgoException("Unknown cmdId!")
        
        self.timestamp = int(self.body.get('timestamp', time.time()*1000))
        self.params = self.body.get('params',{})
        
    def __getattr__(self, name):
        return self.body.get(name)    
        
    def __repr__(self):
        return "address : %s, body : %s" % (self.address, self.body) 
    
    def as_dict(self):
        return self.__dict__
    
    def get_client_ip(self):
        return self.address
    
    def get_argument(self, name, default=None):
        return self.params.get(name) or default
    
class Result(object):
    '''
    TCP common result
    '''
    
    def __init__(self, cmdId, message=""):
        self.cmdId = cmdId
        self.message = message
        
    def __call__(self):
        return self.as_json()        
    
    def as_json(self):
        return escape.json_encode(self.__dict__)
    