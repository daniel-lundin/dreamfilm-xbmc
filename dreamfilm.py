# -*- coding: utf-8 -*-
import urllib
import urllib2
import re
import json
from codecs import BOM_UTF8

import resolvers
from models import Item, Episode, Season

API_BASE_URL = 'http://dreamfilm.se/API/api.php'
ITEMS_PER_PAGE = 25

GENRES = ['Action', 'Anime', 'Animerat', 'Äventyr', 'Biografi', 'Dokumentär', 'Drama', 'Familj', 'Fantasy', 'Komedi', 'Krig', 'Historia', 'Kriminal', 'Musik', 'Musikal', 'Mysterium', 'Reality', 'Romantik', 'Sci-Fi', 'Skräck', 'Sport', 'Svenskt', 'Thriller', 'Western'] 


def search(q, page=0):
    url = _search_url(urllib.quote(q), page)
    print url
    api_response = _api_request(url)
    return _apiresponse_to_items(api_response)

def list_movies(page=0):
    offset = page * ITEMS_PER_PAGE
    url = API_BASE_URL + ('?type=list&serie=0&offset=0&limit=%d&sort=alpha&climb=1' % (offset, ITEMS_PER_PAGE))
    api_response  = _api_request(url)
    return _apiresponse_to_items(api_response)

def list_popular_movies(page=0):
    offset = page * ITEMS_PER_PAGE
    url = API_BASE_URL + ('?type=list&serie=0&offset=%d&limit=%d&sort=views&climb=0' % (offset, ITEMS_PER_PAGE))
    api_response  = _api_request(url)
    return _apiresponse_to_items(api_response)

def list_popular_series(page=0):
    offset = page * ITEMS_PER_PAGE
    url = API_BASE_URL + ('?type=list&serie=1&offset=%d&limit=%d&sort=views&climb=0' % (offset, ITEMS_PER_PAGE))
    api_response  = _api_request(url)
    return _apiresponse_to_items(api_response)


def list_series_alphanumeric(page=0):
    offset = page * ITEMS_PER_PAGE
    url = API_BASE_URL + ('?type=list&serie=1&offset=%d&limit=%d&sort=alpha&climb=1' % (offset, ITEMS_PER_PAGE))
    api_response  = _api_request(url)
    return _apiresponse_to_items(api_response)

def list_series_alphanumeric(page=0):
    offset = page * ITEMS_PER_PAGE
    url = API_BASE_URL + ('?type=list&serie=1&offset=%d&limit=%d&sort=alpha&climb=1' % (offset, ITEMS_PER_PAGE))
    api_response  = _api_request(url)
    return _apiresponse_to_items(api_response)

def list_movies_alphanumeric(page=0):
    offset = page * ITEMS_PER_PAGE
    url = API_BASE_URL + ('?type=list&serie=0&offset=%d&limit=%d&sort=alpha&climb=1' % (offset, ITEMS_PER_PAGE))
    api_response  = _api_request(url)
    return _apiresponse_to_items(api_response)

def list_latest_added(page=0):
    offset = page * ITEMS_PER_PAGE
    url = API_BASE_URL + ('?type=list&offset=%d&limit=%d&sort=time&climb=1' % (offset, ITEMS_PER_PAGE))
    api_response  = _api_request(url)
    return _apiresponse_to_items(api_response)


def list_hd_movies(page=0):
    offset = page * ITEMS_PER_PAGE
    url = API_BASE_URL + ('?type=list&serie=0&hd=1&offset=%d&limit=%d&sort=views&climb=1' % (offset, ITEMS_PER_PAGE))
    api_response  = _api_request(url)
    return _apiresponse_to_items(api_response)


def list_seasons(serie_id):
    url = API_BASE_URL + ('?type=episodes&id=%s' % serie_id)
    api_response  = _api_request(url)
    return _series_to_list(api_response, serie_id)


def streams_from_player_url(url):
    html = _fetch_html(url)
    if 'vk.com' in url:
        return resolvers.vk_streams(html)
    if 'docs.google.com' in url:
        return resolvers.google_streams(html)
    if 'dreamfilm.se' in url:
        return resolvers.leanback_streams(html)
    return []


def _search_url(q, page=0):
    offset = page * ITEMS_PER_PAGE
    return API_BASE_URL + ('?q=%s&type=list&offset=%d&limit=%d' % (q, offset, ITEMS_PER_PAGE))


def _series_to_list(json_data, serie_id):
    response = json.loads(_strip_bom(json_data))
    last_season = None
    seasons = []
    current_episodes = []

    for item in response['data']:
        episode = Episode(item['id'], item['season'], item['episode'], item['url'])
        if last_season and episode.season != last_season:
            seasons.append(_make_season(serie_id, current_episodes))
            current_episodes = []
        current_episodes.append(episode)
        last_season = episode.season
    seasons.append(_make_season(serie_id, current_episodes))
    return seasons


def _make_season(serie_id, episodes):
    return Season(serie_id, episodes[0].season, episodes)

def _api_request(url):
    response = urllib2.urlopen(url)
    return response.read()

def _apiresponse_to_items(json_data):
    response = json.loads(_strip_bom(json_data))
    items = []
    for entry in response['data']:
        item = Item(entry['id'], entry['title'],
                    entry['genres'], entry.get('player', None),
                    entry['type'] == "1", entry['poster'])
        items.append(item)
    return items

def _strip_bom(string, bom=BOM_UTF8):
    if string.startswith(bom):
        return string[len(bom):]
    else:
        return string

def _fetch_html(url):
    response = urllib2.urlopen(url)
    html = response.read()
    return html
