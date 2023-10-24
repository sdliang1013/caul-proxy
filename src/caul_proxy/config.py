import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional, List

import yaml
from pydantic import BaseModel

# will print
logger = logging.getLogger()


class Domain(BaseModel):
    pattern: str
    replace: str
    port: Optional[int]


class Uri(BaseModel):
    rewriter: str
    pattern: Optional[str]
    replace: Optional[str]
    full: Optional[bool] = False


class Config(BaseModel):
    log_level: Optional[str] = 'INFO'
    plugin_dir: Optional[str] = ''
    allows: Optional[List[str]] = []
    denys: Optional[List[str]] = []
    domains: Optional[List[Domain]] = []
    uris: Optional[List[Uri]] = []

    def load_yaml(self, path: str):
        # 加载yaml
        with open(path, 'r', encoding='utf-8') as f:
            data: dict = yaml.load(f, Loader=yaml.FullLoader)
        if not data:
            return
        data_proxy: dict = data["caul"]["proxy"]
        conf = Config(**data_proxy)
        for key in data_proxy.keys():
            setattr(self, key, getattr(conf, key))
        # 设置日志参数
        self.init_logger()

    def init_logger(self):
        # logger format
        fmt = logging.Formatter(
            fmt="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # stdout logger
        handler_std = logging.StreamHandler(sys.stdout)
        handler_std.setFormatter(fmt)
        # Logger
        handler_file = RotatingFileHandler(
            filename='stdout.log',
            mode='a',
            maxBytes=10240000,
            backupCount=30, encoding='utf8')
        handler_file.setFormatter(fmt)
        logger.addHandler(handler_std)
        logger.addHandler(handler_file)
        logger.setLevel(self.log_level)


settings = Config()
