#!/usr/bin/env python
# encoding=utf8
'''
# GayDVDEmpire (IAFD)
                                    Version History
                                    ---------------
    Date            Version             Modification
    13 Apr 2020   2019.08.12.03    Corrected scrapping of collections
    14 Apr 2020   2019.08.12.04    sped up search routine, corrected tagline
                                   search multiple result pages
    01 Jun 2020   2019.08.12.05    Implemented translation of summary
                                   improved getIAFDActor search
    27 Jun 2020   2019.08.12.06    Improvement to Summary Translation: Translate into Plex Library Language
                                   stripping of internet domain suffixes from studio names when matching
                                   handling of unicode characters in film titles and comparision string normalisation
    30 Aug 2020   2019.08.12.07    Handling of Roman Numerals in Titles to Match Arabic Numerals
                                   Errors in getting production year and release dates corrected
    22 Sep 2020   2019.08.12.08    Correction to regex string to handle titles in Sort Order trailing determinates
    07 Oct 2020   2019.08.12.09    IAFD - change to https
    19 Jan 2021   2019.08.12.10    Improved on IAFD search, actors sexual roles if recorded are returned, if not shows a red circle.
                                   corrections to xpath extra )... failing to get genres, cast and directors
    19 Feb 2021   2019.08.12.12    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including LevenShtein Matching on Cast names
                                   set content_rating age to 18
                                   Set collections from filename + countries, cast and directors
                                   Added directors photos
                                   included studio on iafd processing of filename
                                   Added iafd legend to summary
                                   improved logging
    11 Mar 2021   2019.08.12.13    Cast xpath was picking Bios and Interview along with cast name - corrected
    31 Jul 2021   2019.08.12.14    Code reorganisation
    04 Feb 2022   2019.08.12.15    implemented change suggested by Cody: duration matching optional on IAFD matching
                                   Cast list if used in filename becomes the default that is matched against IAFD, useful in case no cast is listed in agent

---------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2019.08.12.15'
PLUGIN_LOG_TITLE = 'GayDVDEmpire'

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

# URLS
BASE_URL = 'http://www.gaydvdempire.com'
BASE_SEARCH_URL = BASE_URL + '/AllSearch/Search?view=list&exactMatch={0}&q={0}'

# dictionary holding film variables
FILMDICT = {}

# Date Formats used by website
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
class GayDVDEmpire(Agent.Movies):
    ''' define Agent class '''
    name = 'GayDVDEmpire (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        log('AGNT  :: Original Search Query        : {0}'.format(myString))

        myString = myString.lower().strip()
        myString = myString.replace(' -', ':').replace(ur'\u2013', '-').replace(ur'\u2014', '-')

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

        # Check filename format
        try:
            FILMDICT = utils.matchFilename(media)
        except Exception as e:
            log('SEARCH:: Error: %s', e)
            return

        FILMDICT['Scraper'] = GayDVDEmpire.name
        log(LOG_BIGLINE)

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        morePages = True
        while morePages:
            log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=90, errors='ignore', sleep=DELAY)
            except Exception as e:
                log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                break

            try:
                searchQuery = html.xpath('.//a[@title="Next"]/@href')[0]
                pageNumber = int(searchQuery.split('page=')[1]) # next page number
                searchQuery = BASE_SEARCH_URL.format(searchTitle) + '&page={0}'.format(pageNumber)
                pageNumber = pageNumber - 1
                log('SEARCH:: Search Query: %s', searchQuery)
                morePages = True if pageNumber <= 10 else False
            except:
                pageNumber = 1
                morePages = False

            titleList = html.xpath('.//div[contains(@class,"row list-view-item")]')
            log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
            log(LOG_BIGLINE)
            for title in titleList:
                # siteTitle = The text in the 'title' - Gay DVDEmpire - displays its titles in SORT order
                try:
                    siteTitle = title.xpath('./div/h3/a[@category and @label="Title"]/@title')[0]
                    # convert sort order version to normal version i.e "Best of Zak Spears, The -> The Best of Zak Spears"
                    pattern = u', (The|An|A)$'
                    matched = re.search(pattern, siteTitle, re.IGNORECASE)  # match against string
                    if matched:
                        determinate = matched.group().replace(', ', '')
                        log('SEARCH:: Found Determinate:           %s', determinate)
                        siteTitle = re.sub(pattern, '', siteTitle)
                        siteTitle = '{0} {1}'.format(determinate, siteTitle)
                        log('SEARCH:: Re-ordered Site Title:       %s', siteTitle)

                    utils.matchTitle(siteTitle, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Title: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('./div/h3/a[@label="Title"]/@href')[0]
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
                    siteStudio = title.xpath('./div/ul/li/a/small[text()="studio"]/following-sibling::text()')[0].strip()
                    utils.matchStudio(siteStudio, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Studio: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Production Year found in brackets - if fails try Release Date 
                try:
                    siteProductionYear = title.xpath('.//small[contains(., "(")]/text()')[0].replace('(', '').replace(')', '').strip()
                    try:
                        siteReleaseDate = utils.matchReleaseDate(siteProductionYear, FILMDICT)
                        log(LOG_BIGLINE)
                    except Exception as e:
                        log('SEARCH:: Error getting Site URL Release Date: %s', e)
                        log(LOG_SUBLINE)
                        continue
                except:
                    # failed to scrape production year - so try release date
                    try:
                        siteReleaseDate = title.xpath('.//small[text()="released"]/following-sibling::text()')[0].strip()
                        try:
                            siteReleaseDate = utils.matchReleaseDate(siteReleaseDate, FILMDICT)
                            log(LOG_BIGLINE)
                        except Exception as e:
                            log('SEARCH:: Error getting Site URL Release Date: %s', e)
                            log(LOG_SUBLINE)
                            continue
                    except:
                        # failed to scrape release date to
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
        #        a. Genres
        #        b. Collections
        #        c. Directors            : List of Drectors (alphabetic order)
        #        d. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        e. Posters/Background
        #        f. Summary

        # 2a.   Genres
        log(LOG_BIGLINE)
        try:
            ignoreGenres = ['sale', '4k ultra hd']
            genres = []
            htmlgenres = html.xpath('//ul[@class="list-unstyled m-b-2"]//a[@label="Category"]/text()[normalize-space()]')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort()
            log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                if anyOf(x in genre.lower() for x in ignoreGenres):
                    continue
                genres.append(genre)
                if 'compilation' in genre.lower():
                    FILMDICT['Compilation'] = 'Compilation'

            metadata.genres.clear()
            for genre in genres:
                metadata.genres.add(genre)
                if COLGENRE:
                    metadata.collections.add(genre)

        except Exception as e:
            log('UPDATE:: Error getting Genres: %s', e)

        # 2b.   Collections
        log(LOG_BIGLINE)
        try:
            htmlcollections = html.xpath('//a[contains(@label, "Series")]/text()[normalize-space()]')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            htmlcollections = [x.replace('"', '').replace('Series', '').strip() for x in htmlcollections]
            log('UPDATE:: %s Collections Found: %s', len(htmlcollections), htmlcollections)
            for collection in htmlcollections:
                if collection.lower() in map(str.lower, FILMDICT['Collection']):  # if set by filename its already in the list - FILMDICT['Collection'] contains a list
                    continue
                metadata.collections.add(collection)
                log('UPDATE:: %s Collection Added: %s', collection)

        except Exception as e:
            log('UPDATE:: Error getting Collections: %s', e)

        # 2c.   Directors
        log(LOG_BIGLINE)
        try:
            htmldirectors = html.xpath('//a[contains(@label, "Director - details")]/text()[normalize-space()]')
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
            log('UPDATE:: Error getting Directors: %s', e)

        # 2d.   Cast
        log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('//a[@class="PerformerName" and @label="Performers - detail"]/text()')
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

        # 2e.   Poster/Art
        log(LOG_BIGLINE)
        try:
            htmlimage = html.xpath('//*[@id="front-cover"]/img')[0]
            image = htmlimage.get('src')
            log('UPDATE:: Poster Image Found: %s', image)
            #  set poster then only keep it
            metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.posters.validate_keys([image])

            image = image.replace('h.jpg', 'bh.jpg')
            log('UPDATE:: Art Image Found: %s', image)
            #  set poster then only keep it
            metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.art.validate_keys([image])

        except Exception as e:
            log('UPDATE:: Error getting Poster/Art: %s', e)

        # 2f.   Reviews - Put all Scene Information here
        log(LOG_BIGLINE)
        try:
            htmlscenes = html.xpath('//div[@class="col-sm-6 m-b-1"]')
            log('UPDATE:: Possible Number of Scenes [%s]', len(htmlscenes))

            metadata.reviews.clear()
            sceneCount = 0 # avoid enumerating the number of scenes as some films have empty scenes
            for count, scene in enumerate(htmlscenes, start=1):
                log('UPDATE:: Scene No %s', count)
                try:
                    try:
                        title = scene.xpath('.//a[@label="Scene Title"]/text()[normalize-space()]')[0]
                        log('UPDATE:: Scene Title: %s', title)
                    except:
                        log('UPDATE:: No Scene Title')
                        title = ''

                    try:
                        writing = scene.xpath('.//span[@class="badge"]/text()[normalize-space()]')[0]
                        writing = ''.join(writing).strip()
                        log('UPDATE:: Scene Text: %s', writing)
                    except:
                        log('UPDATE:: No Scene writing')
                        writing = ''

                    # if no title and no scene write up
                    if not title and not writing:
                        continue
                    sceneCount += 1

                    newReview = metadata.reviews.new()
                    newReview.author = 'Gay DVD Empire'
                    newReview.link  = FILMDICT['SiteURL']
                    if len(title) > 40:
                        for i in range(40, -1, -1):
                            if title[i] == ' ':
                                title = title[0:i]
                                break
                    newReview.source = '{0}. {1}...'.format(sceneCount, title if title else FILMDICT['Title'])
                    if len(writing) > 275:
                        for i in range(275, -1, -1):
                            if writing[i] in ['.', '!', '?']:
                                writing = writing[0:i + 1]
                                break
                    newReview.text = utils.TranslateString(writing, SITE_LANGUAGE, lang, DETECT)
                    log(LOG_SUBLINE)
                except Exception as e:
                    log('UPDATE:: Error getting Scene No. %s: %s', count, e)
        except Exception as e:
            log('UPDATE:: Error getting Scenes: %s', e)

        # 2g.   Summary = IAFD Legend + Synopsis
        log(LOG_BIGLINE)
        # synopsis
        try:
            synopsis = html.xpath('//div[@class="col-xs-12 text-center p-y-2 bg-lightgrey"]/div/p')[0].text_content().strip()
            synopsis = re.sub('<[^<]+?>', '', synopsis)
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