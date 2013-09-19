import sys
import requests
import urllib
from bs4 import BeautifulSoup


SEARCH_URL = 'http://dreamfilm.se/CMS/modules/search/ajax.php'


def search(query):
    r = requests.post(SEARCH_URL, data={'autoquery': query})
    return r


def fetch_html(url):
    r = requests.get(url)
    return r.text


def scrap_search(html):
    soup = BeautifulSoup(html)
    matches = []
    for tag in soup.find_all('a'):
        for hit in tag.find_all('h4'):
            matches.append((hit.string, tag.get('href')))
    return matches


def scrap_movie(html):
    soup = BeautifulSoup(html)
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src')
        if 'vk.com' in src:
            return src
    return None


def scrap_serie(html):
    soup = BeautifulSoup(html)
    seasons = []
    for a in soup.find_all('a'):
        href = a.get('href')
        if href and href.startswith('#season'):
            seasons.append([])

    for idx, season in enumerate(seasons):
        season_start = html.find("id='season_%02d'" % (idx + 1))
        season_end = html.find("id='season", season_start + 1)
        if season_end == -1:
            season_end = len(html)

        curr_a = html.find('<a', season_start)
        while curr_a != -1 and curr_a < season_end:
            curr_a_end = html.find('</a>', curr_a)
            a = html[curr_a:curr_a_end]
            if a.find("class='showmovie") != -1:
                href_idx = a.find('href')
                clip_id = a[href_idx + 6: a.find('"', href_idx + 7)]
                seasons[idx].append(clip_id)
            curr_a = html.find('<a', curr_a + 1)

    return seasons


def scrap_player(html):
    start = html.index('<embed')
    end = html.index('>', start + 1)
    embed_tag = html[start:end]
    fv_idx = embed_tag.index('flashvars')
    flashvars = embed_tag[fv_idx + 10:-1]

    params = flashvars.split('&amp;')
    formats = []
    for param in params:
        key, value = param.split('=')
        if key.startswith('url'):
            formats.append((key, value))
    return formats


def encode_parameters(params):
    return '?' + urllib.urlencode(params)


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

if __name__ == '__main__':
    resp = search(sys.argv[1])
    print scrap_search(resp.text)
