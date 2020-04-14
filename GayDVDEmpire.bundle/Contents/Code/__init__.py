# GayDVDEmpire (IAFD)
'''
                                    Version History
                                    ---------------
    Date            Version             Modification
    13 Apr 2020     2019.08.12.3        Corrected scrapping of collections
    14 Apr 2020     2019.08.12.4        sped up search routine, corrected tagline
                                        search multiple result pages

---------------------------------------------------------------------------------------------------------------
'''
import datetime, linecache, platform, os, re, string, sys, urllib

# Version / Log Title 
VERSION_NO = '2019.08.12.4'
PLUGIN_LOG_TITLE = 'GayDVDEmpire'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
# if title on website has a hyphen in its title that does not correspond to a colon replace it with an em dash in the corresponding position
FILEPATTERN = Prefs['regex']

# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# URLS
BASE_URL = 'http://www.gaydvdempire.com'
BASE_SEARCH_URL = BASE_URL + '/AllSearch/Search?view=list&q={0}{1}'

def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'

def ValidatePrefs():
    pass

class GayDVDEmpire(Agent.Movies):
    name = 'GayDVDEmpire (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']
    accepts_from = ['com.plexapp.agents.localmedia']

    def matchedFilename(self, file):
        # match file name to regex
        self.log ("SELF:: PATTERN = '%s'", FILEPATTERN) 
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

    # Prepare Video title for search query
    def PrepareSearchQueryString(self, myString):
        myString = String.StripDiacritics(myString)
        myString = myString.lower().strip()
        myString = myString.replace(' -', ':').replace('–', '-')
        myString = String.URLEncode(myString )
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
        if Prefs['debug']:
            Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    def search(self, results, media, lang, manual):
        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version - v.%s', VERSION_NO)
        self.log('SEARCH:: Platform - %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Prefs->debug - %s', Prefs['debug'])
        self.log('SEARCH::      ->regex - %s', FILEPATTERN)
        self.log('SEARCH::      ->delay - %s', Prefs['delay'])
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

        #  Release date default to December 31st of Filename value compare against release date on website
        compareReleaseDate = datetime.datetime(int(group_year), 12, 31)

        # saveTitle corresponds to the real title of the movie.
        saveTitle = group_title
        self.log('SEARCH:: Original Group Title: %s', saveTitle)

        # compareTitle will be used to search against the titles on the website, remove all umlauts, accents and ligatures
        compareTitle = self.NormaliseComparisonString(saveTitle)
        
        # Search Query - for use to search the internet
        searchTitle = self.PrepareSearchQueryString(saveTitle)

        # Finds the entire media enclosure <Table> element then steps through the rows
        pageNumber = 0
        morePages = True
        while morePages:
            pageNumber += 1
            self.log('SEARCH:: Result Page No: %s', pageNumber)
            if pageNumber == 1:
                searchQuery = BASE_SEARCH_URL.format(searchTitle, '')
            else:
                searchQuery = BASE_SEARCH_URL.format(searchTitle, '&page=' + str(pageNumber))

            self.log('SEARCH:: Search Query: {0}'.format(searchQuery))

            html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
            try:
                testmorePages = html.xpath('.//a[@title="Next"]/@title')[0]
                morePages = True
            except:
                morePages = False

            # Finds the entire media enclosure <DIV> elements then steps through them
            titleList = html.xpath('.//div[contains(@class,"row list-view-item")]')
            self.log('SEARCH:: Titles List: %s Found', len(titleList))

            for title in titleList:
                # siteTitle = The text in the 'title' - Gay DVDEmpire - displays its titles in SORT order
                try:
                    siteTitle = title.xpath('./div/h3/a[@category and @label="Title"]/@title')[0]
                    siteTitle = self.NormaliseComparisonString(siteTitle)
                    self.log('SEARCH:: Title Match: [{0}] Compare Title - Site Title "{1} - {2}"'.format((compareTitle == siteTitle), compareTitle, siteTitle))
                    if siteTitle != compareTitle:
                        continue
                except:
                    continue

                # Site Studio Check
                try:
                    siteStudio = title.xpath('./div/ul/li/a/small[text()="studio"]/following-sibling::text()')[0].strip()
                    siteStudio = self.NormaliseComparisonString(siteStudio)
                    self.log('SEARCH:: Studio:: {0}'.format(siteStudio))
                    if siteStudio == compareStudio:
                        self.log('SEARCH:: Studio: Full Word Match: Filename: {0} = Website: {1}'.format(compareStudio, siteStudio))
                    elif siteStudio in compareStudio:
                        self.log('SEARCH:: Studio: Part Word Match: Website: {0} IN Filename: {1}'.format(siteStudio, compareStudio))
                    elif compareStudio in siteStudio:
                        self.log('SEARCH:: Studio: Part Word Match: Filename: {0} IN Website: {1}'.format(compareStudio, siteStudio))
                    else:
                        # strip all spaces and compare
                        noSpaceSiteStudio = siteStudio.replace(' ', '')
                        noSpaceCompareStudio = compareStudio.replace(' ', '')
                        if noSpaceSiteStudio != noSpaceCompareStudio:
                            self.log('SEARCH:: Studio: Full Match Fail: Filename: {0} != Website: {1}'.format(compareStudio, siteStudio))
                            continue
                except:
                    continue

                # Get the production year if exists - if it does not match to the compareReleaseDate year AKA group_year - next!
                try:
                    siteProductionYear = title.xpath('./h3/small[contains(.,"(")]')[0]
                    siteProductionYear = siteProductionYear.replace('(', '').replace(')','')
                    if siteProductionYear != group_year:
                        self.log('SEARCH:: Production Year: {0} != does not match File Year: {1}'.format(siteProductionYear, group_year))
                        continue
                # we will use the site release date further on
                except: pass

                siteURL = title.xpath('./div/h3/a[@label="Title"]/@href')[0]
                if BASE_URL not in siteURL:
                    siteURL = BASE_URL + siteURL
                self.log('SEARCH:: Site Title URL: %s', siteURL)

                # Site Released Date Check - default to filename year AKA Production Year
                try:
                    siteReleaseDate = title.xpath('./div/ul/li/span/small[text()="released"]/following-sibling::text()')[0].strip()
                    self.log('SEARCH:: Release Date: %s', siteReleaseDate)
                    siteReleaseDate = datetime.datetime.strptime(siteReleaseDate, '%m/%d/%Y')
                except: 
                    # initialise to 1st Jan 1900
                    siteReleaseDate = datetime.datetime(1900, 1, 1)
                    self.log('SEARCH:: Error getting Release Date from Website')
                    pass

                # if the year of the release date matches the year of the production year, use it as
                # the release date has day, month and year and doesn't default to the last day of the production year
                if siteReleaseDate.year != compareReleaseDate.year:
                    siteReleaseDate = compareReleaseDate

                timedelta = siteReleaseDate - compareReleaseDate
                self.log('SEARCH:: Compare Release Date - %s Site Date - %s : Dx [%s] days"', compareReleaseDate, siteReleaseDate, timedelta.days)
                if abs(timedelta.days) > 366:
                    self.log('SEARCH:: Difference of more than a year between file date and %s date from Website')
                    continue

                # we should have a match on both studio and title now
                results.Append(MetadataSearchResult(id = siteURL+ '|' + siteReleaseDate.strftime('%d/%m/%Y'), name = saveTitle, score = 100, lang = lang))

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

        html = HTML.ElementFromURL(metadata.id.split('|')[0], sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as above
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Content Rating       : Always X
        #        d. Originally Available : set from metadata.id (search result)
        #
        #    2.  Metadata retrieved from website
        #        a. Tag line             : Corresponds to the url of movie if not found
        #        b. Summary 
        #        c. Directors            : List of Drectors (alphabetic order)
        #        d. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        e. Genres
        #        f. Collections
        #        g. Posters/Background 

        # 1a.   Studio
        metadata.studio = group_studio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = group_title
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 1d.   Originally Available from metadata.id
        metadata.originally_available_at =  datetime.datetime.strptime(metadata.id.split('|')[1], '%d/%m/%Y')
        metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)

        # 2a.   Tagline
        try: 
            metadata.tagline = html.xpath('//p[@class="Tagline"]')[0].text_content().strip()
        except: 
            metadata.tagline = metadata.id.split('|')[0]
            self.log('UPDATE:: Default Tagline to Video URL: %s', metadata.tagline)
            pass

        # 2b.   Summary
        try:
            summary = html.xpath('//div[@class="col-xs-12 text-center p-y-2 bg-lightgrey"]/div/p')[0].text_content().strip()
            summary = re.sub('<[^<]+?>', '', summary)
            self.log('UPDATE:: Summary Found: %s' %str(summary))
            metadata.summary = summary
        except:
            self.log('UPDATE:: Error getting Summary')
            pass

        # 2c.   Directors
        try:
            directordict = {}
            htmldirector = html.xpath('//a[contains(@label, "Director - details")]/text()')
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
            pass

        # 2d.   Cast
        try:
            castdict = {}
            htmlcast = html.xpath('//a[contains(@class,"PerformerName")]/text()')
            self.log('UPDATE:: Cast List %s', htmlcast)
            for castname in htmlcast:
                cast = castname.strip()
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

        # 2e.   Genres
        try:
            genreList = []
            metadata.genres.clear()
            ignoregenres = "Sale|4K Ultra HD".lower().split('|')
            htmlgenres = html.xpath('//ul[@class="list-unstyled m-b-2"]//a[@label="Category"]/text()')
            self.log('UPDATE:: %s Genres Found: "%s"', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                genre = genre.strip()
                if (len(genre) > 0):
                    genreList.append(genre)
                    if not genre.lower() in ignoregenres: 
                        metadata.genres.add(genre)
            self.log('UPDATE:: Found Genres: %s' % (' | '.join(genreList)))
        except:
            self.log('UPDATE:: Error getting Genres')
            pass

        # 2f.   Collections
        try:
            metadata.collections.clear()
            htmlcollections = html.xpath('//a[contains(@label, "Series")]/text()')
            self.log('UPDATE:: %s Collections Found: "%s"', len(htmlcollections), htmlcollections)
            for collection in htmlcollections:
                collection = collection.replace('"', '').replace('Series', '').strip()
                if (len(collection) > 0):
                    metadata.collections.add(collection)
        except:
            self.log('UPDATE:: Error getting Collections')
            pass

        # 2g.   Poster/Background Art
        try:
            image = html.xpath('//*[@id="front-cover"]/img')[0]
            posterurl = image.get('src')
            self.log('UPDATE:: Movie Thumbnail Found: "%s"', posterurl)
            validPosterList = [posterurl]
            if posterurl not in metadata.posters:
                try:
                    metadata.posters[posterurl] = Proxy.Media(HTTP.Request(posterurl).content, sort_order = 1)
                except:
                    self.log('UPDATE:: Error getting Poster') 
                    pass
            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

            arturl = posterurl.replace('h.jpg', 'bh.jpg')
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
            self.log('UPDATE:: Error getting Poster/Background Art:')
            pass