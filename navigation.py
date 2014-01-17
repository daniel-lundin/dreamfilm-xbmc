import dreamfilm


class Navigation(object):

    def __init__(self, xbmc, xbmcplugin, xbmcgui, argv):
        self.xbmc = xbmc
        self.xbmcplugin = xbmcplugin
        self.xbmcgui = xbmcgui
        self.plugin_url = argv[0]
        self.handle = int(argv[1])
        try:
            self.params = dreamfilm.decode_parameters(argv[2])
        except:
            self.params = None

    def add_menu_item(self, caption, action):
        url = self.plugin_url + dreamfilm.encode_parameters({'action': action})
        self.xbmc.log('url: ' + url, self.xbmc.LOGERROR)

        list_item = self.xbmcgui.ListItem(caption)
        list_item.setInfo(type="Video", infoLabels={"Title": caption})
        return self.xbmcplugin.addDirectoryItem(handle=self.handle, url=url,
                                                listitem=list_item,
                                                isFolder=True)

    def add_movie_list_item(self, caption, url, thumb_url=None):
        params = {
            'action': 'play_movie' if 'movie' in url else 'list_seasons',
            'title': caption,
            'movie_url': url,
            'type': 'serie' if 'serie' in url else 'movie'
        }
        is_folder = params['type'] == 'serie'
        action_url = self.plugin_url + dreamfilm.encode_parameters(params)
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
        action_url = self.plugin_url + dreamfilm.encode_parameters(params)
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
        action_url = self.plugin_url + dreamfilm.encode_parameters(params)
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
        self.add_menu_item('HD 720p', 'hd')
        self.xbmcplugin.endOfDirectory(self.handle)

    def search(self):
        kb = self.xbmc.Keyboard('', 'Search', False)
        kb.doModal()
        if kb.isConfirmed():
            text = kb.getText()
            matches = dreamfilm.scrap_search(dreamfilm.search(text))
            for m in matches:
                self.add_movie_list_item(m[0], m[1])
            self.xbmcplugin.endOfDirectory(self.handle)

    def play_movie(self, title, movie_url):
        player_url = dreamfilm.scrap_movie(dreamfilm.fetch_html(movie_url))
        stream_urls = dreamfilm.scrap_player(dreamfilm.fetch_html(player_url))
        url = stream_urls[-1][1]
        self.xbmc.log('formats: ' + ", ".join([x[0] for x in stream_urls]),
                      self.xbmc.LOGNOTICE)
        li = self.xbmcgui.ListItem(label=title, path=url)
        li.setInfo(type='Video', infoLabels={"Title": title})
        self.xbmc.Player().play(item=url, listitem=li)

    def play_episode(self, title, season_number, episode_number, clip_id):
        iframe = dreamfilm.serie_iframe(clip_id)
        player_url = dreamfilm.scrap_movie(iframe)
        player_html = dreamfilm.fetch_html(player_url)
        stream_urls = dreamfilm.scrap_player(player_html)
        url = stream_urls[-1][1]
        name = '%s S%02dE%02d' % (title, season_number + 1, episode_number + 1)
        li = self.xbmcgui.ListItem(label=name, path=url)
        li.setInfo(type='Video', infoLabels={"Title": name})
        self.xbmc.Player().play(item=url, listitem=li)

    def list_seasons(self, title, url):
        html = dreamfilm.fetch_html(url)
        seasons = dreamfilm.scrap_serie(html)
        for idx, s in enumerate(seasons):
            self.add_season_list_item(title, idx, url)
        self.xbmcplugin.endOfDirectory(self.handle)

    def list_episodes(self, title, season_number, url):
        html = dreamfilm.fetch_html(url)
        seasons = dreamfilm.scrap_serie(html)
        for idx, e in enumerate(seasons[season_number]):
            self.add_episode_list_item(title, season_number, idx, e)
        self.xbmcplugin.endOfDirectory(self.handle)

    def list_top_movies(self):
        html = dreamfilm.top_movie_html()
        for name, url, thumb_url in dreamfilm.scrap_top_list(html):
            self.add_movie_list_item(name, url, thumb_url)
        self.xbmcplugin.endOfDirectory(self.handle)

    def list_top_series(self):
        html = dreamfilm.top_serie_html()
        for name, url, thumb_url in dreamfilm.scrap_top_list(html):
            self.add_movie_list_item(name, url, thumb_url)
        self.xbmcplugin.endOfDirectory(self.handle)

    def list_latest_movies(self):
        html = dreamfilm.latest_movie_html()
        for name, url, thumb_url in dreamfilm.scrap_top_list(html):
            self.add_movie_list_item(name, url, thumb_url)
        self.xbmcplugin.endOfDirectory(self.handle)

    def list_hd(self, page):
        html = dreamfilm.hd_html(page)
        for name, url, thumb_url in dreamfilm.scrap_hd(html):
            self.add_movie_list_item(name, url, thumb_url)
        #self.add_menu_item('Nex', 'hd')
        self.xbmcplugin.endOfDirectory(self.handle)

    def dispatch(self):
        if not self.params:
            return self.build_main_menu()
        if 'action' in self.params:
            action = self.params['action']
            if action == 'search':
                return self.search()
            if action == 'topmovies':
                return self.list_top_movies()
            if action == 'topseries':
                return self.list_top_series()
            if action == 'latestmovies':
                return self.list_latest_movies()
            if action == 'hd':
                return self.list_hd(self.params.get('page', 0))
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
