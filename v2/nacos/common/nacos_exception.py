CLIENT_INVALID_PARAM = -400

CLIENT_DISCONNECT = -401

CLIENT_OVER_THRESHOLD = -503

INVALID_PARAM = 400

NO_RIGHT = 403

NOT_FOUND = 404

CONFLICT = 409

SERVER_ERROR = 500

BAD_GATEWAY = 502

OVER_THRESHOLD = 503

INVALID_SERVER_STATUS = 300

UN_REGISTER = 301

NO_HANDLER = 302

INVALID_INTERFACE_ERROR = -403

RESOURCE_NOT_FOUND = -404

HTTP_CLIENT_ERROR_CODE = -500


class NacosException(Exception):
    """Custom exception class with an error code attribute."""

    def __init__(self, error_code, message="An error occurred"):
        self.error_code = error_code
        self.message = message
        super().__init__(f'Error [{error_code}]: {message}')
