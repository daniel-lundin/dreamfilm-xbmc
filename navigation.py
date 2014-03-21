import urllib


class Navigation(object):

    def __init__(self, dreamfilm, xbmc, xbmcplugin, xbmcgui, argv):
        self.dreamfilm = dreamfilm
        self.xbmc = xbmc
        self.xbmcplugin = xbmcplugin
        self.xbmcgui = xbmcgui
        self.plugin_url = argv[0]
        self.handle = int(argv[1])
        try:
            self.params = Navigation.decode_parameters(argv[2])
        except:
            self.params = None

    @staticmethod
    def encode_parameters(params):
        return '?' + urllib.urlencode(params)

    @staticmethod
    def decode_parameters(parameters):
        query = parameters[1:]
        params = query.split('&')
        result = {}
        for p in params:
            key, value = p.split('=')
            key = urllib.unquote(key)
            value = urllib.unquote(value).decode('utf-8')
            result[key] = value
        return result

    def add_menu_item(self, caption, action, page=0, search=None):
        params = {'action': action, 'page': page}
        if search:
            params['search'] = search
        url = self.plugin_url + Navigation.encode_parameters(params)
        self.xbmc.log('url: ' + url, self.xbmc.LOGERROR)

        list_item = self.xbmcgui.ListItem(caption)
        list_item.setInfo(type="Video", infoLabels={
            "Title": caption,
        })
        return self.xbmcplugin.addDirectoryItem(handle=self.handle, url=url,
                                                listitem=list_item,
                                                isFolder=True)

    def add_genre_list_item(self, caption, url, page=None):
        params = {
            'action': 'list_genre',
            'title': caption,
            'genre_url': url,
        }
        if page:
            params['page'] = page
        is_folder = True
        action_url = self.plugin_url + Navigation.encode_parameters(params)
        list_item = self.xbmcgui.ListItem(caption)
        return self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                                url=action_url,
                                                listitem=list_item,
                                                isFolder=is_folder)

    def add_movie_list_item(self, caption, url, thumb_url=None):
        params = {
            'action': 'play_movie' if 'movie' in url else 'list_seasons',
            'title': caption,
            'movie_url': url,
            'type': 'serie' if 'serie' in url else 'movie'
        }
        is_folder = params['type'] == 'serie'
        action_url = self.plugin_url + Navigation.encode_parameters(params)
        list_item = self.xbmcgui.ListItem(caption)
        if thumb_url:
            list_item.setThumbnailImage(thumb_url)
        return self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                                url=action_url,
                                                listitem=list_item,
                                                isFolder=is_folder)

    def add_season_list_item(self, title, season_number, serie_url):
        params = {
            'action': 'list_episodes',
            'season_number': season_number,
            'title': title,
            'serie_url': serie_url
        }
        name = 'Season %d' % (season_number + 1)
        action_url = self.plugin_url + Navigation.encode_parameters(params)
        list_item = self.xbmcgui.ListItem(name)
        list_item.setInfo(type='Video', infoLabels={'Title': name})
        return self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                                url=action_url,
                                                listitem=list_item,
                                                isFolder=True)

    def add_episode_list_item(self, title, season_number,
                              episode_number, clip_id):
        params = {
            'action': 'play_episode',
            'title': title,
            'season_number': season_number,
            'episode_number': episode_number,
            'clip_id': clip_id
        }
        name = 'Episode %d' % (episode_number + 1)
        action_url = self.plugin_url + Navigation.encode_parameters(params)
        list_item = self.xbmcgui.ListItem(name)
        list_item.setInfo(type='Video', infoLabels={'Title': name})
        return self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                                url=action_url,
                                                listitem=list_item,
                                                isFolder=False)

    def build_main_menu(self):
        self.add_menu_item('Search', 'search')
        self.add_menu_item('Top movies', 'topmovies')
        self.add_menu_item('Top series', 'topseries')
        self.add_menu_item('Latest movies', 'latestmovies')
        self.add_menu_item('Browse series', 'series')
        self.add_menu_item('Browse movies', 'movies')
        self.add_menu_item('HD 720p', 'hd')
        self.add_menu_item('Genres', 'genres')
        return self.xbmcplugin.endOfDirectory(self.handle)

    def search(self, text, page):
        if not page:
            kb = self.xbmc.Keyboard('', 'Search', False)
            kb.doModal()
            if kb.isConfirmed():
                text = kb.getText()
            else:
                return
        more_pages, matches = self.dreamfilm.search(text, page)
        for m in matches:
            self.add_movie_list_item(m[0], m[1])
        if more_pages:
            self.add_menu_item('Next', 'search', page=page + 1, search=text)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def play_movie(self, title, movie_url):
        player_urls = self.dreamfilm.movie_player_urls(movie_url)
        if len(player_urls) > 1:
            return self.list_movie_parts(title, player_urls)

        if len(player_urls) == 0:
            dialog = self.xbmcgui.Dialog()
            return dialog.ok("Error", "No stream found")

        streams = self.dreamfilm.streams_from_player_url(player_urls[0])
        return self.select_stream(title, streams)

    def select_stream(self, title, streams):
        #stream_urls = self.dreamfilm.streams_from_player_url(player_url)

        # Ask user which stream to use
        url = self.quality_select_dialog(streams)
        if url is None:
            return
        return self.play_stream(title, url)

    def play_stream(self, title, stream):
        li = self.xbmcgui.ListItem(label=title, path=stream)
        li.setInfo(type='Video', infoLabels={"Title": title})
        return self.xbmc.Player().play(item=stream, listitem=li)

    def list_movie_parts(self, title, player_urls):
        for idx, url in enumerate(player_urls):
            params = {
                'action': 'play_movie_part',
                'title': 'title',
                'url': url
            }
            name = 'Part %d' % (idx + 1)
            action_url = self.plugin_url + Navigation.encode_parameters(params)
            list_item = self.xbmcgui.ListItem(name)
            list_item.setInfo(type='Video', infoLabels={'Title': name})
            self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                             url=action_url,
                                             listitem=list_item,
                                             isFolder=False)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def play_movie_part(self, title, player_url):
        streams = self.dreamfilm.streams_from_player_url(player_url)
        return self.select_stream(title, streams)

    def play_episode(self, title, season_number, episode_number, clip_id):
        print clip_id
        streams = self.dreamfilm.streams_from_clip_id(clip_id)
        if len(streams) == 0:
            dialog = self.xbmcgui.Dialog()
            return dialog.ok("Error", "No stream found")

        name = '%s S%02dE%02d' % (title, season_number + 1, episode_number + 1)
        return self.select_stream(name, streams)

    def list_seasons(self, title, url):
        seasons = self.dreamfilm.list_seasons(serie_url=url)
        for idx, s in enumerate(seasons):
            self.add_season_list_item(title, idx, url)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_episodes(self, title, season_number, url):
        seasons = self.dreamfilm.list_episodes(serie_url=url)
        for idx, e in enumerate(seasons[season_number]):
            self.add_episode_list_item(title, season_number, idx, e)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_top_movies(self, page):
        more_pages, matches = self.dreamfilm.list_top_movies()
        for name, url, thumb_url in matches:
            self.add_movie_list_item(name, url, thumb_url)
        if more_pages:
            self.add_menu_item('Next', 'topmovies', page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_top_series(self, page):
        more_pages, matches = self.dreamfilm.list_top_series()
        for name, url, thumb_url in matches:
            self.add_movie_list_item(name, url, thumb_url)
        if more_pages:
            self.add_menu_item('Next', 'topseries', page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_series(self, page):
        more_pages, matches = self.dreamfilm.list_series(page)
        for name, url, thumb_url in matches:
            self.add_movie_list_item(name, url, thumb_url)
        if more_pages:
            self.add_menu_item('Next', 'series', page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_movies(self, page):
        more_pages, matches = self.dreamfilm.list_movies(page)
        for name, url, thumb_url in matches:
            self.add_movie_list_item(name, url, thumb_url)
        if more_pages:
            self.add_menu_item('Next', 'movies', page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_latest_movies(self, page):
        more_pages, matches = self.dreamfilm.list_latest_movies(page)
        for name, url, thumb_url in matches:
            self.add_movie_list_item(name, url, thumb_url)
        if more_pages:
            self.add_menu_item('Next', 'latestmovies', page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_hd(self, page):
        more_pages, matches = self.dreamfilm.list_hd(page)
        for name, url, thumb_url in matches:
            self.add_movie_list_item(name, url, thumb_url)
        if more_pages:
            self.add_menu_item('Next', 'hd', page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_genres(self, page):
        for name, url in self.dreamfilm.list_genres():
            self.add_genre_list_item(name, url)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_genre(self, genre_url, page):
        more_pages, matches = self.dreamfilm.list_genre(genre_url, page)
        for name, url, thumb_url in matches:
            self.add_movie_list_item(name, url, thumb_url)
        if more_pages:
            self.add_genre_list_item('Next', genre_url, page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def quality_select_dialog(self, stream_urls):
        qualities = [s[0] for s in stream_urls]
        dialog = self.xbmcgui.Dialog()
        answer = 0
        if len(qualities) > 1:
            answer = dialog.select("Quality Select", qualities)
            if answer == -1:
                return
        url = stream_urls[answer][1]
        return url

    def dispatch(self):
        if not self.params:
            return self.build_main_menu()
        if 'action' in self.params:
            action = self.params['action']
            page = int(self.params.get('page', 0))
            if action == 'search':
                return self.search(self.params.get('search', None), page)
            if action == 'topmovies':
                return self.list_top_movies(page)
            if action == 'topseries':
                return self.list_top_series(page)
            if action == 'latestmovies':
                return self.list_latest_movies(page)
            if action == 'series':
                return self.list_series(page)
            if action == 'movies':
                return self.list_movies(page)
            if action == 'hd':
                return self.list_hd(page)
            if action == 'genres':
                return self.list_genres(page)
            if action == 'list_genre':
                return self.list_genre(self.params['genre_url'],
                                       page)
            if action == 'play_movie':
                return self.play_movie(self.params['title'],
                                       self.params['movie_url'])
            if action == 'list_seasons':
                return self.list_seasons(self.params['title'],
                                         self.params['movie_url'])
            if action == 'list_episodes':
                return self.list_episodes(self.params['title'],
                                          int(self.params['season_number']),
                                          self.params['serie_url'])
            if action == 'play_episode':
                return self.play_episode(self.params['title'],
                                         int(self.params['season_number']),
                                         int(self.params['episode_number']),
                                         self.params['clip_id'])
            if action == 'play_movie_part':
                return self.play_movie_part(self.params['title'],
                                            self.params['url'])
                return self.play_stream(self.params['title'],
                                        self.params['url'])
