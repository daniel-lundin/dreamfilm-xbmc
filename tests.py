import unittest
import mock
import json

import dreamfilm
import resolvers
from mocks import Xbmc, Xbmcplugin, Xbmcgui
from mock import MagicMock
from navigation import Navigation


class ResolverTests(unittest.TestCase):

    def test_vk_resolver(self):
        with open('fixtures/vknew.html') as f:
            html = f.read()
            formats = resolvers.vk_streams(html)
            self.assertEqual(len(formats), 2)

class ParseTests(unittest.TestCase):

    def test_google_stream_resolver(self):
        with open('fixtures/google_player.html') as f:
            html = f.read()
            formats = resolvers.google_streams(html)
            self.assertEqual(len(formats), 3)

    def test_google_stream_serie_resolver(self):
        with open('fixtures/google_player_serie.html') as f:
            html = f.read()
            formats = resolvers.google_streams(html)
            self.assertEqual(len(formats), 2)

    def test_vk_pass_resolver(self):
        with open('fixtures/vkpass.html') as f:
            html = f.read()
            formats = resolvers._vkpass_streams_from_html(html)
            self.assertEqual(len(formats), 3)


class SubtitleTests(unittest.TestCase):

    def tearDown(self):
        actual = dreamfilm.subtitles_from_url(self.url)
        self.assertEqual(self.expected, actual)

    def test_empty_string_gives_no_subtitles(self):
        self.url = ''
        self.expected = []

    def test_single_subtitle(self):
        self.url = 'http://url.com?cap&c1_file=http://sub1.vtt&c1_label=Svenska'
        self.expected = ['http://sub1.vtt']

    def test_subtitle_with_high_number(self):
        self.url = 'http://url.com?cap&c123_file=http://sub1.vtt&c1_label=Svenska'
        self.expected = ['http://sub1.vtt']

    def test_multiple_subtitles(self):
        self.url = 'http://url.com&c1_file=http://sub1.vtt&c1_label=English&c2_file=http://sub2.vtt&c2_label=Svenska&c3_file=http://sub3.vtt&c3_label=Suomi'
        self.expected = ['http://sub1.vtt', 'http://sub2.vtt', 'http://sub3.vtt']

    def test_missing_http(self):
        self.url = 'http://url.com&c1_file=sub1.vtt&c1_label=English&c2_file=sub2.vtt&c2_label=Svenska&c3_file=sub3.vtt&c3_label=Suomi'
        self.expected = ['http://sub1.vtt', 'http://sub2.vtt', 'http://sub3.vtt']

    def test_leading_and_trailing_whitespace(self):
        self.url = 'http://url.com?cap&c1_file= http://sub.vtt  &c1_label=Dansk'
        self.expected = ['http://sub.vtt']

    def test_leading_whitespace_missing_http(self):
        self.url = 'http://url.com?cap&c1_file= sub.vtt&c1_label=Svenska'
        self.expected = ['http://sub.vtt']

    def test_url_containing_whitespaces(self):
        self.url = 'http://url.com?cap&c1_file= http://s u b.vtt  &c1_label=Dansk'
        self.expected = ['http://s u b.vtt']


class APITests(unittest.TestCase):

    def test_parse_apirespone(self):
        with open('fixtures/api_search.json') as f:
            apiresponse = f.read()
            bom_stripped = dreamfilm._strip_bom(apiresponse)
            items = dreamfilm._apiresponse_to_items(bom_stripped)
            self.assertEqual(len(items), 25)

    def test_parse_season_response(self):
        with open('fixtures/api_seasons.json') as f:
            api_resonse = f.read()
            seasons = dreamfilm._series_to_list(api_resonse, 123)
            self.assertEqual(len(seasons), 7)

    def test_api_url_generation(self):
        expected = 'http://www.dreamfilmhd.org/API/api.php?type=list&offset=0&limit=25&q=Bad%20santa&sort=alpha'
        url = dreamfilm._api_url(type='list', q="Bad santa", sort="alpha")
        self.assertEqual(expected, url)

    def test_paged_api_url_generation(self):
        pager = dreamfilm._paged_api_url(type='list', q="Bad santa", sort="alpha")
        page1 = 'http://www.dreamfilmhd.org/API/api.php?type=list&offset=25&limit=25&q=Bad%20santa&sort=alpha'
        page2 = 'http://www.dreamfilmhd.org/API/api.php?type=list&offset=50&limit=25&q=Bad%20santa&sort=alpha'
        self.assertEqual(pager(1), page1)
        self.assertEqual(pager(2), page2)


class QualitySelectTests(unittest.TestCase):

    def setUp(self):
        self.dialog = Xbmcgui.Dialog()
        self.dialog.select = MagicMock(name='select')
        xbmcgui = Xbmcgui()
        xbmcgui.Dialog = MagicMock(name='Dialog')
        xbmcgui.Dialog.return_value = self.dialog
        self.navigation = Navigation(None, None, xbmcgui, [None, 1])

    def tearDown(self):
        actual = self.navigation.quality_select_dialog(self.input)
        self.assertEqual(actual, self.expected)

        if self.dialog_arg:
            self.dialog.select.assert_called_once_with("Quality Select", self.dialog_arg)
        else:
            self.assertFalse(self.dialog.select.called, "Dialog called!")

    def test_only_one_input(self):
        self.input = [("240p", "url_240")]
        self.expected = "url_240"
        self.dialog_arg = None

    def test_select_first_url(self):
        self.input = [("360p", "url_360"), ('720p', 'url_720')]
        self.dialog_arg = ["360p", "720p"]
        self.dialog.select.return_value = 0
        self.expected = "url_360"

    def test_select_second_url(self):
        self.input = [("360p", "url_360"), ('720p', 'url_720')]
        self.dialog_arg = ["360p", "720p"]
        self.dialog.select.return_value = 1
        self.expected = "url_720"

    def test_unsorted_input(self):
        self.input = [("1080p", "url_1080"), ('720p', 'url_720')]
        self.dialog_arg = ["720p", "1080p"]
        self.dialog.select.return_value = 1
        self.expected = "url_1080"

    def test_select_leading_whitespace_url(self):
        self.input = [("360p", "url_360"), ('720p', ' url_720')]
        self.dialog_arg = ["360p", "720p"]
        self.dialog.select.return_value = 1
        self.expected = "url_720"


class SortTests(unittest.TestCase):

    def tearDown(self):
        actual = sorted(self.input, key=dreamfilm.natural_sort_key)
        self.assertEqual(self.expected, actual)

    def test_alphabetical(self):
        self.input = ['foo', 'bar', 'baz']
        self.expected = ['bar', 'baz', 'foo']

    def test_numbers(self):
        self.input = ['number_12', 'number_4', 'number_0']
        self.expected = ['number_0', 'number_4', 'number_12']

    def test_leading_numbers(self):
        self.input = ['1080p', '720p', '240p', '360p', '480p']
        self.expected = ['240p', '360p', '480p', '720p', '1080p']

    def test_mixed_leading_zeros(self):
        self.input = ['Season 02', 'Season 000010', 'Season 1']
        self.expected = ['Season 1', 'Season 02', 'Season 000010']

    def test_sorting_mixed_cases_preserves_order(self):
        self.input = ['b', 'B', 'A', 'a']
        self.expected = ['A', 'a', 'b', 'B']


if __name__ == '__main__':
    unittest.main()
