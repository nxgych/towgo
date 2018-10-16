#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017年4月17日
@author: shuai.chen
'''

#self-define python mysql orm

import sys
import datetime
from abc import ABCMeta
import functools
from six import iteritems

PY2 = sys.version_info[0] == 2
if PY2:
    import MySQLdb as pymysql
    from MySQLdb.cursors import DictCursor 
else:
    import pymysql
    from pymysql.cursors import DictCursor
        
from DBUtils.PooledDB import PooledDB  
 
from towgo.msetting import settings

class SqlFormat(object):
    ''' sql format class '''
    
    @staticmethod  
    def get_value(value):
        ''' get value '''
        format_string = functools.partial(str.format, "'{0}'")
        
        if isinstance(value, str):
            return format_string(value)
        elif isinstance(value, datetime.datetime):
            return format_string(value.strftime("%Y-%m-%d %H:%M:%S"))
        elif isinstance(value, datetime.date):
            return format_string(value.strftime("%Y-%m-%d"))
        else: 
            return str(value)
          
    def get_condition_str(self, key, value, sign="="):
        """
        condition string
        """
        return str.format("{0} {1} {2}", key, sign, self.get_value(value))
    
    def get_condition(self, condition, sign=" and "):
        """
        get adjust condition and SQL format string
        @param param:
            condition:dict            
        """
        conditions = []
        for k,v in iteritems(condition):
            if isinstance(v, tuple) or isinstance(v, list):
                assert len(v) >= 2
                conditions.append(self.get_condition_str(k, v[1], v[0]))
            else:                
                conditions.append(self.get_condition_str(k, v))                              
        return sign.join(conditions)  
    
def dbo(commit=False):  
    ''' database operation decorator '''
    def _deco(func):
        def __deco(self, *args, **kwargs):  
            conn = self.get_conn()
            cursor = conn.cursor()
            try:                
                if commit:
                    sqls = func(self, *args, **kwargs) 
                    for sql in sqls:      
                        cursor.execute(sql)                    
                    conn.commit()  
                    return cursor.rowcount                         
                else:
                    sql = func(self, *args, **kwargs)
                    cursor.execute(sql) 
                    return cursor.fetchall()             
            except:
                if commit:
                    if conn: conn.rollback()  
                raise
            finally:    
                if cursor: cursor.close()  
                if conn: conn.close() 
        return __deco
    return _deco         
                
class SqlConn(SqlFormat):
    ''' Mysql connection class '''
    
    _conn = {}
    
    def __new__(cls, conn_name='default', *args, **kwargs):
        if conn_name not in cls._conn:
            cls.connect(conn_name, **kwargs)
        return object.__new__(cls)

    def __init__(self,conn_name='default', *args, **kwargs):
        table = args[0]
        assert table != ""
        
        self.conn_name = conn_name
        self.table = table
                    
    @classmethod
    def connect(cls, conn_name, **kwargs):
        config = kwargs or settings.MYSQL[conn_name]            
        config.update(settings.SQLDB_POOL)
            
        pool = PooledDB(creator=pymysql, 
                        mincached=config['mincached'], maxcached=config['maxcached'],
                        maxconnections=config['maxconnections'], blocking=config['blocking'],
                        host=config['host'], port=config['port'], db=config['database'],
                        user=config['username'], passwd=config['password'],
                        use_unicode=False, charset="utf8", cursorclass=DictCursor)  
        cls._conn[conn_name] = pool

    def get_conn(self):
        ''' get connection '''
        return self._conn[self.conn_name].connection() 
        
    def set_table(self, table):
        ''' set table '''
        self.table = table
                 
    def get(self, condition):
        '''
        get one from db with conditions
        @param condition: dict type
        '''
        assert len(condition) > 0

        conn = self.get_conn()
        cursor = conn.cursor()
        try:          
            fc = self.get_condition(condition)
            sql = "SELECT * FROM %s WHERE %s" % (self.table, fc)
            cursor.execute(sql) 
            return cursor.fetchone()
        except:
            raise
        finally:    
            if cursor: cursor.close()  
            if conn: conn.close() 
                    
    @dbo()
    def getmany(self, condition={}, start=0, limit=0):
        '''
        get many from db with conditions
        @param condition: dict type
        '''        
        fc = self.get_condition(condition)
        if fc:
            sql = "SELECT * FROM %s WHERE %s" % (self.table, fc)
        else:
            sql = "SELECT * FROM %s" % self.table
        sql += " LIMIT %d,%d" % (start, limit) if limit > 0 else ""
        return sql  

    @dbo()
    def get_by_sql(self, sql):
        '''
        get from db with sql
        @param sql: sql
        ''' 
        return sql
                    
    def update_sql(self, data, condition):  
        '''
        get update sql 
        @param data: updated data, dict type
        @param condition: query condition, dict type
        '''      
        assert len(data) > 0
        assert len(condition) > 0   
                      
        fc = self.get_condition(condition)
        fvalues = self.get_condition(data, ",")
        sql = "UPDATE %s SET %s WHERE %s" % (self.table, fvalues, fc)  
        return sql
    
    @dbo(commit=True)                        
    def update(self, data, condition):
        '''
        update
        @param data: updated data, dict type
        @param condition: query condition, dict type
        '''    
        return (self.update_sql(data, condition), ) 

    def insert_sql(self, data):
        '''
        get insert sql
        @param data: dict type
        '''  
        assert len(data) > 0  
        
        ks, vs = [], []
        for k,v in iteritems(data):
            vs.append(self.get_value(v))
            ks.append(k)
            
        kf, vf = ",".join(ks), ",".join(vs)             
        sql = "INSERT INTO %s (%s) VALUES (%s)" % (self.table, kf, vf)  
        return sql      
    
    @dbo(commit=True) 
    def insert(self, data):
        '''
        insert
        @param data: dict type
        '''      
        return (self.insert_sql(data), )

    def delete_sql(self, condition):  
        ''' 
        get delete sql
        @param condition: query condition, dict type
        '''        
        assert len(condition) > 0
        
        fc = self.get_condition(condition)
        sql = "DELETE FROM %s WHERE %s" % (self.table, fc)
        return sql
    
    @dbo(commit=True)              
    def delete(self, condition): 
        ''' 
        delete data 
        @param condition: query condition, dict type
        '''
        return (self.delete_sql(condition), )               
    
    @dbo(commit=True) 
    def execute(self, *args):
        '''
        @summary: execute several sqls
        '''  
        return filter(bool, args)

    def executemany(self, sql, values):
        '''
        @summary: execute many record
        @param sql: sql format 
        @param values: type tuple(tuple)/list[list] 
        @return: execute lines number  
        '''          
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            cursor.executemany(sql, values)
            conn.commit()  
            return cursor.rowcount
        except:
            if conn: conn.rollback()
            raise
        finally:    
            if cursor: cursor.close()  
            if conn: conn.close()         

class Column(object):
    ''' mysql column '''

    def __init__(self, field_name, primary_key=False, nullable=True, default=None):  
        '''
        @param field_name: field name
        @param primary_key: is primary key or not
        @param nullable: can be null or not
        @param default: default value 
        '''
        self.field_name = field_name
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default        
        
class Model(object):
    '''
    abstract base model not support create table
    @example:
        class User(Model):
        
            __connection_name__ = "default"
            __table_name__ = "test"    
        
            id = Column("id", primary_key=True)
            name = Column("name", default='')
            age = Column("age" default=18)      
        
        #get    
        user = User.get(id=1)
        print(user.name)
        
        #delete
        user.delete() 
            
        #save or update
        user = User()
        user.id = 1
        user.name = 'abc'
        user.age = 18
        user.save()              
    '''
    
    __metaclass__ = ABCMeta
    
    '''mysql connection name, defalut is 'default' '''
    __connection_name__ = 'default'
    
    '''mysql table name, you must define this variable in your model'''
    __table_name__ = ''
    
    def __new__(cls, *args, **kwargs):
        cls._primary_keys = []
        cls._columns = {}
        if len(cls._columns) <= 0:
            pkl = []
            for k,v in iteritems(cls.__dict__):
                if isinstance(v,Column):
                    cls._columns[k] = v.field_name
                    if v.primary_key:
                        pkl.append(k)  
                                 
            cls._primary_keys = pkl
        return object.__new__(cls)
    
    def __init__(self, conn=None, is_new=True):   
        '''
        @param conn: mysql Connection 
        @param is_new: is new object or not
        '''
        assert self.__table_name__ != ''
        self._conn = conn or SqlConn(self.__connection_name__, self.__table_name__)
        self._is_new = is_new
    
    @property    
    def conn(self):
        return self._conn     
    
    @classmethod
    def get_conn(cls):
        assert cls.__table_name__ != ''
        return SqlConn(cls.__connection_name__, cls.__table_name__)
            
    @classmethod
    def _get_db_data(cls, data):
        class_dict = cls.__dict__
        attr = {}
        for k, v in iteritems(data):
            ck = k
            cv = class_dict.get(k)
            if isinstance(cv, Column):
                ck = cv.field_name
            attr[ck] = v
        return attr       

    @classmethod    
    def get(cls, **condition): 
        ''' 
        get one query
        @param condition: query condition
        @example:
            {'id':1}
        ''' 
        conn = cls.get_conn()
        cond = cls._get_db_data(condition)
        obj = conn.get(cond)  
        if not obj:
            return None
        return cls._create_object(conn, obj)

    @classmethod
    def getmany(cls, start=0, limit=0, **condition):
        ''' 
        get many queries
        @param start: start item index
        @param limit: limit item number
        @param condition: query condition
        @example:
            {'level': ('>', 3), 'age': 18}        
        '''
        conn = cls.get_conn()
        cond = cls._get_db_data(condition)
        co = functools.partial(cls._create_object, conn)
        return map(co, conn.getmany(cond, start=start, limit=limit))

    @classmethod
    def create(cls, **data):
        ''' create object '''
        conn = cls.get_conn()
        values = cls._get_db_data(data)
        conn.insert(values)
        return cls._create_object(conn, values)
        
    @classmethod
    def _create_object(cls, conn, obj):
        '''
        create instance
        @param conn: Connection instalce
        @param obj: result get from mysql
        '''
        instance = cls(conn, False)
        for k,fn in iteritems(instance._columns):
            value = obj.get(fn)
            setattr(instance, k, value)                
        return instance   
    
    @classmethod
    def remove(cls, **condition):
        conn = cls.get_conn()
        cond = cls._get_db_data(condition)
        if len(cond) > 0:                      
            return conn.delete(cond)
        return 0

    @classmethod
    def get_by_sql(cls, sql):
        '''
        get from db with sql
        @param sql: sql
        '''          
        conn = cls.get_conn()
        return conn.get_by_sql(sql)
    
    def _get_filed_name(self, fname):
        ''' get field name '''
        return self._columns.get(fname, fname)
        
    def save(self):
        ''' save object '''
        if self._is_new:
            return self.insert()
        else:
            return self.update()  
            
    def _insert_data(self):        
        attr_dict = self.__dict__
        class_dict = self.__class__.__dict__
        data = {}
        for k, fn in iteritems(self._columns):
            v = attr_dict.get(k) or class_dict.get(k)
            value = v
            if isinstance(v, Column):
                if v.default is not None:
                    value = v.default
                    if callable(value):
                        value = value()
                elif not v.nullable:
                    raise ValueError("'%s' value can't be null!" % v.field_name)      
            data[fn] = value 
        return data
                    
    def insert(self):
        ''' insert object '''
        data = self._insert_data()
        return self._conn.insert(data)
    
    @property     
    def insert_sql(self):   
        ''' get insert sql '''
        data = self._insert_data()
        return self._conn.insert_sql(data) 
        
    def _update_data_condition(self):
        data = self._insert_data()
        condition = {}
        for k in self._primary_keys:
            key = self._get_filed_name(k)
            condition[key] = data.pop(key)  
        return data, condition                
        
    def update(self):
        ''' update object''' 
        data, condition = self._update_data_condition()
        return self._conn.update(data, condition)
    
    @property    
    def update_sql(self):
        ''' get update sql '''
        data, condition = self._update_data_condition()
        return self._conn.update_sql(data, condition)  
        
    def _delete_condition(self):    
        attr_dict = self.__dict__
        condition = {}
        for k in self._primary_keys:
            key = self._get_filed_name(k)
            value = attr_dict.get(k) 
            if not isinstance(value, Column):
                condition[key] = value   
        return condition
                    
    def delete(self):
        ''' delete object '''
        condition = self._delete_condition()
        if len(condition) > 0:                      
            return self._conn.delete(condition)    
        return 0
    
    @property         
    def delete_sql(self):
        ''' get delete sql '''
        condition = self._delete_condition()
        if len(condition) > 0:
            return self._conn.delete_sql(condition)
        return None       
    
    def execute(self, *sql):
        ''' execute sql '''
        return self._conn.execute(*sql) 
    
    @classmethod
    def cexecute(cls, *sql):
        ''' execute sql '''
        conn = cls.get_conn()
        return conn.execute(*sql) 
