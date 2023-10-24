import socket
import threading
import urllib.parse

from caul_proxy.config import logger


def create_proxy_server(ip: str = '0.0.0.0', port: int = 1080) -> socket.socket:
    proxy_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_server_socket.bind((ip, port))
    proxy_server_socket.listen(10)
    return proxy_server_socket


def handle_http_get(client_socket: socket.socket, timeout: int = 60):
    """
    处理客户端请求
    :param client_socket:
    :param timeout:
    :return:
    """
    target_socket = None
    try:
        request_header = parse_http_header(client_socket)
        target_socket = send_target_server(request_header)
        target_socket.settimeout(timeout)
        forward_response(client_socket, target_socket)
    except:
        logger.exception("Proxy Error")
    finally:
        client_socket.close()
        target_socket and target_socket.close()


header_end = b'\r\n\r\n'


def parse_http_header(client_socket: socket.socket) -> bytes:
    """
    处理GET协议头
    :param client_socket:
    :return:
    """
    request_header = b''
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        request_header += data
        if header_end in request_header:
            return request_header.split(header_end)[0]
    return request_header


def send_target_server(request_header: bytes) -> socket.socket:
    """
    发送目标服务器
    :param request_header:
    :return:
    """
    target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target_socket.connect(parse_target_address(request_header))
    target_socket.send(request_header)
    return target_socket


def parse_target_address(request_header: bytes) -> (str, int):
    """
    解析目标服务地址
    :param request_header:
    :return:
    """
    # 解析请求报文
    header_lines = request_header.decode('utf8').split("\r\n")
    # 获取请求方法、URL和协议版本
    _, url, *args = header_lines[0].split()
    # 解析URL
    url_parts = urllib.parse.urlparse(url)
    port = url_parts.port
    if not port:
        port = 80 if url_parts.scheme.lower() == 'http' else 443
    return url_parts.hostname, port


def forward_response(client_socket: socket.socket, target_socket: socket.socket):
    """
    获取响应结果
    :param client_socket:
    :param target_socket:
    :return:
    """
    while True:
        data = target_socket.recv(4096)
        if not data:
            break
        client_socket.send(data)
        # if data.endswith(b'\r\n\r\n'):
        #     break


def start_server(ip: str = '0.0.0.0', port: int = 1080, timeout: int = 60):
    # 创建代理服务器套接字(只支持GET请求)
    server_socket = create_proxy_server(ip=ip, port=port)
    print("**********************************************************")
    print("******************* CaulProxy 1.0.0 **********************")
    print(f"*******************  IP:{ip} PORT:{port} ***********")
    print("**********************************************************")
    while True:
        # 等待客户端连接
        client_socket, client_address = server_socket.accept()
        # 创建线程处理客户端请求
        client_thread = threading.Thread(target=handle_http_get, args=(client_socket, timeout))
        client_thread.start()
