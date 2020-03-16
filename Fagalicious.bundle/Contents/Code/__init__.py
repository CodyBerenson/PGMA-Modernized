# Fagalicious - (IAFD)
import datetime, linecache, platform, os, re, string, sys, urllib

# Version / Log Title 
VERSION_NO = '2020.01.18.6'
PLUGIN_LOG_TITLE = 'Fagalicious'

# PLEX API
load_file = Core.storage.load

DEBUG = Prefs['debug']

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
# if title on website has a hyphen in its title that does not correspond to a colon replace it with an em dash in the corresponding position
FILEPATTERN = Prefs['regex']

# Seconds to pause after a network request was made, ensuring undue burden is not placed on the web server
DELAY = int(Prefs['delay'])

# online image cropper
THUMBOR = Prefs['thumbor'] + "/0x0:{0}x{1}/{2}"

# backup VBScript image cropper
CROPPER = r'"%localappdata%\Plex Media Server\Plug-ins\QueerClick.bundle\Contents\Code\ImageCropper.vbs" "{0}" "{1}" {2} {3}'

# URLS
BASE_URL = 'https://fagalicious.com'
BASE_SEARCH_URL = BASE_URL + '/search/{0}/page/{1}'

def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

def ValidatePrefs():
    pass

class Fagalicious(Agent.Movies):
    name = 'Fagalicious (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultScenes']
    accepts_from = ['com.plexapp.agents.localmedia']

    def matchedFilename(self, file):
        # match file name to regex
        self.log ("PATTERN = %s", FILEPATTERN) 
        pattern = re.compile(FILEPATTERN)
        return pattern.search(file)

    def getFilenameGroups(self, file):
        # return groups from filename regex match
        pattern = re.compile(FILEPATTERN)
        matched = pattern.search(file)
        if matched:
            groups = matched.groupdict()
            groupstitle = groups['title']
            if ' - Disk ' in groupstitle:
                groupstitle = groupstitle.split(' - Disk ')[0]
            if ' - Disc ' in groupstitle:
                groupstitle = groupstitle.split(' - Disc ')[0]
            return groups['studio'], groupstitle, groups['year']

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
        if len(myString) > 50:
            myString = myString[:50].strip()

        self.log('SEARCH:: "%s" found - Stripped Search Title "%s"', item, myString)
        return String.StripDiacritics(myString).lower()        

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
        if DEBUG:
            Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    def search(self, results, media, lang, manual):
        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version - v.%s', VERSION_NO)
        self.log('SEARCH:: Platform - %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Prefs->debug      - %s', DEBUG)
        self.log('SEARCH::      ->delay      - %s', DELAY)
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
        
        # Finds the entire media enclosure <DIV> elements then steps through them
        totalPages = 1
        pageNumber = 0
        self.log('SEARCH:: Initial Total Search Pages: %s pages', totalPages)
        while pageNumber <= totalPages:
            pageNumber += 1
            self.log('SEARCH:: Result Page No: %s', pageNumber)

            searchQuery = BASE_SEARCH_URL.format(searchTitle, pageNumber)
            self.log('SEARCH:: Search Query: %s', searchQuery)
            html = HTML.ElementFromURL(searchQuery, timeout=90, errors='ignore', sleep=DELAY)
            if pageNumber == 1:
                siteTotalPages = html.xpath('//div[@class="nav-links"]/a[@class="page-numbers"]/text()') or '0'
                if siteTotalPages != '0':
                    siteTotalPages = max(siteTotalPages)
                self.log('SEARCH:: Total Search Pages: %s pages', siteTotalPages)
                totalPages = int(siteTotalPages)

            titleList = html.xpath('//h2[@class="entry-title"]')
            self.log('SEARCH:: Titles List: %s Found', len(titleList))

            for title in titleList:
                self.log('SEARCH:: Title : %s', title)

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
            summary = html.xpath('//section[@class="entry-content"]/p//text()')
            summary = " ".join(summary)
            summary = summary.replace('\n','').replace('\r','').strip()
            summary = summary.split('writes:')[1]
            self.log('UPDATE:: Summary Found: %s', summary)
            metadata.summary = summary
        except:
            self.log('UPDATE:: Error getting Summary: %s')
            pass

        # 2b/c.   Cast/Genre
        #       Fagalicious stores the cast and genres as tags, if tag is in title assume its a cast member else its a genre
        #       get thumbnails from IAFD as they are right dimensions for plex cast list
        try:
            castdict = {}
            genres = []
            htmltags = html.xpath('//ul/a[contains(@href, "https://fagalicious.com/tag/")]/text()')
            self.log('UPDATE:: %s Cast/Genres Tags Found: "%s"', len(htmltags), htmltags)
            for tag in htmltags:
                if tag in group_title:
                    cast = tag.strip()
                    if (len(cast) > 0):
                        castdict[cast] = self.getIAFDActorImage(cast)
                else:
                    genres.append(tag.split('(')[0])
        except Exception as e:
            self.log('UPDATE - Error getting Cast/Genres: %s', e)
            pass

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

        # 2d/e.   Posters /Background art - Front Cover set to poster
        imageList = html.xpath('//div[@class="mypicsgallery"]/a/img[@src and @data-src]')
        try:
            thumborImage = None
            scriptImage = None
            image = imageList[0].get('data-src')
            width = int(imageList[0].get('width'))
            height = int(imageList[0].get('height'))
            # width:height ratio 1:1.5
            desiredHeight = int(width * 1.5)
            self.log('UPDATE:: Movie Poster Found: size; (%sx%s) address; "%s"', width, height, image)
            # cropping needs to be done
            if height > desiredHeight:
                thumborImage = THUMBOR.format(width, desiredHeight, image)
                # if thumbor service is down - use vbscript (only windows)
                if not thumborImage and os.name == 'nt':
                    FileName = r"%temp%\{0}".format(image.split("/")[-1])
                    cmd = r'CScript.exe ' + CROPPER.format(image, FileName, width, desiredHeight)
                    self.log('UPDATE:: Command: %s', cmd)
                    subprocess.call(cmd)
                    scriptImage = load_file(FileName)
                    validPosterList = [FileName]
                    metadata.posters[scriptImage] = Proxy.Media(scriptImage, sort_order = 1)
                    self.log('UPDATE:: Script Image; "%s"', scriptImage)                        
                else:
                    validPosterList = [thumborImage]
                    metadata.posters[thumborImage] = Proxy.Media(HTTP.Request(thumborImage).content, sort_order = 1)
                    self.log('UPDATE:: Thumbor Image; "%s"', thumborImage)

            # if no cropping needed or cropping did not occur
            if height <= desiredHeight or (height > desiredHeight and not thumborImage and not scriptImage):
                validPosterList = [image]
                metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order = 1)
                self.log('UPDATE:: Image; "%s"', image)

            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

        except Exception as e:
            self.log('UPDATE:: Error getting Poster Art: %s', e)
            pass     

        try:
            thumborImage = None
            scriptImage = None
            if len(imageList) > 1:
                del imageList[0]
            else:
                imageList = html.xpath('//figure[@class="gallery-item"]/div/img[@src and @data-src]')

            image = imageList[0].get('data-src')
            width = int(imageList[0].get('width'))
            height = int(imageList[0].get('height'))
            # width:height ratio 16:9
            desiredHeight = int(width * 0.5625)
            self.log('UPDATE:: Movie Poster Found: size; (%sx%s) address; "%s"', width, height, image)
            # cropping needs to be done
            if height > desiredHeight:
                thumborImage = THUMBOR.format(width, desiredHeight, image)
                # if thumbor service is down - use vbscript (only windows)
                if not thumborImage and os.name == 'nt':
                    FileName = r"%temp%\{0}".format(image.split("/")[-1])
                    cmd = r'CScript.exe ' + CROPPER.format(image, FileName, width, desiredHeight)
                    self.log('UPDATE:: Command: %s', cmd)
                    subprocess.call(cmd)
                    scriptImage = load_file(FileName)
                    validArtList = [FileName]
                    metadata.art[scriptImage] = Proxy.Media(scriptImage, sort_order = 1)
                    self.log('UPDATE:: Loaded Image; "%s"', scriptImage)                        
                else:
                    validArtList = [thumborImage]
                    metadata.art[thumborImage] = Proxy.Media(HTTP.Request(thumborImage).content, sort_order = 1)
                    self.log('UPDATE:: Thumbor Image; "%s"', thumborImage)

            # if no cropping needed or cropping did not occur
            if height <= desiredHeight or (height > desiredHeight and not thumborImage and not scriptImage):
                validArtList = [image]
                metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order = 1)
                self.log('UPDATE:: Image; "%s"', image)

            #  clean up and only keep the Art we have added
            metadata.art.validate_keys(validArtList)
        except Exception as e:
            self.log('UPDATE:: Error getting Background Art: %s', e)
            pass       
