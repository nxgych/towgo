# towgo

## Description</br>
towgo is a simple web server framework based both tornado and twisted

## Installation</br>
download the realease package and unpack it, access the path and execute the command:</br>
python setup.py install

## Tutorial</br>
参考demo，执行main.py脚本启动服务
 
## Instruction</br>    
### 1、Server 类：</br>

    #tornado http server
    server = TornadoHttpServer()
    #tornado tcp server
    #server = TornadoTcpServer()
    
    #设置服务初始化函数，initialize是一个用于初始化的函数对象,项目的初始化处理可以写在该方法中
    server.setInitMethod(initialize) 
    
    #服务启动
    server.start()   

### 2、settings模块</br>
需要在你的应用中创建settings模块，用于区分应用部署的环境。服务启动时可以指定所要加载的配置参数</br>

	python main.py --settings=settings.development --port=7777
	
（1）、MULTI_PROCESS	 ：设为 True 时表示服务以多进程方式启动，设为 False 时以单进程方式启动；</br>
（2）、THREAD_POOL_SIZE ：设定线程池大小；</br>
（3）、LOG ：日志配置；</br>
（4）、APPS ：用于注册你的应用，类型为元组，例如demo中的app包；</br>
（5）、SESSION ：session设置,注意由于session存放在redis中，开启session时，需要配置 REDIS 或 CODIS 数据库，并保证可正常使用；</br>
 另外towgo中还内置了REDIS、CODIS、SQLALCHEMY、MYSQL、HBASE等数据库的连接配置和连接模块，你可以根据自己的需要添加配置。

### 3、urls.py</br>
在你的应用包中必须包含urls.py，在该文件中定义你的请求路由。</br>

    #http server
	 from .handlers import test_handler
	
	 urls = [
	    #test 
	    # (url , handler)   
	    (r'/test', test_handler.TestHandler),
	 ]
	
	 #tcp server
	 from .handlers import test_handler
	
	 urls = [
	    # (cmdId , handler)    
	    (1, test_handler.TestHandler),       
	 ]	

### 4、Handler 类</br>
TornadoHttpHandler/TwistedHttpHandler 类是一个异步请求的基类，用来处理http请求。</br>
如果你需要使用异步非阻塞的请求处理特性，你的handler可以继承该类，post请求需要重写 _post 方法，get请求需要重写 _get 方法。</br>

	from torgo.handler import TornadoHttpHandler,TwistedHttpHandler
	
	class TestHandler(TornadoHttpHandler):  
	    def _post(self):
	    	self.write('hello, world!')

	class TestHandler(TwistedHttpHandler):  
	    def _post(self):
	    	return 'hello, world!'
	    		    	
TcpHandler 用于处理tcp请求的基类， 需要重写 process 方法。</br>	 
 
	from torgo.handler import TcpHandler
	
	class TestHandler(TcpHandler):  
	    def process(self):
	    	return 'hello, world!' 	
	    	
### 5、log模块</br>
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

### 6、cache模块</br>
towgo中添加了redis及分布式缓存系统codis连接模块及api模块，可以方便的选择使用；</br>

	先定义initialize方法，Server实例需要设置initialize方法；
	在initialize方法中添加如下代码，用于初始化redis的连接
	
	def initialize():
		from torgo.msetting import settings
	    #init redis
	    #codis：from torgo.cache.db_cache import CodisCache 
	    from torgo.cache.db_cache import RedisCache
	    for rdb,configs in settings.REDIS.iteritems():
	        RedisCache(rdb,**configs)   
	        
	from torgo.cache.db_cache import RedisCache  #codis：from torgo.cache.db_cache import CodisCache   
	cache = RedisCache()
	cache.set('a',1) 
	cache.conn.sadd('x','a')

### 7、utils模块</br>
utils中加入了线程池、http request等工具类，可选择使用；</br>	

    #线程池使用示例：
	from torgo.utils.tpool import TPool 
    tpool = TPool(1,1)  
    tpool.addTask(str,100)
   


