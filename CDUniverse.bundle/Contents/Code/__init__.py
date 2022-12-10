#!/usr/bin/env python
# encoding=utf8
'''
# CD Universe - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    25 Aug 2021     2020.12.31.07   IAFD will be only searched if film found on agent Catalogue
    04 Feb 2022     2020.12.31.08   implemented change suggested by Cody: duration matching optional on IAFD matching
                                    Cast list if used in filename becomes the default that is matched against IAFD, useful in case no cast is listed in agent
    19 Aug 2022     2020.12.31.09   Multiple Improvements and major rewrites
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
    05 Dec 2022     2020.12.31.10   Updated to use latest version of utils.py

-----------------------------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2019.12.31.10'
AGENT = 'CDUniverse'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS
BASE_URL = 'https://www.cduniverse.com'
BASE_SEARCH_URL = BASE_URL + '/sresult.asp?HT_Search_Info={0}&HT_SEARCH=TITLE&style=gay&thx=1'
WATERMARK = 'https://cdn0.iconfinder.com/data/icons/mobile-device/512/lowcase-letter-d-latin-alphabet-keyboard-2-32.png'

# Date Format used by website
DATEFORMAT = '%b %d, %Y'

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
class CDUniverse(Agent.Movies):
    ''' define Agent class '''
    name = 'CD Universe (IAFD)'
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        utils.log('AGENT :: {0:<29} {1}'.format('Original Search Query', myString))

        myString = myString.strip().lower()
        myString = myString.replace('-', '').replace(ur'\u2013', '').replace(ur'\u2014', '')
        myString = ' '.join(myString.split())   # remove continous white space

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString)

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        myString = String.URLEncode('"{0}"'.format(myString)).replace('%25', '%').replace('*', '')
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

        utils.logHeader('SEARCH', media, lang)

        # Check filename format
        try:
            FILMDICT = copy.deepcopy(utils.matchFilename(media))
            FILMDICT['lang'] = lang
            FILMDICT['Agent'] = AGENT
            FILMDICT['Status'] = False
        except Exception as e:
            utils.log(LOG_ASTLINE)
            utils.log('SEARCH:: Error: %s', e)
            utils.log(LOG_ASTLINE)
            return

        utils.log(LOG_BIGLINE)

        # Search Query - for use to search the internet, remove all non alphabetic characters.
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        try:
            html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
            # Finds the entire media enclosure
            filmsList = html.xpath('//*[@class="chunkytitle"]')
            if not filmsList:
                raise Exception('< No Films! >')

        except Exception as e:
            utils.log('SEARCH:: Error: Search Query did not pull any results: %s', e)

        else:
            filmsFound = len(filmsList)
            utils.log('SEARCH:: {0:<29} {1}'.format('Titles Found', '{0} Processing Results Page'.format(filmsFound)))
            utils.log(LOG_BIGLINE)
            myYear = '({0})'.format(FILMDICT['Year']) if FILMDICT['Year'] else ''
            for idx, film in enumerate(filmsList, start=1):
                utils.log('SEARCH:: {0:<29} {1}'.format('Processing', '{0} of {1} for {2} - {3} {4}'.format(idx, filmsFound, FILMDICT['Studio'], FILMDICT['Title'], myYear)))
                utils.log(LOG_BIGLINE)

                # Site Title
                try:
                    filmTitle = film.text
                    utils.matchTitle(filmTitle, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Title URL
                utils.log(LOG_BIGLINE)
                try:
                    filmURL = film.get('href')
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
                    fhtml = HTML.ElementFromURL(FILMDICT['FilmURL'], sleep=DELAY)
                    FILMDICT['FilmHTML'] = fhtml
                except Exception as e:
                    utils.log('SEARCH:: Error reading Site URL page: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # Studio Name
                utils.log(LOG_BIGLINE)
                try:
                    fhtmlStudio = fhtml.xpath('//a[@id="studiolink"]/text()')[0]
                    utils.matchStudio(fhtmlStudio, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Studio: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Release Date
                utils.log(LOG_BIGLINE)
                try:
                    fhtmlReleaseDate = fhtml.xpath('//td[text()="Release Date"]/following-sibling::td/text()')[0].strip()
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Release Date', fhtmlReleaseDate))
                    try:
                        releaseDate = datetime.strptime(fhtmlReleaseDate, DATEFORMAT)
                        utils.matchReleaseDate(releaseDate, FILMDICT)
                        vReleaseDate = releaseDate
                    except Exception as e:
                        if FILMDICT['Year']:
                            utils.log(LOG_SUBLINE)
                            continue
                except:
                    utils.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                    vReleaseDate = FILMDICT['CompareDate'] if FILMDICT['CompareDate'] else None

                # Duration - missing on CD Universe
                utils.log(LOG_BIGLINE)
                vDuration = FILMDICT['Duration']
                utils.log('SEARCH:: {0:<29} {1}'.format('Duration: Use Default', vDuration))

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
        if FILMDICT['Status']:
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
        if not FILMDICT['Status']:
            metadata.originally_available_at = None
            metadata.year = 0

        utils.logFooter('UPDATE', FILMDICT)
        return FILMDICT['Status']