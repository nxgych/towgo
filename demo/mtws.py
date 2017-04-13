#coding:utf-8

'''
Created on 2017年4月13日
@author: shuai.chen
'''

#mutiprocess twisted server script

import sys
from os import environ
from sys import executable
from socket import AF_INET  
from multiprocessing import cpu_count

from tornado.options import options
from twisted.internet import reactor
            
#mutiprocess twisted server
def main(fd=None):    
    from towgo.server import TwistedHttpServer
    from demo.app import initialize
    server = TwistedHttpServer()
    server.setInitMethod(initialize)
    
    from towgo.msetting import settings
    reactor.suggestThreadPoolSize(settings.THREAD_POOL_SIZE)
    reactor.callWhenRunning(server.initialize)        

    #http
    from towgo.server import TwistedSite
    site = TwistedSite()
        
    if settings.MULTI_PROCESS:
        if fd is None:
            # Create a new listening port and several other processes to help out.                                                                     
            port = reactor.listenTCP(options.port, site)
            num = cpu_count()
            for _ in range(num):
                reactor.spawnProcess(
                        None, executable, [executable, __file__, str(port.fileno())],
                    childFDs={0: 0, 1: 1, 2: 2, port.fileno(): port.fileno()},
                    env=environ)
        else:
            # Another process created the port, just start listening on it.                                                                            
            port = reactor.adoptStreamPort(fd, AF_INET, site)
    else:
        reactor.listenTCP(options.port, site)
    
    #run    
    reactor.run()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        main()
    else:
        main(int(sys.argv[1]))
        