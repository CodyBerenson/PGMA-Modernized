#!/usr/bin/env python
# encoding=utf8
'''
# GEVI - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    13 May 2022     2019.12.25.37   Introduced error in search string logging
    19 Aug 2022     2019.12.25.38   Multiple Improvements and major rewrites
                                    - using links to AEBN, GayEmpre and GayHotMovies to garner,cast, directors, scenes, chapters, film durations and posters
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
    07 Nov 2022     2019.12.25.39   Search String corrections taking in to account the new GEVI Search Engine
    27 Nov 2022     2019.12.25.40   Updated to use latest version of utils.py
    01 Feb 2023     2019.12.25.41   Corrected release date matching code
    11 Feb 2023     2019.12.25.42   display json retreival data, and use its entries to match against studio.
                                    use sets rather than lists to remove duplicate entries thus sppeding up scrape
                                    changed search url string so that alternate studio names (lines) are retrieved
    23 Feb 2023     2019.12.25.43   Cater for titles that did not have a year provided and no external websites year of production
    15 Apr 2023     2019.12.25.44   Dealt with ² in titles as can not be included in search strings   
    02 Jul 2023     2019.12.25.45   Dealt with 's, 't to improve on search strings
                                    Updated to use new utils.py
    07 Jul 2023     2019.12.25.46   GEVI Website Design Change - implement new xpath
    14 Jul 2023     2019.12.25.47   films to failing to match release dates wer not been assigned the default filename date
    01 Aug 2023     2019.12.25.48   Improved matching with IAFD
-----------------------------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2019.12.25.48'
AGENT = 'GEVI'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS
BASE_URL = 'https://www.gayeroticvideoindex.com'
BASE_SEARCH_URL = BASE_URL + '/shtt.php?draw=4&columns[0][data]=0&columns[0][name]=title&columns[0][searchable]=true&columns[0][orderable]=true&columns[0][search][value]=&columns[0][search][regex]=false&columns[1][data]=1&columns[1][name]=release&columns[1][searchable]=true&columns[1][orderable]=true&columns[1][search][value]={2}&columns[1][search][regex]=false&columns[2][data]=2&columns[2][name]=company&columns[2][searchable]=true&columns[2][orderable]=true&columns[2][search][value]=&columns[2][search][regex]=false&columns[3][data]=3&columns[3][name]=line&columns[3][searchable]=true&columns[3][orderable]=true&columns[3][search][value]=&columns[3][search][regex]=false&columns[4][data]=4&columns[4][name]=type&columns[4][searchable]=true&columns[4][orderable]=true&columns[4][search][value]=show+compilation&columns[4][search][regex]=false&columns[5][data]=5&columns[5][name]=rating&columns[5][searchable]=true&columns[5][orderable]=true&columns[5][search][value]=&columns[5][search][regex]=false&columns[6][data]=6&columns[6][name]=category&columns[6][searchable]=true&columns[6][orderable]=true&columns[6][search][value]=&columns[6][search][regex]=false&order[0][column]=0&order[0][dir]=asc&start={0}&length=100&search[value]={1}&search[regex]=false&_=1676140164112'

# Date Formats used by website
DATEFORMAT = '%Y%m%d'

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
    HTTP.Headers['Referer'] = 'https://gayeroticvideoindex.com/search'

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

        # replace &, and with space, ~ with /
        myString = myString.replace(' & ', ' ').replace(' and ', ' ').replace("'s ", ' ').replace("'t ", ' ')
        utils.log('AGENT :: {0:<29} {1}'.format('Search Query', '{0}: {1}'.format('Replaced ampersands & " and " with ', 'Space')))

        # replace following with null
        nullChars = [',', '!', '#', '+', '=', u'²']     # to be replaced with null
        pattern = u'[{0}]'.format(''.join(nullChars))
        matched = re.search(pattern, myString)          # match against whole string
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
        fraction = True if '½' in myString else False

        myString = String.StripDiacritics(myString) 
        myString = myString if not fraction else myString.replace('12', '½')
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

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        for searchTitle in FILMDICT['SearchTitles']:
            if FILMDICT['Status'] is True:
                break

            startRecord = 0
            searchTitle = self.CleanSearchString(searchTitle)
            searchType = 'containing' if '%7E%7E' in searchTitle else 'starting+with'           # ~~ = %7E%7E after URLEncoding
            searchTitle = searchTitle.replace('%7E%7E', '') if searchType == 'containing' else searchTitle

            pageNumber = 0
            morePages = True
            while morePages:
                pageNumber += 1
                if pageNumber > 10:
                    morePages = False     # search a maximum of 10 pages
                    utils.log('SEARCH:: Warning: Page Search Limit Reached [10]')
                    continue

                searchQuery = BASE_SEARCH_URL.format(startRecord, searchTitle, searchType)
                startRecord = pageNumber * 100       # JSon retrieves 100 records at a time
                utils.log('SEARCH:: Search Query: {0}'.format(searchQuery))
                try:
                    JSon = JSON.ObjectFromURL(searchQuery, timeout=20, sleep=utils.delay())
                    utils.log('SEARCH:: JSON: {0}'.format(JSon))
                    filmsList = JSon.get('data', '')
                    utils.log('SEARCH:: Film List: {0}'.format(filmsList))
                    if not filmsList:
                        raise Exception('< No Film Titles! >')   # out of WHILE loop

                    filmsFound = JSon.get('recordsFiltered', len(filmsList))
                    morePages = True if startRecord <= filmsFound else False
                    if morePages is False:
                        utils.log('SEARCH:: No More Pages Found')
                except Exception as e:
                    utils.log('SEARCH:: Error: Search Query did not pull any results: {0}'.format(e))
                    break

                utils.log('SEARCH:: {0:<29} {1}'.format('Titles Found', '{0} Processing Results Page: {1:>2} - Search String: {2}'.format(filmsFound, pageNumber, searchTitle)))
                utils.log(LOG_BIGLINE)
                myYear = '({0})'.format(FILMDICT['Year']) if FILMDICT['Year'] else ''
                for idx, film in enumerate(filmsList, start=1):
                    utils.log('SEARCH:: {0:<29} {1}'.format('Processing', 'Page {0}: {1} of {2} for {3} - {4} {5}'.format(pageNumber, idx, filmsFound, FILMDICT['Studio'], FILMDICT['Title'], myYear)))
                    utils.log(LOG_BIGLINE)

                    #[u"<a href='/video/30363'>Big & Beefy</a>", u'2008', u"<a href='/company/6303'>Alphamale Media</a>", None, u'', u'', u'General Hardcore']

                    # Site Entry
                    try:
                        film[2] = film[2].split('>', 1)[1].split('<')[0]
                        utils.log('SEARCH:: {0:<29} {1}'.format('JSON Film Entry', film))
                        utils.log('SEARCH:: {0:<29} {1}'.format('      URL/Title', film[0]))
                        utils.log('SEARCH:: {0:<29} {1}'.format('           Year', film[1]))
                        utils.log('SEARCH:: {0:<29} {1}'.format('         Studio', film[2]))
                        utils.log('SEARCH:: {0:<29} {1}'.format('           Line', film[3]))
                        utils.log('SEARCH:: {0:<29} {1}'.format('    Compilation', film[4]))
                        utils.log('SEARCH:: {0:<29} {1}'.format('         Rating', film[5]))
                        utils.log('SEARCH:: {0:<29} {1}'.format('          Genre', film[6]))
                        pattern = re.compile("<a href='(?P<FilmURL>.*?)'>(?P<FilmTitle>.*?)</a>")       # pattern to retrieve Site URL and Film Title
                        matched = pattern.search(film[0])
                        if not matched:
                            raise Exception("< Film Entry [{0}] not in the expected format: <a href='url'>Film Title<a/>! >".format(film[0]))
                        groups = matched.groupdict()
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Entry: {0}'.format(e))
                        utils.log(LOG_SUBLINE)
                        continue

                    # Site Title
                    utils.log(LOG_BIGLINE)
                    try:
                        filmTitle = groups['FilmTitle']
                        unwantedWords = ['[sic]', '(sic)']
                        for unwantedWord in unwantedWords:
                            if unwantedWord in filmTitle:
                                filmTitle = filmTitle.replace(unwantedWord, '')

                        utils.matchTitle(filmTitle, FILMDICT)
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Title: {0}'.format(e))
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
                        utils.log('SEARCH:: Error getting Site Title Url: {0}'.format(e))
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
                        utils.log('SEARCH:: Error reading Site URL page: {0}'.format(e))
                        utils.log(LOG_SUBLINE)
                        continue

                    # Site Studio/Distributor
                    utils.log(LOG_BIGLINE)
                    try:
                        foundStudio = False
                        fhtmlStudios = fhtml.xpath('//a[contains(@href, "company/")]/text()[normalize-space()]')
                        fhtmlStudios = {x.strip() for x in fhtmlStudios if x.strip()}
                        utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Distributor/Studio', fhtmlStudios))
                        if film[2] and film[2] is not None:             # Company Name i.e. distributor in GEVI at this position in json retrieval
                            fhtmlStudios.add(film[2])
                            utils.log('SEARCH:: {0:<29} {1}'.format('Add: JSon Company', fhtmlStudios))

                        if film[3] and film[3] is not None:             # Studios Lines in GEVI at this possition in json retrieval
                            fhtmlStudios.add(film[3])
                            utils.log('SEARCH:: {0:<29} {1}'.format('Add: JSon Line', fhtmlStudios))

                        FILMDICT['RecordedStudios'] = list(set(fhtmlStudios))
                        for siteStudio in FILMDICT['RecordedStudios']:
                            try:
                                utils.matchStudio(siteStudio, FILMDICT)
                                foundStudio = True

                            except Exception as e:
                                utils.log('SEARCH:: Warning: {0}'.format(e))
                                utils.log(LOG_SUBLINE)
                                continue

                            if foundStudio:
                                break

                        if not foundStudio:
                            utils.log('SEARCH:: Error matching Site Studio')
                            utils.log(LOG_SUBLINE)
                            continue

                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Studio: {0}'.format(e))
                        utils.log(LOG_SUBLINE)
                        continue

                    # Release Date - GEVI format YYYY or cYYYY or yyyy-yyyy
                    utils.log(LOG_BIGLINE)
                    releaseDateMatch = False
                    attemptMatch = False
                    vReleaseDate = FILMDICT['CompareDate']
                    try:
                        fhtmlTD = fhtml.xpath('//td//text()[normalize-space()]')         # get all table data ** dirty coing as xpath is not working
                        utils.log('SEARCH:: {0:<29} {1}'.format('Table Cell Data', '{0:>2} - {1}'.format(len(fhtmlTD), fhtmlTD)))
                        if 'Gay Erotic Video Index' in fhtmlTD:         # format 1 like Bring me a boy 68
                            fhtmlIdx = [x for x in range(len(fhtmlTD)) if fhtmlTD[x] == 'released' or fhtmlTD[x] == 'produced']
                            fhtmlReleaseDate = set()
                            [fhtmlReleaseDate.add(fhtmlTD[x+1]) for x in fhtmlIdx]
                        else:                                           # format 2 - normal
                            fhtmlReleaseDate = fhtml.xpath('//td[a[contains(@href,"company/")]]/following-sibling::td[1]/text()[normalize-space()]')
                            try:
                                fhtmlReleaseDate.append(fhtml.xpath('//div[contains(.,"Produced")]/following-sibling::div[1]/text()[normalize-space()]')[0])
                            except Exception as e:
                                utils.log('SEARCH:: Warning: No Production Date Found: {0}'.format(e))

                        utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Released Date', '{0:>2} - {1}'.format(len(fhtmlReleaseDate), fhtmlReleaseDate)))
                        for item in fhtmlReleaseDate:
                            item = item.strip()
                            if item == '?':
                                continue
                            elif 'b' in item or 'c' in item:                                                                # format 4
                                item = item.replace('b', '').replace('c', '')
                            elif ',' in item:                                                                               # format 3 - take year after the comma
                                item = item.split(',')[1]
                            elif '-' in item:                                                                               # format 2 - take year after dash:
                                century = item[0:2]                                                                         # 1995-year.... century = 19
                                decade = item[2]                                                                            # 1995-year.....decade = 9
                                years = item.split('-')
                                years = [x.strip() for x in years]
                                if len(years[-1]) == 1:                                                                      # format 2a e.g. 1995-7
                                    item = '{0}{1}{2}'.format(century, decade, years[-1])
                                elif len(years[-1]) == 2:                                                                    # format 2b e.g. 1995-97
                                    item = '{0}{1}'.format(century, years[-1])
                                else:
                                    item = years[-1]                                                                         # format 2c e.g. 1995-1997

                            # item should now be in YYYY format, if year format YY is less than the comparison date it's 1999, convert to date and add to set
                            item = '{0}1231'.format(item)
                            utils.log('SEARCH:: {0:<29} {1}'.format('Release Date', item))

                            try:
                                attemptMatch = True
                                releaseDate = datetime.strptime(item, DATEFORMAT)
                                utils.log('SEARCH:: {0:<29} {1}'.format('Selected Release Date', releaseDate))
                                utils.matchReleaseDate(releaseDate, FILMDICT)
                                releaseDateMatch = True
                                vReleaseDate = releaseDate
                                break

                            except Exception as e:
                                utils.log('SEARCH:: Error matching Site URL Release Date: {0}'.format(e))

                        if attemptMatch is True and FILMDICT['Year'] and releaseDateMatch is False:
                            utils.log(LOG_SUBLINE)
                            continue
                        else: 
                            utils.log('SEARCH:: Warning: Getting Site URL Release Date: Default to Filename Date: {0}'.format(vReleaseDate))

                    except Exception as e:
                        utils.log('SEARCH:: Error: Getting Site URL Release Date: {0}'.format(e))

                    # Duration: GEVI format = mins
                    utils.log(LOG_BIGLINE)
                    vDuration = FILMDICT['Duration']
                    matchedDuration = False
                    try:
                        if 'Gay Erotic Video Index' in fhtmlTD:         # format 1 like Bring me a boy 68
                            fhtmlIdx = [x for x in range(len(fhtmlTD)) if fhtmlTD[x] == 'length']       # fhtmlTD determined in release date code above
                            fhtmlDuration = set()
                            [fhtmlDuration.add(fhtmlTD[x+1]) for x in fhtmlIdx]
                        else:
                            fhtmlDuration = fhtml.xpath('//td[a[contains(@href,"company/")]]/following-sibling::td[2]/text()[normalize-space()]')

                        utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Duration(s)', '{0:>2} - {1}'.format(len(fhtmlDuration), fhtmlDuration)))
                        for item in fhtmlDuration:
                            item = item.strip()
                            if not item:
                                continue

                            item = int(item) * 60                       # convert to seconds
                            try:
                                duration = datetime.fromtimestamp(item)
                                utils.log('SEARCH:: {0:<29} {1}'.format('Selected Duration', duration))
                                utils.matchDuration(duration, AGENTDICT, FILMDICT)
                                matchedDuration = True
                                vDuration = duration
                                break

                            except Exception as e:
                                utils.log('SEARCH:: Error Matching Duration: {0}'.format(e))

                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site Film Duration: {0}'.format(e))

                    if matchedDuration is False and AGENTDICT['prefMATCHSITEDURATION'] is True:
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
                        fhtmlExternalLinks = fhtml.xpath('//a/@href')
                        fhtmlExternalLinks = [x.strip() for x in fhtmlExternalLinks if '.com' in x]
                        utils.log('SEARCH:: {0:<29} {1}'.format('External Links', '{0:>2} - {1}'.format(len(fhtmlExternalLinks), fhtmlExternalLinks)))
                        for idx, fhtmlExternalLink in enumerate(fhtmlExternalLinks, start=1):
                            key = 'AEBN' if 'aebn' in fhtmlExternalLink else 'GayHotMovies' if 'gayhotmovies' in fhtmlExternalLink else 'GayEmpire' if 'empire' in fhtmlExternalLink else ''
                            if not key:
                                continue
                            utils.log('SEARCH:: {0:<29} {1}'.format('External Sites Found' if idx ==1 else '', '{0:>2} - {1:<15} - {2}'.format(idx, key, fhtmlExternalLink)))
                            if key and key not in webLinks:
                                webLinks[key] = fhtmlExternalLink

                        for key in ['AEBN', 'GayHotMovies', 'GayEmpire']:                  # access links in this order: break after processing first external link
                            if key in webLinks:
                                vFilmURL = webLinks[key]
                                vFilmHTML = HTML.ElementFromURL(vFilmURL, timeout=60, errors='ignore', sleep=utils.delay())
                                FILMDICT[key] = utils.getSiteInfo(key, AGENTDICT, FILMDICT, kwFilmURL=vFilmURL, kwFilmHTML=vFilmHTML)

                                # change Compilation to 'Yes' if the result is not the default 'No'
                                extCompilation = FILMDICT[key]['Compilation']
                                FILMDICT['Compilation'] = extCompilation if FILMDICT['Compilation'] == 'No' and extCompilation == 'Yes' else FILMDICT['Compilation']
                                vCompilation = FILMDICT['Compilation']

                                # GEVI's release dates are set to 31st December, replace date in FILMDICT if earlier one is found
                                extReleaseDate = FILMDICT[key]['ReleaseDate']
                                vReleaseDate = extReleaseDate if extReleaseDate is not None and extReleaseDate < vReleaseDate else vReleaseDate

                                break       # external info retrieved

                    except Exception as e:
                        utils.log('SEARCH:: No External Links Recorded: {0}'.format(e))

                    FILMDICT['vCompilation'] = vCompilation
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
