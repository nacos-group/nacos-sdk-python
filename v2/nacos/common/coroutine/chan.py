import asyncio
import atexit

class Chan:
    def __init__(self, size=0):
        """size 0 indicates a synchronous channel (handshake)
        size -1 indicates an unlimited buffer size
        otherwise send will block when buffer size is reached"""
        if size == 0:
            self.q = asyncio.Queue(0)
            # self.x = asyncio.Queue(0)
        elif size == -1:
            self.q = asyncio.Queue(0)
        else:
            self.q = asyncio.Queue(size)
        self.size = size
        self.is_closed = False

    async def close(self):
        """closes the channel which leads to a failure at the recv side if empty and disallows further sending"""
        self.is_closed = True
        # while not self.q.empty(): 
        #     await self.q.get()
        # self.q.put(None)
        if not self.q.empty():
           self.q.put(None)
  
    async def send(self, item):
        """blocks if size=0 until there is a recv and this send operation was chosen
        blocks if send was used <size> times without a recv
        blocks never for size=-1"""
        if self.is_closed:
            raise ChannelClosed
        await self.q.put(item)

    def send_ready(self):
          return not self.q.full()
  
    def recv_ready(self):
        return not self.q.empty()
  
    async def recv(self):
        """blocks until something is available
        fails if channel is closed after all is processed"""
        # if self.size == 0:
        #     await self.x.put(True)
        item = await self.q.get()
        print("g:", item)
        if item is None:
            raise ChannelClosed
        return item
  
    async def __aiter__(self):
        return self
  
    async def __anext__(self):
        try:
            return await self.recv()
        except ChannelClosed:
            raise StopAsyncIteration

class ChannelClosed(Exception):
    pass


loop = asyncio.get_event_loop() 
atexit.register(loop.close)

