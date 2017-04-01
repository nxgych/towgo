#coding:utf-8

'''
Created on 2017年1月18日
@author: shuai.chen
'''

import traceback
from torgo.handler import AsyncHttpHandler

from torgo.log.log_util import CommonLog

class TestHandler(AsyncHttpHandler):    
    """
    test
    overwrite '_post' or '_get'
    """
    def _post(self):
        try:
            params = self.get_body_params()
            uid = params['uid']
            CommonLog.info("uid:" + uid)
            self.write("success")
        except:
            CommonLog.error('TestHandler:'+traceback.format_exc())
            self.write("error")
            
    def _get(self):
        try:
            uid = self.get_argument('uid','')
            CommonLog.info("uid:" + uid)
            self.write("success")
        except:
            CommonLog.error('TestHandler:'+traceback.format_exc())
            self.write("error")                
        