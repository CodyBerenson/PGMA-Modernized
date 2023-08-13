#!/usr/bin/env python
# encoding=utf8
'''
# BestExclusivePorn - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    19 Aug 2022     2020.08.09.15  Multiple Improvements and major rewrites
                                   - tidy up of genres as they have different names across various websites.
                                   - tidy up of countries and locations
                                   - introduced Grouped Collections and Default to keep track of films
    30 Nov 2022     2020.08.09.16   Updated to use latest version of utils.py
    29 Jan 2023     2020.08.09.17   Improved Logging
    27 Apr 2023     2020.08.09.18   Corrections to Matching Film entries with apostrophes, cast retrieval from tags
    10 May 2023     2020.08.09.19   Corrections to Matching Film entries added typs of hyphens
    20 Jun 2023     2020.08.09.20   Formatting for error messages updated
    25 Jun 2023     2020.08.09.21   Updated to use new utils.py - AGENTDICT
    01 Jul 2023     2020.08.09.22   Updated to use new utils.py
    12 Aug 2023     2020.08.09.23   Updated utils.matchduration call to use AGENTDICT

---------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2020.08.09.23'
AGENT = 'BestExclusivePorn'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# Date Format used by website
DATEFORMAT = '%B %d, %Y'

# URLS
BASE_URL = 'https://bestexclusiveporn.com/'
BASE_SEARCH_URL = BASE_URL + '?s={0}'

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
class BestExclusivePorn(Agent.Movies):
    ''' define Agent class '''
    name = 'BestExclusivePorn (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms', 'com.plexapp.agents.GayAdultScenes']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        utils.log('AGENT :: {0:<29} {1}'.format('Original Search Query', myString))

        # convert to lower case and trim
        myString = myString.lower().strip()

        # remove words with apostrophes in them
        badChars = ["'", ur'\u2018', ur'\u2019', '-']
        pattern = u"\w*[{0}]\w*".format(''.join(badChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, '', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Removed Pattern', pattern)))

        # Best Exclusive uses a maximum of 49 characters when searching
        myString = myString[:49].strip()
        myString = myString if myString[-1] != '%' else myString[:48]

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())
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
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=utils.delay())
                # Finds the entire media enclosure
                filmsList = html.xpath('//div[contains(@class,"type-post status-publish")]')
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

                # Site Entry
                try:
                    filmEntry = film.xpath('./h2[@class="title"]/a/text()')[0]
                    filmEntry = utils.makeASCII(filmEntry)
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Entry', filmEntry))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Entry: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # normalise site entry and film title
                filmEntry = utils.Normalise(filmEntry)
                normalisedFilmTitle = utils.Normalise(FILMDICT['Title'])
                pattern = ur'{0}'.format(normalisedFilmTitle)
                matched = re.search(pattern, filmEntry, re.IGNORECASE)  # match against whole string
                if matched:
                    filmTitle = matched.group()
                    filmStudio = re.sub(pattern, '', filmEntry).strip()
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Entry: Studio - Title', '{0} - {1}'.format(filmStudio, filmTitle)))
                else:
                    utils.log('SEARCH:: Failed to get Studio and Title from Site Entry:')
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
                    filmURL = film.xpath('./h2[@class="title"]/a/@href')[0]
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
                    utils.matchStudio(filmStudio, FILMDICT)
                    utils.log(LOG_BIGLINE)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Studio: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Release Date - use date added to Best Exclusive Porn Website
                utils.log(LOG_BIGLINE)
                try:
                    filmReleaseDate = film.xpath('./div[@class="post-info-top"]/span[@class="post-info-date"]/a[@rel="bookmark"]/text()')[0].strip()
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

                # Site Film Duration - format hh:mm:ss
                utils.log(LOG_BIGLINE)
                matchedDuration = False
                vDuration = FILMDICT['Duration']
                try:
                    filmDuration = film.xpath('.//div[@class="entry"]/p/text()[contains(.,"Duration:")]')[0].strip().replace('Duration: ', '')
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Film Duration', filmDuration))
                    filmDuration = filmDuration.split(':')
                    filmDuration = [int(x.strip()) for x in filmDuration if x.strip()]
                    duration = filmDuration[0] * 3600 + filmDuration[1] * 60 + filmDuration[2]                       # convert to seconds
                    duration = datetime.fromtimestamp(duration)
                    try:
                        utils.matchDuration(duration, AGENTDICT, FILMDICT)
                        matchedDuration = True
                        vDuration = duration
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Film Duration: {0}'.format(e))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Film Duration')

                if AGENTDICT['prefMATCHSITEDURATION'] is True and matchedDuration is False:
                    utils.log(LOG_SUBLINE)
                    continue

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
