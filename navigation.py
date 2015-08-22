import urllib
import dreamfilm
import json


class Navigation(object):

    def __init__(self, xbmc, xbmcplugin, xbmcgui, argv):
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
        quoted_params = []
        for key in params:
            value = unicode(params[key])
            if isinstance(params[key], dict):
                value = json.dumps(params[key])
            if isinstance(params[key], list):
                value = json.dumps(params[key])
            quoted_params.append((urllib.quote(key), urllib.quote(value.encode('unicode_escape'))))
        return "?" + "&".join(["%s=%s" % (a, b) for a, b in quoted_params])

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

    def add_listing_menu_item(self, caption, listing_type, page=0):
        params = {'action': 'listing', 'type': listing_type, 'page': page}
        url = self.plugin_url + Navigation.encode_parameters(params)
        self.xbmc.log('url: ' + url, self.xbmc.LOGERROR)

        list_item = self.xbmcgui.ListItem(caption)
        list_item.setInfo(type="Video", infoLabels={
            "Title": caption,
        })
        return self.xbmcplugin.addDirectoryItem(handle=self.handle, url=url,
                                                listitem=list_item,
                                                isFolder=True)

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

    def add_movie_list_item(self, item):
        action = 'play_movie'
        if item.is_serie:
            action = 'list_seasons'
        if item.players and len(item.players) > 1:
            action = 'list_movie_parts'
        params = {
            'action': action,
            'id': item.id,
            'title': item.title,
            'players': item.players
        }
        action_url = self.plugin_url + Navigation.encode_parameters(params)
        list_item = self.xbmcgui.ListItem(item.title)
        list_item.setThumbnailImage(item.poster_url)
        return self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                                url=action_url,
                                                listitem=list_item,
                                                isFolder=True)

    def add_season_list_item(self, title, serie_id, season_index, season_number):
        params = {
            'action': 'list_episodes',
            'serie_id': serie_id,
            'season_index': season_index,
            'title': title,
        }
        name = 'Season %s' % (season_number)
        action_url = self.plugin_url + Navigation.encode_parameters(params)
        list_item = self.xbmcgui.ListItem(name)
        list_item.setInfo(type='Video', infoLabels={'Title': name})
        return self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                                url=action_url,
                                                listitem=list_item,
                                                isFolder=True)

    def add_episode_list_item(self, title, episode):
        params = {
            'action': 'play_episode',
            'title': title,
            'season_number': episode.season,
            'episode_number': episode.episode,
            'url': episode.url
        }
        name = 'Episode %s' % (episode.episode,)
        action_url = self.plugin_url + Navigation.encode_parameters(params)
        list_item = self.xbmcgui.ListItem(name)
        list_item.setInfo(type='Video', infoLabels={'Title': name})
        return self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                                url=action_url,
                                                listitem=list_item,
                                                isFolder=False)

    def add_genre_item(self, genre, index, serie):
        params = {
            'action': 'list_genre',
            'genre_index': index,
            'serie': serie,
        }
        action_url = self.plugin_url + Navigation.encode_parameters(params)
        list_item = self.xbmcgui.ListItem(genre)
        list_item.setInfo(type='Video', infoLabels={'Title': genre})
        return self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                                url=action_url,
                                                listitem=list_item,
                                                isFolder=True)

    def build_main_menu(self):
        self.add_menu_item('Search', 'search')
        for listing_type, name in dreamfilm.LISTING_NAMES:
            self.add_listing_menu_item(name, listing_type, page=0)

        self.add_menu_item("Movies by genre", "list_movie_genres")
        self.add_menu_item("Series by genre", "list_serie_genres")

        return self.xbmcplugin.endOfDirectory(self.handle)

    def search(self, text, page):
        if not page:
            kb = self.xbmc.Keyboard('', 'Search', False)
            kb.doModal()
            if kb.isConfirmed():
                text = kb.getText()
            else:
                return
        items = dreamfilm.search(text)
        for item in items:
            self.add_movie_list_item(item)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def play_movie(self, title, players_data):
        try:
            players = json.loads(players_data)
            streams = dreamfilm.streams_from_player_url(players[0]['url'])
            subtitles = dreamfilm.subtitles_from_url(players[0]['url'])
            return self.select_stream(title, streams, subtitles)
        except Exception, e:
            print str(e)
            dialog = self.xbmcgui.Dialog()
            dialog.ok("Error", "Failed to open stream")

    def select_stream(self, title, streams, subtitles):

        # Ask user which stream to use
        url = self.quality_select_dialog(streams)
        if url is None:
            return
        return self.play_stream(title, url, subtitles)

    def play_stream(self, title, stream, subtitles):
        li = self.xbmcgui.ListItem(label=title, path=stream)
        li.setInfo(type='Video', infoLabels={"Title": title})
        li.setSubtitles(subtitles)

        return self.xbmc.Player().play(item=stream, listitem=li)

    def list_movie_parts(self, title, players_data):
        players = json.loads(players_data)
        for player in players:
            params = {
                'action': 'play_movie_part',
                'title': title,
                'url': player['url']
            }
            name = player['title']
            action_url = self.plugin_url + Navigation.encode_parameters(params)
            list_item = self.xbmcgui.ListItem(name)
            list_item.setInfo(type='Video', infoLabels={'Title': name})
            self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                             url=action_url,
                                             listitem=list_item,
                                             isFolder=False)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def play_movie_part(self, title, player_url):
        try:
            streams = dreamfilm.streams_from_player_url(player_url)
            subtitles = dreamfilm.subtitles_from_url(player_url)
            return self.select_stream(title, streams, subtitles)
        except Exception, e:
            dialog = self.xbmcgui.Dialog()
            print 'EEEE'
            print str(e)
            dialog.ok("Error", "Failed to open stream: %s" % player_url)

    def play_episode(self, title, season_number, episode_number, url):
        try:
            streams = dreamfilm.streams_from_player_url(url)

            subtitles = dreamfilm.subtitles_from_url(url)
            name = '%s S%sE%s' % (title, season_number, episode_number)
            return self.select_stream(name, streams, subtitles)
        except Exception, e:
            print 'EEEE'
            print str(e)
            dialog = self.xbmcgui.Dialog()
            return dialog.ok("Error", "Failed to open stream: %s" % url)


    def list_seasons(self, serie_id, title):
        seasons = dreamfilm.list_seasons(serie_id)
        for idx, season in enumerate(seasons):
            self.add_season_list_item(title, season.serie_id, idx, season.season_number)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_episodes(self, title, serie_id, season_index):
        seasons = dreamfilm.list_seasons(serie_id)
        for episode in seasons[season_index].episodes:
            self.add_episode_list_item(title, episode)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_movie_genres(self):
        for idx, genre in enumerate(dreamfilm.GENRES):
            self.add_genre_item(genre, idx, serie=0)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_serie_genres(self):
        for idx, genre in enumerate(dreamfilm.GENRES):
            self.add_genre_item(genre, idx, serie=1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_genre(self, serie, genre_index, page=0):
        genre = dreamfilm.GENRES[genre_index]
        items = dreamfilm.list_genre(genre, serie, page)
        for item in items:
            self.add_movie_list_item(item)

        # TODO: Refactor add_menu_item structure
        params = {
            'action': 'list_genre',
            'genre_index': genre_index,
            'serie': serie,
            'page': page + 1
        }
        name = 'Next'
        action_url = self.plugin_url + Navigation.encode_parameters(params)
        list_item = self.xbmcgui.ListItem(name)
        list_item.setInfo(type='Video', infoLabels={'Title': name})
        self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                         url=action_url,
                                         listitem=list_item,
                                         isFolder=True)

        return self.xbmcplugin.endOfDirectory(self.handle)

    def listing(self, type, page=0):
        items = dreamfilm.listing(type, page)
        for item in items:
            self.add_movie_list_item(item)
        self.add_listing_menu_item("Next", type, page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def quality_select_dialog(self, stream_urls):
        sorted_urls = sorted(stream_urls, key=lambda s: dreamfilm.natural_sort_key(s[0]))
        qualities = [s[0] for s in sorted_urls]
        dialog = self.xbmcgui.Dialog()
        answer = 0
        if len(qualities) > 1:
            answer = dialog.select("Quality Select", qualities)
            if answer == -1:
                return
        url = sorted_urls[answer][1]
        return url

    def dispatch(self):
        if not self.params:
            return self.build_main_menu()
        if 'action' in self.params:
            action = self.params['action']
            page = int(self.params.get('page', 0))
            if action == 'search':
                return self.search(self.params.get('search', None), page)

            if action == 'listing':
                return self.listing(int(self.params['type']), int(self.params['page']))
            if action == 'play_movie':
                return self.play_movie(self.params['title'], self.params['players'])
            if action == 'list_movie_parts':
                return self.list_movie_parts(self.params['title'], self.params['players'])
            if action == 'list_seasons':
                return self.list_seasons(self.params['id'],
                                         self.params['title'])
            if action == 'list_episodes':
                return self.list_episodes(self.params['title'],
                                          int(self.params['serie_id']),
                                          int(self.params['season_index']))
            if action == 'list_movie_genres':
                return self.list_movie_genres()
            if action == 'list_serie_genres':
                return self.list_serie_genres()
            if action == 'list_genre':
                return self.list_genre(int(self.params['serie']),
                                       int(self.params['genre_index']),
                                       int(self.params.get('page', 0)))
            if action == 'play_episode':
                return self.play_episode(self.params['title'],
                                         int(self.params['season_number']),
                                         int(self.params['episode_number']),
                                         self.params['url'])
            if action == 'play_movie_part':
                return self.play_movie_part(self.params['title'],
                                            self.params['url'])
