#coding:utf-8

'''
Created on 2017年1月3日
@author: shuai.chen
@qq: 815738968
@email: nxgych@163.com
'''

from __future__ import absolute_import

import tornado
from tornado.options import define

define("port", default=7777, help="running on the port : 7777", type=int)
define("settings", default='settings.development', help="running on the environment : development", type=str)


if __name__ == "__main__":
    '''
    run server command:
    python main.py --settings=settings.development --port=7777
    '''    
    tornado.options.parse_command_line()

    from torgo.server import Server
    from demo.app import initialize
    server = Server()
    server.setInitMethod(initialize)
    
    server.start()    
