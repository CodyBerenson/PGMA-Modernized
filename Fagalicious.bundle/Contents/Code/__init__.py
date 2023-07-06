#!/usr/bin/env python
# encoding=utf8
'''
# Fagalicious - (IAFD)
                                    Version History
                                    ---------------
    Date            Version             Modification
    19 Aug 2022     2020.01.18.29   Multiple Improvements and major rewrites
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
                                    - removed trailers as they did not work
    02 Nov 2022     2020.01.18.30   Enclosed Search String in quotes as navigate to 2nd page of results was failing without it
    30 Nov 2022     2019.01.18.31   Updated to use latest version of utils.py
    28 Dec 2022     2019.01.18.32   removed quotes around search string
    29 Jan 2023     2019.01.18.33   Improved Logging
                                    corrected case of HTTP.Headers - was failing to download cast pics from iafd
                                    changed search string to improve scene retrieval
    09 Feb 2023     2019.01.18.34   removed checks for apostrophes in search string creation
    08 Mar 2023     2019.01.18.35   Added detection and removal of brackets from search string
    27 Apr 2023     2019.01.18.36   Corrections to Matching Film entries with apostrophes, cast retrieval from tags
    03 May 2023     2019.01.18.37   Corrections to Matching Film entries added typs of hyphens
    12 Jun 2023     2019.01.18.38   Corrections to Matching Film entries with 's in title
    20 Jun 2023     2019.01.18.39   Formatting for error messages updated
    25 Jun 2023     2019.01.18.40   Updated to use new utils.py - AGENTDICT
    01 Jul 2023     2019.01.18.41   Updated to use new utils.py

---------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2020.01.18.41'
AGENT = 'Fagalicious'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS
BASE_URL = 'https://fagalicious.com'
BASE_SEARCH_URL = BASE_URL + '/search/{0}'

# Date Format used by website
DATEFORMAT = '%B %d, %Y'

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
class Fagalicious(Agent.Movies):
    ''' define Agent class '''
    name = 'Fagalicious (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultScenes']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        utils.log('AGENT :: {0:<29} {1}'.format('Original Search Query', myString))

        myString = myString.lower().strip()

        # replace all full stops with double space
        if '.' in myString:
            myString = myString.replace('.', '  ')
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1} - {2}'.format('Removed Pattern', 'Full Stop', myString)))

        # remove brackets
        pattern = r' \(|\)|\[|\]|\{|\}'
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, ' ', myString)
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1} - {2}'.format('Removed Pattern', pattern, myString)))

        # remove single letters, ampersands, "and"
        pattern = r' & | and | [a-z] '
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            # first replace all spaces with double spaces in case you get the patterns following each other
            myString = myString.replace(' ', '  ')
            myString = re.sub(pattern, ' ', myString)
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1} - {2}'.format('Removed Pattern', pattern, myString)))

        # remove possesives - 's
        pattern = r"'s"
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, ' ', myString)
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1} - {2}'.format('Removed Pattern', pattern, myString)))

        # string can not be longer than 20 characters
        myString = ' '.join(myString.split())   # remove continous white space
        utils.log('AGENT :: {0:<29} {1}'.format('Search Query', myString))
        if len(myString) > 19:
            lastSpace = myString[:20].rfind(' ')
            myString = myString[:lastSpace]
            utils.log('AGENT :: {0:<29} {1}'.format('Shortened Search Query [Length]', '{0}: "{1} <= 20"'.format(myString[:lastSpace], lastSpace)))

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myString = myString.replace('%25', '%').replace('*', '').replace('%2A', '+')

        utils.log('AGENT :: {0:<29} {1}'.format('Returned Search Query', myString))
        utils.log(LOG_BIGLINE)

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            utils.log(LOG_ASTLINE)
            utils.log('SEARCH:: {0:<29} {1}'.format('Error: Missing Media Item File', 'QUIT'))
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
            utils.log('SEARCH:: {0:<29} {1}'.format('Erro: Could Not Set Agent Parameters', 'QUIT'))
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
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
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
                html = HTML.ElementFromURL(searchQuery, cacheTime=3, timeout=20, sleep=utils.delay())
                filmsList = html.xpath('//header[@class="entry-header"]')
                if not filmsList:
                    raise Exception('< No Scene Titles >')

                # if there is a list of films - check if there are further pages returned
                try:
                    searchQuery = html.xpath('//a[@class="next page-numbers"]/@href')[0]
                    morePages = True
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

                # Site Entry : Composed of Studio, then Scene Title separated by a Colon
                try:
                    filmEntry = film.xpath('./h1[@class="entry-title"]/a/text()')[0].strip()
                    filmEntry = utils.makeASCII(filmEntry)
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Entry', filmEntry))
                    filmStudio, filmTitle = filmEntry.split(': ', 1)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Entry: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Title
                utils.log(LOG_BIGLINE)
                try:
                    utils.matchTitle(filmTitle, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Title URL
                utils.log(LOG_BIGLINE)
                try:
                    filmURL = film.xpath('./h1[@class="entry-title"]/a/@href')[0]
                    filmURL = ('' if BASE_URL in filmURL else BASE_URL) + filmURL
                    FILMDICT['FilmURL'] = filmURL
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', filmURL))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title URL: {0}'.format(e))
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

                # Site Release Date: Format Month, dd YYYY
                utils.log(LOG_BIGLINE)
                vReleaseDate = FILMDICT['CompareDate']
                try:
                    filmReleaseDate = film.xpath('.//li[@class="meta-date"]/a/text()')[0]
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Release Date', filmReleaseDate))
                    try:
                        releaseDate = datetime.strptime(filmReleaseDate, DATEFORMAT)
                        utils.matchReleaseDate(releaseDate, FILMDICT)
                        vReleaseDate = releaseDate
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site URL Release Date: {0}'.format(e))
                        if FILMDICT['Year']:
                            utils.log(LOG_SUBLINE)
                            continue
                except:
                    utils.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')

                FILMDICT['vCompilation'] = ''
                FILMDICT['vDuration'] = ''
                FILMDICT['vReleaseDate'] = vReleaseDate

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
        return utils.updateMetadata(metadata, media, lang, force=True)
