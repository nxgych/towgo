#torgo

##Description</br>
torgo is a simple http server framework based tornado

##Installation</br>
download the realease package and unpack it, access the path and execute the command:</br>
python setup.py install

##Tutorial</br>
refer to demo

	server启动参考demo中的main.py
    run server command:
    python main.py --settings=settings.development --port=7777
 
##Instruction</br>    
###1、Server 类：</br>

    server = Server()
    
    #设置服务初始化函数，initialize是一个用于初始化的函数对象,项目的初始化处理可以写在该方法中
    server.setInitMethod(initialize) 
    
    #服务启动
    server.start()   

###2、settings模块</br>
需要在你的应用中创建settings模块，用于区分应用部署的环境。服务启动时可以指定所要加载的配置参数</br>

	python main.py --settings=settings.development --port=7777
	
（1）、MULTI_PROCESS	 ：设为 True 时表示服务以多进程方式启动，设为 False 时以单进程方式启动；</br>
（2）、ASYNC_THREAD_POOL ：设定异步处理的线程池大小；</br>
（3）、LOG ：日志配置；</br>
（4）、APPS ：用于注册你的应用，类型为元组，例如demo中的app包；</br>
（5）、SESSION ：session设置；</br>
 另外torgo中还内置了REDIS、SQLALCHEMY、MYSQL、HBASE等数据库的连接配置和连接模块，你可以根据自己的需要添加配置。

###3、urls.py</br>
在你的应用包中必须包含urls.py，在该文件中定义你的请求路由。</br>

	from tornado.web import url
	from .handlers import test_handler
	
	urls = [
	    #test    
	    url(r'/test', test_handler.TestHandler),
	]

###4、AsyncHandler 类</br>
AsyncHandler 类是一个异步请求的基类，继承于RequestHandler， 用来处理http请求。</br>
如果你需要使用异步非阻塞的请求处理特性，你的handler可以继承该类，post请求需要重写 _post 方法，get请求需要重写 _get 方法。</br>

	from torgo.handler import AsyncHandler
	
	class TestHandler(AsyncHandler):  
	    def _post(self):
	    	pass
	    	
###5、log模块</br>
该模块可以用于多进程环境下的日志处理。</br>	    	
配置中默认添加了info、error、debug三个常用的日志文件，可以直接使用；</br>

	from torgo.log.log_util import CommonLog
	CommonLog.info('---')
	CommonLog.error('---')
	CommonLog.debug('---')
	
你也可以在LOG配置中增加自己的所需要的日志文件；</br>

	from torgo.log.log_util import Log
	
    log = Log('文件名').get_logger()
    log.info('---')	

###6、cache模块</br>
torgo中添加了redis连接模块及api模块，可以方便的选择使用；</br>

	在initialize方法中添加如下代码，用于初始化redis的连接
	
	def initialize():
		from torgo.msetting import settings
	    #init redis
	    from torgo.cache.redis_py import RedisConn
	    for rdb,configs in settings.REDIS.iteritems():
	        RedisConn(rdb,**configs)   
	        
	from torgo.cache.redis_cache import Cache      
	cache = Cache()
	cache.set('a',1) 
	cache.conn.sadd('x','a')
	

   


