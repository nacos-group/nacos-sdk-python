import hashlib


def md5(content: str):
    if content:
        md = hashlib.md5()
        md.update(content.encode('utf-8'))
        return md.hexdigest()
    return ""
