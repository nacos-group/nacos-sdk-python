import asyncio
import threading
import atexit

#有这里统一管理生命周期
loop = asyncio.get_event_loop()  
atexit.register(loop.close)


