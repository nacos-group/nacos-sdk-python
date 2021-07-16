from abc import abstractmethod


class Request:
    def __init__(self):
        self.headers = {}
        self.request_id = ""

    def put_header(self, key, value):
        self.headers[key] = value

    def put_all_header(self, headers):
        if not headers:
            return
        self.headers.update(headers)

    def get_header(self, key, default_value=None):
        return self.headers[key] if self.headers[key] else default_value

    def set_request_id(self, request_id):
        self.request_id = request_id

    @abstractmethod
    def get_module(self):
        pass

    @abstractmethod
    def get_remote_type(self):
        pass

    def get_headers(self):
        return self.headers

    def clear_headers(self):
        self.headers.clear()

    def __str__(self):
        return self.__class__.__name__ + "{headers" + str(self.headers) + ", requestId='" + self.request_id + "'}"
