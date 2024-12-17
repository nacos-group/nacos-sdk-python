import base64

from Crypto.Cipher import AES

from v2.nacos.utils.encode_util import str_to_bytes, bytes_to_str, decode_base64


def pad(byte_array: bytes) -> bytes:
    """
    pkcs5 padding
    """
    block_size = AES.block_size
    pad_len = block_size - len(byte_array) % block_size
    return byte_array + (bytes([pad_len]) * pad_len)


# pkcs5 - unpadding
def unpad(byte_array: bytes) -> bytes:
    return byte_array[:-ord(byte_array[-1:])]


def encrypt(message: str, key: str) -> str:
    byte_array = str_to_bytes(message)
    key_bytes = decode_base64(str_to_bytes(key))
    aes = AES.new(key_bytes, AES.MODE_ECB)
    padded = pad(byte_array)
    encrypted = aes.encrypt(padded)
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt(encr_data: str, key: str) -> str:
    byte_array = decode_base64(str_to_bytes(encr_data))
    key_bytes = decode_base64(str_to_bytes(key))
    aes = AES.new(key_bytes, AES.MODE_ECB)
    decrypted = aes.decrypt(byte_array)
    return bytes_to_str(unpad(decrypted))
