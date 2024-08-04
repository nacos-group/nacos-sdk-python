import asyncio
import atexit

async def wrap_future(event, coro):
    if asyncio.iscoroutine(coro): 
        task = asyncio.ensure_future(coro) 
    else: 
        task = asyncio.ensure_future(coro()) 
    return event, task
    

class SelectTasks:
    """helper class used for (pending) await-tasks monitored by select()"""
    def __init__(self, futures_list=None, already_running=False, completed=None):
        self.tasks = []
        if futures_list and not already_running:
            self.extend(futures_list)
        elif futures_list and already_running:
            self.tasks = list(futures_list)
        else:
            self.tasks = []
        self.completed = completed if completed else []
  
    def append(self, a):
        e, f = a
        self.tasks.append(asyncio.ensure_future(wrap_future(e,f)))
  
    def extend(self, futures_list):
        new_tasks = [asyncio.ensure_future(wrap_future(e,f)) for e, f in futures_list if asyncio.ensure_future(wrap_future(e,f)) is not None]
        self.tasks.extend(new_tasks)
  
    def __bool__(self):
        return bool(self.tasks) or bool(self.completed)
  
    def __len__(self):
        return len(self.tasks) + len(self.completed)


async def select(futures_list):
    if not isinstance(futures_list, SelectTasks):
        futures_list = SelectTasks(futures_list)
    done, running = await asyncio.wait(futures_list.tasks,
                                            return_when=asyncio.FIRST_COMPLETED)
    results = []
    for task in done:
       result = task.result()
       results.append((result))
    new_select_tasks = SelectTasks(running, already_running=True, completed=results)
    return results, new_select_tasks


loop = asyncio.get_event_loop() 
atexit.register(loop.close)


