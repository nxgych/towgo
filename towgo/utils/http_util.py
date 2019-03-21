#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017年1月9日
@author: shuai.chen
'''

import sys
import json
import re
from functools import reduce 

PY2 = sys.version_info[0] ==2
if PY2:
    import httplib
    import urllib2
else:
    import http.client as httplib
    import urllib.request as urllib2

from six import iteritems

def get_request_url(path, params={}):
    '''
    generate request url
    '''
    p = "&".join(["%s=%s" % (k,v) for k,v in iteritems(params)])
    return "%s&%s"%(path,p) if "?" in path else "%s?%s"%(path,p) if p else path

def httplib_request(host, port, path, method="GET", params={}, headers={}, timeout=10, use_ssl=False):
    '''
    http/https request
    @param path: request path
    @param method: GET OR POST
    @param params: reques params
    @param headers: request headers     
    @param use_ssl: https if True else http
    ''' 
    http_client = None
    try:
        if use_ssl:
            http_client = httplib.HTTPSConnection(host, port, timeout)
        else:
            http_client = httplib.HTTPConnection(host, port, timeout)    
        
        if method.upper() == "GET":
            req_url = get_request_url(path,params) 
            http_client.request("GET", req_url, headers=headers)           
        else:    
            http_client.request("POST", path, json.dumps(params).encode('UTF8'), headers)

        response = http_client.getresponse()
        return response.read()                     
    except:
        raise 
    finally:
        if http_client: http_client.close()

def urllib_request(url, method='GET', params={}, headers={}, timeout=10):
    '''
    @param url: url
    @param method: GET or POST
    @param params: reques params
    @param headers: request headers               
    '''
    req = None
    if method.upper() == "GET":
        req_url = get_request_url(url,params) 
        req = urllib2.Request(req_url,headers=headers)
    else:
        req = urllib2.Request(url, json.dumps(params).encode('UTF8'), headers)
     
    if req:         
        response = urllib2.urlopen(req, timeout=timeout)
        result = response.read()
        return result
    
def ip_int(ip): 
    '''
    string ip to int ip
    @param ip: string ip 
    '''
    if not isinstance(ip, str):
        raise TypeError("'ip' must be a string type")
    if not re.match(r'^\d+.\d+.\d+.\d+$',ip):
        raise ValueError("illegal ip : %s" % ip)
    return reduce(lambda x,y:(x<<8)+y,map(int,ip.split('.')))   

def ip_str(ip):
    '''
    int ip to str ip
    @param ip: int ip 
    '''
    if not isinstance(ip, int):
        raise TypeError("'ip' must be a integer type")
    fun = lambda x: '.'.join([str(x/(256**i)%256).split('.')[0] for i in range(3,-1,-1)])
    return fun(int(ip))
