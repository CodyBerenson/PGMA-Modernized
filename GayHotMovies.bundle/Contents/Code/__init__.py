# GayHotMovies (IAFD)
import datetime, linecache, platform, os, re, string, sys, urllib

# Version / Log Title 
VERSION_NO = '2019.08.12.0'
PLUGIN_LOG_TITLE = 'GayHotMovies'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
# if title on website has a hyphen in its title that does not correspond to a colon replace it with an em dash in the corresponding position
FILEPATTERN = Prefs['regex']

# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])
 
# URLS
BASE_URL = 'https://www.gayhotmovies.com'
BASE_SEARCH_MOVIES = BASE_URL + '/search.php?search_string={0}&find_with=all_ordered&searchtype_value=video_title&view_style=scenes'

def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

def ValidatePrefs():
    pass

class GayHotMovies(Agent.Movies):
    name = 'GayHotMovies (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']
    accepts_from = ['com.plexapp.agents.localmedia']

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
        self.log('SEARCH::      ->delay - %s', Prefs['delay'])
        self.log('SEARCH::      ->regex - %s', FILEPATTERN)
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
        searchTitle = String.StripDiacritics(saveTitle.lower())
        searchTitle = searchTitle.replace(' -', ':').replace('–', '-').replace('& ', '')
        searchQuery = BASE_SEARCH_MOVIES.format(String.URLEncode(searchTitle))
        self.log('SEARCH:: Search Query: %s', searchQuery)


        # Finds the entire media enclosure <DIV> elements then steps through them
        titleList = HTML.ElementFromURL(searchQuery, sleep=DELAY).xpath('//div[contains(@class,"medium-8 cell title maintitle")]/a')
        self.log('SEARCH:: Titles List: %s Found', len(titleList))

        for title in titleList:
            siteTitle = title.text_content()
            siteTitle = self.NormaliseComparisonString(siteTitle)
            siteURL = title.get('href')

            self.log('SEARCH:: Title Match: [{0}] Compare Title - Site Title "{1} - {2}"'.format((compareTitle == siteTitle), compareTitle, siteTitle))
            if siteTitle != compareTitle:
                continue

            # need to check that the studio name of this title matches to the filename's studio
            html = HTML.ElementFromURL(siteURL)

            # Site Studio Check
            siteStudio = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/studio") and (@title) and (@rel)]')[0].text_content()
            siteStudio = self.NormaliseComparisonString(siteStudio)
            self.log('SEARCH:: Studio Match: [{0}] Compare Studio - Site Studio "{1} - {2}"'.format((compareStudio == siteStudio), compareStudio, siteStudio))
            if siteStudio == compareStudio:
                self.log('SEARCH:: Studio: Full Word Match: Filename: {0} = Website: {1}'.format(compareStudio, siteStudio))
            elif siteStudio in compareStudio:
                self.log('SEARCH:: Studio: Part Word Match: Website: {0} IN Filename: {1}'.format(siteStudio, compareStudio))
            elif compareStudio in siteStudio:
                self.log('SEARCH:: Studio: Part Word Match: Filename: {0} IN Website: {1}'.format(compareStudio, siteStudio))
            else:
                continue

            # Search Website for date and reset if available to 1st of month (Website only gives yyyy)
            # there can not be a difference more than 365 days
            siteReleaseDate = 1900
            try: 
                siteReleaseDate = html.xpath('//span[contains(@itemprop,"copyrightYear")]')[0].text_content().strip()
                siteReleaseDate = datetime.datetime(int(siteReleaseDate), 12, 31)
            except:
                siteReleaseDate = compareReleaseDate
                self.log('SEARCH:: Error getting Site Release Date')
                pass

            timedelta = siteReleaseDate - compareReleaseDate
            self.log('SEARCH:: Compare Release Date - %s Site Date - %s : Dx [%s] days"', compareReleaseDate, siteReleaseDate, timedelta.days)
            if abs(timedelta.days) > 366:
                self.log('SEARCH:: Difference of more than a year between file date and %s date from Website')
                continue

            # we should have a match on both studio, title and date now
            results.Append(MetadataSearchResult(id = siteURL, name = saveTitle, score = 100, lang = lang))

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

        # Check filename format
        if not self.matchedFilename(file):
            self.log('UPDATE:: Skipping %s because the file name is not in the expected format: (Studio) - Title (Year)', file)
            return

        group_studio, group_title, group_year = self.getFilenameGroups(file)
        self.log('UPDATE:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)

        html = HTML.ElementFromURL(metadata.id, sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as above
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Content Rating       : Always X
        #        d. Tag line             : Corresponds to the url of movie, as Website does not show Tag lines
        #        e. Originally Available : GayHotMovies only displays the Release Year, so use studio year
        #    2.  Metadata retrieved from website
        #        a. Summary 
        #        b. Directors            : List of Drectors (alphabetic order)
        #        c. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        d. Genres
        #        e. Collections
        #        f. Posters/Background 

        # 1a.   Studio
        metadata.studio = group_studio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Title
        metadata.title = group_title
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c.   Tagline
        metadata.tagline = metadata.id
        self.log('UPDATE:: Tagline: %s', metadata.id)

        # 1d.   Content Rating: Set to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 1e.   Originally Available At: Website lists date released as Year Value
        metadata.originally_available_at = datetime.datetime(int(group_year), 12, 31)
        metadata.year = metadata.originally_available_at.year
        try:
            siteReleaseDate = html.xpath('//span[@itemprop="copyrightYear"]/text()')[0]
            metadata.originally_available_at = datetime.datetime(int(siteReleaseDate), 12, 31).date()
            metadata.year = metadata.originally_available_at.year
        except: 
            self.log('UPDATE:: Error setting Originally Available At')
            pass

        # 2a.   Summary
        try:
            summary = html.xpath('//span[contains(@class,"video_description")]')[0].text_content().strip()
            summary = re.sub('<[^<]+?>', '', summary)
            self.log('UPDATE:: Summary Found: %s' %str(summary))
            metadata.summary = summary
        except:
            self.log('UPDATE:: Error getting Summary')
            pass

        # 2d.   Directors
        try:
            directordict = {}
            htmldirector = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/director/")]/span/text()')
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
        except:
            self.log('UPDATE:: Error getting Director(s)')

        # 2e.   Cast
        #   default to using thumbnails from GayHotMovies as they don't seem to use the same actor names as IAFD, if thumbail has empty gif go to IAFD
        try:
            castdict = {}
            htmlcast = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/porn-star/") and (@title) and (@rel)]/img')
            self.log('UPDATE:: Cast List %s', htmlcast)
            for castname in htmlcast:
                cast = castname.get('alt').lower().replace('(male)', '').title()
                image = castname.get('src')
                self.log('UPDATE:: Cast Name - %s [ %s ]', cast, image)
                if (len(cast) > 0):
                    castdict[cast] = image if not 'empty_mal.gif' in image else self.getIAFDActorImage(cast)

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted (castdict): 
                role = metadata.roles.new()
                role.name = key
                role.photo = castdict[key]
        except:
            self.log('UPDATE:: Error getting Cast')

        # 2f.   Genres
        try:
            metadata.genres.clear()
            htmlgenres = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/category/")]/span/text()')
            self.log('UPDATE:: %s Genres Found: "%s"', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                if '>' in genre:
                    genre = genre.split('>')[1]
                genre.strip()
                if (len(genre) > 0):
                    metadata.genres.add(genre)
        except:
            self.log('UPDATE:: Error getting Genres')

        # 2g.   Collections
        try:
            metadata.collections.clear()
            htmlcollections = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/series/")]/text()')
            self.log('UPDATE:: %s Collections Found: "%s"', len(htmlcollections), htmlcollections)
            for collection in htmlcollections:
                collection = collection.strip()
                if (len(collection) > 0):
                    metadata.collections.add(collection)
        except:
            self.log('UPDATE:: Error getting Collections')
            pass

        # 2h.   Poster
        try:
            posterurl = html.xpath('//div[@class="lg_inside_wrap"]/@data-front')[0]
            self.log('UPDATE:: Movie Front Thumbnail Found: "%s"', posterurl)
            validPosterList = [posterurl]
            if posterurl not in metadata.posters:
                try:
                    metadata.posters[posterurl] = Proxy.Media(HTTP.Request(posterurl).content, sort_order = 1)
                except:
                    self.log('UPDATE:: Error getting Poster') 
                    pass
            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

            arturl = html.xpath('//div[@class="lg_inside_wrap"]/@data-back')[0]
            self.log('UPDATE:: Movie Backgound Art Thumbnail Found: "%s"', arturl)
            validArtList = [arturl]
            if arturl not in metadata.art:
                try:
                    metadata.art[arturl] = Proxy.Media(HTTP.Request(arturl).content, sort_order = 1)
                except:
                    self.log('UPDATE:: Error getting Background Art') 
                    pass
            #  clean up and only keep the background art we have added
            metadata.art.validate_keys(validArtList)
        except:
            #       sometimes no back cover exists... on some old movies
            try:
                self.log('UPDATE:: Movie Cover Picture Found: OLD')
                posterurl = html.xpath('//img[contains(@itemprop,"image") and contains(@id,"cover") and contains(@class,"cover")]')[0]
                posterurl = posterurl.get('src')
                self.log('UPDATE:: Movie Cover Picture Found: "%s"', posterurl)
                validPosterList = [posterurl]
                if posterurl not in metadata.posters:
                    try:
                        metadata.posters[posterurl] = Proxy.Media(HTTP.Request(posterurl).content, sort_order = 1)
                    except:
                        self.log('UPDATE:: Error getting Poster') 
                        pass
                #  clean up and only keep the poster we have added
                metadata.posters.validate_keys(validPosterList)
            except:
                self.log('UPDATE:: Error getting Poster/Background Art:')
                pass

