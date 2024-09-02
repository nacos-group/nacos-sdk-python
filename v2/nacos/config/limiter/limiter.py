from pyrate_limiter import Rate, Limiter, BucketFullException


class RateLimiterCheck:
    _limiter = Limiter(Rate(5, 1))
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RateLimiterCheck()
        return cls._instance

    @staticmethod
    def is_limited(check_key: str):
        try:
            instance = RateLimiterCheck.get_instance()
            instance._limiter.try_acquire(check_key)
            return False
        except BucketFullException:
            return True
        except Exception as e:
            raise
