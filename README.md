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
    server.setInitMethod(initialize) #initialize是一个用于初始化的函数对象
    server.start()   

###2、settings模块</br>
必须在你的应用中创建settings模块，用于区分应用部署环境。</br>
配置中的APPS 用于注册你的应用，类型为元组，例如demo中的app包。</br>

###3、urls.py</br>
在你的应用包中必须包含urls.py，在该文件中定义你的请求路由。</br>

	from tornado.web import url
	from .handlers import test_handler
	
	urls = [
	    #test    
	    url(r'/test', test_handler.TestHandler),
	]

###4、AsyncHandler 类</br>
AsyncHandler 类是一个异步请求的基类，继承于RequestHandler， 用来处理http 请求。</br>
如果你需要使用异步非阻塞的请求处理特性，你的handler可以继承该类，post请求需要重写 _post 方法，get请求需要重写 _get 方法。</br>

	from torgo.handler import AsyncHandler
	
	class TestHandler(AsyncHandler):  
	    def _post(self):
	    	pass
	    	
###5、log模块</br>
该模块可以用于多进程环境下的日志处理</br>	    	



   



