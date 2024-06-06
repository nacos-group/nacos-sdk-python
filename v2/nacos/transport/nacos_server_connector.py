import threading
import requests
import time
import uuid
import hmac
import hashlib
import base64
from typing import List, Dict, Optional

from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.config.client_config import ClientConfig


class NacosServerConnector:
    def __init__(self, client_config: ClientConfig, http_agent, endpoint_query_header: Dict[str, str]):
        if not client_config.server_address and not client_config.endpoint:
            raise NacosException(INVALID_PARAM, "both server list and endpoint are empty")

        self.security_login = AuthClient(client_cfg, server_list, http_agent)
        self.server_address = client_config.server_address
        self.http_agent = http_agent
        self.timeout_ms = client_config.timeout_ms
        self.endpoint = client_config.endpoint
        self.vip_srv_ref_inter_mills = 10000  # Example value
        self.endpoint_context_path = client_cfg.endpoint_context_path
        self.endpoint_query_params = client_cfg.endpoint_query_params
        self.endpoint_query_header = endpoint_query_header
        self.cluster_name = client_cfg.cluster_name
        self.context_path = client_cfg.context_path
        self.server_src_change_signal = threading.Event()
        self.current_index = 0
        if server_list:
            self.current_index = self._choose_random_index(len(server_list))
        else:
            self._init_refresh_srv_if_need()

        # Continue other initializations and login

    def _init_refresh_srv_if_need(self):
        # Initialization logic for refreshing the server list
        pass

    def call_config_server(self, api: str, params: Dict[str, str], new_headers: Dict[str, str], method: str,
                           cur_server: str, context_path: Optional[str], timeout_ms: int):
        # Logic for calling the server for configuration
        pass

    def call_server(self, api: str, params: Dict[str, str], method: str):
        # Logic for calling the server
        pass

    def req_config_api(self, api: str, params: Dict[str, str], headers: Dict[str, str], method: str, timeout_ms: int):
        # Logic to send requests to the config API
        pass

    def req_api(self, api: str, params: Dict[str, str], method: str):
        # Logic to send requests to the generic API
        pass

    def refresh_server_srv_if_need(self, url_string: str):
        # Logic for refreshing the server list if needed
        pass

    def get_server_list(self):
        return self.server_list

    def get_next_server(self):
        if not self.server_list:
            raise ValueError('server list is empty')
        self.current_index = (self.current_index + 1) % len(self.server_list)
        return self.server_list[self.current_index]

    def _choose_random_index(self, upper_limit: int):
        return randrange(0, upper_limit)
