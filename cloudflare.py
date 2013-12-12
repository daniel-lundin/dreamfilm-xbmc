""" Module to bypass cloudflare's "I'm Under Attack Mode"

Tries to make a request, and if a 503 response is returned
Calculate the javascript challenge to get the clearance cookie.

Entry point is dreamfilm_request
"""
import urllib2

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_0) \
        AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/31.0.1650.57 Safari/537.36'


def add(l, r):
    return parse_aritmetic_string(l) + parse_aritmetic_string(r)


def mult(l, r):
    return parse_aritmetic_string(l) * parse_aritmetic_string(r)


def parse_aritmetic_string(s):
    p_pos = s.find('+')
    m_pos = s.find('*')
    if p_pos == -1 and m_pos == -1:
        return int(s)
    if p_pos == -1:
        return mult(s[0:m_pos], s[m_pos + 1:])
    return add(s[0:p_pos], s[p_pos + 1:])


def calc_jschl_answer(html):
    s = 'dreamfilm.se'
    a_start = html.find('a.value')
    expr = html[a_start + 10:html.find(';', a_start)]
    res = parse_aritmetic_string(expr)
    return res + len(s)


def get_form_values(html):
    action_url_start = html.find("action=\"") + 8
    action_url_end = html.find("\"", action_url_start + 1)
    action_url = html[action_url_start:action_url_end]

    a = 'name="jschl_vc" value="'
    vc_value_start = html.find(a) + len(a)
    vc_value_end = html.find('"', vc_value_start)
    vc_value = html[vc_value_start:vc_value_end]

    return action_url, vc_value


def cf_get_url(url, js_answer, vc_value):
    return '%s?jschl_vc=%s&jschl_answer=%s' % (url, vc_value, js_answer)


class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        pass  # Disable redirect


def cloudflare_clearance(cf_content, cfduid_cookie):
    js_answer = calc_jschl_answer(cf_content)
    url, vc = get_form_values(cf_content)
    url_with_query = cf_get_url(url, js_answer, vc)

    headers = {
        'Cookie': cfduid_cookie,
        'User-agent': 'curl/7.30.0'
    }
    req = urllib2.Request('http://dreamfilm.se' + url_with_query,
                          headers=headers)
    try:
        # Build custom opener with a redirect handler
        # This gives us a chance to get the cookie
        opener = urllib2.build_opener(NoRedirectHandler)
        opener.open(req).read()
    except Exception, e:
        # Get clearance cookie
        cookie = e.headers.getheader('Set-Cookie').split(';')[0]
        return cookie


def _dreamfilm_request(url, data=None, cookie_string=None):
    headers = {
        'User-agent': 'curl/7.30.0',
        'Cookie': cookie_string
    }
    req = urllib2.Request(url, headers=headers)
    if data:
        req.add_data(data)

    return urllib2.urlopen(req).read()


def dreamfilm_request(url, data=None, cookie_string=None):
    headers = {
        'User-agent': 'curl/7.30.0'
    }
    if cookie_string:
        headers['Cookie'] = cookie_string
    try:
        req = urllib2.Request(url, headers=headers)
        if data:
            req.add_data(data)
        return urllib2.urlopen(req).read()
    except urllib2.HTTPError, e:
        if e.code != 503:
            return ('Dreamfilm replied with status code: %d' % e.code)

        cfduid_cookie = e.headers.getheaders('Set-Cookie')[0].split(';')[0]

        # Might need wait here
        clearance_cookie = cloudflare_clearance(e.read(), cfduid_cookie)
        cookie_string = '%s;%s' % (cfduid_cookie, clearance_cookie)

        return _dreamfilm_request(url, data, cookie_string)

if __name__ == '__main__':
    print dreamfilm_request('http://dreamfilm.se')
    exit(0)
