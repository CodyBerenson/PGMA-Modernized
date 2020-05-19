# GayMovie - (IAFD)
'''
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    10 May 2020   2020.05.16.01    Creation
    19 May 2020   2020.05.16.02    updated date match function

-----------------------------------------------------------------------------------------------------------------------------------
'''

import datetime, calendar, linecache, platform, os, re, string, sys, urllib, lxml

# Version / Log Title 
VERSION_NO = '2020.05.10.02'
PLUGIN_LOG_TITLE = 'GayMovie'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
# if title on website has a hyphen in its title that does not correspond to a colon replace it with an em dash in the corresponding position
FILEPATTERN = Prefs['regex']
 
# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# URLS
BASE_URL = 'https://gay-movie.org' 
BASE_SEARCH_URL = BASE_URL + '/?s={0}'

# Date Formats used by website
DATE_YMD = '%Y%m%d'
DATEFORMAT = '%Y%m%d'

#----------------------------------------------------------------------------------------------------------------------------------
def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'

#----------------------------------------------------------------------------------------------------------------------------------
def ValidatePrefs():
    pass

#----------------------------------------------------------------------------------------------------------------------------------
class GayMovie(Agent.Movies):
    name = 'GayMovie (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    #-------------------------------------------------------------------------------------------------------------------------------
    def matchFilename(self, file):
        # return groups from filename regex match else return false
        pattern = re.compile(FILEPATTERN)
        matched = pattern.search(file)
        if matched:
            groups = matched.groupdict()
            return groups['studio'], groups['title'], groups['year']
        else:
            raise Exception("File Name [{0}] not in the expected format: (Studio) - Title (Year)".format(file))

    #-------------------------------------------------------------------------------------------------------------------------------
    # match file studio name against website studio name: Boolean Return
    def matchStudioName(self, fileStudioName, siteStudioName):
        siteStudioName = self.NormaliseComparisonString(siteStudioName)

        # remove spaces in comparison variables and check for equality
        noSpaces_siteStudioName = siteStudioName.replace(' ', '')
        noSpaces_fileStudioName = fileStudioName.replace(' ', '')

        if siteStudioName == fileStudioName:
            self.log('SELF:: Studio: Full Word Match: Site: {0} = File: {1}'.format(siteStudioName, fileStudioName))
        elif noSpaces_siteStudioName == noSpaces_fileStudioName:
            self.log('SELF:: Studio: Full Word Match: Site: {0} = File: {1}'.format(siteStudioName, fileStudioName))
        elif siteStudioName in fileStudioName:
            self.log('SELF:: Studio: Part Word Match: Site: {0} IN File: {1}'.format(siteStudioName, fileStudioName))
        elif fileStudioName in siteStudioName:
            self.log('SELF:: Studio: Part Word Match: File: {0} IN Site: {1}'.format(fileStudioName, siteStudioName))
        else:
            raise Exception('Match Failure: Site: {0}'.format(siteStudioName))

        return True

    #-------------------------------------------------------------------------------------------------------------------------------
    # match file year against website release date: return formatted site date if no error or default to formated file date
    def matchReleaseDate(self, fileDate, siteDate):
        if len(siteDate) == 4:      # a year has being provided - default to 31st December of that year
            siteDate = siteDate + '1231'
            siteDate = datetime.datetime.strptime(siteDate, DATE_YMD)
        elif len(siteDate) == 7:    # month/year provided - default to last day of month
            year = int(siteDate[-4:])
            month = int(siteDate[:2])
            day = calendar.monthrange(year, month)[1]
            siteDate = '{0}{1}{2:2d}'.format(year, month, day)
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

    #-------------------------------------------------------------------------------------------------------------------------------
    # Normalise string for Comparison, strip all non alphanumeric characters, Vol., Volume, Part, and 1 in series
    def NormaliseComparisonString(self, myString):
        # convert to lower case and trim
        myString = myString.strip().lower()

        # convert sort order version to normal version i.e "Best of Zak Spears, The -> the Best of Zak Spears"
        if myString.count(', the'):
            myString = 'the ' + myString.replace(', the', '', 1)
        if myString.count(', an'):
            myString = 'an ' + myString.replace(', an', '', 1)
        if myString.count(', a'):
            myString = 'a ' + myString.replace(', a', '', 1)

        # remove vol/volume/part and vol.1 etc wording as filenames dont have these to maintain a uniform search across all websites and remove all non alphanumeric characters
        myString = myString.replace('&', 'and').replace(' vol.', '').replace(' volume', '').replace(' part','').replace(',', '')

        # remove all standalone "1's"
        regex = re.compile(r'(?<!\d)1(?!\d)')
        myString = regex.sub('', myString)

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

    #-------------------------------------------------------------------------------------------------------------------------------
    # Prepare Video title for search query
    def CleanSearchString(self, myString):
        # convert to lower case and trim and strip diacritics
        myString = String.StripDiacritics(myString)
        myString = myString.lower().strip()
        myString = '"{0}"'.format(String.URLEncode(myString))
        self.log('SELF:: Search String = %s', myString)
        return myString

    #-------------------------------------------------------------------------------------------------------------------------------
    # check IAFD web site for better quality actor thumbnails irrespective of whether we have a thumbnail or not
    def getIAFDActorImage(self, actor):
        photourl = ''
        actor = String.StripDiacritics(actor).lower()
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

    #-------------------------------------------------------------------------------------------------------------------------------
    def log(self, message, *args):
        Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    #-------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        if not media.items[0].parts[0].file:
            return
        folder, file = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])

        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version      : v.%s', VERSION_NO)
        self.log('SEARCH:: Python       : %s', sys.version_info)
        self.log('SEARCH:: Platform     : %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Prefs->delay : %s', DELAY)
        self.log('SEARCH::      ->regex : %s', FILEPATTERN)
        self.log('SEARCH:: media.title  : %s', media.title)
        self.log('SEARCH:: File Name    : %s', file)
        self.log('SEARCH:: File Folder  : %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check filename format
        try:
            group_studio, group_title, group_year = self.matchFilename(file)
            self.log('SEARCH:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)
        except Exception as e:
            self.log('SEARCH:: Skipping %s', e)
            return

        # Compare Variables used to check against the studio name on website: remove all umlauts, accents and ligatures
        compareStudio = self.NormaliseComparisonString(group_studio)
        compareTitle = self.NormaliseComparisonString(group_title)
        compareReleaseDate = datetime.datetime(int(group_year), 12, 31) # default to 31 Dec of Filename yesr

        # Search Query - for use to search the internet, remove all non alphabetic characters as GayMovie site returns no results if apostrophes or commas exist etc..
        searchTitle = self.CleanSearchString(group_title)
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        # Finds the entire media enclosure <Table> element then steps through the rows
        morePages = True
        while morePages:
            self.log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
            except Exception as e:
                self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                return

            try:
                searchQuery = html.xpath('//a[@class="pagination-next"]/@href')[0]
                self.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(searchQuery.split('/')[-1].split('?')[0]) - 1
                morePages = True
            except:
                searchQuery = ''
                self.log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            titleList = html.xpath('//div[@class="fusion-post-wrapper"]')
            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))

            for title in titleList:
                # Site Title
                try:
                    siteTitle = title.xpath('.//div/div/h2/a/text()')[0]
                    siteTitle = self.NormaliseComparisonString(siteTitle)
                    self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
                    if siteTitle != compareTitle:
                        continue
                except:
                    self.log('SEARCH:: Error getting Site Title')
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('.//div/div/h2/a/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    self.log('SEARCH:: Site Title url: %s', siteURL)
                except:
                    self.log('SEARCH:: Error getting Site Title Url')
                    continue

                # No Site Release Dates stored so default to filename year
                siteReleaseDate = compareReleaseDate

                # Studio Name
                try:
                    siteStudio = html.xpath('.//a[@rel="tag"]/text()')[0]
                    self.matchStudioName(compareStudio, siteStudio)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Studio: %s', e)
                    continue

                # we should have a match on studio, title and year now
                results.Append(MetadataSearchResult(id = siteURL + '|' + siteReleaseDate.strftime(DATEFORMAT), name = group_title, score = 100, lang = lang)) 
                return

    #-------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        folder, file = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log('-----------------------------------------------------------------------')
        self.log('UPDATE:: Version    : v.%s', VERSION_NO)
        self.log('UPDATE:: File Name  : %s', file)
        self.log('UPDATE:: File Folder: %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check filename format
        try:
            group_studio, group_title, group_year = self.matchFilename(file)
            self.log('UPDATE:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)
        except Exception as e:
            self.log('UPDATE:: Skipping %s', e)
            return

        # Fetch HTML.
        html = HTML.ElementFromURL(metadata.id.split('|')[0], timeout=60, errors='ignore', sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as above
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Tag line             : Corresponds to the url of movie
        #        d. Originally Available : set from metadata.id (search result)
        #        e. Content Rating       : Always X
        #    2.  Metadata retrieved from website
        #        a. Summary 
        #        b. Directors            : List of Directors (alphabetic order)
        #        c. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        d. Posters/Background 

        # 1a.   Studio - straight of the file name
        metadata.studio = group_studio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = group_title
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = metadata.id.split('|')[0]
        metadata.originally_available_at = datetime.datetime.strptime(metadata.id.split('|')[1], DATEFORMAT)
        metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Tagline: %s', metadata.tagline)
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)    

        # 1e.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 2a.   Summary
        try:
            summary = ''
            summary = html.xpath('//div[@class="fusion-text"]/p/text()')[0]
            self.log('UPDATE:: Summary Found: %s', summary)
        except Exception as e:
            summary = ''
            self.log('UPDATE:: Error getting summary: %s', e)

        summary = summary.strip()
        metadata.summary = summary if len(summary) > 0 else ' '

        # 2b.   Directors
        try:
            directordict = {}
            htmldirector = html.xpath('//div[@class="fusion-text"]/p/descendant::strong[contains(text(),"Director")]/parent::p/strong[last()]/following::text()')[0].replace(':', '').split(',')
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

        # 2c.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        try:
            castdict = {}
            htmlcast = html.xpath('//strong[text()="Actors"]//following::text()')[0].replace(': ', '').split(',')
            for castname in htmlcast:
                cast = castname.strip()
                if not cast:
                    continue
                if '(' in cast:
                    cast = cast.split('(')[0]
                castdict[cast] = self.getIAFDActorImage(cast)
                castdict[cast] = '' if castdict[cast] == 'nophoto' else castdict[cast]

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted (castdict): 
                role = metadata.roles.new()
                role.name = key
                role.photo = castdict[key]
        except Exception as e:
            self.log('UPDATE - Error getting Cast: %s', e)

        # 2d.   Posters/Background Art
        try:
            htmlimages = html.xpath('//a[@class="fusion-lightbox"]/img/@src')[:2]	# only need first two images
            image = htmlimages[0]
            validPosterList = [image]
            image = (BASE_URL if BASE_URL not in image else '') + image
            self.log('UPDATE:: Movie Poster Found: "%s"', image)
            validPosterList.append(image)
            if image not in metadata.posters:
                metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order = 1)
            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

            image = htmlimages[1]
            validArtList = [image]
            image = (BASE_URL if BASE_URL not in image else '') + image
            self.log('UPDATE:: Movie Background Art Found: "%s"', image)
            validArtList.append(image)
            if image not in metadata.art:
                metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order = 1)
            #  clean up and only keep the Art we have added
            metadata.art.validate_keys(validArtList)
        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Background Art: %s', e)