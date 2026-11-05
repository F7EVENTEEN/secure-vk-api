import contextlib
import io
import logging
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import jconfig
from vk_api import VkApi, VkUserPermissions
from vk_api.exceptions import AuthError, LoginRequired
from vk_api.utils import enable_debug_mode


ROOT = Path(__file__).resolve().parents[1]


class AuthSecurityTests(unittest.TestCase):
    def test_cookie_and_token_not_in_auth_logs(self):
        client = VkApi(login='FAKE_PHONE')
        client.http.cookies.set('remixsid', 'FAKE_COOKIE', domain='.vk.ru')
        client.token = {'access_token': 'FAKE_TOKEN'}
        with patch.object(client, 'check_sid', return_value=False), \
             patch.object(client, '_vk_login'), \
             patch.object(client, '_check_token', return_value=False), \
             patch.object(client, '_api_login'), \
             self.assertLogs('vk_api', level=logging.INFO) as logs:
            client._auth_cookies()
        joined = '\n'.join(logs.output)
        self.assertNotIn('FAKE_COOKIE', joined)
        self.assertNotIn('FAKE_TOKEN', joined)

    def test_default_storage_never_writes_session_to_disk(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            target = Path(folder) / 'session.json'
            client = VkApi(login='FAKE_PHONE', config_filename=str(target))
            client.storage.cookies = [{'value': 'FAKE_COOKIE'}]
            client.storage.save()
            self.assertFalse(target.exists())
            self.assertIsInstance(client.storage, jconfig.MemoryConfig)

    def test_default_scope_requests_only_audio(self):
        self.assertEqual(int(VkApi().scope), 8)

    def test_explicit_scope_remains_supported(self):
        self.assertEqual(VkApi(scope=VkUserPermissions.PHOTOS).scope, 4)

    def test_no_oauth_application_identity_is_borrowed(self):
        self.assertIsNone(VkApi().app_id)

    def test_missing_explicit_application_id_fails_before_network(self):
        client = VkApi()
        with self.assertRaisesRegex(AuthError, 'app_id'):
            client._api_login()

    def test_password_cleared_after_successful_auth(self):
        client = VkApi(login='FAKE_PHONE', password='FAKE_PASSWORD', app_id=123)
        with patch.object(client, '_auth_cookies'), self.assertLogs('vk_api', level='INFO') as logs:
            client.auth()
        self.assertIsNone(client.password)
        self.assertNotIn('FAKE_PHONE', '\n'.join(logs.output))

    def test_password_cleared_after_failed_auth(self):
        client = VkApi(login='FAKE_PHONE', password='FAKE_PASSWORD', app_id=123)
        with patch.object(client, '_auth_cookies', side_effect=AuthError('synthetic error')):
            with self.assertRaises(AuthError):
                client.auth()
        self.assertIsNone(client.password)

    def test_password_cleared_even_when_login_missing(self):
        client = VkApi(password='FAKE_PASSWORD')
        with self.assertRaises(LoginRequired):
            client.auth()
        self.assertIsNone(client.password)

    def test_http_debug_dump_is_disabled_without_output(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch('requests.get') as request:
            request.return_value.json.return_value = {'info': {'version': '11.10.1'}}
            with self.assertRaisesRegex(RuntimeError, 'disabled'):
                enable_debug_mode(VkApi(), print_content=True)
        self.assertEqual(output.getvalue(), '')
