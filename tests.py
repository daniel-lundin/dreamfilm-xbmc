import os
import sys
curr_dir, _ = os.path.split(os.path.realpath(__file__))
sys.path.append(os.path.join(curr_dir, 'resources/lib'))

import unittest
import dreamfilm
from mocks import xbmc, xbmcplugin, xbmcgui
from navigation import Navigation


class ParseTests(unittest.TestCase):

    def test_search_parse(self):
        with open('fixtures/search.html') as f:
            html = f.read()
            matches = dreamfilm.scrap_search(html)
            self.assertTrue(len(matches), 4)

    def test_movie_parse(self):
        with open('fixtures/movie.html') as f:
            html = f.read()
            url = dreamfilm.scrap_movie(html)
            self.assertEqual(url, 'http://vk.com/video_ext.php?oid=180544485&id=163198922&hash=e88cf73c90e7a1e6&hd=1')

    def test_player_parse(self):
        with open('fixtures/player.html') as f:
            html = f.read()
            formats = dreamfilm.scrap_player(html)
            self.assertEqual(len(formats), 2)

    def test_serie_parse(self):
        with open('fixtures/serie.html') as f:
            html = f.read()
            seasons = dreamfilm.scrap_serie(html)
            self.assertEqual(len(seasons), 5)


class NavigationTest(unittest.TestCase):

    def test_main_menu(self):
        argv = ['plugin.video.dreamfilm', '1']
        navigation = Navigation(xbmc, xbmcplugin, xbmcgui, argv)
        navigation.dispatch()
        self.assertEqual(len(xbmcplugin.dir_items), 3)

    def test_search_dispatch(self):
        params = dreamfilm.encode_parameters({'action': 'search'})
        argv = ['plugin.video.dreamfilm', '1', params]
        navigation = Navigation(xbmc, xbmcplugin, xbmcgui, argv)
        navigation.dispatch()
        self.assertEqual(len(xbmcplugin.dir_items), 8)


if __name__ == '__main__':
    unittest.main()
