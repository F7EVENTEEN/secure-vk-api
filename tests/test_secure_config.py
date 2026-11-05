import functools
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from vk_api import VkApi

ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = Path(os.environ.get('TEST_TMPDIR', ROOT))
KEY = b'0' * 32  # Synthetic test-only key.


class SecureConfigTests(unittest.TestCase):
    def setUp(self):
        try:
            from vk_api.secure_config import EncryptedConfig
        except ModuleNotFoundError:
            self.fail('EncryptedConfig is not implemented')
        self.Config = EncryptedConfig
        self.folder = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'state.enc'

    def config(self, key=KEY):
        return self.Config('synthetic-owner', filename=str(self.path), key=key)

    def save_cookie(self):
        config = self.config()
        config.cookies = [{'value': 'FAKE_COOKIE_Ж', 'domain': '.vk.ru'}]
        config.token = {'access_token': 'FAKE_TOKEN'}
        config.save()
        return config

    def test_roundtrip_and_confidentiality(self):
        self.save_cookie()
        data = self.path.read_bytes()
        self.assertNotIn(b'FAKE_COOKIE', data)
        self.assertNotIn(b'FAKE_TOKEN', data)
        restored = self.config()
        self.assertEqual(restored.cookies[0]['value'], 'FAKE_COOKIE_Ж')
        self.assertEqual(restored.token, {'access_token': 'FAKE_TOKEN'})

    def test_each_save_has_fresh_ciphertext(self):
        config = self.save_cookie()
        first = self.path.read_bytes()
        config.save()
        self.assertNotEqual(first, self.path.read_bytes())
        self.assertEqual(self.config().cookies[0]['value'], 'FAKE_COOKIE_Ж')

    def test_wrong_key_fails_closed(self):
        self.save_cookie()
        with self.assertRaises(ValueError):
            self.config(key=b'1' * 32)

    def test_tampered_ciphertext_fails_closed(self):
        self.save_cookie()
        data = bytearray(self.path.read_bytes())
        data[-1] ^= 1
        self.path.write_bytes(data)
        with self.assertRaises(ValueError):
            self.config()

    def test_plaintext_json_is_rejected(self):
        self.path.write_text('{"synthetic-owner": {"cookies": []}}', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.config()

    def test_truncated_envelope_is_rejected(self):
        self.path.write_bytes(b'SVK1short')
        with self.assertRaises(ValueError):
            self.config()

    def test_key_must_be_exactly_32_bytes(self):
        for key in (b'', b'x' * 16, b'x' * 31, 'x' * 32, None):
            with self.subTest(key_type=type(key).__name__, length=len(key) if key else 0):
                with self.assertRaises(ValueError):
                    self.config(key=key)

    def test_failed_atomic_replace_preserves_existing_file(self):
        config = self.save_cookie()
        before = self.path.read_bytes()
        config.cookies = [{'value': 'FAKE_NEW_COOKIE'}]
        with patch('vk_api.secure_config.os.replace', side_effect=OSError('synthetic failure')):
            with self.assertRaises(OSError):
                config.save()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])
        self.assertEqual(self.config().cookies[0]['value'], 'FAKE_COOKIE_Ж')

    def test_client_accepts_explicit_encrypted_config(self):
        client = VkApi(login='synthetic-owner', config_filename=str(self.path),
                       config=functools.partial(self.Config, key=KEY))
        client.storage.cookies = [{'value': 'FAKE_COOKIE'}]
        client.storage.save()
        self.assertEqual(self.config().cookies, [{'value': 'FAKE_COOKIE'}])
