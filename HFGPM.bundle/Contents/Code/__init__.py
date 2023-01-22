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

-----------------------------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2021.11.15.05'
AGENT = 'HFGPM'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS
WATERMARK = 'https://cdn0.iconfinder.com/data/icons/mobile-device/512/lowcase-letter-d-latin-alphabet-keyboard-2-32.png'

# Date Formats used by website
DATEFORMAT = '%d-%m-%Y'

# Website Language
SITE_LANGUAGE = 'en'

# Preferences
MATCHSITEDURATION = ''

# dictionaries & Set for holding film variables, genres and countries
FILMDICT = {}

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
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'

    utils.setupStartVariables()
    ValidatePrefs()

# ----------------------------------------------------------------------------------------------------------------------------------
def ValidatePrefs():
    ''' Validate Changed Preferences '''
    pass

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

        # Search Query - for use to search the internet
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL
        # Here are all of our headers
        formData = {'do': 'search', 'subaction': 'search', 'search_start': 1, 'full_search': 1, 'story': '{0}'.format(searchTitle),
                    'titleonly': 3, 'searchuser': '', 'replyless': 0, 'replylimit': 0, 'searchdate': 0, 'beforeafter': 'after', 'sortby': 'date',
                    'resorder': 'desc', 'result_num': 500, 'result_from': 1, 'showposts': 0, 'catlist[]': 0}

        utils.log('SEARCH:: Search Query: %s', formData)
        try:
            html = HTML.ElementFromURL(searchQuery, values=formData, headers=formData, timeout=20, sleep=utils.delay())
            # Finds the entire media enclosure
            filmsList = html.xpath('//div[@class="base shortstory"]')
            if not filmsList:
                raise Exception('< No Films! >')

        except Exception as e:
            utils.log('SEARCH:: Error: Search Query did not pull any results: %s', e)

        else:
            filmsFound = len(filmsList)
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
                    if not filmEntry[1]:
                        utils.log('SEARCH:: Error in Site Entry Format')
                        utils.log(LOG_SUBLINE)
                        continue
                    filmTitle = filmEntry[2]
                    filmStudio = filmEntry[0]
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Title
                utils.log(LOG_BIGLINE)
                try:
                    filmTitle = filmTitle.replace(FILMDICT['Year'], '') if FILMDICT['Year'] in filmTitle else filmTitle
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
                    filmURL = title.xpath('./div[@class="bshead"]/div[@class="bshead"]/h1/a/@href')[0]
                    FILMDICT['FilmURL'] = filmURL
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', filmURL))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title Url: %s', e)
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
                        utils.log('SEARCH:: Error matching Site Film Duration: %s', e)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Film Duration')

                if MATCHfilmduration and not matchedDuration:
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
        utils.logHeader('UPDATE', media, lang)

        utils.log('UPDATE:: Convert Date Time & Set Objects:')
        FILMDICT = json.loads(metadata.id, object_hook=utils.jsonLoader)
        utils.log(LOG_BIGLINE)

        utils.printFilmInformation(FILMDICT)

        FILMDICT['Status'] = True

        # use general routine to get Metadata
        utils.log(LOG_BIGLINE)
        try:
            utils.log('SEARCH:: Access Site URL Link:')
            fhtml = HTML.ElementFromURL(FILMDICT['FilmURL'], sleep=utils.delay())
            FILMDICT['FilmHTML'] = fhtml
            FILMDICT[AGENT] = utils.getSiteInfo(AGENT, FILMDICT, kwCompilation=FILMDICT['vCompilation'], kwReleaseDate=FILMDICT['vReleaseDate'], kwDuration=FILMDICT['vDuration'])

        except Exception as e:
            utils.log('SEARCH:: Error Accessing Site URL page: %s', e)
            FILMDICT['Status'] = False

        # we should have a match on studio, title and year now. Find corresponding film on IAFD
        utils.log(LOG_BIGLINE)
        try:
            utils.log(LOG_BIGLINE)
            utils.log('SEARCH:: Check for Film on IAFD:')
            utils.getFilmOnIAFD(FILMDICT)

        except:
            pass

        # update the metadata
        utils.log(LOG_BIGLINE)
        if FILMDICT['Status'] is True:
            utils.log(LOG_BIGLINE)
            '''
            The following bits of metadata need to be established and used to update the movie on plex
            1.  Metadata that is set by Agent as default
                a. id.                 : Plex media id setting
                b. Studio              : From studio group of filename - no need to process this as above
                c. Title               : From title group of filename - no need to process this as is used to find it on website
                d. Tag line            : Corresponds to the url of film
                e. Originally Available: set from metadata.id (search result)
                f. Content Rating      : Always X
                g. Content Rating Age  : Always 18

            2.  Metadata retrieved from website
                a. Originally Availiable Date
                b. Ratings
                c. Genres                           : List of Genres (alphabetic order)
                d. Countries
                e. Cast                             : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
                f. Directors                        : List of Directors (alphabetic order)
                g. Collections                      : retrieved from FILMDICT, Genres, Countries, Cast Directors
                h. Posters
                i. Art (Background)
                j. Reviews
                k. Chapters
                l. Summary
            '''
            utils.setMetadata(metadata, media, FILMDICT)

        # Failure: initialise original availiable date, so that one can find titles sorted by release date which are not scraped
        if FILMDICT['Status'] is False:
            metadata.originally_available_at = None
            metadata.year = 0

        utils.logFooter('UPDATE', FILMDICT)
        return FILMDICT['Status']