#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017年1月4日
@author: shuai.chen
'''

import json

from elasticsearch import Elasticsearch
from elasticsearch import Transport 
from elasticsearch.connection import RequestsHttpConnection 
from elasticsearch.exceptions import NotFoundError
    
from towgo.msetting import settings                                            
                                                
class Connection(object):
    '''
    Elasticsearch pool connection class
    '''    
    _pool = {}
    
    def __new__(cls, conn_name='default', *args, **kwargs):
        if conn_name not in cls._pool:
            cls.connect(conn_name, **kwargs)
        return object.__new__(cls)

    def __init__(self,conn_name='default', *args, **kwargs):
        self.conn_name = conn_name
        
    @classmethod
    def connect(cls, conn_name, **kwargs):
        config = kwargs or settings.ES[conn_name]
        conn = Transport(
                         config['nodes'], 
                         connection_class=RequestsHttpConnection,
                         sniff_on_start=True,
                         sniff_on_connection_fail=True,
                         retry_on_timeout=True,
                         **config
                        )
        cls._pool[conn_name] = conn.connection_pool
              
    def get_conn(self):
        return self._pool[self.conn_name].get_connection()
    
    @property
    def conn(self):
        return self.get_conn()
    
    def create_index(self, index, doc_type='',mappings={}):
        """
        create index and put mapping
        """
        conn = self.get_conn()
        body = {}
        if doc_type and mappings:
            conn.indices.put_mapping(doc_type, mappings, index)
            body = {"mappings":{doc_type:mappings}}
            
        body = json.dumps(body) if body is not None else body
        conn.perform_request("PUT", "/%s" % index, None, body)

    def delete_index(self, index):   
        """
        delete index
        """ 
        try:
            conn = self.get_conn()
            conn.perform_request("DELETE", "/%s" % index)
        except NotFoundError:
            return None 
                               
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

    def get(self, index, doc_type, doc_id):
        """
        get document
        """
        try:
            conn = self.get_conn()
            url = "/%s/%s/%s" % (index, doc_type, str(doc_id))   
            result = conn.perform_request("GET", url)
            ret_json = json.loads(result[2])
            return ret_json
        except NotFoundError:
            return None           
            
    def insert(self, index, doc_type, doc_id, body={}):
        """
        insert document
        """
        conn = self.get_conn()
        url = "/%s/%s/%s" % (index, doc_type, str(doc_id))
        body = json.dumps(body) if body is not None else body
        result = conn.perform_request("PUT", url, None, body)
        ret_json = json.loads(result[2])
        return ret_json
    
    def delete(self, index, doc_type, doc_id):
        '''
        delete document
        '''   
        try:              
            conn = self.get_conn()
            url = "/%s/%s/%s" % (index, doc_type, str(doc_id))
            result = conn.perform_request("DELETE", url)
            ret_json = json.loads(result[2])
            return ret_json
        except NotFoundError:
            return None 
             
class Connection2(object):
    
    _conn = {}
     
    def __new__(cls, conn_name='default', *args, **kwargs):
        if conn_name not in cls._conn:
            cls.connect(conn_name, **kwargs)
        return object.__new__(cls)

    def __init__(self,conn_name='default', *args, **kwargs):
        self.conn_name = conn_name
        
    @classmethod
    def connect(cls, conn_name, **kwargs):
        config = kwargs or settings.ES[conn_name]
        hp_list = []
        for hp in config['nodes']:
            hp_list.append("%s:%d" % (hp['host'], hp['port']))
            
        cls._conn[conn_name] = Elasticsearch(hp_list, **config)    

    def get_conn(self):
        return self._conn[self.conn_name]
    
    @property
    def conn(self):
        return self.get_conn()
    
    def create_index(self, index_name, doc_type='',mappings={}):
        """
        create index and put mapping
        """
        self.conn.indices.create(index=index_name)
        if doc_type and mappings:
            self.conn.indices.put_mapping(doc_type, mappings, index_name)
            
    def delete_index(self, index):   
        """
        delete index
        """ 
        try:
            return self.conn.indices.delete(index=index)    
        except NotFoundError:
            return None    
                                
    def search(self, index, doc_type, body={}):
        """
        search documents
        """
        ret = self.conn.search(index, doc_type, body) 
        return ret['hits']['hits']
            
    def get(self, index, doc_type, doc_id):
        """
        get document
        """
        try:
            ret = self.conn.get(index, doc_id, doc_type) 
            return ret  
        except NotFoundError:
            return None          
     
    def insert(self, index, doc_type, doc_id, body={}):
        """
        insert document
        """
        return self.conn.index(index=index,doc_type=doc_type,id=doc_id,body=body)      
    
    def delete(self, index, doc_type, doc_id):   
        '''
        delete document
        ''' 
        try:
            return self.conn.delete(index=index,doc_type=doc_type,id=doc_id) 
        except NotFoundError:
            return None  
        