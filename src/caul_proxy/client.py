# -*- coding: utf-8 -*-
# desc: 测试使用socks5代理访问
import asyncio

import aiohttp
from aiohttp_socks import ProxyConnector


async def fetch(url):
    server_address = '127.0.0.1'
    server_port = 2080
    username = 'caul'
    password = 'caulproxy'
    connector = ProxyConnector.from_url(f'socks5://{username}:{password}@{server_address}:{server_port}')

    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as response:
            return await response.text(encoding='utf-8')


if __name__ == '__main__':
    asyncio.run(fetch("https://cqu.edu.cn"))
