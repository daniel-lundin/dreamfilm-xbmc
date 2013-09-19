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

    def add_movie_list_item(self, caption, url):

        params = {
            'action': 'list_seasons',
            'title': caption.encode('utf-8'),
            'movie_url': url,
            'type': 'serie' if 'serie' in url else 'movie'
        }
        is_folder = params['type'] == 'serie'
        action_url = self.plugin_url + dreamfilm.encode_parameters(params)
        list_item = self.xbmcgui.ListItem(caption)
        list_item.setInfo(type='Video', infoLabels={'Title': caption})
        return self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                                url=action_url,
                                                listitem=list_item,
                                                isFolder=is_folder)

    def build_main_menu(self):
        self.add_menu_item('Search', 'search')
        self.add_menu_item('Top movies', 'topmovies')
        self.add_menu_item('Top series', 'topseries')
        self.xbmcplugin.endOfDirectory(self.handle)

    def search(self):
        kb = self.xbmc.Keyboard('', 'Search', False)
        kb.doModal()
        if kb.isConfirmed():
            text = kb.getText()
            matches = dreamfilm.scrap_search(dreamfilm.search(text).text)
            for m in matches:
                self.add_movie_list_item(m[0], m[1])
            self.xbmcplugin.endOfDirectory(self.handle)

    def play_movie(self, title, movie_url):
        player_url = dreamfilm.scrap_movie(dreamfilm.fetch_html(movie_url))
        stream_urls = dreamfilm.scrap_player(dreamfilm.fetch_html(player_url))
        url = stream_urls[-1][1]
        li = self.xbmcgui.ListItem(label=title, path=url)
        li.setInfo(type='Video', infoLabels={"Title": title})
        self.xbmc.Player().play(item=url, listitem=li)

    def list_seasons(self, title, url):
        html = dreamfilm.fetch_html(url)
        seasons = dreamfilm.scrap_serie(html)
        for idx, s in enumerate(seasons):
            self.add_menu_item('Season %d' % (idx + 1), 'list_episodes')
        self.xbmcplugin.endOfDirectory(self.handle)

    def dispatch(self):
        if not self.params:
            return self.build_main_menu()
        if 'action' in self.params:
            action = self.params['action']
            if action == 'search':
                return self.search()
            if action == 'play_movie':
                return self.play_movie(self.params['title'],
                                       self.params['movie_url'])
            if action == 'list_seasons':
                return self.list_seasons(self.params['title'],
                                         self.params['movie_url'])
