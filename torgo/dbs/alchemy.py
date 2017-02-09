#coding:utf-8

'''
Created on 2017年1月9日
@author: shuai.chen
'''

import traceback

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

from torgo.msetting import settings
from torgo.log.log_util import CommonLog


class SQLAlchemy(object):
    '''
    sqlalchemy connection class
    '''
    
    _engine = {}
      
    def __new__(cls, dbname='default', *args, **kwargs):
        if dbname not in cls._engine:
            cls._engine[dbname] = cls.connect(dbname, **kwargs)
        return super(SQLAlchemy, cls).__new__(cls)
    
    
    def __init__(self,dbname='default', *args, **kwargs):
        self._dbname = dbname
        
    @staticmethod
    def connect(dbname, **kwargs):
        try:
            configs = kwargs
            conn_url = URL('mysql+mysqldb',**configs)
            alchemy_args = settings.SQLALCHEMY
            return create_engine(conn_url, poolclass=QueuePool,**alchemy_args)
        except:
            CommonLog.error('SQLAlchemy.connect:%s' % traceback.format_exc())
               
    def get_session(self):
        if self._dbname not in self._engine:
            return None
        return sessionmaker(bind=self._engine[self._dbname])


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
    __abstract__ = True
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    
    @declared_attr
    def session(self):
        if hasattr(self, '__connection_name__'):
            return SQLAlchemy(self.__connection_name__).get_session() 
        return SQLAlchemy().get_session()
    
    def as_dict(self):
        return dict((col.name, getattr(self, col.name)) for col in class_mapper(self.__class__).mapped_table.c)
    