#!/usr/bin/env python
# encoding=utf8
'''
# GayEmpire (IAFD)
                                    Version History
                                    ---------------
    Date            Version             Modification
    19 Aug 2022     2019.08.12.17   Multiple Improvements and major rewrites
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
    27 Nov 2022     2019.08.12.18   Updated to use latest version of utils.py
    04 Dec 2022     2019.08.12.19   Renamed GayEmpire
    03 Jan 2022     2019.08.12.20   Corrected multipage search results processing
    03 Feb 2023     2019.08.12.21   Use both production year and release dates in matching
    10 Jul 2023     2019.08.12.22   Updated to use new utils.py
    15 Aug 2023     2019.08.12.23   Updated utils.matchduration call to use AGENTDICT
    05 Feb 2024     2019.08.12.24   Extended Agent to search straight site to get Bi Movies
    22 Apr 2024     2019.08.12.25   Changes to list result html
    06 Jun 2024     2019.08.12.26   Changes to Release Date Processing
    21 Jun 2024     2019.08.12.27   Changes to search results detection
    04 Jul 2024     2019.08.12.28   Film Release Date error - variable used before declaration

---------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2019.08.12.28'
AGENT = 'GayEmpire'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS
BASE_URLS = ['http://www.gaydvdempire.com', 'https://www.adultdvdempire.com/']
BASE_SEARCH_URL = '{0}/AllSearch/Search?view=list&q={1}&page={2}'

# Date Formats used by website
DATEFORMAT = '%m/%d/%Y'

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
class GayEmpire(Agent.Movies):
    ''' define Agent class '''
    name = 'GayEmpire (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        utils.log('AGNT  :: Original Search Query        : {0}'.format(myString))

        myString = myString.replace(' -', ':').replace(ur'\u2013', '-').replace(ur'\u2014', '-').lower().strip()

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString)

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        myString = myString.replace('%25', '%').replace('*', '')
        utils.log('AGNT  :: Returned Search Query        : {0}'.format(myString))
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
        for BASE_URL in BASE_URLS:
            pageNumber = 0
            searchQuery = BASE_SEARCH_URL.format(BASE_URL, searchTitle, pageNumber)

            morePages = True
            while morePages and FILMDICT['Status'] == False:
                utils.log('SEARCH:: {0:<29} {1}'.format('Search Query', searchQuery))
                pageNumber += 1
                if pageNumber > 10:
                    morePages = False     # search a maximum of 10 pages
                    utils.log('SEARCH:: Warning: Page Search Limit Reached [10]')
                    continue

                try:
                    html = HTML.ElementFromURL(searchQuery, timeout=90, errors='ignore', sleep=utils.delay())
                    filmsList = html.xpath('.//div[@class="item-list"]/div[@class="row list-view-item"]')
                    filmsList = html.xpath('.//div[contains(@id, "_Item")]')
                    if not filmsList:
                        msg = '< No Film Titles: {0} >'.format(BASE_URL)
                        raise Exception(msg)   # out of WHILE loop

                    filmsFound = len(filmsList)
                    utils.log('SEARCH:: {0:<29} {1}'.format('Titles Found', '{0} Processing Results Page: {1:>2}'.format(filmsFound, pageNumber)))

                    # if there is a list of films - check if there are further pages returned
                    try:
                        nextPage = html.xpath('.//a[@title="Next"]/@href')[0]
                        morePages = True
                        searchQuery = BASE_SEARCH_URL.format(searchTitle, pageNumber)
                    except:
                        morePages = False

                except Exception as e:
                    utils.log('SEARCH:: Error: Search Query did not pull any results: {0}'.format(e))
                    break

                utils.log(LOG_BIGLINE)
                myYear = '({0})'.format(FILMDICT['Year']) if FILMDICT['Year'] else ''
                for idx, film in enumerate(filmsList, start=1):
                    utils.log('SEARCH:: {0:<29} {1}'.format('Processing', 'Page {0}: {1} of {2} for {3} - {4} {5}'.format(pageNumber, idx, filmsFound, FILMDICT['Studio'], FILMDICT['Title'], myYear)))
                    utils.log(LOG_BIGLINE)

                    # siteTitle = The text in the 'title' - Gay DVDEmpire - displays its titles in SORT order
                    try:
                        filmTitle = film.xpath('.//a[@category and @label="Title"]/text()')[0].strip()
                        # convert sort order version to normal version i.e "Best of Zak Spears, The -> The Best of Zak Spears"
                        pattern = u', (The|An|A)$'
                        matched = re.search(pattern, filmTitle, re.IGNORECASE)  # match against string
                        if matched:
                            determinate = matched.group().replace(', ', '')
                            utils.log('SEARCH:: {0:<29} {1}'.format('Found Determinate', determinate))
                            filmTitle = re.sub(pattern, '', filmTitle)
                            filmTitle = '{0} {1}'.format(determinate, filmTitle)

                        # Gay Empire sometimes has the studio title at the end of title - remove
                        pattern = u'\((.*?)\)$'
                        matched = re.search(pattern, filmTitle, re.IGNORECASE)  # match against string
                        if matched:
                            if matched.group(1) in FILMDICT['Studio'] or FILMDICT['Studio'] in matched.group(1):
                                utils.log('SEARCH:: {0:<29} {1}'.format('Studio in Title', matched.group(1)))
                                filmTitle = re.sub(pattern, '', filmTitle)

                        utils.matchTitle(filmTitle, FILMDICT)
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Title: {0}'.format(e))
                        utils.log(LOG_SUBLINE)
                        continue

                    # Site Title URL
                    utils.log(LOG_BIGLINE)
                    try:
                        filmURL = film.xpath('.//a[@category and @label="Title"]/@href')[0]
                        filmURL = ('' if BASE_URL in filmURL else BASE_URL) + filmURL
                        FILMDICT['FilmURL'] = filmURL
                        utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', filmURL))
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Title Url: {0}'.format(e))
                        utils.log(LOG_SUBLINE)
                        continue

                    # Studio Name
                    utils.log(LOG_BIGLINE)
                    try:
                        filmStudio = film.xpath('.//a[@category and @label="Studio Link"]/@title')[0].strip()
                        utils.matchStudio(filmStudio, FILMDICT)
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Studio: {0}'.format(e))
                        utils.log(LOG_SUBLINE)
                        continue

                    # Site Production Year found in brackets - if fails try Release Date 
                    utils.log(LOG_BIGLINE)
                    vReleaseDate = FILMDICT['CompareDate']
                    releaseDateMatch = False
                    releaseDates = set()
                    try:
                        filmProductionYear = film.xpath('.//a[@category and @label="Title"]/following-sibling::text()')[0].replace('(', '').replace(')', '').strip()
                        utils.log('SEARCH:: {0:<29} {1}'.format('Site Production Year', filmProductionYear))
                        releaseDateMatch = True

                    except Exception as e:
                        filmProductionYear = ''
                        utils.log('SEARCH:: Error getting Site Production Year: {0}'.format(e))

                    # Release Date - On GayEmpire - this date sometimes pertains to the day it was added to the site
                    try:
                        filmReleaseDate = film.xpath('.//small[text()="released"]/following-sibling::text()')[0].strip()
                        utils.log('SEARCH:: {0:<29} {1}'.format('Site Release Date', filmReleaseDate))
                        releaseDates.add(filmReleaseDate)                                                           # add to set

                    except Exception as e:
                        filmReleaseDate = ''
                        utils.log('SEARCH:: Error getting Site Release Date: {0}'.format(e))

                    # if production year and release date are in the same year - use the release date only saved above to set
                    if filmProductionYear and filmProductionYear not in filmReleaseDate:
                        filmProductionYearDate = '12/31/{0}'.format(filmProductionYear)                             # add 31st december to production year
                        releaseDates.add(filmProductionYearDate)                                                    # add to set

                    for item in releaseDates:
                        try:
                            releaseDate = datetime.strptime(item, DATEFORMAT)
                            utils.log('SEARCH:: {0:<29} {1}'.format('Selected Release Date', releaseDate))
                            utils.matchReleaseDate(releaseDate, FILMDICT)
                            releaseDateMatch = True
                            vReleaseDate = releaseDate
                            break
                        except Exception as e:
                            utils.log('SEARCH:: Error getting Release Date: {0}'.format(e))

                    if not releaseDateMatch:
                        if FILMDICT['Year']:
                            utils.log(LOG_SUBLINE)
                            continue
                        else:
                            utils.log('SEARCH:: Error getting Site Release Date: Default to Filename Date')

                    # Site Film Duration
                    utils.log(LOG_BIGLINE)
                    matchedDuration = False
                    vDuration = FILMDICT['Duration']
                    try:
                        filmDuration = film.xpath('.//small[text()="length" or text()="run time"]/following-sibling::text()')[0].strip()
                        utils.log('SEARCH:: {0:<29} {1}'.format('Site Film Duration', filmDuration))
                        # convert to seconds format = 999 mins.
                        duration = filmDuration.split()[0]
                        duration = int(duration) * 60
                        duration = datetime.fromtimestamp(duration)
                        try:
                            utils.matchDuration(duration, AGENTDICT, FILMDICT)
                            matchedDuration = True
                            vDuration = duration
                        except Exception as e:
                            utils.log('SEARCH:: Error matching Site Film Duration: {0}'.format(e))
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Film Duration')

                    if matchedDuration is False and AGENTDICT['prefMATCHSITEDURATION'] is True:
                        utils.log(LOG_SUBLINE)
                        continue

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
