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
        #print params
        #return '?' + urllib.urlencode(params)
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

    def add_movie_list_item(self, item):
        action = 'play_movie'
        if item.is_serie:
            action = 'list_seasons'
        if len(item.players) > 1:
            action = 'list_movie_parts'
        params = {
            'action': action,
            'id': item.id,
            'title': item.title,
            'players': item.players
        }
        is_folder = (action == 'play_movie')
        action_url = self.plugin_url + Navigation.encode_parameters(params)
        list_item = self.xbmcgui.ListItem(item.title)
        list_item.setThumbnailImage(item.poster_url)
        return self.xbmcplugin.addDirectoryItem(handle=self.handle,
                                                url=action_url,
                                                listitem=list_item,
                                                isFolder=is_folder)

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

    def build_main_menu(self):
        self.add_menu_item('Search', 'search')
        self.add_menu_item('Popular movies', 'popular_movies')
        self.add_menu_item('Popular series', 'popular_series')
        self.add_menu_item('Latest uploaded', 'latest_uploaded')
        self.add_menu_item('Browse series', 'series')
        self.add_menu_item('Browse movies', 'movies')
        #self.add_menu_item('HD 720p', 'hd')
        #self.add_menu_item('Genres', 'genres')
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
        players = json.loads(players_data)
        #if len(players) > 1:
        #    return self.list_movie_parts(title, players)

        streams = dreamfilm.streams_from_player_url(players[0]['url'])
        if len(streams) == 0:
            dialog = self.xbmcgui.Dialog()
            return dialog.ok("Error", "No stream found")

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
        print player_url
        streams = dreamfilm.streams_from_player_url(player_url)
        return self.select_stream(title, streams)

    def play_episode(self, title, season_number, episode_number, url):
        streams = dreamfilm.streams_from_player_url(url)
        if len(streams) == 0:
            dialog = self.xbmcgui.Dialog()
            return dialog.ok("Error", "No stream found")

        name = '%s S%sE%s' % (title, season_number, episode_number)
        return self.select_stream(name, streams)

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

    def list_popular_movies(self, page):
        items = dreamfilm.list_popular_movies(page)
        for item in items:
            self.add_movie_list_item(item)
        self.add_menu_item('Next', 'popular_movies', page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_popular_series(self, page):
        items = dreamfilm.list_popular_series(page)
        for item in items:
            self.add_movie_list_item(item)
        self.add_menu_item('Next', 'popular_series', page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_series(self, page):
        items = dreamfilm.list_series_alphanumeric(page)
        for item in items:
            self.add_movie_list_item(item)
        self.add_menu_item('Next', 'series', page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_movies(self, page):
        items = dreamfilm.list_movies_alphanumeric(page)
        for item in items:
            self.add_movie_list_item(item)
        self.add_menu_item('Next', 'movies', page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_latest_uploaded(self, page):
        items = dreamfilm.list_latest_added(page)
        for item in items:
            self.add_movie_list_item(item)
        self.add_menu_item('Next', 'latest_uploaded', page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    def list_hd(self, page):
        items = dreamfilm.list_hd_movies(page)
        for item in items:
            self.add_movie_list_item(item)
        self.add_menu_item('Next', 'hd', page=page + 1)
        return self.xbmcplugin.endOfDirectory(self.handle)

    #def list_genres(self, page):
    #    for name, url in self.dreamfilm.list_genres():
    #        self.add_genre_list_item(name, url)
    #    return self.xbmcplugin.endOfDirectory(self.handle)

    #def list_genre(self, genre_url, page):
    #    more_pages, matches = self.dreamfilm.list_genre(genre_url, page)
    #    for name, url, thumb_url in matches:
    #        self.add_movie_list_item(name, url, thumb_url)
    #    if more_pages:
    #        self.add_genre_list_item('Next', genre_url, page=page + 1)
    #    return self.xbmcplugin.endOfDirectory(self.handle)

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

            if action == 'popular_movies':
                return self.list_popular_movies(page)
            if action == 'popular_series':
                return self.list_popular_series(page)
            if action == 'latest_uploaded':
                return self.list_latest_uploaded(page)
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
            if action == 'play_episode':
                return self.play_episode(self.params['title'],
                                         int(self.params['season_number']),
                                         int(self.params['episode_number']),
                                         self.params['url'])
            if action == 'play_movie_part':
                return self.play_movie_part(self.params['title'],
                                            self.params['url'])
