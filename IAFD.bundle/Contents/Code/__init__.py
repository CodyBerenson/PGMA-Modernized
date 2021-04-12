#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# IAFD - (IAFD)
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
    01 Jun 2020   2020.04.22.04    Implemented translation of summary
                                   put back scrape from local media assets
    27 Jun 2020   2020.04.22.05    Improvement to Summary Translation: Translate into Plex Library Language
                                   stripping of intenet domain suffixes from studio names when matching
                                   handling of unicode characters in film titles and comparision string normalisation
    12 Sep 2020   2020.04.22.06    Titles with hyphens failing as these were converted to ":"
                                   corrected by splitting and using string upto that position as search...
    20 Sep 2020   2020.04.22.07    Titles with '[', '(' were corrected by splitting and using string upto that position as search...
    07 Oct 2020   2020.04.22.08    IAFD - change to https
    07 Mar 2021   2020.04.22.10    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including Levenshtein Matching on Cast names
                                   Added iafd legend to summary
    28 Mar 2021   2020.04.22.11    Added code to create actor collections

---------------------------------------------------------------------------------------------------------------
'''
import datetime, platform, os, re, sys, json
from unidecode import unidecode
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2020.04.22.11'
PLUGIN_LOG_TITLE = 'IAFD'
LOG_BIGLINE = '------------------------------------------------------------------------------'
LOG_SUBLINE = '      ------------------------------------------------------------------------'

# Preferences
REGEX = Prefs['regex']                      # file matching pattern
YEAR = Prefs['year']                        # is year mandatory in the filename?
DELAY = int(Prefs['delay'])                 # Delay used when requesting HTML, may be good to have to prevent being banned from the site
DETECT = Prefs['detect']                    # detect the language the summary appears in on the web page
PREFIXLEGEND = Prefs['prefixlegend']        # place cast legend at start of summary or end
COLCLEAR = Prefs['clearcollections']        # clear previously set collections
COLSTUDIO = Prefs['studiocollection']       # add studio name to collection
COLTITLE = Prefs['titlecollection']         # add title [parts] to collection
COLGENRE = Prefs['genrecollection']         # add genres to collection
COLDIRECTOR = Prefs['directorcollection']   # add director to collection
COLCAST = Prefs['castcollection']           # add cast to collection
COLCOUNTRY = Prefs['countrycollection']     # add country to collection

# IAFD Related variables
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/results.asp?searchtype=comprehensive&searchstring={0}'

IAFD_ABSENT = u'\U0000274C'        # red cross mark - not on IAFD
IAFD_FOUND = u'\U00002705'         # heavy white tick on green - on IAFD
IAFD_THUMBSUP = u'\U0001F44D'      # thumbs up unicode character
IAFD_THUMBSDOWN = u'\U0001F44E'    # thumbs down unicode character
IAFD_LEGEND = u'CAST LEGEND\u2003{0} Actor not on IAFD\u2003{1} Actor on IAFD\u2003:: {2} Film on IAFD ::'

# dictionary holding film variables
FILMDICT = {}

# Date Formats used by website
DATEFORMAT = '%b %d, %Y'

# Website Language
SITE_LANGUAGE = 'en'

# ----------------------------------------------------------------------------------------------------------------------------------
def Start():
    ''' initialise process '''
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'

# ----------------------------------------------------------------------------------------------------------------------------------
def ValidatePrefs():
    ''' validate changed user preferences '''
    pass

# ----------------------------------------------------------------------------------------------------------------------------------
def anyOf(iterable):
    '''  used for matching strings in lists '''
    for element in iterable:
        if element:
            return element
    return None

# ----------------------------------------------------------------------------------------------------------------------------------
class IAFD(Agent.Movies):
    ''' define Agent class '''
    name = 'Internet Adult Film Database'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms', 'com.plexapp.agents.GayAdultScenes']
    accepts_from = ['com.plexapp.agents.localmedia']

    # import General Functions
    from genfunctions import *

    #-------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        self.log('AGNT  :: Original Search Query        : {0}'.format(myString))

        myString = myString.strip().lower()

        # split and take up to first occurence of character
        splitChars = ['-', '[', '(', ur'\u2013', ur'\u2014']
        pattern = u'[{0}]'.format(''.join(splitChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            numPos = matched.start()
            self.log('SELF:: Search Query:: Splitting at position [{0}]. Found one of these {1}'.format(numPos, pattern))
            myString = myString[:numPos]
            self.log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('SELF:: Search Query:: Split not attempted. String has none of these {0}'.format(pattern))

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString)

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        myString = myString.replace('%25', '%').replace('*', '')

        self.log('AGNT  :: Returned Search Query        : {0}'.format(myString))

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])

        self.log(LOG_BIGLINE)
        self.log('SEARCH:: Version                       : v.%s', VERSION_NO)
        self.log('SEARCH:: Python                        : %s', sys.version_info)
        self.log('SEARCH:: Platform                      : %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Preferences:')
        self.log('SEARCH::  > Cast Legend Before Summary : %s', PREFIXLEGEND)
        self.log('SEARCH::  > Collection Gathering')
        self.log('SEARCH::      > Cast                   : %s', COLCAST)
        self.log('SEARCH::      > Director(s)            : %s', COLDIRECTOR)
        self.log('SEARCH::      > Studio                 : %s', COLSTUDIO)
        self.log('SEARCH::      > Film Title             : %s', COLTITLE)
        self.log('SEARCH::      > Genres                 : %s', COLGENRE)
        self.log('SEARCH::  > Delay                      : %s', DELAY)
        self.log('SEARCH::  > Language Detection         : %s', DETECT)
        self.log('SEARCH::  > Library:Site Language      : %s:%s', lang, SITE_LANGUAGE)
        self.log('SEARCH:: Media Title                   : %s', media.title)
        self.log('SEARCH:: File Name                     : %s', filename)
        self.log('SEARCH:: File Folder                   : %s', folder)
        self.log(LOG_BIGLINE)

        # Check filename format
        try:
            FILMDICT = self.matchFilename(filename)
        except Exception as e:
            self.log('SEARCH:: Error: %s', e)
            return
        self.log(LOG_BIGLINE)

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['IAFDTitle'])
        searchQuery = IAFD_SEARCH_URL.format(searchTitle)
        self.log('SEARCH:: Search Query: %s', searchQuery)

        # iafd displays the first 50 results, clicking on "See More Results"  appends the rest
        try:
            html = HTML.ElementFromURL(searchQuery, timeout=90, errors='ignore', sleep=DELAY)
        except Exception as e:
            self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
            return

        try:
            searchQuery = html.xpath('//a[text()="See More Results..."]/@href')[0].strip()
            if IAFD_BASE not in searchQuery:
                searchQuery = IAFD_BASE + '/' + searchQuery
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
                self.matchTitle(siteTitle, FILMDICT)
                self.log(LOG_BIGLINE)
            except Exception as e:
                self.log('SEARCH:: Error getting Site Title; Try AKA Site Title: %s', e)
                self.log(LOG_SUBLINE)
                try:
                    siteAKATitle = title.xpath('./td[4]/text()')[0]
                    self.matchTitle(siteAKATitle, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting AKA Site Title: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

            # Site Title URL Check
            try:
                siteURL = title.xpath('./td[1]/a/@href')[0]
                siteURL = ('/' if siteURL[0] != '/' else '') + siteURL
                siteURL = (IAFD_BASE if IAFD_BASE not in siteURL else '') + siteURL
                FILMDICT['SiteURL'] = siteURL
                self.log('SEARCH:: Site Title url                %s', siteURL)
                self.log(LOG_BIGLINE)
            except Exception as e:
                self.log('SEARCH:: Error getting Site Title Url: %s', e)
                self.log(LOG_SUBLINE)
                continue

            # Search Website for date - date is in format yyyy
            firstdateMatch = True
            try:
                siteReleaseDate = title.xpath('./td[2]/text()')[0].strip()
                try:
                    siteReleaseDate = self.matchReleaseDate(siteReleaseDate, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Release Date: %s', e)
                    self.log(LOG_SUBLINE)
                    firstdateMatch = False
            except Exception as e:
                self.log('SEARCH:: Error getting Site Release Date: Default to Filename Date [%s]', e)
                self.log(LOG_BIGLINE)

            # Site Studio Check: IAFD lists distributor on main page, look in Site URL for this
            # Access Site URL for Studio Name information and release date
            try:
                self.log('SEARCH:: Reading Site URL page         %s', siteURL)
                html = HTML.ElementFromURL(siteURL, sleep=DELAY)
                self.log(LOG_BIGLINE)
            except Exception as e:
                self.log('SEARCH:: Error reading Site URL page: %s', e)
                self.log(LOG_SUBLINE)
                continue

            # Studio Name
            try:
                siteStudio = html.xpath('//p[@class="bioheading" and text()="Studio"]//following-sibling::p[1]/a/text()')[0]
                self.matchStudio(siteStudio, FILMDICT)
                self.log(LOG_BIGLINE)
            except Exception as e:
                self.log('SEARCH:: Error getting Site Studio; Try Distributor: %s', e)
                try:
                    siteDistributor = html.xpath('//p[@class="bioheading" and text()="Distributor"]//following-sibling::p[1]/a/text()')[0]
                    self.matchStudio(siteDistributor, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Distributor: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

            # get release date: if none recorded use main results page value
            try:
                siteReleaseDate = html.xpath('//p[@class="bioheading" and text()="Release Date"]//following-sibling::p[1]/text()')[0].strip()
                try:
                    siteReleaseDate = self.matchReleaseDate(siteReleaseDate, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Release Date: %s', e)
                    self.log(LOG_SUBLINE)
                    if not firstdateMatch:  # if the first match also failed.... skip this title
                        continue
            except Exception as e:
                self.log('SEARCH:: Error getting Site Release Date: Default to Filename Date [%s]', e)
                self.log(LOG_BIGLINE)

            # we should have a match on studio, title and year now
            FILMDICT['FoundOnIAFD'] = 'Yes'
            self.log('SEARCH:: Finished Search Routine')
            self.log(LOG_BIGLINE)
            results.Append(MetadataSearchResult(id=json.dumps(FILMDICT), name=FILMDICT['Title'], score=100, lang=lang))
            return

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log(LOG_BIGLINE)
        self.log('UPDATE:: Version                      : v.%s', VERSION_NO)
        self.log('UPDATE:: File Name                    : %s', filename)
        self.log('UPDATE:: File Folder                  : %s', folder)
        self.log(LOG_BIGLINE)

        # Fetch HTML.
        FILMDICT = json.loads(metadata.id)
        self.log('UPDATE:: Film Dictionary Variables:')
        for key in sorted(FILMDICT.keys()):
            self.log('UPDATE:: {0: <29}: {1}'.format(key, FILMDICT[key]))
        self.log(LOG_BIGLINE)

        html = HTML.ElementFromURL(FILMDICT['SiteURL'], timeout=60, errors='ignore', sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as above
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Tag line             : Corresponds to the url of movie
        #        d. Originally Available : set from metadata.id (search result)
        #        e. Content Rating       : Always X
        #        f. Content Rating Age   : Always 18
        #        g. Collection Info      : From title group of filename 

        # 1a.   Set Studio
        metadata.studio = FILMDICT['Studio']
        self.log('UPDATE:: Studio: %s' , metadata.studio)

        # 1b.   Set Title
        metadata.title = FILMDICT['Title']
        self.log('UPDATE:: Title: %s' , metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = FILMDICT['SiteURL']
        if 'CompareDate' in FILMDICT:
            metadata.originally_available_at = datetime.datetime.strptime(FILMDICT['CompareDate'], DATEFORMAT)
            metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Tagline: %s', metadata.tagline)
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)

        # 1e/f. Set Content Rating to Adult/18 years
        metadata.content_rating = 'X'
        metadata.content_rating_age = 18
        self.log('UPDATE:: Content Rating - Content Rating Age: X - 18')

        # 1g. Collection
        if COLCLEAR:
            metadata.collections.clear()

        collections = FILMDICT['Collection']
        for collection in collections:
            metadata.collections.add(collection)
        self.log('UPDATE:: Collection Set From filename: %s', collections)

        #    2.  Metadata retrieved from website
        #        a. Directors
        #        b. Cast                 : List of Actors and Photos (alphabetic order)
        #        c. Summary              : Synopsis, Scene Breakdown and Comments

        # 2a.   Directors
        self.log(LOG_BIGLINE)
        try:
            directorDict = {}
            htmldirectors = html.xpath('//p[@class="bioheading" and text()="Directors"]//following-sibling::p[1]')
            for director in htmldirectors:
                directorName = director.xpath('./a/text()')[0]
                directorURL = director.xpath('./a/@href')[0]
                try:
                    dhtml = HTML.ElementFromURL(directorURL, sleep=DELAY)
                    try:
                        directorPhoto = dhtml.xpath('//div[@class="headshot"]/img/@src')[0]
                        directorPhoto = '' if 'nophoto' in directorPhoto else directorPhoto
                    except Exception as e:
                        directorPhoto = ''
                except Exception as e:
                    self.log('UPDATE:: Error getting Director Page: %s', e)

                self.log('UPDATE:: Director Name:               \t%s', directorName)
                self.log('UPDATE:: Director URL:                \t%s', directorURL)
                self.log('UPDATE:: Director Photo:              \t%s', directorPhoto)
                self.log(LOG_SUBLINE)

                directorDict[directorName] = directorPhoto

            # sort the dictionary and add kv to metadata
            metadata.directors.clear()
            for key in sorted(directorDict):
                newDirector = metadata.directors.new()
                newDirector.name = key
                newDirector.photo = directorDict[key]
                # add director to collection
                if COLDIRECTOR:
                    metadata.collections.add(key)
        except Exception as e:
            self.log('UPDATE:: Error getting Director(s): %s', e)


        # 2b.   Cast
        self.log(LOG_BIGLINE)
        castdict = {}
        try:
            htmlcast = html.xpath('//h3[.="Performers"]/ancestor::div[@class="panel panel-default"]//div[@class[contains(.,"castbox")]]/p')
            for cast in htmlcast:
                actorName = cast.xpath('./a/text()')[0].strip()
                actorURL = IAFD_BASE + cast.xpath('./a/@href')[0]
                actorPhoto = cast.xpath('./a/img/@src')[0].strip()
                actorPhoto = '' if 'nophoto' in actorPhoto else actorPhoto
                actorRole = cast.xpath('./text()')
                actorRole = ' '.join(actorRole).strip()

                try:
                    actorAlias = cast.xpath('./i/text()')[0].split(':')[1].replace(')', '').strip()
                except:
                    actorAlias = ''
                    pass

                actorRole = 'AKA: {0}'.format(actorAlias) if actorAlias else IAFD_FOUND

                self.log('UPDATE:: Actor Name:                  \t%s', actorName)
                self.log('UPDATE:: Actor Alias:                 \t%s', actorAlias)
                self.log('UPDATE:: Actor URL:                   \t%s', actorURL)
                self.log('UPDATE:: Actor Photo:                 \t%s', actorPhoto)
                self.log('UPDATE:: Actor Role:                  \t%s', actorRole)
                self.log(LOG_SUBLINE)

                myDict = {}
                myDict['Photo'] = actorPhoto
                myDict['Role'] = actorRole
                castdict[actorName] = myDict

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted(castdict):
                cast = metadata.roles.new()
                cast.name = key
                cast.photo = castdict[key]['Photo']
                cast.role = castdict[key]['Role']
                # add cast name to collection
                if COLCAST:
                    metadata.collections.add(key)

        except Exception as e:
            self.log('UPDATE:: Error getting Cast: %s', e)

        # 2c.   Summary (IAFD Legend + synopsis + Scene Breakdown + Comments)
        self.log(LOG_BIGLINE)
        # synopsis
        try:
            synopsis = html.xpath('//div[@id="synopsis"]/div/ul/li//text()')[0].strip()
            self.log('UPDATE:: Summary - Synopsis Found: %s', synopsis)
        except Exception as e:
            synopsis = ''
            self.log('UPDATE:: Error getting Synopsis: %s', e)

        # scenes
        self.log(LOG_SUBLINE)
        try:
            scene = html.xpath('//div[@id="sceneinfo"]/ul/li//text()')[0] # will error if no scenebreakdown
            htmlscenes = html.xpath('//div[@id="sceneinfo"]/ul/li//text()')
            scene = ''
            for item in htmlscenes:
                scene += '{0}\n'.format(item)
            scene = '\nScene Breakdown:\n' + scene
            self.log('UPDATE:: Scene Breakdown Found: %s', scene)
        except Exception as e:
            scene = ''
            self.log('UPDATE:: Error getting Scene Breakdown: %s', e)

        # comments
        self.log(LOG_SUBLINE)
        try:
            comment = html.xpath('//div[@id="commentsection"]/ul/li//text()')[0] # will error if no comments
            htmlcomments = html.xpath('//div[@id="commentsection"]/ul/li//text()')
            listEven = htmlcomments[::2] # Elements from htmlcomments starting from 0 iterating by 2
            listOdd = htmlcomments[1::2] # Elements from htmlcomments starting from 1 iterating by 2
            comment = ''
            for sceneNo, movie in zip(listEven, listOdd):
                comment += '{0} -- {1}\n'.format(sceneNo, movie)
            comment = 'Comments:\n' + comment
            self.log('UPDATE:: Comments Found: %s', comment)
        except Exception as e:
            comment = ''
            self.log('UPDATE:: Error getting Comments: %s', e)

        # combine and update
        self.log(LOG_SUBLINE)
        castLegend = IAFD_LEGEND.format(IAFD_ABSENT, IAFD_FOUND, IAFD_THUMBSUP if FILMDICT['FoundOnIAFD'] == "Yes" else IAFD_THUMBSDOWN)
        summary = ('{0}\n{1}\n{2}\n{3}' if PREFIXLEGEND else '{1}\n{2}\n{3}\n{0}').format(castLegend, synopsis.strip(), scene.strip(), comment.strip())
        summary = summary.replace('\n\n', '\n')
        metadata.summary = self.TranslateString(summary, lang)

        self.log(LOG_BIGLINE)
        self.log('UPDATE:: Finished Update Routine')
        self.log(LOG_BIGLINE)