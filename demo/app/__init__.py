#coding:utf-8


import traceback
              
def initialize():
    '''
    initialize method
    '''   
    from torgo.log.log_util import CommonLog
    try:         
        from torgo.msetting import settings
        #init redis
        from torgo.cache.db_cache import RedisCache
        for cn,configs in settings.REDIS.iteritems():
            RedisCache(cn,**configs)        
    except:
        CommonLog.error("initialize: %s" % traceback.format_exc())
