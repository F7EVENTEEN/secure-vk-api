"""Synthetic 32-field fixtures matching the observed VK response structure."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import requests

from vk_api.audio import VkAudio
from vk_api.exceptions import AccessDenied
from vk_api.secure_transport import SafeSession


def row(audio_id=8, available=True, title='Песня &amp; закат'):
    result = [None] * 32
    result[:6] = [audio_id, 7, '' if not available else 'https://audio.vkuseraudio.ru/a.mp3?sig=FAKE', title, 'Artist', 123]
    result[13] = 'a/b/ownerhash/d/e/urlhash' if available else 'a/b//d/e/'
    result[14] = ''
    return result


def response(body):
    return SimpleNamespace(json=lambda: body, text='<!--' + json.dumps(body))


def page(rows, more=False):
    return response({'data': [{'list': rows, 'hasMore': int(more)}]})


def search_page(rows):
    return response({'payload': [0, [None, {'playlist': {'list': rows}, 'sectionId': 'section', 'nextFrom': 'next'}]]})


class LiveAudioContractTests(unittest.TestCase):
    def setUp(self):
        self.session = SafeSession()
        self.addCleanup(self.session.close)
        with patch.object(self.session, 'get', return_value=requests.Response()):
            self.audio = VkAudio.from_session(self.session, user_id=42)

    def metadata(self, **kwargs):
        method = getattr(self.audio, 'get_metadata_iter', None)
        self.assertIsNotNone(method, 'Metadata-only library enumeration is missing')
        return method(**kwargs)

    def test_metadata_includes_unavailable_rows_without_audio_reload(self):
        with patch.object(self.session, 'post', return_value=page([row(), row(9, False)])) as wire:
            tracks = list(self.metadata())
        self.assertEqual([(t['id'], t['available']) for t in tracks], [(8, True), (9, False)])
        self.assertEqual(tracks[0]['title'], 'Песня & закат')
        self.assertTrue(all('url' not in t for t in tracks))
        self.assertEqual([c.kwargs['data']['act'] for c in wire.call_args_list], ['load_section'])

    def test_metadata_pages_preserve_order_and_do_not_fetch_audio(self):
        with patch.object(self.session, 'post', side_effect=[page([row()], True), page([row(9)])]) as wire:
            tracks = list(self.metadata())
        self.assertEqual([t['id'] for t in tracks], [8, 9])
        self.assertEqual([c.kwargs['data']['offset'] for c in wire.call_args_list], [0, 2000])

    def test_empty_library_is_a_successful_complete_snapshot(self):
        with patch.object(self.session, 'post', return_value=page([])):
            self.assertEqual(list(self.metadata()), [])

    def test_repeated_page_is_rejected_instead_of_looping(self):
        with patch.object(self.session, 'post', side_effect=[page([row()], True), page([row()], True)]):
            with self.assertRaises(AccessDenied):
                list(self.metadata())

    def test_malformed_metadata_row_is_not_silently_dropped(self):
        with patch.object(self.session, 'post', return_value=page([[1]])):
            with self.assertRaises(AccessDenied):
                list(self.metadata())

    def test_unavailable_metadata_has_no_fabricated_playback_reference(self):
        with patch.object(self.session, 'post', return_value=page([row(9, False)])):
            list(self.metadata())
        with patch.object(self.session, 'get', side_effect=AssertionError('Obsolete HTML must not be fetched')):
            self.assertIsNone(self.audio.get_audio_by_id(7, 9))

    def test_search_then_resolve_uses_reference_without_obsolete_html(self):
        replies = [search_page([row()]), response({'data': [[row()]]}), response({'data': [[row()]]})]
        with patch.object(self.session, 'post', side_effect=replies), \
             patch.object(self.session, 'get', side_effect=AssertionError('Obsolete HTML must not be fetched')):
            list(self.audio.search('Песня', count=1))
            track = self.audio.get_audio_by_id(7, 8)
        self.assertEqual((track['owner_id'], track['id']), (7, 8))

    def test_cold_callback_researches_metadata_and_keeps_exact_identity(self):
        replies = [search_page([row(99), row()]), response({'data': [[row(99), row()]]}), response({'data': [[row()]]})]
        with patch.object(self.session, 'post', side_effect=replies), \
             patch.object(self.session, 'get', side_effect=AssertionError('Obsolete HTML must not be fetched')):
            track = self.audio.get_audio_by_id(7, 8, query='Artist Песня')
        self.assertEqual(track['id'], 8)

    def test_cold_callback_does_not_substitute_another_track(self):
        replies = [search_page([row(99)]), response({'data': [[row(99)]]}), search_page([])]
        with patch.object(self.session, 'post', side_effect=replies), \
             patch.object(self.session, 'get', side_effect=AssertionError('Obsolete HTML must not be fetched')):
            self.assertIsNone(self.audio.get_audio_by_id(7, 8, query='Artist Песня'))

    def test_new_unavailable_snapshot_invalidates_old_playback_reference(self):
        with patch.object(self.session, 'post', side_effect=[page([row()]), page([row(8, False)])]):
            list(self.metadata())
            list(self.metadata())
        with patch.object(self.session, 'post', side_effect=AssertionError('Unavailable track must not reload')):
            self.assertIsNone(self.audio.get_audio_by_id(7, 8))

    def test_expired_reference_researches_once_instead_of_false_unavailability(self):
        replies = [search_page([row()]), response({'data': [[row()]]}),
                   response({'data': []}), search_page([row()]), response({'data': [[row()]]})]
        with patch.object(self.session, 'post', side_effect=replies):
            list(self.audio.search('Песня', count=1))
            result = self.audio.get_audio_by_id(7, 8, query='Artist Песня')
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 8)

    def test_repeated_search_cursor_stops_instead_of_reloading_forever(self):
        replies = [search_page([row()]), response({'data': [[row()]]}),
                   search_page([row()]), response({'data': [[row()]]})]
        with patch.object(self.session, 'post', side_effect=replies):
            with self.assertRaises(AccessDenied):
                list(self.audio.search('Песня', count=100))

    def test_failed_metadata_snapshot_preserves_playback_references(self):
        with patch.object(self.session, 'post', return_value=page([row()])):
            list(self.metadata())
        with patch.object(self.session, 'post', return_value=page([row(8, False), [1]])):
            with self.assertRaises(AccessDenied):
                list(self.metadata())
        with patch.object(self.session, 'post', return_value=response({'data': [[row()]]})):
            self.assertEqual(self.audio.get_audio_by_id(7, 8)['id'], 8)

    def test_cancelled_metadata_iteration_does_not_commit_partial_caches(self):
        with patch.object(self.session, 'post', return_value=page([row()])):
            list(self.metadata())
        with patch.object(self.session, 'post', return_value=page([row(8, False), row(9)])):
            iterator = self.metadata()
            next(iterator)
            iterator.close()
        with patch.object(self.session, 'post', return_value=response({'data': [[row()]]})):
            self.assertEqual(self.audio.get_audio_by_id(7, 8)['id'], 8)

    def test_cold_lookup_has_page_budget_even_when_no_audio_is_yielded(self):
        counts = {'pages': 0}
        def wire(*args, **kwargs):
            if kwargs['data']['act'] == 'reload_audio':
                return response({'data': []})
            counts['pages'] += 1
            if counts['pages'] > 3:
                raise AssertionError('Cold lookup exceeded the page budget')
            body = {'payload': [0, [None, {'playlist': {'list': [row(99)]},
                     'sectionId': 'section', 'nextFrom': str(counts['pages'])}]]}
            return response(body)
        with patch.object(self.session, 'post', side_effect=wire):
            self.assertIsNone(self.audio.get_audio_by_id(7, 8, query='missing'))
        self.assertLessEqual(counts['pages'], 3)

    def test_cold_lookup_bounds_reload_requests_with_large_empty_batches(self):
        counts = {'reloads': 0}
        def wire(*args, **kwargs):
            if kwargs['data']['act'] != 'reload_audio':
                return search_page([row(i) for i in range(1000, 2000)])
            counts['reloads'] += 1
            if counts['reloads'] > 10:
                raise AssertionError('Cold lookup exceeded the examined-row budget')
            return response({'data': []})
        with patch.object(self.session, 'post', side_effect=wire), patch('vk_api.audio.time.sleep'):
            self.assertIsNone(self.audio.get_audio_by_id(7, 8, query='missing'))
        self.assertLessEqual(counts['reloads'], 10)

    def playlist_response(self, entries, cursor=None):
        return response({'payload': [0, [None, {'playlists': entries,
                         'sectionId': 'playlist-section', 'nextFrom': cursor}]]})

    def album(self, album_id=3):
        return {'ownerId': 7, 'id': album_id, 'title': 'Мой &amp; плейлист',
                'accessHash': 'FAKE_PLAYLIST_REF', 'authorName': 'Artist', 'listens': 5, 'list': []}

    def test_playlists_use_modern_json_without_obsolete_html_selectors(self):
        with patch.object(self.session, 'post', return_value=self.playlist_response([self.album()])), \
             patch.object(self.session, 'get', side_effect=AssertionError('Obsolete album HTML must not be fetched')):
            albums = list(self.audio.get_albums_iter())
        self.assertEqual([(x['owner_id'], x['id'], x['title']) for x in albums], [(7, 3, 'Мой & плейлист')])
        self.assertEqual(albums[0]['access_hash'], 'FAKE_PLAYLIST_REF')

    def test_playlists_follow_json_pagination_without_duplicate_cursor(self):
        replies = [self.playlist_response([self.album()], 'next-page'), self.playlist_response([self.album(4)])]
        with patch.object(self.session, 'post', side_effect=replies):
            self.assertEqual([x['id'] for x in self.audio.get_albums_iter()], [3, 4])

    def test_malformed_playlist_response_is_not_reported_as_empty_library(self):
        with patch.object(self.session, 'post', return_value=response({'payload': []})):
            with self.assertRaises(AccessDenied):
                list(self.audio.get_albums_iter())
