#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# GayDVDEmpire (IAFD)
                                    Version History
                                    ---------------
    Date            Version             Modification
    13 Apr 2020   2019.08.12.03    Corrected scrapping of collections
    14 Apr 2020   2019.08.12.04    sped up search routine, corrected tagline
                                   search multiple result pages
    01 Jun 2020   2019.08.12.05    Implemented translation of summary
                                   improved getIAFDActor search
    27 Jun 2020   2019.08.12.06    Improvement to Summary Translation: Translate into Plex Library Language
                                   stripping of internet domain suffixes from studio names when matching
                                   handling of unicode characters in film titles and comparision string normalisation
    30 Aug 2020   2019.08.12.07    Handling of Roman Numerals in Titles to Match Arabic Numerals
                                   Errors in getting production year and release dates corrected
    22 Sep 2020   2019.08.12.08    Correction to regex string to handle titles in Sort Order trailing determinates
    07 Oct 2020   2019.08.12.09    IAFD - change to https
    19 Jan 2021   2019.08.12.10    Improved on IAFD search, actors sexual roles if recorded are returned, if not shows a red circle.
                                   corrections to xpath extra )... failing to get genres, cast and directors

---------------------------------------------------------------------------------------------------------------
'''
import datetime, platform, os, re, sys, unicodedata, json
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2019.08.12.10'
PLUGIN_LOG_TITLE = 'GayDVDEmpire'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
REGEX = Prefs['regex']

# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# detect the language the summary appears in on the web page
DETECT = Prefs['detect']

# URLS
BASE_URL = 'http://www.gaydvdempire.com'
BASE_SEARCH_URL = BASE_URL + '/AllSearch/Search?view=list&?exactMatch={0}&q={0}'

# IAFD Related variables
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/results.asp?searchtype=comprehensive&searchstring={0}'

IAFD_ABSENT = u'\U0001F534'  # default value: red circle - not on IAFD
IAFD_NOROLE = u'\U0001F7E1'  # yellow circle - found actor with 

# Date Formats used by website
DATE_YMD = '%Y%m%d'
DATEFORMAT = '%m/%d/%Y'

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
class GayDVDEmpire(Agent.Movies):
    ''' define Agent class '''
    name = 'GayDVDEmpire (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchFilename(self, filename):
        ''' Check filename on disk corresponds to regex preference format '''
        pattern = re.compile(REGEX)
        matched = pattern.search(filename)
        if not matched:
            raise Exception("File Name [{0}] not in the expected format: (Studio) - Title (Year)".format(filename))

        filmDict = {}
        groups = matched.groupdict()
        filmDict['Studio'] = groups['studio']
        filmDict['CompareStudio'] = self.NormaliseComparisonString(filmDict['Studio'])

        filmDict['Title'] =  groups['title']
        filmDict['ShortTitle'] = filmDict['Title']
        filmDict['CompareFullTitle'] = self.SortComparisonString(self.NormaliseComparisonString(filmDict['Title']))
        filmDict['CompareShortTitle'] = filmDict['CompareFullTitle']
        filmDict['SearchTitle'] = filmDict['Title']

        filmDict['Year'] = groups['year']
        filmDict['CompareDate'] = datetime.datetime(int(filmDict['Year']), 12, 31) # default to 31 Dec of Filename year

        filmDict['Collection'] = ''
        filmDict['Compilation'] = '' # default value to be set when movie is being matched

        pattern = r'(?:[\-,]\s)'     # Films in series would either have commas or ' - ' (colons)
        splitFilmTitle = re.compile(pattern).split(filmDict['Title'])
        for partTitle in splitFilmTitle:
            pattern = r'(?<![-.])\b[0-9]+\b(?!\.[0-9])$' # look for whole separate number at end of string
            matchedSeries = re.subn(pattern, '', partTitle.strip())
            if matchedSeries[1]:
                filmDict['Collection'] = matchedSeries[0].strip()
                filmDict['ShortTitle'] = re.sub('{0}|(?:[\-,]\s)'.format(partTitle), '', filmDict['Title'], flags=re.IGNORECASE)
                if not filmDict['ShortTitle']:
                    filmDict['ShortTitle'] = filmDict['Title']
                filmDict['CompareShortTitle'] = self.SortComparisonString(self.NormaliseComparisonString(filmDict['ShortTitle']))
                filmDict['SearchTitle'] = filmDict['ShortTitle']
                break   # series found exit loop

        # prepare IAFD Search String
        filmDict['IAFDSearchTitle'] = filmDict['Title'].replace(' - ', ': ')         # iafd needs colons in place to search correctly
        filmDict['IAFDSearchTitle'] = filmDict['IAFDSearchTitle'].replace('&', 'and')         # iafd does not use &

        # split and take up to first occurence of character
        splitChars = ['-', '[', '(', ur'\u2013', ur'\u2014']
        pattern = u'[{0}]'.format(''.join(splitChars))
        matched = re.search(pattern, filmDict['IAFDSearchTitle'])  # match against whole string
        if matched:
            numPos = matched.start()
            filmDict['IAFDSearchTitle'] = filmDict['IAFDSearchTitle'][:numPos]

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        filmDict['IAFDSearchTitle'] = String.StripDiacritics(filmDict['IAFDSearchTitle'])
        filmDict['IAFDSearchTitle'] = String.URLEncode(filmDict['IAFDSearchTitle'])
        filmDict['IAFDSearchTitle'] = filmDict['IAFDSearchTitle'].replace('%25', '%').replace('*', '')

        # print out dictionary values
        for key in sorted(filmDict.keys()):
            self.log('SEARCH:: {%s} = %s', key, filmDict[key])

        return filmDict

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchStudioName(self, fileStudioName, siteStudioName):
        ''' match file studio name against website studio name: Boolean Return '''
        siteStudioName = self.NormaliseComparisonString(siteStudioName)

        if siteStudioName == fileStudioName:
            self.log('SELF:: Studio: Full Word Match: Site: {0} = File: {1}'.format(siteStudioName, fileStudioName))
        elif siteStudioName in fileStudioName:
            self.log('SELF:: Studio: Part Word Match: Site: {0} IN File: {1}'.format(siteStudioName, fileStudioName))
        elif fileStudioName in siteStudioName:
            self.log('SELF:: Studio: Part Word Match: File: {0} IN Site: {1}'.format(fileStudioName, siteStudioName))
        else:
            raise Exception('Match Failure: File: {0} != Site: {1} '.format(fileStudioName, siteStudioName))

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
        # Check if string has roman numerals as in a series; note the letter I will be converted
        myString = '{0} '.format(myString)  # append space at end of string to match last characters 
        pattern = '\s(?=[MDCLXVI])M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3})\s'
        matches = re.findall(pattern, myString, re.IGNORECASE)  # match against string
        if matches:
            RomanValues = {'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000}
            for count, match in enumerate(matches):
                myRoman = ''.join(match)
                self.log('SELF:: Found Roman Numeral: {0}. {1}'.format(count, myRoman))
                myArabic = RomanValues[myRoman[len(myRoman) - 1]]
                for i in range(len(myRoman) - 1, 0, -1):
                    if RomanValues[myRoman[i]] > RomanValues[myRoman[i - 1]]:
                        myArabic = myArabic - RomanValues[myRoman[i - 1]]
                    else:
                        myArabic = myArabic + RomanValues[myRoman[i - 1]]
                romanString = ' {0}'.format(myRoman)
                arabicString = ' {0}'.format(myArabic)
                myString = myString.replace(romanString, arabicString)

        # convert to lower case and trim
        myString = myString.strip().lower()

        # normalise unicode characters
        myString = unicode(myString)
        myString = unicodedata.normalize('NFD', myString).encode('ascii', 'ignore')

        # replace ampersand with 'and'
        myString = myString.replace('&', 'and')

        # strip domain suffixes, vol., volume from string, standalone "1's"
        pattern = ur'[.](org|com|net|co[.][a-z]{2})|Vol[.]|\bPart\b|\bVolume\b|(?<!\d)1(?!\d)|[^A-Za-z0-9]+'
        myString = re.sub(pattern, '', myString, flags=re.IGNORECASE)

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def SortComparisonString(self, myString):
        ''' Sort Normalised string, keep numbers in the order they appear followed by other characters in sort order '''
        numeric_string = re.sub(r'[^0-9]', '', myString).strip()
        alphabetic_string = re.sub(r'[0-9]', '', myString).strip()
        alphabetic_string = ''.join(sorted(alphabetic_string))
        myString = numeric_string + alphabetic_string

        #   return string as concatenation of numeric + sorted alphabet list - this keeps 32 string unequal to 23 string etc
        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Video title for search query '''
        self.log('SELF:: Original Search Query [{0}]'.format(myString))

        myString = myString.lower().strip()
        myString = myString.replace(' -', ':').replace(ur'\u2013', '-').replace(ur'\u2014', '-')

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString)

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        myString = myString.replace('%25', '%').replace('*', '')
        self.log('SELF:: Returned Search Query [{0}]'.format(myString))

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def TranslateString(self, myString, language):
        ''' Translate string into Library language '''
        myString = myString.strip()
        if language == 'xn' or language == 'xx':    # no language or language unknown
            self.log('SELF:: Library Language: [%s], Run Translation: [False]', 'No Language' if language == 'xn' else 'Unknown')
        elif myString:
            translator = Translator(service_urls=['translate.google.com', 'translate.google.ca', 'translate.google.co.uk',
                                                  'translate.google.com.au', 'translate.google.co.za', 'translate.google.br.com',
                                                  'translate.google.pt', 'translate.google.es', 'translate.google.com.mx',
                                                  'translate.google.it', 'translate.google.nl', 'translate.google.be',
                                                  'translate.google.de', 'translate.google.ch', 'translate.google.at',
                                                  'translate.google.ru', 'translate.google.pl', 'translate.google.bg',
                                                  'translate.google.com.eg', 'translate.google.co.il', 'translate.google.co.jp',
                                                  'translate.google.co.kr', 'translate.google.fr', 'translate.google.dk'])
            runTranslation = (language != SITE_LANGUAGE)
            self.log('SELF:: [Library:Site] Language: [%s:%s], Run Translation: [%s]', language, SITE_LANGUAGE, runTranslation)
            if DETECT:
                detectString = re.findall(ur'.*?[.!?]', myString)[:4]   # take first 4 sentences of string to detect language
                detectString = ''.join(detectString)
                self.log('SELF:: Detect Site Language [%s] using this text: %s', DETECT, detectString)
                try:
                    detected = translator.detect(detectString)
                    runTranslation = (language != detected.lang)
                    self.log('SELF:: Detected Language: [%s] Run Translation: [%s]', detected.lang, runTranslation)
                except Exception as e:
                    self.log('SELF:: Error Detecting Text Language: %s', e)

            try:
                myString = translator.translate(myString, dest=language).text if runTranslation else myString
                self.log('SELF:: Translated [%s] Summary Found: %s', runTranslation, myString)
            except Exception as e:
                self.log('SELF:: Error Translating Text: %s', e)

        return myString if myString else ' '     # return single space to initialise metadata summary field

    # -------------------------------------------------------------------------------------------------------------------------------
    def getIAFD_URLElement(self, myString):
        ''' check IAFD web site for better quality actor thumbnails irrespective of whether we have a thumbnail or not '''
        if not 'www.' in myString:
            myString = IAFD_SEARCH_URL.format(myString)

        myException = ''
        for i in range(2):
            try:
                html = HTML.ElementFromURL(myString, timeout=20, sleep=DELAY)
                return html
            except Exception as e:
                myException = e
                continue
        # failed to read page
        raise Exception('Failed to read IAFD URL [%s]', myException)

    # -------------------------------------------------------------------------------------------------------------------------------
    def getIAFD_Film(self, htmlcast, filmDict):
        ''' check IAFD web site for better quality actor thumbnails per movie'''

        actorDict =  {}

        # search for Film Title on IAFD and check off credited actors
        try:
            html = self.getIAFD_URLElement(filmDict['IAFDSearchTitle'])
            # get films listed within 1 year of what is on agent - as IAFD may have a different year recorded
            filmDict['Year'] = int(filmDict['Year'])
            filmList = html.xpath('//table[@id="titleresult"]/tbody/tr/td[2][.>="{0}" and .<="{1}"]/ancestor::tr'.format(filmDict['Year'] - 1, filmDict['Year'] + 1))
            self.log('SELF:: [%s] IAFD Films in List', len(filmList))
            if not filmList:        # movie not on IAFD - switch to CAST Mode
                raise Exception('No Movie by this name on IAFD')

            AKAList = []
            for film in filmList:
                try:
                    iafdTitle = film.xpath('./td[1]/a/text()')[0].strip()
                    compareIAFDTitle = self.SortComparisonString(self.NormaliseComparisonString(iafdTitle))
                    self.log('SELF:: Film Title           \t%s', iafdTitle)
                    self.log('SELF:: Compare Title        \t%s', compareIAFDTitle)
                    if compareIAFDTitle != filmDict['CompareFullTitle'] and compareIAFDTitle != filmDict['CompareShortTitle']:
                        # failed compare  match against AKA Title if present
                        self.log('SELF:: compareIAFDTitle        \t%s', compareIAFDTitle)
                        self.log('SELF:: compareFullTitle        \t%s', filmDict['CompareFullTitle'])
                        self.log('SELF:: compareShortTitle       \t%s', filmDict['CompareShortTitle'])
                        try:
                            akaTitle = film.xpath('./td[4]/text()')[0].strip()
                            if akaTitle:
                                compareAKATitle = self.SortComparisonString(self.NormaliseComparisonString(akaTitle))
                                self.log('SELF:: AKA Film Title       \t%s', akaTitle)
                                self.log('SELF:: AKA Compare Title    \t%s', compareAKATitle)
                                if compareAKATitle != filmDict['CompareFullTitle'] and compareAKATitle != filmDict['CompareShortTitle']:
                                    continue
                        except:
                            pass
                        continue
                except Exception as e:
                    self.log('SEARCH:: Error: Processing IAFD Film List: %s', e)
                    continue

                try:
                    iafdfilmURL = IAFD_BASE + film.xpath('./td[1]/a/@href')[0]
                    html = self.getIAFD_URLElement(iafdfilmURL)
                except Exception as e:
                    self.log('SEARCH:: Error: IAFD URL Studio: %s', e)
                    continue

                # compare film studio to that recorded on IAFD
                try:
                    siteStudio = html.xpath('//p[@class="bioheading" and text()="Studio"]//following-sibling::p[1]/a/text()')[0]
                    self.matchStudioName(filmDict['CompareStudio'], siteStudio)
                except Exception as e:
                    self.log('SEARCH:: Error: Matching IAFD Studio: %s', e)
                    try:
                        siteDistributor = html.xpath('//p[@class="bioheading" and text()="Distributor"]//following-sibling::p[1]/a/text()')[0]
                        self.matchStudioName(filmDict['CompareStudio'], siteDistributor)
                    except Exception as e:
                        self.log('SEARCH:: Error: Matching IAFD Distributor: %s', e)
                        continue

                try:
                    actorList = html.xpath('//h3[.="Performers"]/ancestor::div[@class="panel panel-default"]//div[@class[contains(.,"castbox")]]/p')
                    self.log('SELF:: Actors Found     \t[ %s ]', len(actorList))
                    for actor in actorList:
                        actorName = actor.xpath('./a/text()')[0].strip()
                        actorPhoto = actor.xpath('./a/img/@src')[0].strip()
                        actorPhoto = '' if 'nophoto' in actorPhoto else actorPhoto
                        actorRole = actor.xpath('./text()')
                        actorRole = ' '.join(actorRole).strip()
                        actorRole = actorRole if actorRole else IAFD_NOROLE

                        # if credited with other name - remove it from htmlcast
                        try:
                            creditedAs = actor.xpath('./i/text()')[0].split(':')[1].replace(')', '').strip()
                            AKAList.append(creditedAs)
                        except:
                            pass

                        self.log('SELF:: Actor:           \t%s', actorName)
                        self.log('SELF:: Actor Photo:     \t%s', actorPhoto)
                        self.log('SELF:: Actor Role:      \t%s', actorRole if actorRole else 'Role Not Assigned on IAFD')
                        self.log('SELF:: =========================================')

                        # Assign values to dictionary
                        myDict = {}
                        myDict['Photo'] = actorPhoto
                        myDict['Role'] = actorRole
                        actorDict[actorName] = myDict

                except Exception as e:
                    self.log('SELF:: Error: Processing IAFD Actor List: %s', e)
                    continue

                # if we get here we have found a match
                break


            # determine if there are any duplicates - by removing spaces and possible '.' after initials 
            duplicateList = []
            for cast in htmlcast:
                onlyAlphaCast = re.sub('[^A-Za-z]+', '', cast)
                for key in actorDict.keys():
                    if re.sub('[^A-Za-z]+', '', key) == onlyAlphaCast:
                        duplicateList.append(cast)

            # leave actors 'not found on IAFD' and 'AKA' and 'Duplicate'
            htmlcast = [cast for cast in htmlcast if cast not in actorDict.keys()]
            htmlcast = [cast for cast in htmlcast if cast not in AKAList]
            htmlcast = [cast for cast in htmlcast if cast not in duplicateList]

            self.log('SELF:: Film Processed: Found Actors: \t%s', actorDict.keys())
            self.log('SELF:: Film Processed: Actors Left:  \t%s', htmlcast)
        except Exception as e:
            self.log('SELF:: Error: IAFD Actor Search Failure, %s', e)

        return htmlcast, actorDict

    # -------------------------------------------------------------------------------------------------------------------------------
    def getIAFD_Actor(self, htmlcast, filmDict):
        ''' check IAFD web site for individual actors'''

        filmDict['Year'] = int(filmDict['Year'])
        actorDict =  {}
        AKAList = []

        for cast in htmlcast:
            splitCast = cast.lower().split()
            splitCast.sort()
            try:
                html = self.getIAFD_URLElement(String.URLEncode(cast))

                # return list of actors with the searched name and iterate through them
                xPathString = '//table[@id="tblMal" or @id="tblDir"]/tbody/tr[td[contains(.,"{0}")]]//ancestor::tr'.format(cast)
                actorList = html.xpath(xPathString)
                actorsFound = len(actorList)
                self.log('SELF:: [ %s ] Actors Found named \t%s', actorsFound, cast)
                for actor in actorList:     
                    try:
                        actorName = actor.xpath('./td[2]/a/text()[normalize-space()]')[0]          # get actor details and compare to Agent cast
                        self.log('SELF:: Actor:           \t%s', actorName)
                        splitActorName = actorName.lower().split()
                        splitActorName.sort()
                        if splitActorName != splitCast:
                            self.log('SELF:: Actor: Failed Name Match: Agent [%s] - IAFD [%s]', cast, actorName)
                            continue

                        actorAKA = actor.xpath('./td[2]/a/text()[normalize-space()]')[0]           # get actor AKA details 
                        startCareer = int(actor.xpath('./td[4]/text()[normalize-space()]')[0]) - 1 # set start of career to 1 year before for pre-releases
                        endCareer = int(actor.xpath('./td[5]/text()[normalize-space()]')[0]) + 1   # set end of career to 1 year after to cater for late releases

                        # only perform career checks if more than one actor found or if title is a compilation
                        if actorsFound > 1 and not filmDict['Compilation']:    
                            inRange = (startCareer <= filmDict['Year'] <= endCareer)
                            if inRange == False:
                                self.log('SELF:: Actor: Failed Career Range Match, Start: [%s] Film Year: [%s] End: [%s]', startCareer, filmDict['Year'], endCareer)
                                continue

                        # add cast name to Also Known as List for later deletion as we display IAFD main name rather than Agent name
                        if cast in actorAKA:
                            self.log('SELF:: Alias:           \t%s', cast)
                            AKAList.append(cast)

                        actorURL = IAFD_BASE + actor.xpath('./td[2]/a/@href')[0]
                        actorPhoto = actor.xpath('./td[1]/a/img/@src')[0] # actor name on agent website - retrieve picture
                        actorPhoto = '' if 'th_iafd_ad.gif' in actorPhoto else actorPhoto.replace('thumbs/th_', '')
                        actorRole = IAFD_NOROLE

                        self.log('SELF:: Start Career:    \t%s', startCareer)
                        self.log('SELF:: End Career:      \t%s', endCareer)
                        self.log('SELF:: Actor URL:       \t%s', actorURL)
                        self.log('SELF:: Actor Photo:     \t%s', actorPhoto)

                        # Assign values to dictionary
                        myDict = {}
                        myDict['Photo'] = actorPhoto
                        myDict['Role'] = actorRole
                        actorDict[actorName] = myDict

                        # processed an actor in site List - break out of loop
                        break   
                    except Exception as e:
                        self.log('SELF:: Error: Processing IAFD Actor List: %s', e)
                        continue

            except Exception as e:
                self.log('SELF:: Error: Processing Agent Actor List: %s', e)

        # leave actors not found on IAFD - remove AKA entries
        htmlcast = [cast for cast in htmlcast if cast not in actorDict.keys()]
        htmlcast = [cast for cast in htmlcast if cast not in AKAList]

        self.log('SELF:: Cast Processed: Found Actors: \t%s', actorDict.keys())
        self.log('SELF:: Cast Processed: Actors Left:  \t%s', htmlcast)

        return htmlcast, actorDict

    # -------------------------------------------------------------------------------------------------------------------------------
    def log(self, message, *args):
        ''' log messages '''
        if re.search('ERROR', message, re.IGNORECASE):
            Log.Error(PLUGIN_LOG_TITLE + ' - ' + message, *args)
        else:
            Log.Info(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])

        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version               : v.%s', VERSION_NO)
        self.log('SEARCH:: Python                : %s', sys.version_info)
        self.log('SEARCH:: Platform              : %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Prefs-> delay         : %s', DELAY)
        self.log('SEARCH::      -> detect        : %s', DETECT)
        self.log('SEARCH::      -> regex         : %s', REGEX)
        self.log('SEARCH:: Library:Site Language : %s:%s', lang, SITE_LANGUAGE)
        self.log('SEARCH:: Media Title           : %s', media.title)
        self.log('SEARCH:: File Name             : %s', filename)
        self.log('SEARCH:: File Folder           : %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check filename format
        try:
            filmDict = self.matchFilename(filename)
        except Exception as e:
            self.log('SEARCH:: Error: %s', e)
            return

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        # if title is in a series the search string will be composed of the Film Title minus Series Name and No.
        searchTitle = self.CleanSearchString(filmDict['SearchTitle'])
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        morePages = True
        while morePages:
            self.log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=90, errors='ignore', sleep=DELAY)
            except Exception as e:
                self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                break

            try:
                searchQuery = html.xpath('.//a[@title="Next"]/@href')[0]
                pageNumber = int(searchQuery.split('page=')[1]) # next page number
                searchQuery = BASE_SEARCH_URL.format(searchTitle) + '&page={0}'.format(pageNumber)
                pageNumber = pageNumber - 1
                self.log('SEARCH:: Search Query: %s', searchQuery)
                morePages = True if pageNumber <= 10 else False
            except:
                pageNumber = 1
                morePages = False

            titleList = html.xpath('.//div[contains(@class,"row list-view-item")]')
            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
            for title in titleList:
                # siteTitle = The text in the 'title' - Gay DVDEmpire - displays its titles in SORT order
                try:
                    siteTitle = title.xpath('./div/h3/a[@category and @label="Title"]/@title')[0]
                    # convert sort order version to normal version i.e "Best of Zak Spears, The -> the Best of Zak Spears"
                    pattern = u', (The|An|A)$'
                    matched = re.search(pattern, siteTitle, re.IGNORECASE)  # match against string
                    if matched:
                        self.log('SEARCH:: Found Determinate: {0}'.format(matched.group()))
                        determinate = matched.group().replace(', ', '')
                        siteTitle = re.sub(pattern, '', siteTitle)
                        siteTitle = '{0} {1}'.format(determinate, siteTitle)
                        self.log('SEARCH:: Re-ordered Site Title: {0}'.format(siteTitle))

                    siteCompareTitle = self.SortComparisonString(self.NormaliseComparisonString(siteTitle))

                    # standard match - full film title to site title
                    self.log('SEARCH:: Site Title                    "%s"', siteTitle)
                    self.log('SEARCH:: Site Compare Title            "%s"', siteCompareTitle)
                    self.log('SEARCH:: Dictionary Compare Full Title "%s"', filmDict['CompareFullTitle'])
                    self.log('SEARCH:: Dictionary Compare Short Tile "%s"', filmDict['CompareShortTitle'])
                    if siteCompareTitle == filmDict['CompareFullTitle'] or siteCompareTitle == filmDict['CompareShortTitle']:
                        self.log('SEARCH:: Title Match [True]  : Site Title "%s"', siteTitle)
                    else:
                        self.log('SEARCH:: Title Match [False] : Site Title "%s"', siteTitle)
                        continue
                except:
                    continue

                # Studio Name
                try:
                    siteStudio = title.xpath('./div/ul/li/a/small[text()="studio"]/following-sibling::text()')[0].strip()
                    self.log('SEARCH:: Studio: %s Compare against: %s', filmDict['CompareStudio'], siteStudio)
                    self.matchStudioName(filmDict['CompareStudio'], siteStudio)
                except Exception as e:
                    self.log('SEARCH:: Error getting Site Studio: %s', e)
                    continue

                # Site Release Date
                # Get the production year if exists - if it does not match to the compareReleaseDate try the release date
                try:
                    siteProductionYear = title.xpath('./div/h3/small[contains(.,"(")]/text()')[0]
                    siteProductionYear = siteProductionYear.replace('(', '').replace(')', '')
                    self.log('SEARCH:: Site Production Year: %s', siteProductionYear)
                    siteReleaseDate = self.matchReleaseDate(filmDict['CompareDate'], siteProductionYear)
                # use the Site Release Date, if this also does not match to comparereleasedate - next
                except Exception as e:
                    self.log('SEARCH:: Error getting Production Year try Release Date: %s', e)
                    try:
                        siteReleaseDate = title.xpath('./div/ul/li/span/small[text()="released"]/following-sibling::text()')[0].strip()
                        self.log('SEARCH:: Release Date: %s Compare against: %s', filmDict['CompareDate'], siteReleaseDate)
                        siteReleaseDate = self.matchReleaseDate(filmDict['CompareDate'], siteReleaseDate)
                    except Exception as e:
                        self.log('SEARCH:: Error getting Site Release Date: %s', e)
                        continue

                self.log('SEARCH:: My Site Release Date: %s', siteReleaseDate)

                # Site Title URL
                try:
                    siteURL = title.xpath('./div/h3/a[@label="Title"]/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    filmDict['SiteURL'] = siteURL
                    self.log('SEARCH:: Site Title url: %s', siteURL)
                except:
                    self.log('SEARCH:: Error getting Site Title Url')
                    continue

                # reset comparison date to above scrapping result
                filmDict['CompareDate'] = siteReleaseDate.strftime(DATE_YMD)

                # we should have a match on studio, title and year now
                results.Append(MetadataSearchResult(id=json.dumps(filmDict), name=filmDict['Title'], score=100, lang=lang))
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

        # Fetch HTML.
        filmDict = json.loads(metadata.id)
        html = HTML.ElementFromURL(filmDict['SiteURL'], timeout=60, errors='ignore', sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as above
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Content Rating       : Always X
        #        d. Tag line             : Corresponds to the url of movie, as Website does not show Tag lines
        #        e. Originally Available : GayHotMovies only displays the Release Year, so use studio year
        #        f. Collections          : from filename: can be added to from website info..
        #
        #    2.  Metadata retrieved from website
        #        a. Tag line             : Corresponds to the url of movie if not found
        #        b. Summary
        #        c. Directors            : List of Drectors (alphabetic order)
        #        d. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        e. Genres
        #        f. Collections
        #        g. Posters/Background

        # 1a.   Studio - straight of the file name
        metadata.studio = filmDict['Studio']
        self.log('UPDATE:: Studio: %s' % metadata.studio)

        # 1b.   Set Title
        metadata.title = filmDict['Title']
        self.log('UPDATE:: Video Title: %s' % metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = filmDict['SiteURL']
        metadata.originally_available_at = datetime.datetime.strptime(filmDict['CompareDate'], DATE_YMD)
        metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Tagline: %s', metadata.tagline)
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)

        # 1e.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 1f. Collection
        metadata.collections.clear()
        metadata.collections.add(filmDict['Collection'])
        self.log('UPDATE:: Collection Set From filename: %s', filmDict['Collection'])

        # 2a.   Tagline
        try:
            metadata.tagline = html.xpath('//p[@class="Tagline"]')[0].text_content().strip()
            self.log('UPDATE:: Tagline: %s', metadata.tagline)
        except:
            pass

        # 2b.   Summary
        try:
            summary = html.xpath('//div[@class="col-xs-12 text-center p-y-2 bg-lightgrey"]/div/p')[0].text_content().strip()
            summary = re.sub('<[^<]+?>', '', summary)
            self.log('UPDATE:: Summary Found: %s', summary)
            metadata.summary = self.TranslateString(summary, lang)
        except:
            self.log('UPDATE:: Error getting Summary')

        # 2c.   Collections
        try:
            htmlcollections = html.xpath('//a[contains(@label, "Series")]/text()[normalize-space()]')
            self.log('UPDATE:: %s Collections Found: "%s"', len(htmlcollections), htmlcollections)
            for collection in htmlcollections:
                collection = collection.replace('"', '').replace('Series', '').strip()
                if collection:
                    metadata.collections.add(collection)
        except:
            self.log('UPDATE:: Error getting Collections')

        # 2d.   Genres
        try:
            ignoreGenres = ['Sale', '4K Ultra HD']
            genres = []
            htmlgenres = html.xpath('//ul[@class="list-unstyled m-b-2"]//a[@label="Category"]/text()[normalize-space()]')
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                genre = genre.strip()
                if not genre:
                    continue
                if anyOf(x in genre for x in ignoreGenres):
                    continue
                if 'compilation' in genre.lower():
                    filmDict['Compilation'] = 'Compilation'
                genres.append(genre)

            genres.sort()
            metadata.genres.clear()
            for genre in genres:
                metadata.genres.add(genre)
        except:
            self.log('UPDATE:: Error getting Genres')

        # 2e.   Directors
        directors = []
        try:
            htmldirector = html.xpath('//a[contains(@label, "Director - details")]/text()[normalize-space()]')
            self.log('UPDATE:: Director List %s', htmldirector)
            for director in htmldirector:
                director = director.strip()
                if director:
                    directors.append(director)

            # sort the dictionary and add kv to metadata
            directors.sort()
            metadata.directors.clear()
            for director in directors:
                Director = metadata.directors.new()
                Director.name = director
        except:
            self.log('UPDATE:: Error getting Director(s)')

        # 2f.   Cast
        castdict = {}
        filmcastLeft = []
        try:
            htmlcast = html.xpath('//a[contains(@class,"PerformerName")]/text()[normalize-space()]')
            htmlcast = [x.split('(')[0].strip() if '(' in x else x.strip() for x in htmlcast]
            htmlcast = [x for x in htmlcast if x]      
            self.log('UPDATE:: Cast List %s', htmlcast)

            # If there is a corresponding Film Entry on IAFD, process all actors recorded in the IAFD entry
            self.log('UPDATE:: Process in Film Mode: %s Recorded Actors: %s', len(htmlcast), htmlcast)
            try:
                filmcastLeft, actordict = self.getIAFD_Film(htmlcast, filmDict) # composed of picture and role
                if actordict:
                    castdict.update(actordict)
            except Exception as e:
                self.log('UPDATE - Process Film Mode Error: %s', e)
            
            # If there is a corresponding Cast Entry on IAFD, process all actors with an entry on IAFD
            if filmcastLeft:
                self.log('UPDATE:: Process in Cast Mode: %s Recorded Actors: %s', len(filmcastLeft), filmcastLeft)
                try:
                    filmcastLeft, actordict = self.getIAFD_Actor(filmcastLeft, filmDict) # composed of picture and role
                    if actordict:
                        castdict.update(actordict)
                except Exception as e:
                        self.log('UPDATE - Process Cast Mode Error: %s', e)

            # Mark any actor left in htmlcast who do not have a dictionary entry as Absent on IAFD and add them to dictionary marked thus
            if filmcastLeft:
                self.log('UPDATE:: %s Actors absent on IAFD: %s', len(filmcastLeft), filmcastLeft)
                for cast in filmcastLeft:
                    castdict[cast] = {'Photo': '', 'Role': IAFD_ABSENT}

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted(castdict):
                cast = metadata.roles.new()
                cast.name = key
                cast.photo = castdict[key]['Photo']
                cast.role = castdict[key]['Role']

        except Exception as e:
            self.log('UPDATE:: Error getting Cast: %s', e)

        # 2g.   Poster/Background Art
        try:
            image = html.xpath('//*[@id="front-cover"]/img')[0]
            posterurl = image.get('src')
            self.log('UPDATE:: Movie Thumbnail Found: "%s"', posterurl)
            validPosterList = [posterurl]
            if posterurl not in metadata.posters:
                try:
                    metadata.posters[posterurl] = Proxy.Media(HTTP.Request(posterurl).content, sort_order=1)
                except:
                    self.log('UPDATE:: Error getting Poster')
            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

            arturl = posterurl.replace('h.jpg', 'bh.jpg')
            validArtList = [arturl]
            if arturl not in metadata.art:
                try:
                    metadata.art[arturl] = Proxy.Media(HTTP.Request(arturl).content, sort_order=1)
                except:
                    self.log('UPDATE:: Error getting Background Art')
            #  clean up and only keep the background art we have added
            metadata.art.validate_keys(validArtList)
        except:
            self.log('UPDATE:: Error getting Poster/Background Art:')
