# GayDVDEmpire (IAFD)
import datetime, linecache, platform, os, re, string, sys, urllib

# Version / Log Title 
VERSION_NO = '2019.08.12.0'
PLUGIN_LOG_TITLE = 'GayDVDEmpire'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
# if title on website has a hyphen in its title that does not correspond to a colon replace it with an em dash in the corresponding position
FILEPATTERN = Prefs['regex']

# URLS
GDE_BASEURL = 'http://www.gaydvdempire.com'
GDE_SEARCH_MOVIES = GDE_BASEURL + '/allsearch/search?view=list&q=%s'
GDE_MOVIE_INFO = GDE_BASEURL + '/%s/'

def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

def ValidatePrefs():
    pass

class GDEAgent(Agent.Movies):
    name = 'Gay DVD Empire (IAFD)'
    languages = [Locale.Language.NoLanguage, Locale.Language.English]
    primary_provider = True
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.cockporn']
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
        myString = myString.replace('&', 'and').replace(' 1', '').replace(' vol.', '').replace(' volume', '').replace(' part ','')

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

    # get product information
    def getProductInfoData(self):
        #   Product info div
        data = {}

        try:
            # Match different code, some titles are missing parts -- Still fails and needs to be refined.
            productinfo = '<small>None</small>'
            if html.xpath('//*[@id="content"]/div[2]/div[2]/div/div[1]/ul'):
                productinfo = HTML.StringFromElement(html.xpath('//*[@id="content"]/div[2]/div[2]/div/div[1]/ul')[0])
            if html.xpath('//*[@id="content"]/div[2]/div[3]/div/div[1]/ul'):
                productinfo = HTML.StringFromElement(html.xpath('//*[@id="content"]/div[2]/div[3]/div/div[1]/ul')[0])
            if html.xpath('//*[@id="content"]/div[2]/div[4]/div/div[1]/ul'):
                productinfo = HTML.StringFromElement(html.xpath('//*[@id="content"]/div[2]/div[4]/div/div[1]/ul')[0])
            if html.xpath('//*[@id="content"]/div[3]/div[3]/div/div[1]/ul'):
                productinfo = HTML.StringFromElement(html.xpath('//*[@id="content"]/div[3]/div[3]/div/div[1]/ul')[0])
            if html.xpath('//*[@id="content"]/div[3]/div[4]/div/div[1]/ul'):
                productinfo = HTML.StringFromElement(html.xpath('//*[@id="content"]/div[3]/div[4]/div/div[1]/ul')[0])

            productinfo = productinfo.replace('<small>', '|').replace('</small>', '')
            productinfo = productinfo.replace('<li>', '').replace('</li>', '')
            productinfo = HTML.ElementFromString(productinfo).text_content()

            for div in productinfo.split('|'):
                if ':' in div:
                    name, value = div.split(':')
                    data[name.strip()] = value.strip()
                    self.log('SELF:: Title Metadata Key: [%s]   Value: [%s]', name.strip(), value.strip())
            return True, data
        except:
            return False, data

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
            self.log('sELF:: Actor  %s - IAFD url: %s', actor, iafd_url)
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
        self.log('SEARCH::      ->useproductiondate - %s', Prefs['useproductiondate'])
        self.log('SEARCH::      ->ignoregenres - %s', Prefs['ignoregenres'])
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

        #  Release date default to January 1st of Filename value compare against release date on website
        compareReleaseDate = datetime.datetime(int(group_year), 1, 1)

        # saveTitle corresponds to the real title of the movie.
        saveTitle = group_title
        self.log('SEARCH:: Original Group Title: %s', saveTitle)

        # gaydvdempire displays colons in the titles and hyphens, so convert hyphens to columns and em-dash to hyphens
        searchTitle = String.StripDiacritics(saveTitle.lower())
        searchTitle = searchTitle.replace(' -', ':').replace('–', '-')
        
        # Search Query - for use to search the internet
        searchQuery = GDE_SEARCH_MOVIES % String.URLEncode(searchTitle)
        self.log('SEARCH:: Search Query: %s', searchQuery)

        compareTitle = self.NormaliseComparisonString(saveTitle)

        # Finds the entire media enclosure <DIV> elements then steps through them
        titleList = HTML.ElementFromURL(searchQuery).xpath('//div[contains(@class,"row list-view-item")]')
        for title in titleList:
            # siteTitle = The text in the 'title' - Gay DVDEmpire - displays its titles in SORT order
            titlehref = title.xpath('.//a[contains(@label,"Title")]')[0]
            siteTitle = titlehref.text_content().strip()
            siteTitle = self.NormaliseComparisonString(siteTitle)

            self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
            if siteTitle != compareTitle:
                continue

            # Site Studio Check
            siteStudio = title.xpath('.//small[contains(text(),"studio")]/following-sibling::text()[1]')[0]
            siteStudio = self.NormaliseComparisonString(siteStudio)
            if siteStudio == compareStudio:
                self.log('SEARCH:: Studio: Full Word Match: Filename: %s = Website: %s', compareStudio, siteStudio)
            elif siteStudio in compareStudio:
                self.log('SEARCH:: Studio: Part Word Match: Website: %s IN Filename: %s', siteStudio, compareStudio)
            elif compareStudio in siteStudio:
                self.log('SEARCH:: Studio: Part Word Match: Filename: %s IN Website: %s', compareStudio, siteStudio)
            else:
                continue

            # Site Released Date Check - default to filename year
            whatDate = 'Filename Date'
            found, data = self.getProductInfoData()
            if found:
                #   Set Originally Available At to Release Date if found else default to default to January 1st of Filename value
                if 'Released' in data:
                    try:
                        siteReleaseDate = Datetime.ParseDate(data['Released']).date()
                        whatDate = 'Released'
                    except: 
                        siteReleaseDate = compareReleaseDate
                        self.log('SEARCH:: Error getting Released Date from Website')
                        pass

                #   Reset to Production Year: If User Prefers
                if Prefs['useproductiondate']:
                    if 'Production Year' in data:
                        try:
                            siteReleaseDate = datetime.datetime(int(data['Production Year']), 1, 1).date()
                            whatDate = 'Production Year'
                        except: 
                            siteReleaseDate = compareReleaseDate
                            self.log('SEARCH:: Error getting Production Year from Website')
                            pass

                timedelta = siteReleaseDate - compareReleaseDate
                self.log('SEARCH:: Compare Release Date - %s Site Date - %s : Dx [%s] days"', compareReleaseDate, siteReleaseDate, timedelta.days)
                if abs(timedelta.days) > 366:
                    self.log('SEARCH:: Difference of more than a year between file date and %s date from Website')
                    pass
            else:
                self.log('SEARCH:: Error getting Product Information')
                pass

            # curID = the ID portion of the href in 'movie'
            siteURL = GDE_MOVIE_INFO % titlehref.get('href').split('/',2)[1]
            self.log('SEARCH:: Site Title URL: %s' % str(siteURL))

            # we should have a match on both studio and title now
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

        html = HTML.ElementFromURL(metadata.id)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as above
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Content Rating       : Always X
        #    2.  Metadata retrieved from website
        #        a. Tag line             : Corresponds to the url of movie if not found
        #        b. Originally Available : Initially set from year group value + 1st Jan
        #                                  if value found on website, replace this initial setting
        #        c. Summary 
        #        d. Directors            : List of Drectors (alphabetic order)
        #        e. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        f. Genres
        #        g. Collections
        #        h. Posters/Background 

        # 1a.   Studio
        metadata.studio = group_studio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = group_title
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 2a.   Tagline
        try: 
            tagline = html.xpath('//p[@class="Tagline"]')[0].text_content().strip()
            metadata.tagline = tagline if len(tagline) == 0 else metadata.id
        except: pass

        # 2b.   Originally Available At
        #   default to 1st January Filename year
        try:
            metadata.originally_available_at = Datetime.ParseDate('Jan 01 ' + group_year).date()
            metadata.year = metadata.originally_available_at.year
        except: 
            self.log('UPDATE:: Error setting Originally Available At from Filename')
            pass

        # check website for release date field
        found, data = self.getProductInfoData()
        if found:
            #   Set Originally Available At to Release Date if found else default to default to January 1st of Filename value
            if 'Released' in data:
                try:
                    metadata.originally_available_at = Datetime.ParseDate(data['Released']).date()
                    metadata.year = metadata.originally_available_at.year
                except: 
                    self.log('UPDATE:: Error getting Originally Available At from Website')

            #   Reset to Production Year: If User Prefers
            if Prefs['useproductiondate']:
                if 'Production Year' in data:
                    try:
                        metadata.originally_available_at = Datetime.ParseDate(data['Production Year'] + '-01-01')
                        metadata.year = metadata.originally_available_at.year
                    except: 
                        self.log('UPDATE:: Error getting setting Originally Available At from Production Year on Website')
        else:
            self.log('UPDATE:: Error getting Product Information')
            pass

        # 2c.   Summary
        try:
            summary = html.xpath('//div[@class="col-xs-12 text-center p-y-2 bg-lightgrey"]/div/p')[0].text_content().strip()
            summary = re.sub('<[^<]+?>', '', summary)
            self.log('UPDATE:: Summary Found: %s' %str(summary))
            metadata.summary = summary
        except:
            self.log('UPDATE:: Error getting Summary')
            pass

        # 2d.   Directors
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

        # 2e.   Cast
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

        # 2f.   Genres
        try:
            genreList = []
            metadata.genres.clear()
            ignoregenres = [x.lower().strip() for x in Prefs['ignoregenres'].split('|')]
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

        # 2g.   Collections
        try:
            metadata.collections.clear()
            htmlcollections = html.xpath('//a[contains(@label, "Series")]')
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
            image = html.xpath('//*[@id="front-cover"]/img')[0]
            posterurl = image.get('src')
            self.log('UPDATE:: Movie Thumbnail Found: "%s"', posterurl)
            validPosterList = [posterurl]
            if posterurl not in metadata.posters:
                try:
                    metadata.posters[posterurl] = Proxy.Preview(HTTP.Request(posterurl).content, sort_order = 1)
                except:
                    self.log('UPDATE:: Error getting Poster') 
                    pass
            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

            arturl = posterurl.replace('h.jpg', 'bh.jpg')
            validArtList = [arturl]
            if arturl not in metadata.art:
                try:
                    metadata.art[arturl] = Proxy.Preview(HTTP.Request(arturl).content, sort_order = 1)
                except:
                    self.log('UPDATE:: Error getting Background Art') 
                    pass
            #  clean up and only keep the background art we have added
            metadata.art.validate_keys(validArtList)
        except:
            self.log('UPDATE:: Error getting Poster/Background Art:')
            pass