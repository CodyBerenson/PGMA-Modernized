#!/usr/bin/env python
# encoding=utf8
'''
# AdultFilmDatabase - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    25 Dec 2020     2020.12.25.01   Creation
    19 Aug 2022     2020.12.25.06   Multiple Improvements and major rewrites
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
    05 Dec 2022     2020.12.25.07   Updated to use latest version of utils.py
    13 Jul 2023     2020.12.25.08   Updated to use latest version of utils.py

-----------------------------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2020.12.25.08'
AGENT = 'AdultFilmDatabase'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS - in list format - ADFD uses post requests rather than building up urls
BASE_URL = 'https://www.adultfilmdatabase.com'
BASE_SEARCH_URL = 'https://www.adultfilmdatabase.com/lookup.cfm'

# Date Format used by website
DATEFORMAT = '%Y%m%d'

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
    HTTP.Headers['Cookie'] = '_ga=GA1.2.816682926.1661214413; _gid=GA1.2.1216533004.1661214413; __atuvc=1|34; __atuvs=63041ed81032eb25000; CFID=120394462; CFTOKEN=32f76bc12c124adf-D11CB69E-BACA-F9BA-DEAF0A8BD0928759; _gat=1'
    HTTP.Headers['Host'] = 'www.adultfilmdatabase.com'
    HTTP.Headers['Origin'] = 'https://www.adultfilmdatabase.com'
    HTTP.Headers['Referer'] = 'https://www.adultfilmdatabase.com/advsearch.cfm'
    HTTP.Headers['Upgrade-Insecure-Requests'] = 1
    HTTP.Headers['User-Agent'] = utils.getUserAgent()

# ----------------------------------------------------------------------------------------------------------------------------------
class AdultFilmDatabase(Agent.Movies):
    ''' define Agent class '''
    name = 'AdultFilmDatabase (IAFD)'
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        utils.log('AGENT :: {0:<29} {1}'.format('Original Search Query', myString))

        # convert to lower case and trim
        myString = myString.replace(' - ', ': ').lower().strip()
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

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL

        formData = {'Find':searchTitle, 'Exact': 0, 'searchType': 'All', 'dsp': 60}
        utils.log('SEARCH:: Search Query Form Data: {0}'.format(formData))
        try:
            html = HTML.ElementFromURL(searchQuery, headers=formData, values=formData, timeout=20, sleep=utils.delay())
            # Finds the entire media enclosure
            filmsList = html.xpath('//div[@class="w3-twothirds"]')
            if not filmsList:
                raise Exception('< No Films! >')

        except Exception as e:
            utils.log('SEARCH:: Error: Search Query did not pull any results: {0}'.format(e))

        else:
            filmsFound = len(filmsList)
            utils.log('SEARCH:: {0:<29} {1}'.format('Titles Found', '{0}'.format(filmsFound)))
            utils.log(LOG_BIGLINE)
            myYear = '({0})'.format(FILMDICT['Year']) if FILMDICT['Year'] else ''
            for idx, film in enumerate(filmsList, start=1):
                utils.log('SEARCH:: {0:<29} {1}'.format('Processing', '{0} of {1} for {2} - {3} {4}'.format(idx, filmsFound, FILMDICT['Studio'], FILMDICT['Title'], myYear)))
                utils.log(LOG_BIGLINE)

                # Site Title
                try:
                    filmTitle = film.xpath('./p/a/@title')[0]
                    utils.matchTitle(filmTitle, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Title URL
                utils.log(LOG_BIGLINE)
                try:
                    filmURL = film.xpath('./p/a/@href')[0]
                    filmURL = ('' if BASE_URL in filmURL else BASE_URL) + filmURL
                    FILMDICT['FilmURL'] = filmURL
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', filmURL))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title URL: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Entry - Studio Name + Release Year
                utils.log(LOG_BIGLINE)
                try:
                    filmEntry = film.xpath('./p/span[@class="w3-small w3-text-grey"]/text()')[0].strip()
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Entry', filmEntry))
                    filmStudio, filmReleaseDate = filmEntry.split('|')
                except:
                    utils.log('SEARCH:: Error getting Site Entry: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Studio Name
                utils.log(LOG_BIGLINE)
                try:
                    filmStudio = filmStudio.strip()
                    utils.matchStudio(filmStudio, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Studio: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Release Date
                utils.log(LOG_BIGLINE)
                try:
                    filmReleaseDate = filmReleaseDate.strip()
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Release Date', filmReleaseDate))
                    try:
                        filmReleaseDate = '{0}1231'.format(filmReleaseDate)
                        filmReleaseDate = datetime.strptime(filmReleaseDate, '%Y%m%d')
                        utils.matchReleaseDate(filmReleaseDate, FILMDICT)
                        vReleaseDate = filmReleaseDate
                    except Exception as e:
                        if FILMDICT['Year']:
                            utils.log(LOG_SUBLINE)
                            continue
                except:
                    utils.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                    vReleaseDate = FILMDICT['CompareDate'] if FILMDICT['CompareDate'] else None

                # Access Site URL
                utils.log(LOG_BIGLINE)
                try:
                    utils.log('SEARCH:: {0:<29} {1}'.format('Reading Site URL page', filmURL))
                    fhtml = HTML.ElementFromURL(FILMDICT['FilmURL'], sleep=utils.delay())
                    FILMDICT['FilmHTML'] = fhtml
                except Exception as e:
                    utils.log('SEARCH:: Error reading Site URL page: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Film Duration
                utils.log(LOG_BIGLINE)
                matchedDuration = False
                vDuration = FILMDICT['Duration']
                try:
                    fhtmlDuration = fhtml.xpath('//span[@itemprop="duration"]/text()')[0].replace('Runtime: ', '').strip()
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Film Duration', fhtmlDuration))
                    fhtmlDuration = fhtmlDuration.split(':')                                                 # split into hr, mins, secs
                    fhtmlDuration = [int(x) for x in fhtmlDuration if x.strip()]                             # convert to integer
                    duration = fhtmlDuration[0] * 3600 + fhtmlDuration[1] * 60 + fhtmlDuration[2]            # convert to seconds
                    duration = datetime.fromtimestamp(duration)
                    try:
                        utils.matchDuration(duration, FILMDICT)
                        matchedDuration = True
                        vDuration = duration
                    except Exception as e:
                        utils.log('SEARCH:: Error matching Site Film Duration: {0}'.format(e))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Film Duration')

                if matchedDuration is False and AGENTDICT['prefMATCHSITEDURATION'] is True:
                    utils.log(LOG_SUBLINE)
                    continue

                FILMDICT['vCompilation'] = ''
                FILMDICT['vDuration'] = vDuration
                FILMDICT['vReleaseDate'] = vReleaseDate
                del FILMDICT['FilmHTML']

                myID = json.dumps(FILMDICT, default=utils.jsonDumper)
                results.Append(MetadataSearchResult(id=myID, name=FILMDICT['Title'], score=100, lang=lang))

                # Film Scraped Sucessfully - update status and break out!
                FILMDICT['Status'] = True
                break       # stop processing

        # End Search Routine
        utils.logFooter('SEARCH', FILMDICT)
        return FILMDICT['Status']

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        utils.updateMetadata(metadata, media, lang, force=True)
