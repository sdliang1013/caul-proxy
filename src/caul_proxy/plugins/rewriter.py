import re
from abc import abstractmethod

import urllib3


class Rewriter:

    def __init__(self, pattern: str = None, replace: str = None):
        self.pattern = pattern
        self.replace = replace
        if self.pattern:
            self.rex = re.compile(self.pattern)

    def match(self, url: urllib3.util.Url) -> bool:
        return self.rex.match(url.url) is not None

    @abstractmethod
    def rewrite(self, url: urllib3.util.Url) -> str:
        ...


class DomainRewriter(Rewriter):

    def __init__(self, pattern: str = None, replace: str = None, port: int = None):
        self.port = port
        super().__init__(pattern=pattern, replace=replace)

    def match(self, url: urllib3.util.Url) -> bool:
        return self.rex.match(url.host) is not None

    @abstractmethod
    def rewrite(self, url: urllib3.util.Url) -> str:
        host = self.replace or url.host
        port = self.port or url.port or (80 if url.scheme.lower() == 'http' else 443)
        res = self.rex.search(url.host)
        # named group
        g_name = res.groupdict()
        for n, v in g_name.items():
            host = host.replace(f'${n}', v)
        # index group
        g_len = len(res.groups())
        for i in range(g_len):
            host = host.replace(f'${i}', res.group(i + 1))
        return f'{url.scheme}://{host}:{port}'


class URIRewriter(Rewriter):

    def __init__(self, pattern: str = None, replace: str = None, by_url: bool = False):
        self.by_url = by_url
        super().__init__(pattern=pattern, replace=replace)

    def match(self, url: urllib3.util.Url) -> bool:
        return self.rex.match(url.url if self.by_url else url.request_uri) is not None

    @abstractmethod
    def rewrite(self, url: urllib3.util.Url) -> str:
        ...


class RegexRewriter(URIRewriter):
    """正则替换"""

    def rewrite(self, url: urllib3.util.Url) -> str:
        res = self.rex.search(url.url if self.by_url else url.request_uri)
        g_len = len(res.groups())
        if not g_len:
            return url.request_uri
        path = self.replace or url.request_uri
        # named group
        g_name = res.groupdict()
        for n, v in g_name.items():
            path = path.replace(f'${n}', v)
        # index group
        for i in range(g_len):
            path = path.replace(f'${i}', res.group(i + 1))
        return path
