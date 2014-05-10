import unittest
import mock

import dreamfilm
import resolvers
from mocks import Xbmc, Xbmcplugin, Xbmcgui
from navigation import Navigation


class ParseTests(unittest.TestCase):

    def test_search_parse(self):
        with open('fixtures/search.html') as f:
            html = f.read()
            more_pages, matches = dreamfilm.Dreamfilm()._scrap_search(html)
            self.assertFalse(more_pages)
            self.assertTrue(len(matches), 3)

    def test_movie_parse(self):
        with open('fixtures/movie.html') as f:
            html = f.read()
            url = dreamfilm.Dreamfilm()._scrap_movie(html)
            self.assertEqual(url[0], 'http://vk.com/video_ext.php?oid=180544485&id=163198922&hash=e88cf73c90e7a1e6&hd=1')

    def test_google_movie_parse(self):
        html = "\xef\xbb\xbf<iframe allowfullscreen='true' webkitallowfullscreen='true' mozallowfullscreen='true' src='https://docs.google.com/file/d/0B5Q8_I828Qbeam40RlRDNTVnWVk/preview' width='530' height='245' frameborder='0'></iframe>"
        url = dreamfilm.Dreamfilm()._scrap_movie(html)

    def test_player_parse(self):
        with open('fixtures/player.html') as f:
            html = f.read()
            formats = resolvers.vk_streams(html)
            self.assertEqual(len(formats), 2)

    def test_vk_resolver(self):
        with open('fixtures/vknew.html') as f:
            html = f.read()
            formats = resolvers.vk_streams(html)
            self.assertEqual(len(formats), 2)

    def test_leanback_player_parse(self):
        with open('fixtures/leanback_player.html') as f:
            html = f.read()
            formats = resolvers.leanback_streams(html)
            self.assertEqual(len(formats), 1)

    def test_leanback_twitvid_parse(self):
        with open('fixtures/leanback_twitvid.html') as f:
            html = f.read()
            formats = resolvers.leanback_streams(html)
            self.assertEqual(len(formats), 1)

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

    def test_serie_parse(self):
        with open('fixtures/serie.html') as f:
            html = f.read()
            seasons = dreamfilm.Dreamfilm()._scrap_serie(html)
            self.assertEqual(len(seasons), 5)

    def test_top_movies_parse(self):
        with open('fixtures/topmovies.html') as f:
            html = f.read()
            more_pages, movies = dreamfilm.Dreamfilm()._scrap_top_list(html)
            self.assertFalse(more_pages)
            self.assertEqual(len(movies), 50)

    def test_top_series_parse(self):
        with open('fixtures/topseries.html') as f:
            html = f.read()
            more_pages, movies = dreamfilm.Dreamfilm()._scrap_top_list(html)
            self.assertFalse(more_pages)
            self.assertEqual(len(movies), 50)

    def test_series_parse(self):
        df = dreamfilm.Dreamfilm()

        with open('fixtures/series.html') as f:
            df._series_html = mock.MagicMock(return_value=f.read())

        more_pages, movies = df.list_series(1)
        self.assertTrue(more_pages)
        self.assertEqual(len(movies), 16)

    def test_movies_parse(self):
        df = dreamfilm.Dreamfilm()

        with open('fixtures/movies.html') as f:
            df._movies_html = mock.MagicMock(return_value=f.read())

        more_pages, movies = df.list_movies(1)
        self.assertTrue(more_pages)
        self.assertEqual(len(movies), 16)



    def test_top_hd(self):
        with open('fixtures/tophd.html') as f:
            html = f.read()
            more_pages, movies = dreamfilm.Dreamfilm()._scrap_hd(html)
            self.assertTrue(more_pages)
            self.assertEqual(len(movies), 16)

    def test_list_genres(self):
        with open('fixtures/startpage.html') as f:
            html = f.read()
            genres = dreamfilm.Dreamfilm()._scrap_genres(html)
            self.assertEqual(len(genres), 23)

    def test_list_genre(self):
        with open('fixtures/genre_action.html') as f:
            html = f.read()
            more_pages, movies = dreamfilm.Dreamfilm()._scrap_top_list(html)
            self.assertTrue(more_pages)
            self.assertEqual(len(movies), 16)



class NavigationTests(unittest.TestCase):

    def test_main_menu(self):
        argv = ['plugin.video.dreamfilm', '1']
        xbmc = Xbmc()
        xbmcplugin = Xbmcplugin()
        xbmcgui = Xbmcgui()
        df = dreamfilm.Dreamfilm()
        navigation = Navigation(df, xbmc, xbmcplugin, xbmcgui, argv)
        navigation.dispatch()
        self.assertEqual(len(xbmcplugin.dir_items), 8)

    def test_search_dispatch(self):
        # Mock
        xbmc = Xbmc()
        xbmcplugin = Xbmcplugin()
        xbmcgui = Xbmcgui()
        xbmc.Keyboard.getText = mock.MagicMock(return_value='bad')
        df = dreamfilm.Dreamfilm()

        with open('fixtures/search.html') as f:
            df._search = mock.MagicMock(return_value=f.read())

        params = Navigation.encode_parameters({'action': 'search'})
        argv = ['plugin.video.dreamfilm', '1', params]
        navigation = Navigation(df, xbmc, xbmcplugin, xbmcgui, argv)
        navigation.dispatch()
        self.assertEqual(len(xbmcplugin.dir_items), 3)

    def test_list_top_series(self):
        url = 'plugin.video.dreamfilm'
        params = Navigation.encode_parameters({'action': 'topseries'})
        argv = [url, 1, params]
        xbmc = Xbmc()
        xbmcplugin = Xbmcplugin()
        xbmcgui = Xbmcgui()
        df = dreamfilm.Dreamfilm()
        with open('fixtures/topseries.html') as f:
            df._top_serie_html = mock.MagicMock(return_value=f.read())

        navigation = Navigation(df, xbmc, xbmcplugin, xbmcgui, argv)
        navigation.dispatch()

        self.assertEqual(len(xbmcplugin.dir_items), 50)

    def test_list_top_movies(self):
        url = 'plugin.video.dreamfilm'
        params = Navigation.encode_parameters({'action': 'topmovies'})
        argv = [url, 1, params]
        xbmc = Xbmc()
        xbmcplugin = Xbmcplugin()
        xbmcgui = Xbmcgui()
        df = dreamfilm.Dreamfilm()
        with open('fixtures/topmovies.html') as f:
            df._top_movie_html = mock.MagicMock(return_value=f.read())

        navigation = Navigation(df, xbmc, xbmcplugin, xbmcgui, argv)
        navigation.dispatch()

        self.assertEqual(len(xbmcplugin.dir_items), 50)

    def test_list_latest_movies(self):
        url = 'plugin.video.dreamfilm'
        params = Navigation.encode_parameters({'action': 'latestmovies'})
        argv = [url, 1, params]
        xbmc = Xbmc()
        xbmcplugin = Xbmcplugin()
        xbmcgui = Xbmcgui()
        df = dreamfilm.Dreamfilm()
        with open('fixtures/startpage.html') as f:
            df._latest_movie_html = mock.MagicMock(return_value=f.read())

        navigation = Navigation(df, xbmc, xbmcplugin, xbmcgui, argv)
        navigation.dispatch()

        self.assertEqual(len(xbmcplugin.dir_items), 12)


if __name__ == '__main__':
    unittest.main()
