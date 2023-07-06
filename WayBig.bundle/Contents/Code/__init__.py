#!/usr/bin/env python
# encoding=utf8
'''
# WayBig (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    19 Aug 2022     2019.08.12.36   Multiple Improvements and major rewrites
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
    30 Nov 2022     2019.08.12.37   Updated to use latest version of utils.py
    29 Jan 2023     2019.08.12.38   Improved Logging
                                    changed processing of & character in search string
    08 Mar 2023     2019.08.12.39   Corrections to matching film entries - issues with square brackets in title
    27 Apr 2023     2019.08.12.40   Corrections to Matching Film entries with apostrophes, cast retrieval from tags
    03 May 2023     2019.08.12.41   Corrections to Matching Film entries added typs of hyphens
    20 Jun 2023     2019.08.12.42   Formatting for error messages updated
    25 Jun 2023     2019.08.12.43   Updated to use new utils.py - AGENTDICT
                                    Issue 257 - matching titles with bullets in name
    01 Jul 2023     2019.08.12.44   Updated utils.py - new image xpath string
    ---------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2019.12.22.44'
AGENT = 'WayBig'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS
BASE_URL = 'https://www.waybig.com'
BASE_SEARCH_URL = BASE_URL + '/blog/index.php?s={0}'

# Date Formats used by website
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
class WayBig(Agent.Movies):
    ''' define Agent class '''
    name = 'WayBig (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultScenes']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        '''  clean search string before searching on WayBig '''
        utils.log('AGENT :: {0:<29} {1}'.format('Original Search Query', myString))

        myString = myString.lower().strip()

        # for titles with "- " replace with ":"
        pattern = ' - |- '
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, ': ', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Replaced {0} with ": "', pattern)))

        # replace ampersand with nothing
        pattern = u' & '
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, '  ', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Removed Pattern', pattern)))

        # remove all apostrophes with straight as strip diacritics will remove these, include back ticks 
        quoteChars = ["'", '"']
        pattern = u'({0})'.format('|'.join(quoteChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, ' ', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Removed Pattern', pattern)))

        # string can not be longer than 50 characters
        if len(myString) > 50:
            lastSpace = myString[:51].rfind(' ')
            myString = myString[:lastSpace]
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: "{1} <= 50"'.format('Search Query Length', lastSpace)))
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: "{1}"'.format('Shorten Search Query', myString[:lastSpace])))

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

        # strip studio name from title to use in comparison
        regex = ur'^{0} |at {0}$'.format(re.escape(FILMDICT['CompareStudio']))
        pattern = re.compile(regex, re.IGNORECASE)
        compareTitle = re.sub(pattern, '', searchTitle)
        compareTitle = utils.Normalise(compareTitle)

        utils.log('SEARCH:: {0:<29} {1}'.format('Search Title', searchTitle))

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
                filmsList = html.xpath('.//div[@class="row"]/div[@class="content-col col"]/article')
                if not filmsList:
                    raise Exception('< No Scene Titles >')

                # if there is a list of films - check if there are further pages returned
                try:
                    searchQuery = html.xpath('//div[@class="nav-links"]/a[@class="next page-numbers"]/@href')[0]
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
                    filmEntry = film.xpath('./a/*[@class="entry-title"]/text()')[0].strip()
                    filmEntry = utils.makeASCII(filmEntry)
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Entry', filmEntry))
                    filmEntry = r'{0}'.format(filmEntry)
                    # the filmEntry usual has the format Studio: Title
                    if ' at ' in filmEntry.lower() and ': ' in filmEntry and (filmEntry.endswith("'") or filmEntry.endswith('"')):  # err 123
                        utils.log('SEARCH:: Matched " at ", ": " and {0} ends with apostrophe in Site entry'.format(re.match(filmEntry, '[\'"]$')))
                        filmStudio, filmTitle = filmEntry.split(': ', 1)

                    elif re.search(r' at ', filmEntry, flags=re.IGNORECASE):                # format:- Title at Studio
                        utils.log('SEARCH:: Matched " at " in Site entry')
                        filmTitle, filmStudio = re.split(r' at ', filmEntry, flags=re.IGNORECASE, maxsplit=1)

                    elif FILMDICT['Title'] in filmEntry:                                    # format:- Studio Title (Title has colon)
                        filmTitle = FILMDICT['Title']
                        filmStudio = filmEntry.replace(filmTitle, '').strip()

                    elif ': ' in filmEntry:                                                 # format:- Studio: Title
                        utils.log('SEARCH:: Matched ": " in Site entry')
                        filmStudio, filmTitle = filmEntry.split(': ', 1)

                    elif ' on ' in filmEntry.lower():                                       # format:- Title on Studio
                        utils.log('SEARCH:: Matched " on " in Site entry')
                        filmTitle, filmStudio = re.split(r' on ', filmEntry, flags=re.IGNORECASE, maxsplit=1)

                    elif '? ' in filmEntry:                                                 # format:- Studio? Title
                        utils.log('SEARCH:: Matched "? " in Site entry')
                        filmStudio, filmTitle = filmEntry.split('? ', 1)

                    elif ', ' in filmEntry:                                                 # format: Studio, Title
                        utils.log('SEARCH:: Matched ", " in Site entry')
                        filmStudio, filmTitle = filmEntry.split(', ', 1)

                    elif FILMDICT['Studio'].lower() in filmEntry.lower():                   # format:- Studio Title {no separtor}
                        utils.log('SEARCH:: Warning: Site Entry did not have a clear separator to separate Studio from Title')
                        filmStudio = FILMDICT['Studio']
                        pattern = r'{0}'.format(filmStudio)
                        filmTitle = re.sub(pattern, '', filmEntry, re.IGNORECASE).strip()
                    else:
                        utils.log('SEARCH:: Error determining Site Studio and Title from Site Entry')
                        utils.log(LOG_SUBLINE)
                        continue

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

                # Site Studio Name
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
                    filmURL = film.xpath('./a[@rel="bookmark"]/@href')[0]
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
                    filmReleaseDate = film.xpath('./div/span[@class="meta-date"]/strong/text()[normalize-space()]')[0]
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
