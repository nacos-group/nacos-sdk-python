import logging #这两个logger.py,logging.py应该可以合并，我后面重新写一下

class NacosLogger:
    @staticmethod
    def get_logger():
        # 在这里实现获取日志器的逻辑，例如：
        # logger = logging.getLogger(__name__)
        # logger.setLevel(logging.INFO)
        # 添加日志处理器等
        pass

    @classmethod
    def info(cls, *args):
        cls.get_logger().info(*args)

    @classmethod
    def warn(cls, *args):
        cls.get_logger().warning(*args)

    @classmethod
    def error(cls, *args):
        cls.get_logger().error(*args)

    @classmethod
    def debug(cls, *args):
        cls.get_logger().debug(*args)

    @classmethod
    def infof(cls, fmt, *args):
        cls.get_logger().info(fmt, *args)

    @classmethod
    def warnf(cls, fmt, *args):
        cls.get_logger().warning(fmt, *args)

    @classmethod
    def errorf(cls, fmt, *args):
        cls.get_logger().error(fmt, *args)

    @classmethod
    def debugf(cls, fmt, *args):
        cls.get_logger().debug(fmt, *args)