#coding:utf-8

              
def initialize():
    '''
    initialize method
    '''        
    from torgo.msetting import settings
    #init redis
    from torgo.cache.redis_py import RedisConn
    for rdb,configs in settings.REDIS.iteritems():
        RedisConn(rdb,**configs)        

