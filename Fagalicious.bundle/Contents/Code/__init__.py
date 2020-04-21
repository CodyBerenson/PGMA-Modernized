# Fagalicious - (IAFD)
'''
                                    Version History
                                    ---------------
    Date            Version             Modification
    22 Dec 2019     2020.01.18.1        Creation
    19 Apr 2020     2020.01.18.9        Corrected image cropping
                                        added new xpath for titles with video image as main image
                                        improved multiple result pages handling
                                        reoved debug print option

---------------------------------------------------------------------------------------------------------------
'''
import datetime, linecache, platform, os, re, string, sys, urllib, subprocess

# Version / Log Title 
VERSION_NO = '2020.01.18.9'
PLUGIN_LOG_TITLE = 'Fagalicious'

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
CROPPER = r'CScript.exe "{0}/Plex Media Server/Plug-ins/Fagalicious.bundle/Contents/Code/ImageCropper.vbs" "{1}" "{2}" "{3}" "{4}"'

# URLS
BASE_URL = 'https://fagalicious.com'
BASE_SEARCH_URL = BASE_URL + '/search/{0}/'

def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'

def ValidatePrefs():
    pass

class Fagalicious(Agent.Movies):
    name = 'Fagalicious (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultScenes']

    def matchedFilename(self, file):
        # match file name to regex
        pattern = re.compile(FILEPATTERN)
        return pattern.search(file)

    def getFilenameGroups(self, file):
        # return groups from filename regex match
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

        # remove vol/volume/part and vol.1 etc wording as filenames dont have these to maintain a uniform search across all websites and remove all non alphanumeric characters
        myString = myString.replace('&', 'and').replace(' vol.', '').replace(' volume', '').replace(' part','')

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

    # clean search string before searching on Fagalicious
    def CleanSearchString(self, myString):
        # for titles with commas, colons in them on disk represented as ' - '
        nullifySearchStrings = [",", " -", " –" ]
        for item in nullifySearchStrings:
            if item in myString:
                myString = myString.replace(item, '')
                self.log('SEARCH:: "%s" found - Amended Search Title "%s"', item, myString)

        # Fagalicious seems to fail to find Titles which have invalid chars in them split at first incident and take first split, just to search but not compare
        # the back tick is added to the list as users who can not include quotes in their filenames can use these to replace them without changing the scrappers code
        badSearchCharacters = ["'", "‘", "’","”", "“", '"', "`", "–"]
        for item in badSearchCharacters:
            if myString[0] == item:
                # if the first character of the title is an invalid character strip it as there will be no search string e.g. "the big red fox" becomes the big red fox"
                myString = myString[1:]

        for item in badSearchCharacters:
            if item in myString:
                myString = myString.split(item)[0].strip()
                self.log('SEARCH:: "%s" found - Amended Search Title "%s"', item, myString)

        # Search Query - for use to search the internet - string can not be longer than 50 characters
        myString = String.StripDiacritics(myString).lower()
        myString = myString[:50].strip()
        return myString

    # check IAFD web site for better quality actor thumbnails irrespective of whether we have a thumbnail or not
    def getIAFDActorImage(self, actor):
        IAFD_ACTOR_URL = 'http://www.iafd.com/person.rme/perfid=FULLNAME/gender=SEX/FULL_NAME.htm'
        photourl = None
        actor = actor.lower()
        fullname = actor.replace(' ','').replace("'", '').replace(".", '')
        full_name = actor.replace(' ','-').replace("'", '&apos;')

        # actors are categorised on iafd as male or director in order of likelihood
        for gender in ['m', 'd']:
            iafd_url = IAFD_ACTOR_URL.replace("FULLNAME", fullname).replace("FULL_NAME", full_name).replace("SEX", gender)
            self.log('SELF:: Actor  %s - IAFD url: %s', actor, iafd_url)
            # Check URL exists and get actors thumbnail
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

        if not media.items[0].parts[0].file:
            return

        folder, file = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log('SEARCH:: File Name: %s', file)
        self.log('SEARCH:: Enclosing Folder: %s', folder)

        # Check filename format
        if not self.matchedFilename(file):
            self.log('SEARCH:: Skipping %s because the file name is not in the expected format: (Studio) - Title (Year)', file)
            return

        group_studio, group_title, group_year = self.getFilenameGroups(file)
        self.log('SEARCH:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)

        # compare Studio - used to check against the studio name on website
        compareStudio = self.NormaliseComparisonString(group_studio)

        #  Release date default to December 31st of Filename value compare against release date on Website
        compareReleaseDate = datetime.datetime(int(group_year), 12, 31)

        # saveTitle corresponds to the real title of the movie.
        saveTitle = group_title
        self.log('SEARCH:: Original Group Title: %s', saveTitle)

        # compareTitle will be used to search against the titles on the website, remove all umlauts, accents and ligatures
        compareTitle = self.NormaliseComparisonString(saveTitle)

        # Search Query - for use to search the internet
        searchTitle = saveTitle
        searchTitle = self.CleanSearchString(searchTitle)
        searchTitle = String.URLEncode(searchTitle)
        
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        morePages = True
        while morePages:
            self.log('SEARCH:: Search Query: %s', searchQuery)
            try: 
                html = HTML.ElementFromURL(searchQuery, timeout=90, errors='ignore', sleep=DELAY)
            except:
                break

            try:
                searchQuery = html.xpath('//div[@class="nav-links"]/a[@class="page-numbers"]/@href')[0]
                pageNumber = html.xpath('//div[@class="nav-links"]/span/text()')[0]
                morePages = True
            except:
                pageNumber = "1"
                morePages = False

            titleList = html.xpath('//h2[@class="entry-title"]')
            titlesFound = len(titleList)
            if titlesFound > 0:
                self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, titlesFound)

            for title in titleList:
                siteEntry = title.find('.//a').text.split(':')
                self.log('SEARCH:: Site Entry: %s"', siteEntry)

                siteTitle = ''
                for i, entry in enumerate(siteEntry):
                    if i == 0:
                        siteStudio = entry
                    else:
                        siteTitle += entry

                self.log('SEARCH:: Site Title: %s"', siteTitle)
                siteTitle = self.NormaliseComparisonString(siteTitle)
                self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
                if siteTitle != compareTitle:
                    continue

                # need to check that the studio name of this title matches to the filename's studio
                self.log('SEARCH:: Site Studio: %s', siteStudio)
                siteStudio = self.NormaliseComparisonString(siteStudio)
                if siteStudio == compareStudio:
                    self.log('SEARCH:: Studio: Full Word Match: Filename: %s = Website: %s', compareStudio, siteStudio)
                elif siteStudio in compareStudio:
                    self.log('SEARCH:: Studio: Part Word Match: Website: %s IN Filename: %s', siteStudio, compareStudio)
                elif compareStudio in siteStudio:
                    self.log('SEARCH:: Studio: Part Word Match: Filename: %s IN Website: %s', compareStudio, siteStudio)
                else:
                    # remove spaces in comparison variables and check for equality
                    noSpaceSiteStudio = siteStudio.replace(' ', '')
                    noSpaceCompareStudio = compareStudio.replace(' ', '')
                    if noSpaceSiteStudio != noSpaceCompareStudio:
                        continue

                siteURL = title.find('.//a').get('href')
                self.log('SEARCH:: Title url: %s', siteURL)

                # Search Website for date - date is in format dd-mm-yyyy
                try:
                    siteReleaseDate = html.xpath('//li[@class="meta-date"]/a/text()')[0].strip()
                    self.log('SEARCH:: Release Date: %s', siteReleaseDate)
                    siteReleaseDate = datetime.datetime.strptime(siteReleaseDate, '%B %d, %Y')
                except:
                    siteReleaseDate = compareReleaseDate
                    self.log('SEARCH:: Error getting Site Release Date')
                    pass

                # there can not be a difference more than 365 days
                timedelta = siteReleaseDate - compareReleaseDate
                self.log('SEARCH:: Compare Release Date - %s Site Date - %s : Dx [%s] days"', compareReleaseDate, siteReleaseDate, timedelta.days)
                if abs(timedelta.days) > 366:
                    self.log('SEARCH:: Difference of more than a year between file date and %s date from Website')
                    continue
                
                # we should have a match on studio, title and year now
                results.Append(MetadataSearchResult(id = siteURL + '|' + siteReleaseDate.strftime('%d/%m/%Y'), name = saveTitle, score = 100, lang = lang))
                return

    def update(self, metadata, media, lang, force=True):
        folder, file = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log('-----------------------------------------------------------------------')
        self.log('UPDATE:: CALLED v.%s', VERSION_NO)
        self.log('UPDATE:: File Name: %s', file)
        self.log('UPDATE:: Enclosing Folder: %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check filename format
        if not self.matchedFilename(file):
            self.log('UPDATE:: Skipping %s because the file name is not in the expected format: (Studio) - Title (Year)', file)
            return

        group_studio, group_title, group_year = self.getFilenameGroups(file)
        self.log('UPDATE:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)

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
        metadata.studio = group_studio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = group_title
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c/d.   Set Tagline/Originally Available from metadata.id
        metadata.tagline = metadata.id.split('|')[0]
        metadata.originally_available_at = datetime.datetime.strptime(metadata.id.split('|')[1], '%d/%m/%Y')
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

            metadata.summary = summary.strip()
        except Exception as e:
            self.log('UPDATE:: Error getting Summary: %s', e)

        # 2b/c.   Cast/Genre
        #       Fagalicious stores the cast and genres as tags, if tag is in title assume its a cast member else its a genre
        #       get thumbnails from IAFD as they are right dimensions for plex cast list
        try:
            castdict = {}
            genres = []
            htmltags = html.xpath('//ul/a[contains(@href, "https://fagalicious.com/tag/")]/text()')
            self.log('UPDATE:: %s Genres/Cast Tags Found: "%s"', len(htmltags), htmltags)
            for tag in htmltags:
                if tag.lower() in group_studio.lower():
                    continue
                tag = tag.split('(')[0].strip()
                cast = self.getIAFDActorImage(tag)
                if cast is None:
                    genres.append(tag)
                else:
                    castdict[tag] = cast
        except Exception as e:
            self.log('UPDATE - Error getting Cast/Genres: %s', e)

        # Process Cast  
        # sort the dictionary and add kv to metadata
        metadata.roles.clear()
        for key in sorted (castdict): 
            role = metadata.roles.new()
            role.name = key
            role.photo = castdict[key]

        # Process Genres
        metadata.genres.clear()
        for genre in genres:
            metadata.genres.add(genre)

        # 2d   Posters - Front Cover set to poster
        envVar = os.environ
        TempFolder = envVar['TEMP']
        LocalAppDataFolder = envVar['LOCALAPPDATA']

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