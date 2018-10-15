#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2016/11/04
@author: willing

HBASE ORM based of happybase
'''


import functools
from abc import ABCMeta

import happybase
from six import iteritems
  

def operate(func):
    '''
    database operate decorator
    '''
    @functools.wraps(func)
    def _deco(self, *args, **kwargs):
        exception = None
        for _ in range(3):
            try:
                with self.pool.connection(timeout=30) as conn:
                    self.check_table(conn)
                    self.table = conn.table(self.table_name)  
                    return func(self, *args, **kwargs)   
            except Exception as e:
                exception = e  
        raise exception                  
    return _deco


class HbaseException(Exception):  
    pass 

class Connection(object):
    '''
    happybase connection class
    you must execute the class method 'connect' before you create a instance of 'Connection'
    @example:
        Connection.connect(host='127.0.0.1',port=9090)
    '''
    
    _conn = {}
    
    def __new__(cls, conn_name="default", *args, **kwargs):
        if conn_name not in cls._conn:
            cls.connect(conn_name, **kwargs)
        return object.__new__(cls)
    
    def __init__(self, conn_name="default", *args, **kwargs):
        '''
        @param conn_name: hbase connection name 
        '''
        table_name, cf = args[0], args[1]
        assert table_name != b""
        
        self.conn_name = conn_name
        self.table_name = table_name.encode("UTF8")
        
        self.cf = self._getColumnFamilyDefault(cf.encode('UTF8'))
        
    @classmethod
    def connect(cls, conn_name="default", **kwargs):
        size = kwargs.pop('pool_size', 10)
        cls._conn[conn_name] = happybase.ConnectionPool(size=size, **kwargs)
    
    @property    
    def pool(self):
        ''' 
        get connection pool
        '''      
        return self._conn[self.conn_name]    

    def check_table(self, conn):
        '''
        check table
        '''
        if self.table_name not in conn.tables():
            conn.create_table(self.table_name, {self.cf: dict()})      
                        
    def _getColumnFamilyDefault(self, cf):
        '''
        get default column family
        '''
        if not cf:
            raise HbaseException('Unknown column family')      
        return b'%s:' % cf if not cf.endswith(b':') else cf               
    
    @operate
    def get(self, key):
        '''
        get one object if the key is exist
        '''
        return self.table.row(key)
    
    @operate
    def gets(self, keys=[]):
        '''
        get several objects by the keys you set
        '''
        if len(keys) <= 0:
            return []
        return self.table.rows(keys)
    
    @operate
    def put(self, key, value={}):
        '''
        put item
        '''
        self.table.put(key, value)
    
    @operate
    def delete(self, key, columns=[]):
        '''
        delete key or columns
        '''
        if len(columns) > 0:
            self.table.delete(key, columns)
        else:
            self.table.delete(key) 
        
class Column(object):
    '''
    hbase column definition class
    '''
    
    def __init__(self, field_name, read_format=None, primary_key=-1):    
        '''
        @param field_name: field name
               if you have several column family, you can add column family as prefix of field name
               and ignore the Model variable '__column_family__'
               like this:
                   id = Column("cf:id",  read_format=str, primary_key=0)
                   age = Column("cfattr:age", read_format=str)   
                   age = Column("cfattr:age", read_format=int)   
        @param read_format: read_format is a function you except to transfer the field value when read from hbase,
               default is None      
        @param primary_key: default is -1,the value means the location of primary key that start with 0,
               you should set the value if you wanna the field value to be part of primary key and 
               it will join by the delimiter sign of the Model variable '__primary_key_delimiter__'.  
        '''               
        if not field_name:
            raise HbaseException("column name must not be null")
        if read_format is not None:
            if not hasattr(read_format,'__call__'):
                raise HbaseException("'%s' is not a function" % read_format)

        self.field_name = field_name.encode("UTF8")
        self.read_format = read_format 
        self.primary_key = primary_key
                
    def getValue(self, value):  
        '''
        get column value
        '''
        if self.read_format is None:
            return value
        return  self.read_format(value) 
    
class Model(object):  
    """
    Base model of hbase,
    you can inherit this class if you hope to use instance method or class method of Model object,
    you must execute the class method 'connect' of 'Connection' class before you use Model
    
    @example:
        class Test(Model):
        
            __table_name__ = "test"
            __column_family__ = "cf:"          # column family default is 'cf:'
            __primary_key_delimiter__ = "_"    # delimiter of primary keys default is '_'      
        
            id = Column("id", read_format=str, primary_key=0)
            name = Column("name", read_format=str)
            age = Column("age", read_format=int)    

        #get
        test = Test.get('a')
        print test.id
        print test.name
        print test.age
    
        #save or update
        test = Test()
        test.id = 1
        test.name = 'abc'
        test.age = 18
        test.save()     
    
        #put with dict
        test = Test()
        test.put(**{'id':1,'name':'xyz','age':22})  
    """
    
    __metaclass__ = ABCMeta
    
    '''
    hbase connection name, defalut is 'default' connection 
    '''
    __connection_name__ = 'default'
        
    '''
    table name, you must define this variable in your model
    '''   
    __table_name__ = ''  
    
    '''
    column family, default is 'cf:', you can redefine this variable in your model
    '''
    __column_family__ = 'cf:'   # column family default is 'cf:'
    
    '''
    delemiter of primary keys, default is '_', you can redefine this variable in your model
    '''
    __primary_key_delimiter__ = b'_'
    
    _primary_keys = []
    _columns = {}
    
    def __new__(cls, *args, **kwargs):
        if len(cls._columns) <= 0:
            pkl = []
            for k,v in iteritems(cls.__dict__):
                if isinstance(v,Column):
                    cls._columns[k] = v.field_name
                    if v.primary_key >= 0 :
                        pkl.append((k,v.primary_key))  
                        
            pkl.sort(key = lambda item:item[1])            
            cls._primary_keys = [k for k,_ in pkl]  
        return object.__new__(cls)
    
    def __init__(self, conn=None):   
        '''
        @param conn: happybase Connection 
        '''
        assert self.__table_name__ != ''
        self._key = ''
        self._conn = conn or Connection(self.__connection_name__, self.__table_name__, self.__column_family__)

    @property    
    def conn(self):
        return self._conn   
    
    @classmethod
    def getConn(cls):
        assert cls.__table_name__ != ''
        return Connection(cls.__connection_name__, cls.__table_name__, cls.__column_family__)
    
    def _getFieldName(self, fname):
        '''
        get field name
        '''
        field_name = self._columns.get(fname, fname)
        if b':' not in field_name:
            return b'%s%s' % (self._conn.cf,field_name)
        return field_name
        
    def _setKeyByPrimaryKey(self, kwargs):  
        '''
        set primary key
        ''' 
        if not self._key:
            primary_key_values = []
            for k in self._primary_keys:
                v = kwargs.get(k)
                if not v:
                    raise HbaseException("Value of primary key cannot be '%s'" % v)
                primary_key_values.append(v)

            if len(primary_key_values) > 0:
                self._key = self.__primary_key_delimiter__.join(map(str,primary_key_values))    
  
    def getKey(self):
        '''
        get primary key
        '''
        return self._key   
     
    def setKey(self, key): 
        '''
        set primary key
        you can set the object key follow you special value with this method directly
        '''
        if not key:  
            raise HbaseException("Value of primary key must not be null")   
        self._key = key   
        
    @property
    def key(self):
        return self.getKey()          

    @key.setter
    def key(self, key):
        self.setKey(key)

    def as_dict(self):
        '''
        object as dict
        '''
        return {k:v for k,v in iteritems(self.__dict__) if k in self._columns} 
            
    @classmethod
    def get(cls, key):
        '''
        get one object
        @param key: primary key 
        '''
        conn = cls.getConn()
        result = conn.get(key)
        if not result: 
            return None
        return cls._createObject(key, conn, result)   
        
    @classmethod
    def gets(cls, keys=[]):
        '''
        get several objects
        @return: [(key,object subclass of Model),...]
        '''
        conn = cls.getConn()
        return [(k, cls._createObject(k, conn, v)) for k,v in conn.gets(keys)]     

    @classmethod
    def create(cls, key, **data):
        ''' create object '''
        class_dict = cls.__dict__
        values = {}
        for k,v in iteritems(data):
            ck = k
            cv = class_dict.get(k)
            if isinstance(cv, Column):
                ck = cv.field_name
            values[ck] = v  
        conn = cls.getConn()
        conn.put(key, value=values) 
        return cls._createObject(key, conn, data)
        
    @classmethod
    def _createObject(cls, key, conn, result):
        '''
        create instance
        @param key: primary key
        @param conn: Connection instalce
        @param result: result get from happybase  
        '''
        instance = cls(conn)
        class_dict = cls.__dict__
        for k, _ in iteritems(instance._columns):
            v = class_dict.get(k)
            if not v:
                continue
            
            fname = instance._getFieldName(v.field_name)
            value = result.get(fname, None)
            value = v.getValue(value) if value else value
            setattr(instance, k, value)     
                 
        instance.setKey(key)             
        return instance    
                    
    def put(self, **kwargs):  
        '''
        update columns value with dict
        ''' 
        self._setKeyByPrimaryKey({k:kwargs.get(k) for k in self._primary_keys})  
        if not self._key:
            raise HbaseException("Value of primary key cannot be '%s'" % self._key)   
                  
        values = {self._getFieldName(k):str(v) for k,v in iteritems(kwargs) if k in self._columns}
        self._conn.put(self._key, value=values)    

    def save(self):
        '''
        save or update object
        '''
        columns = self.__dict__
        self._setKeyByPrimaryKey({k:columns.get(k) for k in self._primary_keys})
        if not self._key:
            raise HbaseException("Value of primary key cannot be '%s'" % self._key)  
        
        values = {self._getFieldName(k):str(v) for k,v in iteritems(columns) if k in self._columns}            
        self._conn.put(self._key, value=values)
        
    def delete(self, columns=[]):
        '''
        delete object or columns
        '''
        if self._key:
            cols = [self._getFieldName(c) for c in columns]
            self._conn.delete(self._key, cols)
            