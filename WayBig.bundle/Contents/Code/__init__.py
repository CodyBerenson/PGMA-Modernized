#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
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
---------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2019.12.22.36'
AGENT = 'WayBig'

# URLS
BASE_URL = 'https://www.waybig.com'
BASE_SEARCH_URL = BASE_URL + '/blog/index.php?s={0}'

# Date Formats used by website
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
        if '- ' in myString:
            myString = myString.replace(' - ', ': ')
            myString = myString.replace('- ', ': ')
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Replaced Hyphens-Dash', 'Colons ":"')))

        # remove all apostrophes with straight as strip diacritics will remove these, include back ticks 
        quoteChars = [ur'‘', ur'’', ur'\u2018', ur'\u2019', "'", '"']
        pattern = u'({0})'.format('|'.join(quoteChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, ' ', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Removed Pattern', pattern)))

        # WayBig seems to fail to find Titles which have invalid chars in them, split at first incident and take first split
        badChars = [ur'\u201c', ur'\u201d']
        pattern = u'({0})'.format('|'.join(badChars))
        myWords = myString.split()
        for count, word in enumerate(myWords):
            matched = re.search(pattern, word) # match against first word
            if matched:
                myWords.remove(myWords[count])
                utils.log('AGENT :: {0:<29} {1}'.format('Search Query', 'Dropped Word {0}: found Pattern {1}'.format(word, pattern)))
                myString = ' '.join(myWords)

        # string can not be longer than 50 characters
        if len(myString) > 50:
            lastSpace = myString[:51].rfind(' ')
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

        # strip studio name from title to use in comparison
        utils.log('SEARCH:: Search Title: %s', searchTitle)
        regex = ur'^{0} |at {0}$'.format(re.escape(FILMDICT['CompareStudio']))
        pattern = re.compile(regex, re.IGNORECASE)
        compareTitle = re.sub(pattern, '', searchTitle)
        compareTitle = utils.Normalise(compareTitle)

        utils.log('SEARCH:: Search Title: %s', searchTitle)

        morePages = True
        while morePages:
            utils.log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
                filmsList = html.xpath('.//div[@class="row"]/div[@class="content-col col"]/article')
                if not filmsList:
                    raise Exception('< No Films! >')
            except Exception as e:
                utils.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                break

            try:
                searchQuery = html.xpath('//div[@class="nav-links"]/a[@class="next page-numbers"]/@href')[0]
                utils.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(html.xpath('//div[@class="nav-links"]/span[@class="page-numbers current"]/text()[normalize-space()]')[0])
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
                    filmEntry = film.xpath('./a/*[@class="entry-title"]/text()')[0].strip()
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Entry', filmEntry))
                    # prepare the Site Entry
                    singleQuotes = ["`", "‘", "’"]
                    pattern = ur'[{0}]'.format(''.join(singleQuotes))
                    filmEntry = re.sub(pattern, "'", filmEntry)
                    # the filmEntry usual has the format Studio: Title
                    if re.search(r' at ', filmEntry, flags=re.IGNORECASE) and ': ' in filmEntry and (filmEntry.endswith("'") or filmEntry.endswith('"')):  # err 123
                        utils.log('SEARCH:: Matched " at ", ": " and %s ends with apostrophe in Site entry', re.match(filmEntry, '[\'"]$'))
                        filmStudio, filmTitle = filmEntry.split(': ', 1)
                    elif re.search(r' at ', filmEntry, flags=re.IGNORECASE):               # format:- Title at Studio
                        utils.log('SEARCH:: Matched " at " in Site entry')
                        filmTitle, filmStudio = re.split(r' at ', filmEntry, flags=re.IGNORECASE, maxsplit=1)
                    elif ': ' in filmEntry:                                                 # format:- Studio: Title
                        utils.log('SEARCH:: Matched ": " Site entry')
                        filmStudio, filmTitle = filmEntry.split(': ', 1)
                    elif re.search(r' on ', filmEntry, flags=re.IGNORECASE):               # format:- Title on Studio
                        utils.log('SEARCH:: Matched " on " in Site entry')
                        filmTitle, filmStudio = re.split(r' on ', filmEntry, flags=re.IGNORECASE, maxsplit=1)
                    elif '? ' in filmEntry:                                                 # format:- Studio? Title
                        utils.log('SEARCH:: Matched "? " in Site entry')
                        filmStudio, filmTitle = filmEntry.split('? ', 1)
                    elif ', ' in filmEntry:                                                 # format: Studio, Title
                        utils.log('SEARCH:: Matched ", " in Site entry')
                        filmStudio, filmTitle = filmEntry.split(', ', 1)
                    elif re.match(FILMDICT['Studio'], filmEntry, flags=re.IGNORECASE):      # format:- Studio Title {no separtor}
                        utils.log('SEARCH:: Warning: Site Entry did not have a clear separator to separate Studio from Title')
                        filmStudio = FILMDICT['Studio']
                        filmTitle = re.sub(filmStudio, '', filmEntry, re.IGNORECASE).strip()
                    else:
                        utils.log('SEARCH:: Error determining Site Studio and Title from Site Entry')
                        utils.log(LOG_SUBLINE)
                        continue

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
                    filmURL = film.xpath('./a[@rel="bookmark"]/@href')[0]
                    filmURL = ('' if BASE_URL in filmURL else BASE_URL) + filmURL
                    FILMDICT['FilmURL'] = filmURL
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', filmURL))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title Url: %s', e)
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
                        utils.log('SEARCH:: Error getting Site URL Release Date: %s', e)
                        if FILMDICT['Year']:
                            utils.log(LOG_SUBLINE)
                            continue
                except:
                    utils.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                    vReleaseDate = FILMDICT['CompareDate']

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
                FILMDICT[AGENT] = utils.getSiteInfo(AGENT, FILMDICT, kwReleaseDate=vReleaseDate)

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