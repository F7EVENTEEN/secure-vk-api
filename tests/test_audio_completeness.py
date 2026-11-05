import unittest
from unittest.mock import patch
import requests

from vk_api.audio import VkAudio
from vk_api.exceptions import AccessDenied
from vk_api.secure_transport import SafeSession


def audio_row(audio_id=8):
    row = [None] * 15
    row[0:6] = [audio_id, 7, 'https://audio.useraudio.net/a.mp3', 'Song', 'Artist', 123]
    row[13] = 'a/b/ownerhash/d/e/urlhash'
    row[14] = ''
    return row


class CompletenessTests(unittest.TestCase):
    def audio(self):
        session = SafeSession()
        self.addCleanup(session.close)
        with patch.object(session, 'get', return_value=requests.Response()):
            audio = VkAudio.from_session(session, user_id=42)
        return audio, session

    def responses(self, rows, batch):
        def response(payload):
            from types import SimpleNamespace
            return SimpleNamespace(json=lambda: payload)
        return [response({'data': [{'list': rows, 'hasMore': False}]}), response(batch)]

    def test_strict_snapshot_rejects_empty_reload_instead_of_succeeding_empty(self):
        audio, session = self.audio()
        with patch.object(session, 'post', side_effect=self.responses([audio_row()], {'data': []})):
            with self.assertRaises(AccessDenied):
                list(audio.get_iter(strict=True))

    def test_strict_snapshot_rejects_missing_track_from_batch(self):
        audio, session = self.audio()
        with patch.object(session, 'post', side_effect=self.responses(
                [audio_row(), audio_row(9)], {'data': [[audio_row()]]})):
            with self.assertRaises(AccessDenied):
                list(audio.get_iter(strict=True))

    def test_strict_snapshot_rejects_unresolvable_enumerated_identity(self):
        audio, session = self.audio()
        row = audio_row()
        row[13] = 'a/b//d/e/'
        with patch.object(session, 'post', side_effect=self.responses([row], {'data': []})):
            with self.assertRaises(AccessDenied):
                list(audio.get_iter(strict=True))

    def test_strict_complete_snapshot_returns_metadata(self):
        audio, session = self.audio()
        with patch.object(session, 'post', side_effect=self.responses([audio_row()], {'data': [[audio_row()]]})):
            tracks = list(audio.get_iter(strict=True))
        self.assertEqual([(t['owner_id'], t['id'], t['artist']) for t in tracks], [(7, 8, 'Artist')])
