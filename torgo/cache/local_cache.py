#coding:utf-8

'''
Created on 2017年1月7日
@author: shuai.chen
'''

from torgo.utils.decos import singleton


@singleton
class LocalCache(object):
    '''
    local storage
    '''
    
    _store = {}
    
    def get_size(self):
        return len(self._store)
    
    def get(self, key):
        return self._store.get(key, None)
    
    def put(self, key, value):
        self._store[key] = value
        
    def remove(self, key):
        return self._store.pop(key)   
