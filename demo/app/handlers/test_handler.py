#coding:utf-8

'''
Created on 2017年1月18日
@author: shuai.chen
'''

import traceback
from towgo.handler import TwistedHttpHandler #TornadoHttpHandler

from towgo.log.log_util import CommonLog

class TestHandler(TwistedHttpHandler):    
    """
    test
    overwrite '_post' or '_get'
    """
    def _post(self):
        try:
            params = self.get_body_params()
            uid = params['uid']
            CommonLog.info("uid:" + uid)
            return 'hello, world!'
        except:
            CommonLog.error('TestHandler:'+traceback.format_exc())
            return 'error'
            
    def _get(self):
        try:
            uid = self.get_argument('uid','')
            CommonLog.info("uid:" + uid)
            return 'hello, world!'
        except:
            CommonLog.error('TestHandler:'+traceback.format_exc())
            return 'error'           
        