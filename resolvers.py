import urllib
import urllib2
import json
import HTMLParser
import re


def vk_streams(html):
    """ Finds streams for vk.com player """
    start = html.index('<embed')
    end = html.index('>', start + 1)
    embed_tag = html[start:end]
    fv_idx = embed_tag.index('flashvars')
    flashvars = embed_tag[fv_idx + 10:-1]

    params = flashvars.split('&amp;')
    formats = []
    for param in params:
        parts = param.split('=')
        key = parts[0]
        value = parts[1]
        if key.startswith('url'):
            if '?' in value:
                value = value[0:value.find('?')]
            formats.append((key, value))
    return formats

def google_streams(html):
    """ Finds streams for docs.google.com player """
    FLASHVARS_START = 'flashVars":{'
    start = html.find(FLASHVARS_START) + len(FLASHVARS_START)
    end = html.find('}', start)

    flashvars = html[start:end]

    d = flashvars.decode('unicode-escape')
    decoded = urllib2.unquote(urllib2.unquote(d))

    urls = [l for l in decoded.split('url=') if 'mp4' in l and l.startswith('https')]
    streams = []
    for u in urls:
        q = 'quality='
        quality = u[u.find(q) + len(q): u.find(',', u.find(q))]
        streams.append((quality, u[:-1]))

    return streams


def leanback_streams(html):
    SOURCE_START = "source src=\""
    start = html.find(SOURCE_START) + len(SOURCE_START)
    end = html.find('"', start + 1)
    return [('', html[start:end])]


def mailru_streams(url):
    req = urllib2.Request(url)

    resp = urllib2.urlopen(req)
    html = resp.read()
    cookie_string = resp.headers.getheader('Set-Cookie').split(';')[0]

    print resp.headers.getheader('Set-Cookie')
    headers = {
        'Cookie': cookie_string
    }

    metadata_url_start = html.find('metadataUrl') + len('metadataUrl":"')
    metadata_url_end = html.find('"', metadata_url_start)
    metadata_url = html[metadata_url_start:metadata_url_end]

    metadata_response =  urllib2.urlopen(metadata_url)
    metadata = json.loads(metadata_response.read()) 

    # XBMC player needs cookies to play these
    xbmc_cookies = '|Cookie=' + urllib.quote(cookie_string)
    streams = [(v['key'], v['url'] + xbmc_cookies) for v in metadata['videos']]

    return streams


def vkpass_streams(html):
    identifier = "vsource=[{file:"
    vsource_start = html.index(identifier) + len(identifier) + 1
    vsource_end = html.index("\"", vsource_start + 1)

    return [('stream', html[vsource_start : vsource_end])]


def picasa_streams(url):
    m = re.search('picasaweb.google.com/(?P<user>[^/]+)/(?P<album>[^?]+)\?authkey=(?P<authkey>[^#]+)#?(?P<photoid>[^?]+)?', url)
    json_url = 'https://picasaweb.google.com/data/entry/base'
    json_url += '/user/' + m.group('user')
    json_url += '/album/' + m.group('album')
    json_url += '/photoid/' + m.group('photoid')
    json_url += '?alt=json'
    json_url += '&authkey=' + m.group('authkey')

    response = urllib2.urlopen(json_url)
    data = json.load(response)
    response.close()

    sources = []
    for l in data['entry']['media$group']['media$content']:
        if l["type"].startswith("video"):
            name = "{height}p".format(height=l["height"])
            link = l["url"]
            item = (name, link)
            sources.append(item)

    return sources


if __name__ == '__main__':
    #print mailru_streams('http://videoapi.my.mail.ru/videos/embed/mail/mr.whoare/video/_myvideo/505.html')
    #response = urllib2.urlopen("http://vkpass.com/token/bdrxwnlzfjpq/m123m/film/po-17915/watching.html?cap&c1_file=http://dreamvtt.com/srt/1/Poker.Night.2014.720p.BluRay.x264.YIFY.vtt&c1_label=English")
    #html = response.read()
    #print vkpass_streams(html)
    #print okru_streams('http://www.ok.ru/video/30025452153')
    #url = 'https://picasaweb.google.com/111770605384240810365/GameOfThronesS04?authkey=Gv1sRgCPLtx-O2nPmYFw#6151744529773049170'
    url = 'https://picasaweb.google.com/105596503743456265443/Random?authkey=Gv1sRgCMaE9_Kn5b2L8QE'
    print(picasa_streams(url))
