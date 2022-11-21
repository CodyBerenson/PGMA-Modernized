#!/usr/bin/env python
# encoding=utf8
'''
# GEVI - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    07 Oct 2020     2019.12.25.21   IAFD - change to https
                                    GEVI now searches all returned results and stops if return is alphabetically greater than title
    08 May 2021     2019.12.25.31   Use of duration matching
    27 Jul 2021     2019.12.25.32   Use of review area for scene matching
    21 Aug 2021     2019.12.25.33   IAFD will be only searched if film found on agent Catalogue
    16 Jan 2021     2019.12.25.34   Gevi changed website design, xml had to change to reflect this, fields affected performers, directors, studio
                                    added body type information to genres and corrected original code to cater for multiple genres as this was not split on commas
    04 Feb 2022     2019.12.25.34   implemented change suggested by Cody: duration matching optional on IAFD matching
                                    Cast list if used in filename becomes the default that is matched against IAFD, useful in case no cast is listed in agent
    21 Mar 2022     2019.12.25.35   #147: Implemented simple fix by fivedays555, to add website to Agents Header Referer
    13 May 2022     2019.12.25.36   Use IAFD Synopsis if present and Site's missing
                                    - corrected code as if no actors were listed on the site, it would not take those added to the filename on disk   
                                    - #162: duration matching had an error in the code - corrected and enhanced
                                    - improved logging
                                    - fixed error if no cast recorded on GEVI
    13 May 2022     2019.12.25.37   Introduced error in search string logging
    19 Aug 2022     2019.12.25.38   Multiple Improvements and major rewrites
                                    - using links to AEBN, GayDVDEmpre and GayHotMovies to garner,cast, directors, scenes, chapters, film durations and posters
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
    07 Nov 2022     2019.12.25.39   Search String corrections taking in to account the new GEVI Search Engine
-----------------------------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2019.12.25.39'
AGENT = 'GEVI'

# URLS
BASE_URL = 'https://www.gayeroticvideoindex.com'
BASE_SEARCH_URL = BASE_URL + '/shtt.php?draw=1&order[0][dir]=desc&start={0}&length=100&search[value]={1}&where={2}&_=1665855952743'
WATERMARK = 'https://cdn0.iconfinder.com/data/icons/mobile-device/512/lowcase-letter-d-latin-alphabet-keyboard-2-32.png'

# Date Formats used by website
DATEFORMAT = '%Y%m%d'
MATCHSITEDURATION = ''

# Website Language
SITE_LANGUAGE = 'en'

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
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36 Edg/104.0.1293.63'
    HTTP.Headers['Referer'] = 'https://gayeroticvideoindex.com/search'

    utils.setupStartVariables()

    ValidatePrefs()

# ----------------------------------------------------------------------------------------------------------------------------------
def ValidatePrefs():
    ''' Validate Changed Preferences '''
    pass

# ----------------------------------------------------------------------------------------------------------------------------------
class GEVI(Agent.Movies):
    ''' define Agent class '''
    name = 'GEVI (IAFD)'
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        utils.log('AGENT :: {0:<29} {1}'.format('Original Search Query', myString))

        # convert to lower case and trim
        myString = myString.lower().strip()

        # replace & with and
        myString = myString.replace(' & ', ' ').replace(' and ', ' ')
        utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Replaced ampersands & " and " with ', 'Space')))

        # replace following with null
        nullChars = [',', '!', '#', '+', '='] # to be replaced with null
        pattern = u'[{0}]'.format(''.join(nullChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, '', myString)
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Removed Pattern', pattern)))

        # replace following with space
        spaceChars = ["@", '\-', ur'\u2013', ur'\u2014', '\(', '\)', '\.', "'", ur'\u2019']  # to be replaced with space
        pattern = u'[{0}]'.format(''.join(spaceChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, ' ', myString)
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Removed Pattern', pattern)))

        # remove continuous spaces in string
        myString = ' '.join(myString.split())

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

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        for searchTitle in FILMDICT['SearchTitles']:
            if FILMDICT['Status']:
                break

            searchTitle = self.CleanSearchString(searchTitle)
            startRecord = 0
            morePages = True
            while morePages:
                searchType = 'containing' if '%7E%7E' in searchTitle else 'starting+with'           # ~~ = %7E%7E after URLEncoding
                if searchType == 'containing':
                    searchTitle = searchTitle.replace('%7E%7E', '')

                searchQuery = BASE_SEARCH_URL.format(startRecord, searchTitle, searchType)
                utils.log('SEARCH:: Search Query: %s', searchQuery)
                try:
                    JSon = JSON.ObjectFromURL(searchQuery, timeout=20, sleep=utils.delay())
                    filmsList = JSon.get('data', '')
                    if not filmsList:
                        raise Exception('< No Film Titles! >')   # out of WHILE loop

                    filmsFound = JSon.get('recordsFiltered', len(filmsList))
                    morePages = True if startRecord <= filmsFound else False
                    if not morePages:
                        utils.log('SEARCH:: No More Pages Found')
                except Exception as e:
                    utils.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                    break

                pageNumber = int(startRecord / 100) + 1
                utils.log('SEARCH:: {0:<29} {1}'.format('Titles Found', '{0} Processing Results Page: {1:>2} - Search String: {2}'.format(filmsFound, pageNumber, searchTitle)))
                utils.log(LOG_BIGLINE)
                myYear = '({0})'.format(FILMDICT['Year']) if FILMDICT['Year'] else ''
                for idx, film in enumerate(filmsList, start=1):
                    utils.log('SEARCH:: {0:<29} {1}'.format('Processing', '{0} of {1} for {2} - {3} {4}'.format(idx + startRecord, filmsFound, FILMDICT['Studio'], FILMDICT['Title'], myYear)))
                    utils.log(LOG_BIGLINE)

                    #[u"<a href='/video/30363'>Big & Beefy</a>", u'2008', u"<a href='/company/6303'>Alphamale Media</a>", None, u'', u'', u'General Hardcore']

                    # Site Entry
                    try:
                        filmEntry = film[0]
                        pattern = re.compile("<a href='(?P<FilmURL>.*?)'>(?P<FilmTitle>.*?)</a>")
                        matched = pattern.search(filmEntry)
                        if not matched:
                            raise Exception("< Film Entry [{0}] not in the expected format: <a href='....'>Film Title<a/>! >".format(filmEntry))
                        groups = matched.groupdict()
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Entry: %s', e)
                        utils.log(LOG_SUBLINE)
                        continue

                    # Site Title
                    try:
                        filmTitle = groups['FilmTitle']
                        unwantedWords = ['[sic]']
                        for unwantedWord in unwantedWords:
                            if unwantedWord in filmTitle:
                                filmTitle = filmTitle.replace(unwantedWord, '')

                        utils.matchTitle(filmTitle, FILMDICT)
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Title: %s', e)
                        utils.log(LOG_SUBLINE)
                        continue

                    # Site Title URL
                    utils.log(LOG_BIGLINE)
                    try:
                        filmURL = groups['FilmURL']
                        filmURL = ('' if BASE_URL in filmURL else BASE_URL) + filmURL
                        FILMDICT['FilmURL'] = filmURL
                        utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', filmURL))
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Title Url: %s', e)
                        utils.log(LOG_SUBLINE)
                        continue

                    # Site Title Type (Compilation)
                    utils.log(LOG_BIGLINE)
                    try:
                        filmType = film[4]
                        FILMDICT['Compilation'] = 'Yes' if filmType.lower() == 'compilation' else 'No'
                        vCompilation = FILMDICT['Compilation']
                        utils.log('SEARCH:: {0:<29} {1}'.format('Compilation?', FILMDICT['Compilation']))
                    except:
                        utils.log('SEARCH:: Error getting Site Type (Compilation)')
                        utils.log(LOG_SUBLINE)
                        continue

                    # Access Site URL for Studio and Release Date information
                    utils.log(LOG_BIGLINE)
                    try:
                        utils.log('SEARCH:: {0:<29} {1}'.format('Reading Site URL page', filmURL))
                        fhtml = HTML.ElementFromURL(FILMDICT['FilmURL'], sleep=utils.delay())
                        FILMDICT['FilmHTML'] = fhtml
                    except Exception as e:
                        utils.log('SEARCH:: Error reading Site URL page: %s', e)
                        utils.log(LOG_SUBLINE)
                        continue

                    # Site Studio/Distributor
                    utils.log(LOG_BIGLINE)
                    try:
                        foundStudio = False
                        fhtmlStudio = fhtml.xpath('//a[contains(@href, "/company/")]/parent::td//text()[normalize-space()]')
                        fhtmlStudio = [x.strip() for x in fhtmlStudio if x.strip()]
                        fhtmlStudio = list(set(fhtmlStudio))
                        utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Distributor/Studio', fhtmlStudio))
                        for siteStudio in fhtmlStudio:
                            try:
                                utils.matchStudio(siteStudio, FILMDICT)
                                foundStudio = True
                            except Exception as e:
                                utils.log('SEARCH:: Error: %s', e)
                                utils.log(LOG_SUBLINE)
                                continue
                            if foundStudio:
                                break

                        if not foundStudio:
                            utils.log('SEARCH:: Error matching Site Studio')
                            utils.log(LOG_SUBLINE)
                            continue

                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Studio: %s', e)
                        utils.log(LOG_SUBLINE)
                        continue

                    # Release Date - GEVI format YYYY or cYYYY or yyyy-yyyy
                    utils.log(LOG_BIGLINE)
                    releaseDateMatch = False
                    vReleaseDate = FILMDICT['CompareDate']
                    try:
                        compareYear = datetime.now().year + 2
                        fhtmlReleaseDate = fhtml.xpath('//td[.="released" or .="produced"]/following-sibling::td[1]/text()[normalize-space()]')
                        fhtmlReleaseDate = [x.replace('?', '').strip() for x in fhtmlReleaseDate]
                        fhtmlReleaseDate = [x for x in fhtmlReleaseDate if x.strip()]
                        if len(fhtmlReleaseDate) == 0:
                            raise Exception('< No Valid Dates Found! >')

                        utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Release Date(s)', '{0:>2} - {1}'.format(len(fhtmlReleaseDate), fhtmlReleaseDate)))
                        for item in fhtmlReleaseDate:
                            if 'c' in item:                                                                                 # format 4
                                item = item.replace('c', '')
                            elif ',' in item:                                                                               # format 3 - take year after the comma
                                item = item.split(',')[1]
                            elif '-' in item:                                                                               # format 2 - take year after dash:
                                items = item.split('-')
                                items = [x.strip() for x in items]
                                if len(items[1]) == 1:
                                    item = '{0}{1}'.format(item[0][0:2], item.split('-')[1])                                # e.g 1995-7  -> 199 + 7
                                    item = '{0}{1}'.format(20 if item > compareYear else 19, item)                          # if year format YY is > than the comparison Year then it's in the previous century
                                elif len(items[1]) == 2:             # e.g 1995-97
                                    item = '{0}{1}'.format(item[0][0:1], item.split('-')[1])                                # e.g 1995-97 -> 19 + 97
                                    item = '{0}{1}'.format(20 if item > compareYear else 19, item)                          # if year format YY is > than the comparison Year then it's in the previous century
                                else:
                                    item = items[1]                                                                         # eg 1995-1997 -> 1997

                            # item should now be in YYYY format, if year format YY is less than the comparison date it's 1999, convert to date and add to set
                            item = '{0}1231'.format(item)
                            utils.log('SEARCH:: {0:<29} {1}'.format('Release Date', item))

                            try:
                                releaseDate = datetime.strptime(item, DATEFORMAT)
                                utils.log('SEARCH:: {0:<29} {1}'.format('Selected Release Date', releaseDate))
                                utils.matchReleaseDate(releaseDate, FILMDICT)
                                releaseDateMatch = True
                                vReleaseDate = releaseDate
                                break
                            except Exception as e:
                                utils.log('SEARCH:: Error matching Site URL Release Date: %s', e)

                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date: %s', e)

                    else:
                        if FILMDICT['Year'] and not releaseDateMatch:
                            utils.log(LOG_SUBLINE)
                            continue

                    # Duration: GEVI format = mins
                    utils.log(LOG_BIGLINE)
                    vDuration = FILMDICT['Duration']
                    durationMatch = False
                    try:
                        fhtmlDuration = fhtml.xpath('//td[.="length"]/following-sibling::td[1]/text()[normalize-space()]')
                        fhtmlDuration = [x.strip() for x in fhtmlDuration if x.strip()]
                        utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Duration(s)', '{0:>2} - {1}'.format(len(fhtmlDuration), fhtmlDuration)))
                        for item in fhtmlDuration:
                            item = int(item) * 60                       # convert to seconds
                            try:
                                duration = datetime.fromtimestamp(item)
                                utils.log('SEARCH:: {0:<29} {1}'.format('Selected Duration', duration))
                                utils.matchDuration(duration, FILMDICT)
                                durationMatch = True
                                vDuration = duration
                                break

                            except Exception as e:
                                utils.log('SEARCH:: Error Matching Duration: %s', e)

                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Film Duration: %s', e)

                    if not durationMatch and MATCHSITEDURATION:
                        utils.log(LOG_SUBLINE)
                        continue

                    # At this point we have a match against default Studio and Title and Release Date and Duration
                    # GEVI has links to External Sites for the Title - These sites may have different Release Dates and Duration Times
                    # Release Dates and Durations must be retrieved - whether matching against them is needed or not
                    # if matching match against all data returned and considered passed if any match
                    utils.log(LOG_BIGLINE)
                    utils.log('SEARCH:: Access External Links:')
                    webLinks = {}
                    try:
                        fhtmlURLs = fhtml.xpath('//td[@class="gsr"]/a/@href')
                        for idx, fhtmlURL in enumerate(fhtmlURLs, start=1):
                            key = 'AEBNiii' if 'aebn' in fhtmlURL else 'GayHotMovies' if 'gayhotmovies' in fhtmlURL else 'GayDVDEmpire' if 'gaydvdempire' in fhtmlURL else ''
                            utils.log('SEARCH:: {0:<29} {1}'.format('External Sites Found' if idx ==1 else '', '{0:>2} - {1:<15} - {2}'.format(idx, key, fhtmlURL)))
                            if key and key not in webLinks:
                                webLinks[key] = fhtmlURL

                        for key in ['AEBNiii', 'GayHotMovies', 'GayDVDEmpire']:                  # access links in this order: break after processing first external link
                            if key in webLinks:
                                vFilmURL = webLinks[key]
                                vFilmHTML = HTML.ElementFromURL(vFilmURL, timeout=60, errors='ignore', sleep=utils.delay())
                                FILMDICT[key] = utils.getSiteInfo(key, FILMDICT, kwFilmURL=vFilmURL, kwFilmHTML=vFilmHTML)

                                # change Compilation to 'Yes' if the result is not the default 'No'
                                extCompilation = FILMDICT[key]['Compilation']
                                FILMDICT['Compilation'] = extCompilation if FILMDICT['Compilation'] == 'No' and extCompilation == 'Yes' else FILMDICT['Compilation']
                                vCompilation = FILMDICT['Compilation']

                                # GEVI's release dates are set to 31st December, replace date in FILMDICT if earlier one is found
                                extReleaseDate = FILMDICT[key]['ReleaseDate']
                                vReleaseDate = extReleaseDate if extReleaseDate is not None and extReleaseDate < vReleaseDate else vReleaseDate

                                break       # external info retrieved

                    except Exception as e:
                        utils.log('SEARCH:: No External Links Recorded: %s', e)

                    FILMDICT['vCompilation'] = vCompilation
                    FILMDICT['vDuration'] = vDuration
                    FILMDICT['vReleaseDate'] = vReleaseDate
                    del FILMDICT['FilmHTML']

                    myID = json.dumps(FILMDICT, default=utils.jsonDumper)
                    results.Append(MetadataSearchResult(id=myID, name=FILMDICT['Title'], score=100, lang=lang))

                    # Film Scraped Sucessfully - update status and break out!
                    FILMDICT['Status'] = True
                    break       # stop processing

                startRecord += 100          # JSon retrieves 100 records at a time
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