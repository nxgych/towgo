#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017年1月9日
@author: shuai.chen
'''

def singleton(cls):  
    """
    singleton decorator
    """
    _instances = {}  
    def _singleton(*args, **kwargs):  
        if cls not in _instances:  
            _instances[cls] = cls(*args, **kwargs)  
        return _instances[cls]  
    return _singleton  
