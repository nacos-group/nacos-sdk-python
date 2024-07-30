import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from v2.nacos.config.encryption.abstract_encryption_plugin_service import AbstractEncryptionPluginService
import logging
#pip install pycryptodome

# 设置日志配置
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class EncryptionPluginService(AbstractEncryptionPluginService):
    # class EncryptionPluginService:
    def __init__(self):
        self.ALGORITHM = 'AES'
        self.AES_PKCS5P = 'AES/ECB/PKCS5Padding'
        self.content_key = self.generate_key()
        self.the_key_of_content_key = self.generate_key()

    def generate_key(self, length=16):
        return base64.urlsafe_b64encode(
            get_random_bytes(length)).decode('utf-8')

    def encrypt(self, secret_key, content):
        cipher = AES.new(secret_key.encode('utf-8'), AES.MODE_ECB)
        encrypted_bytes = cipher.encrypt(
            pad(content.encode('utf-8'), AES.block_size))
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt(self, secret_key, content):
        if not content:
            return None
        cipher = AES.new(secret_key.encode('utf-8'), AES.MODE_ECB)
        decrypted_bytes = unpad(cipher.decrypt(base64.b64decode(content)),
                                AES.block_size)
        return decrypted_bytes.decode('utf-8')

    def generate_secret_key(self):
        return self.content_key

    def algorithm_name(self):
        return self.ALGORITHM.lower()

    def encrypt_secret_key(self, secret_key):
        cipher = AES.new(self.the_key_of_content_key.encode('utf-8'),
                         AES.MODE_ECB)
        encrypted_bytes = cipher.encrypt(
            pad(self.content_key.encode('utf-8'), AES.block_size))
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt_secret_key(self, secret_key):
        if not secret_key:
            return None
        cipher = AES.new(self.the_key_of_content_key.encode('utf-8'),
                         AES.MODE_ECB)
        decrypted_bytes = unpad(cipher.decrypt(base64.b64decode(secret_key)),
                                AES.block_size)
        return decrypted_bytes.decode('utf-8')
