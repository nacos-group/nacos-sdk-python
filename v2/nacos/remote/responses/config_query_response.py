from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type


class ConfigQueryResponse(response.Response):
    CONFIG_NOT_FOUND = 300
    CONFIG_QUERY_CONFLICT = 400

    def __init__(self):
        self.content = ""
        self.content_type = ""
        self.md5 = ""
        self.isBeta = False
        self.tag = ""
        self.last_modified = None  # integer
        self.encrypted_data_key = ""

    def get_remote_type(self):
        return remote_response_type["ConfigQuery"]

    @staticmethod
    def build_fail_response(error_code, message):
        new_response = ConfigQueryResponse()
        new_response.set_error_code(error_code, message)
        return new_response

    @staticmethod
    def build_success_response(content):
        new_response = ConfigQueryResponse()
        new_response.set_contend(content)
        return new_response

    def get_tag(self):
        return self.tag

    def set_tag(self, tag):
        self.tag = tag

    def get_md5(self):
        return self.md5

    def set_md5(self, md5):
        self.md5 = md5

    def get_last_modified(self):
        return self.last_modified

    def set_last_modified(self, last_modified):
        self.last_modified = last_modified

    def is_beta(self):
        return self.isBeta

    def set_beta(self, beta):
        self.isBeta = beta

    def get_contend(self):
        return self.content

    def set_contend(self, contend):
        self.content = contend

    def get_encrypted_data_key(self):
        return self.encrypted_data_key

    def set_encrypted_data_key(self, encrypted_data_key):
        self.encrypted_data_key = encrypted_data_key

    def get_content_type(self):
        return self.content_type

    def set_content_type(self, content_type):
        self.content_type = content_type
