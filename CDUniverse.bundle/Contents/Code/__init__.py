﻿#!/usr/bin/env python
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
    25 Aug 2021   2020.12.31.07    IAFD will be only searched if film found on agent Catalogue
    11 Dec 2021   2021.12.11.01    Be resilient if year not in filename
                                   Film duration is now relying on Plex native method
                                   Adding option to use site image as background

-----------------------------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2021.12.11.01'
PLUGIN_LOG_TITLE = 'CD Universe'

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
class CDUniverse(Agent.Movies):
    ''' define Agent class '''
    name = 'CD Universe (IAFD)'
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
        myString = myString.replace('-', '').replace(ur'\u2013', '').replace(ur'\u2014', '')
        myString = ' '.join(myString.split())   # remove continous white space

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

        try:
            html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
            # Finds the entire media enclosure
            titleList = html.xpath('//*[@class="chunkytitle"]')
            if not titleList:
                return
        except Exception as e:
            log('SEARCH:: Error: Search Query did not pull any results: %s', e)
            return

        log('SEARCH:: Titles List: %s Found', len(titleList))
        log(LOG_BIGLINE)
        for title in titleList:
            try:
                siteTitle = title.text
                utils.matchTitle(siteTitle, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error getting Site Title: %s', e)
                log(LOG_SUBLINE)
                continue

            # Site Title URL
            try:
                siteURL = title.get('href')
                siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                FILMDICT['SiteURL'] = siteURL
                log('SEARCH:: Site Title url                %s', siteURL)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error getting Site Title Url: %s', e)
                log(LOG_SUBLINE)
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

            # Studio Name
            try:
                siteStudio = html.xpath('//a[@id="studiolink"]/text()')[0]
                utils.matchStudio(siteStudio, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error getting Site Studio: %s', e)
                log(LOG_SUBLINE)
                continue

            # Site Release Date
            try:
                siteReleaseDate = html.xpath('//td[text()="Release Date"]/following-sibling::td/text()')[0].strip()
                try:
                    siteReleaseDate = utils.matchReleaseDate(siteReleaseDate, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Release Date: %s', e)
                    log(LOG_SUBLINE)
                    continue
            except:
                log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                log(LOG_BIGLINE)

            # Duration - missing on CD Universe

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
        #        a. Rating
        #        b. Genres               : List of Genres (alphabetic order)
        #        c. Directors            : List of Directors (alphabetic order)
        #        d. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        e. Posters/Art
        #        f. Reviews
        #        g. Summary

        # 2a.   Rating (out of 5 Stars) = Rating can be a maximum of 10 - float value
        log(LOG_BIGLINE)
        try:
            rating = html.xpath('//a[contains(@title, "out of 5 stars")]/@title')[0]
            rating = rating.split()[0]
            rating = float(rating) * 2.0
            log('UPDATE:: Rating %s', rating)
            metadata.rating = rating
        except Exception as e:
            metadata.rating = 0.0
            log('UPDATE:: Error getting Rating: %s', e)

        # 2b.   Genres
        log(LOG_BIGLINE)
        try:
            genres = []
            ignoreGenres = ['4 Hour', '8 Hour', 'HD - High Definition', 'Interactive', 'Multi-Pack', 'Shot In 4K', 'Video On Demand']
            htmlgenres = html.xpath('//td[text()="Category"]/following-sibling::td/a/text()')
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

        # 2c.   Directors
        log(LOG_BIGLINE)
        try:
            htmldirectors = html.xpath('//td[text()="Director"]/following-sibling::td/a/text()')
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

        # 2d.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('//td[text()="Starring"]/following-sibling::td/a/text()')
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

        # 2e.   Posters/Art
        log(LOG_BIGLINE)
        try:
            image = html.xpath('//img[@id="PIMainImg"]/@src')[0]
            log('UPDATE:: Poster Image Found: %s', image)
            #  set poster
            metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.posters.validate_keys([image])

            #  set Art
            if BACKGROUND:
                image = html.xpath('//img[@id="0"]/@src')[0]
                log('UPDATE:: Art Image Found: %s', image)
                metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
                metadata.art.validate_keys([image])

        except Exception as e:
            log('UPDATE:: Error getting Poster/Art: %s', e)

        # 2f.   Reviews
        log(LOG_BIGLINE)
        try:
            htmlreviews = html.xpath('//table[@id="singlereview"]')
            log('UPDATE:: Number of Reviews [%s]', len(htmlreviews))
            metadata.reviews.clear()
            for count, review in enumerate(htmlreviews, start=1):
                log('UPDATE:: Review No %s', count)
                try:
                    try:
                        title = review.xpath('.//span[contains(@style,"font-weight:bold")]/text()[normalize-space()]')
                        title = ''.join(title).strip()
                        log('UPDATE:: Review Title: %s', title)
                    except:
                        title = ''
                    try:
                        stars = review.xpath('.//img[contains(@alt,"star")]/@alt')[0]
                        stars = re.sub('[^0-9]', '', stars)   # strip out non-numerics
                        stars = [u'\U00002B50'] * int(stars)  # change type to list of size
                        stars = ''.join(stars)                # convert back to str
                        log('UPDATE:: Review Stars: %s', stars)
                    except:
                        stars = ''
                    try:
                        writer =  review.xpath('.//td[@rowspan="2"]//text()[normalize-space()]')
                        writer = ''.join(writer).strip()
                        writer = re.sub(ur'^.+By', '', writer).replace('By', '').strip()
                        log('UPDATE:: Review Writer: %s', writer)
                    except:
                        writer = ''
                    try:
                        writing = review.xpath('.//span[@class="reviewtext"]/text()[normalize-space()]')
                        writing = ''.join(writing)
                        log('UPDATE:: Review Text: %s', writing)
                    except:
                        writing = ''

                    newReview = metadata.reviews.new()
                    newReview.author = '{0} {1}'.format(stars, writer)
                    newReview.link  = FILMDICT['SiteURL']
                    if len(title) > 40:
                        for i in range(40, -1, -1):
                            if title[i] == ' ':
                                title = title[0:i]
                                break
                    newReview.source = (title if title else FILMDICT['Title']) + '...'
                    if len(writing) > 275:
                        for i in range(275, -1, -1):
                            if writing[i] in ['.', '!', '?']:
                                writing = writing[0:i + 1]
                                break
                    newReview.text = writing
                    log(LOG_SUBLINE)
                except Exception as e:
                    log('UPDATE:: Error getting Review No. %s: %s', count, e)
        except Exception as e:
            log('UPDATE:: Error getting Reviews: %s', e)

        # 2g.   Summary = IAFD Legend + Synopsis
        log(LOG_BIGLINE)
        # synopsis
        try:
            synopsis = html.xpath('.//div[@id="Description"]/span/text()')[0]
            log('UPDATE:: Synopsis Found: %s', synopsis)
            synopsis = utils.TranslateString(synopsis, SITE_LANGUAGE, lang, DETECT)
        except Exception as e:
            synopsis = ''
            log('UPDATE:: Error getting Synopsis: %s', e)

        # combine and update
        log(LOG_SUBLINE)
        summary = ('{0}\n{1}\n{2}' if PREFIXLEGEND else '{1}\n{0}\n{2}').format(FILMDICT['Legend'], synopsis.strip(), FILMDICT['Synopsis'])
        summary = summary.replace('\n\n', '\n')
        metadata.summary = summary

        log(LOG_BIGLINE)
        log('UPDATE:: Finished Update Routine')
        log(LOG_BIGLINE)