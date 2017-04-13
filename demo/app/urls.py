#coding:utf-8

'''
Created on 2017年1月5日
@author: shuai.chen
'''

from .handlers import test_handler

'''
HTTP server
'''
urls = [
    #test  
    # (url , handler)    
    (r'/test', test_handler.TestHandler),
]

"""

'''
TCP server
'''
urls = [
    # (cmdId , handler)    
    (1, test_handler.TestHandler),       
]
"""