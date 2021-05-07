'''
Functions used to bypass cloudflare restrictions on websites like IAFD
                                                  Version History
                                                  ---------------
    Date         Dev          Modification
    16 Apr 2021  Codeanator   Initial
    03 May 2021  JPH71        Clean-up of unused functions and standardisation of logging
'''
# -------------------------------------------------------------------------------------------------------------------------------
import cloudscraper, fake_useragent
from urlparse import urlparse

scraper = None

# -------------------------------------------------------------------------------------------------------------------------------
def getUserAgent():
    ua = fake_useragent.UserAgent(fallback='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36')

    return ua.random

# -------------------------------------------------------------------------------------------------------------------------------
def HTTPRequest(url, **kwargs):
    url = getClearURL(url)
    headers = kwargs.pop('headers', {})
    cookies = kwargs.pop('cookies', {})
    timeout = kwargs.pop('timeout', 20)
    proxies = {}

    global scraper

    if 'User-Agent' not in headers:
        headers['User-Agent'] = getUserAgent()

    req = None
    try:
        log('UTILS :: CloudScraper Request         \t%s', url)
        if scraper is None:
            scraper = cloudscraper.CloudScraper()
            scraper.headers.update(headers)
            scraper.cookies.update(cookies)
        req = scraper.request('GET', url, timeout=timeout, proxies=proxies)
        log('UTILS :: CloudScraper Response        \tOK? <%s> - Status <%s>', req.ok, req.status_code)

    except Exception as e:
        msg = ('CloudScraper Failed: %s', e)
        raise Exception(msg)

    if req:
        req.encoding = 'UTF-8'

    return req

# -------------------------------------------------------------------------------------------------------------------------------
def getClearURL(url):
    clearURL = url
    if url.startswith('http'):
        url = urlparse(url)
        path = url.path
        path = path.replace('//', '/')

        clearURL = '%s://%s%s' % (url.scheme, url.netloc, path)
        if url.query:
            clearURL += '?%s' % url.query

    return clearURL