import base64
import hmac
from hashlib import sha1


class SignUtil:
    @staticmethod
    def sign(data: str, key: str) -> str:
        hmac_code = hmac.new(key.encode(), data.encode(), sha1)
        return base64.b64encode(hmac_code).decode()
