#coding:utf-8

'''
Created on 2017年1月3日
@author: shuai.chen
'''

from __future__ import absolute_import

import tornado
from tornado.options import define

define("port", default=8603, help="running on the port : 8603", type=int)
define("settings", default='settings.development', help="running on the environment : development", type=str)

if __name__ == "__main__":
    '''
    run server command:
    python main.py --settings=settings.development --port=8603
    '''  
    tornado.options.parse_command_line()

    from towgo.server import TwistedHttpServer # TornadoHttpServer
    from demo.app import initialize
    
    server = TwistedHttpServer()
    server.setInitMethod(initialize)
    
    server.start()
    