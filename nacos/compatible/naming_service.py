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
from abc import abstractmethod

import requests

from nacos.exception import NacosRequestException


class RequestMethods(object):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    HEAD = "HEAD"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"


class NacosBaseRequest(object):
    __slots__ = ['_nacos_server', '_request_api_name', '_request_method', '_request_headers', '_request_timeout',
                 '_namespace']

    def __init__(self,
                 nacos_server,
                 request_api_name,
                 request_method,
                 request_headers=None,
                 request_timeout=None,
                 namespace=None,
                 ):
        self._nacos_server = nacos_server
        self._request_api_name = request_api_name
        self._request_method = request_method
        self._request_headers = request_headers
        self._request_timeout = request_timeout
        self._namespace = namespace

    @property
    def nacos_server(self):
        return self._nacos_server

    @nacos_server.setter
    def nacos_server(self, server):
        self._nacos_server = server

    @property
    def request_api_name(self):
        return self._request_api_name

    @property
    def request_method(self):
        return self._request_method

    @property
    def request_headers(self):
        return self._request_headers

    @request_api_name.setter
    def request_api_name(self, request_api_name):
        self._request_api_name = request_api_name

    @request_method.setter
    def request_method(self, request_method):
        self._request_method = request_method

    @request_headers.setter
    def request_headers(self, request_headers):
        self._request_headers = request_headers

    @property
    def request_timeout(self):
        return self._request_timeout

    @request_timeout.setter
    def request_timeout(self, request_timeout):
        self._request_timeout = request_timeout

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, namespace):
        self._namespace = namespace

    def to_http_url(self):
        return "http://{host}:{port}{uri}".format(host=self._nacos_server[0], port=self._nacos_server[1],
                                                  uri=self._request_api_name if self._request_api_name.startWith(
                                                      "/") else "/" + self._request_api_name)

    @abstractmethod
    def to_payload(self):
        raise NacosRequestException('to_payload is abstract method,not implemented.')

    @abstractmethod
    def tag(self):
        pass


class ListInstanceRequest(NacosBaseRequest):
    def tag(self):
        return "SERVICE"

    def __init__(self, service_name, nacos_server, group_name=None, namespace_id=None,
                 clusters=None, healthy_only=False):
        """
        :param service_name:    服务名
        :param group_name:
        :param namespace_id:
        :param clusters:
        :param healthy_only:
        """
        super(ListInstanceRequest, self).__init__(nacos_server, "/nacos/v1/ns/instance", RequestMethods.GET)
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
        res = requests.get(url=request.to_http_url(),
                           headers=request.request_headers,
                           params=request.to_payload())

        return res.json()
