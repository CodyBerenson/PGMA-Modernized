#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# BestExclusivePorn - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    09 Aug 2020     2020.08.09.01  Creation
    07 Sep 2020     2020.08.09.02  Improved matching on film titles with apostrophes
                                   added cast scraping - actors restricted to 2 names
    15 Sep 2020     2020.08.09.03  removed enquotes around search string
    25 Sep 2020     2020.08.09.04  search string can only have a max of 59 characters
    07 Oct 2020     2020.08.09.05  IAFD - change to https
                                   get cast names from statting label if present
    22 Nov 2020     2020.08.09.06  leave words attached to commas in search string
    23 Dec 2020     2020.08.09.07  Save film in Title Case mode... as this agent detects actor names from the title as they have initial caps
    26 Dec 2020     2020.08.09.08  Improved on IAFD search, actors sexual roles if recorded are returned, if not shows a red circle.
                                   if actor is not credited on IAFD but is on Agent Site it shows as a Yellow Box below the actor
                                   sped up search by removing search by actor/director... less hits on IAFD per actor...
    28 Feb 2021     2020.08.09.10  Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including Levenshtein Matching on Cast names
                                   Added iafd legend to summary
    11 May 2021     2020.08.09.11  Further code reorganisation
    30 May 2021     2020.08.09.12  Further code reorganisation
    04 Feb 2022     2020.08.09.13  implemented change suggested by Cody: duration matching optional on IAFD matching
                                   Cast list if used in filename becomes the default that is matched against IAFD, useful in case no cast is listed in agent
    03 Mar 2022     2020.08.09.14  BASE URL changed from http: to https:
    19 Aug 2022     2020.08.09.15  Multiple Improvements and major rewrites
                                   - tidy up of genres as they have different names across various websites.
                                   - tidy up of countries and locations
                                   - introduced Grouped Collections and Default to keep track of films
-----------------------------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2020.08.09.15'
AGENT = 'BestExclusivePorn'

# Date Format used by website
DATEFORMAT = '%B %d, %Y'

# URLS
BASE_URL = 'https://bestexclusiveporn.com/'
BASE_SEARCH_URL = BASE_URL + '?s={0}'

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
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
                # Finds the entire media enclosure
                filmsList = html.xpath('//div[contains(@class,"type-post status-publish")]')
                if not filmsList:
                    raise Exception('< No Films! >')
            except Exception as e:
                utils.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                break

            try:
                searchQuery = html.xpath('//a[@class="next page-numbers"]/@href')[0]
                utils.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(searchQuery.split('?')[0].split('/')[-1]) - 1
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

                # Site Entry
                try:
                    filmEntry = film.xpath('./h2[@class="title"]/a/text()')[0]
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Entry', filmEntry))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Entry: %s', e)
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
                    utils.log('SEARCH:: Error getting Site Title: %s', e)
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
                    utils.log('SEARCH:: Error getting Site Title Url: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # Studio Name
                utils.log(LOG_BIGLINE)
                try:
                    utils.matchStudio(filmStudio, FILMDICT)
                    utils.log(LOG_BIGLINE)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Studio: %s', e)
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
                        utils.log('SEARCH:: Error getting Site URL Release Date: %s', e)
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
                        utils.matchDuration(duration, FILMDICT)
                        matchedDuration = True
                        vDuration = duration
                    except Exception as e:
                        utils.log('SEARCH:: Error matching Site Film Duration: %s', e)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Film Duration')

                if MATCHSITEDURATION and not matchedDuration:
                    utils.log(LOG_SUBLINE)
                    continue

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
                utils.log('SEARCH:: Access Site URL Link:')
                FILMDICT[AGENT] = utils.getSiteInfo(AGENT, FILMDICT, kwReleaseDate=vReleaseDate, kwDuration=vDuration)

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