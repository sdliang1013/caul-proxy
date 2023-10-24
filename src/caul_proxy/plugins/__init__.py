from typing import Dict, Type, List

from caul_proxy.plugins.rewriter import URIRewriter, DomainRewriter

NS_RW_URI: Dict[str, Type[URIRewriter]] = {}
CACHE_RW_DOMAIN: List[DomainRewriter] = []
CACHE_RW_URI: List[URIRewriter] = []
