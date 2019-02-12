#coding:utf-8


import traceback
              
def initialize():
    '''
    initialize method
    '''   
    from towgo.log.log_util import CommonLog
    try:         
        from towgo.msetting import settings
        #init redis
        from towgo.cache.db_cache import RedisCache
        for cn,configs in settings.REDIS.items():
            RedisCache.connect(cn,**configs)        
    except:
        CommonLog.error("initialize: %s" % traceback.format_exc())
