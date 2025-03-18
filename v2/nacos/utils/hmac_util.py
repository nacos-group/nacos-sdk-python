import base64
import hashlib
import hmac


def sign_with_hmac_sha1_encrypt(encrypt_text: str, encrypt_key: str):
    if not encrypt_key:
        encrypt_key = ""
    key = encrypt_key.encode()
    mac = hmac.new(key, digestmod=hashlib.sha1)
    mac.update(encrypt_text.encode())

    return base64.b64encode(mac.digest()).decode()
