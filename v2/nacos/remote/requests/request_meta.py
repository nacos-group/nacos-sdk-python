class RequestMeta:
    def __init__(self):
        self.__connection_id = ""
        self.__client_ip = ""
        self.__client_version = ""
        self.__labels = {}

    def get_client_version(self):
        return self.__client_version

    def set_client_version(self, client_version):
        self.__client_version = client_version

    def get_labels(self):
        return self.__labels

    def set_labels(self, labels):
        self.__labels = labels

    def get_connection_id(self):
        return self.__connection_id

    def set_connection_id(self, connection_id):
        self.__connection_id = connection_id

    def get_client_ip(self):
        return self.__client_ip

    def set_client_ip(self, client_ip):
        self.__client_ip = client_ip

    def __str__(self):
        return "RequestMeta{connectionId='" + self.__connection_id + "', clientIp='" + self.__client_ip +\
               "', clientVersion='" + "', labels=" + str(self.__labels) + "}"
