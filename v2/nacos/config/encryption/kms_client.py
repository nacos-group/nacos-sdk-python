from openapi.models import Config
from sdk.client import Client
from sdk.models import EncryptRequest, DecryptRequest, GenerateDataKeyRequest
from v2.nacos.utils import encode_util

from v2.nacos.common.client_config import KMSConfig


class KmsClient:
    def __init__(self, client):
        self.client = client

    @staticmethod
    def create_kms_client(kms_config: KMSConfig):
        config = Config(endpoint=kms_config.endpoint,
                        client_key_content=kms_config.client_key_content,
                        password=kms_config.password)
        client = Client(config)
        kms_client = KmsClient(client)
        return kms_client

    def encrypt(self, content: str, key_id: str):
        encrypt_request = EncryptRequest()
        encrypt_request.plaintext = content.encode("utf-8")
        encrypt_request.key_id = key_id
        encrypt_response = self.client.encrypt(encrypt_request)
        return encrypt_response.ciphertext_blob

    def decrypt(self, content: str):
        decrypt_request = DecryptRequest(ciphertext_blob=content)
        decrypt_response = self.client.decrypt(decrypt_request)
        return decrypt_response.plaintext

    def generate_secret_key(self, key_id: str, algorithm: str):
        request = GenerateDataKeyRequest()
        request.key_id = key_id
        request.algorithm = algorithm
        resp = self.client.generate_data_key(request)
        return encode_util.encode_utf8_bytes_to_string(resp.plaintext), encode_util.encode_utf8_bytes_to_string(resp.ciphertext_blob)
