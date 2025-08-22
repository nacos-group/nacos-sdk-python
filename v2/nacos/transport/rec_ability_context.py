import asyncio
from typing import Optional, Dict

from v2.nacos.transport.grpc_connection import GrpcConnection


class RecAbilityContext:

    def __init__(self, logger, connection: Optional[GrpcConnection] = None):

        self.connection = connection
        self.blocker: Optional[asyncio.Event] = asyncio.Event()
        self.need_to_sync = False
        self.logger = logger

        # 初始化状态
        if connection is not None:
            self.blocker.set()  # 默认设置为已触发状态
        else:
            self.blocker.clear()

    def is_need_to_sync(self) -> bool:
        return self.need_to_sync

    def reset(self, connection: GrpcConnection) -> None:
        self.connection = connection
        self.blocker = asyncio.Event()  # 创建新的事件对象
        self.need_to_sync = True

    def release(self, abilities: Optional[Dict[str, bool]]) -> None:
        if self.connection is not None:
            self.connection.set_ability_table(abilities)
            # 避免重复设置
            self.connection = None

        if self.blocker is not None:
            self.blocker.set()

        self.need_to_sync = False

    async def await_abilities(self, timeout: float) -> None:
        if self.blocker is not None:
            try:
                await asyncio.wait_for(self.blocker.wait(), timeout=timeout/1000)
            except asyncio.TimeoutError:
                self.logger.warning("Waiting for server abilities timeout")
                raise
        self.need_to_sync = False

    def check(self, connection: GrpcConnection) -> bool:

        if not connection.is_abilities_set():
            self.logger.error(
                    "Client don't receive server abilities table even empty table "
                    "but server supports ability negotiation. "
                    "You can check if it is need to adjust the timeout of ability "
                    "negotiation if always fail to connect."
            )
            connection.set_abandon(True)
            connection.close()
            return False
        return True