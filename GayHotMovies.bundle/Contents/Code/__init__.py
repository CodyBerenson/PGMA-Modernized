#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
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

---------------------------------------------------------------------------------------------------------------
'''
import datetime, linecache, platform, os, re, string, subprocess, sys, unicodedata, urllib, urllib2
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2019.08.12.05'
PLUGIN_LOG_TITLE = 'GayHotMovies'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
REGEX = Prefs['regex']

# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# detect the language the summary appears in on the web page
DETECT = Prefs['detect']

# URLS
BASE_URL = 'https://www.gayhotmovies.com'
BASE_SEARCH_URL = BASE_URL + '/search.php?num_per_page=48&&page_sort=relevance&search_string={0}'

# Date Formats used by website
DATE_YMD = '%Y%m%d'
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
class GayHotMovies(Agent.Movies):
    ''' define Agent class '''
    name = 'GayHotMovies (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchFilename(self, filename):
        ''' return groups from filename regex match else return false '''
        pattern = re.compile(REGEX)
        matched = pattern.search(filename)
        if matched:
            groups = matched.groupdict()
            return groups['studio'], groups['title'], groups['year']
        else:
            raise Exception("File Name [{0}] not in the expected format: (Studio) - Title (Year)".format(filename))

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchStudioName(self, fileStudioName, siteStudioName):
        ''' match file studio name against website studio name: Boolean Return '''
        siteStudioName = self.NormaliseComparisonString(siteStudioName)

        if siteStudioName == fileStudioName:
            self.log('SELF:: Studio: Full Word Match: Site: {0} = File: {1}'.format(siteStudioName, fileStudioName))
        elif siteStudioName in fileStudioName:
            self.log('SELF:: Studio: Part Word Match: Site: {0} IN File: {1}'.format(siteStudioName, fileStudioName))
        elif fileStudioName in siteStudioName:
            self.log('SELF:: Studio: Part Word Match: File: {0} IN Site: {1}'.format(fileStudioName, siteStudioName))
        else:
            raise Exception('Match Failure: File: {0} != Site: {1} '.format(fileStudioName, siteStudioName))

        return True

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchReleaseDate(self, fileDate, siteDate):
        ''' match file year against website release date: return formatted site date if no error or default to formated file date '''
        if len(siteDate) == 4:      # a year has being provided - default to 31st December of that year
            siteDate = siteDate + '1231'
            siteDate = datetime.datetime.strptime(siteDate, DATE_YMD)
        else:
            siteDate = datetime.datetime.strptime(siteDate, DATEFORMAT)

        # there can not be a difference more than 366 days between FileName Date and SiteDate
        dx = abs((fileDate - siteDate).days)
        msg = 'Match{0}: File Date [{1}] - Site Date [{2}] = Dx [{3}] days'.format(' Failure' if dx > 366 else '', fileDate.strftime('%Y %m %d'), siteDate.strftime('%Y %m %d'), dx)
        if dx > 366:
            raise Exception('Release Date: {0}'.format(msg))
        else:
            self.log('SELF:: Release Date: {0}'.format(msg))

        return siteDate

    # -------------------------------------------------------------------------------------------------------------------------------
    def NormaliseComparisonString(self, myString):
        ''' Normalise string for, strip uneeded characters for comparison of web site values to file name regex group values '''
        # convert to lower case and trim
        myString = myString.strip().lower()

        # normalise unicode characters
        myString = unicode(myString)
        myString = unicodedata.normalize('NFD', myString).encode('ascii', 'ignore')

        # replace ampersand with 'and'
        myString = myString.replace('&', 'and')

        # strip domain suffixes, vol., volume from string, standalone "1's"
        pattern = ur'[.](org|com|net|co[.][a-z]{2})|Vol[.]|\bPart\b|\bVolume\b|(?<!\d)1(?!\d)|[^A-Za-z0-9]+'
        myString = re.sub(pattern, '', myString, flags=re.IGNORECASE)

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Video title for search query '''
        self.log('SELF:: Original Search Query [{0}]'.format(myString))

        myString = myString.strip().lower()
        myString = myString.replace(' -', ':').replace(ur'\u2013', '-').replace(ur'\u2014', '-').replace('& ', '')

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString)

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myString = myString.replace('%25', '%').replace('*', '')
        self.log('SELF:: Returned Search Query [{0}]'.format(myString))

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def TranslateString(self, myString, language):
        ''' Translate string into Library language '''
        myString = myString.strip()
        if language == 'xn' or language == 'xx':    # no language or language unknown
            self.log('SELF:: Library Language: [%s], Run Translation: [False]', 'No Language' if language == 'xn' else 'Unknown')
        elif myString:
            translator = Translator(service_urls=['translate.google.com', 'translate.google.ca', 'translate.google.co.uk',
                                                  'translate.google.com.au', 'translate.google.co.za', 'translate.google.br.com',
                                                  'translate.google.pt', 'translate.google.es', 'translate.google.com.mx',
                                                  'translate.google.it', 'translate.google.nl', 'translate.google.be',
                                                  'translate.google.de', 'translate.google.ch', 'translate.google.at',
                                                  'translate.google.ru', 'translate.google.pl', 'translate.google.bg',
                                                  'translate.google.com.eg', 'translate.google.co.il', 'translate.google.co.jp',
                                                  'translate.google.co.kr', 'translate.google.fr', 'translate.google.dk'])
            runTranslation = (language != SITE_LANGUAGE)
            self.log('SELF:: [Library:Site] Language: [%s:%s], Run Translation: [%s]', language, SITE_LANGUAGE, runTranslation)
            if DETECT:
                detectString = re.findall(ur'.*?[.!?]', myString)[:4]   # take first 4 sentences of string to detect language
                detectString = ''.join(detectString)
                self.log('SELF:: Detect Site Language [%s] using this text: %s', DETECT, detectString)
                try:
                    detected = translator.detect(detectString)
                    runTranslation = (language != detected.lang)
                    self.log('SELF:: Detected Language: [%s] Run Translation: [%s]', detected.lang, runTranslation)
                except Exception as e:
                    self.log('SELF:: Error Detecting Text Language: %s', e)

            try:
                myString = translator.translate(myString, dest=language).text if runTranslation else myString
                self.log('SELF:: Translated [%s] Summary Found: %s', runTranslation, myString)
            except Exception as e:
                self.log('SELF:: Error Translating Text: %s', e)

        return myString if myString else ' '     # return single space to initialise metadata summary field

    # -------------------------------------------------------------------------------------------------------------------------------
    def getIAFDActorImage(self, myString, FilmYear):
        ''' check IAFD web site for better quality actor thumbnails irrespective of whether we have a thumbnail or not '''

        actorname = myString
        myString = String.StripDiacritics(myString).lower()

        # build list containing three possible cast links 1. Full Search in case of AKAs 2. as Performer 3. as Director
        # the 2nd and 3rd links will only be used if there is no search result
        urlList = []
        fullname = myString.replace(' ', '').replace("'", '').replace(".", '')
        full_name = myString.replace(' ', '-').replace("'", '&apos;')
        for gender in ['m', 'd']:
            url = 'http://www.iafd.com/person.rme/perfid={0}/gender={1}/{2}.htm'.format(fullname, gender, full_name)
            urlList.append(url)

        myString = String.URLEncode(myString)
        url = 'http://www.iafd.com/results.asp?searchtype=comprehensive&searchstring={0}'.format(myString)
        urlList.append(url)

        for count, url in enumerate(urlList, start=1):
            photourl = ''
            try:
                self.log('SELF:: %s. IAFD Actor search string [ %s ]', count, url)
                html = HTML.ElementFromURL(url)
                if 'gender=' in url:
                    career = html.xpath('//p[.="Years Active"]/following-sibling::p[1]/text()[normalize-space()]')[0]
                    try:
                        startCareer = career.split('-')[0]
                        self.log('SELF:: Actor: %s  Start of Career: [ %s ]', actorname, startCareer)
                        if startCareer <= FilmYear:
                            photourl = html.xpath('//*[@id="headshot"]/img/@src')[0]
                            photourl = 'nophoto' if 'nophoto' in photourl else photourl
                            self.log('SELF:: Search %s Result: IAFD Photo URL [ %s ]', count, photourl)
                            break
                    except:
                        continue
                else:
                    xPathString = '//table[@id="tblMal" or @id="tblDir"]/tbody/tr/td[contains(normalize-space(.),"{0}")]/parent::tr'.format(actorname)
                    actorList = html.xpath(xPathString)
                    for actor in actorList:
                        try:
                            startCareer = actor.xpath('./td[4]/text()[normalize-space()]')[0]
                            self.log('SELF:: Actor: %s  Start of Career: [ %s ]', actorname, startCareer)
                            if startCareer <= FilmYear:
                                photourl = actor.xpath('./td[1]/a/img/@src')[0]
                                photourl = 'nophoto' if photourl == 'http://www.iafd.com/graphics/headshots/thumbs/th_iafd_ad.gif' else photourl
                                self.log('SELF:: Search %s Result: IAFD Photo URL [ %s ]', count, photourl)
                                break
                        except:
                            continue
                    break
            except Exception as e:
                photourl = ''
                self.log('SELF:: Error: Search %s Result: Could not retrieve IAFD Actor Page, %s', count, e)
                continue

        return photourl

    # -------------------------------------------------------------------------------------------------------------------------------
    def log(self, message, *args):
        ''' log messages '''
        if re.search('ERROR', message, re.IGNORECASE):
            Log.Error(PLUGIN_LOG_TITLE + ' - ' + message, *args)
        else:
            Log.Info(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])

        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version               : v.%s', VERSION_NO)
        self.log('SEARCH:: Python                : %s', sys.version_info)
        self.log('SEARCH:: Platform              : %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Prefs-> delay         : %s', DELAY)
        self.log('SEARCH::      -> detect        : %s', DETECT)
        self.log('SEARCH::      -> regex         : %s', REGEX)
        self.log('SEARCH:: Library:Site Language : %s:%s', lang, SITE_LANGUAGE)
        self.log('SEARCH:: Media Title           : %s', media.title)
        self.log('SEARCH:: File Name             : %s', filename)
        self.log('SEARCH:: File Folder           : %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check filename format
        try:
            FilmStudio, FilmTitle, FilmYear = self.matchFilename(filename)
            self.log('SEARCH:: Processing: Studio: %s   Title: %s   Year: %s', FilmStudio, FilmTitle, FilmYear)
        except Exception as e:
            self.log('SEARCH:: Error: %s', e)
            return

        # Compare Variables used to check against the studio name on website: remove all umlauts, accents and ligatures
        compareStudio = self.NormaliseComparisonString(FilmStudio)
        compareTitle = self.NormaliseComparisonString(FilmTitle)
        compareReleaseDate = datetime.datetime(int(FilmYear), 12, 31)  # default to 31 Dec of Filename year

        # Search Query - for use to search the internet
        searchTitle = self.CleanSearchString(FilmTitle)
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        morePages = True
        while morePages:
            self.log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=90, errors='ignore', sleep=DELAY)
            except Exception as e:
                self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
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
            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))

            for title in titleList:
                # Site Title
                try:
                    siteTitle = title.xpath('./div/div/h3[@class="title"]/a/text()')[0].strip()
                    self.log('SEARCH:: Site Title: "%s"', siteTitle)
                    siteTitle = self.NormaliseComparisonString(siteTitle)
                    self.log('SEARCH:: Title Match: [{0}] Compare Title - Site Title "{1} - {2}"'.format((compareTitle == siteTitle), compareTitle, siteTitle))
                    if siteTitle != compareTitle:
                        continue
                except:
                    self.log('SEARCH:: Error getting Site Title')
                    continue

                # Site Title URL, add code to show scene information
                try:
                    siteURL = title.xpath('./div/div/h3[@class="title"]/a/@href')[0].strip()
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL + '?my_scene_info=more'
                    self.log('SEARCH:: Site Title url: %s', siteURL)
                except:
                    self.log('SEARCH:: Error getting Site Title Url')
                    continue

                # Site Studio Name
                try:
                    siteStudio = title.xpath('./div/div/span[@class="studio_left"]/a/text()')[0].strip()
                    self.matchStudioName(compareStudio, siteStudio)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Studio: %s', e)
                    continue

                # Site Release Date
                try:
                    siteReleaseDate = title.xpath('./div/div/div/span[@class="release_year"]/a/text()')[0].strip()
                    siteReleaseDate = siteReleaseDate.replace('sept ', 'sep ').replace('july ', 'jul ')
                    self.log('SEARCH:: Site URL Release Date: %s', siteReleaseDate)
                    try:
                        siteReleaseDate = self.matchReleaseDate(compareReleaseDate, siteReleaseDate)
                    except Exception as e:
                        self.log('SEARCH:: Error getting Site URL Release Date: %s', e)
                        continue
                except:
                    self.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                    siteReleaseDate = compareReleaseDate

                # we should have a match on studio, title and year now
                results.Append(MetadataSearchResult(id=siteURL + '|' + siteReleaseDate.strftime(DATE_YMD), name=FilmTitle, score=100, lang=lang))
                return

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log('-----------------------------------------------------------------------')
        self.log('UPDATE:: Version    : v.%s', VERSION_NO)
        self.log('UPDATE:: File Name  : %s', filename)
        self.log('UPDATE:: File Folder: %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check filename format
        try:
            FilmStudio, FilmTitle, FilmYear = self.matchFilename(filename)
            self.log('UPDATE:: Processing: Studio: %s   Title: %s   Year: %s', FilmStudio, FilmTitle, FilmYear)
        except Exception as e:
            self.log('UPDATE:: Error: %s', e)
            return

        # Fetch HTML.
        html = HTML.ElementFromURL(metadata.id.split('|')[0], timeout=60, errors='ignore', sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as above
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Content Rating       : Always X
        #        d. Tag line             : Corresponds to the url of movie, as Website does not show Tag lines
        #        e. Originally Available : GayHotMovies only displays the Release Year, so use studio year
        #    2.  Metadata retrieved from website
        #        a. Summary
        #        b. Directors            : List of Directors (alphabetic order)
        #        c. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        d. Categories           : Countries, Genres
        #        e. Collections
        #        f. Posters/Background

        # 1a.   Studio - straight of the file name
        metadata.studio = FilmStudio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = FilmTitle
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = metadata.id.split('|')[0]
        metadata.originally_available_at = datetime.datetime.strptime(metadata.id.split('|')[1], DATE_YMD)
        metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Tagline: %s', metadata.tagline)
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)

        # 1e.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 2a.   Summary = Synopsis + Scene Breakdown
        try:
            synopsis = html.xpath('//span[contains(@class,"video_description")]//text()')[0].strip()
            synopsis = re.sub('<[^<]+?>', '', synopsis)
            self.log('UPDATE:: Synopsis Found: %s' % str(synopsis))

            regex = r'The movie you are enjoying was created by consenting adults.*'
            pattern = re.compile(regex, re.DOTALL | re.IGNORECASE)
            synopsis = re.sub(pattern, '', synopsis)
        except:
            synopsis = ''
            self.log('UPDATE:: Error getting Synopsis')

        # Scene Breakdown
        try:
            htmlheadings = html.xpath('//span[@class="right time"]/text()')
            htmlscenes = html.xpath('//div[@class="scene_details_sm"]')
            self.log('UPDATE:: %s Scenes Found: %s', len(htmlscenes), htmlscenes)
            allscenes = ''
            for (heading, htmlscene) in zip(htmlheadings, htmlscenes):
                settingsList = htmlscene.xpath('./strong[.="Setting"]/following-sibling::*//.//text()[count(.|./strong[.="Theme"]/preceding-sibling::*//.//text()) = count(//strong[.="Theme"]/preceding-sibling::*//.//text())]')
                if settingsList:
                    self.log('UPDATE:: %s Setting Found: %s', len(settingsList), settingsList)
                    settings = ', '.join(settingsList)
                    scene = ('\n[ {0} ] . . . . Setting: {1}').format(heading.strip(), settings)
                else:
                    scene = '\n[ {0} ]'.format(heading.strip())
                starsList = htmlscene.xpath('./div[@class="scene_stars_detail"]/span[@class="scene_stars"]/a[contains(@href,"porn-star")]/text()')
                if starsList:
                    self.log('UPDATE:: %s Stars Found: %s', len(starsList), starsList)
                    for i, star in enumerate(starsList):
                        starsList[i] = star.split('(')[0]
                    stars = ', '.join(starsList)
                    scene += '. . . . Stars: {0}'.format(stars)

                actsList = htmlscene.xpath('./div[@class="attributes"]/span[@class="list_attributes"]/a[contains(@href,"scene_attribute")]/text()')
                if actsList:
                    self.log('UPDATE:: %s Sex Acts Found: %s', len(actsList), actsList)
                    acts = ', '.join(actsList)
                    scene += '\nSex Acts: {0}'.format(acts)
                allscenes += scene
        except Exception as e:
            scene = ''
            self.log('UPDATE:: Error getting Scene Breakdown: %s', e)

        allscenes = '\nScene Breakdown:\n{0}'.format(allscenes) if allscenes else ''
        summary = synopsis + allscenes
        metadata.summary = self.TranslateString(summary, lang)

        # 2b.   Directors
        try:
            directors = []
            htmldirector = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/director/")]/span/text()')
            self.log('UPDATE:: Director List %s', htmldirector)
            for director in htmldirector:
                director = director.strip()
                if director:
                    directors.append(director)

            # sort the dictionary and add kv to metadata
            directors.sort()
            metadata.directors.clear()
            for director in directors:
                Director = metadata.directors.new()
                Director.name = director
        except:
            self.log('UPDATE:: Error getting Director(s)')

        # 2c.   Cast
        #   default to using thumbnails from GayHotMovies as they don't seem to use the same actor names as IAFD,
        #   if thumbnail has empty gif go to IAFD
        try:
            castdict = {}
            htmlcast = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/porn-star/") and (@title) and (@rel)]/img')
            self.log('UPDATE:: Cast List %s', htmlcast)
            for castname in htmlcast:
                cast = castname.get('alt').lower().replace('(male)', '').title().split('(')[0]
                image = castname.get('src')
                self.log('UPDATE:: Cast Name - %s [ %s ]', cast, image)
                if cast:
                    castdict[cast] = image if not 'empty_mal.gif' in image else self.getIAFDActorImage(cast, FilmYear)

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted(castdict):
                role = metadata.roles.new()
                role.name = key
                role.photo = castdict[key]
        except:
            self.log('UPDATE:: Error getting Cast')

        # 2d.  Process Categories: Countries, Genres
        try:
            ignoreCategories = ['language', 'gay', 'movies', 'website', 'settings', 'locale', 'plot', 'character']
            countries = []
            genres = []
            metadata.genres.clear()
            htmlcategories = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/category/")]/span/text()')
            self.log('UPDATE:: %s Categories Found: "%s"', len(htmlcategories), htmlcategories)
            for category in htmlcategories:
                if not category:
                    continue
                elif anyOf(x in category.lower() for x in ignoreCategories):
                    continue
                elif 'international' in category.lower():
                    countries.append(category.split('->')[-1])
                else:
                    category = category.replace('Bareback ->', 'Bareback ')
                    genres.append(category.split('->')[-1])

            countries.sort()
            self.log('UPDATE:: %s Countries Found: "%s"', len(countries), countries)
            for country in countries:
                metadata.countries.add(country)

            genres.sort()
            self.log('UPDATE:: %s Genres Found: "%s"', len(genres), genres)
            for genre in genres:
                metadata.genres.add(genre)
        except:
            self.log('UPDATE:: Error getting Categories: Countries and Genres')

        # 2e.   Collections
        try:
            metadata.collections.clear()
            htmlcollections = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/series/")]/text()')
            self.log('UPDATE:: %s Collections Found: "%s"', len(htmlcollections), htmlcollections)
            for collection in htmlcollections:
                collection = collection.strip()
                if collection:
                    metadata.collections.add(collection)
        except:
            self.log('UPDATE:: Error getting Collections')

        # 2f.   Rating = Thumbs Up / (Thumbs Up + Thumbs Down) * 10 - Rating is out of 10
        try:
            thumbsUp = html.xpath('//span[@class="thumbs-up-count"]/text()')[0].strip()
            thumbsUp = (int(thumbsUp) if unicode(thumbsUp, 'utf-8').isnumeric() else 0) * 1.0
            thumbsDown = html.xpath('//span[@class="thumbs-down-count"]/text()')
            thumbsDown = (1 if not thumbsDown else int(thumbsdown[0].strip())) * 1.0  # default thumbs down to 1 to prevent 100% rating
            rating = thumbsUp / (thumbsUp + thumbsDown) * 10
            self.log('UPDATE:: Film Rating %s', rating)
            metadata.rating = rating
        except:
            self.log('UPDATE:: Error getting Rating')

        # 2g.   Poster
        try:
            posterurl = html.xpath('//div[@class="lg_inside_wrap"]/@data-front')[0]
            self.log('UPDATE:: Movie Front Thumbnail Found: "%s"', posterurl)
            validPosterList = [posterurl]
            if posterurl not in metadata.posters:
                try:
                    metadata.posters[posterurl] = Proxy.Media(HTTP.Request(posterurl).content, sort_order=1)
                except:
                    self.log('UPDATE:: Error getting Poster')

            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

            arturl = html.xpath('//div[@class="lg_inside_wrap"]/@data-back')[0]
            self.log('UPDATE:: Movie Backgound Art Thumbnail Found: "%s"', arturl)
            validArtList = [arturl]
            if arturl not in metadata.art:
                try:
                    metadata.art[arturl] = Proxy.Media(HTTP.Request(arturl).content, sort_order=1)
                except:
                    self.log('UPDATE:: Error getting Background Art')

            #  clean up and only keep the background art we have added
            metadata.art.validate_keys(validArtList)
        except:
            #       sometimes no back cover exists... on some old movies
            try:
                self.log('UPDATE:: Movie Cover Picture Found: OLD')
                posterurl = html.xpath('//img[contains(@itemprop,"image") and contains(@id,"cover") and contains(@class,"cover")]')[0]
                posterurl = posterurl.get('src')
                self.log('UPDATE:: Movie Cover Picture Found: "%s"', posterurl)
                validPosterList = [posterurl]
                if posterurl not in metadata.posters:
                    try:
                        metadata.posters[posterurl] = Proxy.Media(HTTP.Request(posterurl).content, sort_order=1)
                    except:
                        self.log('UPDATE:: Error getting Poster')
                #  clean up and only keep the poster we have added
                metadata.posters.validate_keys(validPosterList)
            except:
                self.log('UPDATE:: Error getting Poster/Background Art:')
