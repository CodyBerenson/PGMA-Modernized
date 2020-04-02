# coding=utf-8

# WayBig (IAFD)
import datetime, linecache, platform, os, re, string, sys, urllib, subprocess

# Version / Log Title 
VERSION_NO = '2019.12.22.11'
PLUGIN_LOG_TITLE = 'WayBig'

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
CROPPER = r'CScript.exe "{0}/Plex Media Server/Plug-ins/WayBig.bundle/Contents/Code/ImageCropper.vbs" "{1}" "{2}" "{3}" "{4}"'

# URLS
BASE_URL = 'https://www.waybig.com'
BASE_SEARCH_URL = BASE_URL + '/blog/index.php?s=%s'

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
    accepts_from = ['com.plexapp.agents.localmedia']

    def matchedimageFileName(self, file):
        # match file name to regex
        pattern = re.compile(FILEPATTERN)
        return pattern.search(file)

    def getimageFileNameGroups(self, file):
        # return groups from imageFileName regex match
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

        # remove vol/volume/part and vol.1 etc wording as imageFileNames dont have these to maintain a uniform search across all websites and remove all non alphanumeric characters
        myString = myString.replace('&', 'and').replace(' 1', '').replace(' vol.', '').replace(' volume', '').replace(' part ','')

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

    # clean search string before searching on WayBig
    def CleanSearchString(self, myString):
        # Waybig seems to fail to find Titles which have an apostrophe in them split at first incident and take first split, just to search but not compare
        invalidCharacters = ["'", "‘", "’"]
        for Char in invalidCharacters:
            if Char in myString:
                myString = myString.split(Char)[0]
                self.log('SEARCH:: "%s" found - Amended Search Title "%s"', Char, myString)

        # for titles with colons in them
        if " - " in myString:
            myString = myString.replace(' - ',': ')
            self.log('SEARCH:: Hyphen found - Amended Search Title "%s"', myString)

        # Search Query - for use to search the internet
        return String.StripDiacritics(myString).lower()        

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

        folder, file = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log('SEARCH:: File Name: %s', file)
        self.log('SEARCH:: Enclosing Folder: %s', folder)
 
        # Check imageFileName format
        if not self.matchedimageFileName(file):
            self.log('SEARCH:: Skipping %s because the file name is not in the expected format: (Studio) - Title (Year)', file)
            return

        group_studio, group_title, group_year = self.getimageFileNameGroups(file)
        self.log('SEARCH:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)

        #  Release date default to December 31st of imageFileName value compare against release date on website
        compareReleaseDate = datetime.datetime(int(group_year), 12, 31)

        # saveTitle corresponds to the real title of the movie.
        saveTitle = group_title
        self.log('SEARCH:: Original Group Title: %s', saveTitle)

        # WayBig displays its movies as Studio: Title or Studio:Title (at Studio) or Title at Studio
        # compareTitle will be used to search against the titles on the website, remove all umlauts, accents and ligatures
        searchTitleList = []
        compareTitleList = []

        cleanStudio = self.CleanSearchString(group_studio)
        cleanTitle = self.CleanSearchString(group_title)
        compareStudio  = self.NormaliseComparisonString(group_studio)
        compareTitle = self.NormaliseComparisonString(group_title)
        
        compareTitleList.append(compareTitle)
        searchTitleList.append(cleanTitle)

        compareTitleList.append(compareStudio + ' ' + compareTitle)
        searchTitleList.append(cleanStudio + ' ' + cleanTitle)

        compareTitleList.append(compareStudio + ': ' + compareTitle)
        searchTitleList.append(cleanStudio + ': ' + cleanTitle)

        compareTitleList.append(compareStudio + ': ' + compareTitle + ' at ' + compareStudio)
        searchTitleList.append(cleanStudio + ': ' + cleanTitle + ' at ' + cleanStudio)

        compareTitleList.append(compareTitle + ' at ' + compareStudio)
        searchTitleList.append(cleanTitle + ' at ' + cleanStudio)

        for searchTitle in searchTitleList:
            compareTitle = compareTitleList[searchTitleList.index(searchTitle)]
            searchQuery = BASE_SEARCH_URL % String.URLEncode(searchTitle)
            self.log('SEARCH:: Search Query: %s', searchQuery) 

            html = HTML.ElementFromURL(searchQuery, timeout=90, errors='ignore', sleep=DELAY)
            titleList = html.xpath('.//div[contains(@class,"row")]/div[contains(@class,"content-col col")]/article')
            self.log('SEARCH:: Titles List: %s Found', len(titleList))

            for title in titleList:
                siteTitle = title.xpath('.//h2[contains (@class, "entry-title")]')[0].text_content().strip()
                self.log('SEARCH:: Site Title "%s"', siteTitle)
                siteTitle = self.NormaliseComparisonString(siteTitle)
                compareTitle  = self.NormaliseComparisonString(compareTitle)
                self.log('SEARCH:: Site Title: [%s]', siteTitle)
                self.log('SEARCH:: Comp Title: [%s]', compareTitle)
                if siteTitle != compareTitle:
                    siteTitle = siteTitle.replace(group_studio.lower(),'')
                    compareTitle = compareTitle.replace(group_studio.lower(),'')
                    if siteTitle != compareTitle:
                        continue

                self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)

                # curID = the ID portion of the href in 'movie'
                siteURL = title.xpath('.//a[contains(@rel, "bookmark")]/@href')[0]
                self.log('SEARCH:: Site Title URL: %s' % str(siteURL))

                # Get thumbnail image - store it with the CURID for use during updating
                siteImageURL = ''
                try:
                    siteImageURL = title.xpath('.//img/@src')[0]
                    self.log('SEARCH:: Site Thumbnail Image URL: %s' % str(siteImageURL))
                except:
                    self.log('SEARCH:: Error Site Thumbnail Image')
                    pass

                # Site Released Date Check - default to imageFileName year
                try:
                    siteReleaseDate = datetime.datetime(int(siteURL.split('/')[4]), int(siteURL.split('/')[5]), int(siteURL.split('/')[6]))
                except:
                    siteReleaseDate = compareReleaseDate
                    self.log('SEARCH:: Error getting Site Release Date')
                    pass

                timedelta = siteReleaseDate - compareReleaseDate
                self.log('SEARCH:: Compare Release Date - %s Site Date - %s : Dx [%s] days"', compareReleaseDate, siteReleaseDate, timedelta.days)
                if abs(timedelta.days) > 366:
                    self.log('SEARCH:: Difference of more than a year between file date and %s date from Website')
                    continue

                # we should have a match on both studio and title now
                results.Append(MetadataSearchResult(id = siteURL + '|' + siteImageURL, name = saveTitle, score = 100, lang = lang))

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

        # Check imageFileName format
        if not self.matchedimageFileName(file):
            self.log('UPDATE:: Skipping %s because the file name is not in the expected format: (Studio) - Title (Year)', file)
            return

        group_studio, group_title, group_year = self.getimageFileNameGroups(file)
        self.log('UPDATE:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)

        # the ID is composed of the webpage for the video and its thumbnail
        html = HTML.ElementFromURL(metadata.id.split('|')[0], timeout=60, errors='ignore', sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of imageFileName - no need to process this as above
        #        b. Title                : From title group of imageFileName - no need to process this as is used to find it on website
        #        c. Content Rating       : Always X
        #        d. Tag line             : Corresponds to the url of movie, retrieved from metadata.id split
        #        e. Originally Available : retrieved from the url of the movie
        #        f. background Art       : retrieved from metadata.id split
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
        try:
            self.log('UPDATE:: Originally Available Date: Year [%s], Month [%s], Day [%s]',  metadata.id.split('/')[4], metadata.id.split('/')[5], metadata.id.split('/')[6])
            metadata.originally_available_at = datetime.datetime(int(metadata.id.split('/')[4]),int(metadata.id.split('/')[5]),int(metadata.id.split('/')[6])).date()
            metadata.year = metadata.originally_available_at.year
        except: 
            self.log('UPDATE:: Error setting Originally Available At from imageFileName')
            pass

        # 1f.   Background art
        arturl = metadata.id.split('|')[1].strip()
        if not arturl:
            validArtList = [arturl]
            if arturl not in metadata.art:
                try:
                    self.log('UPDATE:: Background Art URL: %s', arturl)
                    metadata.art[arturl] = Proxy.Media(HTTP.Request(arturl).content, sort_order = 1)
                except:
                    self.log('UPDATE:: Error getting Background Art') 
                    pass
            #  clean up and only keep the background art we have added
            metadata.art.validate_keys(validArtList)

        # 2a.   Summary
        try:
            summary = html.xpath('//div[@class="entry-content"]')[0].text_content().strip()
            summary = re.sub('<[^<]+?>', '', summary)
            # delete first line from summary text as its the name of the video flick at studio
            # summary = summary[summary.index('\n')+1:]
            # ignore all code from start of html code
            self.log('UPDATE:: Summary Found: %s' %str(summary))
            if 'jQuery' in summary:
                summary = summary.split('jQuery')[0].strip()
            if '});' in summary:
                summary = summary.split('});')[1].strip()
            summary = summary.replace('Watch ' + group_title + ' at ' + group_studio, '').strip()
            summary = summary.replace('Watch as ' + group_title + ' at ' + group_studio, '').strip()
            summary = summary.replace(group_title + ' at ' + group_studio + ':', '').strip()
            metadata.summary = summary
        except:
            self.log('UPDATE:: Error getting Summary')
            pass

        # 2b.   Cast
        try:
            castdict = {}
            htmlcast = html.xpath('//a[contains(@href,"https://www.waybig.com/blog/tag/")]/text()')
            self.log('UPDATE:: Cast List %s', htmlcast)
            for castname in htmlcast:
                cast = castname.replace(u'\u2019s','').strip()
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
            pass

        # 2c.   Posters - Front Cover set to poster
        imageList = html.xpath('//a[@target="_self" or @target="_blank"]/img[(@height or @width) and @alt and contains(@src, "zing.waybig.com/reviews")]')
        try:
            thumborImage = None
            scriptImage = None
            image = imageList[0].get('src')
            width = int(imageList[0].get('width'))

            self.log('UPDATE:: Movie Poster Found: width; %s address; "%s"', width, image)

            # width:height ratio 1:1.5
            height = int(width * 1.5)
            if hasattr(imageList[0], 'height'):
                if int(imageList[0].get('height')) < height:
                    height = imageList[0].get('height')

            try:
                # crop by default
                thumborImage = THUMBOR.format(width, height, image)
                validPosterList = [thumborImage]
                metadata.posters[thumborImage] = Proxy.Media(HTTP.Request(thumborImage).content, sort_order = 1)
                self.log('UPDATE:: Thumbor Image; "%s"', thumborImage)
            except Exception as e:
                # if thumbor service is down - use vbscript (only windows)
                thumborImage = None
                try:
                    if os.name == 'nt':
                        envVar = os.environ
                        scriptImage = os.path.join(envVar['TEMP'], image.split("/")[-1]).replace('\\', '/')
                        localappdata = envVar['LOCALAPPDATA'].replace('\\', '/')
                        cmd = CROPPER.format(localappdata, image, scriptImage, width, height)
                        self.log('UPDATE:: Command: %s', cmd)

                        subprocess.call(cmd)
                        scriptImageData = load_file(scriptImage)
                        validPosterList = [scriptImage]
                        metadata.posters[scriptImage] = Proxy.Media(scriptImageData, sort_order = 1)
                        self.log('UPDATE:: Script Image; "%s"', scriptImage)                        
                except Exception as e:
                    scriptImage = None
                    pass
                pass

            # if cropping did not occur
            if not thumborImage and not scriptImage:
                    validPosterList = [image]
                    metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order = 1)
                    self.log('UPDATE:: Original Image; "%s"', image)

            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)
        except Exception as e:
            self.log('UPDATE:: Error getting Poster Art: %s', e)
            pass     

        # 2d.   Background Art - Next picture set to Background 
        #       height attribute not always provided - so crop to ratio as default - if thumbor fails use script
        try:
            thumborImage = None
            scriptImage = None
            image = imageList[1].get('src')
            width = int(imageList[1].get('width'))

            self.log('UPDATE:: Background Art Found: width; %s address; "%s"', width, image)

            # width:height ratio 16:9
            height = int(width * 0.5625)
            if hasattr(imageList[1], 'height'):
                if int(imageList[1].get('height')) < height:
                    height = imageList[1].get('height')

            try:
                # crop by default
                thumborImage = THUMBOR.format(width, height, image)
                validArtList = [thumborImage]
                metadata.art[thumborImage] = Proxy.Media(HTTP.Request(thumborImage).content, sort_order = 1)
                self.log('UPDATE:: Thumbor Image; "%s"', thumborImage)
            except Exception as e:
                # if thumbor service is down - use vbscript (only windows)
                thumborImage = None

                try:
                    if os.name == 'nt':
                        envVar = os.environ
                        scriptImage = os.path.join(envVar['TEMP'], image.split("/")[-1]).replace('\\', '/')
                        localappdata = envVar['LOCALAPPDATA'].replace('\\', '/')
                        cmd = CROPPER.format(localappdata, image, scriptImage, width, height)
                        self.log('UPDATE:: Command: %s', cmd)

                        subprocess.call(cmd)
                        scriptImageData = load_file(scriptImage)
                        validArtList = [scriptImage]
                        metadata.art[scriptImage] = Proxy.Media(scriptImageData, sort_order = 1)
                        self.log('UPDATE:: Script Image; "%s"', scriptImage)                        
                except Exception as e:
                    scriptImage = None
                    pass
                pass

            # if cropping did not occur
            if not thumborImage and not scriptImage:
                validArtList = [image]
                metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order = 1)
                self.log('UPDATE:: Original Image; "%s"', image)

            #  clean up and only keep the Art we have added
            metadata.art.validate_keys(validArtList)
        except Exception as e:
            self.log('UPDATE:: Error getting Background Art: %s', e)
            pass