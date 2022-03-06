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
    28 Feb 2021   2020.08.09.10    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including Levenshtein Matching on Cast names
                                   Added iafd legend to summary
    11 May 2021   2020.08.09.11    Further code reorganisation
    30 May 2021   2020.08.09.12    Further code reorganisation
    04 Feb 2022   2020.08.09.13    implemented change suggested by Cody: duration matching optional on IAFD matching
                                   Cast list if used in filename becomes the default that is matched against IAFD, useful in case no cast is listed in agent
    03 Mar 2022   2020.08.09.14    BASE URL changed from http: to https:

-----------------------------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2020.08.09.14'
PLUGIN_LOG_TITLE = 'BestExclusivePorn'
LOG_BIGLINE = '------------------------------------------------------------------------------'
LOG_SUBLINE = '      ------------------------------------------------------------------------'

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

# PLEX API /CROP Script/online image cropper
load_file = Core.storage.load
CROPPER = r'CScript.exe "{0}/Plex Media Server/Plug-ins/BestExclusivePorn.bundle/Contents/Code/ImageCropper.vbs" "{1}" "{2}" "{3}" "{4}"'
THUMBOR = Prefs['thumbor'] + "/0x0:{0}x{1}/{2}"

# URLS
BASE_URL = 'https://bestexclusiveporn.com/'
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
class BestExclusivePorn(Agent.Movies):
    ''' define Agent class '''
    name = 'BestExclusivePorn (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms', 'com.plexapp.agents.GayAdultScenes']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        log('AGNT  :: Original Search Query        : {0}'.format(myString))

        # convert to lower case and trim
        myString = myString.lower().strip()

        # remove words with apostrophes in them
        badChars = ["'", ur'\u2018', ur'\u2019', '-']
        pattern = u"\w*[{0}]\w*".format(''.join(badChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            log('AGNT  :: Search Query:: Replacing characters in string. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, '', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            log('AGNT  :: Amended Search Query [{0}]'.format(myString))
        else:
            log('AGNT  :: Search Query:: String has none of these {0}'.format(pattern))

        # Best Exclusive uses a maximum of 49 characters when searching
        myString = myString[:49].strip()
        myString = myString if myString[-1] != '%' else myString[:48]

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())
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

        morePages = True
        while morePages:
            log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
                # Finds the entire media enclosure
                titleList = html.xpath('//div[contains(@class,"type-post status-publish")]')
                if not titleList:
                    break
            except Exception as e:
                log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                return

            try:
                searchQuery = html.xpath('//a[@class="next page-numbers"]/@href')[0]
                log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(searchQuery.split('?')[0].split('/')[-1]) - 1
                morePages = True if pageNumber <= 10 else False
            except:
                searchQuery = ''
                log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
            log(LOG_BIGLINE)
            for title in titleList:
                # Site Entry
                try:
                    siteEntry = title.xpath('./h2[@class="title"]/a/text()')[0]
                    log('SEARCH:: Site Entry: %s', siteEntry)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Entry: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # normalise site entry and film title
                siteEntry = utils.NormaliseComparisonString(siteEntry)
                normalisedFilmTitle = utils.NormaliseComparisonString(FILMDICT['Title'])
                pattern = ur'{0}'.format(normalisedFilmTitle)
                matched = re.search(pattern, siteEntry, re.IGNORECASE)  # match against whole string
                if matched:
                    siteTitle = matched.group()
                    siteStudio = re.sub(pattern, '', siteEntry).strip()
                    log('SEARCH:: Studio and Title from Site Entry: %s - %s', siteStudio, siteTitle)
                    log(LOG_BIGLINE)
                else:
                    log('SEARCH:: Failed to get Studio and Title from Site Entry:')
                    log(LOG_SUBLINE)
                    continue

                # Site Title
                try:
                    utils.matchTitle(siteTitle, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Title: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('./h2[@class="title"]/a/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    FILMDICT['SiteURL'] = siteURL
                    log('SEARCH:: Site Title url                %s', siteURL)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Title Url: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Studio Name
                try:
                    utils.matchStudio(siteStudio, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Studio: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Release Date
                try:
                    siteReleaseDate = title.xpath('./div[@class="post-info-top"]/span[@class="post-info-date"]/a[@rel="bookmark"]/text()')[0].strip()
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
        FILMDICT['Title'] = FILMDICT['Title']
        metadata.title = " ".join(word.capitalize() if "'s" in word or "’s" in word or "'t" in word or "’t" in word else word.title() for word in FILMDICT['Title'].split())
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
        #        a.   Countries
        #        b.   Genres               : List of Genres (alphabetic order)
        #        c.   Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        d.   Posters/Art
        #        e.   Summary

        # 2a.   Countries
        log(LOG_BIGLINE)
        try:
            htmlcountries = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Country: ")]')[0].strip().replace('Country: ', '').split(',')
            htmlcountries = [x.strip() for x in htmlcountries if x]
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

        # 2b.   Genres
        log(LOG_BIGLINE)
        try:
            htmlgenres = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Genre: ")]')[0].strip().replace('Genre: ', '').split(',')
            htmlgenres = [x.strip() for x in htmlgenres if x]
            htmlgenres.sort()
            log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            if 'compilation' in [x.lower() for x in htmlgenres]:
                FILMDICT['Compilation'] = 'Compilation'
            metadata.genres.clear()
            for genre in htmlgenres:
                metadata.genres.add(genre)
                # add genre to collection
                if COLGENRE:
                    metadata.collections.add(genre)

        except Exception as e:
            log('UPDATE:: Error getting Genres: %s', e)

        # 2c.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        #             If there is a Starring heading use it to get the actors else try searching the title for the cast
        #             if there is a cast list in the filename, use this as the definitive
        log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Starring: ")]')[0].strip().replace('Starring: ', '').split(',')

        except Exception as e:
            htmlcast = []
            log('UPDATE:: Error getting Cast: No Starring Entry: %s', e)
            log('UPDATE:: Get Cast from Film Title')
            pattern = u'([A-Z]\w+(?=[\s\-][A-Z])(?:[\s\-][A-Z]\w*)+)'
            matches = re.findall(pattern, FILMDICT['Title'])  # match against Film title
            log('UPDATE:: Matches:: {0}'.format(matches))
            if matches:
                for count, castname in enumerate(matches, 1):
                    log('UPDATE:: {0}. Found Possible Cast Name: {1}'.format(count, castname))
                    if castname:
                        htmlcast.append(castname)
        try:
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

        # 2d.   Posters/Art - First Image set to Poster, next to Art
        log(LOG_BIGLINE)
        imageType = 'Poster & Art'
        try:
            htmlimages = html.xpath('//div[@class="entry"]/p//img/@src')
            log('UPDATE:: %s Images Found: %s', len(htmlimages), htmlimages)
            for index, image in enumerate(htmlimages):
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
                    metadata.art[pic] = Proxy.Media(picContent, sort_order=1)
                    metadata.art.validate_keys([pic])

        except Exception as e:
            log('UPDATE:: Error getting %s: %s', imageType, e)

        # 2e.   Summary = IAFD Legend + Synopsis
        log(LOG_BIGLINE)
        # synopsis
        try:
            synopsis = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Description: ")]')[0].strip().replace('Description: ', '')
            log('UPDATE:: Synopsis Found: %s', synopsis)
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