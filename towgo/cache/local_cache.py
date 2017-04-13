#coding:utf-8

'''
Created on 2017年1月7日
@author: shuai.chen
'''

from towgo.utils.decos import singleton
from towgo.utils.extend import DiffExpireDict
 
@singleton
class LocalCache(object):
    '''
    local storage
    '''
    
    _store = DiffExpireDict()
    
    def __len__(self):
        return len(self._store)
    
    def __contains__(self, key):   
        return key in self._store
    
    def __getitem__(self, key):
        return self._store.get(key)
    
    def __setitem__(self, key, (value, expire)):
        self._store[key] = value, expire
        
    def __delitem__(self, key):    
        return self._store.pop(key) 
    
    def __repr__(self):
        return self._store.__repr__()
    
    def get_conn(self):
        return self
    
    def get_size(self):
        return len(self._store)
    
    def has_key(self, key):
        return key in self._store 
    
    def get(self, key):
        return self._store.get(key)
    
    def set(self, key, value, expire=0):
        self._store[key] = value,expire
        
    def setex(self, key, value, expire=0):  
        self._store[key] = value,expire  
        
    def ttl(self, key):   
        return self._store.ttl(key) 
        
    def remove(self, key):
        return self._store.pop(key)   
    
    def clear(self):
        self._store.clear()
        