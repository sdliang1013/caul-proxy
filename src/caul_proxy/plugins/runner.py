from typing import List

import urllib3.util

from caul_proxy.config import Config, Domain, Uri
from caul_proxy.plugins import NS_RW_URI, CACHE_RW_URI, CACHE_RW_DOMAIN, rewriter


def rewrite_domain(url_parts: urllib3.util.Url) -> str:
    """
    重写domain
    :param url_parts:
    :return:
    """
    for rw_domain in CACHE_RW_DOMAIN:
        if rw_domain.match(url_parts):
            return rw_domain.rewrite(url_parts)
    return f'{url_parts.scheme}://{url_parts.host}:{url_parts.port}'


def rewrite_uri(url_parts: urllib3.util.Url) -> str:
    """
    重写uri
    :param url_parts:
    :return:
    """
    for rw_uri in CACHE_RW_URI:
        if rw_uri.match(url_parts):
            return rw_uri.rewrite(url_parts)
    return url_parts.request_uri


def load_plugins(settings: Config):
    # load class
    load_cls(settings.plugin_dir)
    # init domain rewriter
    init_domain_rewriter(settings.domains)
    # init uri rewriter
    init_uri_rewriter(settings.uris)


def load_cls(plugin_dir: str):
    """
    加载rewriter类
    :param plugin_dir:
    :return:
    """
    # rewriter
    NS_RW_URI.update(
        RegexRewriter=rewriter.RegexRewriter,
        YhopRewriter=rewriter.YhopRewriter,
    )
    # todo load from plugin_dir/rewriter


def init_domain_rewriter(rw_list: List[Domain]):
    """
    初始化DomainRewriter对象
    :param rw_list:
    :return:
    """
    CACHE_RW_DOMAIN.clear()
    for rw in rw_list:
        CACHE_RW_DOMAIN.append(rewriter.DomainRewriter(pattern=rw.pattern, replace=rw.replace, port=rw.port))


def init_uri_rewriter(rw_list: List[Uri]):
    """
    初始化URIRewriter对象
    :param rw_list:
    :return:
    """
    CACHE_RW_URI.clear()
    for rw in rw_list:
        rwr_cls = NS_RW_URI.get(rw.rewriter, None)
        if not rwr_cls:
            raise ModuleNotFoundError(f'Could Not Find Rewriter: {rw.rewriter}')
        CACHE_RW_URI.append(rwr_cls(pattern=rw.pattern, replace=rw.replace, by_url=rw.full))
