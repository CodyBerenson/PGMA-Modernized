#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# BestExclusivePorn - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    09 Aug 2020   2020.08.09.01    Creation
    07 Sep 2020   2020.08.09.02    Improved matching on film titles with apostrophes
                                   added cast scraping - actors restricted to 2 names
    15 Sep 2020   2020.08.09.03    removed enquotes around search string
    25 Sep 2020   2020.08.09.04    search string can only have a max of 59 characters
    07 Oct 2020   2020.08.09.05    IAFD - change to https
                                   get cast names from statting label if present
    22 Nov 2020   2020.08.09.06    leave words attached to commas in search string
    23 Dec 2020   2020.08.09.07    Save film in Title Case mode... as this agent detects actor names from the title as they have initial caps
    26 Dec 2020   2020.08.09.08    Improved on IAFD search, actors sexual roles if recorded are returned, if not shows a red circle.
                                   if actor is not credited on IAFD but is on Agent Site it shows as a Yellow Box below the actor
                                   sped up search by removing search by actor/director... less hits on IAFD per actor...
    09 Feb 2021   2020.08.09.10    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including LevenShtein Matching on Cast names
                                   set content_rating age to 18
                                   Set collections from filename and cast
                                   included studio on iafd processing of filename
                                   Added iafd legend to summary
                                   improved logging
                                   Added Thumbor / PIL Image processing
                                   improved matching on actors names - now picks Cutler X for example
-----------------------------------------------------------------------------------------------------------------------------------
'''
import datetime, platform, os, re, sys, subprocess, json, urllib
from unidecode import unidecode
from PIL import Image
from io import BytesIO
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2020.08.09.09'
PLUGIN_LOG_TITLE = 'BestExclusivePorn'
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

# PLEX API /CROP Script
load_file = Core.storage.load
CROPPER = r'CScript.exe "{0}/Plex Media Server/Plug-ins/BestExclusivePorn.bundle/Contents/Code/ImageCropper.vbs" "{1}" "{2}" "{3}" "{4}"'

# URLS
BASE_URL = 'http://bestexclusiveporn.com/'
BASE_SEARCH_URL = BASE_URL + '?s={0}'

# dictionary holding film variables
FILMDICT = {}   

# Date Format used by website
DATEFORMAT = '%B %d, %Y'

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
class BestExclusivePorn(Agent.Movies):
    ''' define Agent class '''
    name = 'BestExclusivePorn (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms', 'com.plexapp.agents.GayAdultScenes']

    # import IAFD Functions
    from iafd import *

    # import General Functions
    from genfunctions import *

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        self.log('AGNT  :: Original Search Query        : {0}'.format(myString))

        # convert to lower case and trim
        myString = myString.lower().strip()

        # remove words with apostrophes in them
        badChars = ["'", ur'\u2018', ur'\u2019', '-']
        pattern = u"\w*[{0}]\w*".format(''.join(badChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            self.log('AGNT :: Search Query:: Replacing characters in string. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, '', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            self.log('AGNT :: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('AGNT :: Search Query:: String has none of these {0}'.format(pattern))

        # Best Exclusive uses a maximum of 60 characters when searching
        myString = myString[:49].strip()
        myString = myString if myString[-1] != '%' else myString[:48]

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())
        myString = myString.replace('%25', '%').replace('*', '')
        self.log('AGNT  :: Returned Search Query        : {0}'.format(myString))
        self.log(LOG_BIGLINE)

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def getFilmImages(self, imageType, imageURL, whRatio):
        ''' get Film images - posters/background art and crop if necessary '''
        pic = imageURL
        picInfo = Image.open(BytesIO(HTTP.Request(pic).content))
        width, height = picInfo.size
        dispWidth = '{:,d}'.format(width)       # thousands separator
        dispHeight = '{:,d}'.format(height)     # thousands separator

        self.log('AGNT  :: {0} Found: Width ({1}) x Height ({2}); URL: {3}'.format(imageType, dispWidth, dispHeight, imageURL))

        maxHeight = float(width * whRatio)      # Maximum allowable height

        cropHeight = float(maxHeight if maxHeight <= height else height)
        cropWidth = float(cropHeight / whRatio)

        DxHeight = 0.0 if cropHeight == height else (abs(cropHeight - height) / height) * 100.0
        DxWidth = 0.0 if cropWidth == width else (abs(cropWidth - width) / width) * 100.0

        cropRequired = True if DxWidth >= 10 or DxHeight >=10 else False
        cropWidth = int(cropWidth)
        cropHeight = int(cropHeight)
        desiredWidth = '{0:,d}'.format(cropWidth)     # thousands separator
        desiredHeight = '{0:,d}'.format(cropHeight)   # thousands separator
        DxWidth = '{0:.2f}'.format(DxWidth)    # percent format
        DxHeight = '{0:.2f}'.format(DxHeight)  # percent format
        self.log('AGNT  :: Crop {0} {1}: Actual (w{2} x h{3}), Desired (w{4} x h{5}), % Dx = w[{6}%] x h[{7}%]'.format("Required:" if cropRequired else "Not Required:", imageType, dispWidth, dispHeight, desiredWidth, desiredHeight, DxWidth, DxHeight))
        if cropRequired:
            try:
                self.log('AGNT  :: Using Thumbor to crop image to: {0} x {1}'.format(desiredWidth, desiredHeight))
                pic = THUMBOR.format(cropWidth, cropHeight, imageURL)
                picContent = HTTP.Request(pic).content
            except Exception as e:
                self.log('AGNT  :: Error Thumbor Failed to Crop Image to: {0} x {1}'.format(desiredWidth, desiredHeight))
                try:
                    if os.name == 'nt':
                        self.log('AGNT  :: Using Script to crop image to: {0} x {1}'.format(desiredWidth, desiredHeight))
                        envVar = os.environ
                        TempFolder = envVar['TEMP']
                        LocalAppDataFolder = envVar['LOCALAPPDATA']
                        pic = os.path.join(TempFolder, imageURL.split("/")[-1])
                        cmd = CROPPER.format(LocalAppDataFolder, imageURL, pic, cropWidth, cropHeight)
                        subprocess.call(cmd)
                        picContent = load_file(pic)
                except Exception as e:
                    self.log('AGNT  :: Error Script Failed to Crop Image to: {0} x {1}'.format(desiredWidth, desiredHeight))
        else:
            picContent = HTTP.Request(pic).content

        return pic, picContent

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
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
                titleList = html.xpath('//div[contains(@class,"type-post status-publish")]')
                if not titleList:
                    break
            except Exception as e:
                self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                return

            try:
                searchQuery = html.xpath('//a[@class="next page-numbers"]/@href')[0]
                self.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(searchQuery.split('?')[0].split('/')[-1]) - 1
                morePages = True if pageNumber <= 10 else False
            except:
                searchQuery = ''
                self.log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
            self.log(LOG_BIGLINE)
            for title in titleList:
                # Site Entry
                try:
                    siteEntry = title.xpath('./h2[@class="title"]/a/text()')[0]
                    self.log('SEARCH:: Site Entry: %s', siteEntry)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Entry: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # normalise site entry and film title
                siteEntry = self.NormaliseComparisonString(siteEntry)
                normalisedFilmTitle = self.NormaliseComparisonString(FILMDICT['Title'])
                pattern = ur'{0}'.format(normalisedFilmTitle)
                matched = re.search(pattern, siteEntry, re.IGNORECASE)  # match against whole string
                if matched:
                    siteTitle = matched.group()
                    siteStudio = re.sub(pattern, '', siteEntry).strip()
                    self.log('SEARCH:: Studio and Studio from Site Entry: %s - %s', siteStudio, siteTitle)
                    self.log(LOG_BIGLINE)
                else:
                    self.log('SEARCH:: Failed to get Studio and Title from Site Entry:')
                    self.log(LOG_SUBLINE)
                    continue

                # Site Title
                try:
                    self.matchTitle(siteTitle, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Title: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('./h2[@class="title"]/a/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    FILMDICT['SiteURL'] = siteURL
                    self.log('SEARCH:: Site Title url                %s', siteURL)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Title Url: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # Studio Name
                try:
                    self.matchStudio(siteStudio, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Studio: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # Site Release Date
                try:
                    siteReleaseDate = title.xpath('./div[@class="post-info-top"]/span[@class="post-info-date"]/a[@rel="bookmark"]/text()')[0].strip()
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
        metadata.title = " ".join(word.capitalize() if "'s" in word else word.title() for word in FILMDICT['Title'].split())
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
        #        a.   Countries
        #        b.   Genres               : List of Genres (alphabetic order)
        #        c.   Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        d.   Posters/Art
        #        e.   Summary

        # 2a.   Countries
        self.log(LOG_BIGLINE)
        try:
            htmlcountries = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Country: ")]')[0].strip().replace('Country: ', '').split(',')
            htmlcountries = [x.strip() for x in htmlcountries if x]
            htmlcountries.sort()
            self.log('UPDATE:: Countries List %s', htmlcountries)
            metadata.countries.clear()
            for country in htmlcountries:
                metadata.countries.add(country)
                # add country to collection
                if COLCOUNTRY:
                    metadata.collections.add(country)

        except Exception as e:
            self.log('UPDATE:: Error getting Countries: %s', e)

        # 2b.   Genres
        self.log(LOG_BIGLINE)
        try:
            htmlgenres = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Genre: ")]')[0].strip().replace('Genre: ', '').split(',')
            htmlgenres = [x.strip() for x in htmlgenres if x]
            htmlgenres.sort()
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            if 'compilation' in [x.lower() for x in htmlgenres]:
                FILMDICT['Compilation'] = 'Compilation'
            metadata.genres.clear()
            for genre in htmlgenres:
                metadata.genres.add(genre)
                # add genre to collection
                if COLGENRE:
                    metadata.collections.add(genre)

        except Exception as e:
            self.log('UPDATE:: Error getting Genres: %s', e)

        # 2c.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        #             If there is a Starring heading use it to get the actors else try searching the title for the cast
        self.log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Starring: ")]')[0].strip().replace('Starring: ', '').split(',')

        except Exception as e:
            htmlcast = []
            self.log('UPDATE:: Error getting Cast: No Starring Entry, Get Cast from Film Title: %s', e)
            pattern = u'([A-Z]\w+(?=[\s\-][A-Z])(?:[\s\-][A-Z]\w*)+)'
            matches = re.findall(pattern, FILMDICT['Title'])  # match against Film title
            self.log('UPDATE:: Matches:: {0}'.format(matches))
            if matches:
                for count, castname in enumerate(matches, 1):
                    self.log('UPDATE:: {0}. Found Possible Cast Name: {1}'.format(count, castname))
                    if castname:
                        htmlcast.append(castname)
        try:
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

        # 2d  Posters/Art - First Image set to Poster, next to Art
        self.log(LOG_BIGLINE)
        imageType = 'Poster & Art'
        try:
            htmlimages = html.xpath('//div[@class="entry"]/p//img/@src')
            for index, image in enumerate(htmlimages):
                if index > 1:
                    break
                whRatio = 1.5 if index == 0 else 0.5625
                imageType = 'Poster' if index == 0 else 'Art'
                pic, picContent = self.getFilmImages(imageType, image, whRatio)    # height is 1.5 times the width for posters
                if index == 0:      # processing posters
                    #  clean up and only keep the posters we have added
                    metadata.posters[pic] = Proxy.Media(picContent, sort_order=1)
                    metadata.posters.validate_keys([pic])
                    self.log(LOG_SUBLINE)
                else:               # processing art
                    metadata.art[pic] = Proxy.Media(picContent, sort_order=1)
                    metadata.art.validate_keys([pic])

        except Exception as e:
            self.log('UPDATE:: Error getting %s: %s', imageType, e)

        # 2e.   Summary = IAFD Legend + Synopsis
        self.log(LOG_BIGLINE)
        # synopsis
        try:
            synopsis = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Description: ")]')[0].strip().replace('Description: ', '')
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