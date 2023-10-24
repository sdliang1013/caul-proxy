import re
import typing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests
import urllib3.util

from caul_proxy import util
from caul_proxy.config import settings, logger
from caul_proxy.plugins import runner


class ProxyHandler(BaseHTTPRequestHandler):

    def do_HEAD(self):
        """处理HEAD请求"""
        self.do_request(lambda url: requests.head(url=url, headers=self.req_headers(),
                                                  timeout=self.timeout))

    def do_GET(self):
        """处理GET请求"""
        self.do_request(lambda url: requests.get(url=url, headers=self.req_headers(),
                                                 timeout=self.timeout))

    def do_POST(self):
        """处理POST请求"""
        self.do_request(lambda url: requests.post(url=url, headers=self.req_headers(),
                                                  data=self.req_data(), timeout=self.timeout))

    def do_request(self, func: typing.Callable):
        # allows and denys
        if self.is_deny() or not self.is_allow():
            self.send_error(code=403)
            return
        # rewrite
        try:
            url_parts = urllib3.util.parse_url(self.path)
            uri = runner.rewrite_uri(url_parts)
            url = runner.rewrite_domain(url_parts) + uri
            if uri.startswith('http://') or uri.startswith('https://'):
                url = uri
        except BaseException as e:
            logger.error(f'{self.command} {self.path} {self.protocol_version}: {util.err_msg(e)}\n'
                         f'{util.err_msg(e)}')
            raise
        # forward
        try:
            with func(url) as response:
                logger.info(f'{self.command} {url} {self.protocol_version} {response.status_code}')
                # code
                self.send_response(response.status_code)
                # headers
                self.resp_headers(response)
                # body
                self.resp_data(response)
        except BaseException as e:
            logger.error(f'{self.command} {url} {self.protocol_version}\n'
                         f'{util.err_msg(e)}')
            raise

    def req_headers(self) -> dict:
        headers = {}
        for header, value in self.headers.items():
            headers.update({header: value})
        return headers

    def req_data(self) -> typing.AnyStr:
        return self.rfile.read()

    def resp_headers(self, response: requests.Response):
        # cross domain
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        # for header, value in response.headers.items():
        for header in ['Content-Type', 'Content-Length']:  # 'Transfer-Encoding', 'Connection', 'Content-Encoding'
            value = response.headers.get(header, None)
            if value:
                self.send_header(header, value)
        self.end_headers()

    def resp_data(self, response: requests.Response):
        for content in response.iter_content(chunk_size=4096):
            self.wfile.write(content)

    def is_allow(self) -> bool:
        host, port = self.client_address
        if not settings.allows:
            return True
        for allow in settings.allows:
            if re.match(pattern=allow, string=host):
                return True
        return False

    def is_deny(self) -> bool:
        host, port = self.client_address
        if not settings.denys:
            return False
        for deny in settings.denys:
            if re.match(pattern=deny, string=host):
                return False
        return True


def start_server(ip: str = '0.0.0.0', port: int = 1080, timeout: int = 60):
    ProxyHandler.timeout = timeout
    http_server = ThreadingHTTPServer((ip, port), ProxyHandler)
    print("**********************************************************")
    print("******************* CaulProxy 1.0.0 **********************")
    print(f"*******************  IP:{ip} PORT:{port} ***********")
    print("**********************************************************")
    http_server.serve_forever()

# ############################################################################
# -----------------------------------plugins----------------------------------
# ############################################################################
