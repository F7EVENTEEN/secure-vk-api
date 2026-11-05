import io
import unittest

import requests
from requests.adapters import BaseAdapter
from vk_api import VkApi


class OfflineAdapter(BaseAdapter):
    """Only the external wire is substituted; Requests redirect logic is real."""
    def __init__(self, redirect=None):
        self.sent = []
        self.redirect = redirect

    def send(self, request, **kwargs):
        self.sent.append((request, kwargs))
        response = requests.Response()
        response.request = request
        response.url = request.url
        response.status_code = 302 if self.redirect else 200
        response._content = b'{}'
        response.raw = io.BytesIO(b'{}')
        if self.redirect:
            response.headers['Location'] = self.redirect
        return response

    def close(self):
        pass


class TransportTests(unittest.TestCase):
    def setUp(self):
        try:
            from vk_api.secure_transport import SafeSession
        except ModuleNotFoundError:
            self.fail('SafeSession is not implemented')
        self.SafeSession = SafeSession
        self.session = SafeSession()
        self.adapter = OfflineAdapter()
        self.session.mount('https://', self.adapter)
        self.session.mount('http://', self.adapter)
        self.addCleanup(self.session.close)

    def test_vk_https_request_has_bounded_timeout_and_verified_tls(self):
        response = self.session.get('https://api.vk.ru/method/users.get')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.adapter.sent[0][1]['timeout'], (10, 30))
        self.assertIs(self.adapter.sent[0][1]['verify'], True)

    def test_legacy_vk_domain_is_supported(self):
        self.assertEqual(self.session.get('https://vk.com/').status_code, 200)

    def test_untrusted_and_malformed_destinations_rejected_before_wire(self):
        urls = [
            'http://vk.ru/', 'https://example.org/', 'https://vk.ru.evil.example/',
            'https://evilvk.ru/', 'https://127.0.0.1/', 'https://[::1]/',
            'https://vk.ru:444/', 'https://user:secret@vk.ru/',
            'https://vk.ru./', 'https://vk.ru@evil.example/',
        ]
        for url in urls:
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.session.get(url)
        self.assertEqual(self.adapter.sent, [])

    def test_cross_origin_redirect_is_blocked_before_second_request(self):
        self.adapter.redirect = 'https://evil.example/collect'
        with self.assertRaises(ValueError):
            self.session.get('https://vk.ru/feed')
        self.assertEqual(len(self.adapter.sent), 1)

    def test_https_to_http_redirect_is_blocked(self):
        self.adapter.redirect = 'http://vk.ru/collect'
        with self.assertRaises(ValueError):
            self.session.get('https://vk.ru/feed')
        self.assertEqual(len(self.adapter.sent), 1)

    def test_direct_prepared_send_cannot_bypass_destination_policy(self):
        request = requests.Request('GET', 'https://evil.example/').prepare()
        with self.assertRaises(ValueError):
            self.session.send(request)
        self.assertEqual(self.adapter.sent, [])

    def test_tls_verification_cannot_be_disabled_by_call_or_session(self):
        with self.assertRaises(ValueError):
            self.session.get('https://vk.ru/', verify=False)
        self.session.verify = False
        with self.assertRaises(ValueError):
            self.session.get('https://vk.ru/')
        self.assertEqual(self.adapter.sent, [])

    def test_unbounded_and_invalid_timeouts_are_rejected(self):
        for timeout in (None, 0, -1, float('inf'), float('nan'), True,
                        (10, None), (0, 1), (1,), (1, 2, 3), '30', object()):
            with self.subTest(timeout_type=type(timeout).__name__), self.assertRaises(ValueError):
                self.session.get('https://vk.ru/', timeout=timeout)
        self.assertEqual(self.adapter.sent, [])

    def test_positive_explicit_timeout_is_respected(self):
        self.session.get('https://vk.ru/', timeout=(3, 4))
        self.assertEqual(self.adapter.sent[0][1]['timeout'], (3, 4))

    def test_environment_proxy_inheritance_is_disabled(self):
        self.assertFalse(self.session.trust_env)

    def test_explicit_proxy_cannot_forward_credentials(self):
        with self.assertRaises(ValueError):
            self.session.get('https://vk.ru/', proxies={'https': 'http://evil.example:80'})
        self.assertEqual(self.adapter.sent, [])

    def test_client_uses_safe_session_and_rejects_arbitrary_sessions(self):
        client = VkApi()
        self.addCleanup(client.http.close)
        self.assertIsInstance(client.http, self.SafeSession)
        with self.assertRaises(ValueError):
            VkApi(session=requests.Session())
        self.assertIs(VkApi(session=self.session).http, self.session)
