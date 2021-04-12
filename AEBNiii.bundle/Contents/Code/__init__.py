# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# AEBNiii - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    21 May 2020   2020.05.21.01    Creation: using current AdultEntertainmentBroadcastNetwork website - added scene breakdown to summary
    01 Jun 2020   2020.05.21.02    Implemented translation of summary
                                   improved getIAFDActor search
    27 Jun 2020   2020.05.21.03    Improvement to Summary Translation: Translate into Plex Library Language
                                   stripping of intenet domain suffixes from studio names when matching
                                   handling of unicode characters in film titles and comparision string normalisation
    01 Jul 2020   2020.05.21.03	   Renamed to AEBNiii
    14 Jul 2020   2020.05.21.04    Enhanced seach to also look through the exact matches, as AEBN does not always put these
                                   in the general search results
    07 Oct 2020   2020.05.21.05    IAFD - change to https
    09 Jan 2021   2020.05.21.06    IAFD - New Search Routine + Auto Collection setting
    19 Feb 2021   2020.05.21.08    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including LevenShtein Matching on Cast names
                                   set content_rating age to 18
                                   Set collections from filename + countries, cast and directors
                                   Added directors photos
                                   included studio on iafd processing of filename
                                   Added iafd legend to summary
                                   improved logging

-----------------------------------------------------------------------------------------------------------------------------------
'''
import datetime, platform, os, re, sys, json
from unidecode import unidecode
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2020.05.21.08'
PLUGIN_LOG_TITLE = 'AEBN iii'
LOG_BIGLINE = '------------------------------------------------------------------------------'
LOG_SUBLINE = '      ------------------------------------------------------------------------'

# Preferences
REGEX = Prefs['regex']                      # file matching pattern
YEAR = Prefs['year']                        # is year mandatory in the filename?
DELAY = int(Prefs['delay'])                 # Delay used when requesting HTML, may be good to have to prevent being banned from the site
DETECT = Prefs['detect']                    # detect the language the summary appears in on the web page
PREFIXLEGEND = Prefs['prefixlegend']        # place cast legend at start of summary or end
COLCLEAR = Prefs['clearcollections']        # clear previously set collections
COLSTUDIO = Prefs['studiocollection']       # add studio name to collection
COLTITLE = Prefs['titlecollection']         # add title [parts] to collection
COLGENRE = Prefs['genrecollection']         # add genres to collection
COLDIRECTOR = Prefs['directorcollection']   # add director to collection
COLCAST = Prefs['castcollection']           # add cast to collection
COLCOUNTRY = Prefs['countrycollection']     # add country to collection
BACKGROUND = Prefs['background']            # download art
ACT_AS_GENRE = Prefs['acts']                # using sex acts as categories

# IAFD Related variables
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/results.asp?searchtype=comprehensive&searchstring={0}'

IAFD_ABSENT = u'\U0000274C'        # red cross mark - not on IAFD
IAFD_FOUND = u'\U00002705'         # heavy white tick on green - on IAFD
IAFD_THUMBSUP = u'\U0001F44D'      # thumbs up unicode character
IAFD_THUMBSDOWN = u'\U0001F44E'    # thumbs down unicode character
IAFD_LEGEND = u'CAST LEGEND\u2003{0} Actor not on IAFD\u2003{1} Actor on IAFD\u2003:: {2} Film on IAFD ::\n'

# URLS
BASE_URL = 'https://gay.aebn.com'
BASE_SEARCH_URL = [BASE_URL + '/gay/search/?sysQuery={0}', BASE_URL + '/gay/search/movies/page/1?sysQuery={0}&criteria=%7B%22sort%22%3A%22Relevance%22%7D']

# dictionary holding film variables
FILMDICT = {}

# Date Formats used by website
DATEFORMAT = '%b %d, %Y'

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
class AEBNiii(Agent.Movies):
    ''' define Agent class '''
    name = 'AEBN iii (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # import IAFD Functions
    from iafd import *

    # import General Functions
    from genfunctions import *

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchFilmTitle(self, ExactMatches, title, FILMDICT):
        ''' match Film in list returned by running the query '''
        matched = True

        # Site Title
        try:
            siteTitle = title.xpath('./section//h1/a/text()')[0] if ExactMatches else title.xpath('./a//img/@title')[0]
            self.matchTitle(siteTitle, FILMDICT)
            self.log(LOG_BIGLINE)
        except Exception as e:
            self.log('AGNT  :: Error getting Site Title: %s', e)
            self.log(LOG_SUBLINE)
            matched = False

        # Site Title URL
        if matched:
            try:
                siteURL = title.xpath('./section//h1/a/@href')[0] if ExactMatches else title.xpath('./a/@href')[0]
                siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                FILMDICT['SiteURL'] = siteURL
                self.log('AGNT  :: Site Title URL                %s', siteURL)
                self.log(LOG_BIGLINE)
            except:
                self.log('AGNT  :: Error getting Site Title Url')
                self.log(LOG_SUBLINE)
                matched = False

        # Access Site URL for Studio and Release Date information only when looking at non exact match titles
        if matched:
            if not ExactMatches:
                try:
                    self.log('AGNT  :: Reading Site URL page         %s', siteURL)
                    html = HTML.ElementFromURL(FILMDICT['SiteURL'], sleep=DELAY)
                except Exception as e:
                    self.log('AGNT  :: Error reading Site URL page: %s', e)
                    self.log(LOG_SUBLINE)
                    matched = False

        # Site Studio
        if matched:
            foundStudio = False
            try:
                htmlSiteStudio = title.xpath('./section//li[contains(@class,"item-studio")]/a/text()') if ExactMatches else html.xpath('//div[@class="dts-studio-name-wrapper"]/a/text()')
                self.log('AGNT  :: %s Site URL Studios            %s', len(htmlSiteStudio), htmlSiteStudio)
                for siteStudio in htmlSiteStudio:
                    try:
                        self.matchStudio(siteStudio, FILMDICT)
                        foundStudio = True
                    except Exception as e:
                        self.log('AGNT  :: Error: %s', e)
                        self.log(LOG_SUBLINE)

                    if foundStudio:
                        self.log(LOG_BIGLINE)
                        break
            except Exception as e:
                self.log('AGNT  :: Error getting Site Studio %s', e)
                self.log(LOG_SUBLINE)
                matched = False

            if not foundStudio:
                self.log('AGNT  :: Error No Matching Site Studio')
                self.log(LOG_SUBLINE)
                matched = False

        # Site Release Date
        if matched:
            try:
                siteReleaseDate = title.xpath('./section//li[contains(@class,"item-release-date")]/text()')[0] if ExactMatches else html.xpath('//li[contains(@class,"item-release-date")]/text()')[0]
                siteReleaseDate = siteReleaseDate.strip().lower()
                siteReleaseDate = siteReleaseDate.replace('sept ', 'sep ').replace('july ', 'jul ')
                self.log('AGNT  :: Site URL Release Date         %s', siteReleaseDate)
                try:
                    siteReleaseDate = self.matchReleaseDate(siteReleaseDate, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('AGNT  :: Error getting Site URL Release Date: %s', e)
                    self.log(LOG_SUBLINE)
                    matched = False
            except:
                self.log('AGNT  :: Error getting Site URL Release Date: Default to Filename Date')
                self.log(LOG_SUBLINE)

        return matched

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        self.log('AGNT  :: Original Search Query        : {0}'.format(myString))

        # convert to lower case and trim and strip diacritics, fullstops, enquote
        myString = myString.replace('.', '').replace('-', '')
        myString = myString.lower().strip()
        myString = String.StripDiacritics(myString)

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myNormalString = String.URLEncode(myString).replace('%25', '%').replace('*', '')
        myQuotedString = String.URLEncode('"{0}"'.format(myString)).replace('%25', '%').replace('*', '')
        myString = [myQuotedString, myNormalString]
        self.log('AGNT  :: Returned Search Query        : {0}'.format(myString))
        self.log(LOG_BIGLINE)

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])

        self.log(LOG_BIGLINE)
        self.log('SEARCH:: Version                      : v.%s', VERSION_NO)
        self.log('SEARCH:: Python                       : %s', sys.version_info)
        self.log('SEARCH:: Platform                     : %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Preferences:')
        self.log('SEARCH::  > Cast Legend Before Summary: %s', PREFIXLEGEND)
        self.log('SEARCH::  > Collection Gathering')
        self.log('SEARCH::      > Cast                  : %s', COLCAST)
        self.log('SEARCH::      > Director(s)           : %s', COLDIRECTOR)
        self.log('SEARCH::      > Studio                : %s', COLSTUDIO)
        self.log('SEARCH::      > Film Title            : %s', COLTITLE)
        self.log('SEARCH::      > Genres                : %s', COLGENRE)
        self.log('SEARCH::  > Delay                     : %s', DELAY)
        self.log('SEARCH::  > Language Detection        : %s', DETECT)
        self.log('SEARCH::  > Library:Site Language     : %s:%s', lang, SITE_LANGUAGE)
        self.log('SEARCH:: Media Title                  : %s', media.title)
        self.log('SEARCH:: File Name                    : %s', filename)
        self.log('SEARCH:: File Folder                  : %s', folder)
        self.log(LOG_BIGLINE)

        # Check filename format
        try:
            FILMDICT = self.matchFilename(filename)
        except Exception as e:
            self.log('SEARCH:: Error: %s', e)
            return
        self.log(LOG_BIGLINE)

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitleList = self.CleanSearchString(FILMDICT['SearchTitle'])
        for count, searchTitle in enumerate(searchTitleList, start=1):
            searchQuery = BASE_SEARCH_URL[0].format(searchTitle)
            self.log('SEARCH:: %s. Exact Match Search Query: %s', count, searchQuery)

            # first check exact matches
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
                titleList = html.xpath('//section[contains(@class,"dts-panel-exact-match")]/div[@class="dts-panel-content"]')
                for title in titleList:
                    matchedTitle = self.matchFilmTitle(True, title, FILMDICT)

                    # we should have a match on studio, title and year now
                    if matchedTitle:
                        self.log('SEARCH:: Finished Search Routine')
                        self.log(LOG_BIGLINE)
                        results.Append(MetadataSearchResult(id=json.dumps(FILMDICT), name=FILMDICT['Title'], score=100, lang=lang))
                        return
            except Exception as e:
                self.log('SEARCH:: Error: Search Query did find any Exact Movie Matches: %s', e)

            # if we get here there were no exact matches returned by the search query, so search through the rest
            searchQuery = BASE_SEARCH_URL[1].format(searchTitle)
            self.log('SEARCH:: %s. General Search Query: %s', count, searchQuery)
            morePages = True
            while morePages:
                self.log('SEARCH:: Search Query: %s', searchQuery)
                try:
                    html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
                    # Finds the entire media enclosure
                    titleList = html.xpath('//div[@class="dts-image-overlay-container"]')
                    if not titleList:
                        break   # out of WHILE loop to the FOR loop
                except Exception as e:
                    self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                    return

                try:
                    searchQuery = html.xpath('//ul[@class="dts-pagination"]/li[@class="active" and text()!="..."]/following::li/a[@class="dts-paginator-tagging"]/@href')[0]
                    searchQuery = (BASE_URL if BASE_URL not in searchQuery else '') + searchQuery
                    self.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                    pageNumber = int(html.xpath('//ul[@class="dts-pagination"]/li[@class="active" and text()!="..."]/text()')[0])
                    morePages = True if pageNumber <= 10 else False
                except:
                    searchQuery = ''
                    self.log('SEARCH:: No More Pages Found')
                    pageNumber = 1
                    morePages = False

                self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
                self.log(LOG_BIGLINE)
                for title in titleList:
                    # get film variables in dictionary format: if dict is filled we have a match
                    matchedTitle = self.matchFilmTitle(False, title, FILMDICT)
                    if matchedTitle:
                        # we should have a match on studio, title and year now
                        self.log('SEARCH:: Finished Search Routine')
                        self.log(LOG_BIGLINE)
                        results.Append(MetadataSearchResult(id=json.dumps(FILMDICT), name=FILMDICT['Title'], score=100, lang=lang))
                        return

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log(LOG_BIGLINE)
        self.log('UPDATE:: Version                      : v.%s', VERSION_NO)
        self.log('UPDATE:: File Name                    : %s', filename)
        self.log('UPDATE:: File Folder                  : %s', folder)
        self.log(LOG_BIGLINE)

        # Fetch HTML.
        FILMDICT = json.loads(metadata.id)
        self.log('UPDATE:: Film Dictionary Variables:')
        for key in sorted(FILMDICT.keys()):
            self.log('UPDATE:: {0: <29}: {1}'.format(key, FILMDICT[key]))
        self.log(LOG_BIGLINE)

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
        self.log('UPDATE:: Studio: %s' , metadata.studio)

        # 1b.   Set Title
        metadata.title = FILMDICT['Title']
        self.log('UPDATE:: Title: %s' , metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = FILMDICT['SiteURL']
        if 'CompareDate' in FILMDICT:
            metadata.originally_available_at = datetime.datetime.strptime(FILMDICT['CompareDate'], DATEFORMAT)
            metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Tagline: %s', metadata.tagline)
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)

        # 1e/f. Set Content Rating to Adult/18 years
        metadata.content_rating = 'X'
        metadata.content_rating_age = 18
        self.log('UPDATE:: Content Rating - Content Rating Age: X - 18')

        # 1g. Collection
        if COLCLEAR:
            metadata.collections.clear()

        collections = FILMDICT['Collection']
        for collection in collections:
            metadata.collections.add(collection)
        self.log('UPDATE:: Collection Set From filename: %s', collections)

        #    2.  Metadata retrieved from website
        #        a. Genres
        #        b. Collections
        #        c. Directors            : List of Drectors (alphabetic order)
        #        d. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        e. Posters/Background
        #        f. Summary              : Synopsis + Scene Breakdowns

        # 2a.   Genres
        self.log(LOG_BIGLINE)
        try:
            ignoreGenres = ['feature', 'exclusive', 'new release']
            genres = []
            htmlgenres = html.xpath('//span[@class="dts-image-display-name"]/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres = [x for x in htmlgenres if x.strip()]
            htmlgenres.sort()
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                if anyOf(x in genre.lower() for x in ignoreGenres):
                    continue
                genres.append(genre)
                if 'compilation' in genre.lower():
                    FILMDICT['Compilation'] = 'Compilation'

            metadata.genres.clear()
            for genre in genres:
                metadata.genres.add(genre)
                # add genres to collection
                if COLGENRE:
                    metadata.collections.add(genre)


        except Exception as e:
            self.log('UPDATE:: Error getting Genres: %s', e)

        # 2b.   Collections
        self.log(LOG_BIGLINE)
        try:
            htmlcollections = html.xpath('//li[@class="section-detail-list-item-series"]/span/a/span/text()')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            self.log('UPDATE:: %s Collections Found: %s', len(htmlcollections), htmlcollections)
            for collection in htmlcollections:
                if collection.lower() in map(str.lower, FILMDICT['Collection']):  # if set by filename its already in the list - FILMDICT['Collection'] contains a list
                    continue
                metadata.collections.add(collection)
                self.log('UPDATE:: %s Collection Added: %s', collection)
        except Exception as e:
            self.log('UPDATE:: Error getting Collections: %s', e)

        # 2c.   Directors
        self.log(LOG_BIGLINE)
        try:
            htmldirectors = html.xpath('//li[@class="section-detail-list-item-director"]/span/a/span/text()')
            htmldirectors = ['{0}'.format(x.strip()) for x in htmldirectors if x.strip()]
            self.log('UPDATE:: Director List %s', htmldirectors)
            directorDict = self.getIAFD_Director(htmldirectors, FILMDICT)
            metadata.directors.clear()
            for key in sorted(directorDict):
                newDirector = metadata.directors.new()
                newDirector.name = key
                newDirector.photo = directorDict[key]
                # add director to collection
                if COLDIRECTOR:
                    metadata.collections.add(key)

        except Exception as e:
            self.log('UPDATE:: Error getting Director(s): %s', e)

        # 2d.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list and have more actor photos than AdultEntertainmentBroadcastNetwork
        self.log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('//div[@class="dts-star-name-overlay"]/text()')
            castdict = self.ProcessIAFD(htmlcast, FILMDICT)

            # sort the dictionary and add key(Name)- value(Photo, Role) to metadata
            metadata.roles.clear()
            for key in sorted(castdict):
                newRole = metadata.roles.new()
                newRole.name = key
                newRole.photo = castdict[key]['Photo']
                newRole.role = castdict[key]['Role']
                # add cast name to collection
                if COLCAST:
                    metadata.collections.add(key)

        except Exception as e:
            self.log('UPDATE:: Error getting Cast: %s', e)


        # 2e.   Posters/Art - Front Cover set to poster, Back Cover to art
        self.log(LOG_BIGLINE)
        try:
            htmlimages = html.xpath('//*[contains(@class,"dts-movie-boxcover")]//img/@src')
            image = htmlimages[0].split('?')[0]
            image = ('http:' if 'http:' not in image else '') + image
            self.log('UPDATE:: Poster Image Found: %s', image)
            #  clean up and only keep the poster we have added
            metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.posters.validate_keys([image])

            if BACKGROUND:
                self.log(LOG_SUBLINE)
                image = htmlimages[1].split('?')[0]
                image = ('http:' if 'http:' not in image else '') + image
                self.log('UPDATE:: Art Image Found: %s', image)
                #  clean up and only keep the Art we have added
                metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
                metadata.art.validate_keys([image])
        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Art: %s', e)

        # 2f.   Summary = IAFD Legend + Synopsis + Scene Information
        # synopsis
        try:
            synopsis = html.xpath('//div[@class="dts-section-page-detail-description-body"]/text()')[0].strip()
            self.log('UPDATE:: Synopsis Found: %s', synopsis)
        except Exception as e:
            synopsis = ''
            self.log('UPDATE:: Error getting Synopsis: %s', e)

        # scene information
        self.log(LOG_SUBLINE)
        allscenes = ''
        allacts = []
        try:
            htmlheadings = html.xpath('//header[@class="dts-panel-header"]/div/h1[contains(text(),"Scene")]/text()')
            htmlscenes = html.xpath('//div[@class="dts-scene-info dts-list-attributes"]')
            self.log('UPDATE:: %s Scenes Found: %s', len(htmlscenes), htmlscenes)
            for (heading, htmlscene) in zip(htmlheadings, htmlscenes):
                settingsList = htmlscene.xpath('./ul/li[descendant::span[text()="Settings:"]]/a/text()')
                if settingsList:
                    self.log('UPDATE:: %s Setting Found: %s', len(settingsList), settingsList)
                    settings = ', '.join(settingsList)
                    scene = ('\n[ {0} ] . . . . Setting: {1}').format(heading.strip(), settings)
                else:
                    scene = '\n[ {0} ]'.format(heading.strip())
                starsList = htmlscene.xpath('./ul/li[descendant::span[text()="Stars:"]]/a/text()')
                if starsList:
                    starsList = [x.split('(')[0] for x in starsList]
                    self.log('UPDATE:: %s Stars Found: %s', len(starsList), starsList)
                    stars = ', '.join(starsList)
                    scene += '. . . . Stars: {0}'.format(stars)

                actsList = htmlscene.xpath('./ul/li[descendant::span[text()="Sex acts:"]]/a/text()')
                if actsList:
                    if ACT_AS_GENRE:
                        for act in actsList:
                            if act not in allacts:
                                allacts.append(act)
                                metadata.genres.add(act)
                    self.log('UPDATE:: %s Sex Acts Found: %s', len(actsList), actsList)
                    acts = ', '.join(actsList)
                    scene += '\nSex Acts: {0}'.format(acts)
                allscenes += scene
        except Exception as e:
            scene = ''
            self.log('UPDATE:: Error getting Scene Breakdown: %s', e)

        allscenes = '\nScene Breakdown:\n{0}'.format(allscenes) if allscenes else ''

        # combine and update
        self.log(LOG_SUBLINE)
        castLegend = IAFD_LEGEND.format(IAFD_ABSENT, IAFD_FOUND, IAFD_THUMBSUP if FILMDICT['FoundOnIAFD'] == "Yes" else IAFD_THUMBSDOWN)
        summary = ('{0}\n{1}\n{2}' if PREFIXLEGEND else '{1}\n{2}\n{0}').format(castLegend, synopsis.strip(), allscenes.strip())
        summary = summary.replace('\n\n', '\n')
        metadata.summary = self.TranslateString(summary, lang)

        self.log(LOG_BIGLINE)
        self.log('UPDATE:: Finished Update Routine')
        self.log(LOG_BIGLINE)
