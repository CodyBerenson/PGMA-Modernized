#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# nymMedia - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    06 Jan 2021   2021.01.06.01    Creation
    27 Feb 2021   2021.01.06.03    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including Levenshtein Matching on Cast names
                                   Added iafd legend to summary
-----------------------------------------------------------------------------------------------------------------------------------
'''
import datetime, platform, os, re, sys, json
from unidecode import unidecode
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2021.01.06.03'
PLUGIN_LOG_TITLE = 'nymMedia'
LOG_BIGLINE = '------------------------------------------------------------------------------'
LOG_SUBLINE = '      ------------------------------------------------------------------------'

# Preferences
REGEX = Prefs['regex']                      # file matching pattern
YEAR = Prefs['year']                        # is year mandatory in the filename?
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
BACKGROUND = Prefs['background']            # download art

# IAFD Related variables
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/results.asp?searchtype=comprehensive&searchstring={0}'

IAFD_ABSENT = u'\U0000274C'        # red cross mark - not on IAFD
IAFD_FOUND = u'\U00002705'         # heavy white tick on green - on IAFD
IAFD_THUMBSUP = u'\U0001F44D'      # thumbs up unicode character
IAFD_THUMBSDOWN = u'\U0001F44E'    # thumbs down unicode character
IAFD_LEGEND = u'CAST LEGEND\u2003{0} Actor not on IAFD\u2003{1} Actor on IAFD\u2003:: {2} Film on IAFD ::'

# URLS - nymMedia uses post requests rather than building up urls
BASE_URL = 'https://www.nymmedia.com'
BASE_SEARCH_URL = BASE_URL + '/nymVideo/control/search'

# dictionary holding film variables
FILMDICT = {}   

# Date Formats used by website
DATEFORMAT = '%Y%m%d'

# Website Language
SITE_LANGUAGE = 'en'

# ----------------------------------------------------------------------------------------------------------------------------------
def Start():
    ''' initialise process '''
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'
    HTTP.Headers['Cookie'] = 'JSESSIONID=JpKTGsPEh83w7RR5iLyftH-Z.undefined; __utmz=109840026.1609887627.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utmc=109840026; __utma=109840026.740767263.1609887627.1609970853.1609974688.5; __utmt=1; __utmb=109840026.8.10.1609974688'

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
class nymMedia(Agent.Movies):
    ''' define Agent class '''
    name = 'nymMedia (IAFD)'
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
        myString = myString.replace(' - ', ': ')
        myString = myString.lower().strip()
        myString = String.StripDiacritics(myString)

        # strip non-alphanumeric characters bar space and colon
        pattern = ur'[^A-Za-z0-9]+'
        myString = re.sub(pattern, ' ', myString, flags=re.IGNORECASE)
        myString = myString.replace('  ', ' ').strip()

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
        self.log('SEARCH:: Preferences:')
        self.log('SEARCH::  > Cast Legend Before Summary: %s', PREFIXLEGEND)
        self.log('SEARCH::  > Collection Gathering')
        self.log('SEARCH::      > Cast                  : %s', COLCAST)
        self.log('SEARCH::      > Director(s)           : %s', COLDIRECTOR)
        self.log('SEARCH::      > Studio                : %s', COLSTUDIO)
        self.log('SEARCH::      > Film Title            : %s', COLTITLE)
        self.log('SEARCH::      > Genres                : %s', COLGENRE)
        self.log('SEARCH::  > Delay                     : %s', DELAY)
        self.log('SEARCH::  > Language Detection        : %s', DETECT)
        self.log('SEARCH::  > Library:Site Language     : %s:%s', lang, SITE_LANGUAGE)
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
        searchQuery = BASE_SEARCH_URL
        # Here are all of our headers
        formData = {'search_text': '{0}'.format(searchTitle),
                    'search_span': 'Selected',
                    'search_title': 'true',
                    'search.x': 0,
                    'search.y': 0}

        morePages = True
        while morePages:
            self.log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, values=formData, headers=formData, timeout=20, sleep=DELAY)
                # Finds the entire media enclosure
                titleList = html.xpath('//td[@class="contentH1"]')
                if not titleList:
                    break
            except Exception as e:
                self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                return

            try:
                nextPageNumber = html.xpath('//area[@alt="Next"]/@title')[0].split()[1].strip()
                self.log('SEARCH:: Created Post Request for Next Page [%s]', nextPageNumber)
                pageNumber = int(nextPageNumber) - 1
                startIndex = pageNumber * 10
                formData = {'searchText': '{0}'.format(searchTitle),
                            'search_span': 'Selected',
                            'search_title': 'true',
                            'search_reviews': 'false',
                            'startIndex': startIndex,
                            'pageSize': 10,
                            'sortOption': 3}
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
                    siteTitle = title.xpath('./a/text()')[0]
                    self.matchTitle(siteTitle, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Title: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('./a/@href')[0]
                    siteURL = '{0}/nymVideo/control/{1}'.format(BASE_URL, siteURL)
                    FILMDICT['SiteURL'] = siteURL
                    self.log('SEARCH:: Site Title url                %s', siteURL)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Title Url: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # Access Site URL for Studio Name information
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
                    siteStudio = html.xpath('//tr[td[@class="contentH2" and text()="Studio:"]]/td[3]/a/text()')[0].strip()
                    self.matchStudio(siteStudio, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Studio: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # Site Release Date
                try:
                    siteReleaseDate = html.xpath('//tr[td[@class="contentH2" and text()="Year:"]]/td[3]/text()')[0].strip()
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
        self.log('UPDATE:: Version                      : v.%s', VERSION_NO)
        self.log('UPDATE:: File Name                    : %s', filename)
        self.log('UPDATE:: File Folder                  : %s', folder)
        self.log(LOG_BIGLINE)

        # Fetch HTML.
        FILMDICT = json.loads(metadata.id)
        self.log('UPDATE:: Film Dictionary Variables:')
        for key in sorted(FILMDICT.keys()):
            self.log('UPDATE:: {0: <29}: {1}'.format(key, FILMDICT[key]))
        self.log(LOG_BIGLINE)

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
        #        a. Genres               : alphabetic order
        #        b. Rating               : out of 10
        #        c. Countries            : alphabetic order
        #        d. Directors            : List of Directors (alphabetic order)
        #        e. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        f. Posters/Art
        #        g. Reviews
        #        h. Summary

        # 2a.   Genres
        self.log(LOG_BIGLINE)
        try:
            htmlgenres = html.xpath('//tr[td[@class="contentH2" and text()="Themes:"]]/td[3]/a/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort()
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            metadata.genres.clear()
            for genre in htmlgenres:
                if 'compilation' in genre.lower():
                    filmDict['Compilation'] = 'Compilation'

                metadata.genres.add(genre)
                # add genres to collection
                if COLGENRE:
                    metadata.collections.add(genre)

        except Exception as e:
            self.log('UPDATE:: Error getting Genres: %s', e)

        # 2b.   Rating (out of 5 Stars) = Rating can be a maximum of 10 - float value
        self.log(LOG_BIGLINE)
        try:
            rating = html.xpath('//tr[td[@class="contentH2" and text()="Our Rating:"]]/td[3]/img[@title="Production Quality Rating"]/@src')[0]
            rating = re.sub('[^0-9]', '', rating)   # strip out non-numerics, including decimals 2.8 will return as 28
            rating = float(rating) * 2.0/10.0 if float(rating) * 2.0 > 10 else float(rating) * 2.0
            self.log('UPDATE:: Production Rating %s', rating)
            metadata.rating = rating
        except Exception as e:
            self.log('UPDATE:: Error getting Film Production Rating; Try Average Member Rating: %s', e)
            # check if there is an average member rating
            try:
                rating = html.xpath('//tr[td[@class="contentH2" and text()="Average Member Rating:"]]/td[3]/img[not(contains(@src, "turnOn"))]/@title')[0]
                rating = re.sub('[^0-9]', '', rating)   # strip out non-numerics
                rating = float(rating) * 2.0/10.0 if float(rating) * 2.0 > 10 else float(rating) * 2.0
                self.log('UPDATE:: Average Member Rating %s', rating)
                metadata.rating = rating
            except Exception as e:
                metadata.rating = 0.0
                self.log('UPDATE:: Error getting Production/Average Member Rating: %s', e)

        # 2c.   Countries
        self.log(LOG_BIGLINE)
        try:
            htmlcountries = html.xpath('//tr[td[@class="contentH2" and text()="Produced in:"]]/td[3]/a/text()')
            htmlcountries = [x.strip() for x in htmlcountries if x.strip()]
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

        # 2d.   Directors
        self.log(LOG_BIGLINE)
        try:
            htmldirectors = html.xpath('//tr[td[@class="contentH2" and text()="Directed by:"]]/td[3]/a/text()')
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

        # 2e.   Cast: get thumbnails from IAFD if missing as they are right dimensions for plex cast list
        self.log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('//tr[td[@class="contentH2" and text()="Cast:"]]/td[3]/a/text()')
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
            htmlimages = html.xpath('//span[@title="Click here to view larger image"]/a/@href')
            htmlimages = ['https:' + x for x in htmlimages]
            image = htmlimages[0]
            self.log('UPDATE:: Poster Image Found: %s', image)
            #  set poster then only keep it
            metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.posters.validate_keys([image])

            if BACKGROUND:
                image = htmlimages[1]
                self.log('UPDATE:: Art Image Found: %s', image)
                metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
                metadata.art.validate_keys([image])

        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Art: %s', e)

        # 2g.   Reviews
        self.log(LOG_BIGLINE)
        reviewCount = 4
        try:
            htmlreviews = html.xpath('//table[@id="customerReviews"]/following-sibling::table')
            htmlreviews = htmlreviews[:reviewCount] if len(htmlreviews) >= reviewCount else htmlreviews
            self.log('UPDATE:: Number of Reviews [%s]', len(htmlreviews))
            metadata.reviews.clear()
            for count, review in enumerate(htmlreviews, start=1):
                self.log('UPDATE:: Review No %s', count)
                try:
                    try:
                        title = review.xpath('.//td[@class="contentH2"]/text()')
                        title = ''.join(title).strip()
                        self.log('UPDATE:: Review Title: %s', title)
                    except:
                        title = ''
                    try:
                        stars = review.xpath('.//td[@class="contentReview"]/img[contains(@src, "star")]/@src')[0]
                        stars = re.sub('[^0-9]', '', stars)   # strip out non-numerics
                        stars = [u'\U00002B50'] * int(stars)  # change type to list of size
                        stars = ''.join(stars)                # convert back to str
                        self.log('UPDATE:: Review Stars: %s', stars)
                    except:
                        stars = ''
                    try:
                        writer =  review.xpath('.//td[@class="contentReview"][count(@*)=1]//text()[normalize-space()]')
                        writer = ''.join(writer)
                        writer = ' '.join(writer.split())
                        self.log('UPDATE:: Review Writer: %s', writer)
                    except:
                        writer = ''
                    try:
                        writing = review.xpath('.//td[@class="contentReview"][@colspan="2"]/text()[normalize-space()]')
                        writing = ''.join(writing)
                        self.log('UPDATE:: Review Text: %s', writing)
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
                    self.log(LOG_SUBLINE)
                except Exception as e:
                    self.log('UPDATE:: Error getting Review No. %s: %s', count, e)
        except Exception as e:
            self.log('UPDATE:: Error getting Reviews: %s', e)

        # 2h.   Summary = IAFD Legend + Synopsis - if no synopsis there is usually an Agent Website review
        self.log(LOG_BIGLINE)
        # synopsis
        try:
            synopsis = ''
            htmlsynopsis = html.xpath('//div[@id="synopsis"]/text()')
            synopsis = ' '.join(htmlsynopsis).strip()
            if synopsis:            
                self.log('UPDATE:: Synopsis Found: %s', synopsis)
            else:
                raise('No Synopsis Found!')
        except Exception as e:
            self.log('UPDATE:: Error getting Synopsis: Try nymMedia Review: %s', e)
            htmlsynopsis = html.xpath('//div[@id="ourReview" or @id="extendedReview"]/p//text()')
            synopsis = ' '.join(htmlsynopsis).replace('\t', '').replace('\n more... ', '').strip()
            self.log('UPDATE:: Synopsis Found: %s', synopsis)
            synopsis = 'nymMEDIA Review:\n' + synopsis if synopsis else ''

        # combine and update
        self.log(LOG_SUBLINE)
        castLegend = IAFD_LEGEND.format(IAFD_ABSENT, IAFD_FOUND, IAFD_THUMBSUP if FILMDICT['FoundOnIAFD'] == "Yes" else IAFD_THUMBSDOWN)
        summary = ('{0}\n{1}' if PREFIXLEGEND else '{1}\n{0}').format(castLegend, synopsis.strip())
        summary = summary.replace('\n\n', '\n')
        metadata.summary = self.TranslateString(summary, lang)

        self.log(LOG_BIGLINE)
        self.log('UPDATE:: Finished Update Routine')
        self.log(LOG_BIGLINE)