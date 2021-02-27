#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# AVEntertainments - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    22 Dec 2020   2020.12.22.01    Creation
    22 Jan 2021   2020.12.22.02    Improved on IAFD search, actors sexual roles if recorded are returned, if not shows a red circle.
                                   fixed error with single quote in title, scrapping collection info added
    19 Feb 2021   2020.12.22.04    Moved IAFD and general functions to other py files
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
VERSION_NO = '2020.12.22.04'
PLUGIN_LOG_TITLE = 'AVEntertainments'
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

# URLS - in list format
BASE_URL = 'https://www.aventertainments.com'
BASE_SEARCH_URL = BASE_URL + '/search_products.aspx?Dept_ID=43&keyword={0}&whichOne=all&languageID=1&rows=3&SaveData=3'

# dictionary holding film variables
FILMDICT = {}

# Date Format used by website
DATEFORMAT = '%m/%d/%Y'

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
class AVEntertainments(Agent.Movies):
    ''' define Agent class '''
    name = 'AVEntertainments (IAFD)'
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

        # convert to lower case and trim and strip diacritics
        myString = myString.lower().strip()
        myString = String.StripDiacritics(myString)

        # strip non-alphanumeric characters bar space, comma and single quote
        pattern = ur"[^A-Za-z0-9',]+"
        myString = re.sub(pattern, ' ', myString, flags=re.IGNORECASE)
        myString = myString.replace('  ', ' ').strip()

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        myString = String.URLEncode('{0}'.format(myString)).replace('%25', '%').replace('*', '')
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

        morePages = True
        while morePages:
            self.log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
                # Finds the entire media enclosure
                titleList = html.xpath('//div[@class="single-slider-product__content  single-slider-product--list-view__content"]')
                if not titleList:
                    break
            except Exception as e:
                self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                return

            try:
                searchQuery = html.xpath('//li/a[@title="Next"]/@href')[0]
                self.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(searchQuery.split('CountPage=')[-1]) - 1
                morePages = True if pageNumber <= 10 else False
            except:
                searchQuery = ''
                self.log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
            self.log(LOG_BIGLINE)
            for title in titleList:
                # Site Title
                try:
                    siteTitle = title.xpath('./div/p[@class="product-title"]/a/text()')[0].split('(')[0].strip()
                    self.matchTitle(siteTitle, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Title: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('./div/p[@class="product-title"]/a/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    FILMDICT['SiteURL'] = siteURL
                    self.log('SEARCH:: Site Title url                %s', siteURL)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Title Url: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # Site Release Date
                try:
                    siteReleaseDate = title.xpath('./div/div/span[@class="availability-title"]/text()[not(contains(.,"Date:"))]')[0]
                    try:
                        siteReleaseDate = self.matchReleaseDate(siteReleaseDate, FILMDICT)
                        self.log(LOG_BIGLINE)
                    except Exception as e:
                        self.log('SEARCH:: Error getting Site URL Release Date: %s', e)
                        self.log(LOG_SUBLINE)
                        continue
                except:
                    self.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                    self.log(LOG_BIGLINE)

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
                    siteStudio = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Studio"]/following-sibling::span/a/text()')[0].strip()
                    self.matchStudio(siteStudio, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Studio: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

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
        #        b. Collections
        #        c. Directors            : List of Directors (alphabetic order)
        #        d. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        e. Posters/Background
        #        f. Summary

        # 2a.   Genres
        self.log(LOG_BIGLINE)
        try:
            ignoreGenres = ['3-D', 'Blu-ray Disc', "Editor's Pick", 'Gay', 'Gay - New Release', 'HD DVD', 'New Release', 'Pre Release', 'Sample Movies']
            genres = []
            htmlgenres = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Category"]/following-sibling::span/a/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                if anyOf(x in genre for x in ignoreGenres):
                    continue
                if 'compilation' in genre.lower():
                    FILMDICT['Compilation'] = 'Compilation'
                genre = genre.replace('Gay - ', '')
                genre = genre.split(' / ')
                genres = genres + genre

            genres.sort()
            self.log('UPDATE:: %s Genres Found: %s', len(genres), genres)
            metadata.genres.clear()
            for genre in genres:
                metadata.genres.add(genre)
                if COLGENRE:
                    metadata.collections.add(genre)

        except Exception as e:
            self.log('UPDATE:: Error getting Genres: %s', e)

        # 2b.   Collections
        self.log(LOG_BIGLINE)
        try:
            htmlcollections = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Series"]/following-sibling::span/a/text()')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            htmlcollections.sort()
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
            htmldirectors = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Director"]/following-sibling::span/a/text()')
            htmldirectors = [x for x in htmldirectors if 'N/A' not in x.upper()]
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

        # 2d.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        self.log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Starring"]/following-sibling::span/a/text()')
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

        # 2f.   Posters/Art
        self.log(LOG_BIGLINE)
        try:
            htmlimage = html.xpath('//a[text()="Cover Jacket"]/@href')[0]
            image = htmlimage.replace('bigcover', 'jacket_images') # replace text of dvd cover url to get poster
            self.log('UPDATE:: Poster Image Found: %s', image)
            #  set poster then only keep it
            metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.posters.validate_keys([image])

            image = htmlimage.replace('bigcover', 'screen_shot') # replace text of dvd cover url to get background
            self.log('UPDATE:: Art Image Found: %s', image)
            #  set Art then only keep it
            metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.art.validate_keys([image])

        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Art: %s', e)

        # 2g.   Summary = IAFD Legend + Synopsis
        self.log(LOG_BIGLINE)
        # synopsis
        try:
            synopsis = html.xpath('//div[@class="product-description mt-20"]/text()')[0].strip()
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