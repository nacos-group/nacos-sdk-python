# -*- coding=utf-8 -*-

"""
 Verion: 1.0
 Since : 3.6
 Author: zhangjian
 Site: https://github.com/xarrow/
 File: naming_service.py
 Time: 2020/8/31

 Add New Functional nacos-sdk-python

 Just Python2 NacosNamingService
"""

import requests


class ListInstanceRequest(object):
    def __init__(self, service_name,
                 group_name=None,
                 namespace_id=None,
                 clusters=None,
                 healthy_only=False):
        """
        :param service_name:    服务名
        :param group_name:
        :param namespace_id:
        :param clusters:
        :param healthy_only:
        """
        self._service_name = service_name
        self._group_name = group_name
        self._namespace_id = namespace_id
        self._clusters = clusters
        self._healthy_only = healthy_only

    def invalid(self):
        return self

    def to_payload(self):
        payload = {
            "serviceName": self._service_name,
            "healthyOnly": self._healthy_only
        }
        if self._group_name:
            payload['groupName'] = self._group_name
        if self._clusters:
            payload['clusters'] = self._clusters
        if self._namespace_id:
            payload['namespaceId'] = self._namespace_id


class NacosNamingService(object):
    def __init__(self):
        self._local_instance = dict()

    def list_instances(self, request):
        return requests.get(url="/nacos/v1/ns/instance/list",
                            params=request.to_payload()).json()
