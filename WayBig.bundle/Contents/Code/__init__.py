#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# WayBig (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    22 Dec 2019   2019.12.22.1     Corrected scrapping of collections
    14 Apr 2020   2019.08.12.14    Corrected xPath to properly identify titles in result list
                                   Dropped first word of title with invalid characters i.e "'"
                                   Improved title matching and logging around it
                                   Search multiple result pages
    17 Apr 2020   2019.08.12.15    Removed disable debug logging preference
                                   corrected logic around image cropping
    28 Apr 2020   2019.08.12.16    update IAFD routine
    08 May 2020   2019.08.12.17    Added [ and ] to characters not be be url encoded as titles were not returning results
                                   updated removal of stand alone '1' in comparison routine
    26 May 2020   2019.08.12.18    Corrected error in summary scrape
    01 Jun 2020   2019.08.12.19    Implemented translation of summary
                                   improved getIAFDActor search

---------------------------------------------------------------------------------------------------------------
'''
import datetime, linecache, platform, os, re, string, sys, urllib, subprocess
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2019.12.22.19'
PLUGIN_LOG_TITLE = 'WayBig'

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
CROPPER = r'CScript.exe "{0}/Plex Media Server/Plug-ins/WayBig.bundle/Contents/Code/ImageCropper.vbs" "{1}" "{2}" "{3}" "{4}"'

# URLS
BASE_URL = 'https://www.waybig.com'
BASE_SEARCH_URL = BASE_URL + '/blog/index.php?s={0}'

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
class WayBig(Agent.Movies):
    ''' define Agent class '''
    name = 'WayBig (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultScenes']

    #-------------------------------------------------------------------------------------------------------------------------------
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
        myString = myString.replace('&', 'and').replace(' vol.', '').replace(' volume', '').replace(',', '')

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
        '''  clean search string before searching on WayBig '''
        self.log('SELF:: Original Search Query [{0}]'.format(myString))

        myString = myString.lower().strip()

        # for titles with " - " replace with ":"
        myString = myString.replace(' - ', ': ')

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

        # WayBig seems to fail to find Titles which have invalid chars in them split at first incident and take first split, just to search but not compare
        # the back tick is added to the list as users who can not include quotes in their filenames can use these to replace them without changing the scrappers code
        badChars = ["'", '"', '`', u'\u201c', u'\u201d', u'\u2018', u'\u2019']
        pattern = u'({0})'.format('|'.join(badChars))
        myWords = myString.split()
        matched = re.search(pattern, myWords[0]) # match against first word
        if matched:
            myWords.remove(myWords[0])
            self.log('SELF:: Search Query:: Dropping first word [{0}]. Found one of these {1}'.format(myWords[0], pattern))
            myString = ' '.join(myWords)
            self.log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('SELF:: Search Query:: First word has none of these {0}'.format(pattern))

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
        compareReleaseDate = datetime.datetime(int(FilmYear), 12, 31)

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
                searchQuery = html.xpath('//div[@class="nav-links"]/a[@class="next page-numbers"]/@href')[0]
                self.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(html.xpath('//div[@class="nav-links"]/span[@class="page-numbers current"]/text()[normalize-space()]')[0])
                morePages = True if pageNumber <= 10 else False
            except:
                searchQuery = ''
                self.log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            titleList = html.xpath('.//div[@class="row"]/div[@class="content-col col"]/article')
            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))

            for title in titleList:
                # some studios are sometimes listed with no spaces.. Next Door Ebony as NextDoorEbony
                # remove all spaces and studio name and compare and possible added ":"
                try:
                    siteTitle = title.xpath('./a/h2[@class="entry-title"]/text()')[0].strip()
                    self.log('SEARCH:: Site Title: %s', siteTitle)
                    # clean Site Title
                    regex = r'{0}:|{1}:|at {0}|at {1}'.format(FilmStudio, compareStudio)
                    pattern = re.compile(regex, re.IGNORECASE)
                    siteTitle = re.sub(pattern, '', siteTitle)
                    siteTitle = self.NormaliseComparisonString(siteTitle)
                    self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
                    if siteTitle != compareTitle:
                        continue
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Title: %s', e)
                    continue

                try:
                    siteURL = title.xpath('./a[@rel="bookmark"]/@href')[0]
                    self.log('SEARCH:: Site Title URL: %s', siteURL)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Title URL: %s', e)
                    continue

                # Site Release Date
                try:
                    siteReleaseDate = title.xpath('./div/span[@class="meta-date"]/strong/text()[normalize-space()]')[0]
                    self.log('SEARCH:: Site URL Release Date: %s', siteReleaseDate)
                    try:
                        siteReleaseDate = self.matchReleaseDate(compareReleaseDate, siteReleaseDate)
                    except Exception as e:
                        self.log('SEARCH:: Exception Site URL Release Date: %s', e)
                        continue
                except:
                    self.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                    siteReleaseDate = compareReleaseDate

                # we should have a match on both studio and title now
                results.Append(MetadataSearchResult(id=siteURL + '|' + siteReleaseDate.strftime(DATE_YMD), name=FilmTitle, score=100, lang=lang))

                # we have found a title that matches quit loop
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
        #        a. Studio               : From studio group of FileName - no need to process this as above
        #        b. Title                : From title group of FileName - no need to process this as is used to find it on website
        #        c. Content Rating       : Always X
        #        d. Tag line             : Corresponds to the url of movie, retrieved from metadata.id split
        #        e. Originally Available : retrieved from the url of the movie
        #    2.  Metadata retrieved from website
        #        a. Summary
        #        b. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        c. Poster
        #        d. Background Art

        # 1a.   Studio
        metadata.studio = FilmStudio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = FilmTitle
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = metadata.id.split('|')[0]
        metadata.originally_available_at = datetime.datetime.strptime(metadata.id.split('|')[1], DATE_YMD)
        metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Tagline: %s', metadata.tagline)
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)

        # 2a.   Summary
        try:
            summary = ''
            htmlsummary = html.xpath('//div[@class="entry-content"]/p[not(descendant::script) and not(descendant::a[@target and @rel])]')
            for item in htmlsummary:
                summary = '{0}{1}\n'.format(summary, item.text_content())
            self.log('UPDATE:: Summary Found: %s', summary)
            metadata.summary = self.TranslateString(summary)
        except:
            self.log('UPDATE:: Error getting Summary')

        # 2b.   Cast
        try:
            castdict = {}
            htmlcast = html.xpath('//a[contains(@href,"https://www.waybig.com/blog/tag/")]/text()')
            htmlcast = list(set(htmlcast))
            self.log('UPDATE:: Cast List %s', htmlcast)
            for castname in htmlcast:
                cast = castname.replace(u'\u2019s', '').strip()
                if '(' in cast:
                    cast = cast.split('(')[0]
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

        # 2c.   Posters - Front Cover set to poster
        imageList = html.xpath('//a[@target="_self" or @target="_blank"]/img[(@height or @width) and @alt and contains(@src, "zing.waybig.com/reviews")]')
        index = 0
        try:
            fromWhere = 'ORIGINAL'
            image = imageList[index].get('src')
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
                        testImageContent = self.cropImage(image, height)
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

        # 2d.   Background Art - Next picture set to Background
        #       height attribute not always provided - so crop to ratio as default - if thumbor fails use script
        index = 1
        try:
            fromWhere = 'ORIGINAL'
            image = imageList[index].get('src')
            imageContent = HTTP.Request(image).content

            # default width to 800 as most of them are set to this
            try:
                width = int(imageList[index].get('width'))
            except:
                width = 800
                self.log('UPDATE:: No Width Attribute, default to; "%s"', width)

            # width:height ratio 16:9
            maxHeight = int(width * 0.5625)
            try:
                height = int(imageList[index].get('height'))
            except:
                height = maxHeight
                self.log('UPDATE:: No Height Attribute, default to; "%s"', height)

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
                        testImageContent = self.cropImage(image, height)
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
