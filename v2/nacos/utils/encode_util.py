import base64
from binascii import Error


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
    try:
        # Use base64's decode method without referencing binascii explicitly
        return base64.b64decode(bytes_)
    except Error as e:
        # Return the error message in a more Pythonic way
        return None, str(e)


def encode_base64(bytes_):
    # Simply encode the input bytes to Base64
    return base64.b64encode(bytes_).decode('utf-8')  # Decoding to string for consistency with Go's behavior
