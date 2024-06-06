import json
import requests
import time
import threading
from contextlib import contextmanager

from v2.nacos.config.client_config import ClientConfig


class AuthClient:
    def __init__(self, client_config: ClientConfig, http_agent):
        self.username = client_config.username
        self.password = client_config.password
        self.client_config = client_config
        self.http_agent = http_agent
        self.access_token = None
        self.token_ttl = 0
        self.last_refresh_time = 0
        self.token_refresh_window = 0

    def get_access_token(self):
        return self.access_token

    @contextmanager
    def auto_refresh(self):
        if self.username == "":
            yield
            return

        def refresh_job():
            nonlocal self
            timer_interval = 5
            if self.last_refresh_time > 0 and self.token_ttl > 0 and self.token_refresh_window > 0:
                timer_interval = self.token_ttl - self.token_refresh_window

            while True:
                time.sleep(timer_interval)
                success, _ = self.login()
                if success:
                    timer_interval = self.token_ttl - self.token_refresh_window
                else:
                    timer_interval = 5

        refresh_thread = threading.Thread(target=refresh_job)
        refresh_thread.start()
        try:
            yield
        finally:
            refresh_thread.join()

    def login(self):
        for server_cfg in self.server_cfgs:
            success, error = self._login(server_cfg)
            if success:
                return True, None
        return False, error

    def _login(self, server_cfg):
        if self.username != "":
            context_path = server_cfg.get('ContextPath', '').rstrip('/')
            scheme = server_cfg.get('Scheme', 'http')
            ip_addr = server_cfg.get('IpAddr')
            port = server_cfg.get('Port')
            req_url = f"{scheme}://{ip_addr}:{port}{context_path}/v1/auth/users/login"

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {"username": self.username, "password": self.password}

            response = requests.post(req_url, headers=headers, data=data, timeout=self.client_cfg.get('TimeoutMs'))
            resp_json = response.json()

            if response.status_code != 200:
                return False, resp_json

            self.access_token = resp_json.get("accessToken")
            self.last_refresh_time = time.time()
            self.token_ttl = resp_json.get("tokenTtl", 0)
            self.token_refresh_window = self.token_ttl / 10

            return True, None
        return False, "Username is blank"