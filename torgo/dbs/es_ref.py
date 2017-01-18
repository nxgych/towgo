#coding:utf-8

'''
Created on 2017年1月4日
@author: shuai.chen
'''

import traceback
import json

from elasticsearch import Elasticsearch
from elasticsearch import Transport 
from elasticsearch.connection import RequestsHttpConnection 

from torgo.log.log_util import CommonLog
                                                
                                                
class ElasticsearchConn(object):
    '''
    elasticsearch pool connection class
    '''
    
    _POOL = None
    
    def __new__(cls, *args, **kwargs):
        if cls._POOL is None:
            cls._POOL = cls.connect(**kwargs)
        return object.__new__(cls)
    
    @staticmethod
    def connect(**kwargs):
        config = kwargs #settings.ES
        try:
            conn = Transport(
                             config['nodes'], 
                             connection_class=RequestsHttpConnection,
                             sniff_on_start=True,
                             sniffer_timeout=60,
                             sniff_on_connection_fail=True,
                             retry_on_timeout=True
                            )
            return conn.connection_pool
        except:
            CommonLog.error('elasticsearch connect error:'+traceback.format_exc()) 
              
    def get_conn(self):
        return self._POOL.get_connection()
       
    def search(self, index, doc_type, body={}):
        """
        search method
        """
        conn = self.get_conn()
        url = "/%s/%s/%s" % (index, doc_type, "_search")
        body = json.dumps(body) if body is not None else body
        result = conn.perform_request("GET", url, None, body)
        ret_json = json.loads(result[2])
        return ret_json['hits']['hits']


class ElasticsearchConn2(object):
    
    _conn = None
     
    def __new__(cls, *args, **kwargs):
        if cls._conn is None:
            cls._conn = cls.connect(**kwargs)
        return object.__new__(cls, *args, **kwargs)
        
    @staticmethod
    def connect(**kwargs):
        config = kwargs #settings.ES
        
        try:
            hp_list = []
            for hp in config['nodes']:
                hp_list.append("%s:%d" % (hp['host'], hp['port']))
                
            return Elasticsearch(hp_list)    
        except:
            CommonLog.error('elasticsearch connect error:'+traceback.format_exc())      
            
    def search(self, index, doc_type, body={}):
        ret = self._conn.search(index, doc_type, body) 
        return ret['hits']['hits']
        