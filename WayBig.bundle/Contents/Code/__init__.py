#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# WayBig (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    22 Dec 2019   2019.12.22.1     Corrected scrapping of collections
    14 Aug 2020   2019.08.12.21    Change to regex matching code - site titles which had studio name in them were failing to match to 
                                   file titles as regex was different between the two
    22 Sep 2020   2019.08.12.22    correction to summary xpath to cater for different layouts
    07 Oct 2020   2019.08.12.23    IAFD - change to https
    28 Feb 2021   2019.08.12.25    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including Levenshtein Matching on Cast names
                                   Added iafd legend to summary
    27 Mar 2021   2019.08.12.26    Site Title had spaces removed before normalisation - caused matching failure
                                   Site Studio was been set to [-1] rather than the last element of the site entry split, so Studio always matched
    21 Apr 2021   2019.08.12.27    Posters with url extention .webp - renamed to .jpg
    25 Apr 2021   2019.08.12.28    removed regex pref, search string length only has full words, json unicode issues, added to title/studio matching
    25 Apr 2021   2019.08.12.29    Issue #96 - changed title sort so that 'title 21' sorts differently to 'title 12'
                                   duration matching with iafd entries as iafd has scene titles that match with film titles
                                   use of ast module to avoid unicode issues in some libraries
                                   Removal of REGEX preference
                                   code reorganisation like moving logging fuction out of class so it can be used by all imports
    11 May 2021   2019.08.12.30    Further code reorganisation
    29 Jul 2021   2019.08.12.31    Further code reorganisation
    11 Dec 2021   2021.12.11.01    Be resilient if year not in filename
                                   Film duration is now relying on Plex native method
                                   Adding option to use site image as background
    12 Dec 2021   2021.12.12.01    Making the cropping more resilient. Fallback to original image
    13 Dec 2021   2021.12.13.01    Adding Trailer support
                                   Adding a fallback search method based on actor names

---------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2021.12.13.01'
PLUGIN_LOG_TITLE = 'WayBig'
LOG_BIGLINE = '------------------------------------------------------------------------------'
LOG_SUBLINE = '      ------------------------------------------------------------------------'

# Preferences
DELAY = int(Prefs['delay'])                         # Delay used when requesting HTML, may be good to have to prevent being banned from the site
MATCHSITEDURATION = int(Prefs['matchsiteduration']) # Acceptable difference between actual duration of video file and that on agent website
DURATIONDX = int(Prefs['durationdx'])               # Acceptable difference between actual duration of video file and that on agent website
DETECT = Prefs['detect']                            # detect the language the summary appears in on the web page
BACKGROUND = Prefs['background']                    # use the site image as background
PREFIXLEGEND = Prefs['prefixlegend']                # place cast legend at start of summary or end
COLCLEAR = Prefs['clearcollections']                # clear previously set collections
COLSTUDIO = Prefs['studiocollection']               # add studio name to collection
COLTITLE = Prefs['titlecollection']                 # add title [parts] to collection
COLGENRE = Prefs['genrecollection']                 # add genres to collection
COLDIRECTOR = Prefs['directorcollection']           # add director to collection
COLCAST = Prefs['castcollection']                   # add cast to collection
COLCOUNTRY = Prefs['countrycollection']             # add country to collection

# PLEX API /CROP Script/online image cropper
load_file = Core.storage.load
CROPPER = r'CScript.exe "{0}/Plex Media Server/Plug-ins/BestExclusivePorn.bundle/Contents/Code/ImageCropper.vbs" "{1}" "{2}" "{3}" "{4}"'
THUMBOR = Prefs['thumbor'] + "/0x0:{0}x{1}/{2}"

# URLS
BASE_URL = 'https://www.waybig.com'
BASE_SEARCH_URL = BASE_URL + '/blog/index.php?s={0}'

# dictionary holding film variables
FILMDICT = {}   

# Date Formats used by website
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
import utils

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
        log('AGNT  :: Original Search Query        : {0}'.format(myString))

        myString = myString.lower().strip()

        # for titles with " - " replace with ":"
        myString = myString.replace(' - ', ': ')

        # replace curly apostrophes with straight as strip diacritics will remove these
        quoteChars = [ur'‘', ur'’', ur'\u2018', ur'\u2019']
        pattern = u'({0})'.format('|'.join(quoteChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            log('AGNT  :: Search Query:: Replacing characters in string. Found one of these {0}'.format(quoteChars))
            myString = re.sub(pattern, "'", myString)
            myString = ' '.join(myString.split())   # remove continous white space
            log('AGNT  :: Amended Search Query [{0}]'.format(myString))
        else:
            log('AGNT  :: Search Query:: String has none of these {0}'.format(quoteChars))

        # WayBig seems to fail to find Titles which have invalid chars in them, split at first incident and take first split, just to search but not compare
        # the back tick is added to the list as users who can not include quotes in their filenames can use these to replace them without changing the scrappers code
        badChars = ["'", '"', '`', ur'\u201c', ur'\u201d']
        pattern = u'({0})'.format('|'.join(badChars))
        myWords = myString.split()
        for count, word in enumerate(myWords):
            matched = re.search(pattern, word) # match against first word
            if matched:
                myWords.remove(myWords[count])
                log('AGNT  :: Search Query:: Dropping word {0} "{1}". Found one of these {2} characters'.format(count, word, badChars))
                myString = ' '.join(myWords)
                log('AGNT  :: Amended Search Query [{0}]'.format(myString))
            else:
                log('AGNT  :: Search Query:: Word {0} "{1}" has none of these chracters {2}'.format(count, word, badChars))

        # Removing & and and from filename to be sure we get the actors
        spaceChars = [' & ',' and ',',','fucks','barebacks','raw']
        pattern = u'({0})'.format('|'.join(spaceChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            log('AGNT  :: Search Query:: Replacing characters in string. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, ' ', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            log('AGNT  :: Amended Search Query [{0}]'.format(myString))
        else:
            log('AGNT  :: Search Query:: String has none of these {0}'.format(pattern))

        # string can not be longer than 50 characters
        if len(myString) > 50:
            lastSpace = myString[:50].rfind(' ')
            myString = myString[:lastSpace]

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myString = myString.replace('%25', '%').replace('*', '')

        log('AGNT  :: Returned Search Query        : {0}'.format(myString))
        log(LOG_BIGLINE)

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return

        utils.logHeaders('SEARCH', media, lang)

        # Calculate duration
        filmDuration = 0
        for part in media.items[0].parts:
                filmDuration += int(long(getattr(part, 'duration')))

        # Check filename format
        try:
            FILMDICT = utils.matchFilename(media.items[0].parts[0].file, filmDuration)
        except Exception as e:
            log('SEARCH:: Error: %s', e)
            return

        log(LOG_BIGLINE)

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        # strip studio name from title to use in comparison
        log('SEARCH:: Search Title: %s', searchTitle)
        regex = ur'^{0} |at {0}$'.format(re.escape(FILMDICT['CompareStudio']))
        pattern = re.compile(regex, re.IGNORECASE)
        compareTitle = re.sub(pattern, '', searchTitle)
        compareTitle = utils.NormaliseComparisonString(compareTitle)

        log('SEARCH:: Search Title: %s', searchTitle)

        morePages = True
        while morePages:
            log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
            except Exception as e:
                log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                return

            try:
                searchQuery = html.xpath('//div[@class="nav-links"]/a[@class="next page-numbers"]/@href')[0]
                log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(html.xpath('//div[@class="nav-links"]/span[@class="page-numbers current"]/text()[normalize-space()]')[0])
                morePages = True if pageNumber <= 10 else False
            except:
                searchQuery = ''
                log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            titleList = html.xpath('.//div[@class="row"]/div[@class="content-col col"]/article')
            log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
            log(LOG_BIGLINE)

            for title in titleList:
                # Site Entry
                try:
                    siteEntry = title.xpath('./a/h2[@class="entry-title"]/text()')[0].strip()
                    log('SEARCH:: Site Entry:                   %s', siteEntry)
                    # prepare the Site Entry
                    singleQuotes = ["`", "‘", "’"]
                    pattern = ur'[{0}]'.format(''.join(singleQuotes))
                    siteEntry = re.sub(pattern, "'", siteEntry)
                    
                    # Strip everything after " (" as it is either the bareback mention or list of actors
                    siteEntry = siteEntry.split(' (')[0]

                    # the siteEntry usual has the format Studio: Title
                    siteEntry = siteEntry.lower()
                    if ': ' in siteEntry:
                        siteStudio, siteTitle = siteEntry.split(': ', 1)
                        # none standard titles
                    elif ' at ' in siteEntry:
                        siteTitle, siteStudio = siteEntry.rsplit(' at ', 1)
                    elif ' on ' in siteEntry:
                        siteTitle, siteStudio = siteEntry.rsplit(' on ', 1)
                    elif '? ' in siteEntry:
                        siteStudio, siteTitle = siteEntry.split('? ', 1)
                    elif ', ' in siteEntry:
                        siteStudio, siteTitle = siteEntry.split(', ', 1)
                    elif FILMDICT['Studio'].lower() in siteEntry:       # in case the film title is mssing a separator between the studio and clip name
                        log('SEARCH:: Warning: Site Entry did not have a clear separator to separate Studio from Title')
                        siteStudio = FILMDICT['Studio'].lower()
                        siteTitle = FILMDICT['Title'].lower() if FILMDICT['Title'].lower() in siteEntry else ''
                    else:
                        log('SEARCH:: Error determining Site Studio and Title from Site Entry')
                        log(LOG_SUBLINE)
                        continue

                    log(LOG_BIGLINE)

                except Exception as e:
                    log('SEARCH:: Error getting Site Entry: %s', e)
                    log(LOG_SUBLINE)
                    continue

                    
                # Site Actors
                siteActorList = title.xpath('.//div[@id="tags"]//a/text()')
                log('SEARCH:: Site Actors: %s', siteActorList)
                siteActors = ' '.join(siteActorList)
                log('SEARCH:: Site Actors: %s', siteActors)

                # Site Title
                try:
                    utils.matchTitle(siteTitle, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Title: %s', e)
                    log('SEARCH:: Trying by extracting actors name from %s', siteTitle)
                    try:
                        utils.matchTitleActors(siteActors, FILMDICT)
                    except Exception as e:
                        log('SEARCH:: Error getting Site Title: %s', e)
                        log(LOG_SUBLINE)
                        continue

                # Studio Name
                try:
                    utils.matchStudio(siteStudio, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Studio : %s', e)
                    log(LOG_SUBLINE)
                    continue
                    

                # Site Title URL
                try:
                    siteURL = title.xpath('./a[@rel="bookmark"]/@href')[0]
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
                    siteReleaseDate = title.xpath('./div/span[@class="meta-date"]/strong/text()[normalize-space()]')[0]
                    try:
                        siteReleaseDate = utils.matchReleaseDate(siteReleaseDate, FILMDICT)
                        log(LOG_BIGLINE)
                    except Exception as e:
                        log('SEARCH:: Error getting Site URL Release Date: %s', e)
                        log(LOG_SUBLINE)
                        continue
                except:
                    log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                    log(LOG_BIGLINE)

                # we should have a match on studio, title and year now. Find corresponding film on IAFD
                log('SEARCH:: Check for Film on IAFD:')
                utils.getFilmOnIAFD(FILMDICT)
                if FILMDICT['IAFDFilmURL'] == '':
                    log('SEARCH:: Film not found on IAFD. Trying with actors')
                    utils.getFilmOnIAFDActors(FILMDICT)

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
        if FILMDICT['CompareDate']!='':
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
        #        a.   Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        b.   Posters/Art
        #        c.   Summary

        # 2a. Tags - Waybigs stores the cast as tags
        log(LOG_BIGLINE)
        castList = []
        try:
            ignoreCast = ['British', 'Furry', 'Hairy', 'Hawaiian', 'Solo', 'U.K', 'United Kingdom']
            htmlcast = html.xpath('//a[contains(@href,"https://www.waybig.com/blog/tag/")]/text()')
            htmlcast = [x.replace(u'\u2019s', '') for x in htmlcast]
            htmlcast = list(set(htmlcast))
            # remove File Studio Name
            htmlcast = [x for x in htmlcast if not '.tv' in x.lower()]
            htmlcast = [x for x in htmlcast if not '.com' in x.lower()]
            htmlcast = [x for x in htmlcast if not '.net' in x.lower()]
            htmlcast = [x for x in htmlcast if not FILMDICT['Studio'].replace(' ', '').lower() in x.replace(' ', '').lower()]
            # actors will have initial capitals for names
            for count, cast in enumerate(htmlcast):
                words = cast.split()
                wordcount = len(words)
                words = [x for x in words if x[0].isupper() and (x[1].islower() or x[1]=="'")] # cater for irish style names like O'Leary
                capcount = len(words)
                htmlcast[count] = cast if wordcount == capcount else ''

            htmlcast = [x for x in htmlcast if x]

            for cast in htmlcast:
                if anyOf(x in cast for x in ignoreCast):
                    continue
                castList.append(cast)

        except Exception as e:
            log('UPDATE:: Error getting Cast: No Tags Found, Get Cast from Film Title: %s', e)
            pattern = u'([A-Z]\w+(?=[\s\-][A-Z])(?:[\s\-][A-Z]\w*)+)'
            matches = re.findall(pattern, FILMDICT['Title'])  # match against Film title
            log('UPDATE:: Matches:: {0}'.format(matches))
            if matches:
                for count, castname in enumerate(matches, 1):
                    log('UPDATE:: {0}. Found Possible Cast Name: {1}'.format(count, castname))
                    if castname:
                        castList.append(castname)

        try:
            castDict = utils.getCast(castList, FILMDICT)
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

        # 2c.   Posters/Art - First Image set to Poster, next to Art
        log(LOG_BIGLINE)
        imageType = 'Poster & Art'
        try:
            htmlimages = html.xpath('//a[@target="_self" or @target="_blank"]/img[(@height or @width) and @alt and contains(@src, "zing.waybig.com/reviews")]/@src')
            if len(htmlimages) == 1:
                htmlimages.append(htmlimages[0])
            log('UPDATE:: %s Images Found: %s', len(htmlimages), htmlimages)
            for index, image in enumerate(htmlimages):
                image = image.replace('.webp', '.jpg')      # change extension of url image
                if index > 1:
                    break
                whRatio = 1.5 if index == 0 else 0.5625
                imageType = 'Poster' if index == 0 else 'Art'
                pic, picContent = utils.getFilmImages(imageType, image, whRatio)    # height is 1.5 times the width for posters
                if index == 0:      # processing posters
                    #  clean up and only keep the posters we have added
                    metadata.posters[pic] = Proxy.Media(picContent, sort_order=1)
                    metadata.posters.validate_keys([pic])
                    log(LOG_SUBLINE)
                else:               # processing art
                    if BACKGROUND:
                        metadata.art[pic] = Proxy.Media(picContent, sort_order=1)
                        metadata.art.validate_keys([pic])

        except Exception as e:
            log('UPDATE:: Error getting %s: %s', imageType, e)

        # 2e. Trailer
        # If trailer if embedded
        try:
            htmlTrailer = html.xpath('//iframe[starts-with(@src,"https://www.waybig.com/embed")]/@src')[0]
            htmltrailer =  HTML.ElementFromURL(trailerPlayerUrl, timeout=20, sleep=DELAY)
            log('UPDATE:: htmlTrailer: %s', htmltrailer)
            trailerUrl = htmltrailer.xpath('//source/@src')[0]
            log('UPDATE:: Trailer url: %s', trailerUrl)
            trailerThumb = ''
            try:
                trailerStyle = htmltrailer.xpath('//video/@poster')[0]
                log('UPDATE:: Trailer Style: %s', trailerStyle)
                trailerThumb = re.search('url\((.*)\)', trailerStyle).group(1)
                log('UPDATE:: Trailer Thumb: %s', trailerThumb)
            except:
                log('UPDATE:: Error getting thumb')
            extras = []
            extras.append({ 'type' : 'trailer',
                            'extra' : TrailerObject (
                                                    file=trailerUrl,
                                                    title=metadata.title,
                                                    thumb=trailerThumb
                                                     )
                             })
            for extra in extras:
                metadata.extras.add(extra['extra'])
        except:
            log('UPDATE:: Error getting trailer')

        # If trailer if flowplayer
        try:
            htmltrailer = html.xpath('//div[starts-with(@id,"flowplayer-video")]')[0]
            log('UPDATE:: htmlTrailer: %s', htmltrailer)
            trailerUrl = htmltrailer.xpath('//source/@src')[0]
            log('UPDATE:: Trailer url: %s', trailerUrl)
            trailerThumb = ''
            try:
                trailerStyle = htmltrailer.xpath('//div[starts-with(@id,"flowplayer-video")]/@style')[0]
                log('UPDATE:: Trailer Style: %s', trailerStyle)
                trailerThumb = re.search('url\((.*)\)', trailerStyle).group(1)
                log('UPDATE:: Trailer Thumb: %s', trailerThumb)
            except:
                log('UPDATE:: Error getting thumb')
            extras = []
            extras.append({ 'type' : 'trailer',
                            'extra' : TrailerObject (
                                                    file=trailerUrl,
                                                    title=metadata.title,
                                                    thumb=trailerThumb
                                                     )
                             })
            for extra in extras:
                metadata.extras.add(extra['extra'])
        except:
            log('UPDATE:: Error getting trailer')

        # 2a.   Summary = IAFD Legend + Synopsis
        # synopsis
        synopsis = ''
        try:
            htmlsynopsis = html.xpath('//div[@class="entry-content"]/p[not(descendant::script) and not(contains(., "Watch as"))]')
            for item in htmlsynopsis:
                synopsis = '{0}{1}\n'.format(synopsis, item.text_content())
            log('UPDATE:: Synopsis Found: %s', synopsis)
            pattern = re.compile(r'Watch.*at.*', re.IGNORECASE)
            synopsis = re.sub(pattern, '', synopsis)
            synopsis = utils.TranslateString(synopsis, SITE_LANGUAGE, lang, DETECT)
        except Exception as e:
            log('UPDATE:: Error getting Synopsis: %s', e)

        # combine and update
        log(LOG_SUBLINE)
        summary = ('{0}\n{1}\n{2}' if PREFIXLEGEND else '{1}\n{0}\n{2}').format(FILMDICT['Legend'], synopsis.strip(), FILMDICT['Synopsis'])
        summary = summary.replace('\n\n', '\n')
        metadata.summary = summary

        log(LOG_BIGLINE)
        log('UPDATE:: Finished Update Routine')
        log(LOG_BIGLINE)