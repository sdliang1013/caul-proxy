import aiohttp
import uvicorn
from fastapi import FastAPI
from fastapi import Request
from starlette.responses import Response

app = FastAPI(title="Yhop Proxy",
              version="0.0.1",
              openapi_url="/openapi.json", )


@app.route("/", methods=['HEAD', 'OPTION', 'GET', 'POST'])
async def proxy(request: Request):
    url = request.url
    method = request.method
    headers = request.headers
    data = await request.body()
    # 发送转发请求到目标服务器
    async with aiohttp.ClientSession(timeout=5) as session:
        async with session.request(method=method, url=str(url), headers=headers, data=data) as response:
            # 构造响应对象，并将目标服务器的响应返回给客户端
            resp = Response(status_code=response.status,
                            content=response.content,
                            headers=response.headers)
    return resp


def start_server(ip: str = '0.0.0.0', port: int = 1080, timeout: int = 60):
    uvicorn.run(app, host=ip, port=port)
