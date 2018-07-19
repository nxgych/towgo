#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2016/11/04
@author: willing
@url: https://github.com/nxgych/whbase

hbase orm based happybase
'''

import happybase
from abc import ABCMeta

class ColumnFamliyExceotion(Exception):  
    pass   

class Connection(object):
    '''
    happybase connection class
    you must execute the class method 'connect' before you create a instance of 'Connection'
    @example:
        Connection.connect(host='127.0.0.1',port=9090)
    
    if you wanna to use more method of happybase, you can init this class directly without Model
    @example:
        conn = Connection(table='table')
        conn.table.method()
    '''
    
    _conn = {}
    
    def __new__(cls, conn_name="default", table="", cf='cf:', *args, **kwargs):
        if conn_name not in cls._conn:
            cls.connect(conn_name, **kwargs)
        return object.__new__(cls, *args, **kwargs)
    
    def __init__(self, conn_name="default", table="", cf='cf:', *args, **kwargs):
        '''
        @param table: hbase table name 
        @param cf: hbase table column famliy, default is 'cf:'  
        '''
        assert table != ""
        self.conn_name = conn_name
        self.cf = self._getColumnFamliyDefault(cf)
        self.table = self.getConn().table(table)  
             
        self._createTable(table)
        
    @classmethod
    def connect(cls, conn_name="default", **kwargs):
        '''
        happybase connect, you must execute this method before you create a instance of 'Connection'
        
        @example:
            Connection.connect(host='127.0.0.1',port=9090)
        '''
        cls._conn[conn_name] = happybase.Connection(**kwargs)
        
    def getConn(self):
        ''' 
        get connection 
        '''      
        return self._conn[self.conn_name]    
        
    def _getColumnFamliyDefault(self, cf):
        '''
        get default column famliy
        '''
        if not cf:
            raise ColumnFamliyExceotion('Unknown column famliy')      
        return '%s:' % cf if not cf.endswith(':') else cf               
    
    def _createTable(self, table):
        '''
        create table if the table is not exist
        '''
        if table not in self.getConn().client.getTableNames():
            self.getConn().create_table(table,{self.cf: dict()})
   
    def get(self, key):
        '''
        get one object if the key is exist
        '''
        return self.table.row(key)
    
    def gets(self, keys=[]):
        '''
        get several objects by the keys you setted
        '''
        if len(keys) <= 0:
            return []
        return self.table.rows(keys)
    
    def put(self, key, value={}):
        '''
        put item
        '''
        self.table.put(key, value)
    
    def delete(self, key, columns=[]):
        '''
        delete key or columns
        '''
        if len(columns) > 0:
            self.table.delete(key, columns)
        else:
            self.table.delete(key) 

    def scan(self):
        '''
        scan the table
        '''
        return self.table.scan()
    
class PrimaryKeyException(Exception):
    pass

class Model(object):  
    """
    Base model of hbase,
    you can inherit this class if you hope to use instance method or class method of Model object,
    you must execute the class method 'connect' of 'Connection' class before you use Model
    
    @example:
    
        class Test(Model):
        
            __table_name__ = "test"
            __column_famliy__ = "cf:"          # column famliy default is 'cf:'
            __primary_key_delimiter__ = "_"    # delimiter of primary keys default is '_'      
        
            id = Column("id", primary_key=0, value_type=int)
            name = Column("name", value_type=str)
            age = Column("age", value_type=int)    

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
        values = {'id':1,'name':'xyz','age':22}
        test.put(**values)  
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
    column famliy, default is 'cf:', you can redefine this variable in your model
    '''
    __column_famliy__ = 'cf:'   # column famliy default is 'cf:'
    
    '''
    delemiter of primary keys, default is '_', you can redefine this variable in your model
    '''
    __primary_key_delimiter__ = '_'
    
    _primary_keys = []
    _columns = {}
    
    def __new__(cls, *args, **kwargs):
        if len(cls._columns) <= 0:
            pkl = []
            for k,v in cls.__dict__.iteritems():
                if isinstance(v,Column):
                    cls._columns[k] = v.field_name
                    if v.primary_key >= 0 :
                        pkl.append((k,v.primary_key))  
                        
            pkl.sort(key = lambda item:item[1])            
            cls._primary_keys = [k for k,_ in pkl]  
        return object.__new__(cls, *args, **kwargs)
    
    def __init__(self, conn=None):   
        '''
        @param conn: happybase Connection 
        '''
        assert self.__table_name__ != ''
        self._conn = conn or Connection(self.__connection_name__, self.__table_name__, self.__column_famliy__)
        self._cf = self._conn.cf
        self._key = '' 

    @property    
    def conn(self):
        return self._conn   
    
    @classmethod
    def getConn(cls):
        assert cls.__table_name__ != ''
        return Connection(cls.__connection_name__, cls.__table_name__, cls.__column_famliy__)
    
    def _getFieldName(self, fname):
        '''
        get field name
        '''
        field_name = self._columns.get(fname, fname)
        if ':' not in field_name:
            return '%s%s' % (self._cf,field_name)
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
                    raise PrimaryKeyException("Value of primary key cannot be '%s'" % v)
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
        if not key or not isinstance(key,str):  
            raise PrimaryKeyException("Value of primary key must be a string type and not null")   
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
        return {k:v for k,v in self.__dict__.iteritems() if k in self._columns} 
            
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
        return [(k,cls._createObject(k,conn, v)) for k,v in conn.gets(keys)]     

    @classmethod
    def create(cls, key, **data):
        ''' create object '''
        class_dict = cls.__dict__
        values = {}
        for k,v in data.iteritems():
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
        for k,_ in instance._columns.iteritems():
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
            raise PrimaryKeyException("Value of primary key cannot be '%s'" % self._key)   
                  
        values = {self._getFieldName(k):str(v) for k,v in kwargs.iteritems() if k in self._columns}
        self._conn.put(self._key, value=values)    

    def save(self):
        '''
        save or update object
        '''
        columns = self.__dict__
        self._setKeyByPrimaryKey({k:columns.get(k) for k in self._primary_keys})
        if not self._key:
            raise PrimaryKeyException("Value of primary key cannot be '%s'" % self._key)  
        
        values = {self._getFieldName(k):str(v) for k,v in columns.iteritems() if k in self._columns}            
        self._conn.put(self._key, value=values)
        
    def delete(self, columns=[]):
        '''
        delete object or columns
        '''
        if self._key:
            cols = [self._getFieldName(c) for c in columns]
            self._conn.delete(self._key, cols)

class ColumnException(Exception):
    pass

class FunctionException(Exception):
    pass
        
class Column(object):
    '''
    hbase column definition class
    '''
    
    def __init__(self, field_name, primary_key=-1, value_type=str):    
        '''
        @param field_name: field name
               if you have several column famliy, you can add column famliy as prefix of field name
               and ignore the Model variable '__column_famliy__'
               like this:
                   id = Column("cf:id", primary_key=0, value_type=int)
                   age = Column("cfattr:age", value_type=str)   
                   age = Column("cfattr:age", value_type=int)         
        @param primary_key: default is -1,the value means the location of primary key that start with 0,
               you should set the value if you wanna the field value to be part of primary key and 
               it will join by the delimiter sign of the Model variable '__primary_key_delimiter__'.
        @param value_type: value type is a function you except to transfer the field value,
               default is 'str' function      
        '''               
        if not field_name or not isinstance(field_name, str):
            raise ColumnException("column name must be a string type and not null")
        if not hasattr(value_type,'__call__'):
            raise FunctionException("'%s' is not a function" % value_type)

        self.field_name = field_name
        self.value_type = value_type 
        self.primary_key = primary_key
                
    def getValue(self, value):  
        '''
        get column value
        '''
        return  self.value_type(value) 
    