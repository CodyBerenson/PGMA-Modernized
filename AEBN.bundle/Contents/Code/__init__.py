# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# AEBN - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    21 May 2020   2020.05.21.01    Creation: using current aebn website - added scene breakdown to summary
    01 Jun 2020   2020.05.21.02    Implemented translation of summary
                                   improved getIAFDActor search

-----------------------------------------------------------------------------------------------------------------------------------
'''
import datetime, linecache, platform, os, re, string, sys, urllib
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2020.05.21.02'
PLUGIN_LOG_TITLE = 'AEBN'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
REGEX = Prefs['regex']

# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# The summary of the film title will be translated into this language
LANGUAGE = Prefs['language']

# detect the language the summary appears in on the web page
DETECT = Prefs['detect']

# URLS
BASE_URL = 'https://gay.aebn.com'
BASE_SEARCH_URL = BASE_URL + '/gay/search/movies/page/1?sysQuery={0}&criteria=%7B%22sort%22%3A%22Relevance%22%7D'

# Date Formats used by website
DATE_YMD = '%Y%m%d'
DATEFORMAT = '%b %d, %Y'

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
class AEBN(Agent.Movies):
    ''' define Agent class '''
    name = 'AEBN (IAFD)'
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
            raise Exception("File Name [{0}] not in the expected format: (Studio) - Title (Year)".format(file))

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchStudioName(self, fileStudioName, siteStudioName):
        ''' match file studio name against website studio name: Boolean Return '''
        siteStudioName = self.NormaliseComparisonString(siteStudioName)

        # remove spaces in comparison variables and check for equality
        noSpaces_siteStudioName = siteStudioName.replace(' ', '')
        noSpaces_fileStudioName = fileStudioName.replace(' ', '')

        if siteStudioName == fileStudioName:
            self.log('SELF:: Studio: Full Word Match: Site: {0} = File: {1}'.format(siteStudioName, fileStudioName))
        elif noSpaces_siteStudioName == noSpaces_fileStudioName:
            self.log('SELF:: Studio: Full Word Match: Site: {0} = File: {1}'.format(siteStudioName, fileStudioName))
        elif siteStudioName in fileStudioName:
            self.log('SELF:: Studio: Part Word Match: Site: {0} IN File: {1}'.format(siteStudioName, fileStudioName))
        elif fileStudioName in siteStudioName:
            self.log('SELF:: Studio: Part Word Match: File: {0} IN Site: {1}'.format(fileStudioName, siteStudioName))
        else:
            raise Exception('Match Failure: Site: {0}'.format(siteStudioName))

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
        ''' Normalise string for Comparison, strip all non alphanumeric characters, Vol., Volume, Part, and 1 in series '''
        # convert to lower case and trim
        myString = myString.strip().lower()

        # remove vol/volume/part and vol.1 etc wording as filenames dont have these to maintain a uniform search across all websites and remove all non alphanumeric characters
        myString = myString.replace('&', 'and').replace(' vol. ', '').replace(' volume ', '')

        # remove all standalone "1's"
        regex = re.compile(r'(?<!\d)1(?!\d)')
        myString = regex.sub('', myString)

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Video title for search query '''
        self.log('SELF:: Original Search Query [{0}]'.format(myString))

        # convert to lower case and trim and strip diacritics, fullstops, enquote
        myString = myString.replace('.', '')
        myString = myString.lower().strip()
        myString = String.StripDiacritics(myString)

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        myNormalString = String.URLEncode(myString).replace('%25', '%').replace('*', '')
        myQuotedString = String.URLEncode('"{0}"'.format(myString)).replace('%25', '%').replace('*', '')
        myString = [myNormalString, myQuotedString]
        self.log('SELF:: Returned Search Query [{0}]'.format(myString))

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def TranslateString(self, myString):
        ''' Determine if translation should be done '''
        myString = myString.strip()
        if myString:
            translator = Translator()
            runTranslation = (LANGUAGE != 'en')
            self.log('SELF:: Default Language: [%s], Run Translation: [%s]', LANGUAGE, runTranslation)
            if DETECT:
                detected = translator.detect(myString)
                runTranslation = (LANGUAGE != detected.lang)
                self.log('SELF:: Detect source Language: [%s] Run Translation: [%s]', detected.lang, runTranslation)
            myString = translator.translate(myString, dest=LANGUAGE).text if runTranslation else myString
            self.log('SELF:: Translated [%s] Summary Found: %s', runTranslation, myString)

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
                self.log('SELF:: Search %s Result: Could not retrieve IAFD Actor Page, %s', count, e)
                continue

        return photourl

    # -------------------------------------------------------------------------------------------------------------------------------
    def log(self, message, *args):
        ''' log messages '''
        Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])

        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version         : v.%s', VERSION_NO)
        self.log('SEARCH:: Python          : %s', sys.version_info)
        self.log('SEARCH:: Platform        : %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Prefs->delay    : %s', DELAY)
        self.log('SEARCH::      ->detect   : %s', DETECT)
        self.log('SEARCH::      ->language : %s', LANGUAGE)
        self.log('SEARCH::      ->regex    : %s', REGEX)
        self.log('SEARCH:: media.title     : %s', media.title)
        self.log('SEARCH:: File Name       : %s', filename)
        self.log('SEARCH:: File Folder     : %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check filename format
        try:
            FilmStudio, FilmTitle, FilmYear = self.matchFilename(filename)
            self.log('SEARCH:: Processing: Studio: %s   Title: %s   Year: %s', FilmStudio, FilmTitle, FilmYear)
        except Exception as e:
            self.log('SEARCH:: Skipping %s', e)
            return

        # Compare Variables used to check against the studio name on website: remove all umlauts, accents and ligatures
        compareStudio = self.NormaliseComparisonString(FilmStudio)
        compareTitle = self.NormaliseComparisonString(FilmTitle)
        compareReleaseDate = datetime.datetime(int(FilmYear), 12, 31)  # default to 31 Dec of Filename year

        # Search Query - for use to search the internet
        searchTitleList = self.CleanSearchString(FilmTitle)
        for count, searchTitle in enumerate(searchTitleList, start=1):
            searchQuery = BASE_SEARCH_URL.format(searchTitle)
            self.log('SEARCH:: %s. Search Query: %s', count, searchQuery)

            morePages = True
            while morePages:
                self.log('SEARCH:: Search Query: %s', searchQuery)
                try:
                    html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
                    # Finds the entire media enclosure
                    titleList = html.xpath('//div[@class="dts-image-overlay-container"]')
                    if not titleList:
                        break   # out of WHILE loop to the FOR loop
                except Exception as e:
                    self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                    return

                try:
                    searchQuery = html.xpath('//ul[@class="dts-pagination"]/li[@class="active" and text()!="..."]/following::li/a[@class="dts-paginator-tagging"]/@href')[0]
                    searchQuery = (BASE_URL if BASE_URL not in searchQuery else '') + searchQuery
                    self.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                    pageNumber = int(html.xpath('//ul[@class="dts-pagination"]/li[@class="active" and text()!="..."]/text()')[0])
                    morePages = True if pageNumber <= 10 else False
                except:
                    searchQuery = ''
                    self.log('SEARCH:: No More Pages Found')
                    pageNumber = 1
                    morePages = False

                self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
                for title in titleList:
                    # Site Title
                    try:
                        siteTitle = title.xpath('./a//img/@title')[0]
                        siteTitle = self.NormaliseComparisonString(siteTitle)
                        self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
                        if siteTitle != compareTitle:
                            continue
                    except:
                        self.log('SEARCH:: Error getting Site Title')
                        continue

                    # Site Title URL
                    try:
                        siteURL = title.xpath('./a/@href')[0]
                        siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                        self.log('SEARCH:: Site Title url: %s', siteURL)
                    except:
                        self.log('SEARCH:: Error getting Site Title Url')
                        continue

                    # Access Site URL for Studio and Release Date information
                    try:
                        html = HTML.ElementFromURL(siteURL, sleep=DELAY)
                    except Exception as e:
                        self.log('SEARCH:: Error reading Site URL page: %s', e)
                        continue

                    # Site Studio
                    try:
                        foundStudio = False
                        htmlSiteStudio = html.xpath('//div[@class="dts-studio-name-wrapper"]/a/text()')
                        self.log('SEARCH:: %s Site URL Studios: %s', len(htmlSiteStudio), htmlSiteStudio)
                        for siteStudio in htmlSiteStudio:
                            try:
                                self.matchStudioName(compareStudio, siteStudio)
                                self.log('SEARCH:: %s Compare with: %s', compareStudio, siteStudio)
                                foundStudio = True
                            except Exception as e:
                                self.log('SEARCH:: Error: %s', e)
                                continue

                            if foundStudio:
                                break
                    except Exception as e:
                        self.log('SEARCH:: Error getting Site Studio %s', e)
                        continue

                    if not foundStudio:
                        self.log('SEARCH:: Error No Matching Site Studio')
                        continue

                    # Site Release Date
                    try:
                        siteReleaseDate = html.xpath('//li[@class="section-detail-list-item-release-date"]/text()')[0].strip().lower()
                        siteReleaseDate = siteReleaseDate.replace('sept ', 'sep ').replace('july ', 'jul ')
                        self.log('SEARCH:: Site URL Release Date: %s', siteReleaseDate)
                        try:
                            siteReleaseDate = self.matchReleaseDate(compareReleaseDate, siteReleaseDate)
                        except Exception as e:
                            self.log('SEARCH:: Exception Site URL Release Date: %s', e)
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
            self.log('UPDATE:: Skipping %s', e)
            return

        # Fetch HTML.
        html = HTML.ElementFromURL(metadata.id, sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as is used to find it on website
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Tag line             : Corresponds to the url of movie
        #        d. Originally Available : set from metadata.id (search result)
        #        e. Content Rating       : Always X
        #    2.  Metadata retrieved from website
        #        a. Summary              : Synopsis + Scene Breakdowns
        #        b. Directors            : List of Drectors (alphabetic order)
        #        c. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        d. Genres
        #        e. Collections
        #        f. Posters/Background

        # 1a.   Studio - straight of the file name
        metadata.studio = FilmStudio
        self.log('UPDATE:: Studio: %s' % metadata.studio)

        # 1b.   Set Title
        metadata.title = FilmTitle
        self.log('UPDATE:: Video Title: %s' % metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = metadata.id.split('|')[0]
        metadata.originally_available_at = datetime.datetime.strptime(metadata.id.split('|')[1], DATE_YMD)
        metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Tagline: %s', metadata.tagline)
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)

        # 1e.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 2a.   Summary = Synopsis + Scene Information
        try:
            synopsis = html.xpath('//div[@class="dts-section-page-detail-description-body"]/text()')[0].strip()
            self.log('UPDATE:: Synopsis Found: %s', synopsis)
        except Exception as e:
            synopsis = ''
            self.log('UPDATE:: Error getting Synopsis: %s', e)

        # scene information
        try:
            htmlheadings = html.xpath('//header[@class="dts-panel-header"]/div/h1[contains(text(),"Scene")]/text()')
            htmlscenes = html.xpath('//div[@class="dts-scene-info dts-list-attributes"]')
            self.log('UPDATE:: %s Scenes Found: %s', len(htmlscenes), htmlscenes)
            allscenes = ''
            for (heading, htmlscene) in zip(htmlheadings, htmlscenes):
                settingsList = htmlscene.xpath('./ul/li[descendant::span[text()="Settings:"]]/a/text()')
                if settingsList:
                    self.log('UPDATE:: %s Setting Found: %s', len(settingsList), settingsList)
                    settings = ', '.join(settingsList)
                    scene = ('\n[ {0} ] . . . . Setting: {1}').format(heading.strip(), settings)
                else:
                    scene = '\n[ {0} ]'.format(heading.strip())
                starsList = htmlscene.xpath('./ul/li[descendant::span[text()="Stars:"]]/a/text()')
                if starsList:
                    starsList = [x.split('(')[0] for x in starsList]
                    self.log('UPDATE:: %s Stars Found: %s', len(starsList), starsList)
                    stars = ', '.join(starsList)
                    scene += '. . . . Stars: {0}'.format(stars)

                actsList = htmlscene.xpath('./ul/li[descendant::span[text()="Sex acts:"]]/a/text()')
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
        metadata.summary = self.TranslateString(summary)

        # 2b.   Directors
        try:
            directors = []
            htmldirector = html.xpath('//li[@class="section-detail-list-item-director"]/span/a/span/text()')
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
                Director.name = direcor
        except Exception as e:
            self.log('UPDATE:: Error getting Director(s): %s', e)

        # 2c.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list and have more actor photos than AEBN
        try:
            castdict = {}
            htmlcast = html.xpath('//a[contains(@href,"/gay/stars/")]/@title')
            self.log('UPDATE:: Cast List %s', htmlcast)
            for castname in htmlcast:
                cast = castname.strip()
                if not cast:
                    continue
                if '(' in cast:
                    cast = cast.split('(')[0]
                castdict[cast] = self.getIAFDActorImage(cast, FilmYear)
                castdict[cast] = '' if castdict[cast] == 'nophoto' else castdict[cast]

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted(castdict):
                role = metadata.roles.new()
                role.name = key
                role.photo = castdict[key]
        except Exception as e:
            self.log('UPDATE - Error getting Cast: %s', e)

        # 2d.   Genres
        try:
            ignoreGenres = ['feature', 'exclusive']
            genres = []
            htmlgenres = html.xpath('//span[@class="dts-image-display-name"]/text()')
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                genre = genre.strip()
                if not genre:
                    continue
                if anyOf(x in genre.lower() for x in ignoreGenres):
                    continue
                genres.append(genre)

            genres.sort()
            metadata.genres.clear()
            for genre in genres:
                metadata.genres.add(genre)
        except Exception as e:
            self.log('UPDATE:: Error getting Genres: %s', e)

        # 2e.   Collections
        try:
            metadata.collections.clear()
            htmlcollections = html.xpath('//li[@class="section-detail-list-item-series"]/span/a/span/text()')
            self.log('UPDATE:: %s Collections Found: %s', len(htmlcollections), htmlcollections)
            for collection in htmlcollections:
                collection = collection.strip()
                if collection:
                    metadata.collections.add(collection)
        except Exception as e:
            self.log('UPDATE:: Error getting Collections: %s', e)

        # 2f.   Posters/Background Art - Front Cover set to poster, Back Cover to background art
        # In this list we are going to save the posters that we want to keep
        try:
            htmlimages = html.xpath('//a[@class="dts-movie-boxcover"]//img/@src')
            self.log('UPDATE:: %s Poster/Background Art Found: %s', len(htmlimages), htmlimages)

            validPosterList = []
            image = htmlimages[0].split('?')[0]
            image = ('http:' if 'http:' not in image else '') + image
            self.log('UPDATE:: Movie Poster Found: %s', image)
            validPosterList.append(image)
            if image not in metadata.posters:
                metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

            validArtList = []
            image = htmlimages[1].split('?')[0]
            image = ('http:' if 'http:' not in image else '') + image
            self.log('UPDATE:: Movie Background Art Found: %s', image)
            validArtList.append(image)
            if image not in metadata.art:
                metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            #  clean up and only keep the Art we have added
            metadata.art.validate_keys(validArtList)
        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Background Art: %s', e)
