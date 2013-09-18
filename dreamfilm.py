import sys
import requests
from bs4 import BeautifulSoup


SEARCH_URL = 'http://dreamfilm.se/CMS/modules/search/ajax.php'


def search(query):
    r = requests.post(SEARCH_URL, data={'autoquery': query})
    return r


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

    #return formats
    #soup = BeautifulSoup(html)
    #embed = soup.find('embed')
    #flashvars = embed.get('flashvars')
    #params = flashvars.split('&amp;')
    #formats = []
    #for param in params:
    #    key, value = param.split('=')
    #    if key.startswith('url'):
    #        formats.append((key, value))

    #return formats


if __name__ == '__main__':
    resp = search(sys.argv[1])
    print scrap_search(resp.text)
