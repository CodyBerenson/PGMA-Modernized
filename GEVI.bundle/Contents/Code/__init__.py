#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# GEVI - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    07 Oct 2020   2019.12.25.21    IAFD - change to https
                                   GEVI now searches all returned results and stops if return is alphabetically greater than title
    22 Nov 2020   2019.12.25.22    Improved generation of search string - previously titles like The 1000 Load Fuck would not match
                                   as both first word and second word can not be used to search for movies in GEVI. i.e numeric and indefinite article
    26 Dec 2020   2020.12.25.23    Improved on IAFD search, actors sexual roles if recorded are returned, if not shows a red circle.
                                   if actor is not credited on IAFD but is on Agent Site it shows as a Yellow Box below the actor
                                   sped up search by removing search by actor/director... less hits on IAFD per actor...
    09 Jan 2021   2020.12.25.24    Adjusted poster/background image collection as website xpath had changed
                                   change to the collection of images - first image is now poster, second image defaults to backgroun
                                   image 3 onwards are added to both collections to give a choice.
    09 Jan 2021   2020.12.25.25    change of xpath to images - website changed way images were placed
    09 Feb 2021   2020.12.25.27    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including LevenShtein Matching on Cast names
                                   set content_rating age to 18
                                   Set collections from filename + countries, cast and directors
                                   Added directors photos
                                   included studio on iafd processing of filename
                                   Added iafd legend to summary
                                   improved logging

-----------------------------------------------------------------------------------------------------------------------------------
'''
import datetime, platform, os, re, sys, json
from unidecode import unidecode
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2019.12.25.27'
PLUGIN_LOG_TITLE = 'GEVI'
LOG_BIGLINE = '------------------------------------------------------------------------------'
LOG_SUBLINE = '      ------------------------------------------------------------------------'

# Preferences
REGEX = Prefs['regex']                      # file matching pattern
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
IAFD_LEGEND = u'CAST LEGEND\u2003{0} Actor not on IAFD\u2003{1} Actor on IAFD\u2003:: {2} Film on IAFD ::\n'

# URLS
BASE_URL = 'https://www.gayeroticvideoindex.com'
BASE_SEARCH_URL = BASE_URL + '/search.php?type=t&where=b&query={0}&Search=Search&page=1'

# dictionary holding film variables
FILMDICT = {}

# Date Formats used by website
DATEFORMAT = '%Y%m%d'

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
class GEVI(Agent.Movies):
    ''' define Agent class '''
    name = 'GEVI (IAFD)'
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # import IAFD Functions
    from iafd import *

    # import General Functions
    from genfunctions import *

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        self.log('AGNT  :: Original Search Query        : {0}'.format(myString))

        # convert to lower case and trim
        myString = myString.lower().strip()
        myBackupString = myString

        # replace & with and
        if ' & ' in myString:
            self.log('AGNT  :: Search Query:: Replacing characters in string. Found " & "')
            myString = myString.replace(' & ', ' and ')
            self.log('AGNT  :: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('AGNT  :: Search Query:: String has no " & "')

        # replace following with null
        nullChars = ["'", ',', '!', '.', '#'] # to be replaced with null
        pattern = u'[{0}]'.format(''.join(nullChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            self.log('AGNT  :: Search Query:: Replacing characters in string. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, '', myString)
            self.log('AGNT  :: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('AGNT  :: Search Query:: String has none of these {0}'.format(pattern))

        spaceChars = ['-', ur'\u2013', ur'\u2014', '(', ')']  # to be replaced with space
        pattern = u'[{0}]'.format(''.join(spaceChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            self.log('AGNT  :: Search Query:: Replacing characters with Space. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, ' ', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            self.log('AGNT  :: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('AGNT  :: Search Query:: String has none of these {0}'.format(pattern))

        # examine first word
        # remove if numerical or indefinite word in french, english, portuguese, spanish, german
        numbers = ['[0-9]+']
        eng = ['a', 'an', 'the']
        fre = ['un', 'une', 'des', 'le', 'la', 'les', "l'"]
        prt = ['um', 'uma', 'uns', 'umas', 'o', 'a', 'os', 'as']
        esp = ['un', 'una', 'unos', 'unas', 'el', 'la', 'los', 'las']
        ger = ['ein', 'eine', 'eines', 'einen', 'einem', 'einer', 'das', 'die', 'der', 'dem', 'den', 'des']
        oth = ['mr']
        regexes = numbers + eng + fre + prt + esp + ger + oth
        pattern = r'|'.join(r'\b{0}\b'.format(regex) for regex in regexes)
        while True:
            myWords = myString.split()
            matched = re.search(pattern, myWords[0].lower())  # match against first word
            if matched:
                self.log("AGNT  :: Search Query:: Dropping first word [{0}]".format(myWords[0]))
                myWords.remove(myWords[0])
                myString = ' '.join(myWords)
                self.log('AGNT  :: Amended Search Query [{0}]'.format(myString))
            else:
                self.log("AGNT  :: Search Query:: Did not match against first word [{0}]".format(myWords[0]))
                break

        # examine string for numbers and &
        pattern = r'[0-9&]'
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            numPos = matched.start()
            self.log('AGNT  :: Search Query:: Splitting at position [{0}]. Found one of these {1}'.format(numPos, pattern))
            myString = myString[:numPos]
            self.log('AGNT  :: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('AGNT  :: Search Query:: Split not attempted. String has none of these {0}'.format(pattern))

        # all preparation has resulted in an empty string e.g title like 35 & Up by Bacchus Releasing
        myString = re.sub(r'[^A-Za-z]', ' ', myBackupString) if not myString else myString

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myString = myString.replace('%25', '%').replace('*', '')

        # GEVI uses a maximum of 24 characters when searching
        myString = myString[:24].strip()
        myString = myString if myString[-1] != '%' else myString[:23]
        self.log('AGNT  :: Returned Search Query        : {0}'.format(myString))
        self.log(LOG_BIGLINE)

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])

        self.log(LOG_BIGLINE)
        self.log('SEARCH:: Version                      : v.%s', VERSION_NO)
        self.log('SEARCH:: Python                       : %s', sys.version_info)
        self.log('SEARCH:: Platform                     : %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Preferences:')
        self.log('SEARCH::  > Cast Legend Before Summary: %s', PREFIXLEGEND)
        self.log('SEARCH::  > Collection Gathering')
        self.log('SEARCH::      > Cast                  : %s', COLCAST)
        self.log('SEARCH::      > Director(s)           : %s', COLDIRECTOR)
        self.log('SEARCH::      > Studio                : %s', COLSTUDIO)
        self.log('SEARCH::      > Film Title            : %s', COLTITLE)
        self.log('SEARCH::      > Genres                : %s', COLGENRE)
        self.log('SEARCH::  > Delay                     : %s', DELAY)
        self.log('SEARCH::  > Language Detection        : %s', DETECT)
        self.log('SEARCH::  > Library:Site Language     : %s:%s', lang, SITE_LANGUAGE)
        self.log('SEARCH:: Media Title                  : %s', media.title)
        self.log('SEARCH:: File Name                    : %s', filename)
        self.log('SEARCH:: File Folder                  : %s', folder)
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
        searchTitle = self.CleanSearchString(FILMDICT['SearchTitle'])
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
                searchQuery = html.xpath('//a[text()="Next"]/@href')[0]
                searchQuery = "{0}/{1}".format(BASE_URL, searchQuery)   # href does not have base_url in it
                self.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(searchQuery.split('&where')[0].split('page=')[1]) - 1
                morePages = True
            except:
                searchQuery = ''
                self.log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            titleList = html.xpath('//table[contains(@class,"d")]/tr/td[@class="cd"]/parent::tr')
            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
            self.log(LOG_BIGLINE)
            for title in titleList:
                # Site Title
                try:
                    siteTitle = title[0].text_content().strip()
                    self.matchTitle(siteTitle, FILMDICT)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Title: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('.//a/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    FILMDICT['SiteURL'] = siteURL
                    self.log('SEARCH:: Site Title url                %s', siteURL)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Title Url: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # Site Title Type (Compilation)
                try:
                    siteType = title[4].text_content().strip()
                    FILMDICT['Compilation'] = "Yes" if siteType.lower() == 'compilation' else "No"
                    self.log('SEARCH:: Compilation?                  %s', FILMDICT['Compilation'])
                    self.log(LOG_BIGLINE)
                except:
                    self.log('SEARCH:: Error getting Site Type (Compilation)')
                    continue

                # Access Site URL for Studio and Release Date information
                try:
                    self.log('SEARCH:: Reading Site URL page         %s', siteURL)
                    html = HTML.ElementFromURL(siteURL, sleep=DELAY)
                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error reading Site URL page: %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # Site Studio/Distributor
                try:
                    foundStudio = False
                    htmlSiteStudio = html.xpath('//a[contains(@href, "/C/")]/parent::td//text()[normalize-space()]')
                    htmlSiteStudio = [x.strip() for x in htmlSiteStudio if x.strip()]
                    htmlSiteStudio = list(set(htmlSiteStudio))
                    self.log('SEARCH:: Site URL Distributor/Studio   %s', htmlSiteStudio)
                    for siteStudio in htmlSiteStudio:
                        try:
                            self.matchStudio(siteStudio, FILMDICT)
                            foundStudio = True
                        except Exception as e:
                            self.log('SEARCH:: Error: %s', e)
                            self.log(LOG_SUBLINE)
                            continue
                        if foundStudio:
                            break

                    if not foundStudio:
                        self.log('SEARCH:: Error No Matching Site Studio')
                        self.log(LOG_SUBLINE)
                        continue

                    self.log(LOG_BIGLINE)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Studio %s', e)
                    self.log(LOG_SUBLINE)
                    continue

                # Release Date
                siteReleaseDate = ''
                releaseDateMatchFail = False
                try:
                    htmlReleaseDate = html.xpath('//td[.="released" or .="produced"]/following-sibling::td[1]/text()[normalize-space()]')
                    htmlReleaseDate = [x if unicode(x, 'utf-8').isnumeric() else x.split('-')[0] if '-' in x else x.split(',')[0] if ',' in x else x[1:] if x[0] == 'c' else '' for x in htmlReleaseDate]
                    htmlReleaseDate = [x.strip() for x in htmlReleaseDate if x]
                    htmlReleaseDate = list(set(htmlReleaseDate))
                    self.log('SEARCH:: Site URL Release Dates        %s', htmlReleaseDate)
                    for ReleaseDate in htmlReleaseDate:
                        try:
                            ReleaseDate = self.matchReleaseDate(ReleaseDate, FILMDICT)
                            siteReleaseDate = ReleaseDate
                            break
                        except Exception as e:
                            self.log('SEARCH:: Error: %s', e)
                            releaseDateMatchFail = True
                            continue
                    if not siteReleaseDate:
                        raise Exception('No Release Dates Found')

                    self.log(LOG_BIGLINE)

                except Exception as e:
                    self.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date [%s]', e)
                    self.log(LOG_SUBLINE)
                    if releaseDateMatchFail:
                        continue

                # we should have a match on studio, title and year now
                self.log(LOG_BIGLINE)
                self.log('SEARCH:: Finished Search Routine')
                self.log(LOG_BIGLINE)
                results.Append(MetadataSearchResult(id=json.dumps(FILMDICT), name=FILMDICT['Title'], score=100, lang=lang))
                return

        self.log(LOG_BIGLINE)
        self.log('SEARCH:: Finished Search Routine')
        self.log(LOG_BIGLINE)

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
        #        a. Genre                : Alphabetic order
        #        b. Countries            : Alphabetic order
        #        c. Rating
        #        d. Directors            : List of Directors (alphabetic order)
        #        e. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        f. Posters/Background
        #        g. Summary

        # 2a.   Genre
        self.log(LOG_BIGLINE)
        try:
            htmlgenres = html.xpath('//td[contains(text(),"category")]//following-sibling::td[1]/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort()
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            metadata.genres.clear()
            for genre in htmlgenres:
                metadata.genres.add(genre)
                # add genres to collection
                if COLGENRE:
                    metadata.collections.add(genre)

        except Exception as e:
            self.log('UPDATE:: Error getting Genres: %s', e)

        # 2b.   Rating (out of 4 Stars) = Rating can be a maximum of 10 - float value
        self.log(LOG_BIGLINE)
        try:
            rating = html.xpath('//td[contains(text(),"rating out of 4")]//following-sibling::td[1]/text()')[0].strip()
            rating = rating.count('*') * 2.5
            self.log('UPDATE:: Film Rating %s', rating)
            metadata.rating = rating

        except Exception as e:
            metadata.rating = 0.0
            self.log('UPDATE:: Error getting Rating: %s', e)

        # 2c.   Countries
        self.log(LOG_BIGLINE)
        try:
            htmlcountries = html.xpath('//td[contains(text(),"location")]//following-sibling::td[1]/text()')
            htmlcountries = [x.strip() for x in htmlcountries if x.strip()]
            htmlcountries.sort()
            self.log('UPDATE:: Countries List %s', htmlcountries)
            metadata.countries.clear()
            for country in htmlcountries:
                metadata.countries.add(country)
                # add country to collection
                if COLCOUNTRY:
                    metadata.collections.add(country)

        except Exception as e:
            self.log('UPDATE:: Error getting Countries: %s', e)

        # 2d.   Directors
        self.log(LOG_BIGLINE)
        try:
            htmldirectors = html.xpath('//td[contains(text(),"director")]//following-sibling::td[1]/a/text()')
            htmldirectors = ['{0}'.format(x.strip()) for x in htmldirectors if x.strip()]
            self.log('UPDATE:: Director List %s', htmldirectors)
            directorDict = self.getIAFD_Director(htmldirectors, FILMDICT)
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

        # 2e.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        self.log(LOG_BIGLINE)
        try:
            htmlcast = html.xpath('//td[@class="pd"]/a/text()')
            castdict = self.ProcessIAFD(htmlcast, FILMDICT)

            # sort the dictionary and add key(Name)- value(Photo, Role) to metadata
            metadata.roles.clear()
            for key in sorted(castdict):
                newRole = metadata.roles.new()
                newRole.name = key
                newRole.photo = castdict[key]['Photo']
                newRole.role = castdict[key]['Role']
                # add cast name to collection
                if COLCAST:
                    metadata.collections.add(key)

        except Exception as e:
            self.log('UPDATE:: Error getting Cast: %s', e)

        # 2f.   Posters/Background Art
        #       GEVI does not distinguish between poster and back ground images - we assume first image is poster and second is background
        #           if there is only 1 image - apply it to both
        self.log(LOG_BIGLINE)
        try:
            htmlimages = html.xpath('//img/@src[contains(.,"Covers")]')
            htmlimages = [(BASE_URL if BASE_URL not in image else '') + image.replace('/Icons/','/') for image in htmlimages] 
            if len(htmlimages) == 1:    # if only one image duplicate it
                htmlimages.append(htmlimages[0])

            image = htmlimages[0]
            self.log('UPDATE:: Poster Image Found: [1] - %s', image)
            metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.posters.validate_keys([image])

            image = htmlimages[1]
            self.log('UPDATE:: Art Image Found: [2] - %s', image)
            metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            metadata.art.validate_keys([image])

        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Art: %s', e)

        # 2g.   Summary = IAFD Legend + Synopsis + Scene Information
        # synopsis
        self.log(LOG_BIGLINE)
        try:
            synopsis = ''
            htmlpromo = html.xpath('//td[contains(text(),"promo/")]//following-sibling::td//span[@style]/text()[following::br]')
            for item in htmlpromo:
                synopsis = '{0}\n{1}'.format(synopsis, item)
            self.log('UPDATE:: Promo Found: %s', synopsis)
            synopsis = synopsis.replace('\n', ' ')
        except Exception as e:
            synopsis = ''
            self.log('UPDATE:: Error getting Promo: %s', e)

        # Legend
        self.log(LOG_SUBLINE)
        try:
            htmllegend = html.xpath('//td[@class="sfn"]//text()')
            legend = ''.join(htmllegend).replace('\n', '')
            self.log('UPDATE:: Legend: %s', legend)
        except Exception as e:
            legend = ''
            self.log('UPDATE:: Error getting Legend: %s', e)
        finally:
            legend = 'Legend: {0}'.format(legend.strip()) if legend else ''

        # scenes
        self.log(LOG_SUBLINE)
        try:
            htmlscenes = html.xpath('//td[@class="scene"]')
            allscenes = ''
            for item in htmlscenes:
                allscenes = '{0}\n{1}'.format(allscenes, ''.join(item.itertext()).strip())
            allscenes = allscenes.strip()
            self.log('UPDATE:: Scenes Found: %s', allscenes)
        except Exception as e:
            allscenes = ''
            self.log('UPDATE:: Error getting Scenes: %s', e)

        legend = legend if allscenes else ''
        synopsis = "{0}\n{1}\n{2}".format(synopsis, legend, allscenes)
        synopsis = self.NormaliseUnicode(synopsis)
        regex = r'View this scene at.*|found in compilation.*|see also.*'
        pattern = re.compile(regex, re.IGNORECASE)
        synopsis = re.sub(pattern, '', synopsis)
        
        # combine and update
        self.log(LOG_SUBLINE)
        castLegend = IAFD_LEGEND.format(IAFD_ABSENT, IAFD_FOUND, IAFD_THUMBSUP if FILMDICT['FoundOnIAFD'] == "Yes" else IAFD_THUMBSDOWN)
        summary = ('{0}\n{1}' if PREFIXLEGEND else '{1}\n{0}').format(castLegend, synopsis.strip())
        summary = summary.replace('\n\n', '\n')
        metadata.summary = self.TranslateString(summary, lang)

        self.log(LOG_BIGLINE)
        self.log('UPDATE:: Finished Update Routine')
        self.log(LOG_BIGLINE)