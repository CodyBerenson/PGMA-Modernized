# WayBig (IAFD)
'''
                                    Version History
                                    ---------------
    Date            Version             Modification
    22 Dec 2019     2019.12.22.1        Corrected scrapping of collections
    14 Apr 2020     2019.08.12.14       Corrected xPath to properly identify titles in result list
                                        Dropped first word of title with invalid characters i.e "'"
                                        Improved title matching and logging around it
                                        Search multiple result pages
    17 Apr 2020     2019.08.12.15       Removed disable debug logging preference
                                        corrected logic around image cropping

---------------------------------------------------------------------------------------------------------------
'''
import datetime, linecache, platform, os, re, string, sys, urllib, subprocess

# Version / Log Title 
VERSION_NO = '2019.12.22.15'
PLUGIN_LOG_TITLE = 'WayBig'

# PLEX API
load_file = Core.storage.load

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
# if title on website has a hyphen in its title that does not correspond to a colon replace it with an em dash in the corresponding position
FILEPATTERN = Prefs['regex']

# Seconds to pause after a network request was made, ensuring undue burden is not placed on the web server
DELAY = int(Prefs['delay'])

# online image cropper
THUMBOR = Prefs['thumbor'] + "/0x0:{0}x{1}/{2}"

# backup VBScript image cropper
CROPPER = r'CScript.exe "{0}/Plex Media Server/Plug-ins/WayBig.bundle/Contents/Code/ImageCropper.vbs" "{1}" "{2}" "{3}" "{4}"'

# URLS
BASE_URL = 'https://www.waybig.com'
BASE_SEARCH_URL = BASE_URL + '/blog/index.php?s={0}'

def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

def ValidatePrefs():
    pass

class WayBig(Agent.Movies):
    name = 'WayBig (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultScenes']

    def matchedFileName(self, file):
        # match file name to regex
        pattern = re.compile(FILEPATTERN)
        return pattern.search(file)

    def getFileNameGroups(self, file):
        # return groups from FileName regex match
        pattern = re.compile(FILEPATTERN)
        matched = pattern.search(file)
        if matched:
            groups = matched.groupdict()
            return groups['studio'], groups['title'], groups['year']

    # Normalise string for Comparison, strip all non alphanumeric characters, Vol., Volume, Part, and 1 in series
    def NormaliseComparisonString(self, myString):
        # convert to lower case and trim
        myString = myString.strip().lower()

        # convert sort order version to normal version i.e "Best of Zak Spears, The -> the Best of Zak Spears"
        if myString.count(', the'):
            myString = 'the ' + myString.replace(', the', '', 1)
        if myString.count(', An'):
            myString = 'an ' + myString.replace(', an', '', 1)
        if myString.count(', a'):
            myString = 'a ' + myString.replace(', a', '', 1)

        # remove vol/volume/part and vol.1 etc wording as FileNames dont have these to maintain a uniform search across all websites and remove all non alphanumeric characters
        myString = myString.replace('&', 'and').replace(' 1', '').replace(' vol.', '').replace(' volume', '').replace(' part ','')

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

    # clean search string before searching on WayBig
    def PrepareSearchQueryString(self, myString):
        myString = myString.lower().strip()

        # if string has an invalid character in it process
        invalidCharacters = ["'", "‘", "’", '"', "“", "”", "&"]
        inString = True
        while inString:
            inString = bool([Char for Char in invalidCharacters if(Char in myString)])
            if inString:
                # if first word has an invalid character that stops a search drop it
                myWords = myString.split()
                inWord = bool([Char for Char in invalidCharacters if(Char in myWords[0])])
                if inWord:
                    self.log('SELF:: Dropping  first word [%s] from search query. Found one of these %s', myWords[0], invalidCharacters)
                    myWords.remove(myWords[0])
                    myString = ' '.join(myWords)
                inString = False

        # Split at first incident of any invalid character that now should not be in the first word
        for Char in invalidCharacters:
            if Char in myString:
                myString = myString.split(Char)[0]
                self.log('SELF:: "{0}" found - Amended Search Query "{1}"'.format(Char, myString))

        # for titles with colons in them: always replace ":" with " - " in filenames
        if " - " in myString:
            myString = myString.replace(' - ',': ')
            self.log('SELF:: Hyphen found - Amended Search Query "%s"', myString)

        # Search Query - for use to search the internet
        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString)
        # reverse url encoding on the folowing characters (, ), &, :, ! and ,
        myString = myString.replace('%2528','(').replace('%2529',')').replace('%40','&').replace('%3A',':').replace('%2C',',').replace('%21','!')
        myString = myString[:50].strip()
        return myString

    # check IAFD web site for better quality Actor thumbnails irrespective of whether we have a thumbnail or not
    def getIAFDActorImage(self, Actor):
        IAFD_Actor_URL = 'http://www.iafd.com/person.rme/perfid=FULLNAME/gender=SEX/FULL_NAME.htm'
        photourl = None
        Actor = Actor.lower()
        fullname = Actor.replace(' ','').replace("'", '').replace(".", '')
        full_name = Actor.replace(' ','-').replace("'", '&apos;')

        # Actors are categorised on iafd as male or director in order of likelihood
        for gender in ['m', 'd']:
            iafd_url = IAFD_Actor_URL.replace("FULLNAME", fullname).replace("FULL_NAME", full_name).replace("SEX", gender)
            self.log('SELF:: Actor  %s - IAFD url: %s', Actor, iafd_url)
            # Check URL exists and get Actors thumbnail
            try:
                html = HTML.ElementFromURL(iafd_url)
                photourl = html.xpath('//*[@id="headshot"]/img')[0].get('src')
                photourl = photourl.replace('headshots/', 'headshots/thumbs/th_')
                if 'nophoto340.jpg' in photourl:
                    photourl = None
                return photourl
            except: 
                self.log('SELF:: NO IAFD Actor Page')

    def log(self, message, *args):
        Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    def search(self, results, media, lang, manual):
        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version - v.%s', VERSION_NO)
        self.log('SEARCH:: Platform - %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Prefs->delay      - %s', DELAY)
        self.log('SEARCH::      ->regex      - %s', FILEPATTERN)
        self.log('SEARCH::      ->thumbor    - %s', THUMBOR)
        self.log('SEARCH:: media.title - %s', media.title)
        self.log('SEARCH:: media.items[0].parts[0].file - %s', media.items[0].parts[0].file)
        self.log('SEARCH:: media.items - %s', media.items)
        self.log('SEARCH:: media.filename - %s', media.filename)
        self.log('SEARCH:: lang - %s', lang)
        self.log('SEARCH:: manual - %s', manual)
        self.log('-----------------------------------------------------------------------')

        folder, file = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log('SEARCH:: File Name: %s', file)
        self.log('SEARCH:: Enclosing Folder: %s', folder)
 
        # Check FileName format
        if not self.matchedFileName(file):
            self.log('SEARCH:: Skipping %s because the file name is not in the expected format: (Studio) - Title (Year)', file)
            return

        group_studio, group_title, group_year = self.getFileNameGroups(file)
        self.log('SEARCH:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)

        #  Release date default to December 31st of FileName value compare against release date on website
        compareReleaseDate = datetime.datetime(int(group_year), 12, 31)

        # saveTitle corresponds to the real title of the movie.
        saveTitle = group_title
        self.log('SEARCH:: Original Group Title: %s', saveTitle)

        # WayBig displays its movies as Studio: Title or Studio:Title (at Studio) or Title at Studio
        # compareTitle will be used to search against the titles on the website, remove all umlauts, accents and ligatures
        searchType =[]
        searchTitleList = []
        compareTitleList = []

        cleanStudio = group_studio
        cleanTitle = self.PrepareSearchQueryString(group_title)
        compareStudio  = self.NormaliseComparisonString(group_studio)
        compareTitle = self.NormaliseComparisonString(group_title)
        
        searchType.append('BY STUDIO: TITLE')
        compareTitleList.append(compareStudio + ': ' + compareTitle)
        searchTitleList.append(cleanStudio + ': ' + cleanTitle)

        searchType.append('BY TITLE')
        compareTitleList.append(compareTitle)
        searchTitleList.append(cleanTitle)

        searchType.append('BY STUDIO: TITLE at STUDIO')
        compareTitleList.append(compareStudio + ': ' + compareTitle + ' at ' + compareStudio)
        searchTitleList.append(cleanStudio + ': ' + cleanTitle + ' at ' + cleanStudio)

        searchType.append('BY TITLE at STUDIO')
        compareTitleList.append(compareTitle + ' at ' + compareStudio)
        searchTitleList.append(cleanTitle + ' at ' + cleanStudio)

        for searchTitle in searchTitleList:
            index = searchTitleList.index(searchTitle)
            self.log('SEARCH:: [%s. %s]', index + 1, searchType[index])

            # Search Query - for use to search the internet
            searchTitle = self.PrepareSearchQueryString(searchTitle)
            searchQuery = BASE_SEARCH_URL.format(searchTitle)

            compareTitle = compareTitleList[index]

            # Finds the entire media enclosure <Table> element then steps through the rows
            morePages = True
            while morePages:
                self.log('SEARCH:: Search Query: %s', searchQuery)
                try: 
                    html = HTML.ElementFromURL(searchQuery, timeout=90, errors='ignore', sleep=DELAY)
                except:
                    break

                try:
                    searchQuery = html.xpath('//div[@class="nav-links"]/a[@class="next page-numbers"]/@href')[0]
                    pageNumber = html.xpath('//div[@class="nav-links"]/span[@class="page-numbers current"]/text()')[0]
                    morePages = True
                except:
                    pageNumber = "1"
                    morePages = False

                titleList = html.xpath('.//div[@class="row"]/div[@class="content-col col"]/article')
                titlesFound = len(titleList)
                if titlesFound > 0:
                    self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, titlesFound)

                for title in titleList:
                    # some studios are sometimes listed with no spaces.. Next Door Ebony as NextDoorEbony
                    # remove all spaces and studio name and compare and possible added ":"
                    try:
                        siteTitle = title.xpath('./a/h2[@class="entry-title"]/text()')[0].strip()
                        siteTitle = self.NormaliseComparisonString(siteTitle)
                        noSpaceStudio = group_studio.lower().replace(' ', '')
                        siteTitle = siteTitle.replace(' ','').replace(noSpaceStudio,'').replace(':','')
                        compareTitle = compareTitle.replace(' ','').replace(noSpaceStudio,'').replace(':','')
                        self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
                        if siteTitle != compareTitle:
                            continue
                    except:
                        continue

                    try:
                        siteURL = title.xpath('./a[@rel="bookmark"]/@href')[0]
                        self.log('SEARCH:: Site Title URL: %s' % str(siteURL))
                    except:
                        self.log('SEARCH:: Error getting Site Title URL')
                        continue

                    # Site Released Date Check - default to FileName year
                    try:
                        siteReleaseDate = title.xpath('./div/span[@class="meta-date"]/strong/text()')[0].strip()
                        siteReleaseDate = datetime.datetime.strptime(siteReleaseDate, '%B %d, %Y')
                    except:
                        siteReleaseDate = compareReleaseDate
                        self.log('SEARCH:: Error getting Site Release Date')

                    timedelta = siteReleaseDate - compareReleaseDate
                    self.log('SEARCH:: Compare Release Date - %s Site Date - %s : Dx [%s] days"', compareReleaseDate, siteReleaseDate, timedelta.days)
                    if abs(timedelta.days) > 366:
                        self.log('SEARCH:: Difference of more than a year between file date and %s date from Website')
                        continue

                    # we should have a match on both studio and title now
                    results.Append(MetadataSearchResult(id = siteURL + '|' + siteReleaseDate.strftime('%d/%m/%Y'), name = saveTitle, score = 100, lang = lang))

                    # we have found a title that matches quit loop
                    return

    def update(self, metadata, media, lang, force=True):
        folder, file = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log('-----------------------------------------------------------------------')
        self.log('UPDATE:: Version - v.%s', VERSION_NO)
        self.log('UPDATE:: Platform - %s %s', platform.system(), platform.release())
        self.log('UPDATE:: File Name: %s', file)
        self.log('UPDATE:: Enclosing Folder: %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check FileName format
        if not self.matchedFileName(file):
            self.log('UPDATE:: Skipping %s because the file name is not in the expected format: (Studio) - Title (Year)', file)
            return

        group_studio, group_title, group_year = self.getFileNameGroups(file)
        self.log('UPDATE:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)

        # the ID is composed of the webpage for the video and its thumbnail
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
        metadata.studio = group_studio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = group_title
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 1d.   Tagline
        metadata.tagline = metadata.id.split('|')[0]

        # 1e.   Originally Available At
        metadata.originally_available_at = datetime.datetime.strptime(metadata.id.split('|')[1], '%d/%m/%Y')
        metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)

        # 2a.   Summary
        try:
            summary = html.xpath('//div[@class="entry-content"]')[0].text_content().strip()
            self.log('UPDATE:: Summary Found: %s' %str(summary))

            # clean summary text
            summary = re.sub('<[^<]+?>', '', summary)
            regex = '.*}\);'
            pattern = re.compile(regex, re.DOTALL)
            summary = re.sub(pattern, '', summary)
            regex = r'JQuery.*'
            pattern = re.compile(regex, re.DOTALL | re.IGNORECASE)
            summary = re.sub(pattern, '', summary)
            regex = r'Watch .* at .*|{0} at {1}:'.format(group_title, group_studio)
            pattern = re.compile(regex, re.IGNORECASE)
            summary = re.sub(pattern, '', summary)
            regex = r'Related Posts.*'
            pattern = re.compile(regex, re.DOTALL | re.IGNORECASE)
            summary = re.sub(pattern, '', summary)
            metadata.summary = summary.strip()
        except:
            self.log('UPDATE:: Error getting Summary')

        # 2b.   Cast
        try:
            castdict = {}
            htmlcast = html.xpath('//a[contains(@href,"https://www.waybig.com/blog/tag/")]/text()')
            self.log('UPDATE:: Cast List %s', htmlcast)
            for castname in htmlcast:
                cast = castname.replace(u'\u2019s','').strip()
                if '(' in cast:
                    cast = cast.split('(')[0]
                if (len(cast) > 0):
                    castdict[cast] = self.getIAFDActorImage(cast)

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted (castdict): 
                role = metadata.roles.new()
                role.name = key
                role.photo = castdict[key]
        except:
            self.log('UPDATE:: Error getting Cast')

        # 2c.   Posters - Front Cover set to poster
        envVar = os.environ
        TempFolder = envVar['TEMP']
        LocalAppDataFolder = envVar['LOCALAPPDATA']

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
                        if os.name == 'nt':
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
                        if os.name == 'nt':
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