import base64


def decode_string_to_utf8_bytes(data):
    if not data:
        return bytearray()
    # Python strings are Unicode, so we directly encode to get the UTF-8 bytes
    return data.encode('utf-8')


def encode_utf8_bytes_to_string(bytes_):
    if not bytes_:
        return ""
    # Directly decode the UTF-8 bytes back to a string
    return bytes_.decode('utf-8')


def decode_base64(bytes_):
    return base64.b64decode(bytes_)


def encode_base64(bytes_):
    # Simply encode the input bytes to Base64
    return base64.b64encode(bytes_).decode('utf-8')  # Decoding to string for consistency with Go's behavior


def urlsafe_b64encode(bytes_):
    return base64.urlsafe_b64encode(bytes_).decode('utf-8')
