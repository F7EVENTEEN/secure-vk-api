"""VK-only HTTPS transport for the secure-vk-api fork (Apache-2.0).

This intentionally excludes audio CDN downloading, generic uploads and arbitrary
Long Poll hosts. Review those separately instead of adding a wildcard allowlist.
"""
import math
from urllib.parse import urlsplit

import requests

DEFAULT_TIMEOUT = (10, 30)


def _validate_timeout(timeout):
    values = timeout if isinstance(timeout, tuple) else (timeout,)
    if isinstance(timeout, tuple) and len(timeout) != 2:
        raise ValueError('A connect/read timeout pair is required')
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('Timeouts must be finite positive seconds')
        if not math.isfinite(value) or value <= 0:
            raise ValueError('Timeouts must be finite positive seconds')


def _validate_url(url):
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or '').lower()
        trusted = host in ('vk.ru', 'vk.com') or host.endswith(('.vk.ru', '.vk.com'))
        valid = (parsed.scheme == 'https' and trusted and
                 parsed.port in (None, 443) and parsed.username is None and
                 parsed.password is None)
    except (ValueError, TypeError):
        valid = False
    if not valid:
        # Never include a credential-bearing URL in this diagnostic.
        raise ValueError('Destination is outside the approved VK HTTPS boundary')


class SafeSession(requests.Session):
    def __init__(self):
        super().__init__()
        self.trust_env = False

    def request(self, method, url, **kwargs):
        kwargs.setdefault('timeout', DEFAULT_TIMEOUT)
        return super().request(method, url, **kwargs)

    def send(self, request, **kwargs):
        # Requests calls send() again for redirects; validate every hop here.
        _validate_url(request.url)
        kwargs.setdefault('timeout', DEFAULT_TIMEOUT)
        _validate_timeout(kwargs['timeout'])
        if kwargs.get('verify', self.verify) is not True:
            raise ValueError('TLS certificate verification cannot be disabled')
        if kwargs.get('proxies', self.proxies):
            raise ValueError('Proxy forwarding is disabled for account sessions')
        kwargs['verify'] = True
        kwargs['proxies'] = {}
        return super().send(request, **kwargs)
