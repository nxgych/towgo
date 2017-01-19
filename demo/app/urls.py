#coding:utf-8

'''
Created on 2017年1月5日
@author: shuai.chen
'''

from tornado.web import url
from .handlers import test_handler

urls = [
    #test    
    url(r'/test', test_handler.TestHandler),
]