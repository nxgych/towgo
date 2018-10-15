#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017/01/09
@author: shuai.chen
'''

from __future__ import absolute_import

import os
import warnings

from tornado.options import options
from tornado.util import import_object

from . import gsetting

SETTINGS_MODULE_ENVIRON = gsetting._SETTINGS_MODULE_ENVIRON

class ConfigException(Exception):
    pass


class _Settings(object):
    '''
    settings manager
    '''
    
    def __contains__(self, item):
        setting = _Settings.settings_object()
        return hasattr(setting, item)

    def __getattr__(self, item):
        setting = _Settings.settings_object()
        if hasattr(setting, item):
            config = getattr(setting, item)
        else:
            raise ConfigException('settings "%s" not exist' % item)
        return config   

    @classmethod
    def settings_object(cls):
        
        if not hasattr(cls, '_sett'):
            cls._sett = gsetting
            try:
                sett_obj = import_object(options.settings)
                cls._sett.__dict__.update(sett_obj.__dict__)
            except AttributeError:
                if os.environ.get(SETTINGS_MODULE_ENVIRON, None):
                    sett_obj = import_object(os.environ[SETTINGS_MODULE_ENVIRON])
                    cls._sett.__dict__.update(sett_obj.__dict__)
                else:
                    raise ConfigException(
                        'tornado.options not have "settings",You may try to use settings before "define settings module"')
            except ImportError:
                cls._sett = gsetting
                warnings.warn('settings file import error')

        return cls._sett    
    
settings = _Settings()    