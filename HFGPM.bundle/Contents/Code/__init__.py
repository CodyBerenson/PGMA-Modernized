#!/usr/bin/env python
# encoding=utf8
'''
# HFGPM - (IAFD): Hot Free Gay Porn Movies
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    19 Aug 2022     2021.11.15.04  Multiple Improvements and major rewrites
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
    05 Dec 2022     2021.11.15.05   Updated to use latest version of utils.py
    19 Feb 2023     2021.11.15.06   Corrected multiple errors processing site entries
    26 Feb 2023     2021.11.15.07   Corrected error processing file titles
    13 Jul 2023     2021.11.15.08   Updated to use latest version of utils.py

-----------------------------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2021.11.15.08'
AGENT = 'HFGPM'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS
BASE_URL = 'https://gay-hotfile.errio.net/'
BASE_SEARCH_URL = BASE_URL + 'index.php?do=search'

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
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-Agent'] = utils.getUserAgent()

# ----------------------------------------------------------------------------------------------------------------------------------
class HFGPM(Agent.Movies):
    ''' define Agent class '''
    name = 'HFGPM (IAFD)'
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

        # Search Query - for use to search the internet
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL

        # Here are all of our headers
        formData = {'do': 'search', 'subaction': 'search', 'search_start': 1, 'full_search': 1, 'story': '{0}'.format(searchTitle),
                    'titleonly': 3, 'searchuser': '', 'replyless': 0, 'replylimit': 0, 'searchdate': 0, 'beforeafter': 'after', 'sortby': 'date',
                    'resorder': 'desc', 'result_num': 500, 'result_from': 1, 'showposts': 0, 'catlist[]': 0}

        utils.log('SEARCH:: Search Query: {0}'.format(formData))
        try:
            html = HTML.ElementFromURL(searchQuery, values=formData, headers=formData, timeout=20, sleep=utils.delay())
            # Finds the entire media enclosure
            filmsList = html.xpath('//div[@class="base shortstory"]')
            if not filmsList:
                raise Exception('< No Films! >')

        except Exception as e:
            utils.log('SEARCH:: Error: Search Query did not pull any results: {0}'.format(e))

        else:
            filmsFound = len(filmsList)
            pageNumber = 1          # no need to increment as the agent returns up to 500 items
            utils.log('SEARCH:: {0:<29} {1}'.format('Titles Found', '{0} Processing Results Page: {1:>2}'.format(filmsFound, pageNumber)))
            utils.log(LOG_BIGLINE)
            myYear = '({0})'.format(FILMDICT['Year']) if FILMDICT['Year'] else ''
            for idx, film in enumerate(filmsList, start=1):
                utils.log('SEARCH:: {0:<29} {1}'.format('Processing', '{0} of {1} for {2} - {3} {4}'.format(idx, filmsFound, FILMDICT['Studio'], FILMDICT['Title'], myYear)))
                utils.log(LOG_BIGLINE)

                # Site Entry
                try:
                    filmEntry = film.xpath('./div[@class="bshead"]/div[@class="bshead"]/h1/a/text()')[0]
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Entry', filmEntry))
                    filmEntry = filmEntry.partition(' - ') # converts to tuple
                    if filmEntry[1] != ' - ':
                        utils.log('SEARCH:: Error in Site Entry Format')
                        utils.log(LOG_SUBLINE)
                        continue
                    filmStudio = filmEntry[0]
                    filmTitle = filmEntry[2]
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Entry: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Title
                utils.log(LOG_BIGLINE)
                try:
                    filmTitle = filmTitle.replace(str(FILMDICT['Year']), '')
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
                    filmURL = film.xpath('./div[@class="bshead"]/div[@class="bshead"]/h1/a/@href')[0]
                    FILMDICT['FilmURL'] = filmURL
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', filmURL))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title Url: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Release Date, formatted as dd-mm-yyyy, hh:mm
                utils.log(LOG_BIGLINE)
                try:
                    filmreleasedate = film.xpath('./div[@class="base shortstory"]/div[@class="maincont"]/div/text()[contains(.,"Release Year:")]')[0].strip()
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Release Date', filmreleasedate))
                    try:
                        releaseDate = datetime.strptime(filmreleasedate, DATEFORMAT)
                        utils.matchReleaseDate(releaseDate, FILMDICT)
                        vReleaseDate = releaseDate
                    except Exception as e:
                        if FILMDICT['Year']:
                            utils.log(LOG_SUBLINE)
                            continue
                except:
                    utils.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                    vReleaseDate = FILMDICT['CompareDate'] if FILMDICT['CompareDate'] else None

                # Site Film Duration - formatted as 99h 99mn 99sc 999ms 
                utils.log(LOG_BIGLINE)
                matchedDuration = False
                vDuration = FILMDICT['Duration']
                try:
                    filmduration = html.xpath('./div[@class="base shortstory"]/div[@class="maincont"]/div/text()[contains(.,"mn ")]')[0].strip()
                    durationM = filmduration.partition('mn ')
                    durationH = filmduration.partition('h ')
                    duration = int(durationH[0]) * 60 + int(durationM[1])
                    duration = duration * 60                                                         # convert to seconds
                    duration = datetime.fromtimestamp(duration)
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Film Duration', duration.strftime('%H:%M:%S')))
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
