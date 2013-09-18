import unittest
import dreamfilm


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
            #url240=http://cs514312v4.vk.me/u180544485/videos/c540d52bf6.240.mp4

if __name__ == '__main__':
    unittest.main()
