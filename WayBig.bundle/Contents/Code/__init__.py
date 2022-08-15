#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# WayBig (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    22 Dec 2019   2019.12.22.1     Corrected scrapping of collections
    14 Aug 2020   2019.08.12.21    Change to regex matching code - site titles which had studio name in them were failing to match to 
                                   file titles as regex was different between the two
    22 Sep 2020   2019.08.12.22    correction to summary xpath to cater for different layouts
    07 Oct 2020   2019.08.12.23    IAFD - change to https
    28 Feb 2021   2019.08.12.25    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including Levenshtein Matching on Cast names
                                   Added iafd legend to summary
    27 Mar 2021   2019.08.12.26    Site Title had spaces removed before normalisation - caused matching failure
                                   Site Studio was been set to [-1] rather than the last element of the site entry split, so Studio always matched
    21 Apr 2021   2019.08.12.27    Posters with url extention .webp - renamed to .jpg
    25 Apr 2021   2019.08.12.28    removed regex pref, search string length only has full words, json unicode issues, added to title/studio matching
    25 Apr 2021   2019.08.12.29    Issue #96 - changed title sort so that 'title 21' sorts differently to 'title 12'
                                   duration matching with iafd entries as iafd has scene titles that match with film titles
                                   use of ast module to avoid unicode issues in some libraries
                                   Removal of REGEX preference
                                   code reorganisation like moving logging fuction out of class so it can be used by all imports
    11 May 2021   2019.08.12.30    Further code reorganisation
    29 Jul 2021   2019.08.12.31    Further code reorganisation
    04 Feb 2022   2019.08.12.32    implemented change suggested by Cody: duration matching optional on IAFD matching
                                   Cast list if used in filename becomes the default that is matched against IAFD, useful in case no cast is listed in agent
    27 Feb 2022   2019.08.12.33    Solved issue #123
                                   tags with colons in them are excluded from cast list
    08 Mar 2022   2019.08.12.34    Solved Reopened issue #123
                                   tags with colons in them are excluded from cast list
    15 Jul 2022   2019.08.12.35    Solved xPath change for Site entries - noticed by Cody
                                   - updated utils.py to latest version to use new routines.
---------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2019.12.22.35'
AGENT = 'WayBig'

# Plex System Variables/Methods
PlexSupportPath = Core.app_support_path
PlexLoadFile = Core.storage.load

# log section separators
LOG_BIGLINE = '---------------------------------------------------------------------------------'
LOG_SUBLINE = '      ---------------------------------------------------------------------------'
LOG_ASTLINE = '*********************************************************************************'

# Preferences
COLCAST = Prefs['castcollection']                   # add cast to collection
COLCLEAR = Prefs['clearcollections']                # clear previously set collections
COLCOUNTRY = Prefs['countrycollection']             # add country to collection
COLDIRECTOR = Prefs['directorcollection']           # add director to collection
COLGENRE = Prefs['genrecollection']                 # add genres to collection
COLSTUDIO = Prefs['studiocollection']               # add studio name to collection
COLSERIES = Prefs['seriescollection']               # add series to collection
DELAY = int(Prefs['delay'])                         # Delay used when requesting HTML, may be good to have to prevent being banned from the site
DETECT = Prefs['detect']                            # detect the language the summary appears in on the web page
DURATIONDX = int(Prefs['durationdx'])               # Acceptable difference between actual duration of video file and that on agent website
MATCHIAFDDURATION = Prefs['matchiafdduration']      # Match against IAFD Duration value
MATCHSITEDURATION = Prefs['matchsiteduration']      # Match against Site Duration value
PREFIXLEGEND = Prefs['prefixlegend']                # place cast legend at start of summary or end

# PLEX API /CROP Script/online image cropper
CROPPER = r'CScript.exe "{0}/Plex Media Server/Plug-ins/BestExclusivePorn.bundle/Contents/Code/ImageCropper.vbs" "{1}" "{2}" "{3}" "{4}"'
THUMBOR = Prefs['thumbor'] + "/0x0:{0}x{1}/{2}"

# URLS
BASE_URL = 'https://www.waybig.com'
BASE_SEARCH_URL = BASE_URL + '/blog/index.php?s={0}'

# dictionary holding film variables
FILMDICT = {}

# Date Formats used by website
DATEFORMAT = '%B %d, %Y'

# Website Language
SITE_LANGUAGE = 'en'
# ----------------------------------------------------------------------------------------------------------------------------------
# imports placed here to use previously declared variables
import utils

# ----------------------------------------------------------------------------------------------------------------------------------
def Start():
    ''' initialise process '''
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'

# ----------------------------------------------------------------------------------------------------------------------------------
def ValidatePrefs():
    ''' Validate Changed Preferences '''
    pass

# ----------------------------------------------------------------------------------------------------------------------------------
def anyOf(iterable):
    '''  used for matching strings in lists '''
    for element in iterable:
        if element:
            return element
    return None

# ----------------------------------------------------------------------------------------------------------------------------------
class WayBig(Agent.Movies):
    ''' define Agent class '''
    name = 'WayBig (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultScenes']

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        '''  clean search string before searching on WayBig '''
        utils.log('AGENT :: {0:<29} {1}'.format('Original Search Query', myString))

        myString = myString.lower().strip()

        # for titles with "- " replace with ":"
        if '- ' in myString:
            myString = myString.replace(' - ', ': ')
            myString = myString.replace('- ', ': ')
            utils.log('AGENT :: Search Query:: Replaced Minus-Dash sequence with Colon')

        # replace curly apostrophes with straight as strip diacritics will remove these
        quoteChars = [ur'‘', ur'’', ur'\u2018', ur'\u2019']
        pattern = u'({0})'.format('|'.join(quoteChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            myString = re.sub(pattern, "'", myString)
            myString = ' '.join(myString.split())   # remove continous white space
            utils.log('AGENT :: Search Query:: Replaced characters in string. Found one of these {0}'.format(quoteChars))
            utils.log('AGENT :: Amended Search Query [{0}]'.format(myString))

        # WayBig seems to fail to find Titles which have invalid chars in them, split at first incident and take first split, just to search but not compare
        # the back tick is added to the list as users who can not include quotes in their filenames can use these to replace them without changing the scrappers code
        badChars = ["'", '"', '`', ur'\u201c', ur'\u201d']
        pattern = u'({0})'.format('|'.join(badChars))
        myWords = myString.split()
        for count, word in enumerate(myWords):
            matched = re.search(pattern, word) # match against first word
            if matched:
                myWords.remove(myWords[count])
                utils.log('AGENT :: Search Query:: Dropped word {0} "{1}". Found one of these {2} characters'.format(count, word, badChars))
                myString = ' '.join(myWords)
                utils.log('AGENT :: Amended Search Query [{0}]'.format(myString))

        # string can not be longer than 50 characters
        if len(myString) > 50:
            lastSpace = myString[:50].rfind(' ')
            myString = myString[:lastSpace]
            utils.log('AGENT :: Search Query:: Query length trimmed > 50 Characters')

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myString = myString.replace('%25', '%').replace('*', '')

        utils.log('AGENT :: {0:<29} {1}'.format('Returned Search Query', myString))
        utils.log(LOG_BIGLINE)

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            utils.log('SEARCH:: {0:<29} {1}'.format('Error: Missing Media Item File', 'QUIT'))
            return

        #clear-cache directive
        if media.name == "clear-cache":  
            HTTP.ClearCache()
            results.Append(MetadataSearchResult(id='clear-cache', name='Plex web cache cleared', year=media.year, lang=lang, score=0))
            utils.log('SEARCH:: {0:<29} {1}'.format('Warning: Clear Cache Directive Encountered', 'QUIT'))
            return

        utils.logHeader('SEARCH', media, lang)

        # Check filename format
        try:
            FILMDICT = utils.matchFilename(media)
            FILMDICT['lang'] = lang
            FILMDICT['Agent'] = AGENT
        except Exception as e:
            utils.log('SEARCH:: Error: %s', e)
            return

        utils.log(LOG_BIGLINE)

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        # strip studio name from title to use in comparison
        utils.log('SEARCH:: Search Title: %s', searchTitle)
        regex = ur'^{0} |at {0}$'.format(re.escape(FILMDICT['CompareStudio']))
        pattern = re.compile(regex, re.IGNORECASE)
        compareTitle = re.sub(pattern, '', searchTitle)
        compareTitle = utils.NormaliseComparisonString(compareTitle)

        utils.log('SEARCH:: Search Title: %s', searchTitle)

        morePages = True
        while morePages:
            utils.log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
            except Exception as e:
                utils.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                return

            try:
                searchQuery = html.xpath('//div[@class="nav-links"]/a[@class="next page-numbers"]/@href')[0]
                utils.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(html.xpath('//div[@class="nav-links"]/span[@class="page-numbers current"]/text()[normalize-space()]')[0])
                morePages = True if pageNumber <= 10 else False
            except:
                searchQuery = ''
                utils.log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            titleList = html.xpath('.//div[@class="row"]/div[@class="content-col col"]/article')
            titleListLength = len(titleList)
            utils.log('SEARCH:: {0:<29} {1}'.format('Titles Found', '{0} Processing Results Page: {1:>2}'.format(titleListLength, pageNumber)))
            utils.log(LOG_BIGLINE)
            for idx, title in enumerate(titleList, start=1):
                utils.log('SEARCH:: {0:<29} {1}'.format('Processing', '{0} of {1} for {2} - {3}'.format(idx, titleListLength, FILMDICT['Studio'], FILMDICT['Title'])))
                # Site Entry
                utils.log(LOG_BIGLINE)
                try:
                    siteEntry = title.xpath('./a/*[@class="entry-title"]/text()')[0].strip()
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Entry', siteEntry))
                    # prepare the Site Entry
                    singleQuotes = ["`", "‘", "’"]
                    pattern = ur'[{0}]'.format(''.join(singleQuotes))
                    siteEntry = re.sub(pattern, "'", siteEntry)
                    # the siteEntry usual has the format Studio: Title
                    siteEntry = siteEntry.lower()
                    if ' at ' in siteEntry and ': ' in siteEntry and (siteEntry.endswith("'") or siteEntry.endswith('"')):       # err 123
                        utils.log('SEARCH:: Matched " at ", ": " and %s ends with apostrophe in Site entry', re.match(siteEntry, '[\'"]$'))
                        siteStudio, siteTitle = siteEntry.split(': ', 1)
                    elif ' at ' in siteEntry:
                        utils.log('SEARCH:: Matched " at " in Site entry')
                        siteTitle, siteStudio = siteEntry.rsplit(' at ', 1)
                    elif ': ' in siteEntry:
                        utils.log('SEARCH:: Matched ": " Site entry')
                        siteStudio, siteTitle = siteEntry.split(': ', 1)
                        # none standard titles
                    elif ' on ' in siteEntry:
                        utils.log('SEARCH:: Matched " on " in Site entry')
                        siteTitle, siteStudio = siteEntry.rsplit(' on ', 1)
                    elif '? ' in siteEntry:
                        utils.log('SEARCH:: Matched "? " in Site entry')
                        siteStudio, siteTitle = siteEntry.split('? ', 1)
                    elif ', ' in siteEntry:
                        utils.log('SEARCH:: Matched ", " in Site entry')
                        siteStudio, siteTitle = siteEntry.split(', ', 1)
                    elif FILMDICT['Studio'].lower() in siteEntry:       # in case the film title is mssing a separator between the studio and clip name
                        utils.log('SEARCH:: Warning: Site Entry did not have a clear separator to separate Studio from Title')
                        siteStudio = FILMDICT['Studio'].lower()
                        siteTitle = FILMDICT['Title'].lower() if FILMDICT['Title'].lower() in siteEntry else ''
                    else:
                        utils.log('SEARCH:: Error determining Site Studio and Title from Site Entry')
                        utils.log(LOG_SUBLINE)
                        continue

                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Entry: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Title
                utils.log(LOG_BIGLINE)
                try:
                    utils.matchTitle(siteTitle, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # Studio Name
                utils.log(LOG_BIGLINE)
                try:
                    utils.matchStudio(siteStudio, FILMDICT)
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Studio: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Title URL
                utils.log(LOG_BIGLINE)
                try:
                    siteURL = title.xpath('./a[@rel="bookmark"]/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    FILMDICT['SiteURL'] = siteURL
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', siteURL))
                except Exception as e:
                    utils.log('SEARCH:: Error getting Site Title Url: %s', e)
                    utils.log(LOG_SUBLINE)
                    continue

                # Site Release Date
                utils.log(LOG_BIGLINE)
                try:
                    siteReleaseDate = title.xpath('./div/span[@class="meta-date"]/strong/text()[normalize-space()]')[0]
                    utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Release Date', siteReleaseDate))
                    try:
                        siteReleaseDate = datetime.strptime(siteReleaseDate, DATEFORMAT)
                        siteReleaseDate = utils.matchReleaseDate(siteReleaseDate, FILMDICT)
                    except Exception as e:
                        utils.log('SEARCH:: Error getting Site URL Release Date: %s', e)
                        utils.log(LOG_SUBLINE)
                        continue
                except:
                    utils.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')

                # we should have a match on studio, title and year now. Find corresponding film on IAFD
                utils.log(LOG_BIGLINE)
                utils.log('SEARCH:: Check for Film on IAFD:')
                utils.getFilmOnIAFD(FILMDICT)

                FILMDICT['id'] = media.id
                myID = json.dumps(FILMDICT, default=utils.jsonDumper)
                results.Append(MetadataSearchResult(id=myID, name=FILMDICT['Title'], score=100, lang=lang))
                utils.logFooter('SEARCH', FILMDICT)
                return


    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        utils.logHeader('UPDATE', media, lang)

        utils.log('UPDATE:: Convert Date Time & Set Objects:')
        FILMDICT = json.loads(metadata.id, object_hook=utils.jsonLoader)
        utils.log(LOG_BIGLINE)

        utils.printFilmInformation(FILMDICT)
        utils.log(LOG_BIGLINE)

        # Fetch HTML. - if this fails abandon the update!!!!
        try:
            webURL = FILMDICT['SiteURL']
            html = HTML.ElementFromURL(webURL, timeout=60, errors='ignore', sleep=DELAY)
        except Exception as e:
            utils.log('UPDATE:: Error - Failed to Load Film Title Page; Abandon Update Process: %s', e)
            return

        # The following bits of metadata need to be established and used to update the movie on plex
        #   1.  Metadata that is set by Agent as default
        #       a. Studio               : From studio group of filename - no need to process this as above
        #       b. Title                : From title group of filename - no need to process this as is used to find it on website
        #       c. Tag line             : Corresponds to the url of film
        #       d. Originally Available : set from metadata.id (search result)
        #       e. Content Rating       : Always X
        #       f. Content Rating Age   : Always 18
        #       g. Collection Info      : From title group of filename 
        metadata = utils.setDefaultMetadata(metadata, FILMDICT)
        utils.log(LOG_BIGLINE)

        #    2.  Metadata retrieved from website
        #        a.   Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        b.   Posters/Art
        #        c.   Summary

        # 2a. Tags - Waybigs stores the cast as tags
        utils.log(LOG_BIGLINE)
        castList = []
        try:
            ignoreCast = ['British', 'Furry', 'Hairy', 'Hawaiian', 'Solo', 'U.K', 'United Kingdom']
            htmlcast = html.xpath('//a[contains(@href,"https://www.waybig.com/blog/tag/")]/text()')
            htmlcast = [x.replace(u'\u2019s', '') for x in htmlcast]
            htmlcast = list(set(htmlcast))

            # remove all tags with non name characters such as colons
            htmlcast = [x for x in htmlcast if not ':' in x]
            htmlcast = [x for x in htmlcast if not x + ':' in FILMDICT['Title']]
            # remove File Studio Name
            htmlcast = [x for x in htmlcast if not '.tv' in x.lower()]
            htmlcast = [x for x in htmlcast if not '.com' in x.lower()]
            htmlcast = [x for x in htmlcast if not '.net' in x.lower()]
            htmlcast = [x for x in htmlcast if not FILMDICT['Studio'].replace(' ', '').lower() in x.replace(' ', '').lower()]

            # actors will have initial capitals for names
            for count, cast in enumerate(htmlcast):
                words = cast.split()
                wordcount = len(words)
                words = [x for x in words if x[0].isupper() and (x[1].islower() or x[1]=="'")] # cater for irish style names like O'Leary
                capcount = len(words)
                htmlcast[count] = cast if wordcount == capcount else ''

            htmlcast = [x for x in htmlcast if x]

            for cast in htmlcast:
                if anyOf(x in cast for x in ignoreCast):
                    continue
                castList.append(cast)

        except Exception as e:
            utils.log('UPDATE:: Error getting Cast: No Tags Found, Get Cast from Film Title: %s', e)
            pattern = u'([A-Z]\w+(?=[\s\-][A-Z])(?:[\s\-][A-Z]\w*)+)'
            matches = re.findall(pattern, FILMDICT['Title'])  # match against Film title
            utils.log('UPDATE:: Matches:: {0}'.format(matches))
            if matches:
                for count, castname in enumerate(matches, 1):
                    utils.log('UPDATE:: {0}. Found Possible Cast Name: {1}'.format(count, castname))
                    if castname:
                        castList.append(castname)

        try:
            castDict = utils.getCast(castList, FILMDICT)
            # sort the dictionary and add key(Name)- value(Photo, Role) to metadata
            metadata.roles.clear()
            for key in sorted(castDict):
                newRole = metadata.roles.new()
                newRole.name = key
                newRole.photo = castDict[key]['Photo']
                newRole.role = castDict[key]['Role']
                # add cast name to collection
                if COLCAST:
                    metadata.collections.add(key)

        except Exception as e:
            utils.log('UPDATE:: Error getting Cast: %s', e)

        # 2c.   Posters/Art - First Image set to Poster, next to Art
        utils.log(LOG_BIGLINE)
        imageType = 'Poster & Art'
        try:
            htmlimages = html.xpath('//a[@target="_self" or @target="_blank"]/img[(@height or @width) and @alt and contains(@src, "zing.waybig.com/reviews")]/@src')
            if len(htmlimages) == 1:
                htmlimages.append(htmlimages[0])
            utils.log('UPDATE:: %s Images Found: %s', len(htmlimages), htmlimages)
            for index, image in enumerate(htmlimages):
                image = image.replace('.webp', '.jpg')      # change extension of url image
                if index > 1:
                    break
                whRatio = 1.5 if index == 0 else 0.5625
                imageType = 'Poster' if index == 0 else 'Art'
                pic, picContent = utils.getFilmImages(imageType, image, whRatio)    # height is 1.5 times the width for posters
                if index == 0:      # processing posters
                    #  clean up and only keep the posters we have added
                    metadata.posters[pic] = Proxy.Media(picContent, sort_order=1)
                    metadata.posters.validate_keys([pic])
                    utils.log(LOG_SUBLINE)
                else:               # processing art
                    metadata.art[pic] = Proxy.Media(picContent, sort_order=1)
                    metadata.art.validate_keys([pic])

        except Exception as e:
            utils.log('UPDATE:: Error getting %s: %s', imageType, e)

        # 2a.   Summary = IAFD Legend + Synopsis
        # synopsis
        synopsis = ''
        try:
            htmlsynopsis = html.xpath('//div[@class="entry-content"]/p[not(descendant::script) and not(contains(., "Watch as"))]')
            for item in htmlsynopsis:
                synopsis = '{0}{1}\n'.format(synopsis, item.text_content())
            utils.log('UPDATE:: Synopsis Found: %s', synopsis)
            pattern = re.compile(r'Watch.*at.*', re.IGNORECASE)
            synopsis = re.sub(pattern, '', synopsis)
            synopsis = utils.TranslateString(synopsis, SITE_LANGUAGE, lang, DETECT)
        except Exception as e:
            utils.log('UPDATE:: Error getting Synopsis: %s', e)

        # combine and update
        utils.log(LOG_SUBLINE)
        summary = ('{0}\n{1}' if PREFIXLEGEND else '{1}\n{0}').format(FILMDICT['Legend'], synopsis.strip())
        summary = summary.replace('\n\n', '\n')
        utils.log('UPDATE:: Summary with Legend: %s', summary)
        metadata.summary = summary

        utils.log(LOG_ASTLINE)
        utils.log('UPDATE:: %s', 'Finished Update Routine'.center(72))
        utils.log(LOG_ASTLINE)
        return
