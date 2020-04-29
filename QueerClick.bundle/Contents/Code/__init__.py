# QueerClick - (IAFD)
'''
                                    Version History
                                    ---------------
    Date            Version             Modification
    28 Apr 2020     2020.02.14.10       Removed disable debug logging preference
                                        corrected logic around image cropping
                                        improved error handling on title, url retrieval
    29 Apr 2020     2020.02.14.11       update IAFD routine

---------------------------------------------------------------------------------------------------------------
'''
import datetime, linecache, platform, os, re, string, sys, urllib, urllib2, subprocess

# Version / Log Title 
VERSION_NO = '2020.02.14.10'
PLUGIN_LOG_TITLE = 'QueerClick'

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
CROPPER = r'CScript.exe "{0}/Plex Media Server/Plug-ins/QueerClick.bundle/Contents/Code/ImageCropper.vbs" "{1}" "{2}" "{3}" "{4}"'

# URLS
BASE_URL = 'https://queerclick.com'
BASE_SEARCH_URL = BASE_URL + '/?s={0}'

def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'

def ValidatePrefs():
    pass

class QueerClick(Agent.Movies):
    name = 'QueerClick (IAFD)'
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
            groupsgenres = groups['genres'][2:].strip() if groups['genres'] else ''
            return groups['studio'], groups['title'], groupsgenres, groups['year']

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
        myString = myString.replace('&', 'and').replace(' vol. ', '').replace(' volume ', '').replace(' part ','')

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

    # clean search string before searching on QueerClick
    def CleanSearchString(self, myString):
        # for titles with commas, colons in them on disk represented as ' - '
        nullifySearchStrings = [",", " -", " –" ]
        for item in nullifySearchStrings:
            if item in myString:
                myString = myString.replace(item, '')
                self.log('SEARCH:: "%s" found - Amended Search Title "%s"', item, myString)

        # QueerClick seems to fail to find Titles which have invalid chars in them split at first incident and take first split, just to search but not compare
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
        if len(myString) > 50:
            myString = myString[:50].strip()

        self.log('SEARCH:: "%s" found - Stripped Search Title "%s"', item, myString)
        return String.StripDiacritics(myString).lower()        

    # check IAFD web site for better quality actor thumbnails irrespective of whether we have a thumbnail or not
    def getIAFDActorImage(self, actor):
        photourl = ''
        actor = actor.lower()
        fullname = actor.replace(' ','').replace("'", '').replace(".", '')
        full_name = actor.replace(' ','-').replace("'", '&apos;')

        # actors are categorised on iafd as male, director, female in order of likelihood
        for gender in ['m', 'd']:
            iafd_url = 'http://www.iafd.com/person.rme/perfid={0}/gender={1}/{2}.htm'.format(fullname, gender, full_name)
            self.log('SELF:: Actor  %s - IAFD url: %s', actor, iafd_url)
            # Check URL exists and get actors thumbnail
            try:
                photourl = HTML.ElementFromURL(iafd_url).xpath('//*[@id="headshot"]/img')[0].get('src')
                photourl = photourl.replace('headshots/', 'headshots/thumbs/th_')
                photourl = 'nophoto' if 'nophoto' in photourl else photourl
                break   # if we have got here then actor has a page, stop iteration
            except: 
                self.log('SELF:: NO IAFD Actor Page')

        return photourl

    def log(self, message, *args):
        Log(PLUGIN_LOG_TITLE + ' - '  +  message, *args)

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
            self.log('SEARCH:: Skipping %s because the file name is not in the expected format: (Studio) - Title [- Genres ](Year)', file)
            return

        group_studio, group_title, group_genres, group_year = self.getFilenameGroups(file)
        self.log('SEARCH:: Processing: Studio: %s   Title: %s   Genres: %s Year: %s', group_studio, group_title, group_genres, group_year)

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
        searchTitle = "{0} {1}".format(group_studio, saveTitle)
        searchTitle = self.CleanSearchString(searchTitle)
        searchTitle = String.URLEncode(searchTitle)

        searchQuery = BASE_SEARCH_URL.format(searchTitle)
        
        morePages = True
        pageNumber = 0
        while morePages:
            self.log('SEARCH:: Search Query: %s', searchQuery)
            try: 
                html = HTML.ElementFromURL(searchQuery, timeout=90, errors='ignore', sleep=DELAY)
            except:
                break

            pageNumber += 1
            try:
                searchQuery = html.xpath('//div[@class="pagination post"]/span[@class="right"]/a/@href')[0]    # next page to go to
                morePages = True
            except:
                morePages = False

            titleList = html.xpath('.//article[@id and @class]')
            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))

            for title in titleList:
                # Site Entry
                try:
                    siteEntry = title.find('.//h2[@class="entry-title"]/a')
                    siteEntry = siteEntry.text.split(':')
                    self.log('SEARCH:: Site Entry: %s"', siteEntry)
                except:
                    continue

                # Site Title 
                try:
                    siteTitle = ' '.join(siteEntry[1:])
                    # remove genres from the site entry
                    if group_genres:
                        siteTitle = siteTitle.replace(group_genres, '').strip()
                    self.log('SEARCH:: Site Title: %s"', siteTitle)
                    siteTitle = self.NormaliseComparisonString(siteTitle)
                    self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
                    if siteTitle != compareTitle:
                        continue
                except:
                    continue

                # Site Studio - need to check that the studio name of this title matches to the filename's studio
                try:
                    siteStudio = siteEntry[0]
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
                except:
                    continue
                
                # Site Title URL
                try:
                    siteURL = title.find('.//h2[@class="entry-title"]/a').get('href')
                    self.log('SEARCH:: Site Title URL: %s' % str(siteURL))
                except:
                    self.log('SEARCH:: Error getting Site Title URL')
                    continue

                # Search Website for date - date is in format dd mmm yy
                try:
                    siteReleaseDate = title.find('.//span[@class="date updated"]').text
                    self.log('SEARCH:: Release Date: %s', siteReleaseDate)
                    siteReleaseDate = datetime.datetime.strptime(siteReleaseDate, '%d %b %y')
                except:
                    siteReleaseDate = compareReleaseDate
                    self.log('SEARCH:: Error getting Site Release Date')

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
            self.log('UPDATE:: Skipping %s because the file name is not in the expected format: (Studio) - Title [- Genres ](Year)', file)
            return

        group_studio, group_title, group_genres, group_year = self.getFilenameGroups(file)
        self.log('UPDATE:: Processing: Studio: %s   Title: %s   Genres: %s Year: %s', group_studio, group_title, group_genres, group_year)

        # Fetch HTML
        html = HTML.ElementFromURL(metadata.id.split('|')[0], timeout=60, errors='ignore', sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as is used to find it on website
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Tag line             : Corresponds to the url of movie
        #        d. Originally Available : set from metadata.id (search result)
        #        e. Content Rating       : Always X
        #        f. Genres               : Not always defined
        #    2.  Metadata retrieved from website
        #        a. Summary 
        #        b. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        c. Posters
        #        d. Background 

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

        # 1f.   Genres
        metadata.genres.clear()
        if group_genres is not None:
            group_genres = group_genres.split()
            self.log('UPDATE:: %s Genres Found: "%s"', len(group_genres), group_genres)
            for genre in group_genres:
                if (len(genre) > 0):
                    metadata.genres.add(genre)
        else:
            self.log('UPDATE:: No Genres Found')

        # 2a.   Summary
        try:
            summary = html.xpath('//article[@id and @class]/p//text()')
            summary = " ".join(summary)
            self.log('UPDATE:: Summary Found: %s', summary)
            metadata.summary = summary
        except:
            self.log('UPDATE:: Error getting Summary: %s')

        # 2b/c.   Cast
        #         QueerClick stores the cast as links in the summary text
        newStyle = False
        try:
            castdict = {}
            htmlcast = html.xpath('//div[@class="taxonomy"]/a/@title')
            if len(htmlcast) == 0:
                htmlcast = html.xpath('//article[@id and @class]/p/a/text()')
                # remove duplicates
                htmlcast = list(dict.fromkeys(htmlcast))
                joinedCast = " ".join(htmlcast)
                newStyle = True
            self.log('UPDATE:: %s Cast Found: "%s"', len(htmlcast), htmlcast)
            for cast in htmlcast:
                cast = cast.replace(group_studio,"").replace("()","").strip()
                if newStyle:
                    # most actors will have forename and surname
                    if len(cast.split()) > 2:
                        continue 
                    # as cast is found in text and actors can be reffered to by their first names subsequently, try and remove these
                    if joinedCast.count(cast) > 1:
                        self.log('UPDATE:: Cast: %s : Times Name Found: %s', cast, joinedCast.count(cast))
                        continue
                    # if the xpath value is not in the title skip
                    if cast.lower() not in group_title.lower():
                        continue 
                if len(cast) == 0:
                    continue
                castdict[cast] = self.getIAFDActorImage(cast)
        except Exception as e:
            self.log('UPDATE - Error getting Cast: %s', e)

        # Process Cast  
        # sort the dictionary and add kv to metadata
        metadata.roles.clear()
        for key in sorted (castdict): 
            role = metadata.roles.new()
            role.name = key
            role.photo = castdict[key]

        # 2d/e.   Posters /Background art - Front Cover set to poster, posters/art contain cast list
        imageList = []
        imageCount = 0
        try:
            allimages = html.findall('.//img')
            for image in allimages:
                src = image.get('src')
                if src[-4:] != ".jpg":
                    continue
                height = image.get('height')
                if height is None:
                    continue
                imageCount += 1
                # Only need two images
                if imageCount > 2:
                    break

                # convert to numeric
                width = int(image.get('width'))
                height = int(height)
                self.log('UPDATE:: Found Image %s. "%s"', imageCount, src)
                imageList.append([src, width, height])
        except Exception as e:
            self.log('UPDATE:: Error getting Posters/Background Art: %s', e)
        else:
            # Posters
            try:
                fromWhere = 'ORIGINAL'
                image, width, height = imageList[0]
                imageContent = HTTP.Request(image).content

                # width:height ratio 1:1.5
                maxHeight = int(width * 1.5)

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

            #   Background Art - set second image to background art
            try:
                fromWhere = 'ORIGINAL'
                image, width, height = imageList[1]
                imageContent = HTTP.Request(image).content

                # width:height ratio 16:9
                maxHeight = int(width * 0.5625)

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