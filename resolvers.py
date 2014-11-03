import urllib
import urllib2
import json

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
    #print decoded

    #print decoded.split('url=')

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

    video_params_start = html.find('videoParams');
    video_params_end = html.find('}', video_params_start)
    json_string = html[video_params_start + 14:video_params_end + 1]

    video_params = json.loads(json_string)
    
    metadata_response = urllib2.urlopen(video_params['metadataUrl'])
    metadata = json.loads(metadata_response.read())

    streams = metadata['videos']
    # XBMC player needs cookies to play these
    for key in streams:
        streams[key] += '|Cookie=' + urllib.quote(cookie_string)

    return streams.items()
