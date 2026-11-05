import unittest
from unittest.mock import patch
import requests

from vk_api.audio import VkAudio
from vk_api.secure_transport import SafeSession


class AudioSessionTests(unittest.TestCase):
    def test_existing_web_session_does_not_require_oauth_app_or_token(self):
        session = SafeSession()
        self.addCleanup(session.close)
        session.cookies.set('remixsid', 'FAKE_COOKIE', domain='.vk.ru')
        try:
            factory = VkAudio.from_session
        except AttributeError:
            self.fail('Web-session constructor is missing')
        with patch.object(session, 'get', return_value=requests.Response()):
            audio = factory(session, user_id=42)
        self.assertEqual(audio.user_id, 42)
        self.assertIs(audio._vk.http, session)
        self.assertFalse(audio.convert_m3u8_links)
        self.assertEqual(session.cookies.get('remixsid', domain='.vk.ru'), 'FAKE_COOKIE')

    def test_web_session_rejects_invalid_identity_and_unsafe_transport(self):
        factory = getattr(VkAudio, 'from_session', None)
        self.assertIsNotNone(factory, 'Web-session constructor is missing')
        with self.assertRaises(ValueError):
            factory(requests.Session(), user_id=42)
        session = SafeSession()
        self.addCleanup(session.close)
        for identity in (None, 0, -1, True, '42'):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                factory(session, user_id=identity)
