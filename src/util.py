import asyncio
import functools
import hashlib
import json
import os
import re
from asyncio.events import AbstractEventLoop
from concurrent import futures
from pathlib import Path
from typing import Callable, Any, TypeVar, List

import anyio

_TYPE_PARSERS_ = {
    bool: lambda v: str(v).lower() in ['true', '1', 'yes'] if v else False,
    dict: lambda v: json.loads(v) if v else {},
    list: lambda v: json.loads(v) if v else []
}

T = TypeVar("T")

executor = futures.ThreadPoolExecutor(max_workers=min(32, os.cpu_count() + 4), thread_name_prefix="AsyncThread")


async def as_async(func, loop: AbstractEventLoop = None, pool: futures.Executor = None, *args, **kwargs):
    if not loop:
        loop = asyncio.get_event_loop()
    if not pool:
        pool = executor
    return await loop.run_in_executor(pool, lambda: func(*args, loop=loop, **kwargs))


def call_soon(func, loop: AbstractEventLoop = None, thread_safe: bool = False, *args, **kwargs):
    if not loop:
        loop = asyncio.get_event_loop()
    if thread_safe:
        return loop.call_soon_threadsafe(lambda: func(*args, loop=loop, **kwargs))
    return loop.call_soon(lambda: func(*args, loop=loop, **kwargs))


def run_coroutine(task, loop: AbstractEventLoop = None):
    if not loop:
        loop = asyncio.get_event_loop()
    return asyncio.run_coroutine_threadsafe(coro=task, loop=loop)


def gather(*tasks, loop: AbstractEventLoop = None):
    if not loop:
        loop = asyncio.get_event_loop()
    fut = asyncio.gather(*tasks, loop=loop, return_exceptions=True)
    if loop.is_running():
        return fut
    return loop.run_until_complete(fut)


async def run_in_threadpool(func: Callable[..., T],
                            *args: Any,
                            loop=None,
                            **kwargs: Any
                            ):
    if loop is None:
        loop = asyncio.get_event_loop()
    if kwargs:
        # loop.run_in_executor doesn't accept 'kwargs', so bind them in here
        func = functools.partial(func, **kwargs)
    return await loop.run_in_executor(None, func, *args)


async def read_last(path: str, lines: int = 1) -> (list, int):
    """
    读取文件最后的内容

    :param path:
    :param lines: 最后的行数
    :return:
    """
    lines = max(lines, 1)
    limit = os.stat(path).st_size
    async with await anyio.open_file(file=path, mode='rb') as f:  # 打开文件
        off = 50  # 设置偏移量
        while True:
            if off >= limit:
                await f.seek(0)
                last_lines = await f.readlines()  # 读取文件指针范围内所有行
                tell = await f.tell()
                break
            await f.seek(-off, 2)  # seek(off, 2)表示文件指针：从文件末尾(2)开始向前50个字符(-50)
            last_lines = await f.readlines()  # 读取文件指针范围内所有行
            if len(last_lines) >= lines:  # 判断是否最后至少有两行，这样保证了最后一行是完整的
                last_lines = last_lines[-lines:]
                tell = await f.tell()
                break
            off *= 2

    return last_lines, tell


async def read_lines(path: str, lines: int = 0, offset: int = 0) -> (list, int, bool):
    size = os.stat(path).st_size
    content = list()
    # is end
    if offset >= size:
        return content, size, True
    async with await anyio.open_file(file=path, mode='rb') as f:
        if offset:
            await f.seek(offset)
        if not lines:
            content = await f.readlines()
            tell = size
        else:
            for _ in range(lines):
                content.append(await f.readline())
                tell = await f.tell()
                if tell >= size:
                    break

    return content, tell, tell >= size


async def read_range(path: str, start: int = 0, end: int = -1) -> bytes:
    """

    :param path:
    :param start:
    :param end:
    :return: [start, end)
    """
    len_file = os.stat(path=path).st_size
    if end < 0 or end > len_file:
        end = len_file
    # end
    if start >= end or start >= len_file:
        return b''
    async with await anyio.open_file(file=path, mode='rb') as file:
        await file.seek(start)
        return await file.read(end - start)


def text_hash(text: str, types="md5"):
    """
    计算text的hash值

    :param text:
    :param types:
    :return:
    """
    type_ary = types
    if isinstance(types, str):
        type_ary = [types]
    hash_dict = {t: getattr(hashlib, type)() for t in type_ary}
    data = text.encode(encoding="utf-8")
    for _, h in hash_dict.items():
        h.update(data)
    if isinstance(types, str):
        return hash_dict.get(types).hexdigest()
    return {t: h.hexdigest() for t, h in hash_dict.items()}


def path_join(path_1: str, path_2: str):
    """
    路径合并

    :param path_1:
    :param path_2:
    :return:
    """
    splits = ['/', '\\']
    prefix = path_1
    suffix = path_2
    if path_1 and path_1[-1] in splits:
        prefix = path_1[:-1]
    if path_2 and path_2[0:1] in splits:
        suffix = path_2[1:]
    return f'{prefix}/{suffix}'


def abspath(path: str, prefix=None):
    """
    相对路径->绝对路径

    :param path:
    :param prefix:
    :return:
    """
    if path[0:1] == "/" or re.match("[A-Za-z]:", path[0:2]):
        return path
    if prefix:
        return path_join(prefix, path)
    return os.path.abspath(path)


def array_filter(data: List, func: Callable) -> List:
    """
    类似Array的Filter操作

    :param data:
    :param func:
    :return:
    """
    ary = []
    for item in data:
        if func(item):
            ary.append(item)
    return ary


def file_info(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    stat = os.stat(path)
    p = Path(path)
    return {
        "name": p.name,
        "suffix": p.suffix,
        "size": stat.st_size,
        "create_time": stat.st_ctime,
        "modify_time": stat.st_mtime,
        "access_time": stat.st_atime,
    }


def parse_value(value: Any, typing: type = str):
    if value is None or isinstance(value, typing):
        return value
    if typing in _TYPE_PARSERS_:
        return _TYPE_PARSERS_[typing](value)
    return typing(value)


def err_msg(e: BaseException) -> str:
    return str(e) or e.__class__.__name__
