import logging
import unittest
from unittest.mock import patch, MagicMock
import time
import json

from security_proxy import AuthClient

class TestAuthClient(unittest.TestCase):

    def __init__(self, methodName: str = ...):
        super().__init__(methodName)

    def setUp(self):
        self.client_cfg = {
            'username': 'nacos',
            'password': 'nacos'
        }
        self.server_cfgs = [
            {
                'ipAddr': '192.168.220.1',
                'port': 8848,
                'contextPath': '/nacos',
                'scheme': 'http'
            }
        ]
        self.auth_client = AuthClient(self.client_cfg, self.server_cfgs)

    @patch('requests.post')
    def test_login_success(self, mock_post):
        """
        测试成功登录的情况。
        成功会返回 True，错误信息为 None。
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'accessToken': 'test_token',
            'tokenTtl': 600
        }
        mock_post.return_value = mock_response

        success, err = self.auth_client.login()

        self.assertTrue(success)
        self.assertIsNone(err)
        self.assertEqual(self.auth_client.get_access_token(), 'test_token')
        self.assertGreater(self.auth_client.token_ttl, 0)

    @patch('requests.post')
    def test_login_failure(self, mock_post):
        """
        测试登录失败的情况。
        失败会返回 False，并返回错误信息。
        """
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_post.return_value = mock_response

        success, err = self.auth_client.login()

        self.assertFalse(success)
        self.assertEqual(err, 'Unauthorized')
        self.assertIsNone(self.auth_client.get_access_token())

    def test_get_access_token_no_token(self):
        """
        测试在没有访问令牌时，get_access_token 返回 None。
        """
        self.assertIsNone(self.auth_client.get_access_token())

    @patch('client_auth.requests.post')
    def test_get_access_token_with_token(self, mock_post):
        """
        测试在成功登录后，get_access_token 返回访问令牌。
        """
        # 配置模拟的登录响应
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'accessToken': 'mocked_access_token',
            'tokenTtl': 3600  # 令牌有效期1小时
        }

        # 执行登录
        success, _ = self.auth_client.login()

        # 检查登录是否成功
        self.assertTrue(success)

        # 检查访问令牌是否正确设置
        self.assertEqual(self.auth_client.get_access_token(), 'mocked_access_token')

    def test_get_server_list(self):
        """
        测试 get_server_list 返回正确的服务器列表。
        """
        # self.assertEqual(self.auth_client.get_server_list(), self.server_cfgs)
        self.assertEqual(self.auth_client.get_server_list(), self.server_cfgs,
                         f"Expected server list: {self.auth_client.get_server_list()}\nActual server list: {self.server_cfgs}")
        print("Expected server list:", self.auth_client.get_server_list())
        print("Actual server list:", self.server_cfgs)

    @patch('requests.post')
    def test_auto_refresh(self, mock_post):
        """
        测试自动刷新功能。
        成功会刷新访问令牌，并在令牌过期前刷新令牌。
        """
        # 模拟初次登录的响应
        initial_response = MagicMock()
        initial_response.status_code = 200
        initial_response.json.return_value = {
            'accessToken': 'test_token',
            'tokenTtl': 10
        }

        # 模拟刷新时的响应
        refresh_response = MagicMock()
        refresh_response.status_code = 200
        refresh_response.json.return_value = {
            'accessToken': 'refreshed_token',
            'tokenTtl': 10
        }

        mock_post.side_effect = [initial_response, refresh_response]

        self.auth_client.auto_refresh()

        # 初次登陆
        time.sleep(1)
        self.assertEqual(self.auth_client.get_access_token(), 'test_token')

        # 等待自动刷新
        time.sleep(10)
        self.assertEqual(self.auth_client.get_access_token(), 'refreshed_token')

    def test_update_server_list(self):
        """
        测试更新服务器列表。
        """
        new_server_cfgs = [
            {
                'ipAddr': '192.168.1.1',
                'port': 8848,
                'contextPath': '/nacos',
                'scheme': 'http'
            }
        ]
        self.auth_client.update_server_list(new_server_cfgs)
        self.assertEqual(self.auth_client.get_server_list(), new_server_cfgs)


if __name__ == '__main__':
    unittest.main()
