#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
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

---------------------------------------------------------------------------------------------------------------
'''
import datetime, linecache, platform, os, re, string, subprocess, sys, unicodedata, urllib, urllib2
from platform import architecture
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2019.08.12.09'
PLUGIN_LOG_TITLE = 'GayDVDEmpire'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
REGEX = Prefs['regex']

# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# detect the language the summary appears in on the web page
DETECT = Prefs['detect']

# URLS
BASE_URL = 'http://www.gaydvdempire.com'
BASE_SEARCH_URL = BASE_URL + '/AllSearch/Search?view=list&?exactMatch={0}&q={0}'
# Date Formats used by website
DATE_YMD = '%Y%m%d'
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
class GayDVDEmpire(Agent.Movies):
    ''' define Agent class '''
    name = 'GayDVDEmpire (IAFD)'
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
        ''' Normalise string for Comparison, strip all non alphanumeric characters, Vol., Volume, Part, and 1 in series '''
        # Check if string has roman numerals as in a series; note the letter I will be converted
        myString = '{0} '.format(myString)  # append space at end of string to match last characters 
        pattern = '\s(?=[MDCLXVI])M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3})\s'
        matches = re.findall(pattern, myString, re.IGNORECASE)  # match against string
        if matches:
            RomanValues = {'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000}
            for count, match in enumerate(matches):
                myRoman = ''.join(match)
                self.log('SELF:: Found Roman Numeral: {0}. {1}'.format(count, myRoman))
                myArabic = RomanValues[myRoman[len(myRoman) - 1]]
                for i in range(len(myRoman) - 1, 0, -1):
                    if RomanValues[myRoman[i]] > RomanValues[myRoman[i - 1]]:
                        myArabic = myArabic - RomanValues[myRoman[i - 1]]
                    else:
                        myArabic = myArabic + RomanValues[myRoman[i - 1]]
                romanString = ' {0}'.format(myRoman)
                arabicString = ' {0}'.format(myArabic)
                myString = myString.replace(romanString, arabicString)

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

        myString = myString.lower().strip()
        myString = myString.replace(' -', ':').replace(ur'\u2013', '-').replace(ur'\u2014', '-')

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
            url = 'https://www.iafd.com/person.rme/perfid={0}/gender={1}/{2}.htm'.format(fullname, gender, full_name)
            urlList.append(url)

        myString = String.URLEncode(myString)
        url = 'https://www.iafd.com/results.asp?searchtype=comprehensive&searchstring={0}'.format(myString)
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
                                photourl = 'nophoto' if photourl == 'https://www.iafd.com/graphics/headshots/thumbs/th_iafd_ad.gif' else photourl
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
        compareReleaseDate = datetime.datetime(int(FilmYear), 12, 31)  # default to 31 Dec of Filename yesr

        # Search Query - for use to search the internet, remove all non alphabetic characters as GayMovie site returns no results if apostrophes or commas exist etc..
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
                searchQuery = html.xpath('.//a[@title="Next"]/@href')[0]
                pageNumber = int(searchQuery.split('page=')[1]) # next page number
                searchQuery = BASE_SEARCH_URL.format(searchTitle) + '&page={0}'.format(pageNumber)
                pageNumber = pageNumber - 1
                self.log('SEARCH:: Search Query: %s', searchQuery)
                morePages = True if pageNumber <= 10 else False
            except:
                pageNumber = 1
                morePages = False

            titleList = html.xpath('.//div[contains(@class,"row list-view-item")]')
            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
            for title in titleList:
                # siteTitle = The text in the 'title' - Gay DVDEmpire - displays its titles in SORT order
                try:
                    siteTitle = title.xpath('./div/h3/a[@category and @label="Title"]/@title')[0]
                    # convert sort order version to normal version i.e "Best of Zak Spears, The -> the Best of Zak Spears"
                    pattern = u', (The|An|A)$'
                    matched = re.search(pattern, siteTitle, re.IGNORECASE)  # match against string
                    if matched:
                        self.log('SEARCH:: Found Determinate: {0}'.format(matched.group()))
                        determinate = matched.group().replace(', ', '')
                        siteTitle = re.sub(pattern, '', siteTitle)
                        siteTitle = '{0} {1}'.format(determinate, siteTitle)
                        self.log('SEARCH:: Re-ordered Site Title: {0}'.format(siteTitle))

                    siteTitle = self.NormaliseComparisonString(siteTitle)
                    self.log('SEARCH:: Title Match: [{0}] Compare Title - Site Title "{1} - {2}"'.format((compareTitle == siteTitle), compareTitle, siteTitle))
                    if siteTitle != compareTitle:
                        continue
                except:
                    continue

                # Studio Name
                try:
                    siteStudio = title.xpath('./div/ul/li/a/small[text()="studio"]/following-sibling::text()')[0].strip()
                    self.matchStudioName(compareStudio, siteStudio)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Studio: %s', e)
                    continue

                # Site Release Date
                # Get the production year if exists - if it does not match to the compareReleaseDate try the release date
                try:
                    siteProductionYear = title.xpath('./div/h3/small[contains(.,"(")]/text()')[0]
                    siteProductionYear = siteProductionYear.replace('(', '').replace(')', '')
                    self.log('SEARCH:: Site Production Year: %s', siteProductionYear)
                    siteReleaseDate = self.matchReleaseDate(compareReleaseDate, siteProductionYear)
                # use the Site Release Date, if this also does not match to comparereleasedate - next
                except Exception as e:
                    self.log('SEARCH:: Error getting Production Year try Release Date: %s', e)
                    try:
                        siteReleaseDate = title.xpath('./div/ul/li/span/small[text()="released"]/following-sibling::text()')[0].strip()
                        self.log('SEARCH:: Site Release Date: %s', siteReleaseDate)
                        siteReleaseDate = self.matchReleaseDate(compareReleaseDate, siteReleaseDate)
                    except Exception as e:
                        self.log('SEARCH:: Error getting Site Release Date: %s', e)
                        continue

                self.log('SEARCH:: My Site Release Date: %s', siteReleaseDate)
                # Site Title URL
                try:
                    siteURL = title.xpath('./div/h3/a[@label="Title"]/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    self.log('SEARCH:: Site Title url: %s', siteURL)
                except:
                    self.log('SEARCH:: Error getting Site Title Url')
                    continue

                # we should have a match on studio, title and year now
                results.Append(MetadataSearchResult(id=siteURL + '|' + siteReleaseDate.strftime(DATEFORMAT), name=FilmTitle, score=100, lang=lang))
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
        html = HTML.ElementFromURL(metadata.id.split('|')[0], sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as above
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Content Rating       : Always X
        #        d. Originally Available : set from metadata.id (search result)
        #
        #    2.  Metadata retrieved from website
        #        a. Tag line             : Corresponds to the url of movie if not found
        #        b. Summary
        #        c. Directors            : List of Drectors (alphabetic order)
        #        d. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        e. Genres
        #        f. Collections
        #        g. Posters/Background

        # 1a.   Studio
        metadata.studio = FilmStudio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = FilmTitle
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 1d.   Originally Available from metadata.id
        metadata.originally_available_at = datetime.datetime.strptime(metadata.id.split('|')[1], DATEFORMAT)
        metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)

        # 2a.   Tagline
        try:
            metadata.tagline = html.xpath('//p[@class="Tagline"]')[0].text_content().strip()
        except:
            metadata.tagline = metadata.id.split('|')[0]
            self.log('UPDATE:: Default Tagline to Video URL: %s', metadata.tagline)

        # 2b.   Summary
        try:
            summary = html.xpath('//div[@class="col-xs-12 text-center p-y-2 bg-lightgrey"]/div/p')[0].text_content().strip()
            summary = re.sub('<[^<]+?>', '', summary)
            self.log('UPDATE:: Summary Found: %s', summary)
            metadata.summary = self.TranslateString(summary, lang)
        except:
            self.log('UPDATE:: Error getting Summary')

        # 2c.   Directors
        try:
            directors = []
            htmldirector = html.xpath('//a[contains(@label, "Director - details")]/text())[normalize-space()]')
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

        # 2d.   Cast
        try:
            castdict = {}
            htmlcast = html.xpath('//a[contains(@class,"PerformerName")]/text()[normalize-space(.)]')
            self.log('UPDATE:: Cast List %s', htmlcast)
            for castname in htmlcast:
                cast = castname.strip()
                if cast:
                    castdict[cast] = self.getIAFDActorImage(cast, FilmYear)

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted(castdict):
                role = metadata.roles.new()
                role.name = key
                role.photo = castdict[key]
        except:
            self.log('UPDATE:: Error getting Cast')

        # 2e.   Genres
        try:
            ignoreGenres = ['Sale', '4K Ultra HD']
            genres = []
            htmlgenres = html.xpath('//ul[@class="list-unstyled m-b-2"]//a[@label="Category"]/text())[normalize-space()]')
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                genre = genre.strip()
                if not genre:
                    continue
                if anyOf(x in genre for x in ignoreGenres):
                    continue
                genres.append(genre)

            genres.sort()
            metadata.genres.clear()
            for genre in genres:
                metadata.genres.add(genre)
        except:
            self.log('UPDATE:: Error getting Genres')

        # 2f.   Collections
        try:
            metadata.collections.clear()
            htmlcollections = html.xpath('//a[contains(@label, "Series")]/text())[normalize-space()]')
            self.log('UPDATE:: %s Collections Found: "%s"', len(htmlcollections), htmlcollections)
            for collection in htmlcollections:
                collection = collection.replace('"', '').replace('Series', '').strip()
                if collection:
                    metadata.collections.add(collection)
        except:
            self.log('UPDATE:: Error getting Collections')

        # 2g.   Poster/Background Art
        try:
            image = html.xpath('//*[@id="front-cover"]/img')[0]
            posterurl = image.get('src')
            self.log('UPDATE:: Movie Thumbnail Found: "%s"', posterurl)
            validPosterList = [posterurl]
            if posterurl not in metadata.posters:
                try:
                    metadata.posters[posterurl] = Proxy.Media(HTTP.Request(posterurl).content, sort_order=1)
                except:
                    self.log('UPDATE:: Error getting Poster')
            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

            arturl = posterurl.replace('h.jpg', 'bh.jpg')
            validArtList = [arturl]
            if arturl not in metadata.art:
                try:
                    metadata.art[arturl] = Proxy.Media(HTTP.Request(arturl).content, sort_order=1)
                except:
                    self.log('UPDATE:: Error getting Background Art')
            #  clean up and only keep the background art we have added
            metadata.art.validate_keys(validArtList)
        except:
            self.log('UPDATE:: Error getting Poster/Background Art:')
