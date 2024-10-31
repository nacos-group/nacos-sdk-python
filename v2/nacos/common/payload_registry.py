class PayloadRegistry:
    _REGISTRY_REQUEST = {}

    @classmethod
    def init(cls, payloads):
        cls.payloads = payloads
        cls.scan()

    @classmethod
    def scan(cls):
        for payload_class in cls.payloads:
            cls.register(payload_class.__name__, payload_class)

    @classmethod
    def register(cls, type_name, clazz):
        if isinstance(clazz, type) and any("Abstract" in b.__name__ for b in clazz.__bases__):
            return
        if type_name in cls._REGISTRY_REQUEST:
            raise RuntimeError(f"Fail to register, type:{type_name}, clazz:{clazz.__name__}")
        cls._REGISTRY_REQUEST[type_name] = clazz

    @classmethod
    def get_class_by_type(cls, type_name):
        return cls._REGISTRY_REQUEST.get(type_name)
