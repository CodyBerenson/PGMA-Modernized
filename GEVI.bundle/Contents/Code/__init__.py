#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# GEVI - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    07 Apr 2020   2019.12.25.7     Changed the agent to search past the first page of results
    08 Apr 2020   2019.12.25.8     Created new function to prepare the video title to build the search query
    12 Apr 2020   2019.12.25.9     removed line in updating countries as it raised an error in the logs
                                   logical error replacing full stops in title when preparing search string
    26 Apr 2020   2019.12.25.10    corrected search string: can only be 24 characters long and be comprised of full words
                                   search and replace of special characters in search string was not working correctly
    28 Apr 2020   2019.12.25.11    Failed to scrap for some titles, found errors stopped execution, so code placed in try: exception
                                   added no spaces comparison to studio found results
                                   Added Scene breakdown scrape to summary
                                   Added Ratings scrape
    08 May 2020   2019.12.25.12    Enhanced the creation of the search string and the search url to return fewer but more exact results
                                   added portugues, spanish, german - articles for removal from search title
                                   added/merge matching string routines - filename, studio, release date
                                   removed references from summary relating to where scene can be found in compilation or other movie
    28 May 2020   2019.12.25.13    Took into account Brackets () in Title - characters replaced by Space
                                   GEVI will now compare file studio name against both site distributor and site studio names
    01 Jun 2020   2019.06.01.14    Implemented translation of summary
                                   improved getIAFDActor search

-----------------------------------------------------------------------------------------------------------------------------------
'''
import datetime, linecache, platform, os, re, string, sys, urllib, unicodedata
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2019.12.25.14'
PLUGIN_LOG_TITLE = 'GEVI'

REGEX = Prefs['regex']

# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# The summary of the film title will be translated into this language
LANGUAGE = Prefs['language']

# detect the language the summary appears in on the web page
DETECT = Prefs['detect']

# URLS
BASE_URL = 'https://www.gayeroticvideoindex.com'
BASE_SEARCH_URL = BASE_URL + '/search.php?type=t&where=b&query={0}&Search=Search&page=1'

# Date Formats used by website
DATE_YMD = '%Y%m%d'
DATEFORMAT = '%Y%m%d'

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
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchFilename(self, filename):
        ''' return groups from filename regex match else return false '''
        pattern = re.compile(REGEX)
        matched = pattern.search(filename)
        if matched:
            groups = matched.groupdict()
            return groups['studio'], groups['title'], groups['year']
        else:
            raise Exception("File Name [{0}] not in the expected format: (Studio) - Title (Year)".format(filename))

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchStudioName(self, fileStudioName, siteStudioName):
        ''' match file studio name against website studio name: Boolean Return '''
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

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchReleaseDate(self, fileDate, siteDate):
        ''' match file year against website release date: return formatted site date if no error or default to formated file date '''
        if len(siteDate) == 4:      # a year has being provided - default to 31st December of that year
            siteDate = siteDate + '1231'
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

    # -------------------------------------------------------------------------------------------------------------------------------
    def NormaliseComparisonString(self, myString):
        ''' Normalise string for Comparison, strip all non alphanumeric characters, Vol., Volume, Part, and 1 in series '''
        # convert to lower case and trim
        myString = myString.strip().lower()

        # remove vol/volume/part and vol.1 etc wording as filenames dont have these to maintain a uniform search across all websites and remove all non alphanumeric characters
        myString = myString.replace('&', 'and').replace(' vol.', '').replace(' volume', '').replace(' part', '').replace(',', '')

        # remove all standalone "1's"
        regex = re.compile(r'(?<!\d)1(?!\d)')
        myString = regex.sub('', myString)

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Video title for search query '''
        self.log('SELF:: Original Search Query [{0}]'.format(myString))

        # convert to lower case and trim and strip diacritics - except ß which we replace with one s
        myString = myString.replace('ß', 's')
        myString = myString.lower().strip()
        myBackupString = myString

        nullChars = ["'", ',' '&', '!', '.', '#'] # to be replaced with null
        pattern = u'[{0}]'.format(''.join(nullChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            self.log('SELF:: Search Query:: Replacing characters in string. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, '', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            self.log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('SELF:: Search Query:: String has none of these {0}'.format(pattern))

        spaceChars = ['-', '–', '(', ')']  # to be replaced with space
        pattern = u'[{0}]'.format(''.join(spaceChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            self.log('SELF:: Search Query:: Replacing characters with Space. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, ' ', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            self.log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('SELF:: Search Query:: String has none of these {0}'.format(pattern))

        pattern = r'[0-9]'
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            numPos = matched.start()
            self.log('SELF:: Search Query:: Splitting at position [{0}]. Found one of these {1}'.format(numPos, pattern))
            myString = myString[:numPos]
            self.log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('SELF:: Search Query:: Split not attempted. String has none of these {0}'.format(pattern))

        # removal of (in)definitive articles in title as it messes GEVIs search algorithm - English, French and German
        # split myString at position of first separate digit e.g MY TITLE 7 - THE 7TH RETURN becomes MY TITLE
        try:
            eng = ['a', 'an', 'the']
            fre = ['un', 'une', 'des', 'le', 'la', 'les', "l'"]
            prt = ['um', 'uma', 'uns', 'umas', 'o', 'a', 'os', 'as']
            esp = ['un', 'una', 'unos', 'unas', 'el', 'la', 'los', 'las']
            ger = ['ein', 'eine', 'eines', 'einen', 'einem', 'einer', 'das', 'die', 'der', 'dem', 'den', 'des']
            pattern = eng + fre + prt + esp + ger
            myWords = myString.split()
            matched = myWords[0].lower() in pattern # match against first word
            if matched:
                self.log('SELF:: Search Query:: Dropping first word [{0}], Found one of these {1}'.format(myWords[0], pattern))
                myWords.remove(myWords[0])
                myString = ' '.join(myWords)
                self.log('SELF:: Amended Search Query [{0}]'.format(myString))
            else:
                self.log('SELF:: Search Query:: First word has none of these {0}'.format(pattern))
        except Exception as e:
            self.log('SELF:: Error removing initial (in)definitive articles: %s', e)

        # all preparation has resulted in an empty string e.g title like 35 & Up by Bacchus Releasing
        myString = re.sub(r'[^A-Za-z]', '', myBackupString) if not myString else myString

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString.strip())

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myString = myString.replace('%25', '%').replace('*', '')

        # GEVI uses a maximum of 24 characters when searching
        myString = myString[:24].strip()
        myString = myString if myString[-1] != '%' else myString[:23]
        self.log('SELF:: Amended Search Query [{0}]'.format(myString))

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def TranslateString(self, myString):
        ''' Determine if translation should be done '''
        myString = myString.strip()
        if myString:
            translator = Translator()
            runTranslation = (LANGUAGE != 'en')
            self.log('SELF:: Default Language: [%s], Run Translation: [%s]', LANGUAGE, runTranslation)
            if DETECT:
                detected = translator.detect(myString)
                runTranslation = (LANGUAGE != detected.lang)
                self.log('SELF:: Detect source Language: [%s] Run Translation: [%s]', detected.lang, runTranslation)
            myString = translator.translate(myString, dest=LANGUAGE).text if runTranslation else myString
            self.log('SELF:: Translated [%s] Summary Found: %s', runTranslation, myString)

        return myString if myString else ' '     # return single space to initialise metadata summary field

    # -------------------------------------------------------------------------------------------------------------------------------
    def getIAFDActorImage(self, myString, FilmYear):
        ''' check IAFD web site for better quality actor thumbnails irrespective of whether we have a thumbnail or not '''

        actorname = myString
        myString = String.StripDiacritics(myString).lower()

        # build list containing three possible cast links 1. Full Search in case of AKAs 2. as Performer 3. as Director
        # the 2nd and 3rd links will only be used if there is no search result
        urlList = []
        fullname = myString.replace(' ', '').replace("'", '').replace(".", '')
        full_name = myString.replace(' ', '-').replace("'", '&apos;')
        for gender in ['m', 'd']:
            url = 'http://www.iafd.com/person.rme/perfid={0}/gender={1}/{2}.htm'.format(fullname, gender, full_name)
            urlList.append(url)

        myString = String.URLEncode(myString)
        url = 'http://www.iafd.com/results.asp?searchtype=comprehensive&searchstring={0}'.format(myString)
        urlList.append(url)

        for count, url in enumerate(urlList, start=1):
            photourl = ''
            try:
                self.log('SELF:: %s. IAFD Actor search string [ %s ]', count, url)
                html = HTML.ElementFromURL(url)
                if 'gender=' in url:
                    career = html.xpath('//p[.="Years Active"]/following-sibling::p[1]/text()[normalize-space()]')[0]
                    try:
                        startCareer = career.split('-')[0]
                        self.log('SELF:: Actor: %s  Start of Career: [ %s ]', actorname, startCareer)
                        if startCareer <= FilmYear:
                            photourl = html.xpath('//*[@id="headshot"]/img/@src')[0]
                            photourl = 'nophoto' if 'nophoto' in photourl else photourl
                            self.log('SELF:: Search %s Result: IAFD Photo URL [ %s ]', count, photourl)
                            break
                    except:
                        continue
                else:
                    xPathString = '//table[@id="tblMal" or @id="tblDir"]/tbody/tr/td[contains(normalize-space(.),"{0}")]/parent::tr'.format(actorname)
                    actorList = html.xpath(xPathString)
                    for actor in actorList:
                        try:
                            startCareer = actor.xpath('./td[4]/text()[normalize-space()]')[0]
                            self.log('SELF:: Actor: %s  Start of Career: [ %s ]', actorname, startCareer)
                            if startCareer <= FilmYear:
                                photourl = actor.xpath('./td[1]/a/img/@src')[0]
                                photourl = 'nophoto' if photourl == 'http://www.iafd.com/graphics/headshots/thumbs/th_iafd_ad.gif' else photourl
                                self.log('SELF:: Search %s Result: IAFD Photo URL [ %s ]', count, photourl)
                                break
                        except:
                            continue
                    break
            except Exception as e:
                photourl = ''
                self.log('SELF:: Search %s Result: Could not retrieve IAFD Actor Page, %s', count, e)
                continue

        return photourl

    # -------------------------------------------------------------------------------------------------------------------------------
    def log(self, message, *args):
        ''' log messages '''
        Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])

        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version         : v.%s', VERSION_NO)
        self.log('SEARCH:: Python          : %s', sys.version_info)
        self.log('SEARCH:: Platform        : %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Prefs->delay    : %s', DELAY)
        self.log('SEARCH::      ->detect   : %s', DETECT)
        self.log('SEARCH::      ->language : %s', LANGUAGE)
        self.log('SEARCH::      ->regex    : %s', REGEX)
        self.log('SEARCH:: media.title     : %s', media.title)
        self.log('SEARCH:: File Name       : %s', filename)
        self.log('SEARCH:: File Folder     : %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check filename format
        try:
            FilmStudio, FilmTitle, FilmYear = self.matchFilename(filename)
            self.log('SEARCH:: Processing: Studio: %s   Title: %s   Year: %s', FilmStudio, FilmTitle, FilmYear)
        except Exception as e:
            self.log('SEARCH:: Skipping %s', e)
            return

        # Compare Variables used to check against the studio name on website: remove all umlauts, accents and ligatures
        compareStudio = self.NormaliseComparisonString(FilmStudio)
        compareTitle = self.NormaliseComparisonString(FilmTitle)
        compareReleaseDate = datetime.datetime(int(FilmYear), 12, 31) # default to 31 Dec of Filename yesr

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        searchTitle = self.CleanSearchString(FilmTitle)
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
                morePages = True if pageNumber <= 10 else False
            except:
                searchQuery = ''
                self.log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            titleList = html.xpath('//table[contains(@class,"d")]/tr/td[@class="cd"]/parent::tr')
            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))

            for title in titleList:
                # Site Title
                try:
                    siteTitle = title[0].text_content().strip()
                    siteTitle = self.NormaliseComparisonString(siteTitle)
                    self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
                    if siteTitle != compareTitle:
                        continue
                except:
                    self.log('SEARCH:: Error getting Site Title')
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('.//a/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    self.log('SEARCH:: Site Title url: %s', siteURL)
                except:
                    self.log('SEARCH:: Error getting Site Title Url')
                    continue

                # Access Site URL for Studio and Release Date information
                try:
                    html = HTML.ElementFromURL(siteURL, sleep=DELAY)
                except Exception as e:
                    self.log('SEARCH:: Error reading Site URL page: %s', e)
                    continue

                # Site Studio/Distributor
                try:
                    foundStudio = False

                    htmlSiteStudio = html.xpath('//a[contains(@href, "/C/")]/parent::td//text()[normalize-space()]')
                    htmlSiteStudio = [x.strip() for x in htmlSiteStudio]
                    htmlSiteStudio = list(set(htmlSiteStudio))
                    self.log('SEARCH:: %s Site URL Distributor/Studio: %s', len(htmlSiteStudio), htmlSiteStudio)
                    for siteStudio in htmlSiteStudio:
                        try:
                            self.log('SEARCH:: Studio: %s Compare against: %s', compareStudio, siteStudio)
                            self.matchStudioName(compareStudio, siteStudio)
                            foundStudio = True
                        except Exception as e:
                            self.log('SEARCH:: Error: %s', e)
                            continue
                        if foundStudio:
                            break

                    if not foundStudio:
                        self.log('SEARCH:: Error No Matching Site Studio')
                        continue

                except Exception as e:
                    self.log('SEARCH:: Error getting Site Studio %s', e)
                    continue

                # Release Date
                try:
                    foundReleaseDate = False
                    siteReleaseDate = ''

                    # get the release dates - if not numeric replace with file year
                    htmlReleaseDate = html.xpath('//td[.="released" or .="produced"]/following-sibling::td[1]/text()[normalize-space()]')
                    htmlReleaseDate = [x if unicode(x, 'utf-8').isnumeric() else x.split('-')[0] if '-' in x else x.split(',')[0] if ',' in x else FilmYear for x in htmlReleaseDate]
                    htmlReleaseDate = list(set(htmlReleaseDate))
                    self.log('SEARCH:: %s Site URL Release Dates: %s', len(htmlReleaseDate), htmlReleaseDate)
                    for ReleaseDate in htmlReleaseDate:
                        try:
                            self.log('SEARCH:: Release Date: %s Compare against: %s', compareReleaseDate, ReleaseDate)
                            ReleaseDate = self.matchReleaseDate(compareReleaseDate, ReleaseDate)
                            foundReleaseDate = True
                            siteReleaseDate = ReleaseDate
                        except Exception as e:
                            self.log('SEARCH:: Error: %s', e)
                            continue
                        if foundReleaseDate:
                            break

                    if not foundReleaseDate:
                        self.log('SEARCH:: Error No Matching Site Release Date')
                        continue


                except Exception as e:
                    self.log('SEARCH:: Error getting Release Date %s', e)
                    continue

                # we should have a match on studio, title and year now
                results.Append(MetadataSearchResult(id=siteURL + '|' + siteReleaseDate.strftime(DATE_YMD), name=FilmTitle, score=100, lang=lang))
                return

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log('-----------------------------------------------------------------------')
        self.log('UPDATE:: Version    : v.%s', VERSION_NO)
        self.log('UPDATE:: File Name  : %s', filename)
        self.log('UPDATE:: File Folder: %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check filename format
        try:
            FilmStudio, FilmTitle, FilmYear = self.matchFilename(filename)
            self.log('UPDATE:: Processing: Studio: %s   Title: %s   Year: %s', FilmStudio, FilmTitle, FilmYear)
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
        #        b. Countries            : Alphabetic order
        #        c. Rating
        #        d. Directors            : List of Directors (alphabetic order)
        #        e. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        f. Genre
        #        g. Posters/Background

        # 1a.   Studio - straight of the file name
        metadata.studio = FilmStudio
        self.log('UPDATE:: Studio: %s' % metadata.studio)

        # 1b.   Set Title
        metadata.title = FilmTitle
        self.log('UPDATE:: Video Title: %s' % metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = metadata.id.split('|')[0]
        metadata.originally_available_at = datetime.datetime.strptime(metadata.id.split('|')[1], DATE_YMD)
        metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Tagline: %s', metadata.tagline)
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)

        # 1e.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 2a.   Summary = Promo + Scenes + Action Notes
        try:
            promo = ''
            htmlpromo = html.xpath('//td[contains(text(),"promo/")]//following-sibling::td//span[@style]/text()[following::br]')
            for item in htmlpromo:
                promo = '{0}\n{1}'.format(promo, item)
            self.log('UPDATE:: Promo Found: %s', promo)
        except Exception as e:
            promo = ''
            self.log('UPDATE:: Error getting Promo: %s', e)

        # action notes
        try:
            htmlactionnotes = html.xpath('//td[@class="sfn"]//text()')
            actionnotes = ''.join(htmlactionnotes).replace('\n', '')
            self.log('UPDATE:: Action Notes: %s', actionnotes)
        except Exception as e:
            actionnotes = ''
            self.log('UPDATE:: Error getting Action Notes: %s', e)

        # scenes
        try:
            htmlscenes = html.xpath('//td[contains(text(),"scenes /")]//following-sibling::td//div')
            scenes = '' if htmlscenes else '\nScenes: {0}'.format(actionnotes)
            for item in htmlscenes:
                scenes = '{0}\n{1}'.format(scenes, item.text_content().strip())
            self.log('UPDATE:: Scenes Found: %s', scenes)
        except Exception as e:
            scenes = ''
            self.log('UPDATE:: Error getting Scenes: %s', e)

        # combine and update
        summary = promo + scenes
        regex = r'View this scene at.*|found in compilation.*|see also.*'
        pattern = re.compile(regex, re.IGNORECASE)
        summary = re.sub(pattern, '', summary)
        metadata.summary = self.TranslateString(summary)

        # 2b.   Countries
        try:
            countries = []
            htmlcountries = html.xpath('//td[contains(text(),"location")]//following-sibling::td[1]/text()')
            self.log('UPDATE:: Countries List %s', htmlcountries)
            for country in htmlcountries:
                country = country.strip()
                if country:
                    countries.append(country)

            countries.sort()
            metadata.countries.clear()
            for country in countries:
                metadata.countries.add(country)
        except Exception as e:
            self.log('UPDATE:: Error getting Countries(ies): %s', e)

        # 2c.   Rating (out of 4 Stars) = Rating can be a maximum of 10 - float value
        try:
            rating = html.xpath('//td[contains(text(),"rating out of 4")]//following-sibling::td[1]/text()')[0].strip()
            rating = rating.count('*') * 2.5
            self.log('UPDATE:: Film Rating %s', rating)
            metadata.rating = rating
        except Exception as e:
            self.log('UPDATE:: Error getting Rating: %s', e)

        # 2d.   Directors
        try:
            directors = []
            htmldirector = html.xpath('//td[contains(text(),"director")]//following-sibling::td[1]/a/text()')
            self.log('UPDATE:: Director List %s', htmldirector)
            for directorname in htmldirector:
                director = directorname.strip()
                if director:
                    directors.append(director)

            directors.sort()
            metadata.directors.clear()
            for director in directors:
                Director = metadata.directors.new()
                Director.name = director
        except Exception as e:
            self.log('UPDATE:: Error getting Director(s): %s', e)

        # 2e.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        try:
            castdict = {}
            htmlcast = html.xpath('//td[@class="pd"]/a/text()')
            for castname in htmlcast:
                cast = castname.strip()
                if not cast:
                    continue
                if '(' in cast:
                    cast = cast.split('(')[0]
                castdict[cast] = self.getIAFDActorImage(cast, FilmYear)
                castdict[cast] = '' if castdict[cast] == 'nophoto' else castdict[cast]

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted(castdict):
                role = metadata.roles.new()
                role.name = key
                role.photo = castdict[key]
        except Exception as e:
            self.log('UPDATE - Error getting Cast: %s', e)

        # 2f.   Genre
        try:
            genres = []
            htmlgenres = html.xpath('//td[contains(text(),"category")]//following-sibling::td[1]/text()')
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                genre = genre.strip()
                if genre:
                    genres.append(genre)

            genres.sort()
            metadata.genres.clear()
            for genre in genres:
                metadata.genres.add(genre)
        except Exception as e:
            self.log('UPDATE:: Error getting Genres: %s', e)

        # 2g.   Posters/Background Art
        try:
            htmlimages = html.xpath('//td[@class="gp"]/a/@href')
            posterImages = htmlimages if len(htmlimages) == 1 else htmlimages[::2]          # assume poster images first
            backgroundImages = htmlimages if len(htmlimages) == 1 else htmlimages[1::2]     # are followed by their background images

            validPosterList = []
            for image in posterImages:
                image = (BASE_URL if BASE_URL not in image else '') + image
                self.log('UPDATE:: Movie Poster Found: %s', image)
                validPosterList.append(image)
                if image not in metadata.posters:
                    metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
                #  clean up and only keep the poster we have added
                metadata.posters.validate_keys(validPosterList)

            validArtList = []
            for image in backgroundImages:
                image = (BASE_URL if BASE_URL not in image else '') + image
                self.log('UPDATE:: Movie Background Art Found: %s', image)
                validArtList.append(image)
                if image not in metadata.art:
                    metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
                #  clean up and only keep the Art we have added
                metadata.art.validate_keys(validArtList)
        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Background Art: %s', e)
