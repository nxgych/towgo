#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017年1月9日
@author: shuai.chen
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL

# from sqlalchemy.pool import NullPool
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import class_mapper

from sqlalchemy import exc
from sqlalchemy import event
from sqlalchemy.pool import Pool

from towgo.msetting import settings

class Connection(object):
    '''
    sqlalchemy orm connection class for mysql
    '''  
    _engine = {}
      
    def __new__(cls, conn_name='default', *args, **kwargs):
        if conn_name not in cls._engine:
            cls.connect(conn_name, **kwargs)
        return super(Connection, cls).__new__(cls)
      
    def __init__(self,conn_name='default', *args, **kwargs):
        self._conn_name = conn_name
        
    @classmethod
    def connect(cls, conn_name, **kwargs):
        configs = kwargs or settings.MYSQL[conn_name]
        conn_url = URL('mysql+mysqldb',**configs)
        alchemy_args = settings.SQLALCHEMY
        cls._engine[conn_name] = create_engine(conn_url, poolclass=QueuePool,**alchemy_args)
               
    def get_session(self):
        if self._conn_name not in self._engine:
            return None
        return sessionmaker(bind=self._engine[self._conn_name])

@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # raise DisconnectionError - pool will try
        # connecting again up to three times before raising.
        raise exc.DisconnectionError()
    cursor.close()
        
MetaBaseModel = declarative_base()
class BaseModel(MetaBaseModel):
    '''
    sqlalchemy base model
    @example:
        from sqlalchemy import *
        #define model
        class Demo(BaseModel):
            id = Column('id',BigInteger,primary_key=True,autoincrement=True,nullable=False)
            account = Column('account',String(32), unique=True, nullable=False)
            password = Column('password',String(32),nullable=False)
        
        #create instance
        demo = Demo()
        demo.account = 'abc'
        demo.password = '123456'
        
        #commit
        session = Demo.session()
        try:
            session.add(demo)
            session.commit()
        except:
            if session:session.rollback()
        finally:
            if session:session.close()   
    '''
        
    __abstract__ = True
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    
    @declared_attr
    def session(self):
        if hasattr(self, '__connection_name__'):
            return Connection(self.__connection_name__).get_session() 
        return Connection().get_session()
    
    def as_dict(self):
        return {col.name:getattr(self, col.name) for col in class_mapper(self.__class__).mapped_table.c}
    