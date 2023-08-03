#!/usr/bin/env python
# encoding=utf8
'''
# HomoActive - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    12 Aug 2019     2019.08.12.01   Creation
    05 Dec 2022     2019.08.12.10   Updated to use latest version of utils.py
    04 Feb 2023     2019.08.12.11   added code to retrieve studio from site entry
    13 Jul 2023     2019.08.12.12   Updated to use latest version of utils.py
    
-----------------------------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2019.08.12.12'
AGENT = 'HomoActive'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS
BASE_URL = 'https://www.homoactive.com'
BASE_SEARCH_URL = BASE_URL + '/catalogsearch/result/?q={0}'

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
class HomoActive(Agent.Movies):
    ''' define Agent class '''
    name = 'HomoActive (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        utils.log('AGENT :: {0:<29} {1}'.format('Original Search Query', myString))

        myString = myString.replace(' -', ':').replace(ur'\u2013', '-').replace(ur'\u2014', '-').replace('& ', '').strip().lower()
        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString)

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
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        morePages = True
        while morePages:
            utils.log('SEARCH:: Search Query: {0}'.format(searchQuery))
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=utils.delay())
                # Finds the entire media enclosure
                filmsList = html.xpath('//div[@class="item"]')
                if not filmsList:
                    raise Exception('< No Films! >')
            except Exception as e:
                utils.log('SEARCH:: Error: Search Query did not pull any results: {0}'.format(e))
                break

            try:
                pageNumber = int(html.xpath('//ol[@class="pagination pagination-sm"]/li[@class="current active"]/span/text()')[0])
                searchQuery = html.xpath('//ol[@class="pagination pagination-sm"]/li/a[text()="{0}"]/@href').format(pageNumber + 1)[0]
                utils.log('SEARCH:: Next Page Search Query: {0}'.format(searchQuery))
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

                # Site Title
                try:
                    filmTitle = film.xpath('./a/@title')[0]
                    filmTitle = re.sub(ur' (dvd|download).*$', '', filmTitle, flags=re.IGNORECASE)
                    filmTitle = filmTitle.split('(')[0].strip()
                    utils.matchTitle(filmTitle, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Title URL
                utils.log(LOG_BIGLINE)
                try:
                    filmURL = film.xpath('./a/@href')[0]
                    filmURL = ('' if BASE_URL in filmURL else BASE_URL) + filmURL
                    FILMDICT['FilmURL'] = filmURL
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', filmURL))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title Url: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Access Site URL for Studio and Release Date information
                utils.log(LOG_BIGLINE)
                try:
                    utils.log('SEARCH:: {0:<29} {1}'.format('Reading Site URL page', filmURL))
                    fhtml = HTML.ElementFromURL(FILMDICT['FilmURL'], sleep=utils.delay())
                    FILMDICT['FilmHTML'] = fhtml
                except Exception as e:
                    utils.log('SEARCH:: Error reading Site URL page: {0}'.format(e))
                    utils.log(LOG_SUBLINE)
                    continue

                # Studio Name
                utils.log(LOG_BIGLINE)
                try:
                    fhtmlStudio = fhtml.xpath('//div[@class="product-name"]/span/dd/a/text()')[0]
                    utils.matchStudio(fhtmlStudio, FILMDICT)
                except Exception as e:
                    # some entries have the studio title within the site title enclosed in brackets
                    try:
                        filmStudio = film.xpath('./a/@title')[0]
                        filmStudio = re.search(r'\((.*?)\)', filmStudio).group(1)
                        utils.matchStudio(filmStudio, FILMDICT)
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Studio: {0}'.format(e))
                        utils.log(LOG_SUBLINE)
                        continue

                # Site Release Date
                utils.log(LOG_BIGLINE)
                try:
                    fhtmlReleaseDate = fhtml.xpath('//dt[text()="Release Date:"]/following-sibling::dd[1]/text()[normalize-space()]')[0].strip()
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

                # Site Film Duration
                utils.log(LOG_BIGLINE)
                matchedDuration = False
                vDuration = FILMDICT['Duration']
                try:
                    fhtmlduration = fhtml.xpath('//dt[text()="Run Time:"]/following-sibling::dd[1]/text()[normalize-space()]')[0].strip()
                    fhtmlduration = re.sub('[^0-9]', '', fhtmlduration).strip()                      # strip away alphabetic characters leaving mins
                    duration = int(fhtmlduration) * 60                                                    # convert to seconds
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
                del FILMDICT['FilmHTML']

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
        utils.updateMetadata(metadata, media, lang, force=True)
