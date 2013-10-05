import sys
import requests
import urllib
from bs4 import BeautifulSoup


SEARCH_URL = 'http://dreamfilm.se/CMS/modules/search/ajax.php'
SERIE_URL = 'http://dreamfilm.se/CMS/modules/series/ajax.php'
TOP_SERIE_URL = 'http://dreamfilm.se/top/serier/'
TOP_MOVIE_URL = 'http://dreamfilm.se/top/filmer/'
HD_URL = 'http://dreamfilm.se/hd/720p/'


def search(query):
    r = requests.post(SEARCH_URL, data={'autoquery': query})
    return r


def serie_iframe(clip_id):
    r = requests.post(SERIE_URL, data={'action': 'showmovie', 'id': clip_id})
    return r.text


def top_movie_html():
    r = requests.get(TOP_MOVIE_URL)
    return r.text


def top_serie_html():
    r = requests.get(TOP_SERIE_URL)
    return r.text


def hd_html(page):
    r = requests.get(HD_URL + ('?page=%d' % page))
    return r.text


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


def scrap_top_list(html):
    soup = BeautifulSoup(html)
    movies = []
    for movie in soup.find_all("div", class_="galery"):
        a = movie.find('a')
        title = a.string.lstrip().rstrip()
        href = a.get('href')
        movies.append((title, href))
    return movies


def scrap_hd(html):
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
        matches.append((a_content, link))
        galery_idx = html.find('<div class="menu-galery">', galery_idx + 1)
    print matches
    return matches


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
