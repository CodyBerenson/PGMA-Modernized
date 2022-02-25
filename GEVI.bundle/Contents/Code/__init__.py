#!/usr/bin/env python
# encoding=utf8
'''
# GEVI - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    07 Oct 2020   2019.12.25.21    IAFD - change to https
                                   GEVI now searches all returned results and stops if return is alphabetically greater than title
    08 May 2021   2019.12.25.31    Use of duration matching
    27 Jul 2021   2019.12.25.32    Use of review area for scene matching
    21 Aug 2021   2019.12.25.33    IAFD will be only searched if film found on agent Catalogue
    16 Jan 2021   2019.12.25.34    Gevi changed website design, xml had to change to reflect this, fields affected performers, directors, studio
                                   added body type information to genres and corrected original code to cater for multiple genres as this was not split on commas
    04 Feb 2022   2019.12.25.34    implemented change suggested by Cody: duration matching optional on IAFD matching
                                   Cast list if used in filename becomes the default that is matched against IAFD, useful in case no cast is listed in agent

-----------------------------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime
from helpers import clear_posters, clear_art

# Version / Log Title
VERSION_NO = '2019.12.25.34'
PLUGIN_LOG_TITLE = 'GEVI'

# log section separators
LOG_BIGLINE = '--------------------------------------------------------------------------------'
LOG_SUBLINE = '      --------------------------------------------------------------------------'

# Preferences
COLCAST = Prefs['castcollection']                   # add cast to collection
COLCLEAR = Prefs['clearcollections']                # clear previously set collections
COLCOUNTRY = Prefs['countrycollection']             # add country to collection
COLDIRECTOR = Prefs['directorcollection']           # add director to collection
COLGENRE = Prefs['genrecollection']                 # add genres to collection
COLSTUDIO = Prefs['studiocollection']               # add studio name to collection
COLTITLE = Prefs['titlecollection']                 # add title [parts] to collection
DELAY = int(Prefs['delay'])                         # Delay used when requesting HTML, may be good to have to prevent being banned from the site
DETECT = Prefs['detect']                            # detect the language the summary appears in on the web page
DURATIONDX = int(Prefs['durationdx'])               # Acceptable difference between actual duration of video file and that on agent website
MATCHIAFDDURATION = Prefs['matchiafdduration']      # Match against IAFD Duration value
MATCHSITEDURATION = Prefs['matchsiteduration']      # Match against Site Duration value
PREFIXLEGEND = Prefs['prefixlegend']                # place cast legend at start of summary or end

# URLS
BASE_URL = 'https://www.gayeroticvideoindex.com'
BASE_SEARCH_URL = BASE_URL + '/search.php?type=t&where=b&query={0}&Search=Search&page=1'

# dictionary holding film variables
FILMDICT = {}

# Date Formats used by website
DATEFORMAT = '%Y%m%d'

# Website Language
SITE_LANGUAGE = 'en'

# ----------------------------------------------------------------------------------------------------------------------------------
def Start():
    ''' initialise process '''
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'

# ----------------------------------------------------------------------------------------------------------------------------------
def ValidatePrefs():
    ''' validate changed user preferences '''
    pass
# ----------------------------------------------------------------------------------------------------------------------------------
def anyOf(iterable):
    '''  used for matching strings in lists '''
    for element in iterable:
        if element:
            return element
    return None

# ----------------------------------------------------------------------------------------------------------------------------------
def log(message, *args):
    ''' log messages '''
    if re.search('ERROR', message, re.IGNORECASE):
        Log.Error(PLUGIN_LOG_TITLE + ' - ' + message, *args)
    else:
        Log.Info(PLUGIN_LOG_TITLE + '  - ' + message, *args)

# ----------------------------------------------------------------------------------------------------------------------------------
# imports placed here to use previously declared variables
import utils

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
        log('AGNT  :: Original Search Query        : {0}'.format(myString))

        # convert to lower case and trim
        myString = myString.lower().strip()

        # replace honorifics in string with null
        foundHonorific = False
        honorifics = ['mr.', 'sgt.', 'lt.', 'gen.', 'cpt.']
        for honorific in honorifics:
            if honorific in myString:
                myString = myString.replace(honorific, '')
                foundHonorific = True

        if foundHonorific:
            log('AGNT  :: Search Query:: [{0}] after removing one of these {1}'.format(myString, honorifics))
        else:
            log('AGNT  :: Search Query:: [{0}] found none of these {0}'.format(myString, honorifics))

        # replace & with and
        if ' & ' in myString:
            myString = myString.replace(' & ', ' and ')
            log('AGNT  :: Search Query:: [{0}] after replacing " & "'.format(myString))
        else:
            log('AGNT  :: Search Query:: [{0}] found no " & "'.format(myString))

        # replace following with null
        nullChars = ["'", ',', '!', '\.', '#'] # to be replaced with null
        pattern = u'[{0}]'.format(''.join(nullChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, '', myString)
            log('AGNT  :: Search Query:: [{0}] after removing one of these {1}'.format(myString, pattern))
        else:
            log('AGNT  :: Search Query:: [{0}] found none of these {0}'.format(myString, pattern))

        # replace following with space
        spaceChars = ["@", '\-', ur'\u2013', ur'\u2014', '\(', '\)']  # to be replaced with space
        pattern = u'[{0}]'.format(''.join(spaceChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, ' ', myString)
            log('AGNT  :: Search Query:: [{0}] after removing one of these {1}'.format(myString, pattern))
        else:
            log('AGNT  :: Search Query:: [{0}] found none of these {0}'.format(myString, pattern))

        # examine first word
        # remove if indefinite word in french, english, portuguese, spanish, german
        myWords = myString.split()
        eng = ['a', 'an', 'the']
        fre = ['un', 'une', 'des', 'le', 'la', 'les', "l'"]
        prt = ['um', 'uma', 'uns', 'umas', 'o', 'a', 'os', 'as']
        esp = ['un', 'una', 'unos', 'unas', 'el', 'la', 'los', 'las']
        ger = ['ein', 'eine', 'eines', 'einen', 'einem', 'einer', 'das', 'die', 'der', 'dem', 'den', 'des']
        regexes = eng + fre + prt + esp + ger
        pattern = r'|'.join(r'\b{0}\b'.format(regex) for regex in regexes)
        matched = re.search(pattern, myWords[0].lower())  # match against first word
        if matched:
            myWords.remove(myWords[0])
            myString = ' '.join(myWords)
            log("AGNT  :: Search Query:: [{0}] after dropping first word [{1}]".format(myString, myWords[0]))
        else:
            log('AGNT  :: Search Query:: [{0}] drop not attempted. First word was not an indefinite article'.format(myString))

        # examine first word in string for numbers
        myWords = myString.split()
        pattern = r'[0-9]'
        matched = re.search(pattern, myWords[0])  # match against whole string
        if matched:
            numPos = matched.start()
            if numPos > 0:
                myWords[0] = myWords[0][:numPos]
                myString = ' '.join(myWords)
                log('AGNT  :: Search Query:: [{0}] after splitting at position <{1}> first word had one of these {2}'.format(myString, numPos, pattern))
            else:
                log('AGNT  :: Search Query:: [{0}] split not attempted as first charater of word [{1}] is a number'.format(myString, myWords[0][0]))
        else:
            log('AGNT  :: Search Query:: [{0}] split not attempted. First word had none of these {1}'.format(myString, pattern))

        # examine subsequent words in string for numbers and '&'
        myWords = myString.split()
        pattern = r'[0-9&]'
        matched = re.search(pattern, ' '.join(myWords[1:]))  # match against whole string
        if matched:
            numPos = matched.start() + len(myWords[0])
            myString = myString[:numPos]
            log('AGNT  :: Search Query:: [{0}] after splitting at position <{1}> subsequent words have some of these {2}'.format(myString, numPos, pattern))
        else:
            log('AGNT  :: Search Query:: [{0}] split not attempted. Subsequent words have none of these {1}'.format(myString, pattern))

        # remove continuous spaces in string
        myString = ' '.join(myString.split())

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myString = myString.replace('%25', '%').replace('*', '')

        # GEVI uses a maximum of 24 characters when searching
        myString = myString[:24].strip()
        myString = myString if myString[-1] != '%' else myString[:23]
        log('AGNT  :: Returned Search Query        : {0}'.format(myString))
        log(LOG_BIGLINE)

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return

        utils.logHeaders('SEARCH', media, lang)

        # Check filename format
        try:
            FILMDICT = utils.matchFilename(media)
        except Exception as e:
            log('SEARCH:: Error: %s', e)
            return

        log(LOG_BIGLINE)

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        # Finds the entire media enclosure <Table> element then steps through the rows
        morePages = True
        while morePages:
            log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
            except Exception as e:
                log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                return

            try:
                searchQuery = html.xpath('//a[text()="Next"]/@href')[0]
                searchQuery = "{0}/{1}".format(BASE_URL, searchQuery)   # href does not have base_url in it
                log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(searchQuery.split('&where')[0].split('page=')[1]) - 1
                morePages = True
            except:
                searchQuery = ''
                log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            titleList = html.xpath('//table[contains(@class,"d")]/tr/td[@class="cd"]/parent::tr')
            log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
            log(LOG_BIGLINE)
            for title in titleList:
                # Site Title
                try:
                    siteTitle = title[0].text_content().strip()
                    unwantedWords = ['[sic]']
                    for unwantedWord in unwantedWords:
                        if unwantedWord in siteTitle:
                            siteTitle = siteTitle.replace(unwantedWord, '')

                    utils.matchTitle(siteTitle, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Title: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('.//a/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    FILMDICT['SiteURL'] = siteURL
                    log('SEARCH:: Site Title url                %s', siteURL)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Title Url: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Title Type (Compilation)
                try:
                    siteType = title[4].text_content().strip()
                    FILMDICT['Compilation'] = "Yes" if siteType.lower() == 'compilation' else "No"
                    log('SEARCH:: Compilation?                  %s', FILMDICT['Compilation'])
                    log(LOG_BIGLINE)
                except:
                    log('SEARCH:: Error getting Site Type (Compilation)')
                    continue

                # Access Site URL for Studio and Release Date information
                try:
                    log('SEARCH:: Reading Site URL page         %s', siteURL)
                    html = HTML.ElementFromURL(siteURL, sleep=DELAY)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error reading Site URL page: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Studio/Distributor
                try:
                    foundStudio = False
                    htmlSiteStudio = html.xpath('//a[contains(@href, "/company/")]/parent::td//text()[normalize-space()]')
                    htmlSiteStudio = [x.strip() for x in htmlSiteStudio if x.strip()]
                    htmlSiteStudio = list(set(htmlSiteStudio))
                    log('SEARCH:: Site URL Distributor/Studio   %s', htmlSiteStudio)
                    for siteStudio in htmlSiteStudio:
                        try:
                            utils.matchStudio(siteStudio, FILMDICT)
                            foundStudio = True
                        except Exception as e:
                            log('SEARCH:: Error: %s', e)
                            log(LOG_SUBLINE)
                            continue
                        if foundStudio:
                            break

                    if not foundStudio:
                        log('SEARCH:: Error No Matching Site Studio')
                        log(LOG_SUBLINE)
                        continue

                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Studio %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Release Date
                siteReleaseDate = ''
                releaseDateMatchFail = False
                try:
                    htmlReleaseDate = html.xpath('//td[.="released" or .="produced"]/following-sibling::td[1]/text()[normalize-space()]')
                    htmlReleaseDate = [x if unicode(x, 'utf-8').isnumeric() else x.split('-')[0] if '-' in x else x.split(',')[0] if ',' in x else x[1:] if x[0] == 'c' else '' for x in htmlReleaseDate]
                    htmlReleaseDate = [x.strip() for x in htmlReleaseDate if x]
                    htmlReleaseDate = list(set(htmlReleaseDate))
                    log('SEARCH:: Site URL Release Dates        %s', htmlReleaseDate)
                    for ReleaseDate in htmlReleaseDate:
                        try:
                            ReleaseDate = utils.matchReleaseDate(ReleaseDate, FILMDICT)
                            siteReleaseDate = ReleaseDate
                            break
                        except Exception as e:
                            log('SEARCH:: Error: %s', e)
                            releaseDateMatchFail = True
                            continue
                    if FILMDICT['Year'] and not siteReleaseDate:
                        raise Exception('No Release Dates Found')

                    log(LOG_BIGLINE)

                except Exception as e:
                    if FILMDICT['Year']:
                        log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date [%s]', e)
                        log(LOG_SUBLINE)
                        if releaseDateMatchFail:
                            continue

                # Duration
                if MATCHSITEDURATION:
                    try:
                        siteDuration = html.xpath('//td[.="length"]/following-sibling::td[1]/text()[normalize-space()]')[0].strip()
                        log('SEARCH:: Site Film Duration            %s Minutes', siteDuration)
                        utils.matchDuration(siteDuration, FILMDICT, MATCHSITEDURATION)
                        log(LOG_BIGLINE)
                    except Exception as e:
                        log('SEARCH:: Error getting Site Film Duration: %s', e)
                        log(LOG_SUBLINE)
                        continue

                # GEVI usually sets its Genre to General Hardcore rather than having a more robust system like other websites, however it stores links to the film on the other websites
                # Check AEBN/GayDVDEmpire/GayHotMovies Links and take genre information from them: Store them as 'Genres'Key in FILMDICT
                FilmLinks = {}
                ignoreGenres = ['4k ultra hd', 'character', 'exclusive', 'feature', 'gay', 'hd movies', 'high definition', 'language', 'locale', 'movies', 'new release', 'plot', 'sale downloads', 'sale rentals', 'sale streaming', 'sale', 'settings', 'streaming video', 'website']
                genres = {}
                try:
                    webURLs = html.xpath('//td[contains(text(),"this production at")]/a/@href')
                    for webURL in webURLs:
                        if webURL not in FilmLinks:        # links are sometimes duplicated in GEVI
                            FilmLinks[webURL] = ''
                            fhtml = HTML.ElementFromURL(webURL, sleep=DELAY)
                            if 'aebn' in webURL:
                                fhtmlgenres = fhtml.xpath('//span[@class="dts-image-display-name"]/text()')
                                fhtmlgenres = [x.strip() for x in fhtmlgenres if x.strip()]
                                log('SEARCH:: AEBN Genres                   %s', fhtmlgenres)
                                for genre in fhtmlgenres:
                                    if anyOf(x in genre.lower() for x in ignoreGenres):
                                        continue
                                    if genre not in genres:
                                        genres[genre] = ''
                                    if 'compilation' in genre.lower():
                                        FILMDICT['Compilation'] = 'Compilation'
                            elif 'gayhotmovies' in webURL:
                                fhtmlgenres = fhtml.xpath('//a[contains(@href,"https://www.gayhotmovies.com/category/")]/@title')
                                fhtmlgenres = [x.strip() for x in fhtmlgenres if x.strip()]
                                log('SEARCH:: GayHotMovies Genres           %s', fhtmlgenres)
                                for genre in fhtmlgenres:
                                    if anyOf(x in genre.lower() for x in ignoreGenres):
                                        continue
                                    elif 'international' in genre.lower():
                                        continue
                                    else:
                                        genre = genre.replace('Bareback ->', 'Bareback ')
                                        genre = genre.split('->')[-1]
                                    if genre not in genres:
                                        genres[genre] = ''
                                    if 'compilation' in genre.lower():
                                        FILMDICT['Compilation'] = 'Compilation'
                            elif 'gaydvdempire' in webURL:
                                fhtmlgenres = fhtml.xpath('//ul[@class="list-unstyled m-b-2"]//a[@label="Category"]/text()[normalize-space()]')
                                fhtmlgenres = [x.strip() for x in fhtmlgenres if x.strip()]
                                log('SEARCH:: GayDVDEmpire Genres           %s', fhtmlgenres)
                                for genre in fhtmlgenres:
                                    if anyOf(x in genre.lower() for x in ignoreGenres):
                                        continue
                                    if genre not in genres:
                                        genres[genre] = ''
                                    if 'compilation' in genre.lower():
                                        FILMDICT['Compilation'] = 'Compilation'

                except Exception as e:
                    log('SEARCH:: Error getting View Production Links: %s', e)
                    log(LOG_SUBLINE)
                
                finally:
                    FILMDICT['Genres'] = {key.strip(): value for key, value in genres.items()}
                    log('SEARCH:: Genres Found                  %s', genres)

                # we should have a match on studio, title and year now. Find corresponding film on IAFD
                log('SEARCH:: Check for Film on IAFD:')
                utils.getFilmOnIAFD(FILMDICT)

                results.Append(MetadataSearchResult(id=json.dumps(FILMDICT), name=FILMDICT['Title'], score=100, lang=lang))
                log(LOG_BIGLINE)
                log('SEARCH:: Finished Search Routine')
                log(LOG_BIGLINE)
                return

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        utils.logHeaders('UPDATE', media, lang)

        # Fetch HTML.
        FILMDICT = json.loads(metadata.id)
        log('UPDATE:: Film Dictionary Variables:')
        for key in sorted(FILMDICT.keys()):
            log('UPDATE:: {0: <29}: {1}'.format(key, FILMDICT[key]))
        log(LOG_BIGLINE)

        html = HTML.ElementFromURL(FILMDICT['SiteURL'], timeout=60, errors='ignore', sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as above
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Tag line             : Corresponds to the url of movie
        #        d. Originally Available : set from metadata.id (search result)
        #        e. Content Rating       : Always X
        #        f. Content Rating Age   : Always 18
        #        g. Collection Info      : From title group of filename 

        # 1a.   Set Studio
        metadata.studio = FILMDICT['Studio']
        log('UPDATE:: Studio: %s' , metadata.studio)

        # 1b.   Set Title
        metadata.title = FILMDICT['Title']
        log('UPDATE:: Title: %s' , metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = FILMDICT['SiteURL']
        log('UPDATE:: Tagline: %s', metadata.tagline)
        if FILMDICT['Year']:
            metadata.originally_available_at = datetime.strptime(FILMDICT['CompareDate'], DATEFORMAT)
            metadata.year = metadata.originally_available_at.year
            log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)

        # 1e/f. Set Content Rating to Adult/18 years
        metadata.content_rating = 'X'
        metadata.content_rating_age = 18
        log('UPDATE:: Content Rating - Content Rating Age: X - 18')

        # 1g. Collection
        if COLCLEAR:
            metadata.collections.clear()

        collections = FILMDICT['Collection']
        for collection in collections:
            metadata.collections.add(collection)
        log('UPDATE:: Collection Set From filename: %s', collections)

        #    2.  Metadata retrieved from website
        #        a. Genre                : Alphabetic order
        #        b. Countries            : Alphabetic order
        #        c. Rating
        #        d. Directors            : List of Directors (alphabetic order)
        #        e. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        f. Posters/Background
        #        g. Summary

        # 2a.   Genre
        log(LOG_BIGLINE)
        try:
            genres = FILMDICT['Genres'] # genres in AEBN/GayDVDEmpire/GayHotMovies
            htmlgenres = html.xpath('//td[contains(text(),"category")]//following-sibling::td[1]/text()')[0]            # add GEVI categories to genres
            try:
                htmlbodyTypes = html.xpath('//td[contains(text(),"body types")]//following-sibling::td[1]/text()')[0]   # add GEVI body type to genres
                log('UPDATE:: Body Types Found: %s', htmlbodyTypes)
                htmlbodyTypes = htmlbodyTypes.replace('Hvy', 'Heavy')
                htmlgenres = htmlgenres + ',' + htmlbodyTypes
            except Exception as e:
                log('UPDATE:: Error getting Body Types: %s', e)

            htmlgenres = htmlgenres.split(',')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]   # trim and remove null elements
            for genre in htmlgenres:
                if genre not in genres:
                    genres[genre] = ''  # add genre as key, note values are always blank

            # reset htmlgenres to be a list containing keys of the genre dictionary and delete duplicated genres for example bear/bears - should leave only bears
            htmlgenres = list(genres.keys())
            log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)

            copygenres = htmlgenres[:]
            for index, genre in enumerate(htmlgenres):
                for copygenre in copygenres:
                    if genre != copygenre and genre in copygenre and len(copygenre.split()) == 1:
                        htmlgenres[index] = ''

            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]   # trim and remove null elements
            htmlgenres.sort()
            log('UPDATE:: %s Filtered and Sorted Genres: %s', len(htmlgenres), htmlgenres)

            metadata.genres.clear()
            for genre in htmlgenres:
                metadata.genres.add(genre)
                # add genres to collection
                if COLGENRE:
                    metadata.collections.add(genre)

        except Exception as e:
            log('UPDATE:: Error getting Genres: %s', e)

        # 2b.   Rating (out of 4 Stars) = Rating can be a maximum of 10 - float value
        log(LOG_BIGLINE)
        try:
            rating = html.xpath('//td[contains(text(),"rating out of 4")]//following-sibling::td[1]/text()')[0].strip()
            rating = rating.count('*') * 2.5
            log('UPDATE:: Film Rating %s', rating)
            metadata.rating = rating

        except Exception as e:
            metadata.rating = 0.0
            log('UPDATE:: Error getting Rating: %s', e)

        # 2c.   Countries
        log(LOG_BIGLINE)
        try:
            htmlcountries = html.xpath('//td[contains(text(),"location")]//following-sibling::td[1]/text()')
            htmlcountries = [x.strip() for x in htmlcountries if x.strip()]
            htmlcountries.sort()
            log('UPDATE:: Countries List %s', htmlcountries)
            metadata.countries.clear()
            for country in htmlcountries:
                metadata.countries.add(country)
                # add country to collection
                if COLCOUNTRY:
                    metadata.collections.add(country)

        except Exception as e:
            log('UPDATE:: Error getting Countries: %s', e)

        # 2d.   Directors
        log(LOG_BIGLINE)
        try:
            htmldirectors = html.xpath('//td[@class="pd"]/a[contains(@href, "/director/")]/text()')
            htmldirectors = ['{0}'.format(x.strip()) for x in htmldirectors if x.strip()]
            log('UPDATE:: Director List %s', htmldirectors)
            directorDict = utils.getDirectors(htmldirectors, FILMDICT)
            metadata.directors.clear()
            for key in sorted(directorDict):
                newDirector = metadata.directors.new()
                newDirector.name = key
                newDirector.photo = directorDict[key]
                # add director to collection
                if COLDIRECTOR:
                    metadata.collections.add(key)

        except Exception as e:
            log('UPDATE:: Error getting Director(s): %s', e)

        # 2e.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('//td[@class="pd"]/a[contains(@href, "/performer/")]//text()')
            log('UPDATE:: Cast List %s', htmlcast)
            castDict = utils.getCast(htmlcast, FILMDICT)

            # sort the dictionary and add key(Name)- value(Photo, Role) to metadata
            metadata.roles.clear()
            for key in sorted(castDict):
                newRole = metadata.roles.new()
                newRole.name = key
                newRole.photo = castDict[key]['Photo']
                newRole.role = castDict[key]['Role']
                # add cast name to collection
                if COLCAST:
                    metadata.collections.add(key)

        except Exception as e:
            log('UPDATE:: Error getting Cast: %s', e)

        # 2f.   Posters/Background Art
        #       GEVI does not distinguish between poster and back ground images - we assume first image is poster and second is background
        #           if there is only 1 image - apply it to both
        log(LOG_BIGLINE)
        try:
            htmlimages = html.xpath('//img/@src[contains(.,"Covers")]')
            htmlimages = [(BASE_URL if BASE_URL not in image else '') + image.replace('/Icons/','/') for image in htmlimages] 
            if len(htmlimages) == 1:    # if only one image duplicate it
                htmlimages.append(htmlimages[0])

            image = htmlimages[0]
            log('UPDATE:: Poster Image Found: [1] - %s', image)
            clear_posters(metadata)
            metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.posters.validate_keys([image])

            image = htmlimages[1]
            log('UPDATE:: Art Image Found: [2] - %s', image)
            clear_art(metadata)
            metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.art.validate_keys([image])

        except Exception as e:
            log('UPDATE:: Error getting Poster/Art: %s', e)

        # 2g.   Reviews - Put all Scene Information here IAFD + GEVI
        log(LOG_BIGLINE)

        # Legend
        try:
            htmllegend = html.xpath('//td[@class="sfn"]//text()')
            legend = ''.join(htmllegend).replace('\n', '').replace('=', ':').replace(';', '').strip()
            log('UPDATE:: Legend: %s', legend if legend else 'None Found')
        except Exception as e:
            legend = ''
            log('UPDATE:: Error getting Legend: %s', e)

        # Scenes
        log(LOG_SUBLINE)
        try:
            htmlscenes = html.xpath('//td[@class="scene"]')
            log('UPDATE:: Possible Number of Scenes [%s]', len(htmlscenes))

            metadata.reviews.clear()
            sceneCount = 0 # avoid enumerating the number of scenes as some films have empty scenes
            for count, scene in enumerate(htmlscenes, start=1):
                log('UPDATE:: Scene No %s', count)
                try:
                    try:
                        reviewSource = scene.xpath('./span[@class="plist"]//text()[normalize-space()]')
                        reviewSource = ''.join(reviewSource).strip()
                        reviewSource = re.sub(' \(.*?\)', '', reviewSource)    # GEVI sometimes has the studio in brackets after the cast name
                        log('UPDATE:: Scene Title: %s', reviewSource)
                    except:
                        log('UPDATE:: No Scene Title')
                        reviewSource = ''

                    try:
                        reviewText = scene.xpath('./span[@style]//text()[normalize-space()]')
                        reviewText = ''.join(reviewText).strip()
                        log('UPDATE:: Scene Text: %s', reviewText)
                    except:
                        log('UPDATE:: No Scene Writing')
                        reviewText = ''

                    # if no title and no scene write up
                    if not reviewSource and not reviewText:
                        continue
                    sceneCount += 1

                    newReview = metadata.reviews.new()
                    newReview.author = legend if legend else 'GEVI'
                    newReview.link = FILMDICT['SiteURL']
                    newReview.source = FILMDICT['Title']
                    if len(reviewSource) > 40:
                        for i in range(40, -1, -1):
                            if reviewSource[i] == ' ':
                                reviewSource = reviewSource[0:i]
                                break
                    newReview.source = '{0}. {1}...'.format(sceneCount, reviewSource if reviewSource else FILMDICT['Title'])
                    if len(reviewText) > 275:
                        for i in range(275, -1, -1):
                            if reviewText[i] in ['.', '!', '?']:
                                reviewText = reviewText[0:i + 1]
                                break
                    newReview.text = utils.TranslateString(reviewText, SITE_LANGUAGE, lang, DETECT)
                    log(LOG_SUBLINE)
                except Exception as e:
                    log('UPDATE:: Error getting Scene No. %s: %s', count, e)
        except Exception as e:
            log('UPDATE:: Error getting Scenes: %s', e)

        # 2h.   Summary = Synopsis with IAFD Legend
        log(LOG_BIGLINE)
        try:
            synopsis = ''
            htmlpromo = html.xpath('//td[contains(text(),"promo/")]//following-sibling::td//span[@style]/text()[following::br]')
            for item in htmlpromo:
                synopsis = '{0}\n{1}'.format(synopsis, item)
            log('UPDATE:: Synopsis Found: %s', synopsis)
            synopsis = synopsis.replace('\n', ' ')

            regex = r'View this scene at.*|found in compilation.*|see also.*|^\d+\.$'
            pattern = re.compile(regex, re.IGNORECASE | re.MULTILINE)
            synopsis = re.sub(pattern, '', synopsis)
            synopsis = utils.TranslateString(synopsis, SITE_LANGUAGE, lang, DETECT)
        except Exception as e:
            synopsis = ''
            log('UPDATE:: Error getting Synopsis: %s', e)

        # combine and update
        log(LOG_SUBLINE)
        summary = ('{0}\n{1}' if PREFIXLEGEND else '{1}\n{0}').format(FILMDICT['Legend'], synopsis.strip())
        summary = summary.replace('\n\n', '\n')
        metadata.summary = summary

        log(LOG_BIGLINE)
        log('UPDATE:: Finished Update Routine')
        log(LOG_BIGLINE)