import urllib
import urllib2
import re

from cloudflare import dreamfilm_request
import resolvers


SEARCH_URL = 'http://dreamfilm.se/CMS/modules/search/ajax.php'
SERIE_URL = 'http://dreamfilm.se/CMS/modules/series/ajax.php'
TOP_SERIE_URL = 'http://dreamfilm.se/top/serier/'
TOP_MOVIE_URL = 'http://dreamfilm.se/top/filmer/'
LATEST_MOVIE_URL = 'http://dreamfilm.se/movies/'
HD_URL = 'http://dreamfilm.se/hd/720p/'
START_URL = 'http://dreamfilm.se/'


def _post(url, data):
    data = urllib.urlencode(data)
    return dreamfilm_request(url, data)
    content = urllib2.urlopen(url=url, data=data).read()
    return content


def fetch_html(url):
    return dreamfilm_request(url)
    response = urllib2.urlopen(url)
    return response.read()


def search(query):
    return _post(SEARCH_URL, {'autoquery': query})


def serie_iframe(clip_id):
    return _post(SERIE_URL, {'action': 'showmovie', 'id': clip_id})


def top_movie_html():
    return fetch_html(TOP_MOVIE_URL)


def top_serie_html():
    return fetch_html(TOP_SERIE_URL)


def latest_movie_html():
    return fetch_html(LATEST_MOVIE_URL)


def hd_html(page):
    return fetch_html(HD_URL + ('?page=%d' % page))


def start_html(page):
    return fetch_html(START_URL + ('?page=%d' % page))


def scrap_search(html):
    hits = html.split('</li>')
    matches = []
    for hit in hits[0:-1]:
        title = hit[hit.find("<h4>") + 4:hit.find("</h4>")]
        a_start = hit.find("<a")
        a_end = hit.find(">", a_start)
        href = hit[a_start + 9:a_end - 1]
        matches.append((title.lstrip().rstrip(), href))
    return matches


def scrap_movie(html):
    srcs = []
    iframe_idx = html.find("<iframe")
    while iframe_idx != -1:
        src = html[iframe_idx + 13:html.find(" ", iframe_idx + 14)]
        src = src[0:-1]
        if 'vk.com' in src:
            srcs.append(src)
        if 'docs.google.com' in src:
            srcs.append(src)
        iframe_idx = html.find("<iframe", iframe_idx + 1)
    return srcs


def scrap_top_list(html):
    items = html.split('<footer>')[0].split("<div class=\"span3 galery")[1:]

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

        img_start = html.find("<img src", a_tag_idx)
        img_end = html.find(">", img_start)
        img_src = html[img_start + 10: img_end - 1]
        if 'http://' not in img_src:
            img_src = "http://dreamfilm.se/" + img_src

        matches.append((a_content, link, img_src))
        galery_idx = html.find('<div class="menu-galery">', galery_idx + 1)
    return matches


def scrap_serie(html):
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
            if a.find("class='showmovie") != -1:
                href_idx = a.find('href')
                clip_id = a[href_idx + 6: a.find('"', href_idx + 7)]
                seasons[idx].append(clip_id)
            curr_a = html.find('<a', curr_a + 1)

    return seasons

def scrap_genres(html):
    genres = []

    cat_start = html.find('<ul class="nav nav-list">')
    li_idx = html.find("<li class=''>", cat_start)
    while li_idx != -1:

        link_start = html.find("href='", li_idx) + 6
        link_end = html.find("'", link_start + 1)

        name_start = html.find(">", link_end + 1) + 1
        name_end = html.find("<", name_start + 1)
        genres.append((html[name_start:name_end], html[link_start:link_end]))

        li_idx = html.find("<li class=''>", li_idx + 1)

    return genres


def streams_from_player_url(url):
    html = fetch_html(url)
    if 'vk.com' in url:
        return resolvers.vk_streams(html)
    if 'docs.google.com' in url:
        return resolvers.google_streams(html)
    return []


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
    resp = search('bad')
    result = scrap_search(resp)
    print "result from searching bad ", result
    print scrap_top_list(top_movie_html())
