import os
import sys

import typer

from caul_proxy import server_requests
from caul_proxy.config import settings
from caul_proxy.plugins import runner

# Remove '' and current working directory from the first entry
# of sys.path, if present to avoid using current directory
# in pip commands check, freeze, install, list and show,
# when invoked as python -m pip <command>
if sys.path[0] in ("", os.getcwd()):
    sys.path.pop(0)

# If we are running from a wheel, add the wheel to sys.path
# This allows the usage python pip-*.whl/pip install pip-*.whl
if __package__ == "":
    # __file__ is pip-*.whl/pip/__main__.py
    # first dirname call strips of '/__main__.py', second strips off '/pip'
    # Resulting path is the name of the wheel itself
    # Add that to sys.path so we can import pip
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)


def main(
        host: str = typer.Option("0.0.0.0"),
        port: int = typer.Option(5008),
        timeout: int = typer.Option(60),
        config: str = typer.Option("config.yaml"),
):
    # 加载配置文件
    settings.load_yaml(config)
    # 加载插件
    runner.load_plugins(settings)
    # 启动服务
    server_requests.start_server(ip=host, port=port, timeout=timeout)


if __name__ == '__main__':
    sys.exit(typer.run(main))
