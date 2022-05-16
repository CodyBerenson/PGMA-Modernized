#!/usr/bin/env python
# encoding=utf8
'''
# SimplyAdult - (IAFD): Hot Free Gay Porn Movies
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    15 Nov 2021   2021.11.15.01    Initial
    04 Feb 2022   2021.11.15.02    implemented change suggested by Cody: duration matching optional on IAFD matching
                                   Cast list if used in filename becomes the default that is matched against IAFD, useful in case no cast is listed in agent
-----------------------------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2021.11.15.02'
PLUGIN_LOG_TITLE = 'SimplyAdult'

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
BASE_URL = 'https://www.simply-adult.com/'
BASE_SEARCH_URL = BASE_URL + 'search.php'

# dictionary holding film variables
FILMDICT = {}   

# Date Formats used by website
DATEFORMAT = '%d-%m-%Y'

# Website Language
SITE_LANGUAGE = 'en'

# ----------------------------------------------------------------------------------------------------------------------------------
def Start():
    ''' initialise process '''
    HTTP.CacheTime = 0
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.34'
    #HTTP.Headers['Set-Cookie'] = 'xid_509da=d3544e95f63a25f786d74ec818b41eae; path=/; domain=www.simply-adult.com; secure; httponly'
    HTTP.Headers['Cookie'] = 'partner=51; RefererCookie=https://www.gaydvds.co.uk/; store_language=en; _ga=GA1.2.604161530.1634826735; partner_clickid=5815773; partner_time=1645891068; _gid=GA1.2.1143087968.1638115069; xid_509da=d3544e95f63a25f786d74ec818b41eae'
    HTTP.Headers['Referer'] = 'https://www.simply-adult.com/search.php'
    HTTP.Headers['Cache-Control'] = 'max-age=0'
    
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
class SimplyAdult(Agent.Movies):
    ''' define Agent class '''
    name = 'SimplyAdult (IAFD)'
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        log('AGNT  :: Original Search Query        : {0}'.format(myString))

        # convert to lower case and trim
        myString = myString.replace(' - ', ': ').replace('- ', ': ')
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

        # Search Query - for use to search the internet, remove all non alphabetic characters etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL
        # Here are all of our headers
        posted_data = {'substring': '', 'including': 'phrase', 'by_title': 'on', 'categoryid': None, 'search_in_subcategories': 'on', 'price_min': None, 'price_max': None, 'weight_min': None, 'weight_max': None}
        formData1 = {'mode': 'search', 'posted_data': posted_data}

        posted_data = {'by_title': 'Y', 'by_descr': 'Y', 'by_sku': 'Y', 'search_in_subcategories': 'Y', 'including': 'all', 'substring': '{0}'.format(searchTitle)}
        formData = {'simple_search': 'Y', 'mode': 'search', 'posted_data': posted_data, 'x': 0, 'y': 0}

        log('SEARCH:: Search Query: %s', formData)
        try:
            html = HTML.ElementFromURL(searchQuery, values=formData, headers=formData, timeout=20, sleep=DELAY)
            # Finds the entire media enclosure
            titleList = html.xpath('//div[@class="item-box"]')
        except Exception as e:
            log('SEARCH:: Error: Search Query did not pull any results: %s', e)
            return

        log('SEARCH:: Result Page No: 1, Titles Found %s', len(titleList))
        log(LOG_BIGLINE)
        for title in titleList:
            # Site Title
            try:
                siteTitle = title.xpath('./div[@class="details"]/a/text()')[0]
                utils.matchTitle(siteTitle, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error getting Site Title: %s', e)
                log(LOG_SUBLINE)
                continue

            # Studio Name
            try:
                siteStudio = title.xpath('./div[@class="details"]/div[@class="manufacturer"]/text()')[0]
                utils.matchStudio(siteStudio, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error getting Site Studio: %s', e)
                log(LOG_SUBLINE)
                continue

            # Site Title URL
            try:
                siteURL = title.xpath('./div[@class="details"]/a/@href')[0]
                FILMDICT['SiteURL'] = siteURL
                log('SEARCH:: Site Title url                %s', siteURL)
                log(LOG_BIGLINE)
            except Exception as e:
                log('SEARCH:: Error getting Site Title Url: %s', e)
                log(LOG_SUBLINE)
                continue

            # NO Site Release Date recorded

            # NO Duration recorded

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
        log('UPDATE:: Tagline: %s', metadata.tagline)
        if FILMDICT['Year']:
            metadata.originally_available_at = datetime.strptime(FILMDICT['CompareDate'], DATEFORMAT)
            metadata.year = metadata.originally_available_at.year
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
        log('UPDATE:: Collection Set From Filename: %s', collections)

        #    2.  Metadata retrieved from website
        #        a. Collections          : Alphabetic order
        #        b. Countries            : Alphabetic order
        #        c. Rating
        #        d. Directors            : List of Directors (alphabetic order)
        #        e. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        f. Posters/Background
        #        g. Summary

        # 2a.   Collections
        log(LOG_BIGLINE)
        try:
            htmlcollections = html.xpath('//div[@class="property-name"][text()="Series"]/following-sibling::div[@class="property-value"]/a/text()[normalize-space()]')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            log('UPDATE:: %s Collections Found: %s', len(htmlcollections), htmlcollections)
            uniqueCollections = [x for x in htmlcollections if x.lower() not in (y.lower() for y in FILMDICT['Collection'])]
            for collection in uniqueCollections:
                metadata.collections.add(collection)
                log('UPDATE:: Collection Added: %s', collection)
        except Exception as e:
            log('UPDATE:: Error getting Collections: %s', e)

        # 2b.   Directors
        log(LOG_BIGLINE)
        try:
            htmldirectors = html.xpath('//div[@class="property-name"][text()="Director"]/following-sibling::div[@class="property-value"]/a/text()')
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
            htmlcast = html.xpath('//div[@class="property-name"][text()="Cast:"]/following-sibling::div[@class="property-value"]/a/text()')
            htmlcast = ['{0}'.format(x.strip()) for x in htmlcast if x.strip() and 'n/a' not in x.lower()]
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

        # 2d.   Posters/Background Art
        #       Simply Adult only stores the poster image and poster+background art as the second image
        #       apply the poster image to both
        log(LOG_BIGLINE)
        try:
            htmlimages = html.xpath('//img[@id="product_thumbnail"]/@src')
            for i, htmlimage in enumerate(htmlimages):
                htmlimages[i] = htmlimage if 'https:' in htmlimage else 'https:' + htmlimage

            if len(htmlimages) == 1:    # if only one image duplicate it
                htmlimages.append(htmlimages[0])

            image = htmlimages[0]
            log('UPDATE:: Poster Image Found: [1] - %s', image)
            metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.posters.validate_keys([image])

            image = htmlimages[1]
            log('UPDATE:: Art Image Found: [2] - %s', image)
            metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.art.validate_keys([image])

        except Exception as e:
            log('UPDATE:: Error getting Poster/Art: %s', e)

        # 2e.   Summary = Synopsis with IAFD Legend
        log(LOG_BIGLINE)
        try:
            synopsis = html.xpath('//div[@class="product_description"]/text()')[0].strip()
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