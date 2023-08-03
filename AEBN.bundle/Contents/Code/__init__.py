#!/usr/bin/env python
# encoding=utf8
'''
# AEBN - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    19 Aug 2022     2020.05.21.13   Multiple Improvements and major rewrites
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
    27 Nov 2022     2020.05.21.14   Updated to use latest version of utils.py
    04 Dec 2022     2020.05.21.15   Renamed to AEBN
    10 Jul 2023     2020.05.21.16   Updated to use new utils.py
    01 Aug 2023     2020.05.21.17   Improved matching with IAFD
-----------------------------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2020.05.21.17'
AGENT = 'AEBN'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS
BASE_URL = 'https://gay.aebn.com'
BASE_SEARCH_URL = BASE_URL + '/gay/search?queryType=Free+Form&sysQuery={0}&criteria=%7B%22sort%22%3A%22Relevance%22%7D'

# Date Formats used by website
DATEFORMAT = '%b %d, %Y'

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
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-Agent'] = utils.getUserAgent()

# ----------------------------------------------------------------------------------------------------------------------------------
class AEBN(Agent.Movies):
    ''' define Agent class '''
    name = 'AEBN (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        utils.log('AGENT :: {0:<29} {1}'.format('Original Search Query', myString))

        # convert to lower case and trim and strip diacritics, fullstops, enquote
        myString = myString.lower().strip()
        myString = String.StripDiacritics(myString)

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myString = String.URLEncode('{0}'.format(myString)).replace('%25', '%').replace('*', '')

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

        # Search Query - for use to search the internet, remove all non alphabetic characters.
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        for searchTitle in FILMDICT['SearchTitles']:
            if FILMDICT['Status'] is True:
                break

            searchTitle = self.CleanSearchString(searchTitle)
            searchQuery = BASE_SEARCH_URL.format(searchTitle)
            morePages = True
            pageNumber = 0
            while morePages:
                utils.log('SEARCH:: {0:<29} {1}'.format('Search Query', searchQuery))
                pageNumber += 1
                if pageNumber > 10:
                    morePages = False     # search a maximum of 10 pages
                    utils.log('SEARCH:: Warning: Page Search Limit Reached [10]')
                    continue

                try:
                    html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=utils.delay())
                    filmsList = html.xpath('//div[@class="dts-collection-item dts-collection-item-movie"][@id]/div[contains(@id, "dtsImageOverlayContainer")]')
                    if not filmsList:
                        raise Exception('< No Films! >')

                    # if there is a list of films - check if there are further pages returned
                    try:
                        searchQuery = html.xpath('//ul[@class="dts-pagination"]/li[@class="active" and text()!="..."]/following::li/a[@class="dts-paginator-tagging"]/@href')[0]
                        searchQuery = (BASE_URL if BASE_URL not in searchQuery else '') + searchQuery
                        morePages = True    # next page search query determined so set as true
                    except:
                        morePages = False

                except Exception as e:
                    utils.log('SEARCH:: Error: Search Query did not pull any results: {0}'.format(e))
                    break

                filmsFound = len(filmsList)
                utils.log('SEARCH:: {0:<29} {1}'.format('Titles Found', '{0} Processing Results Page: {1:>2}'.format(filmsFound, pageNumber)))
                utils.log(LOG_BIGLINE)
                myYear = '({0})'.format(FILMDICT['Year']) if FILMDICT['Year'] else ''
                for idx, film in enumerate(filmsList, start=1):
                    utils.log('SEARCH:: {0:<29} {1}'.format('Processing', 'Page {0}: {1} of {2} for {3} - {4} {5}'.format(pageNumber, idx, filmsFound, FILMDICT['Studio'], FILMDICT['Title'], myYear)))
                    utils.log(LOG_BIGLINE)

                    # Site Title
                    try:
                        filmTitle = film.xpath('./a[contains(@href,"/movies/")]//img/@title')[0]
                        utils.matchTitle(filmTitle, FILMDICT)
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Title: {0}'.format(e))
                        utils.log(LOG_SUBLINE)
                        continue

                    # Site Title URL
                    utils.log(LOG_BIGLINE)
                    try:
                        filmURL = film.xpath('./a/@href')[0]
                        filmURL = ('' if BASE_URL in filmURL else BASE_URL) + filmURL
                        FILMDICT['FilmURL'] = filmURL
                        utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', filmURL))
                    except:
                        utils.log('SEARCH:: Error getting Site Title Url')
                        utils.log(LOG_SUBLINE)
                        continue

                    # Access Site URL for Studio and Release Date information
                    utils.log(LOG_BIGLINE)
                    try:
                        utils.log('SEARCH:: {0:<29} {1}'.format('Reading Site URL page', filmURL))
                        fhtml = HTML.ElementFromURL(FILMDICT['FilmURL'], sleep=utils.delay())
                        FILMDICT['FilmHTML'] = fhtml
                    except Exception as e:
                        utils.log('SEARCH:: Error reading Site URL page: {0}'.format(e))
                        utils.log(LOG_SUBLINE)
                        continue

                    # Site Studio Name
                    utils.log(LOG_BIGLINE)
                    matchedStudio = False
                    try:
                        fhtmlStudios = fhtml.xpath('//div[@class="dts-studio-name-wrapper"]/a/text()')
                        FILMDICT['RecordedStudios'] = fhtmlStudios
                        utils.log('UPDATE:: {0:<29} {1}'.format('Site URL Studios', '{0:>2} - {1}'.format(len(fhtmlStudios), fhtmlStudios)))
                        for item in fhtmlStudios:
                            try:
                                utils.matchStudio(item, FILMDICT)
                                matchedStudio = True
                                break
                            except Exception as e:
                                utils.log('SEARCH:: Error Matching {0}: {1}'.format(item, e))
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Studio {0}'.format(e))

                    if not matchedStudio:
                        utils.log('SEARCH:: Error No Matching Site Studio')
                        utils.log(LOG_SUBLINE)
                        continue

                    # Site Release Date
                    utils.log(LOG_BIGLINE)
                    vReleaseDate = FILMDICT['CompareDate']
                    try:
                        fhtmlReleaseDate = fhtml.xpath('//li[contains(@class,"item-release-date")]/text()')[0].strip()
                        fhtmlReleaseDate = fhtmlReleaseDate.replace('July', 'Jul').replace('Sept', 'Sep')    # AEBN uses 4 letter abbreviation for September & July
                        utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Release Date', fhtmlReleaseDate))
                        try:
                            releaseDate = datetime.strptime(fhtmlReleaseDate, DATEFORMAT)
                            utils.matchReleaseDate(releaseDate, FILMDICT)
                            vReleaseDate = releaseDate
                        except Exception as e:
                            utils.log('SEARCH:: Error getting Site URL Release Date: {0}'.format(e))
                            if FILMDICT['Year']:
                                utils.log(LOG_SUBLINE)
                                continue
                    except:
                        utils.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')

                    # Site Film Duration
                    utils.log(LOG_BIGLINE)
                    matchedDuration = False
                    vDuration = FILMDICT['Duration']
                    try:
                        fhtmlDuration = fhtml.xpath('//span[text()="Running Time:"]/parent::li/text()')[0].strip()
                        utils.log('SEARCH:: {0:<29} {1}'.format('Site Film Duration', fhtmlDuration))
                        fhtmlDuration = fhtmlDuration.split(':')                                                      # split into hr, mins, secs
                        fhtmlDuration = [int(x) for x in fhtmlDuration]                                               # convert to integer
                        fhtmlDuration = ['0{0}'.format(x) if x < 10 else '{0}'.format(x) for x in fhtmlDuration]      # converted to zero padded items
                        fhtmlDuration = ['00'] + fhtmlDuration if len(fhtmlDuration) == 2 else fhtmlDuration    # prefix with zero hours if string is only minutes and seconds
                        fhtmlDuration = '1970-01-01 {0}'.format(':'.join(fhtmlDuration))                              # prefix with 1970-01-01 to conform to timestamp
                        duration = datetime.strptime(fhtmlDuration, '%Y-%m-%d %H:%M:%S')                                 # turn to date time object
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

                if FILMDICT['Status'] is True:      # if search and process sucessful stop processing
                    break

        # End Search Routine
        utils.logFooter('SEARCH', FILMDICT)
        return FILMDICT['Status']

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        utils.updateMetadata(metadata, media, lang, force=True)
