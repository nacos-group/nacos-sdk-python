# -*- coding=utf-8 -*-

"""
 Verion: 1.0
 Since : 3.6
 Author: zhangjian
 Site: https://github.com/xarrow/
 File: __init__.py
 Time: 2020/8/30
 
 Add New Functional nacos-sdk-python
"""
import requests

NACOS_SERVE = "127.0.0.1:8848"
API = "http://{server}{api_name}"

payload = {
    "serviceName": "test.service"
}

# res = requests.get(url=API.format(server=NACOS_SERVE, api_name="/nacos/v1/ns/instance/list"),
#                    params=payload)
# print(res.text)

#  test

d = dict()


def dd(a, b):
    a[b] = b


dd(d, "name")

print(d)
