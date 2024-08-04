import asyncio
import threading
import atexit

count_tasks = 0


def counter(i=0):
    global count_tasks
    count_tasks += i
    return count_tasks


loop = asyncio.get_event_loop()
atexit.register(loop.close)


def coroutine(f, *args, **kwargs):
    """schedule an async function on the asyncio event loop of the worker thread
    returns a concurrent.future which has a (non-await) blocking .result() method to wait until the result of f() is returned"""
    async def wrapper():
        if asyncio.iscoroutinefunction(f):
            task = asyncio.ensure_future(f(*args, **kwargs))
        else:
            task = f
        x = await task
        counter(-1)
        if counter() == 0:
            loop.stop()
        return x
    wrapped_task = loop.create_task(wrapper()) if asyncio.iscoroutinefunction(f) else f
    counter(+1)
    if not loop.is_running():
        threading.Thread(name='eventloop-worker', target=loop.run_forever).start()
    return wrapped_task
