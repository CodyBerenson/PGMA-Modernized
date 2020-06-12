#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# Fagalicious - (IAFD)
                                    Version History
                                    ---------------
    Date            Version             Modification
    22 Dec 2019   2020.01.18.1     Creation
    19 Apr 2020   2020.01.18.9     Corrected image cropping
                                   added new xpath for titles with video image as main image
                                   improved multiple result pages handling
                                   removed debug print option
    29 Apr 2020   2020.01.18.10    updated IAFD routine, corrected error in multiple page processing
    01 Jun 2020   2020.01.18.11    Implemented translation of summary
                                   improved getIAFDActor search

---------------------------------------------------------------------------------------------------------------
'''
import datetime, linecache, platform, os, re, string, sys, urllib, subprocess
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2020.01.18.11'
PLUGIN_LOG_TITLE = 'Fagalicious'

# PLEX API
load_file = Core.storage.load

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
REGEX = Prefs['regex']

# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# The summary of the film title will be translated into this language
LANGUAGE = Prefs['language']

# detect the language the summary appears in on the web page
DETECT = Prefs['detect']

# online image cropper
THUMBOR = Prefs['thumbor'] + "/0x0:{0}x{1}/{2}"

# backup VBScript image cropper
CROPPER = r'CScript.exe "{0}/Plex Media Server/Plug-ins/Fagalicious.bundle/Contents/Code/ImageCropper.vbs" "{1}" "{2}" "{3}" "{4}"'

# URLS
BASE_URL = 'https://fagalicious.com'
BASE_SEARCH_URL = BASE_URL + '/search/{0}/'

# Date Formats used by website
DATE_YMD = '%Y%m%d'
DATEFORMAT = '%B %d, %Y'

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
class Fagalicious(Agent.Movies):
    ''' define Agent class '''
    name = 'Fagalicious (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultScenes']

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
        myString = myString.replace('&', 'and').replace(' vol.', '').replace(' volume', '')

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Video title for search query '''
        self.log('SELF:: Original Search Query [{0}]'.format(myString))

        myString = myString.lower().strip()

        # replace curly apostrophes with straight as strip diacritics will remove these
        quoteChars = [u'\u2018', u'\u2019']
        pattern = u'({0})'.format('|'.join(quoteChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            self.log('SELF:: Search Query:: Replacing characters in string. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, "'", myString)
            myString = ' '.join(myString.split())   # remove continous white space
            self.log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('SELF:: Search Query:: String has none of these {0}'.format(pattern))

        nullChars = [',', '–', u'\u2013', u'\u2014'] # for titles with commas, colons in them on disk represented as ' - '
        pattern = u'({0})'.format('|'.join(nullChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            self.log('SELF:: Search Query:: Replacing characters in string. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, '', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            self.log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('SELF:: Search Query:: String has none of these {0}'.format(pattern))

        # Fagalicious seems to fail to find Titles which have invalid chars in them split at first incident and take first split, just to search but not compare
        # the back tick is added to the list as users who can not include quotes in their filenames can use these to replace them without changing the scrappers code
        badChars = ["'",  '"', '`', u'\u201c', u'\u201d', u'\u2018', u'\u2019']
        pattern = u'({0})'.format('|'.join(badChars))
        matched = re.search(pattern, myString[0])  # match against first character
        if matched:
            self.log('SELF:: Search Query:: Dropping first character [{0}]. Found one of these {1}'.format(myString[0], pattern))
            myString = myString[1:]
            self.log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('SELF:: Search Query:: First character has none of these {0}'.format(pattern))

        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            badPos = matched.start()
            self.log('SELF:: Search Query:: Splitting at position [{0}]. Found one of these {1}'.format(badPos, pattern))
            myString = myString[:badPos]
        else:
            self.log('SELF:: Search Query:: Split not attempted. String has none of these {0}'.format(pattern))

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        myString = myString.replace('%25', '%').replace('*', '')

        # string can not be longer than 50 characters
        myString = myString[:50].strip()
        myString = myString if myString[-1] != '%' else myString[:49]
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
        self.log('SEARCH::      ->thumbor  : %s', THUMBOR)
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
        compareReleaseDate = datetime.datetime(int(FilmYear), 12, 31)  # default to 31 Dec of Filename yesr

        # Search Query - for use to search the internet, remove all non alphabetic characters as GayMovie site returns no results if apostrophes or commas exist etc..
        searchTitle = self.CleanSearchString(FilmTitle)
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        morePages = True
        while morePages:
            self.log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
            except Exception as e:
                self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                return

            try:
                searchQuery = html.xpath('//a[@class="next page-numbers"]/@href')[0]
                self.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(html.xpath('//span[@class="page-numbers current"]/text()[normalize-space()]')[0])
                morePages = True if pageNumber <= 10 else False
            except:
                searchQuery = ''
                self.log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            titleList = html.xpath('//header[@class="entry-header"]')
            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))

            for title in titleList:
                # Site Entry : Composed of Studio, then Scene Title separated by a Colon
                try:
                    siteEntry = title.xpath('./h2/a/text()[normalize-space()]')[0]
                    siteEntry = siteEntry.split(":")
                    self.log('SEARCH:: Site Entry: %s', siteEntry)
                except:
                    continue
                
                # Site Title 
                try:
                    siteTitle = ' '.join(siteEntry[1:None])
                    self.log('SEARCH:: Site Title: %s', siteTitle)
                    siteTitle = self.NormaliseComparisonString(siteTitle)
                    self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
                    if siteTitle != compareTitle:
                        continue
                except:
                    continue

                # Studio Name
                try:
                    siteStudio = siteEntry[0]
                    self.matchStudioName(compareStudio, siteStudio)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Studio: %s', e)
                    continue
                
                # Site Title URL
                try:
                    siteURL = title.xpath('./h2/a/@href')[0]
                    self.log('SEARCH:: Title url: %s', siteURL)
                except:
                    self.log('SEARCH:: Error getting Site Title Url')
                    continue

                # Site Release Date
                try:
                    siteReleaseDate = title.xpath('./ul/li[@class="meta-date"]/a/text()[normalize-space()]')[0]
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
        html = HTML.ElementFromURL(metadata.id.split('|')[0], timeout=60, errors='ignore', sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as is used to find it on website
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Tag line             : Corresponds to the url of movie
        #        d. Originally Available : set from metadata.id (search result)
        #        e. Content Rating       : Always X
        #    2.  Metadata retrieved from website
        #        a. Summary
        #        b. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        c. Genres
        #        d. Posters
        #        e. Background

        # 1a.   Studio - straight of the file name
        metadata.studio = FilmStudio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = FilmTitle
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c/d.   Set Tagline/Originally Available from metadata.id
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
            summary = ''
            htmlsummary = html.xpath('//section[@class="entry-content"]/p')
            for item in htmlsummary:
                summary = '{0}{1}\n'.format(summary, item.text_content())
            self.log('UPDATE:: Summary Found: %s', summary)

            regex = r'.*writes:'
            pattern = re.compile(regex, re.IGNORECASE | re.DOTALL)
            summary = re.sub(pattern, '', summary)

            regex = r'– Get the .*|– Download the .*'
            pattern = re.compile(regex, re.IGNORECASE)
            summary = re.sub(pattern, '', summary)

            metadata.summary = self.TranslateString(summary)
        except Exception as e:
            self.log('UPDATE:: Error getting Summary: %s', e)

        # 2b/c.   Cast/Genre
        #       Fagalicious stores the cast and genres as tags, if tag is in title assume its a cast member else its a genre
        #       get thumbnails from IAFD as they are right dimensions for plex cast list
        try:
            castdict = {}
            genresList = ['bareback', 'black studs', 'big dicks', 'hairy', 'daddy', 'hairy', 'interracial', 'muscle hunks', 'uncut', 'jocks', 'latino', 'gaycest', 'group']
            genres = []
            htmltags = html.xpath('//ul/a[contains(@href, "https://fagalicious.com/tag/")]/text()')
            htmltags = list(set(htmltags))
            self.log('UPDATE:: %s Genres/Cast Tags Found: "%s"', len(htmltags), htmltags)
            for tag in htmltags:
                if anyOf(x in tag.lower() for x in genresList):
                    genres.append(tag)
                    continue

                # do not process studio names in tags
                if '.com' in tag.lower():
                    continue
                if tag.lower().replace(' ', '') in FilmStudio.lower().replace(' ', ''):
                    continue

                # process actors, assume a return of no photo is a genre
                tagIsGenre = True
                tag = tag.replace('AKA', '/').replace('(', '').replace(')', '') if 'AKA' in tag else tag
                tagList = [x.strip() for x in tag.split('/')]  # if actor has AKA names, this will return a list with length > 1
                for tag in tagList:
                    cast = self.getIAFDActorImage(tag, FilmYear)
                    if cast:
                        tagIsGenre = False
                        castdict[tagList[0]] = cast   # assign picture to main name
                        break

                if tagIsGenre:
                    genres.append(tag)  # if not cast - then assign to genre
        except Exception as e:
            self.log('UPDATE - Error getting Cast/Genres: %s', e)

        # Process Cast  
        # sort the dictionary and add kv to metadata
        metadata.roles.clear()
        for key in sorted(castdict):
            role = metadata.roles.new()
            role.name = key
            role.photo = castdict[key]

        # Process Genres
        metadata.genres.clear()
        genres.sort()
        for genre in genres:
            metadata.genres.add(genre)

        # 2d   Posters - Front Cover set to poster
        index = 0
        try:
            fromWhere = 'ORIGINAL'
            imageList = html.xpath('//div[@class="mypicsgallery"]/a/img[@src and @data-src]')
            if imageList:
                image = imageList[index].get('data-src')
                if '?' in image:
                    image = image.split('?')[0]
                imageContent = HTTP.Request(image).content

                # default width is 800 as most of them are set to this
                try:
                    width = int(imageList[index].get('width'))
                except:
                    width = 800
                    self.log('UPDATE:: No Width Attribute, default to; "%s"', width)

                # width:height ratio 1:1.5
                maxHeight = int(width * 1.5)
                try:
                    height = int(imageList[index].get('height'))
                except:
                    height = maxHeight
                    self.log('UPDATE:: No Height Attribute, default to; "%s"', height)
            else:
                # no cropping needed as these video images are 800x450
                image = html.xpath('//video/@poster')[0]
                imageContent = HTTP.Request(image).content
                width = 800
                height = 450
                maxHeight = height

            self.log('UPDATE:: Movie Poster Found: w x h; %sx%s address; "%s"', width, height, image)

            # cropping needed
            if height >= maxHeight:
                self.log('UPDATE:: Attempt to Crop as Image height; %s > Maximum Height; %s', height, maxHeight)
                height = maxHeight
                try:
                    testImage = THUMBOR.format(width, height, image)
                    testImageContent = HTTP.Request(testImage).content
                except Exception as e:
                    self.log('UPDATE:: Thumbor Failure: %s', e)
                    try:
                        if os.name == 'nt':
                            envVar = os.environ
                            TempFolder = envVar['TEMP']
                            LocalAppDataFolder = envVar['LOCALAPPDATA']
                            testImage = os.path.join(TempFolder, image.split("/")[-1])
                            cmd = CROPPER.format(LocalAppDataFolder, image, testImage, width, height)
                            self.log('UPDATE:: Command: %s', cmd)
                            subprocess.call(cmd)
                            testImageContent = load_file(testImage)
                    except Exception as e:
                        self.log('UPDATE:: Crop Script Failure: %s', e)
                    else:
                        fromWhere = 'SCRIPT'
                        image = testImage
                        imageContent = testImageContent
                else:
                    fromWhere = 'THUMBOR'
                    image = testImage
                    imageContent = testImageContent

            #  clean up and only keep the poster we have added
            self.log('UPDATE:: %s Image; "%s"', fromWhere, image)
            for key in metadata.posters.keys():
                del metadata.posters[key]
            metadata.posters[image] = Proxy.Media(imageContent)

        except Exception as e:
            self.log('UPDATE:: Error getting Poster: %s', e)

        
        # 2e.   Background Art - Next picture set to Background 
        #       height attribute not always provided - so crop to ratio as default - if thumbor fails use script
        try:
            fromWhere = 'ORIGINAL'
            imageList = html.xpath('//div[@class="mypicsgallery"]/a/img[@src and @data-src]')

            # use second image in list as background
            index = 1

            # if there is no background image in list - try this xpath and use first image as background art
            if not imageList:
                index = 0
                imageList = html.xpath('//figure[@class="gallery-item"]/div/img[@src and @data-src]')

            if imageList:
                image = imageList[index].get('data-src')
                if '?' in image:
                    image = image.split('?')[0]
                imageContent = HTTP.Request(image).content

                # default width is 800 as most of them are set to this
                try:
                    width = int(imageList[index].get('width'))
                except:
                    width = 800
                    self.log('UPDATE:: No Width Attribute, default to; "%s"', width)

                # width:height ratio 1:1.5
                maxHeight = int(width * 1.5)
                try:
                    height = int(imageList[index].get('height'))
                except:
                    height = maxHeight
                    self.log('UPDATE:: No Height Attribute, default to; "%s"', height)
            else:
                # no cropping needed as these video images are 800x450
                image = html.xpath('//video/@poster')[0]
                imageContent = HTTP.Request(image).content
                width = 800
                height = 450
                maxHeight = height

            self.log('UPDATE:: Background Art Found: w x h; %sx%s address; "%s"', width, height, image)

            # cropping needed
            if height >= maxHeight:
                self.log('UPDATE:: Attempt to Crop as Image height; %s > Maximum Height; %s', height, maxHeight)
                height = maxHeight
                try:
                    testImage = THUMBOR.format(width, height, image)
                    testImageContent = HTTP.Request(testImage).content
                except Exception as e:
                    self.log('UPDATE:: Thumbor Failure: %s', e)
                    try:
                        if os.name == 'nt':
                            envVar = os.environ
                            TempFolder = envVar['TEMP']
                            LocalAppDataFolder = envVar['LOCALAPPDATA']
                            testImage = os.path.join(TempFolder, image.split("/")[-1])
                            cmd = CROPPER.format(LocalAppDataFolder, image, testImage, width, height)
                            self.log('UPDATE:: Command: %s', cmd)
                            subprocess.call(cmd)
                            testImageContent = load_file(testImage)
                    except Exception as e:
                        self.log('UPDATE:: Crop Script Failure: %s', e)
                    else:
                        fromWhere = 'SCRIPT'
                        image = testImage
                        imageContent = testImageContent
                else:
                    fromWhere = 'THUMBOR'
                    image = testImage
                    imageContent = testImageContent

            #  clean up and only keep the art we have added
            self.log('UPDATE:: %s Image; "%s"', fromWhere, image)
            for key in metadata.art.keys():
                del metadata.art[key]
            metadata.art[image] = Proxy.Media(imageContent)
        except Exception as e:
            self.log('UPDATE:: Error getting Background Art: %s', e)