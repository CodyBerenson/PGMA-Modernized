import googlesearch
import fake_useragent
import cloudscraper
import requests
import urlparse
from requests_response import FakeResponse

scraper = None

def getUserAgent():
    ua = fake_useragent.UserAgent(fallback='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36')

    return ua.random


def cloudScraperRequest(url, method, **kwargs):
    headers = kwargs.pop('headers', {})
    cookies = kwargs.pop('cookies', {})
    params = kwargs.pop('params', {})
    global scraper

    if scraper is None:
        scraper = cloudscraper.CloudScraper()
        scraper.headers.update(headers)
        scraper.cookies.update(cookies)

    req = scraper.request(method, url, data=params)

    return req


def reqBinRequest(url, method, **kwargs):
    headers = kwargs.pop('headers', {})
    cookies = kwargs.pop('cookies', {})
    proxies = kwargs.pop('proxies', {})
    params = kwargs.pop('params', {})

    if cookies and 'Cookie' not in headers:
        cookie = '; '.join(['%s=%s' % (key, cookies[key]) for key in cookies])
        headers['Cookie'] = cookie

    req_headers = '\n'.join(['%s: %s' % (key, headers[key]) for key in headers])

    for node in ['US', 'DE']:
        req_data = {
            'method': method,
            'url': url,
            'headers': req_headers,
            'apiNode': node,
            'idnUrl': url
        }

        if method == 'POST':
            if headers['Content-Type'] == 'application/json':
                req_data['contentType'] = 'JSON'
                req_data['content'] = params
            else:
                req_data['contentType'] = 'URLENCODED'
                req_data['content'] = '&'.join(['%s=%s' % (key, params[key]) for key in params])

        req_params = json.dumps({
            'id': 0,
            'json': json.dumps(req_data),
            'deviceId': '',
            'sessionId': ''
        })

        req = HTTPRequest('https://api.reqbin.com/api/v1/requests', headers={'Content-Type': 'application/json'}, params=req_params, proxies=proxies, bypass=False)
        if req.ok:
            data = req.json()
            return FakeResponse(req, url, int(data['StatusCode']), data['Content'])
    return None


def HTTPBypass(url, method='GET', **kwargs):
    method = method.upper()
    headers = kwargs.pop('headers', {})
    cookies = kwargs.pop('cookies', {})
    params = kwargs.pop('params', {})
    proxies = kwargs.pop('proxies', {})

    req_bypass = None

    if not req_bypass or not req_bypass.ok:
        Log('CloudScraper')
        try:
            req_bypass = cloudScraperRequest(url, method, proxies=proxies, headers=headers, cookies=cookies, params=params)
        except Exception as e:
            Log('CloudScraper failed : %s', e)
            pass

    if not req_bypass or not req_bypass.ok:
        Log('ReqBin')
        try:
            req_bypass = reqBinRequest(url, method, proxies=proxies, headers=headers, cookies=cookies, params=params)
        except Exception as e:
            Log('ReqBin failed : %s', e)
            pass
    
    Log('UTILS:: Req_bypass: %s', req_bypass)

    return req_bypass


def HTTPRequest(url, method='GET', **kwargs):
    url = getClearURL(url)
    method = method.upper()
    headers = kwargs.pop('headers', {})
    cookies = kwargs.pop('cookies', {})
    params = kwargs.pop('params', {})
    bypass = kwargs.pop('bypass', True)
    timeout = kwargs.pop('timeout', None)
    errors = kwargs.pop('errors', 'ignore')
    sleep = kwargs.pop('sleep', 0)
    allow_redirects = kwargs.pop('allow_redirects', True)
    proxies = {}

    if 'User-Agent' not in headers:
        headers['User-Agent'] = getUserAgent()

    if params:
        method = 'POST'

    Log('UTILS:: Requesting %s "%s"' % (method, url))

    req = None
    try:
        req = requests.request(method, url, proxies=proxies, headers=headers, cookies=cookies, data=params, timeout=timeout, verify=False, allow_redirects=allow_redirects)
        Log('UTILS:: Req is OK? %s - Req.status: %s', req.ok, req.status_code)
    except Exception as e:
        req = FakeResponse(None, url, 418, None)
        Log('UTILS:: Sending fake response following exception %s', e)

    req_bypass = None
    if not req.ok and bypass:
        if req.status_code == 403 or req.status_code == 503:
            Log('UTILS:: Switching to HTTPBypass for %s', url)
            req_bypass = HTTPBypass(url, method, proxies=proxies, headers=headers, cookies=cookies, params=params)

    if req_bypass:
        req = req_bypass

    req.encoding = 'UTF-8'

    Log('UTILS:: Returning req: %s', req)

    return req


def getFromGoogleSearch(searchText, site='', **kwargs):
    stop = kwargs.pop('stop', 10)
    lang = kwargs.pop('lang', 'en')

    if isinstance(site, int):
        site = PAsearchSites.getSearchBaseURL(site).split('://')[1].lower()
        if site.startswith('www.'):
            site = site.replace('www.', '', 1)

    googleResults = []
    searchTerm = 'site:%s %s' % (site, searchText) if site else searchText

    if not searchText:
        return googleResults

    Log('Using Google Search "%s"' % searchTerm)

    try:
        googleResults = list(googlesearch.search(searchTerm, stop=stop, lang=lang, user_agent=getUserAgent()))
    except:
        Log('Google Search Error')
        pass

    return googleResults

def getClearURL(url):
    newURL = url
    if url.startswith('http'):
        url = urlparse.urlparse(url)
        path = url.path

        while '//' in path:
            path = path.replace('//', '/')

        newURL = '%s://%s%s' % (url.scheme, url.netloc, path)
        if url.query:
            newURL += '?%s' % url.query

    return newURL