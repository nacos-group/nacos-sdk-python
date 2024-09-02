from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


def encrypt_to_bytes(data_key_bytes: bytes, content_bytes: bytes):
    cipher = AES.new(data_key_bytes, AES.MODE_ECB)
    encrypted_bytes = cipher.encrypt(
        pad(content_bytes, AES.block_size))
    return encrypted_bytes


def decrypt_to_bytes(data_key_bytes: bytes, content_bytes: bytes):
    # print(type(base64.b64decode(content)))
    cipher = AES.new(data_key_bytes,
                     AES.MODE_ECB)
    decrypted_bytes = unpad(cipher.decrypt(content_bytes),
                            AES.block_size)
    return decrypted_bytes


def get_random_bytes_from_crypto(length: int):
    return get_random_bytes(length)
