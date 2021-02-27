#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# CD Universe - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    31 Dec 2019   2019.12.31.01    Creation
    01 Jun 2020   2019.12.31.02    Implemented translation of summary
                                   improved getIAFDActor search
    27 Jun 2020   2019.12.31.03    Improvement to Summary Translation: Translate into Plex Library Language
                                   stripping of intenet domain suffixes from studio names when matching
                                   handling of unicode characters in film titles and comparision string normalisation
    07 Oct 2020   2020.12.31.04    IAFD - change to https
    22 Feb 2021   2020.12.31.06    Moved IAFD and general functions to other py files
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
VERSION_NO = '2019.12.31.06'
PLUGIN_LOG_TITLE = 'CD Universe'
LOG_BIGLINE = '------------------------------------------------------------------------------'
LOG_SUBLINE = '      ------------------------------------------------------------------------'

# Preferences
REGEX = Prefs['regex']                      # file matching pattern
DELAY = int(Prefs['delay'])                 # Delay used when requesting HTML, may be good to have to prevent being banned from the site
DETECT = Prefs['detect']                    # detect the language the summary appears in on the web page
COLCLEAR = Prefs['clearcollections']        # clear previously set collections
COLSTUDIO = Prefs['studiocollection']       # add studio name to collection
COLTITLE = Prefs['titlecollection']         # add title [parts] to collection
COLGENRE = Prefs['genrecollection']         # add genres to collection
COLDIRECTOR = Prefs['directorcollection']   # add director to collection
COLCAST = Prefs['castcollection']           # add cast to collection
COLCOUNTRY = Prefs['countrycollection']     # add country to collection

# IAFD Related variables
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/results.asp?searchtype=comprehensive&searchstring={0}'

IAFD_ABSENT = u'\U0000274C'        # red cross mark - not on IAFD
IAFD_FOUND = u'\U00002705'         # heavy white tick on green - on IAFD
IAFD_THUMBSUP = u'\U0001F44D'      # thumbs up unicode character
IAFD_THUMBSDOWN = u'\U0001F44E'    # thumbs down unicode character
IAFD_LEGEND = u'CAST LEGEND\u2003{0} Actor not on IAFD\u2003{1} Actor on IAFD\u2003:: {2} Film on IAFD ::\n'

# URLS
BASE_URL = 'https://www.cduniverse.com'
BASE_SEARCH_URL = BASE_URL + '/sresult.asp?HT_Search_Info={0}&HT_SEARCH=TITLE&style=gay&thx=1'

# dictionary holding film variables
FILMDICT = {}

# Date Format used by website
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
class CDUniverse(Agent.Movies):
    ''' define Agent class '''
    name = 'CD Universe (IAFD)'
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
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        self.log('AGNT  :: Original Search Query        : {0}'.format(myString))

        myString = myString.strip().lower()
        myString = myString.replace('-', '').replace(ur'\u2013', '').replace(ur'\u2014', '')
        myString = ' '.join(myString.split())   # remove continous white space

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString)

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myString = myString.replace('%25', '%').replace('*', '')
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
        self.log('SEARCH:: Prefs-> delay                : %s', DELAY)
        self.log('SEARCH::      -> Collection Gathering')
        self.log('SEARCH::         -> Studio            : %s', COLSTUDIO)
        self.log('SEARCH::         -> Film Title        : %s', COLTITLE)
        self.log('SEARCH::         -> Genres            : %s', COLGENRE)
        self.log('SEARCH::         -> Director(s)       : %s', COLDIRECTOR)
        self.log('SEARCH::         -> Film Cast         : %s', COLCAST)
        self.log('SEARCH::      -> Language Detection   : %s', DETECT)
        self.log('SEARCH:: Library:Site Language        : %s:%s', lang, SITE_LANGUAGE)
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
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        try:
            html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
            # Finds the entire media enclosure
            titleList = html.xpath('//*[@class="chunkytitle"]')
            if not titleList:
                break
        except Exception as e:
            self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
            return

        self.log('SEARCH:: Titles List: %s Found', len(titleList))
        self.log(LOG_BIGLINE)
        for title in titleList:
            try:
                siteTitle = title.text
                self.matchTitle(siteTitle, FILMDICT)
                self.log(LOG_BIGLINE)
            except Exception as e:
                self.log('SEARCH:: Error getting Site Title: %s', e)
                self.log(LOG_SUBLINE)
                continue

            # Site Title URL
            try:
                siteURL = title.get('href')
                siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                FILMDICT['SiteURL'] = siteURL
                self.log('SEARCH:: Site Title url                %s', siteURL)
                self.log(LOG_BIGLINE)
            except Exception as e:
                self.log('SEARCH:: Error getting Site Title Url: %s', e)
                self.log(LOG_SUBLINE)
                continue

            # Access Site URL for Studio and Release Date information
            try:
                self.log('SEARCH:: Reading Site URL page         %s', siteURL)
                html = HTML.ElementFromURL(siteURL, sleep=DELAY)
                self.log(LOG_BIGLINE)
            except Exception as e:
                self.log('SEARCH:: Error reading Site URL page: %s', e)
                self.log(LOG_SUBLINE)
                continue

            # Studio Name
            try:
                siteStudio = html.xpath('//a[@id="studiolink"]/text()')[0]
                self.matchStudio(siteStudio, FILMDICT)
                self.log(LOG_BIGLINE)
            except Exception as e:
                self.log('SEARCH:: Error getting Site Studio: %s', e)
                self.log(LOG_SUBLINE)
                continue

            # Site Release Date
            try:
                siteReleaseDate = html.xpath('//td[text()="Release Date"]/following-sibling::td/text()')[0].strip()
                try:
                    siteReleaseDate = self.matchReleaseDate(siteReleaseDate, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Release Date: %s', e)
                    self.log(LOG_SUBLINE)
                    continue
            except:
                self.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                self.log(LOG_BIGLINE)

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
        self.log('UPDATE:: Version    : v.%s', VERSION_NO)
        self.log('UPDATE:: File Name  : %s', filename)
        self.log('UPDATE:: File Folder: %s', folder)
        self.log(LOG_BIGLINE)

        # Fetch HTML.
        FILMDICT = json.loads(metadata.id)
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
        #        a. Genres               : List of Genres (alphabetic order)
        #        b. Directors            : List of Directors (alphabetic order)
        #        c. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        d. Posters/Art
        #        e. Summary

        # 2a.   Genres
        self.log(LOG_BIGLINE)
        try:
            genres = []
            ignoreGenres = ['4 Hour', '8 Hour', 'HD - High Definition', 'Interactive', 'Multi-Pack', 'Shot In 4K', 'Video On Demand']
            htmlgenres = html.xpath('//td[text()="Category"]/following-sibling::td/a/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                if anyOf(x in genre for x in ignoreGenres):
                    continue
                if 'compilation' in genre.lower():
                    FILMDICT['Compilation'] = 'Compilation'
                genre = genre.split(' / ')
                genres = genres + genre

            genres.sort()
            metadata.genres.clear()
            for genre in genres:
                metadata.genres.add(genre)
                # add genre to collection
                if COLGENRE:
                    metadata.collections.add(genre)

        except Exception as e:
            self.log('UPDATE:: Error getting Genres: %s', e)

        # 2b.   Directors
        self.log(LOG_BIGLINE)
        try:
            htmldirectors = html.xpath('//td[text()="Director"]/following-sibling::td/a/text()')
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

        # 2c.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        self.log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('//td[text()="Starring"]/following-sibling::td/a/text()')
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

        # 2d.   Posters/Art - no Art pictures so use the poster as Art
        self.log(LOG_BIGLINE)
        try:
            image = html.xpath('//img[@id="PIMainImg"]/@src')[0]
            self.log('UPDATE:: Poster Image Found: %s', image)
            #  set poster then only keep it
            metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.posters.validate_keys([image])

            #  set Art then only keep it
            image = html.xpath('//img[@id="0"]/@src')[0]
            self.log('UPDATE:: Art Image Found: %s', image)
            metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.art.validate_keys([image])

        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Art: %s', e)

        # 2e.   Summary = IAFD Legend + Synopsis
        self.log(LOG_BIGLINE)
        # synopsis
        try:
            synopsis = html.xpath('.//div[@id="Description"]/span/text()')[0]
            self.log('UPDATE:: Synopsis Found: %s', synopsis)
        except Exception as e:
            synopsis = ''
            self.log('UPDATE:: Error getting Synopsis: %s', e)

        # combine and update
        self.log(LOG_SUBLINE)
        summary = IAFD_LEGEND.format(IAFD_ABSENT, IAFD_FOUND, IAFD_THUMBSUP if FILMDICT['FoundOnIAFD'] == "Yes" else IAFD_THUMBSDOWN) + synopsis
        metadata.summary = self.TranslateString(summary, lang)

        self.log(LOG_BIGLINE)
        self.log('UPDATE:: Finished Update Routine')
        self.log(LOG_BIGLINE)