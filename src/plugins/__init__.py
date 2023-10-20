from typing import Dict, Type, List

from plugins.rewriter import URIRewriter, DomainRewriter

T_REWRITER_URI: Dict[str, Type[URIRewriter]] = {}
O_REWRITER_DOMAIN: List[DomainRewriter] = []
O_REWRITER_URI: List[URIRewriter] = []
