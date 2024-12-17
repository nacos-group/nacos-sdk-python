import base64


def str_to_bytes(text: str, encoding: str = 'utf-8') -> bytes:
    """
    将字符串转换为字节。

    :param text: 要转换的字符串
    :param encoding: 字符串的编码方式，默认为 'utf-8'
    :return: 转换后的字节
    """
    return text.encode(encoding)


def bytes_to_str(bytes_, encoding: str = 'utf-8'):
    if not bytes_:
        return ""
    # Directly decode the UTF-8 bytes back to a string
    return bytes_.decode(encoding)


def decode_base64(bytes_: bytes):
    return base64.b64decode(bytes_)


def encode_base64(bytes_):
    # Simply encode the input bytes to Base64
    return base64.b64encode(bytes_).decode('utf-8')  # Decoding to string for consistency with Go's behavior


def urlsafe_b64encode(bytes_):
    return base64.urlsafe_b64encode(bytes_).decode('utf-8')
