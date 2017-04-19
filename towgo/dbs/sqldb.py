#coding:utf-8

'''
Created on 2017年4月17日
@author: shuai.chen
'''

import datetime
import types
from abc import ABCMeta

import MySQLdb  
from MySQLdb.cursors import DictCursor 
from DBUtils.PooledDB import PooledDB  
 
from towgo.utils.extend import Odict 
from towgo.msetting import settings

class SqlFormat(object):
    
    @staticmethod        
    def need_str(value):
        """
        check value type
        """
        if (type(value) is types.StringType or type(value) is types.UnicodeType
            or isinstance(value,datetime.date) or isinstance(value,datetime.datetime)):
            return True
        return False   
    
    @staticmethod  
    def get_value(value):
        '''get value'''
        if isinstance(value, datetime.datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")   
        if isinstance(value, datetime.date):
            return value.strftime("%Y-%m-%d")    
        return value     
          
    def get_condition_str(self, key, value, sign="="):
        """
        condition string
        """
        sstr = "{0} {1} '{2}'" if self.need_str(value) else "{0} {1} {2}"
        return str.format(sstr, key, sign, self.get_value(value))
    
    def get_condition(self, condition, sign=" and "):
        """
        get adjust condition and SQL format string
        @param param:
            condition:dict            
        """
        conditions = []
        for k,v in condition.iteritems():
            if isinstance(v,tuple):
                conditions.append(self.get_condition_str(k, v[1], v[0]))
            else:                
                conditions.append(self.get_condition_str(k, v))                              
        return sign.join(conditions)  

class SqlConn(SqlFormat):
    ''' Mysql connection class '''
    
    _conn = {}
    
    def __new__(cls, conn_name='default', *args, **kwargs):
        if conn_name not in cls._conn:
            cls.connect(conn_name, **kwargs)
        return object.__new__(cls, *args, **kwargs)

    def __init__(self,conn_name='default', *args, **kwargs):
        self.conn = self._conn[conn_name].connection() 
        self.table = args[0] if len(args) > 0 else None

    def __del__(self):
        try:
            if self.conn:
                self.conn.close()
        except:
            pass    
                    
    @classmethod
    def connect(cls, conn_name, **kwargs):
        config = kwargs or settings.MYSQL[conn_name]
        pool = PooledDB(creator=MySQLdb, 
                        host=config['host'], port=config['port'], db=config['database'],
                        user=config['username'], passwd=config['password'],
                        use_unicode=False, charset="utf8", cursorclass=DictCursor,
                        **settings.SQL_POOL)  
        cls._conn[conn_name] = pool
    
    def set_table(self, table):
        self.table = table
    
    def get(self, condition, as_dict=False):
        '''
        get one from db with conditions
        @param condition: dict type
        @param as_dict: return dict type if True   
        '''
        cursor = self.conn.cursor()
        try:
            assert len(condition) > 0
            fc = self.get_condition(condition)
            sql = "SELECT * FROM %s WHERE %s" % (self.table, fc)
            cursor.execute(sql)
            if as_dict:
                obj = cursor.fetchoneDict()
                return Odict(obj) if obj else None
            return cursor.fetchone()
        except:
            raise
        finally:    
            cursor.close()       
    
    def getmany(self, condition={}, limit=0, as_dict=False):
        '''
        get many from db with conditions
        @param condition: dict type
        @param as_dict: return dict type if True   
        '''        
        cursor = self.conn.cursor()
        try:
            fc = self.get_condition(condition)
            if fc:
                sql = "SELECT * FROM %s WHERE %s" % (self.table, fc)
            else:
                sql = "SELECT * FROM %s" % self.table
                  
            sql += " LIMIT %d" % limit if limit > 0 else ''
            cursor.execute(sql)
            return [Odict(item) for item in cursor.fetchallDict()] if as_dict else cursor.fetchall()
        except:
            raise
        finally:    
            cursor.close()

    def get_by_sql(self, sql, as_dict=False):
        '''
        get from db with sql
        '''        
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql)
            return [Odict(item) for item in cursor.fetchallDict()] if as_dict else cursor.fetchall()
        except:
            raise
        finally:    
            cursor.close() 
                
    def update(self, data, condition):
        '''
        update
        @param data: dict type
        @param condition: dict type
        '''            
        cursor = self.conn.cursor()
        try:
            assert len(data) > 0
            assert len(condition) > 0
            fc = self.get_condition(condition)
            fvalues = self.get_condition(data, ",")
            sql = "UPDATE %s SET %s WHERE %s" % (self.table, fvalues, fc)  
            cursor.execute(sql)
            self.conn.commit()    
        except:
            self.conn.rollback()
            raise
        finally:    
            cursor.close()
    
    def insert(self, data):
        '''
        insert
        @param data: dict type
        '''         
        cursor = self.conn.cursor()
        try:
            assert len(data) > 0
            ks, vs = [], []
            for k,v in data.iteritems():
                sstr = "'{0}'" if self.need_str(v) else "{0}"
                vs.append(str.format(sstr, self.get_value(v)))
                ks.append(k)
                
            k_format = ",".join(ks)    
            v_format = ",".join(vs)              
            
            sql = "INSERT INTO %s (%s) VALUES (%s)" % (self.table, k_format, v_format)
            cursor.execute(sql)
            self.conn.commit()    
        except:
            self.conn.rollback()
            raise
        finally:    
            cursor.close()
            
    def delete(self, condition): 
        ''' delete data '''
        cursor = self.conn.cursor()
        try:
            fc = self.get_condition(condition)
            sql = "DELETE FROM %s WHERE %s" % (self.table, fc)
            cursor.execute(sql)
            self.conn.commit()    
        except:
            self.conn.rollback()
            raise
        finally:    
            cursor.close()                 
    
    def execute(self, *args):
        '''
        @summary: execute several sqls
        '''          
        cursor = self.conn.cursor()
        try:
            for sql in args:
                cursor.execute(sql)

            self.conn.commit()    
        except:
            self.conn.rollback()
            raise
        finally:    
            cursor.close()

    def executemany(self, sql, values):
        '''
        @summary: execute many record
        @param sql: sql format 
        @param values:type tuple(tuple)/list[list] 
        @return: execute lines number  
        '''          
        cursor = self.conn.cursor()
        try:
            cursor.executemany(sql, values)
            self.conn.commit()    
        except:
            self.conn.rollback()
            raise
        finally:    
            cursor.close()        

class Column(object):
    ''' mysql column '''

    def __init__(self, field_name, primary_key=False, default=None):  
        '''
        @param field_name: field name
        @param primary_key: is primary key or not
        @param default: default value 
        '''
        self.field_name = field_name
        self.primary_key = primary_key
        self.default = default
        
class Model(object):
    
    __metaclass__ = ABCMeta
    
    '''mysql connection name, defalut is 'default' '''
    __connection_name__ = 'default'
    
    '''mysql table name, you must define this variable in your model'''
    __table_name__ = ''
    
    _primary_keys = []
    _columns = {}
    
    def __new__(cls, *args, **kwargs):
        if len(cls._columns) <= 0:
            pkl = []
            for k,v in cls.__dict__.iteritems():
                if isinstance(v,Column):
                    cls._columns[k] = v.field_name
                    if v.primary_key:
                        pkl.append(k)  
                                 
            cls._primary_keys = pkl
        return object.__new__(cls, *args, **kwargs)
    
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
        for k, v in data.iteritems():
            ck = k
            cv = class_dict.get(k)
            if cv is None:
                continue
            if isinstance(cv, Column):
                ck = cv.field_name
            attr[ck] = v
        return attr       

    @classmethod    
    def get(cls, **condition): 
        ''' get one ''' 
        conn = cls.get_conn()
        cond = cls._get_db_data(condition)
        obj = conn.get(cond, as_dict=True)  
        if not obj:
            return None
        return cls._create_object(conn, obj)

    @classmethod
    def getmany(cls, condition={}, limit=0):
        ''' get many '''
        conn = cls.get_conn()
        cond = cls._get_db_data(condition)
        return [cls._create_object(conn, v) for v in conn.getmany(cond, limit=limit, as_dict=True)]   

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
        class_dict = cls.__dict__
        for k,fn in instance._columns.iteritems():
            v = class_dict.get(k)
            if not v:
                continue
            value = obj.get(fn, v.default)
            setattr(instance, k, value)                
        return instance   

    def _get_filed_name(self, fname):
        ''' get field name '''
        return self._columns.get(fname, fname)
        
    def save(self):
        ''' save object '''
        if self._is_new:
            self._insert()
        else:
            self._update()    

    def _update(self):
        attr_dict = self.__dict__
        data, condition = {}, {}
        for k, fn in self._columns.iteritems():
            v = attr_dict.get(k)
            data[fn] = v.default if isinstance(v, Column) else v  
        for k in self._primary_keys:
            key = self._get_filed_name(k)
            condition[key] = data.pop(key)     
        self._conn.update(data, condition)
    
    def _insert(self):
        attr_dict = self.__dict__
        data = {}
        for k, fn in self._columns.iteritems():
            v = attr_dict.get(k)
            data[fn] = v.default if isinstance(v, Column) else v                 
        self._conn.insert(data)
        
    def delete(self):
        ''' delete object '''
        attr_dict = self.__dict__
        condition = {}
        for k in self._primary_keys:
            key = self._get_filed_name(k)
            value = attr_dict.get(k) 
            if not isinstance(value, Column):
                condition[key] = value   
        if len(condition) > 0:                      
            self._conn.delete(condition)    
