import asyncio
import contextvars
import functools
import uuid

TRACE_ID = contextvars.ContextVar("trace_id", default="-")


def new_trace_id() -> str:
    return uuid.uuid4().hex


def get_trace_id() -> str:
    return TRACE_ID.get()


def set_trace_id(value: str) -> None:
    TRACE_ID.set(value)


def with_trace_id(trace_id: str | None = None):
    """装饰器：给同步/异步函数临时设置 trace_id（常用于一次性任务）"""

    def deco(fn):
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def aw(*a, **kw):
                token = TRACE_ID.set(trace_id or new_trace_id())
                try:
                    return await fn(*a, **kw)
                finally:
                    TRACE_ID.reset(token)

            return aw
        else:
            @functools.wraps(fn)
            def w(*a, **kw):
                token = TRACE_ID.set(trace_id or new_trace_id())
                try:
                    return fn(*a, **kw)
                finally:
                    TRACE_ID.reset(token)

            return w

    return deco


def create_task(coro: asyncio.coroutines, *, name: str | None = None) -> asyncio.Task:
    """在保留当前 contextvars 的前提下创建子任务。"""
    ctx = contextvars.copy_context()
    # 让 create_task 在相同的上下文里运行，确保 TRACE_ID 继承
    return ctx.run(asyncio.create_task, coro, name=name)
