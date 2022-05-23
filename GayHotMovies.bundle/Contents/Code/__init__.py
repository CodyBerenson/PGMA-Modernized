#!/usr/bin/env python
# encoding=utf8
'''
# GayHotMovies (IAFD)
                                    Version History
                                    ---------------
    Date            Version             Modification
    12 Aug 2019   2019.08.12.01    Creation
    25 Apr 2020   2019.08.12.02    added multiple result pages handling
                                   removed debug print option
                                   improved error handling
    23 May 2020   2019.08.12.03    Added scene breakdown to summary
    01 Jun 2020   2019.08.12.04    Implemented translation of summary
                                   improved getIAFDActor search
    27 Jun 2020   2019.08.12.05    Improvement to Summary Translation: Translate into Plex Library Language
                                   stripping of intenet domain suffixes from studio names when matching
                                   handling of unicode characters in film titles and comparision string normalisation
    30 Aug 2020   2019.08.12.06    Handling of Roman Numerals in Titles to Match Arabic Numerals
                                   dodgy xpath around site studio name corrected
    12 Sep 2020   2019.08.12.07    Improved search facility - titles with non alphabetic characters like "!" 
                                   were failing to search... took code from GEVI
    07 Oct 2020   2019.08.12.08    IAFD - change to https
    16 Jan 2021   2019.08.12.09    Improved on IAFD search, actors sexual roles if recorded are returned, if not shows a red circle.
    19 Feb 2021   2019.08.12.11    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including LevenShtein Matching on Cast names
                                   set content_rating age to 18
                                   Set collections from filename + countries, cast and directors
                                   Added directors photos
                                   included studio on iafd processing of filename
                                   Added iafd legend to summary
                                   improved logging
    13 Aug 2021   2019.08.12.12    Use of duration matching
                                   Use of review area for scene matching
                                   Code reorganisation
    25 Aug 2021   2019.08.12.13    IAFD will be only searched if film found on agent Catalogue
                                   changes to xpath
    04 Feb 2022   2019.18.12.14    implemented change suggested by Cody: duration matching optional on IAFD matching
                                   Cast list if used in filename becomes the default that is matched against IAFD, useful in case no cast is listed in agent
---------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2019.08.12.14'
PLUGIN_LOG_TITLE = 'GayHotMovies'

# log section separators
LOG_BIGLINE = '--------------------------------------------------------------------------------'
LOG_SUBLINE = '      --------------------------------------------------------------------------'

# Preferences
DELAY = int(Prefs['delay'])                         # Delay used when requesting HTML, may be good to have to prevent being banned from the site
MATCHIAFDDURATION = Prefs['matchiafdduration']      # Match against IAFD Duration value
MATCHSITEDURATION = Prefs['matchsiteduration']      # Match against Site Duration value
DURATIONDX = int(Prefs['durationdx'])               # Acceptable difference between actual duration of video file and that on agent website
DETECT = Prefs['detect']                            # detect the language the summary appears in on the web page
PREFIXLEGEND = Prefs['prefixlegend']                # place cast legend at start of summary or end
COLCLEAR = Prefs['clearcollections']                # clear previously set collections
COLSTUDIO = Prefs['studiocollection']               # add studio name to collection
COLTITLE = Prefs['titlecollection']                 # add title [parts] to collection
COLGENRE = Prefs['genrecollection']                 # add genres to collection
COLDIRECTOR = Prefs['directorcollection']           # add director to collection
COLCAST = Prefs['castcollection']                   # add cast to collection
COLCOUNTRY = Prefs['countrycollection']             # add country to collection

# URLS
BASE_URL = 'https://www.gayhotmovies.com'
BASE_SEARCH_URL = BASE_URL + '/search.php?num_per_page=48&&page_sort=relevance&search_string={0}&find_with=all&searchtype_value=video_title'

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
class GayHotMovies(Agent.Movies):
    ''' define Agent class '''
    name = 'GayHotMovies (IAFD)'
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
        nullChars = ['-', "'", ',' '&', '!', '.', '#'] # to be replaced with null
        pattern = u'[{0}]'.format(''.join(nullChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            log('AGNT  :: Search Query:: Replacing characters in string. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, '', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            log('AGNT  :: Amended Search Query [{0}]'.format(myString))
        else:
            log('AGNT  :: Search Query:: String has none of these {0}'.format(pattern))

        spaceChars = [ur'\u2013', ur'\u2014', '(', ')']  # to be replaced with space
        pattern = u'[{0}]'.format(''.join(spaceChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            log('AGNT  :: Search Query:: Replacing characters with Space. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, ' ', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            log('AGNT  :: Amended Search Query [{0}]'.format(myString))
        else:
            log('AGNT  :: Search Query:: String has none of these {0}'.format(pattern))

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
                searchQuery = html.xpath('//a[@title="Next Page"]/@href')[0]
                searchQuery = (BASE_URL if BASE_URL not in searchQuery else '') + searchQuery
                pageNumber = int(searchQuery.split('&')[0].split('=')[1]) - 1
                morePages = True if pageNumber <= 10 else False
            except:
                pageNumber = 1
                morePages = False

            titleList = html.xpath('//div[@class="cell movie_box"]')
            log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))

            log(LOG_BIGLINE)
            for title in titleList:
                # Site Title
                try:
                    siteTitle = title.xpath('./div/div/h3[contains(@class,"title")]/a/text()')[0].strip()
                    utils.matchTitle(siteTitle, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Title: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('./div/div/h3[contains(@class,"title")]/a/@href')[0].strip()
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    FILMDICT['SiteURL'] = siteURL
                    log('SEARCH:: Site Title url                %s', siteURL)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Title Url: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Studio Name
                try:
                    siteStudio = title.xpath('./div/div/span/strong[text()="Studio:"]/following::a[contains(@title,"Studio name:")]/text()')[0].strip()
                    utils.matchStudio(siteStudio, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('SEARCH:: Error getting Site Studio: %s', e)
                    log(LOG_SUBLINE)
                    continue

                # Site Release Date
                try:
                    siteReleaseDate = title.xpath('./div/div/div/span[@class="release_year"]/a/text()')[0].strip()
                    siteReleaseDate = siteReleaseDate.replace('sept ', 'sep ').replace('july ', 'jul ')
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
                        log('SEARCH:: Reading Site URL page         %s', siteURL)
                        html = HTML.ElementFromURL(siteURL, sleep=DELAY)
                        log(LOG_BIGLINE)
                    except Exception as e:
                        log('SEARCH:: Error reading Site URL page: %s', e)
                        log(LOG_SUBLINE)
                        continue

                    try:
                        siteDuration = html.xpath('//span[@datetime]/text()')[0]
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
        #        a. Categories           : Countries, Genres
        #        b. Collections
        #        c. Rating
        #        d. Directors            : List of Directors (alphabetic order)
        #        e. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        f. Posters/Art
        #        g. Reviews
        #        h. Summary

        # 2a.  Process Categories: Countries, Genres
        log(LOG_BIGLINE)
        try:
            ignoreCategories = ['language', 'gay', 'movies', 'website', 'settings', 'locale', 'plot', 'character']
            countries = []
            genres = []
            htmlcategories = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/category/")]/@title')
            htmlcategories = [x.strip() for x in htmlcategories if x.strip()]
            htmlcategories.sort()
            log('UPDATE:: %s Categories Found: %s', len(htmlcategories), htmlcategories)
            for category in htmlcategories:
                if anyOf(x in category.lower() for x in ignoreCategories):
                    continue
                elif 'international' in category.lower():
                    countries.append(category.split('->')[-1])
                else:
                    category = category.replace('Bareback ->', 'Bareback ')
                    genres.append(category.split('->')[-1])
                    if 'compilation' in category.lower():
                        FILMDICT['Compilation'] = 'Compilation'

            log('UPDATE:: %s Countries Found: %s', len(countries), countries)
            metadata.countries.clear()
            for country in countries:
                metadata.countries.add(country)

            log('UPDATE:: %s Genres Found: %s', len(genres), genres)
            metadata.genres.clear()
            for genre in genres:
                metadata.genres.add(genre)
                # add genres to collection
                if COLGENRE:
                    metadata.collections.add(genre)

        except Exception as e:
            log('UPDATE:: Error getting Categories: Countries and Genres: %s', e)

        # 2b.   Collections
        log(LOG_BIGLINE)
        try:
            htmlcollections = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/series/")]/text()')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            htmlcollections.sort()
            log('UPDATE:: %s Collections Found: %s', len(htmlcollections), htmlcollections)
            for collection in htmlcollections:
                if collection.lower() in map(str.lower, FILMDICT['Collection']):  # if set by filename its already in the list - FILMDICT['Collection'] contains a list
                    continue
                metadata.collections.add(collection)
                log('UPDATE:: %s Collection Added: %s', collection)

        except Exception as e:
            log('UPDATE:: Error getting Collections: %s', e)

        # 2c.   Rating = Thumbs Up / (Thumbs Up + Thumbs Down) * 10 - Rating is out of 10
        log(LOG_BIGLINE)
        try:
            thumbsUp = html.xpath('//span[@class="thumbs-up-count"]/text()')[0].strip()
            thumbsUp = (int(thumbsUp) if unicode(thumbsUp, 'utf-8').isnumeric() else 0) * 1.0
            thumbsDown = html.xpath('//span[@class="thumbs-down-count"]/text()')
            thumbsDown = (1 if not thumbsDown else int(thumbsDown[0].strip())) * 1.0  # default thumbs down to 1 to prevent 100% rating
            rating = thumbsUp / (thumbsUp + thumbsDown) * 10
            log('UPDATE:: Film Rating %s', rating)
            metadata.rating = rating

        except Exception as e:
            log('UPDATE:: Error getting Rating: %s', e)

        # 2d.   Directors
        log(LOG_BIGLINE)
        try:
            htmldirectors = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/director/")]/span/text()')
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

        # 2e.   Cast
        log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('//div[@class="name"]/a/text()[normalize-space()]')
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

        # 2f.   Poster / Art
        log(LOG_BIGLINE)
        try:
            image = html.xpath('//div[@class="lg_inside_wrap"]/@data-front')[0]
            log('UPDATE:: Poster Image Found: %s', image)
            #  set poster then only keep it
            metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.posters.validate_keys([image])

            image = html.xpath('//div[@class="lg_inside_wrap"]/@data-back')[0]
            log('UPDATE:: Art Image Found: %s', image)
            #  set Art then only keep it
            metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.art.validate_keys([image])

        except Exception as e:
            log('UPDATE:: Error getting Poster/Art: %s', e)
            try:
                # sometimes no back cover exists... on some old movies/ so use cover photo for both poster/art
                image = html.xpath('//img[@id="cover" and @class="cover"]/@src')[0]
                log('UPDATE:: Old Style Cover Image Found: %s', image)
                #  set poster then only keep it
                metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
                metadata.posters.validate_keys([image])

                #  set Art then only keep it
                metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
                metadata.art.validate_keys([image])
            except Exception as e:
                log('UPDATE:: Error getting Old Style Poster/Art: %s', e)

        # 2g.   Reviews OR Scenes if no reviews
        log(LOG_BIGLINE)
        # reviews
        reviewLink = FILMDICT['SiteURL']
        reviewSource = FILMDICT['Title']
        reviewsList = []
        try:
            htmlreviews = html.xpath('//div[@class="review"]')
            log('UPDATE:: Number of Reviews [%s]', len(htmlreviews))
            for count, review in enumerate(htmlreviews, start=1):
                log('UPDATE:: Review No %s', count)
                try:
                    reviewAuthor =  review.xpath('./span[@class="handle_text"]/text()[normalize-space()]')[0]
                    log('UPDATE:: Review Writer: %s', reviewAuthor)
                except:
                    reviewAuthor = ''

                try:
                    reviewText = review.xpath('./div[@class="review_content"]/span/text()[normalize-space()]')
                    reviewText = ''.join(reviewText)
                    log('UPDATE:: Review Text: %s', reviewText)
                    reviewText = utils.TranslateString(reviewText, SITE_LANGUAGE, lang, DETECT)
                except:
                    reviewText = ''

                if reviewAuthor:
                    reviewsList.append((reviewAuthor, reviewLink, reviewSource, reviewText))

        except Exception as e:
            log('UPDATE:: Error getting Reviews: %s', e)

        # Scene Breakdown - append to reviews
        log(LOG_SUBLINE)
        try:
            htmlheadings = html.xpath('//span[@class="right time"]/text()')
            htmlscenes = html.xpath('//div[@class="scene_details_sm"]')
            log('UPDATE:: %s Scenes Found: %s', len(htmlscenes), htmlscenes)
            for (heading, htmlscene) in zip(htmlheadings, htmlscenes):
                settingsList = htmlscene.xpath('./strong[.="Setting"]/following-sibling::*//.//text()[count(.|./strong[.="Theme"]/preceding-sibling::*//.//text()) = count(//strong[.="Theme"]/preceding-sibling::*//.//text())]')
                if settingsList:
                    log('UPDATE:: %s Setting Found: %s', len(settingsList), settingsList)
                    reviewAuthor = ', '.join(settingsList)
                else:
                    reviewAuthor = heading.strip()

                starsList = htmlscene.xpath('./div[@class="scene_stars_detail"]/span[@class="scene_stars"]/a[contains(@href,"porn-star")]/text()')
                if starsList:
                    log('UPDATE:: %s Stars Found: %s', len(starsList), starsList)
                    for i, star in enumerate(starsList):
                        starsList[i] = star.split('(')[0]
                    reviewSource = ', '.join(starsList)
                else:
                    reviewSource = 'No Cast Recorded'

                actsList = htmlscene.xpath('./div[@class="attributes"]/span[@class="list_attributes"]/a[contains(@href,"scene_attribute")]/text()')
                if actsList:
                    log('UPDATE:: %s Sex Acts Found: %s', len(actsList), actsList)
                    reviewText = ', '.join(actsList)
                else:
                    reviewText = 'No Sex Acts Recorded'

                reviewsList.append((reviewAuthor, reviewLink, reviewSource, reviewText))
        except Exception as e:
            log('UPDATE:: Error getting Scene Breakdown: %s', e)

        # enumerate Reviews or Scenes Garnered 
        metadata.reviews.clear()
        for count, review in enumerate(reviewsList, start=1):
            log('UPDATE:: Review No %s - %s', count, review)
            try:
                newReview = metadata.reviews.new()
                newReview.author, newReview.link, newReview.source, newReview.text = review
                if len(newReview.text) > 275:
                    for i in range(275, -1, -1):
                        if newReview.text[i] in ['.', '!', '?']:
                            newReview.text = newReview.text[0:i + 1]
                            break
                log(LOG_SUBLINE)
            except Exception as e:
                log('UPDATE:: Error getting Review No. %s: %s', count, e)

        # 2h.   Summary = IAFD Legend + Synopsis
        log(LOG_BIGLINE)
        # synopsis
        try:
            synopsis = html.xpath('//span[contains(@class,"video_description")]//text()')
            log('UPDATE:: Synopsis Found: %s', synopsis)
            synopsis = ' '.join(synopsis).replace('\n', ' ')
            synopsis = re.sub('<[^<]+?>', '', synopsis).strip()

            regex = r'The movie you are enjoying was created by consenting adults.*'
            pattern = re.compile(regex, re.DOTALL | re.IGNORECASE)
            synopsis = re.sub(pattern, '', synopsis)
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