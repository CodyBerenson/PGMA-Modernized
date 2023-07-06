#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# QueerClick - (IAFD)
                                    Version History
                                    ---------------
    Date            Version             Modification
    19 Aug 2022     2020.02.14.23   Multiple Improvements and major rewrites
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
    30 Nov 2022     2020.02.14.24   Updated to use latest version of utils.py
    29 Jan 2023     2020.02.14.25   Improved Logging
    08 Feb 2023     2020.02.14.26   Corrected Search String process - was trimming after url encoding
    27 Apr 2023     2020.02.14.27   Corrections to Matching Film entries with apostrophes, cast retrieval from tags
    03 May 2023     2020.02.14.28   Corrections to Matching Film entries added typs of hyphens
    20 Jun 2023     2020.02.14.29   Formatting for error messages updated
    25 Jun 2023     2020.02.14.30   Updated to use new utils.py - AGENTDICT
    01 Jul 2023     2020.02.14.31   Updated to use new utils.py

---------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2020.02.14.31'
AGENT = 'QueerClick'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS
BASE_URL = 'https://www.queerclick.com'
BASE_SEARCH_URL = BASE_URL + '/?s={0}'

# Date Formats used by website
DATEFORMAT = '%d %b %y'

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
class QueerClick(Agent.Movies):
    ''' define Agent class '''
    name = 'QueerClick (IAFD)'
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

        spaceChars = [',', '-', ur'\u2011', ur'\u2012', ur'\u2013', ur'\u2014'] # for titles with commas, colons in them on disk represented as ' - '
        pattern = u'({0})'.format('|'.join(spaceChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, ' ', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Removed Pattern', pattern)))

        # QueerClick seems to fail to find Titles which have invalid chars in them split at first incident and take first split, just to search but not compare
        badChars = ["'", '"']
        pattern = u'({0})'.format('|'.join(badChars))

        # check that title section of string does not start with a bad character, if it does remove studio from search string
        matched = re.search(pattern, myString[0])  # match against first character
        if matched:
            myString = myString[1:]
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Dropped 1st Char', myString[0])))
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Found Pattern', pattern)))

        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            badPos = matched.start()
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Crop at', badPos)))
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Found Pattern', pattern)))
            myString = myString[:badPos]

        # string can not be longer than 50 characters and enquote
        if len(myString) > 50:
            lastSpace = myString[:51].rfind(' ')
            utils.log('sssssssssss  %s', lastSpace)
            myString = myString[:lastSpace]
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: "{1} <= 50"'.format('Search Query Length', lastSpace)))
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: "{1}"'.format('Shorten Search Query', myString[:lastSpace])))

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myString = myString.replace('%25', '%').replace('*', '')

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

        # strip studio name from title to use in comparison
        regex = ur'^{0} |at {0}$'.format(re.escape(FILMDICT['CompareStudio']))
        pattern = re.compile(regex, re.IGNORECASE)
        compareTitle = re.sub(pattern, '', searchTitle)
        compareTitle = utils.Normalise(compareTitle)

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
                filmsList = html.xpath('.//article[@id and @class]')
                if not filmsList:
                    raise Exception('< No Scene Titles >')

                # if there is a list of films - check if there are further pages returned
                try:
                    searchQuery = html.xpath('//div[@class="pagination post"]/span[@class="right"]/a/@href')[0]
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

                # Site Entry
                try:
                    filmEntry = film.xpath('./h2[@class="entry-title"]/a/text()')[0]
                    filmEntry = utils.makeASCII(filmEntry)
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Entry', filmEntry))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Entry: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # the filmEntry usual has the format Studio: Title
                if ':' in filmEntry:
                    filmStudio, filmTitle = filmEntry.split(': ', 1)
                else: # on very old entries it was Title [at|on] Studio
                    filmEntry = filmEntry.split()
                    if filmEntry[-2].lower() == 'at' or filmEntry[-2].lower() == 'on':
                        filmStudio = [-1]
                        filmTitle = ''.join(filmEntry[0:-2])
                    else:
                        utils.log('SEARCH:: Error determining Site Studio and Title from Site Entry')
                        continue

                # Site Title
                utils.log(LOG_BIGLINE)
                try:
                    filmTitle = filmTitle.strip()
                    pattern = ur'[^a-zA-Z0-9] [A-Z0-9!% ]*[!|%]$'           # pattern start with Hyphen followed by Capital letters,%,! but has to end with exclamation or percent
                    matched = re.search(pattern, filmTitle, re.UNICODE)     # match against whole string
                    filmTitle = re.sub(pattern, '', filmTitle).strip() if matched else filmTitle
                    utils.matchTitle(filmTitle, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Studio Name
                utils.log(LOG_BIGLINE)
                try:
                    utils.matchStudio(filmStudio, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Studio: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Title URL
                utils.log(LOG_BIGLINE)
                try:
                    filmURL = film.xpath('./h2[@class="entry-title"]/a/@href')[0]
                    filmURL = ('' if BASE_URL in filmURL else BASE_URL) + filmURL
                    FILMDICT['FilmURL'] = filmURL
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', filmURL))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title URL: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Release Date
                utils.log(LOG_BIGLINE)
                try:
                    filmReleaseDate = film.xpath('./div[@class="postdetails"]/span[@class="date updated"]/text()[normalize-space()]')[0]
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
                    vReleaseDate = FILMDICT['CompareDate']

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
