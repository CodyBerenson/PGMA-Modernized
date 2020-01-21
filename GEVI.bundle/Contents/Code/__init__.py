# GEVI - (IAFD)
import datetime, linecache, platform, os, re, string, sys, urllib, lxml

# Version / Log Title 
VERSION_NO = '2019.12.25.1'
PLUGIN_LOG_TITLE = 'GEVI'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
# if title on website has a hyphen in its title that does not correspond to a colon replace it with an em dash in the corresponding position
FILEPATTERN = Prefs['regex']
 
# Delay used when requesting HTML, may be good to have to prevent being banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL = 'https://www.gayeroticvideoindex.com'
BASE_SEARCH_URL = BASE_URL + '/search.php?type=t&where=b&query=%s&Search=Search&page=1'

def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

def ValidatePrefs():
    pass

class GEVI(Agent.Movies):
    name = 'GEVI (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = True
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.cockporn']
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
        myString = myString.replace('&', 'and').replace(' 1', '').replace(' vol.', '').replace(' volume', '').replace(' part','')

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

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
        if Prefs['debug']:
            Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    def search(self, results, media, lang, manual):
        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version - v.%s', VERSION_NO)
        self.log('SEARCH:: Platform - %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Prefs->debug - %s', Prefs['debug'])
        self.log('SEARCH::      ->regex - %s', FILEPATTERN)
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

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        searchTitle = String.StripDiacritics(saveTitle.lower())
        searchTitle = searchTitle.replace('-', '').replace('–', '').replace("'",'').replace(',','').replace('& ','').replace('  ', ' ')

        # split searchTitle at first digit as GEVI will not find titles with digits in them
        for firstDigit, character in enumerate(searchTitle):
            if character.isdigit():
                uptofirstDigit = firstDigit - 1
                searchTitle = searchTitle[0:uptofirstDigit]
                break
        
        searchQuery = BASE_SEARCH_URL % String.URLEncode(searchTitle)
        self.log('SEARCH:: Search Query: %s', searchQuery)

        # Finds the entire media enclosure <Table> element then steps through the rows
        titleList = HTML.ElementFromURL(searchQuery, sleep=REQUEST_DELAY).xpath('//table[contains(@class,"d")]/tr')
        self.log('SEARCH:: Titles List: %s Found', len(titleList))

        for title in titleList:
            siteTitle = title[0].text_content().strip()
            if siteTitle == '':
                break

            siteTitle = self.NormaliseComparisonString(siteTitle)
            self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
            if siteTitle != compareTitle:
                continue

            siteURL = title.xpath('.//td/a/@href')[0]
            if BASE_URL not in siteURL:
                siteURL = BASE_URL + siteURL
            self.log('SEARCH:: Title url: %s', siteURL)

            # need to check that the studio name of this title matches to the filename's studio
            siteStudio = title[2].text_content().strip()
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

            # Search Website for date - date is in format yyyy - so default to December 31st
            try:
                siteReleaseDate = title[1].text_content().strip()
                self.log('SEARCH:: Release Date: %s', siteReleaseDate)
                siteReleaseDate = datetime.datetime(int(siteReleaseDate), 12, 31)
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
            results.Append(MetadataSearchResult(id = siteURL, name = saveTitle, score = 100, lang = lang)) 
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
            self.log('SEARCH:: Skipping %s because the file name is not in the expected format: (Studio) - Title (Year)', file)
            return

        group_studio, group_title, group_year = self.getFilenameGroups(file)
        self.log('UPDATE:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)

        # Fetch HTML.
        html = HTML.ElementFromURL(metadata.id, sleep=REQUEST_DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as above
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Tag line             : Corresponds to the url of movie
        #        d. Content Rating       : Always X
        #    2.  Metadata retrieved from website
        #        a. Originally Available : Initially set from year group value + 31st December
        #                                  if value found on website, replace this initial setting
        #        b. Summary 
        #        c. Directors            : List of Drectors (alphabetic order)
        #        d. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        e. Genre
        #        f. Posters/Background 

        # 1a.   Studio - straight of the file name
        metadata.studio = group_studio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = group_title
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c.   Set Tagline to URL.
        metadata.tagline = metadata.id
        self.log('UPDATE:: Tagline: %s', metadata.id)

        # 1d.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 2a.   Originally Available - default to December 31st of Filename value, then update with website value if found
        metadata.originally_available_at = datetime.datetime(int(group_year), 12, 31)
        metadata.year = metadata.originally_available_at.year
        try:
            siteReleaseDate = html.xpath('//td[contains(text(),"released")]//following-sibling::td[1]/text()')[0].strip()
            metadata.originally_available_at = datetime.datetime(int(siteReleaseDate), 12, 31).date()
            metadata.year = metadata.originally_available_at.year
        except: 
            self.log('UPDATE:: Error setting Originally Available At')
            pass

        # 2b.   Summary
        try:
            summary = html.xpath('//td[@class="sd"]/div[@class="dw"]/span/text()')[0].strip()
            summary = summary.replace('\n','').replace('\r','').strip()
            self.log('UPDATE:: Summary Found: %s', summary)
            metadata.summary = summary
        except:
            self.log('UPDATE:: Error getting Summary: %s')
            pass

        # 2c.   Directors
        try:
            directordict = {}
            htmldirector = html.xpath('//td[contains(text(),"director")]//following-sibling::td[1]/a/text()')
            self.log('UPDATE:: Director List %s', htmldirector)
            for directorname in htmldirector:
                director = directorname.strip()
                if (len(director) > 0):
                    directordict[director] = None

            # sort the dictionary and add kv to metadata
            metadata.directors.clear()
            for key in sorted (directordict): 
                director = metadata.directors.new()
                director.name = key
        except Exception as e:
            self.log('UPDATE:: Error getting Director(s): %s', e)
            pass

        # 2d.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        try:
            castdict = {}
            htmlcast = html.xpath('//td[@class="pd"]/a/text()')
            for castname in htmlcast:
                cast = castname.strip()
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
        except Exception as e:
            self.log('UPDATE - Error getting Cast: %s', e)
            pass

        # 2e.   Genre
        try:
            metadata.genres.clear()
            htmlgenres = html.xpath('//td[contains(text(),"category")]//following-sibling::td[1]/text()')
            self.log('UPDATE:: %s Genres Found: "%s"', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                genre = genre.strip()
                if (len(genre) > 0):
                    metadata.genres.add(genre)
        except Exception as e:
            self.log('UPDATE:: Error getting Genres: %s', e)
            pass

        # 2f.   Posters/Background Art
        try:
            htmlimage = html.xpath('//td[@class="gp"]/a/@href')
            image = htmlimage[0]
            if BASE_URL not in image:
                image = BASE_URL + image
            self.log('UPDATE:: Movie Poster Found: "%s"', image)
            validPosterList = [image]
            if image not in metadata.posters:
                metadata.posters[image] = Proxy.Preview(HTTP.Request(image).content, sort_order = 1)
            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

            image = htmlimage[1]
            if BASE_URL not in image:
                image = BASE_URL + image
            self.log('UPDATE:: Movie Background Art Found: "%s"', image)
            validArtList = [image]
            if image not in metadata.art:
                metadata.art[image] = Proxy.Preview(HTTP.Request(image).content, sort_order = 1)
            #  clean up and only keep the Art we have added
            metadata.art.validate_keys(validArtList)
        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Background Art: %s', e)
            pass       
