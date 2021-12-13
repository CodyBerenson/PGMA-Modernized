#!/usr/bin/env python
# encoding=utf8
'''
# HomoActive - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    12 Aug 2019   2019.08.12.01    Creation
    01 Jun 2020   2019.08.12.02    Implemented translation of summary
                                   improved getIAFDActor search
    27 Jun 2020   2019.08.12.03    Improvement to Summary Translation: Translate into Plex Library Language
                                   stripping of intenet domain suffixes from studio names when matching
                                   handling of unicode characters in film titles and comparision string normalisation
    07 Oct 2020   2019.08.12.04    IAFD - change to https
    27 Feb 2021   2019.08.12.06    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including Levenshtein Matching on Cast names
                                   Added iafd legend to summary
    25 Aug 2021   2020.18.03.08    IAFD will be only searched if film found on agent Catalogue
    11 Dec 2021   2021.12.11.01    Be resilient if year not in filename
                                   Film duration is now relying on Plex native method
                                   Adding option to use site image as background
    12 Dec 2021   2021.12.12.01    Making the cropping more resilient. Fallback to original image
    13 Dec 2021   2021.12.13.01    Adding Trailer support

-----------------------------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2021.12.13.01'
PLUGIN_LOG_TITLE = 'HomoActive'

# log section separators
LOG_BIGLINE = '--------------------------------------------------------------------------------'
LOG_SUBLINE = '      --------------------------------------------------------------------------'

# Preferences
DELAY = int(Prefs['delay'])                         # Delay used when requesting HTML, may be good to have to prevent being banned from the site
MATCHSITEDURATION = Prefs['matchsiteduration']      # Match against Site Duration value
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

# URLS
BASE_URL = 'https://www.homoactive.com'
BASE_SEARCH_URL = BASE_URL + '/catalogsearch/result/?q={0}'

# dictionary holding film variables
FILMDICT = {}   

# Date Formats used by website
DATEFORMAT = '%d-%m-%Y'

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
        log('AGNT  :: Original Search Query        : {0}'.format(myString))

        myString = myString.strip().lower()
        myString = myString.replace(' -', ':').replace(ur'\u2013', '-').replace(ur'\u2014', '-').replace('& ', '')

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString)

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

        # Finds the entire media enclosure <DIV> elements then steps through them
        titleList = HTML.ElementFromURL(searchQuery, sleep=DELAY).xpath('//div[@class="item"]')
        log('SEARCH:: Titles Found %s', len(titleList))
        log(LOG_BIGLINE)

        for title in titleList:
            # Site Title
            try:
                siteTitle = title.xpath('./a/@title')[0]
                siteTitle = re.sub(ur' (dvd|download).*$', '', siteTitle, flags=re.IGNORECASE)
                siteTitle = siteTitle.split('(')[0].strip()
                utils.matchTitle(siteTitle, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error getting Site Title: %s', e)
                log(LOG_SUBLINE)
                continue

            # Site Title URL
            try:
                siteURL = title.xpath('./a/@href')[0]
                siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                FILMDICT['SiteURL'] = siteURL
                log('SEARCH:: Site Title url                %s', siteURL)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error getting Site Title Url: %s', e)
                log(LOG_SUBLINE)
                continue

            # Access Site URL for Studio Name information
            try:
                log('SEARCH:: Reading Site URL page         %s', siteURL)
                html = HTML.ElementFromURL(siteURL, sleep=DELAY)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error reading Site URL page: %s', e)
                log(LOG_SUBLINE)
                continue

            # Studio Name
            try:
                siteStudio = html.xpath('//div[@class="product-name"]/span/dd/a/text()')[0]
                utils.matchStudio(siteStudio, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error getting Site Studio: %s', e)
                log(LOG_SUBLINE)
                continue

            # Site Release Date
            try:
                siteReleaseDate = html.xpath('//dt[text()="Release Date:"]/following-sibling::dd[1]/text()[normalize-space()]')[0].strip()
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

            # Duration - # Access Site URL for Film Duration
            if MATCHSITEDURATION:
                try:
                    siteDuration = html.xpath('//dt[text()="Run Time:"]/following-sibling::dd[1]/text()[normalize-space()]')[0].strip()
                    siteDuration = re.sub('[^0-9]', '', siteDuration)
                    log('SEARCH:: Site Film Duration            %s Minutes', siteDuration)
                    utils.matchDuration(siteDuration, FILMDICT, MATCHSITEDURATION)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Film Duration: %s', e)
                    log(LOG_SUBLINE)
                    continue

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
        #        a. Country
        #        b. Directors            : List of Drectors (alphabetic order)
        #        c. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        d. Posters/Background
        #        e. Summary
        #        f. Trailer

        # 2a.   Country
        log(LOG_BIGLINE)
        try:
            htmlcountries = html.xpath('//dt[text()="Country:"]/following-sibling::dd[1]/text()[normalize-space()]')
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

        # 2b.   Directors
        log(LOG_BIGLINE)
        try:
            htmldirectors = html.xpath('//dt[text()="Director:"]/following-sibling::dd[1]/text()[normalize-space()]')
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

        # 2c.   Cast: get thumbnails from IAFD if missing as they are right dimensions for plex cast list
        log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('//dt[text()="Actors:"]/following-sibling::dd[1]/a/text()')
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

        # 2d.   Posters/Art
        log(LOG_BIGLINE)
        try:
            htmlimages = html.xpath('//img[@class="gallery-image"]/@src')
            image = htmlimages[0]
            log('UPDATE:: Poster Image Found: %s', image)
            #  set poster then only keep it
            metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.posters.validate_keys([image])

            if BACKGROUND:
                image = htmlimages[1]
                log('UPDATE:: Art Image Found: %s', image)
                metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
                metadata.art.validate_keys([image])

        except Exception as e:
            log('UPDATE:: Error getting Poster/Art: %s', e)

        # 2e.   Summary = IAFD Legend + Synopsis
        log(LOG_BIGLINE)
        # synopsis
        try:
            synopsis = html.xpath('//div[@class="description"]/div[@class="std"]/text()')
            synopsis = " ".join(synopsis)
            synopsis = synopsis.replace('\n', '').replace('\r', '').strip()
            log('UPDATE:: Synopsis Found: %s', synopsis)
            synopsis = utils.TranslateString(synopsis, SITE_LANGUAGE, lang, DETECT)
        except Exception as e:
            synopsis = ''
            log('UPDATE:: Error getting Synopsis: %s', e)

        # 2f. Trailer
        try:
            htmltrailers = html.xpath('//div[@class="product-shop"]//video')
            extras = []
            for htmltrailer in htmltrailers:
                log('UPDATE:: htmlTrailer: %s', htmltrailer)
                trailerUrl = htmltrailer.xpath('//source/@src')[0]
                trailerType = htmltrailer.xpath('//source/@type')[0]
                log('UPDATE:: Trailer url: %s - Type: %s', trailerUrl, trailerType)
                trailerThumb = ''
                try:
                    htmlimages = html.xpath('//img[@class="gallery-image"]/@src')
                    if len(htmlimages) > 2:
                        trailerThumb = htmlimages[3]
                    else:
                        trailerThumb = htmlimages[0]
                    log('UPDATE:: Trailer Thumb: %s', trailerThumb)
                except:
                    log('UPDATE:: Error getting trailer thumb')
            if trailerType == "video/mp4":
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

        # combine and update
        log(LOG_SUBLINE)
        summary = ('{0}\n{1}\n{2}' if PREFIXLEGEND else '{1}\n{0}\n{2}').format(FILMDICT['Legend'], synopsis.strip(), FILMDICT['Synopsis'])
        summary = summary.replace('\n\n', '\n')
        metadata.summary = summary

        log(LOG_BIGLINE)
        log('UPDATE:: Finished Update Routine')
        log(LOG_BIGLINE)