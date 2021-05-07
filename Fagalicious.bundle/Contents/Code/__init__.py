#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# Fagalicious - (IAFD)
                                    Version History
                                    ---------------
    Date            Version             Modification
    22 Dec 2019   2020.01.18.1     Creation
    19 Apr 2020   2020.01.18.9     Corrected image cropping
                                   added new xpath for titles with video image as main image
                                   improved multiple result pages handling
                                   removed debug print option
    29 Apr 2020   2020.01.18.10    updated IAFD routine, corrected error in multiple page processing
    01 Jun 2020   2020.01.18.11    Implemented translation of summary
                                   improved getIAFDActor search
    25 Jun 2020   2020.01.18.12    Improvement to Summary Translation: Translate into Plex Library Language
                                   stripping of intenet domain suffixes from studio names when matching
                                   handling of unicode characters in film titles and comparision string normalisation
    25 Jul 2020   2020.01.18.13    changed replacement of hyphens etc to null with hyphens to space when building 
                                   the search string, added chars u\2011 (nonbreaking hyphen) and u\2012 (figure dash)
    28 Feb 2021   2020.01.18.20    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including Levenshtein Matching on Cast names
                                   Added iafd legend to summary
    23 Mar 2021   2020.01.18.21    Search string size reduced from 50 to 48
    21 Apr 2021   2020.01.18.22    Search string size reduced from 48 to 21, json convert to dictionary issues
    06 May 2021   2020.01.18.23    Added Double Penetration to Genres, and some studios to ignore genres
                                   Issue #96 - changed title sort so that 'title 21' sorts differently to 'title 12'
                                   duration matching with iafd entries as iafd has scene titles that match with film titles
                                   use of ast module to avoid unicode issues in some libraries
                                   Removal of REGEX preference
                                   code reorganisation like moving logging fuction out of class so it can be used by all imports
-----------------------------------------------------------------------------------------------------------------------------------
'''
import platform, os, re, sys, subprocess, json, ast
from datetime import datetime
from PIL import Image
from io import BytesIO

# Version / Log Title
VERSION_NO = '2020.01.18.23'
PLUGIN_LOG_TITLE = 'Fagalicious'
LOG_BIGLINE = '------------------------------------------------------------------------------'
LOG_SUBLINE = '      ------------------------------------------------------------------------'

# Preferences
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

# IAFD Related variables
IAFD_ABSENT = u'\U0000274C'        # red cross mark - not on IAFD
IAFD_FOUND = u'\U00002705'         # heavy white tick on green - on IAFD
IAFD_THUMBSUP = u'\U0001F44D'      # thumbs up unicode character
IAFD_THUMBSDOWN = u'\U0001F44E'    # thumbs down unicode character
IAFD_LEGEND = u'CAST LEGEND\u2003{0} Actor not on IAFD\u2003{1} Actor on IAFD\u2003:: {2} Film on IAFD ::\n'

# PLEX API /CROP Script/online image cropper
load_file = Core.storage.load
CROPPER = r'CScript.exe "{0}/Plex Media Server/Plug-ins/BestExclusivePorn.bundle/Contents/Code/ImageCropper.vbs" "{1}" "{2}" "{3}" "{4}"'
THUMBOR = Prefs['thumbor'] + "/0x0:{0}x{1}/{2}"

# URLS
BASE_URL = 'https://fagalicious.com'
BASE_SEARCH_URL = BASE_URL + '/search/{0}'

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
def log(message, *args):
    ''' log messages '''
    if re.search('ERROR', message, re.IGNORECASE):
        Log.Error(PLUGIN_LOG_TITLE + ' - ' + message, *args)
    else:
        Log.Info(PLUGIN_LOG_TITLE + '  - ' + message, *args)

# ----------------------------------------------------------------------------------------------------------------------------------
# imports placed here to use previously declared variables
import iafd
import genfunctions

# ----------------------------------------------------------------------------------------------------------------------------------
class Fagalicious(Agent.Movies):
    ''' define Agent class '''
    name = 'Fagalicious (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultScenes']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        log('AGNT  :: Original Search Query        : {0}'.format(myString))

        myString = myString.lower().strip()

        # replace curly apostrophes with straight as strip diacritics will remove these
        quoteChars = [ur'\u2018', ur'\u2019']
        pattern = u'({0})'.format('|'.join(quoteChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            log('AGNT  :: Search Query:: Replacing characters in string. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, "'", myString)
            myString = ' '.join(myString.split())   # remove continous white space
            log('AGNT  :: Amended Search Query [{0}]'.format(myString))
        else:
            log('AGNT  :: Search Query:: String has none of these {0}'.format(pattern))

        spaceChars = [',', '-', ur'\u2011', ur'\u2012', ur'\u2013', ur'\u2014'] # for titles with commas, colons in them on disk represented as ' - '
        pattern = u'({0})'.format('|'.join(spaceChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            log('AGNT  :: Search Query:: Replacing characters in string. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, ' ', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            log('AGNT  :: Amended Search Query [{0}]'.format(myString))
        else:
            log('AGNT  :: Search Query:: String has none of these {0}'.format(pattern))

        # Fagalicious seems to fail to find Titles which have invalid chars in them split at first incident and take first split, just to search but not compare
        # the back tick is added to the list as users who can not include quotes in their filenames can use these to replace them without changing the scrappers code
        badChars = ["'", '"', '`', ur'\u201c', ur'\u201d', ur'\u2018', ur'\u2019']
        pattern = u'({0})'.format('|'.join(badChars))
        matched = re.search(pattern, myString[0])  # match against first character
        if matched:
            log('AGNT  :: Search Query:: Dropping first character [{0}]. Found one of these {1}'.format(myString[0], pattern))
            myString = myString[1:]
            log('AGNT  :: Amended Search Query [{0}]'.format(myString))
        else:
            log('AGNT  :: Search Query:: First character has none of these {0}'.format(pattern))

        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            badPos = matched.start()
            log('AGNT  :: Search Query:: Splitting at position [{0}]. Found one of these {1}'.format(badPos, pattern))
            myString = myString[:badPos]
        else:
            log('AGNT  :: Search Query:: Split not attempted. String has none of these {0}'.format(pattern))

        # string can not be longer than 21 characters and enquote
        if len(myString) > 21:
            lastSpace = myString[:21].rfind(' ')
            myString = '"{0}"'.format(myString[:lastSpace])

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myString = myString.replace('%25', '%').replace('*', '')

        log('AGNT  :: Returned Search Query        : {0}'.format(myString))
        log(LOG_BIGLINE)

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def getFilmImages(self, imageType, imageURL, whRatio):
        ''' get Film images - posters/background art and crop if necessary '''
        pic = imageURL
        picContent = ''
        picInfo = Image.open(BytesIO(HTTP.Request(pic).content))
        width, height = picInfo.size
        dispWidth = '{:,d}'.format(width)       # thousands separator
        dispHeight = '{:,d}'.format(height)     # thousands separator

        log('AGNT  :: {0} Found: Width ({1}) x Height ({2}); URL: {3}'.format(imageType, dispWidth, dispHeight, imageURL))

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
        log('AGNT  :: Crop {0} {1}: Actual (w{2} x h{3}), Desired (w{4} x h{5}), % Dx = w[{6}%] x h[{7}%]'.format("Required:" if cropRequired else "Not Required:", imageType, dispWidth, dispHeight, desiredWidth, desiredHeight, DxWidth, DxHeight))
        if cropRequired:
            try:
                log('AGNT  :: Using Thumbor to crop image to: {0} x {1}'.format(desiredWidth, desiredHeight))
                pic = THUMBOR.format(cropWidth, cropHeight, imageURL)
                picContent = HTTP.Request(pic).content
            except Exception as e:
                log('AGNT  :: Error Thumbor Failed to Crop Image to: {0} x {1}: {2} - {3}'.format(desiredWidth, desiredHeight, pic, e))
                try:
                    if os.name == 'nt':
                        log('AGNT  :: Using Script to crop image to: {0} x {1}'.format(desiredWidth, desiredHeight))
                        envVar = os.environ
                        TempFolder = envVar['TEMP']
                        LocalAppDataFolder = envVar['LOCALAPPDATA']
                        pic = os.path.join(TempFolder, imageURL.split("/")[-1])
                        cmd = CROPPER.format(LocalAppDataFolder, imageURL, pic, cropWidth, cropHeight)
                        subprocess.call(cmd)
                        picContent = load_file(pic)
                except Exception as e:
                    log('AGNT  :: Error Script Failed to Crop Image to: {0} x {1}'.format(desiredWidth, desiredHeight))
        else:
            picContent = HTTP.Request(pic).content

        return pic, picContent

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return

        log(LOG_BIGLINE)
        log('SEARCH:: Version                      : v.%s', VERSION_NO)
        log('SEARCH:: Python                       : %s', sys.version_info)
        log('SEARCH:: Platform                     : %s %s', platform.system(), platform.release())
        log('SEARCH:: Preferences:')
        log('SEARCH::  > Cast Legend Before Summary: %s', PREFIXLEGEND)
        log('SEARCH::  > Collection Gathering')
        log('SEARCH::      > Cast                  : %s', COLCAST)
        log('SEARCH::      > Director(s)           : %s', COLDIRECTOR)
        log('SEARCH::      > Studio                : %s', COLSTUDIO)
        log('SEARCH::      > Film Title            : %s', COLTITLE)
        log('SEARCH::      > Genres                : %s', COLGENRE)
        log('SEARCH::  > Delay                     : %s', DELAY)
        log('SEARCH::  > Language Detection        : %s', DETECT)
        log('SEARCH::  > Library:Site Language     : %s:%s', lang, SITE_LANGUAGE)
        log('SEARCH:: Media Title                  : %s', media.title)
        log('SEARCH:: File Path                    : %s', media.items[0].parts[0].file)
        log(LOG_BIGLINE)

        # Check filename format
        try:
            FILMDICT = genfunctions.matchFilename(media.items[0].parts[0].file)
        except Exception as e:
            log('SEARCH:: Error: %s', e)
            return

        log(LOG_BIGLINE)

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        morePages = True
        while morePages:
            log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, cacheTime=3, timeout=20, sleep=10)
            except Exception as e:
                log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                return

            try:
                searchQuery = html.xpath('//a[@class="next page-numbers"]/@href')[0]
                log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(html.xpath('//span[@class="page-numbers current"]/text()[normalize-space()]')[0])
                morePages = True if pageNumber <= 10 else False
            except:
                searchQuery = ''
                log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            titleList = html.xpath('//header[@class="entry-header"]')
            log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))

            log(LOG_BIGLINE)
            for title in titleList:
                # Site Entry : Composed of Studio, then Scene Title separated by a Colon
                try:
                    siteEntry = title.xpath('./h2/a/text()')
                    siteEntry = ''.join(siteEntry)
                    log('SEARCH:: Site Entry: %s', siteEntry)
                    siteStudio, siteTitle = siteEntry.split(":", 1)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Entry: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Title
                try:
                    genfunctions.matchTitle(siteTitle, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Title: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Studio Name
                try:
                    genfunctions.matchStudio(siteStudio, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Studio: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('./h2/a/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    FILMDICT['SiteURL'] = siteURL
                    log('SEARCH:: Site Title url                %s', siteURL)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Title Url: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Release Date
                try:
                    siteReleaseDate = title.xpath('./ul/li[@class="meta-date"]/a/text()[normalize-space()]')[0]
                    try:
                        siteReleaseDate = genfunctions.matchReleaseDate(siteReleaseDate, FILMDICT)
                        log(LOG_BIGLINE)
                    except Exception as e:
                        log('SEARCH:: Error getting Site URL Release Date: %s', e)
                        log(LOG_SUBLINE)
                        continue
                except:
                    log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                    log(LOG_BIGLINE)

                # we should have a match on studio, title and year now
                log('SEARCH:: Finished Search Routine')
                log(LOG_BIGLINE)
                results.Append(MetadataSearchResult(id=json.dumps(FILMDICT), name=FILMDICT['Title'], score=100, lang=lang))
                return

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        log(LOG_BIGLINE)
        log('UPDATE:: Version                      : v.%s', VERSION_NO)
        log('UPDATE:: File Name                    : %s', filename)
        log('UPDATE:: File Folder                  : %s', folder)
        log(LOG_BIGLINE)

        # Fetch HTML.
        FILMDICT = ast.literal_eval(metadata.id)    # use ast.literal_eval does not convert strings to unicode
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
        metadata.studio = FILMDICT['Studio'].decode('unicode-escape')
        log('UPDATE:: Studio: %s' , metadata.studio)

        # 1b.   Set Title
        metadata.title = FILMDICT['Title'].decode('unicode-escape')
        log('UPDATE:: Title: %s' , metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = FILMDICT['SiteURL']
        metadata.originally_available_at = datetime.strptime(FILMDICT['CompareDate'], DATEFORMAT)
        metadata.year = metadata.originally_available_at.year
        log('UPDATE:: Tagline: %s', metadata.tagline)
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
        #        a. Tags                 : composed of Genres and cast (alphabetic order)
        #        b. Posters/Art
        #        c. Summary

        # 2a. Tags - Fagalicious stores the cast and genres as tags
        log(LOG_BIGLINE)
        castList = []
        genreList = []
        try:
            testStudio = FILMDICT['Studio'].lower().replace(' ', '')
            ignoreGenres = ['Raging Stallion', 'Trailers', 'Hot House', 'BelAmi', 'NakedSword']
            useGenres = ['bareback', 'big dicks', 'black studs', 'double penetration', 'hairy', 'daddy', 'hairy', 'interracial', 'muscle hunks', 'uncut', 'jocks', 'latino', 'gaycest', 'group']
            htmltags = html.xpath('//ul/a[contains(@href, "https://fagalicious.com/tag/")]/text()')
            log('UPDATE:: %s Genres/Cast Tags Found: "%s"', len(htmltags), htmltags)
            for tag in htmltags:
                if '(' in tag:
                    tag = tag.split('(')[0].strip()
                if 'AKA' in tag:
                    tag = tag.split('AKA')[0].strip()

                if anyOf(x in tag.lower() for x in useGenres):
                    genreList.append(tag)
                    continue

                if anyOf(x.lower() in tag.lower() for x in ignoreGenres):
                    continue

                # do not process studio names in tags
                if 'Movie' in tag or 'Series' in tag or '.com' in tag:
                    continue
                if tag.lower().replace(' ', '') in testStudio:
                    continue

                # assume rest are cast
                castList.append(tag)
        except Exception as e:
            log('UPDATE:: Error getting Cast/Genres: %s', e)

        # Process Cast
        log(LOG_SUBLINE)
        try:
            castdict = iafd.ProcessIAFD(castList, FILMDICT)

            # sort the dictionary and add key(Name)- value(Photo, Role) to metadata - if there is no phot assume its a genre
            metadata.roles.clear()
            for key in sorted(castdict):
                newRole = metadata.roles.new()
                if castdict[key]['Photo'] or len(key.split()) == 2:          # most actors will have 2 names
                    newRole.name = key
                    newRole.photo = castdict[key]['Photo']
                    newRole.role = castdict[key]['Role']
                    # add cast name to collection
                    if COLCAST:
                        metadata.collections.add(key)
                else: 
                    genreList.append(key)

        except Exception as e:
            log('UPDATE:: Error getting Cast: %s', e)

        # Process Genres
        log(LOG_SUBLINE)
        log('UPDATE:: %s Genres Found: %s', len(genreList), genreList)
        metadata.genres.clear()
        genreList.sort()
        for genre in genreList:
            metadata.genres.add(genre)
            # add genres to collection
            if COLGENRE:
                metadata.collections.add(genre)

        # 2b.   Posters/Art - First Image set to Poster, next to Art
        log(LOG_BIGLINE)
        imageType = 'Poster & Art'
        try:
            htmlimages = html.xpath('//div[@class="mypicsgallery"]/a//img/@src')
            htmlimages = [x for x in htmlimages if 'data:image' not in x]
            log('UPDATE:: %s Images Found: %s', len(htmlimages), htmlimages)
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
                    log(LOG_SUBLINE)
                else:               # processing art
                    metadata.art[pic] = Proxy.Media(picContent, sort_order=1)
                    metadata.art.validate_keys([pic])

        except Exception as e:
            log('UPDATE:: Error getting %s: %s', imageType, e)

        # 2c.   Summary
        log(LOG_BIGLINE)
        # synopsis
        try:
            synopsis = ''
            htmlsynopsis = html.xpath('//section[@class="entry-content"]/p')
            for item in htmlsynopsis:
                synopsis = '{0}{1}\n'.format(synopsis, item.text_content())
            log('UPDATE:: Synopsis Found: %s', synopsis)

            regex = r'.*writes:'
            pattern = re.compile(regex, re.IGNORECASE | re.DOTALL)
            synopsis = re.sub(pattern, '', synopsis)

            regex = ur'– Get the .*|– Download the .*|– Watch .*'
            pattern = re.compile(regex, re.IGNORECASE)
            synopsis = re.sub(pattern, '', synopsis)

        except Exception as e:
            log('UPDATE:: Error getting Synopsis: %s', e)

        # combine and update
        log(LOG_SUBLINE)
        castLegend = IAFD_LEGEND.format(IAFD_ABSENT, IAFD_FOUND, IAFD_THUMBSUP if FILMDICT['FoundOnIAFD'] == "Yes" else IAFD_THUMBSDOWN)
        summary = ('{0}\n{1}' if PREFIXLEGEND else '{1}\n{0}').format(castLegend, synopsis.strip())
        summary = summary.replace('\n\n', '\n')
        metadata.summary = genfunctions.TranslateString(summary, lang)

        log(LOG_BIGLINE)
        log('UPDATE:: Finished Update Routine')
        log(LOG_BIGLINE)