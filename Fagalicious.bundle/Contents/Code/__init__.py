#!/usr/bin/env python
# encoding=utf8
'''
# Fagalicious - (IAFD)
                                    Version History
                                    ---------------
    Date            Version             Modification
    22 Dec 2019     2020.01.18.1    Creation
    19 Apr 2020     2020.01.18.9    Corrected image cropping
                                    added new xpath for titles with video image as main image
                                    improved multiple result pages handling
                                    removed debug print option
    29 Apr 2020     2020.01.18.10   updated IAFD routine, corrected error in multiple page processing
    01 Jun 2020     2020.01.18.11   Implemented translation of summary
                                    improved getIAFDActor search
    25 Jun 2020     2020.01.18.12   Improvement to Summary Translation: Translate into Plex Library Language
                                    stripping of intenet domain suffixes from studio names when matching
                                    handling of unicode characters in film titles and comparision string normalisation
    04 Feb 2022     2020.01.18.26   implemented change suggested by Cody: duration matching optional on IAFD matching
                                    Cast list if used in filename becomes the default that is matched against IAFD, useful in case no cast is listed in agent
    04 Feb 2022     2020.01.18.27   CodeAnator Suggestion: Updated fagalicious genre list to avoid false actor detection
    20 Mar 2022     2020.01.18.28   CodeAnator: Implemented Extras:Trailers
    19 Aug 2022     2020.01.18.29   Multiple Improvements and major rewrites
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
                                    - removed trailers as they did not work
    02 Nov 2022     2020.01.18.30   Enclosed Search String in quotes as navigate to 2nd page of results was failing without it
-----------------------------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2020.01.18.30'
AGENT = 'Fagalicious'

# URLS
BASE_URL = 'https://fagalicious.com'
BASE_SEARCH_URL = BASE_URL + '/search/{0}'

# Date Format used by website
DATEFORMAT = '%B %d, %Y'

# Website Language
SITE_LANGUAGE = 'en'

# Preferences
COLCAST = Prefs['castcollection']                   # add cast to collection
COLCOUNTRY = Prefs['countrycollection']             # add country to collection
COLDIRECTOR = Prefs['directorcollection']           # add director to collection
COLGENRE = Prefs['genrecollection']                 # add genres to collection
COLSTUDIO = Prefs['studiocollection']               # add studio name to collection
COLSERIES = Prefs['seriescollection']               # add series to collection
DELAY = int(Prefs['delay'])                         # Delay used when requesting HTML, may be good to have to prevent being banned from the site
DETECT = Prefs['detect']                            # detect the language the summary appears in on the web page
DURATIONDX = int(Prefs['durationdx'])               # Acceptable difference between actual duration of video file and that on agent website
GROUPCOL = Prefs['groupcollections']                # group collections by Genre, Directors, and Cast
MATCHIAFDDURATION = Prefs['matchiafdduration']      # Match against IAFD Duration value
MATCHSITEDURATION = Prefs['matchsiteduration']      # Match against Site Duration value
PREFIXLEGEND = Prefs['prefixlegend']                # place cast legend at start of summary or end
RESETMETA = Prefs['resetmeta']                      # clear previously set metadata
USEBACKGROUNDART = Prefs['usebackgroundart']        # Use background art

# dictionaries & Set for holding film variables, genres and countries
FILMDICT = {}
TIDYDICT = {}
COUNTRYSET = set()

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
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'
    utils.setupStartVariables()
    ValidatePrefs()

# ----------------------------------------------------------------------------------------------------------------------------------
def ValidatePrefs():
    ''' Validate Changed Preferences '''
    pass

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

        # replace ampersand with nothing
        pattern = u'&'
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, '', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Removed Pattern', pattern)))

        # replace curly single apostrophes with straight quote
        singleQuoteChars = [ur'\u2018', ur'\u2019']
        pattern = u'({0})'.format('|'.join(singleQuoteChars))
        matchedSingleQuote = re.search(pattern, myString)  # match against whole string
        if matchedSingleQuote:
            myString = re.sub(pattern, "'", myString)
            myString = ' '.join(myString.split())   # remove continous white space
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Removed Pattern', pattern)))

        # Fagalicious seems to fail to find Titles which have invalid chars in them split at first incident and take first split, just to search but not compare
        # the back tick is added to the list as users who can not include quotes in their filenames can use these to replace them without changing the scrappers code
        badChars = ['"', '`', ur'\u201c', ur'\u201d', ur'\u2018', ur'\u2019']
        pattern = u'({0})'.format('|'.join(badChars))
        matched = re.search(pattern, myString[0])  # match against first character
        if matched:
            myString = myString[1:]
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Dropped 1st Word', myString[0])))
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Found Pattern', pattern)))

        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            badPos = matched.start()
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Crop at', badPos)))
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Found Pattern', pattern)))
            myString = myString[:badPos]

        # string can not be longer than 20 characters and enquote
        if len(myString) > 19:
            lastSpace = myString[:20].rfind(' ')
            myString = myString[:lastSpace]
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: "{1} <= 20"'.format('Search Query Length', lastSpace)))
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: "{1}"'.format('Shorten Search Query', myString[:lastSpace])))

        myString = '"{0}"'.format(myString)
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
            utils.log('SEARCH:: {0:<29} {1}'.format('Error: Missing Media Item File', 'QUIT'))
            return

        #clear-cache directive
        if media.name == "clear-cache":  
            HTTP.ClearCache()
            results.Append(MetadataSearchResult(id='clear-cache', name='Plex web cache cleared', year=media.year, lang=lang, score=0))
            utils.log('SEARCH:: {0:<29} {1}'.format('Warning: Clear Cache Directive Encountered', 'QUIT'))
            return

        utils.logHeader('SEARCH', media, lang)

        # Check filename format
        try:
            FILMDICT = utils.matchFilename(media)
            FILMDICT['lang'] = lang
            FILMDICT['Agent'] = AGENT
        except Exception as e:
            utils.log('SEARCH:: Error: %s', e)
            return

        utils.log(LOG_BIGLINE)

        # Search Query - for use to search the internet, remove all non alphabetic characters etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        morePages = True
        while morePages:
            utils.log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, cacheTime=3, timeout=20, sleep=10)
                filmsList = html.xpath('//header[@class="entry-header"]')
                if not filmsList:
                    raise Exception('< No Films! >')
            except Exception as e:
                utils.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                break

            try:
                searchQuery = html.xpath('//a[@class="next page-numbers"]/@href')[0]
                utils.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(html.xpath('//span[@class="page-numbers current"]/text()[normalize-space()]')[0])
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

                # Site Entry : Composed of Studio, then Scene Title separated by a Colon
                try:
                    filmEntry = film.xpath('./h1[@class="entry-title"]/a/text()')[0]
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Entry', filmEntry))
                    filmStudio, filmTitle = filmEntry.split(": ", 1)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Entry: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Title
                utils.log(LOG_BIGLINE)
                try:
                    utils.matchTitle(filmTitle, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # Studio Name
                utils.log(LOG_BIGLINE)
                try:
                    utils.matchStudio(filmStudio, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Studio: %s', e)
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
                    utils.log('SEARCH:: Error getting Site Title Url: %s', e)
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
                        utils.log('SEARCH:: Error getting Site URL Release Date: %s', e)
                        if FILMDICT['Year']:
                            utils.log(LOG_SUBLINE)
                            continue
                except:
                    utils.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')

                # Access Site URL
                utils.log(LOG_BIGLINE)
                try:
                    utils.log('SEARCH:: {0:<29} {1}'.format('Reading Site URL page', filmURL))
                    fhtml = HTML.ElementFromURL(FILMDICT['FilmURL'], sleep=DELAY)
                    FILMDICT['FilmHTML'] = fhtml
                except Exception as e:
                    utils.log('SEARCH:: Error reading Site URL page: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # use general routine to get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information
                utils.log(LOG_BIGLINE)
                try:
                    utils.log('SEARCH:: Access Site URL Link:')
                    FILMDICT[AGENT] = utils.getSiteInfo(AGENT, FILMDICT, kwReleaseDate=vReleaseDate)
                except Exception as e:
                    utils.log('SEARCH:: Error Accessing Site URL page: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # we should have a match on studio, title and year now. Find corresponding film on IAFD
                utils.log(LOG_BIGLINE)
                utils.log('SEARCH:: Check for Film on IAFD:')
                utils.getFilmOnIAFD(FILMDICT)

                FILMDICT['id'] = media.id
                myID = json.dumps(FILMDICT, default=utils.jsonDumper)
                results.Append(MetadataSearchResult(id=myID, name=FILMDICT['Title'], score=100, lang=lang))

                # Film Scraped Sucessfully - update status and break out!
                FILMDICT['Status'] = True
                break       # stop processing

            if FILMDICT['Status']:      # if search and process sucessful stop processing
                break

        # End Search Routine
        utils.logFooter('SEARCH', FILMDICT)
        return FILMDICT['Status']

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        utils.logHeader('UPDATE', media, lang)

        utils.log('UPDATE:: Convert Date Time & Set Objects:')
        FILMDICT = json.loads(metadata.id, object_hook=utils.jsonLoader)
        utils.log(LOG_BIGLINE)

        utils.printFilmInformation(FILMDICT)
        utils.log(LOG_BIGLINE)

        utils.setMetadata(metadata, FILMDICT)

        utils.logFooter('UPDATE', FILMDICT)
        return FILMDICT['Status']