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


def _api_url(type='list', page=0, q=None,
              serie=None, id=None, hd=False, sort=None, climb=None):
    params = []
    params.append(('type','list'))
    params.append(('offset', page * ITEMS_PER_PAGE))
    params.append(('limit', 25))
    if q:
        params.append(('q', urllib.quote(q)))
    if serie:
        params.append(('serie', serie))
    if hd:
        params.append(('hd', '1'))
    if sort:
        params.append(('sort', sort))
    if climb:
        params.append(('climb', climb))
    if id:
        params.append(('id', id))
    return API_BASE_URL + "?" +  "&".join(("%s=%s" % (str(a), str(b)) for a,b in params))

def _paged_api_url(**kwargs):
    def wrapped(page):
        return _api_url(page=page, **kwargs)
    return wrapped

POPULAR_MOVIES_LISTING = 1
POPULAR_SERIES_LISTING = 2
LATEST_UPLOADED_LISTING = 3
BROWSE_MOVIES_LISTING = 4
BROWSE_SERIES_LISTING = 5
HD_ONLY_LISTING = 6

LISTING_NAMES = [
    (POPULAR_MOVIES_LISTING, "Popular movies"),
    (POPULAR_SERIES_LISTING, "Popular series"),
    (LATEST_UPLOADED_LISTING, "Latest uploaded"),
    (BROWSE_SERIES_LISTING, "Browse series"),
    (BROWSE_MOVIES_LISTING, "Browse movies"),
    (HD_ONLY_LISTING, "HD-only")
]

PAGED_LISTING_URLS = {
    POPULAR_MOVIES_LISTING: _paged_api_url(type='list', serie='0', sort='views', climb='0'),
    POPULAR_SERIES_LISTING: _paged_api_url(type='list', serie='1', sort='views', climb='0'),
    BROWSE_MOVIES_LISTING: _paged_api_url(type='list', serie='0', sort='alpha', climb='1'),
    BROWSE_SERIES_LISTING: _paged_api_url(type='list', serie='1', sort='alpha', climb='1'),
    LATEST_UPLOADED_LISTING: _paged_api_url(type='list', sort='time', climb='1'),
    HD_ONLY_LISTING: _paged_api_url(type='list', serie='0', hd=True, sort='views', climb='1'),
}

def listing(listing_type, page=0):
    url = PAGED_LISTING_URLS[listing_type](page)
    api_response = _api_request(url)
    return _apiresponse_to_items(api_response)


def search(q, page=0):
    url = _search_url(urllib.quote(q), page)
    api_response = _api_request(url)
    return _apiresponse_to_items(api_response)

def list_seasons(serie_id):
    url = API_BASE_URL + ('?type=episodes&id=%s' % serie_id)
    api_response  = _api_request(url)
    return _series_to_list(api_response, serie_id)


def streams_from_player_url(url):
    if 'mail.ru' in url:
        return resolvers.mailru_streams(url)

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
