import requests
import threading
import time
import json
from requests.auth import HTTPBasicAuth


class AuthClient:
    def __init__(self, client_cfg, server_cfgs):
        self.username = client_cfg['username']
        self.password = client_cfg['password']
        self.server_cfgs = server_cfgs
        self.token_ttl = 0
        self.last_refresh_time = 0
        self.token_refresh_window = 0
        self.access_token = None

    def get_access_token(self):
        return self.access_token

    def auto_refresh(self):
        if not self.username:
            return

        def refresh():
            while True:
                if self.last_refresh_time > 0 and self.token_ttl > 0 and self.token_refresh_window > 0:
                    sleep_time = self.token_ttl - self.token_refresh_window
                else:
                    sleep_time = 5

                time.sleep(sleep_time)
                success, err = self.login()
                if not success:
                    print(f"Login error: {err}")
                    time.sleep(5)
                else:
                    print(
                        f"Login success, tokenTtl: {self.token_ttl} seconds, tokenRefreshWindow: {self.token_refresh_window} seconds")

        threading.Thread(target=refresh, daemon=True).start()#asyncio

    def login(self):
        throwable = None
        for server in self.server_cfgs:
            result, err = self._login(server)
            throwable = err
            if result:
                return True, None
        return False, throwable

    def update_server_list(self, server_list):
        self.server_cfgs = server_list

    def get_server_list(self):
        return self.server_cfgs

    def _login(self, server):
        if self.username:
            context_path = server.get('contextPath', '/')
            if not context_path.startswith('/'):
                context_path = '/' + context_path
            if context_path.endswith('/'):
                context_path = context_path[:-1]

            scheme = server.get('scheme', 'http')
            req_url = f"{scheme}://{server['ipAddr']}:{server['port']}{context_path}/v1/auth/users/login"

            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'username': self.username,
                'password': self.password,
            }

            try:
                response = requests.post(req_url, headers=headers, data=data, timeout=self.token_ttl)
                response.raise_for_status()
            except requests.RequestException as e:
                return False, str(e)

            if response.status_code != 200:
                return False, response.text

            try:
                result = response.json()
            except json.JSONDecodeError as e:
                return False, str(e)

            if 'accessToken' in result:
                self.access_token = result['accessToken']
                self.last_refresh_time = int(time.time())
                self.token_ttl = int(result.get('tokenTtl', 0))
                self.token_refresh_window = self.token_ttl // 10

            return True, None

        return False, "Username not provided"
