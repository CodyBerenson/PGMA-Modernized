# IAFD - (IAFD)
'''
                                    Version History
                                    ---------------
    Date            Version             Modification
    22 Apr 2020     2020.04.22.1        Creation

---------------------------------------------------------------------------------------------------------------
'''
import datetime, linecache, platform, os, re, string, sys, urllib

# Version / Log Title 
VERSION_NO = '2020.04.22.1'
PLUGIN_LOG_TITLE = 'IAFD'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
# if title on website has a hyphen in its title that does not correspond to a colon replace it with an em dash in the corresponding position
FILEPATTERN = Prefs['regex']

# Seconds to pause after a network request was made, ensuring undue burden is not placed on the web server
DELAY = int(Prefs['delay'])

# URLS
BASE_URL = 'http://www.iafd.com'
BASE_SEARCH_URL = BASE_URL + '/results.asp?searchtype=comprehensive&searchstring={0}'

def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'

def ValidatePrefs():
    pass

class IAFD(Agent.Movies):
    name = 'Internet Adult Film Database'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms', 'com.plexapp.agents.GayAdultScenes']

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

        # remove articles from beginning of string and reference to first in a series
        if myString[:4] == 'the ':
            myString = myString[4:]
        if myString[:3] == 'an ':
            myString = myString[3:]
        if myString[:2] == 'a ':
            myString = myString[2:]
        if myString[-2:] == ' 1':
            myString = myString[:-2]

        # remove vol/volume/part and vol.1 etc wording as filenames dont have these to maintain a uniform search across all websites and remove all non alphanumeric characters
        myString = myString.replace('&', 'and').replace(' vol.', '').replace(' volume', '').replace(' part','')

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

    # clean search string before searching on IAFD
    def CleanSearchString(self, myString):
        # Search Query - for use to search the internet
        myString = myString.strip().lower()
        if myString[:4] == 'the ':
            myString = myString[4:]
        if myString[:3] == 'an ':
            myString = myString[3:]
        if myString[:2] == 'a ':
            myString = myString[2:]
        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString)
        return myString

    def log(self, message, *args):
        Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    def search(self, results, media, lang, manual):
        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version - v.%s', VERSION_NO)
        self.log('SEARCH:: Platform - %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Prefs->delay      - %s', DELAY)
        self.log('SEARCH::      ->regex      - %s', FILEPATTERN)
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
        searchTitle = self.CleanSearchString(saveTitle)
        searchQuery = BASE_SEARCH_URL.format(searchTitle)
        self.log('SEARCH:: Search Query: %s', searchQuery)

        # iafd displays the first 50 results, clicking on "See More Results"  appends the rest
        try:
            html = HTML.ElementFromURL(searchQuery, timeout=90, errors='ignore', sleep=DELAY)
        except Exception as e:
            self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
            return

        try:
            searchQuery = html.xpath('//a[text()="See More Results..."]/@href')[0].strip()
            if BASE_URL not in searchQuery:
                searchQuery = BASE_URL + '/' + searchQuery
            self.log('SEARCH:: Loading Additional Search Results: %s', searchQuery)
            html = HTML.ElementFromURL(searchQuery, timeout=90, errors='ignore', sleep=DELAY)
        except:
            self.log('SEARCH:: No Additional Search Results')

        titleList = html.xpath('//table[@id="titleresult"]/tbody/tr')
        self.log('SEARCH:: Titles List: %s Found', len(titleList))
        for title in titleList:
            # Site Title Check
            try:
                siteTitle = title.xpath('./td[1]/a/text()')[0]
                self.log('SEARCH:: Site Title: "%s"', siteTitle)
                siteTitle = self.NormaliseComparisonString(siteTitle)
                self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
                if siteTitle != compareTitle: # compare against AKA column
                    try:
                        siteAKATitle = title.xpath('./td[4]/text()')[0]
                        siteAKATitle = self.NormaliseComparisonString(siteAKATitle)
                        if siteAKATitle != compareTitle: 
                            continue
                    except:
                        self.log('SEARCH:: Error getting Site AKA Title')
                        continue
            except:
                self.log('SEARCH:: Error getting Site Title')
                continue

            # Site Studio Check
            try:
                siteStudio = title.xpath('./td[3]/text()')[0]
                self.log('SEARCH:: Site Studio: %s', siteStudio)
                siteStudio = self.NormaliseComparisonString(siteStudio)
                self.log('SEARCH:: Studio Match: [%s] Compare Studio - Site Studio "%s - %s"', (compareStudio == siteStudio), compareStudio, siteStudio)
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
                self.log('SEARCH:: Error getting Site Studio')
                continue

            # Site Title URL Check
            try:
                siteURL = title.xpath('./td[1]/a/@href')[0]
                if siteURL[0] != '/':
                    siteURL = '/' + siteURL
                if BASE_URL not in siteURL:
                    siteURL = BASE_URL + siteURL
                self.log('SEARCH:: Site Title url: %s', siteURL)
            except:
                self.log('SEARCH:: Error getting Site Title Url')

            # Search Website for date - date is in format yyyy
            try:
                siteReleaseDate = title.xpath('./td[2]/text()')[0].strip()
                self.log('SEARCH:: Site Release Date: %s', siteReleaseDate)
                siteReleaseDate = datetime.datetime(int(siteReleaseDate), 12, 31)
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
        #        d. Content Rating       : Always X
        #    2.  Metadata retrieved from website
        #        a. Originally Available : set from metadata.id (search result), then if release date found on url page update it
        #        b. Summary              : Synopsis, Scene Breakdown and Comments
        #        c. Cast                 : List of Actors and Photos (alphabetic order)
        #        d. Directors

        # 1a.   Studio - straight of the file name
        metadata.studio = group_studio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = group_title
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c.   Set Tagline/Originally Available from metadata.id
        metadata.tagline = metadata.id.split('|')[0]
        self.log('UPDATE:: Tagline: %s', metadata.tagline)

        # 1d.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 2a.   Originally Available at
        try:
            siteReleaseDate = html.xpath('.//p[@class="bioheading" and text()="Release Date"]//following-sibling::p[1]//text()')[0].strip()
            siteReleaseDate = datetime.datetime.strptime(siteReleaseDate, '%b %d, %Y')
        except Exception as e:
            self.log('UPDATE:: Error getting Release Date, reset to Filename Year: %s', e)
            siteReleaseDate = datetime.datetime.strptime(metadata.id.split('|')[1], '%d/%m/%Y')
        finally:
            metadata.originally_available_at = siteReleaseDate
            metadata.year = metadata.originally_available_at.year
            self.log('UPDATE:: Release Date %s', metadata.originally_available_at)

        # 2b.   Summary (synopsis + Scene Breakdown + Comments)
        try:
            synopsis = html.xpath('//div[@id="synopsis"]/div/ul/li//text()')[0].strip()
            self.log('UPDATE:: Summary - Synopsis Found: %s', synopsis)
        except Exception as e:
            synopsis = ''
            self.log('UPDATE:: Summary - No Synopsis: %s', e) 

        try:
            scene = html.xpath('//div[@id="sceneinfo"]/ul/li//text()')[0] # will error if no scenebreakdown
            htmlscenes = html.xpath('//div[@id="sceneinfo"]/ul/li//text()')
            scene = ''
            for item in htmlscenes:
                scene += '{0}\n'.format(item)
            scene = 'Scene Breakdown:\n' + scene
            self.log('UPDATE:: Summary - Scene Breakdown Found: %s', scene)
        except Exception as e:
            scene = ''
            self.log('UPDATE:: Summary - No Scene Breakdown: %s', e)

        try:
            comment = html.xpath('//div[@id="commentsection"]/ul/li//text()')[0] # will error if no comments
            htmlcomments = html.xpath('//div[@id="commentsection"]/ul/li//text()')
            listEven = htmlcomments[::2] # Elements from htmlcomments starting from 0 iterating by 2
            listOdd = htmlcomments[1::2] # Elements from htmlcomments starting from 1 iterating by 2
            comment = ''
            for sceneNo, movie in zip(listEven, listOdd):
                comment += '{0} -- {1}\n'.format(sceneNo, movie)
            comment = 'Comments:\n' + comment
            self.log('UPDATE:: Summary - Comments Found: %s', comment)
        except Exception as e:
            comment =''
            self.log('UPDATE:: Summary - No Comments: %s', e)

        summary = synopsis + scene + comment
        if summary:
            metadata.summary = summary

        # 2c.   Cast
        try:
            castdict = {}
            htmlcastnames = html.xpath('//div[@class="castbox"]/p/a//text()')
            htmlcastphotos = html.xpath('//div[@class="castbox"]/p/a/img/@src')
            self.log('UPDATE:: %s Cast Names: %s', len(htmlcastnames), htmlcastnames)
            self.log('UPDATE:: %s Cast Photos: %s', len(htmlcastphotos), htmlcastphotos)
            for castname, castphoto in zip(htmlcastnames, htmlcastphotos):
                castdict[castname] = '' if 'nophoto' in castphoto else castphoto

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted (castdict): 
                role = metadata.roles.new()
                role.name = key
                role.photo = castdict[key]
        except Exception as e:
            self.log('UPDATE - Error getting Cast: %s', e)

        # 2d.   Directors
        try:
            directordict = {}
            htmldirector = html.xpath('//p[@class="bioheading" and text()="Directors"]//following-sibling::p[1]/a/text()')
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