#!/usr/bin/env python
# encoding=utf8
'''
# SimplyAdult - (IAFD): Hot Free Gay Porn Movies
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    15 Nov 2021     2021.11.15.01   Initial
    04 Feb 2022     2021.11.15.02   implemented change suggested by Cody: duration matching optional on IAFD matching
                                    Cast list if used in filename becomes the default that is matched against IAFD, useful in case no cast is listed in agent
    19 Aug 2022     2020.11.15.03   Multiple Improvements and major rewrites
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
    05 Dec 2022     2020.11.15.04   Updated to use latest version of utils.py
    13 Jul 2023     2020.11.15.05   Updated to use latest version of utils.py

-----------------------------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2021.11.15.05'
AGENT = 'SimplyAdult'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS
BASE_URL = 'https://www.simply-adult.com/'
BASE_SEARCH_URL = BASE_URL + 'search.php?mode=search&page={0}'

# Date Formats used by website
DATEFORMAT = '%d-%m-%Y'

# Website Language
SITE_LANGUAGE = 'en'

# utils.log section separators
LOG_BIGLINE = '-' * 140
LOG_SUBLINE = '      ' + '-' * 100
LOG_ASTLINE = '*' * 140
# ----------------------------------------------------------------------------------------------------------------------------------
# imports placed here to use previously declared variables
import utils

# ----------------------------------------------------------------------------------------------------------------------------------
def Start():
    ''' initialise process '''
    HTTP.CacheTime = 0
    HTTP.Headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    HTTP.Headers['Accept-Encoding'] = 'gzip, deflate, br'
    HTTP.Headers['Accept-Language'] = 'en-GB,en;q=0.9,en-US;q=0.8'
    HTTP.Headers['Cache-Control'] = 'max-age=0'
    HTTP.Headers['Content-Type'] = 'application/x-www-form-urlencoded'
    HTTP.Headers['Cookie'] = 'RefererCookie=https://www.gaydvds.co.uk/; store_language=en; partner=51; partner_clickid=6800535; partner_time=1666373835; __utmc=108201344; __utmz=108201344.1661191760.2.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); xid_509da=6267c503f5ac8fc781894366f057ece5; _ga=GA1.2.604161530.1634826735; _gid=GA1.2.1534648779.1661191770; __utma=108201344.604161530.1634826735.1661196433.1661200043.4; __utmt=1; __utmb=108201344.2.10.1661200043; _gat=1'
    HTTP.Headers['Host'] = 'www.simply-adult.com'
    HTTP.Headers['Origin'] = 'https://www.simply-adult.com'
    HTTP.Headers['Referer'] = 'https://www.simply-adult.com/search.php'
    HTTP.Headers['Upgrade-Insecure-Requests'] = 1
    HTTP.Headers['User-Agent'] = utils.getUserAgent()

# ----------------------------------------------------------------------------------------------------------------------------------
class SimplyAdult(Agent.Movies):
    ''' define Agent class '''
    name = 'SimplyAdult (IAFD)'
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        utils.log('AGENT :: {0:<29} {1}'.format('Original Search Query', myString))

        # convert to lower case and trim
        myString = myString.replace(' - ', ': ').replace('- ', ': ').lower().strip()
        myString = String.StripDiacritics(myString)

        # strip non-alphanumeric characters
        pattern = ur'[^A-Za-z0-9]+'
        myString = re.sub(pattern, ' ', myString, flags=re.IGNORECASE)
        myString = myString.replace('  ', ' ').strip()

        utils.log('AGENT :: {0:<29} {1}'.format('Returned Search Query', myString))
        utils.log(LOG_BIGLINE)

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            utils.log(LOG_ASTLINE)
            utils.log('SEARCH:: {0:<29} {1}'.format('Warning: Missing Media Item File', 'QUIT'))
            utils.log(LOG_ASTLINE)
            return

        #clear-cache directive
        if media.name == "clear-cache":
            HTTP.ClearCache()
            results.Append(MetadataSearchResult(id='clear-cache', name='Plex web cache cleared', year=media.year, lang=lang, score=0))
            utils.log(LOG_ASTLINE)
            utils.log('SEARCH:: {0:<29} {1}'.format('Warning: Clear Cache Directive Encountered', 'QUIT'))
            utils.log(LOG_ASTLINE)
            return

        AGENTDICT = copy.deepcopy(utils.setupAgentVariables(media))
        if not AGENTDICT:
            utils.log(LOG_ASTLINE)
            utils.log('SEARCH:: {0:<29} {1}'.format('Error: Could Not Set Agent Parameters', 'QUIT'))
            utils.log(LOG_ASTLINE)
            return

        utils.logHeader('SEARCH', AGENTDICT, media, lang)

        # Check filename format
        try:
            FILMDICT = copy.deepcopy(utils.matchFilename(AGENTDICT, media))
            FILMDICT['lang'] = lang
            FILMDICT['Agent'] = AGENT
            FILMDICT['Status'] = False
        except Exception as e:
            utils.log(LOG_ASTLINE)
            utils.log('SEARCH:: Error: {0}'.format(e))
            utils.log(LOG_ASTLINE)
            return

        utils.log(LOG_BIGLINE)

        # Search Query - for use to search the internet
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL

        # Here are all of our headers
        posted_data = {'substring': searchTitle, 'including': 'phrase', 'by_title': 'on', 'categoryid': 2, 'search_in_subcategories': 'on', 
                       'price_min': None, 'price_max': None, 'weight_min': None, 'weight_max': None}
        formData = {'mode': 'search', 'posted_data': posted_data}

        morePages = True
        pageNumber = 1
        while morePages:
            utils.log('SEARCH:: Search Query Form Data: {0}'.format(formData))
            try:
                html = HTML.ElementFromURL(searchQuery.format(pageNumber), headers=formData, timeout=20, sleep=utils.delay())
                # Finds the entire media enclosure
                filmsList = html.xpath('//div[@class="item-box"]')
                if not filmsList:
                    raise Exception('< No Films! >')

            except Exception as e:
                utils.log('SEARCH:: Error: Search Query did not pull any results: {0}'.format(e))
                break

            try:
                pageNumber = int(html.xpath('//div[@class="nav-pages"]/span[contains(@title,"Current page:")]/text()')[0])
                searchQuery = BASE_SEARCH_URL.format(pageNumber + 1)
                utils.log('SEARCH:: Next Page Search Query: {0}'.format(searchQuery))
                morePages = True if pageNumber <= 10 else False
            except:
                searchQuery = ''
                utils.log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            filmsFound = len(filmsList)
            utils.log('SEARCH:: {0:<29} {1}'.format('Titles Found', '{0} Processing Results Page: {1:>2}'.format(filmsFound, pageNumber)))
            utils.log(LOG_BIGLINE)
            myYear = '({0})'.format(FILMDICT['Year']) if FILMDICT['Year'] else ''
            for idx, film in enumerate(filmsList, start=1):
                utils.log('SEARCH:: {0:<29} {1}'.format('Processing', '{0} of {1} for {2} - {3} {4}'.format(idx, filmsFound, FILMDICT['Studio'], FILMDICT['Title'], myYear)))
                utils.log(LOG_BIGLINE)

                # Site Title
                try:
                    filmTitle =  film.xpath('./div[@class="details"]/a/text()')[0]
                    utils.matchTitle(filmTitle, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Title URL
                utils.log(LOG_BIGLINE)
                try:
                    filmURL =  film.xpath('./div[@class="details"]/a/@href')[0]
                    FILMDICT['FilmURL'] = filmURL
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', filmURL))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title Url: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Studio Name
                utils.log(LOG_BIGLINE)
                try:
                    filmStudio =  film.xpath('./div[@class="details"]/div[@class="manufacturer"]/text()')[0]
                    utils.matchStudio(filmStudio, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Studio: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Release Date - None on Site
                utils.log(LOG_BIGLINE)
                vReleaseDate = FILMDICT['CompareDate']
                utils.log('SEARCH:: {0:<29} {1}'.format('Release Date: Use Default', vReleaseDate))

                # Site Film Duration - None on Site
                utils.log(LOG_BIGLINE)
                vDuration = FILMDICT['Duration']
                utils.log('SEARCH:: {0:<29} {1}'.format('Duration: Use Default', vDuration))

                FILMDICT['vCompilation'] = ''
                FILMDICT['vDuration'] = vDuration
                FILMDICT['vReleaseDate'] = vReleaseDate
                del FILMDICT['FilmHTML']

                myID = json.dumps(FILMDICT, default=utils.jsonDumper)
                results.Append(MetadataSearchResult(id=myID, name=FILMDICT['Title'], score=100, lang=lang))

                # Film Scraped Sucessfully - update status and break out!
                FILMDICT['Status'] = True
                break       # stop processing

            if FILMDICT['Status'] is True:      # if search and process sucessful stop processing
                break

        # End Search Routine
        utils.logFooter('SEARCH', FILMDICT)
        return FILMDICT['Status']

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        utils.updateMetadata(metadata, media, lang, force=True)
