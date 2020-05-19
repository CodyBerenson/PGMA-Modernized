# IAFD - (IAFD)
'''
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    22 Apr 2020   2020.04.22.01    Creation
    15 May 2020   2020.04.22.02    Corrected search string to account for titles that have a Colon in them
                                   added/merge matching string routines - filename, studio, release date
                                   included cast with non-sexual roles
    19 May 2020   2020.04.22.03    Corrected search to look past the results page and get the movie title page to find
                                   studio/release date as the results page only listed the distributor/production year
                                   updated date match function

---------------------------------------------------------------------------------------------------------------
'''
import datetime, calendar, linecache, platform, os, re, string, sys, urllib

# Version / Log Title 
VERSION_NO = '2020.04.22.03'
PLUGIN_LOG_TITLE = 'IAFD'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
# if title on website has a hyphen in its title that does not correspond to a colon replace it with an em dash in the corresponding position
FILEPATTERN = Prefs['regex']

# Seconds to pause after a network request was made, ensuring undue burden is not placed on the web server
DELAY = int(Prefs['delay'])

# URLS
BASE_URL = 'http://www.iafd.com'
BASE_SEARCH_URL = BASE_URL + '/results.asp?searchtype=comprehensive&searchstring={0}'

# Date Formats used by website
DATE_YMD = '%Y%m%d'
DATEFORMAT = '%b %d, %Y'
#----------------------------------------------------------------------------------------------------------------------------------
def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'

#----------------------------------------------------------------------------------------------------------------------------------
def ValidatePrefs():
    pass

#----------------------------------------------------------------------------------------------------------------------------------
class IAFD(Agent.Movies):
    name = 'Internet Adult Film Database'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms', 'com.plexapp.agents.GayAdultScenes']

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

    #-------------------------------------------------------------------------------------------------------------------------------
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

        myString = myString.replace(" - ", ": ")
        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString)
        return myString

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

            # Site Title URL Check
            try:
                siteURL = title.xpath('./td[1]/a/@href')[0]
                siteURL = ('/' if siteURL[0] != '/' else '') + siteURL
                siteURL = (BASE_URL if BASE_URL not in siteURL else '') + siteURL
                self.log('SEARCH:: Site Title url: %s', siteURL)
            except:
                self.log('SEARCH:: Error getting Site Title Url')

            # Search Website for date - date is in format yyyy
            try:
                siteReleaseDate = title.xpath('./td[2]/text()')[0].strip()
                self.log('SEARCH:: Site Release Date: %s', siteReleaseDate)
                try:
                    siteReleaseDate = self.matchReleaseDate(compareReleaseDate, siteReleaseDate)
                except Exception as e:
                    self.log('SEARCH:: Site Release Date: %s: Default to Filename Date', e)
                    siteReleaseDate = compareReleaseDate
            except:
                self.log('SEARCH:: Error getting Site Release Date: Default to Filename Date')
                siteReleaseDate = compareReleaseDate

            # Site Studio Check: IAFD lists distributor on main page, look in Site URL for this
            try:
                siteDistributor = title.xpath('./td[3]/text()')[0]
                self.log('SEARCH:: Site Distributor: %s', siteDistributor)
                html = HTML.ElementFromURL(siteURL, sleep=DELAY)
                siteStudio = html.xpath('//p[@class="bioheading" and text()="Studio"]//following-sibling::p[1]/a/text()')[0]
                try:
                    self.matchStudioName(compareStudio, siteStudio)
                except Exception as e:
                    self.log('SEARCH:: Site URL Studio: %s', e)
                    continue

                # get release date: if none recorded use main results page value
                try:
                    siteReleaseDate = html.xpath('//p[@class="bioheading" and text()="Release Date"]//following-sibling::p[1]/text()')[0].strip()
                    self.log('SEARCH:: Site URL Release Date: %s', siteReleaseDate)
                    try:
                        siteReleaseDate = self.matchReleaseDate(compareReleaseDate, siteReleaseDate)
                    except Exception as e:
                        self.log('SEARCH:: Site xURL Release Date: %s: Default to Filename Date', e)
                        siteReleaseDate = compareReleaseDate
                except:
                    self.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                    siteReleaseDate = compareReleaseDate

            except:
                self.log('SEARCH:: Error getting Site Studio')
                continue
            
            # we should have a match on studio, title and year now
            results.Append(MetadataSearchResult(id = siteURL + '|' + siteReleaseDate.strftime(DATE_YMD), name = saveTitle, score = 100, lang = lang))
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
        #        a. Studio               : From studio group of filename - no need to process this as is used to find it on website
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Tag line             : Corresponds to the url of movie
        #        d. Originally Available : set from metadata.id (search result)
        #        e. Content Rating       : Always X
        #    2.  Metadata retrieved from website
        #        b. Summary              : Synopsis, Scene Breakdown and Comments
        #        c. Cast                 : List of Actors and Photos (alphabetic order)
        #        d. Directors

        # 1a.   Studio - straight of the file name
        metadata.studio = group_studio
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = group_title
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = metadata.id.split('|')[0]
        metadata.originally_available_at = datetime.datetime.strptime(metadata.id.split('|')[1], DATE_YMD)
        metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Tagline: %s', metadata.tagline)
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)    

        # 1e.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 2a.   Summary (synopsis + Scene Breakdown + Comments)
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
            scene = '\nScene Breakdown:\n' + scene
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

        # 2b.   Cast
        try:
            castdict = {}
            htmlcastnames = html.xpath('//div[contains(@class,"castbox")]/p/a//text()')
            htmlcastphotos = html.xpath('//div[contains(@class,"castbox")]/p/a/img/@src')
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

        # 2c.   Directors
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