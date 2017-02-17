#coding:utf-8

'''
Created on 2017/01/04
@author: shuai.chen
'''

from __future__ import absolute_import

import threading  
from multiprocessing import cpu_count

from .decos import singleton


class _WorkerTask(object):  
    '''
    A task to be performed by the ThreadPool.
    ''' 
  
    def __init__(self, function, *args, **kwargs):  
        self.function = function  
        self.args = args  
        self.kwargs = kwargs  
  
    def __call__(self):  
        self.function(*self.args, **self.kwargs)  
        
        
class _Worker(threading.Thread):  
    '''
    Worker thread
    '''

    def __init__(self, pool, **kwargs):  
        threading.Thread.__init__(self, **kwargs)  
        self.setDaemon(1)
        
        self.pool = pool   
        self.busy = False  
        
        self._started = False  
        self._event = None  

    def work(self):  
        if self._started is True:  
            if self._event is not None and not self._event.isSet():  
                self._event.set()  
        else:  
            self._started = True  
            self.start()  
  
    def run(self):  
        while True:  
            self.busy = True  
            while len(self.pool.tasks) > 0:   
                task = self.pool.tasks.pop() 
                task()  
  
            # Sleep until needed again  
            self.busy = False  
            if self._event is None:  
                self._event = threading.Event()  
            else:  
                self._event.clear()  
            self._event.wait()  
            

@singleton
class TPool(object):
    '''
    Custom thread pool for asynchronous tasks
    @example:
        from torgo.utils.tpool import TPool 
        tpool = TPool(1,1)  
        tpool.addTask(func,*args)    
    '''
    
    def __init__(self, init_threads=1, max_threads=cpu_count()*2):
        '''
        @param init_threads: init thread num
        @param max_threads: max threads num
        '''
        self._max_threads = max_threads
        self._threads = []       
        self.tasks = []  

        self._createWorker(init_threads)
            
    def _createWorker(self, thread_num):
        init_num = min(thread_num, self._max_threads)
        for _ in xrange(init_num):
            self._threads.append(_Worker(self))  

    def _addTask(self, task):  
        self.tasks.append(task)  
  
        worker_thread = None  
        for thread in self._threads:  
            if thread.busy is False:  
                worker_thread = thread  
                break  

        if worker_thread is None and len(self._threads) <= self._max_threads:  
            worker_thread = _Worker(self)  
            self._threads.append(worker_thread)  
              
        if worker_thread is not None:  
            worker_thread.work()  
  
    def addTask(self, function, *args, **kwargs):  
        self._addTask(_WorkerTask(function, *args, **kwargs))  
          

