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


def _okru_to_res(string):
    string = string.strip()
    resolution = string
    if string == 'full':
        resolution = '1080p'
    elif string == 'hd':
        resolution = '720p'
    elif string == 'sd':
        resolution = '480p'
    elif string == 'low':
        resolution = '360p'
    elif string == 'lowest':
        resolution = '240p'
    elif string == 'mobile':
        resolution = '144p'

    return resolution


def okru_streams(url):
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    id = re.search('\d+', url).group(0)
    json_url = 'http://ok.ru/dk?cmd=videoPlayerMetadata&mid=' + id

    req = urllib2.Request(json_url, headers=HEADERS)
    response = urllib2.urlopen(req)
    source = response.read()
    response.close()

    json_source = json.loads(source)

    sources = []
    for source in json_source['videos']:
        name = _okru_to_res(source['name'])
        link = '%s|User-Agent=%s&Accept=%s'
        link = link % (source['url'], HEADERS['User-Agent'], HEADERS['Accept'])
        item = (name, link)
        sources.append(item)

    return sources


def vkpass_streams(url):
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'http://www.dreamfilmhd.org/API/api.php'
    }

    req = urllib2.Request(url, headers=HEADERS)
    response = urllib2.urlopen(req)
    html = response.read()
    response.close()

    return _vkpass_streams_from_html(html)

def _vkpass_streams_from_html(html):
    identifier = "vsource=["
    vsource_start = html.index(identifier) + len(identifier) - 1
    vsource_end = html.index("]", vsource_start + 1) + 1

    file_start = html.find('file:', vsource_start)
    formats = []

    while file_start != -1 and file_start < vsource_end:
        quote_start = file_start + 6
        quote_end = html.find('"', quote_start + 1)
        url = html[quote_start : quote_end]

        label_start = html.find('label:', quote_end)
        quote_start = label_start + 7
        quote_end = html.find('"', quote_start + 1)
        label = html[quote_start : quote_end]

        formats.append((label, url))
        file_start = html.find('file:', quote_end)


    return formats


def picasa_streams(url):
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    source = response.read()
    response.close()

    result = re.search('{"content":(\[{"url":.*?\])', source)
    links = json.loads(result.groups(1)[0])

    sources = []
    for l in links:
        if l["type"].startswith("video"):
            name = "{height}p".format(height=l["height"])
            link = l["url"]
            item = (name, link)
            sources.append(item)

    return sources


if __name__ == '__main__':
    #print mailru_streams('http://videoapi.my.mail.ru/videos/embed/mail/mr.whoare/video/_myvideo/505.html')
    response = urllib2.urlopen("http://vkpass.com/token/bdrxwnlzfjpq/m123m/film/po-17915/watching.html?cap&c1_file=http://dreamvtt.com/srt/1/Poker.Night.2014.720p.BluRay.x264.YIFY.vtt&c1_label=English")
    html = response.read()
    print vkpass_streams(html)
    #print okru_streams('http://www.ok.ru/video/30025452153')
