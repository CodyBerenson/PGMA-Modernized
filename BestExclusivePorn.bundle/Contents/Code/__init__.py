#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# BestExclusivePorn - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    09 Aug 2020   2020.08.09.01    Creation
    07 Sep 2020   2020.08.09.02    Improved matching on film titles with apostrophes
                                   added cast scraping - actors restricted to 2 names
    15 Sep 2020   2020.08.09.03    removed enquotes around search string
    25 Sep 2020   2020.08.09.04    search string can only have a max of 59 characters
    07 Oct 2020   2020.08.09.05    IAFD - change to https
                                   get cast names from statting label if present
    22 Nov 2020   2020.08.09.06    leave words attached to commas in search string
    23 Dec 2020   2020.08.09.07    Save film in Title Case mode... as this agent detects actor names from the title as they have initial caps
    26 Dec 2020   2020.08.09.08    Improved on IAFD search, actors sexual roles if recorded are returned, if not shows a red circle.
                                   if actor is not credited on IAFD but is on Agent Site it shows as a Yellow Box below the actor
                                   sped up search by removing search by actor/director... less hits on IAFD per actor...

-----------------------------------------------------------------------------------------------------------------------------------
'''
import datetime, platform, os, re, sys, unicodedata
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2020.08.09.08'
PLUGIN_LOG_TITLE = 'BestExclusivePorn'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
REGEX = Prefs['regex']

# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# detect the language the summary appears in on the web page
DETECT = Prefs['detect']

# URLS
BASE_URL = 'http://bestexclusiveporn.com/'
BASE_SEARCH_URL = BASE_URL + '?s={0}'

# Date Formats used by website
DATE_YMD = '%Y%m%d'
DATEFORMAT = '%B %d, %Y'

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
class BestExclusivePorn(Agent.Movies):
    ''' define Agent class '''
    name = 'BestExclusivePorn (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms', 'com.plexapp.agents.GayAdultScenes']

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

        # convert to lower case and trim
        myString = myString.lower().strip()

        # remove words with apostrophes in them
        badChars = ["'", ur'\u2018', ur'\u2019', '-']
        pattern = u"\w*[{0}]\w*".format(''.join(badChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            self.log('SELF:: Search Query:: Replacing characters in string. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, '', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            self.log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('SELF:: Search Query:: String has none of these {0}'.format(pattern))

        # Best Exclusive uses a maximum of 60 characters when searching
        myString = myString[:59].strip()
        myString = myString if myString[-1] != '%' else myString[:58]

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())
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
    def getIAFDActorImage(self, myString, FilmYear, compareTitle):
        ''' check IAFD web site for better quality actor thumbnails irrespective of whether we have a thumbnail or not '''

        myString = myString.strip()
        searchActor = myString
        myString = String.StripDiacritics(myString).lower()
        myString = String.URLEncode(myString)
        url = 'https://www.iafd.com/results.asp?searchtype=comprehensive&searchstring={0}'.format(myString)

        FilmYear = int(FilmYear)
        photourl = ''
        role = ''
        try:
            # the IAFD website can be notoriously slow at times, so give it 3 times to search for an actor
            for i in range(2):
                try:
                    html = HTML.ElementFromURL(url, timeout=20, sleep=DELAY)
                    break
                except Exception as e:
                    if i == 2:
                        raise Exception('Failed to Search for Actor [%s]', e)
                    continue

            # return list of actors with the searched name and iterate through them
            self.log('SELF:: Search IAFD for all Actors named as [ %s ]', searchActor)
            xPathString = '//table[@id="tblMal" or @id="tblDir"]/tbody/tr/td[contains(normalize-space(.),"{0}")]/parent::tr'.format(searchActor)
            actorList = html.xpath(xPathString)
            for actor in actorList:
                try:
                    # get actor details 
                    startCareer = int(actor.xpath('./td[4]/text()[normalize-space()]')[0]) - 1   # set start of career to 1 year before for pre-releases
                    endCareer = int(actor.xpath('./td[5]/text()[normalize-space()]')[0]) + 1     # set end of career to 1 year after to cater for late releases
                    if not (startCareer <= FilmYear <= endCareer):
                        continue

                    actorName = actor.xpath('./td[2]/a/text()[normalize-space()]')[0]
                    actorURL = 'https://www.iafd.com' + actor.xpath('./td[2]/a/@href')[0]
                    photourl = actor.xpath('./td[1]/a/img/@src')[0] # actor name on agent website - retrieve picture
                    photourl = 'nophoto' if photourl == 'https://www.iafd.com/graphics/headshots/thumbs/th_iafd_ad.gif' else photourl
                    role = u'\U0001F7E8' # default: yellow square - actor not credited on IAFD
                    self.log('SELF:: Actor: %s active from [%s to %s] --- URL %s', actorName, startCareer, endCareer, actorURL)
                    try:
                        actorHtml = HTML.ElementFromURL(actorURL, sleep=DELAY)
                        htmlFilms = actorHtml.xpath('//a[@href[contains(.,"/year={0}")]]/ancestor::tr'.format(FilmYear))
                        for filmrow in htmlFilms:
                            film = filmrow.xpath('./td[1]/a/text()')[0].strip()
                            compareFilm = self.NormaliseComparisonString(film)
                            if compareFilm == compareTitle:
                                role = filmrow.xpath('./td[4]/i/text()')[0].strip()
                                role = u'\U0001F534' if not role else role # missing role on IAFD
                                self.log('SELF:: Film found [ %s (%s) ] Role: [ %s ] Photo: [ %s ]', film, FilmYear, role, photourl)
                                break
                    except Exception as e:
                        self.log('SELF:: Error reading Actor URL page: %s', e)
                        continue
                except:
                    continue
                break   # found an actor - break out of loop
        except Exception as e:
            role = ''
            photourl = ''
            self.log('SELF:: Error: IAFD Actor Search Failure, %s', e)
        
        return [photourl, role]

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

        # Search Query - for use to search the internet, remove all non alphabetic characters as returns no results if apostrophes exist etc..
        searchTitle = self.CleanSearchString(FilmTitle)
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        morePages = True
        while morePages:
            self.log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
                # Finds the entire media enclosure
                titleList = html.xpath('//div[contains(@class,"type-post status-publish")]')
                if not titleList:
                    break
            except Exception as e:
                self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                return

            try:
                searchQuery = html.xpath('//a[@class="next page-numbers"]/@href')[0]
                self.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(searchQuery.split('?')[0].split('/')[-1]) - 1
                morePages = True if pageNumber <= 10 else False
            except:
                searchQuery = ''
                self.log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
            for title in titleList:
                # Site Entry
                try:
                    siteEntry = title.xpath('./h2[@class="title"]/a/text()')[0]
                    self.log('SEARCH:: Site Entry: %s', siteEntry)

                    # normalise site entry and film title
                    siteEntry = self.NormaliseComparisonString(siteEntry)
                    normalisedFilmTitle = self.NormaliseComparisonString(FilmTitle)
                    pattern = ur'{0}'.format(normalisedFilmTitle)
                    matched = re.search(pattern, siteEntry, re.IGNORECASE)  # match against whole string
                    if matched:
                        siteTitle = matched.group()
                        siteStudio = re.sub(pattern, '', siteEntry).strip()
                        # Studio Name
                        try:
                            self.matchStudioName(compareStudio, siteStudio)
                        except Exception as e:
                            self.log('SEARCH:: Error getting Site Studio: %s', e)
                            continue
                    else:
                        continue
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Entry: %s', e)
                    continue

                # Site Title
                try:
                    siteTitle = self.NormaliseComparisonString(siteTitle)
                    self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
                    if siteTitle != compareTitle:
                        continue
                except:
                    self.log('SEARCH:: Error getting Site Title')
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('./h2[@class="title"]/a/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    self.log('SEARCH:: Site Title url: %s', siteURL)
                except:
                    self.log('SEARCH:: Error getting Site Title Url')
                    continue

                # Site Release Date
                try:
                    siteReleaseDate = title.xpath('./div[@class="post-info-top"]/span[@class="post-info-date"]/a[@rel="bookmark"]/text()')[0].strip()
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
        #        c. Tag line             : Corresponds to the url of movie
        #        d. Originally Available : set from metadata.id (search result)
        #        e. Content Rating       : Always X
        #    2.  Metadata retrieved from website
        #        a. Summary
        #        b. Directors            : List of Directors (alphabetic order)
        #        c. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        d. Genres               : List of Genres (alphabetic order)
        #        e. Posters/Background

        # 1a.   Studio - straight of the file name
        metadata.studio = FilmStudio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = " ".join(word.capitalize() for word in FilmTitle.split())
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

        # 2a.   Summary
        try:
            summary = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Description: ")]')[0].strip().replace('Description: ', '')
            self.log('UPDATE:: Summary Found: %s', summary)
            metadata.summary = self.TranslateString(summary, lang)
        except Exception as e:
            self.log('UPDATE:: Error getting summary: %s', e)

        # 2b.   Countries
        try:
            countries = []
            htmlcountries = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Country: ")]')[0].strip().replace('Country: ', '').split(',')
            self.log('UPDATE:: Countries List %s', htmlcountries)
            for country in htmlcountries:
                country = country.strip()
                if country:
                    countries.append(country)

            countries.sort()
            metadata.countries.clear()
            for country in countries:
                metadata.countries.add(country)
        except Exception as e:
            self.log('UPDATE:: Error getting Country(ies): %s', e)


        # 2c.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        #             If there is a Starring heading use it to get the actors else try searching the title for the cast
        compareTitle = self.NormaliseComparisonString(FilmTitle)
        castdict = {}
        actors = []
        try:
            htmlcast = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Starring: ")]')[0].strip().replace('Starring: ', '').split(',')
            self.log('UPDATE:: %s Cast Found: %s', len(htmlcast), htmlcast)
            for cast in htmlcast:
                castname = cast.strip()
                if castname:
                    actors.append(castname)
        except Exception as e:
            self.log('UPDATE - Error getting Cast: No Starring Entry - Attempt getting cast from title: %s', e)
            pattern = u'([A-Z][a-z]+|\.)(?:\s+([A-Z][a-z]+|\.))'
            matches = re.findall(pattern, FilmTitle)  # match against Film title
            self.log('UPDATE:: Matches:: {0}'.format(matches))
            if matches:
                for count, castname in enumerate(matches, 1):
                    castname = [str(i) for i in castname]
                    castname = ' '.join(castname).strip()
                    self.log('UPDATE:: {0}. Found Possible Cast Name:: {1}'.format(count, castname))
                    if castname:
                        actors.append(castname)
        if actors:
            for castname in actors:
                castlist = self.getIAFDActorImage(castname, FilmYear, compareTitle) # composed of picture and role
                castlist[0] = '' if castlist[0] == 'nophoto' else castlist[0]
                castdict[castname] = castlist

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted(castdict):
                cast = metadata.roles.new()
                cast.photo = castdict[key][0]
                cast.role = castdict[key][1]
                cast.name = key
        else:
            self.log('UPDATE - Error getting Cast: No Cast Found')

        # 2d.   Genres
        try:
            genres = []
            htmlgenres = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Genre: ")]')[0].strip().replace('Genre: ', '').split(',')
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                genre = genre.strip()
                if genre:
                    genres.append(genre)

            genres.sort()
            metadata.genres.clear()
            for genre in genres:
                metadata.genres.add(genre)
        except:
            self.log('UPDATE:: Error getting Genres')

        # 2e.   Posters/Background Art
        try:
            htmlimages = html.xpath('//div[@class="entry"]/p//img/@src')  # only need first two images

            validPosterList = []
            image = htmlimages[0]
            self.log('UPDATE:: Movie Poster Found: "%s"', image)
            validPosterList.append(image)
            if image not in metadata.posters:
                metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

            validArtList = []
            image = htmlimages[1]
            self.log('UPDATE:: Movie Background Art Found: "%s"', image)
            validArtList.append(image)
            if image not in metadata.art:
                metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            #  clean up and only keep the Art we have added
            metadata.art.validate_keys(validArtList)
        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Background Art: %s', e)
