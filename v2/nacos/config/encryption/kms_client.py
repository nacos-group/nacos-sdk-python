from alibabacloud_kms20160120 import models as kms_20160120_models
from alibabacloud_kms20160120.client import Client
from alibabacloud_tea_openapi import models as open_api_models

from v2.nacos.common.client_config import KMSConfig
from v2.nacos.utils.encode_util import bytes_to_str


class KmsClient:
    def __init__(self, client: Client):
        self.client = client

    @staticmethod
    def create_kms_client(kms_config: KMSConfig):
        config = open_api_models.Config(
            access_key_id=kms_config.access_key,
            access_key_secret=kms_config.secret_key,
            endpoint=kms_config.endpoint)
        config.protocol = "https"
        client = Client(config)
        kms_client = KmsClient(client)
        return kms_client

    def encrypt(self, content: str, key_id: str):
        encrypt_request = kms_20160120_models.EncryptRequest()
        encrypt_request.plaintext = content.encode("utf-8")
        encrypt_request.key_id = key_id
        encrypt_response = self.client.encrypt(encrypt_request)
        return encrypt_response.body.ciphertext_blob

    def decrypt(self, content: str):
        decrypt_request = kms_20160120_models.DecryptRequest(ciphertext_blob=content)
        decrypt_response = self.client.decrypt(decrypt_request)
        return decrypt_response.body.plaintext

    def generate_secret_key(self, key_id: str, key_spec: str):
        request = kms_20160120_models.GenerateDataKeyRequest()
        request.key_id = key_id
        request.key_spec = key_spec
        resp = self.client.generate_data_key(request)
        return resp.body.plaintext, resp.body.ciphertext_blob
