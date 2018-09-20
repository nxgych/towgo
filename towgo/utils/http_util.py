#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017年1月9日
@author: shuai.chen
'''

import json
import httplib
import urllib2
import re

def get_request_url(path, params={}):
    '''
    generate request url
    '''
    p = "&".join(["%s=%s" % (k,v) for k,v in params.iteritems()])
    return "%s&%s"%(path,p) if "?" in path else "%s?%s"%(path,p) if p else path

def httplib_request(domain, path, method="GET", use_ssl=False, params={}, headers={}, timeout=10):
    '''
    http/https request
    @param domain: http:port  or domain
    @param path: request path
    @param method: GET OR POST
    @param use_ssl: https
    @param params: reques params
    @param headers: request headers     
    ''' 
    http_client = None
    try:
        if use_ssl:
            http_client = httplib.HTTPSConnection(domain, timeout)
        else:
            http_client = httplib.HTTPConnection(domain, timeout)    
        
        if method.upper() == "GET":
            req_url = get_request_url(path,params) 
            http_client.request("GET", req_url, headers=headers)           
        else:    
            http_client.request("POST", path, json.dumps(params), headers)

        response = http_client.getresponse()
        return response.read()                     
    except:
        raise 
    finally:
        if http_client: http_client.close()

def urllib_request(url, method='GET', params={}, headers={}):
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
        req = urllib2.Request(url,json.dumps(params),headers)
     
    if req:         
        response = urllib2.urlopen(req)
        result = response.read()
        return result
    
def ip_int(ip): 
    '''
    string ip to int ip
    @param ip: string ip 
    '''
    if not (isinstance(ip, str) or isinstance(ip, unicode)):
        raise TypeError("'ip' must be a string type")
    if not re.match(r'^\d+.\d+.\d+.\d+$',ip):
        raise ValueError("illegal ip : %s" % ip)
    return reduce(lambda x,y:(x<<8)+y,map(int,ip.split('.')))   

def ip_str(ip):
    '''
    int ip to str ip
    @param ip: int ip 
    '''
    if not (isinstance(ip, int) or isinstance(ip, long)):
        raise TypeError("'ip' must be a integer or long type")
    fun = lambda x: '.'.join([str(x/(256**i)%256) for i in range(3,-1,-1)])
    return fun(int(ip))
