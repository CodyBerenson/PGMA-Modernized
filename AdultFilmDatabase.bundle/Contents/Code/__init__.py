#!/usr/bin/env python
# encoding=utf8
'''
# AdultFilmDatabase - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    25 Dec 2020   2020.12.25.01    Creation
                                   Improved on IAFD search, actors sexual roles if recorded are returned, if not shows a red circle.
                                   if actor is not credited on IAFD but is on Agent Site it shows as a Yellow Box below the actor
                                   sped up search by removing search by actor/director... less hits on IAFD per actor...
    19 Feb 2021   2020.12.25.03    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including LevenShtein Matching on Cast names
                                   set content_rating age to 18
                                   Set collections from filename + countries, cast and directors
                                   Added directors photos
                                   included studio on iafd processing of filename
                                   Added iafd legend to summary
                                   improved logging
    25 Aug 2021   2020.12.25.04    IAFD will be only searched if film found on agent Catalogue
    04 Feb 2022   2020.12.25.05    implemented change suggested by Cody: duration matching optional on IAFD matching
                                   Cast list if used in filename becomes the default that is matched against IAFD, useful in case no cast is listed in agent


-----------------------------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2020.12.25.05'
PLUGIN_LOG_TITLE = 'AdultFilmDatabase'

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

# URLS - in list format - ADFD uses post requests rather than building up urls
BASE_URL = 'https://www.adultfilmdatabase.com/index.cfm'
BASE_SEARCH_URL = 'http://www.adultfilmdatabase.com/lookup.cfm'

# dictionary holding film variables
FILMDICT = {}

# Date Format used by website
DATEFORMAT = '%Y%m%d'

# Website Language
SITE_LANGUAGE = 'en'

# ----------------------------------------------------------------------------------------------------------------------------------
def Start():
    ''' initialise process '''
    HTTP.CacheTime = 0
    HTTP.Headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    HTTP.Headers['Accept-Encoding'] = 'gzip, deflate, br'
    HTTP.Headers['Accept-Language'] = 'en-GB,en;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6'
    HTTP.Headers['Cache-Control'] = 'max-age=0'
    HTTP.Headers['Connection'] = 'keep-alive'
    HTTP.Headers['Content-Length'] = 71
    HTTP.Headers['Content-Type'] = 'application/x-www-form-urlencoded'
    HTTP.Headers['Cookie'] = '_ga=GA1.2.1234723832.1644274530; _gid=GA1.2.556761427.1644274530; CFID=104961037; CFTOKEN=9d1970834eb33232-8CCC70A4-B660-BD41-889CA24DED9DB9FD; _gat=1'
    HTTP.Headers['DNT'] = 1
    HTTP.Headers['Host'] = 'www.adultfilmdatabase.com'
    HTTP.Headers['Origin'] = 'https://www.adultfilmdatabase.com/index.cfm'
    HTTP.Headers['Referer'] = 'https://www.adultfilmdatabase.com/browse.cfm?type=title'
    HTTP.Headers['sec-ch-ua'] = '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"'
    HTTP.Headers['sec-ch-ua-mobile'] = '?0'
    HTTP.Headers['sec-ch-ua-platform'] = '"Windows"'
    HTTP.Headers['Sec-Fetch-Dest'] = 'document'
    HTTP.Headers['Sec-Fetch-Mode'] = 'navigate'
    HTTP.Headers['Sec-Fetch-Site'] = 'same-origin'
    HTTP.Headers['Sec-Fetch-User'] = '?1'
    HTTP.Headers['Upgrade-Insecure-Requests'] = 1
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'


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
class AdultFilmDatabase(Agent.Movies):
    ''' define Agent class '''
    name = 'AdultFilmDatabase (IAFD)'
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        log('AGNT  :: Original Search Query        : {0}'.format(myString))

        # convert to lower case and trim
        myString = myString.replace(' - ', ': ')
        myString = myString.lower().strip()
        myString = String.StripDiacritics(myString)

        # strip non-alphanumeric characters
        pattern = ur'[^A-Za-z0-9]+'
        myString = re.sub(pattern, ' ', myString, flags=re.IGNORECASE)
        myString = myString.replace('  ', ' ').strip()

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
        searchQuery = BASE_SEARCH_URL
        formData =  {'find': '{0}'.format(searchTitle)}
        headerdata = {'Content-Type': 'text/html;charset=UTF-8', 'Content-Encoding': 'gzip', 'Vary': 'Accept-Encoding', 'Server': 'Microsoft-IIS/8.5', 'Set-Cookie': 'CFID=104963556; Expires=Thu, 01-Feb-2052 20:38:05 GMT; Path=/; HttpOnly, CFTOKEN=baa53c7833ef30d3-8E9424B6-A2C0-5EE6-F5DD64EE8B89E1D0; Expires=Thu, 01-Feb-2052 20:38:05 GMT; Path=/; HttpOnly', 'X-Powered-By': 'ASP.NET', 'Date': 'Tue, 08 Feb 2022 20:38:04 GMT', 'Content-Length': '6675'}
        log('SEARCH:: Search Query: %s', formData)
        try:
            html = HTML.ElementFromURL(searchQuery, values=formData, headers=headerdata, timeout=20, sleep=DELAY)
            log('SEARCH:: HTML:::: %s', html.text)
            # Finds the entire media enclosure
            titleList = html.xpath('//div[@class="w3-col m12 s12 l6 w3-white"]')
            log('SEARCH:: Result Page No: 1, Titles Found %s', len(titleList))
            titleList = html.xpath('//div[@class="w3-twothirds"]')
            log('SEARCH:: Result Page No: 1, Titles Found %s', len(titleList))
        except Exception as e:
            log('SEARCH:: Error: Search Query did not pull any results: %s', e)
            return

        log('SEARCH:: Result Page No: 1, Titles Found %s', len(titleList))
        log(LOG_BIGLINE)
        for title in titleList:
            # Site Title
            try:
                siteTitle = title.xpath('./p/a/@title')[0]
                utils.matchTitle(siteTitle, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error getting Site Title: %s', e)
                log(LOG_SUBLINE)
                continue

            # Site Title URL
            try:
                siteURL = title.xpath('./p/a/@href')[0]
                siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                FILMDICT['SiteURL'] = siteURL
                log('SEARCH:: Site Title url                %s', siteURL)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error getting Site Title Url: %s', e)
                log(LOG_SUBLINE)
                continue

            # Site Entry - Studio Name + Release Year
            try:
                siteEntry = title.xpath('./p/span[@class="w3-small w3-text-grey"]/text()')[0].strip()
                log('SEARCH:: Site Entry: %s', siteEntry)
            except:
                log('SEARCH:: Error getting Site Entry: %s', e)
                continue

            # Studio Name
            try:
                siteStudio = siteEntry.split('|')[0].strip()
                utils.matchStudio(siteStudio, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error getting Site Studio: %s', e)
                log(LOG_SUBLINE)
                continue

            # Site Release Date
            try:
                siteReleaseDate = siteEntry.split('|')[1].strip()
                try:
                    siteReleaseDate = utils.matchReleaseDate(siteReleaseDate, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Release Date: %s', e)
                    log(LOG_SUBLINE)
                    continue
            except Exception as e:
                log('SEARCH:: Error getting Site Release Date: Default to Filename Date [%s]', e)
                log(LOG_SUBLINE)

            # Duration - # Access Site URL for Film Duration
            if MATCHSITEDURATION:
                try:
                    log('SEARCH:: Reading Site URL page         %s', siteURL)
                    html = HTML.ElementFromURL(siteURL, sleep=DELAY)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error reading Site URL page: %s', e)
                    log(LOG_SUBLINE)
                    continue

                try:
                    siteDuration = html.xpath('//span[@itemprop="duration"]/text()')[0]
                    siteDuration = siteDuration.split(':', 1)[1].strip()
                    log('SEARCH:: Site Film Duration            %s', siteDuration)
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
        #        a. Genres               : List of Genres (alphabetic order)
        #        b. Directors            : List of Directors (alphabetic order)
        #        c. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        d. Posters/Art
        #        e. Summary

        # 2a.   Genres
        log(LOG_BIGLINE)
        try:
            ignoreGenres = ['Feature', 'Gay']
            genres = []
            htmlgenres = html.xpath('//a[@href[contains(.,"&cf=")]]/span/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
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
            log('UPDATE:: Error getting Genres: %s', e)

        # 2b.   Directors
        log(LOG_BIGLINE)
        try:
            htmldirectors = html.xpath('//span[@itemprop="director"]//text()[normalize-space()]')
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

        # 2c.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('//span[@itemprop="actor"]//text()[normalize-space()]')
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

        # 2d.   Poster/Art
        log(LOG_BIGLINE)
        try:
            htmlimages = html.xpath('//img[@title]/@src')
            image = htmlimages[0]
            image = ('' if BASE_URL in image else BASE_URL) + image
            log('UPDATE:: Poster Image Found: %s', image)
            #  set poster then only keep it
            metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.posters.validate_keys([image])

            image = htmlimages[1]
            image = ('' if BASE_URL in image else BASE_URL) + image
            log('UPDATE:: Art Image Found: %s', image)
            #  set art then only keep it
            metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.art.validate_keys([image])

        except Exception as e:
            log('UPDATE:: Error getting Poster/Art: %s', e)

        # 2e.   Summary = IAFD Legend + Synopsis
        log(LOG_BIGLINE)
        # synopsis
        try:
            synopsis = ''
            htmlsynopsis = html.xpath('//p[@itemprop="description"]/text()')
            for item in htmlsynopsis:
                summary = '{0}\n{1}'.format(synopsis, item.strip())
            log('UPDATE:: Synopsis Found: %s', synopsis)
            synopsis = utils.TranslateString(synopsis, SITE_LANGUAGE, lang, DETECT)
        except Exception as e:
            synopsis = ''
            log('UPDATE:: Error getting Synopsis: %s', e)

        # combine and update
        log(LOG_SUBLINE)
        summary = ('{0}\n{1}' if PREFIXLEGEND else '{1}\n{0}').format(FILMDICT['Legend'], synopsis.strip())
        summary = summary.replace('\n\n', '\n')
        log('UPDATE:: Summary with Legend: %s', summary)
        metadata.summary = summary

        log(LOG_BIGLINE)
        log('UPDATE:: Finished Update Routine')
        log(LOG_BIGLINE)