# -*- coding=utf-8 -*-

"""
 Verion: 1.0
 Since : 3.6
 Author: zhangjian
 Site: https://github.com/xarrow/
 File: nacos_exchange.py
 Time: 2020/8/31

 Http  Or Socket
 
 Add New Functional nacos-sdk-python
"""
from abc import abstractmethod

import requests


class ExchangeType(object):
    S = ""
    A = ""
    pass


class NacosExchange(object):
    def __init__(self):
        pass

    @abstractmethod
    def do_exchange(self):
        pass


class NacosHTTPExchange(NacosExchange):
    pass
