import urllib
import urllib2
import json
import HTMLParser
import re
import binascii
import xbmc
import traceback

from vendor import packer


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


def vkpass_streams(url, recursive_call=False):
    xbmc.log('vkpass_streams: ' + str(url), xbmc.LOGDEBUG)
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#        'Referer': 'http://www.dreamfilmhd.org/API/api.php'
    }

    req = urllib2.Request(url, headers=HEADERS)
    response = urllib2.urlopen(req)
    html = response.read()
    response.close()

    return _vkpass_streams_from_html(html, recursive_call)

def _extract_packed_videourls(html):
    eval_start = html.find('eval(function(p,a,c,k,e')
    eval_end = html.find('</script>', eval_start)
    packed_script = html[eval_start : eval_end]
    unpacked_script = packer.unpack(packed_script)
    return _extract_source_tags(unpacked_script, single_quotes=False)

def _extract_source_tags(html, single_quotes=True):
    source_tags = re.findall(r'(<source.*?\/>)', html)
    if source_tags:
        streams = []
        for source_tag in source_tags:
            match = re.search(r"src='(.*?)'.*?label='(.*?)'", source_tag)
            if not match:
                match = re.search(r'src="(.*?)".*?label="(.*?)"', source_tag)
            if match:
                streams.append((match.group(2), match.group(1)))

        if len(streams) == 0:
            xbmc.log('_extract_source_tags: failed to extract streams', xbmc.LOGERROR)
            xbmc.log(traceback.format_exc(), xbmc.LOGERROR)
        return streams
    xbmc.log('_extract_source_tags: no source tags', xbmc.LOGERROR)
    xbmc.log(traceback.format_exc(), xbmc.LOGERROR)

def _extract_videoz_url(html):
    url = re.search("<iframe.*? src='(.*?)'", html)
    xbmc.log('_extract_videoz_url: ' + str(url), xbmc.LOGDEBUG)
    return vkpass_streams(url.group(1), recursive_call=True)

def _vkpass_streams_from_html(html, recursive_call):
    xbmc.log('_vkpass_streams_from_html', xbmc.LOGDEBUG)
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    # Look for videoz
    if re.findall("<iframe.*? src='", html):
        xbmc.log('_vkpass_streams_from_html: videoz', xbmc.LOGDEBUG)
        return _extract_videoz_url(html)

    # Look for p,a,c,k,e,d js files
    if html.find('eval(function(p,a,c,k,e') != -1:
        xbmc.log('_vkpass_streams_from_html: packed', xbmc.LOGDEBUG)
        return _extract_packed_videourls(html)


    # Look for video tag
    source_tags = re.findall(r'(<source.*?\/>)', html)
    if source_tags:
        xbmc.log('_vkpass_streams_from_html: tags', xbmc.LOGDEBUG)
        return _extract_source_tags(html)

    identifier = "vsource=["

    if identifier not in html:
        binurl = re.search(r"src= \"javascript:decodeURIComponent\(escape\(window.atob\(\\'(?P<binurl>.*)\\'\)\)\)\"", html) #\(\\\'(?P<binurl>.*)\\\'\)\)', html)
        if binurl:
            url = binascii.a2b_base64(binurl.group('binurl'))
            return _vkpass_streams_from_html(url, True)

        # No match, try clear text decoding
        redirect_url = re.search('src=\"(?P<url>.*?)\?', html)
        if redirect_url and not recursive_call:
            return vkpass_streams(redirect_url.group('url'), True)
        else:
            xbmc.log('_vkpass_streams_from_html: failed to extract stream', xbmc.LOGERROR)
            xbmc.log(html, xbmc.LOGERROR)
            return None


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
        link = '%s|User-Agent=%s&Accept=%s'
        link = link % (url, HEADERS['User-Agent'], HEADERS['Accept'])

        formats.append((label, link))
        file_start = html.find('file:', quote_end)

    if len(formats) == 0:
        xbmc.log('_vkpass_streams_from_html: failed to extract formats', xbmc.LOGERROR)
        xbmc.log(traceback.format_exc(), xbmc.LOGERROR)
    return formats


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
    url = 'http://vkpass.com/token/bdrxwnlzfjpq/vklhash/Pw7Iy8MztzzwN6xh7nOhf6o80rxCAYIhP8xiQFZ2fGXGWU7DkuzOqurGGBoJoMTvOUqd6XOGaWciR1FfSDFw7Q=='
    print(vkpass_streams(url))
