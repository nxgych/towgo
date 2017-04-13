#coding:utf-8

'''
Created on 2017年1月3日
@author: shuai.chen
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

    #tornado server
    from towgo.server import TornadoHttpServer
    from demo.app import initialize
    server = TornadoHttpServer()
    server.setInitMethod(initialize)
    
    server.start()

    #mutiprocess twisted server
#     from demo import mtws
#     f = mtws.__file__
#     execfile(f.replace('pyc', 'py'))
    