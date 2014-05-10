# -*- coding: utf-8 -*-
import urllib
import urllib2
import re

from cloudflare import dreamfilm_request
import resolvers


SEARCH_URL = 'http://dreamfilm.se/search/'
SERIE_URL = 'http://dreamfilm.se/CMS/modules/series/ajax.php'
TOP_SERIE_URL = 'http://dreamfilm.se/top/serier/'
SERIES_URL = 'http://dreamfilm.se/series/'
MOVIES_URL = 'http://dreamfilm.se/movies/'
TOP_MOVIE_URL = 'http://dreamfilm.se/top/filmer/'
LATEST_MOVIE_URL = 'http://dreamfilm.se/movies/'
HD_URL = 'http://dreamfilm.se/hd/720p/'
START_URL = 'http://dreamfilm.se/'


class Dreamfilm(object):
    def search(self, text, page):
        return self._scrap_search(self._search(text, page))

    def list_top_movies(self):
        html = self._top_movie_html()
        return self._scrap_top_list(html)

    def list_top_series(self):
        html = self._top_serie_html()
        return self._scrap_top_list(html)

    def list_series(self, page):
        html = self._series_html(page)
        return self._scrap_top_list(html)

    def list_latest_movies(self, page):
        html = self._latest_movie_html(page)
        return self._scrap_top_list(html)

    def list_movies(self, page):
        html = self._movies_html(page)
        return self._scrap_top_list(html)

    def list_hd(self, page):
        html = self._hd_html(page)
        return self._scrap_hd(html)

    def list_seasons(self, serie_url):
        html = self._fetch_html(serie_url)
        return self._scrap_serie(html)

    def list_episodes(self, serie_url):
        html = self._fetch_html(serie_url)
        return self._scrap_serie(html)

    def list_genres(self):
        html = self._start_html(page=0)
        return self._scrap_genres(html)

    def list_genre(self, genre_url, page):
        html = self._fetch_html(genre_url, page=page)
        return self._scrap_top_list(html)

    def streams_from_clip_id(self, clip_id):
        html = self._serie_iframe(clip_id)
        if 'iframe' in html:
            player_urls = self._scrap_movie(html)
            if len(player_urls) == 0:
                return []
            return self.streams_from_player_url(player_urls[0])
        elif 'leanback-player-video' in html:
            return resolvers.leanback_streams(html)
        elif 'leanback-player-flash-fallback' in html:
            return resolvers.leanback_streams(html)


    def streams_from_player_url(self, url):
        html = self._fetch_html(url)
        if 'vk.com' in url:
            return resolvers.vk_streams(html)
        if 'docs.google.com' in url:
            return resolvers.google_streams(html)
        if 'dreamfilm.se' in url:
            return resolvers.leanback_streams(html)
        return []

    def movie_player_urls(self, movie_url):
        html = self._fetch_html(movie_url)
        if 'leanback-player-video' in html:
            return [movie_url]
        return self._scrap_movie(html)

    def _post(self, url, data):
        data = urllib.urlencode(data)
        return dreamfilm_request(url, data)
        content = urllib2.urlopen(url=url, data=data).read()
        return content

    def _fetch_html(self, url, page=None):
        if page:
            url = url + ('?page=%d' % page)
        return dreamfilm_request(url)
        response = urllib2.urlopen(url)
        return response.read()

    def _search(self, query, page):
        return self._fetch_html(SEARCH_URL + '?' +
                                urllib.urlencode({'q': query,
                                                  'page': page}))

    def _serie_iframe(self, clip_id):
        return self._post(SERIE_URL, {'action': 'showmovie', 'id': clip_id})

    def _top_movie_html(self):
        return self._fetch_html(TOP_MOVIE_URL)

    def _top_serie_html(self):
        return self._fetch_html(TOP_SERIE_URL)

    def _series_html(self, page):
        return self._fetch_html(SERIES_URL + ('?page=%d' % page))

    def _movies_html(self, page):
        return self._fetch_html(MOVIES_URL + ('?page=%d' % page))

    def _latest_movie_html(self, page):
        return self._fetch_html(LATEST_MOVIE_URL + ('?page=%d' % page))

    def _hd_html(self, page):
        return self._fetch_html(HD_URL + ('?page=%d' % page))

    def _start_html(self, page):
        return self._fetch_html(START_URL + ('?page=%d' % page))

    def _scrap_search(self, html):
        more_pages = html.find("class='pages'") > -1 and \
            html.find("disabled'>Nästa") == -1
        html = re.findall('<h3>(.+?)<footer>', html, re.DOTALL)[0]
        urls = re.findall('<a href="(.+?)".+?<li>', html, re.DOTALL)
        titles = [x.lstrip().rstrip() for x in
                  re.findall('<h4>(.+?)</h4>', html, re.DOTALL)]
        matches = zip(titles, urls)
        return more_pages, matches

    def _scrap_movie(self, html):
        srcs = []
        iframe_idx = html.find("<iframe")
        while iframe_idx != -1:
            m = re.search(r"src=['\"](.*?)['\"]", html[iframe_idx:])
            if m:
                src = m.groups(1)[0]
                if 'vk.com' in src:
                    srcs.append(src)
                if 'docs.google.com' in src:
                    srcs.append(src)
            iframe_idx = html.find("<iframe", iframe_idx + 1)
        return srcs

    def _scrap_top_list(self, html):
        more_pages = html.find("class='pages'") > -1 and \
            html.find("disabled'>Nästa") == -1
        items = html.split('<footer>')[0].split('<div class="span3 galery')[1:]

        movies = []
        for item in items:
            a_start = item.find("<a")
            href = item[a_start + 9:item.find("\"", a_start + 11)]
            content_start = item.find(">", a_start)
            content_end = item.find("</a>", a_start)
            title = item[content_start + 1:content_end]
            #img_start = item.find("<img src")
            img_start = item.find("<img")
            img_start = item.find('src', img_start)
            img_end = item.find(">", img_start)
            img_src = item[img_start + 5:img_end - 1]
            if 'http://' not in img_src:
                img_src = "http://dreamfilm.se/" + img_src
            movies.append((title.lstrip().rstrip(), href, img_src))
        return more_pages, movies

    def _scrap_hd(self, html):
        more_pages = html.find("class='pages'") > -1 and \
            html.find("disabled'>Nästa") == -1
        html = html[html.find('<body'):]
        galery_idx = html.find('<div class="menu-galery">')
        matches = []
        while galery_idx != -1:
            a_tag_idx = html.find('<a href="http://dreamfilm.se', galery_idx)
            link_end = html.find('"', a_tag_idx + 9)
            link = html[a_tag_idx + 9:link_end]

            a_tag_end = html.find('>', a_tag_idx)
            a_tag_close = html.find('</a>', a_tag_end)
            a_content = html[a_tag_end + 1:a_tag_close]
            a_content = a_content.lstrip().rstrip()

            img_start = html.find("<img src", a_tag_idx)
            img_end = html.find(">", img_start)
            img_src = html[img_start + 10: img_end - 1]
            if 'http://' not in img_src:
                img_src = "http://dreamfilm.se/" + img_src

            matches.append((a_content, link, img_src))
            galery_idx = html.find('<div class="menu-galery">', galery_idx + 1)
        return more_pages, matches

    def _scrap_serie(self, html):
        pattern = re.compile("href='#season_\d\d")

        seasons = []
        for idx, season in enumerate(pattern.findall(html)):
            seasons.append([])

            season_start = html.find("id='season_%02d'" % (idx + 1))
            season_end = html.find("id='season", season_start + 1)
            if season_end == -1:
                season_end = len(html)

            curr_a = html.find('<a', season_start)
            while curr_a != -1 and curr_a < season_end:
                curr_a_end = html.find('</a>', curr_a)
                a = html[curr_a:curr_a_end]
                "onclick=\"epselect('"
                if a.find("class='showmovie") != -1:
                    clip_id_marker = "onclick=\"epselect('"
                    clip_start = a.find(clip_id_marker) + len(clip_id_marker)
                    clip_id = a[clip_start: a.find("'", clip_start + 1)]
                    seasons[idx].append(clip_id)
                curr_a = html.find('<a', curr_a + 1)

        return seasons

    def _scrap_genres(self, html):
        genres = []

        cat_start = html.find('<ul class="nav nav-list">')
        li_idx = html.find("<li class=''>", cat_start)
        while li_idx != -1:

            link_start = html.find("href='", li_idx) + 6
            link_end = html.find("'", link_start + 1)

            name_start = html.find(">", link_end + 1) + 1
            name_end = html.find("<", name_start + 1)
            genres.append((html[name_start:name_end],
                           html[link_start:link_end]))

            li_idx = html.find("<li class=''>", li_idx + 1)

        return genres
