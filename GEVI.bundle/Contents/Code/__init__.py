#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# GEVI - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    01 Jun 2020   2019.12.25.14    Implemented translation of summary
                                   improved getIAFDActor search
    24 Jun 2020   2019.12.25.15    Improvement to Summary Translation: Translate into Plex Library Language
                                   stripping of intenet domain suffixes from studio names when matching
                                   handling of unicode characters in film titles
    12 Jul 2020   2019.12.25.16    drop first word of title if numeric to search
    30 Aug 2020   2019.12.25.17    Handling of Roman Numerals in Titles to Match Arabic Numerals
    12 Sep 2020   2019.12.25.18    Error in creating search string whilst handling Ampersands, 
                                   these were replaced with a null string instead of splitting at the position as in numerals
    17 Sep 2020   2019.12.25.19    Error in determining default date
    28 Sep 2020   2019.12.25.20    Fixed dates which had a Circa in them i.e c1980
    07 Oct 2020   2019.12.25.21    IAFD - change to https
                                   GEVI now searches all returned results and stops if return is alphabetically greater than title
    22 Nov 2020   2019.12.25.22    Improved generation of search string - previously titles like The 1000 Load Fuck would not match
                                   as both first word and second word can not be used to search for movies in GEVI. i.e numeric and indefinite article
    26 Dec 2020   2020.12.25.23    Improved on IAFD search, actors sexual roles if recorded are returned, if not shows a red circle.
                                   if actor is not credited on IAFD but is on Agent Site it shows as a Yellow Box below the actor
                                   sped up search by removing search by actor/director... less hits on IAFD per actor...
-----------------------------------------------------------------------------------------------------------------------------------
'''
import datetime, platform, os, re, sys, unicodedata, json
from googletrans import Translator
import pprint

# Version / Log Title
VERSION_NO = '2019.12.25.23'
PLUGIN_LOG_TITLE = 'GEVI'

REGEX = Prefs['regex']

# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# detect the language the summary appears in on the web page
DETECT = Prefs['detect']

# URLS
BASE_URL = 'https://www.gayeroticvideoindex.com'
BASE_SEARCH_URL = BASE_URL + '/search.php?type=t&where=b&query={0}&Search=Search&page=1'
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/results.asp?searchtype=comprehensive&searchstring={0}'

# Date Formats used by website
DATE_YMD = '%Y%m%d'
DATEFORMAT = '%Y%m%d'

# IAFD Search Mode - ALL|CAST: Search for film and Scene titles on IAFD | Search for Actor 
IAFD_SEARCH_MODE = 'ALL'

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
        ''' Normalise string for, strip uneeded characters for comparison of web site values to file name regex group values '''
        # Check if string has roman numerals as in a series; note the letter I will be converted
        myString = '{0} '.format(myString)  # append space at end of string to match last characters 
        pattern = '\s(?=[MDCLXVI])M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3})$'
        matches = re.findall(pattern, myString, re.IGNORECASE)  # match against string
        if matches:
            RomanValues = {'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000}
            for count, match in enumerate(matches):
                myRoman = ''.join(match).upper()
                self.log('SELF:: Found Roman Numeral: {0}.. {1} len[{2}]'.format(count, myRoman, len(myRoman)))
                myArabic = RomanValues[myRoman[-1]]
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

        # convert to lower case and trim
        myString = myString.lower().strip()
        myBackupString = myString

        nullChars = ["'", ',', '!', '.', '#'] # to be replaced with null
        pattern = u'[{0}]'.format(''.join(nullChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            self.log('SELF:: Search Query:: Replacing characters in string. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, '', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            self.log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('SELF:: Search Query:: String has none of these {0}'.format(pattern))

        spaceChars = ['-', ur'\u2013', ur'\u2014', '(', ')']  # to be replaced with space
        pattern = u'[{0}]'.format(''.join(spaceChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            self.log('SELF:: Search Query:: Replacing characters with Space. Found one of these {0}'.format(pattern))
            myString = re.sub(pattern, ' ', myString)
            myString = ' '.join(myString.split())   # remove continous white space
            self.log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('SELF:: Search Query:: String has none of these {0}'.format(pattern))

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
                self.log("SELF:: Search Query:: Dropping first word [{0}]".format(myWords[0]))
                myWords.remove(myWords[0])
                myString = ' '.join(myWords)
                self.log('SELF:: Amended Search Query [{0}]'.format(myString))
            else:
                self.log("SELF:: Search Query:: Did not match against first word [{0}]".format(myWords[0]))
                break

        # examine string for numbers and &
        pattern = r'[0-9&]'
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            numPos = matched.start()
            self.log('SELF:: Search Query:: Splitting at position [{0}]. Found one of these {1}'.format(numPos, pattern))
            myString = myString[:numPos]
            self.log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            self.log('SELF:: Search Query:: Split not attempted. String has none of these {0}'.format(pattern))

        # all preparation has resulted in an empty string e.g title like 35 & Up by Bacchus Releasing
        myString = re.sub(r'[^A-Za-z]', ' ', myBackupString) if not myString else myString

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
            myString = myString.replace('&', 'and')
            myString = String.StripDiacritics(myString.lower())
            myString = String.URLEncode(myString.strip())
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
    def getIAFD_Actor(self, htmlcast, filmDict):
        ''' check IAFD web site for individual actors'''

        filmDict['Year'] = int(filmDict['Year'])
        NoRoleOnIAFD = u'\U0001F7E1'  # yellow circle - found actor with no role unassigned
        actorDict =  {}
        AKAList = []

        for cast in htmlcast:
            splitCast = cast.lower().split()
            splitCast.sort()
            try:
                html = self.getIAFD_URLElement(cast)

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
                        actorRole = NoRoleOnIAFD

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
    def getIAFD_Film(self, htmlcast, filmDict):
        ''' check IAFD web site for better quality actor thumbnails per movie'''

        actorDict =  {}

        # search for Film Title on IAFD and check off credited actors
        try:
            html = self.getIAFD_URLElement(filmDict['ShortTitle'])
            # get films listed within 1 year of what is on agent - as IAFD may have a different year recorded
            filmDict['Year'] = int(filmDict['Year'])
            filmList = html.xpath('//table[@id="titleresult"]/tbody/tr/td[2][.>="{0}" and .<="{1}"]/ancestor::tr'.format(filmDict['Year'] - 1, filmDict['Year'] + 1))
            self.log('SELF:: [%s] IAFD Films in List', len(filmList))
            if not filmList:        # movie not on IAFD - switch to CAST Mode
                raise Exception('No Movie by this name on IAFD')

            NoRoleOnIAFD = u'\U0001F7E1'  # yellow circle - found actor with no role unassigned
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
                                self.log('SELF:: here 2        \t%s', compareIAFDTitle)
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
                        actorRole = actorRole if actorRole else NoRoleOnIAFD

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

            # leave actors not found on IAFD and credited as
            htmlcast = [cast for cast in htmlcast if cast not in actorDict.keys()]
            htmlcast = [cast for cast in htmlcast if cast not in AKAList]

            self.log('SELF:: Film Processed: Found Actors: \t%s', actorDict.keys())
            self.log('SELF:: Film Processed: Actors Left:  \t%s', htmlcast)
        except Exception as e:
            self.log('SELF:: Error: IAFD Actor Search Failure, %s', e)

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

            for title in titleList:
                # Site Title
                try:
                    siteTitle = title[0].text_content().strip()
                    siteCompareTitle = self.SortComparisonString(self.NormaliseComparisonString(siteTitle))

                    # standard match - full film title to site title
                    self.log('SEARCH:: Site Title "%s"', siteTitle)
                    self.log('SEARCH:: Compare Title "%s"', siteCompareTitle)
                    self.log('SEARCH:: Dictionary Compare Full Title "%s"', filmDict['CompareFullTitle'])
                    self.log('SEARCH:: Dictionary Compare Short Tile "%s"', filmDict['CompareShortTitle'])
                    if siteCompareTitle == filmDict['CompareFullTitle'] or siteCompareTitle == filmDict['CompareShortTitle']:
                        self.log('SEARCH:: Title Match [True]  : Site Title "%s"', siteTitle)
                    else:
                        self.log('SEARCH:: Title Match [False] : Site Title "%s"', siteTitle)
                        continue
                except:
                    self.log('SEARCH:: Error getting Site Title')
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('.//a/@href')[0]
                    siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                    filmDict['SiteURL'] = siteURL
                    self.log('SEARCH:: Site Title url: %s', siteURL)
                except:
                    self.log('SEARCH:: Error getting Site Title Url')
                    continue

                # Site Title Type (Compilation)
                try:
                    siteType = title[4].text_content().strip()
                    if siteType.lower() == 'compilation':
                        filmDict['Compilation'] = 'Compilation'
                except:
                    self.log('SEARCH:: Error getting Site Type (Compilaion)')
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
                            self.log('SEARCH:: Studio: %s Compare against: %s', filmDict['CompareStudio'], siteStudio)
                            self.matchStudioName(filmDict['CompareStudio'], siteStudio)
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
                siteReleaseDate = ''
                releaseDateMatchFail = False
                try:
                    # get the release dates
                    htmlReleaseDate = html.xpath('//td[.="released" or .="produced"]/following-sibling::td[1]/text()[normalize-space()]')
                    htmlReleaseDate = [x if unicode(x, 'utf-8').isnumeric() else x.split('-')[0] if '-' in x else x.split(',')[0] if ',' in x else x[1:] if x[0] == 'c' else '' for x in htmlReleaseDate]
                    htmlReleaseDate = [x for x in htmlReleaseDate if x]
                    htmlReleaseDate = list(set(htmlReleaseDate))
                    self.log('SEARCH:: %s Site URL Release Dates: %s', len(htmlReleaseDate), htmlReleaseDate)
                    for ReleaseDate in htmlReleaseDate:
                        try:

                            self.log('SEARCH:: Release Date: %s Compare against: %s', filmDict['CompareDate'], ReleaseDate)
                            ReleaseDate = self.matchReleaseDate(filmDict['CompareDate'], ReleaseDate)
                            siteReleaseDate = ReleaseDate
                            break
                        except Exception as e:
                            self.log('SEARCH:: Error: %s', e)
                            releaseDateMatchFail = True
                            continue
                    if not siteReleaseDate:
                        raise Exception('No Release Dates Found')

                except Exception as e:
                    self.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date [%s]', e)
                    if releaseDateMatchFail:
                        continue
                    siteReleaseDate = filmDict['CompareDate']

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
        #        c. Tag line             : Corresponds to the url of movie
        #        d. Originally Available : set from metadata.id (search result)
        #        e. Content Rating       : Always X
        #        e. Collection Info      : From title group of filename 
        #    2.  Metadata retrieved from website
        #        a. Summary
        #        b. Countries            : Alphabetic order
        #        c. Rating
        #        d. Directors            : List of Directors (alphabetic order)
        #        e. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        f. Genre
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

        # 2a.   Summary = Promo + Scenes + Legend
        try:
            promo = ''
            htmlpromo = html.xpath('//td[contains(text(),"promo/")]//following-sibling::td//span[@style]/text()[following::br]')
            for item in htmlpromo:
                promo = '{0}\n{1}'.format(promo, item)
            self.log('UPDATE:: Promo Found: %s', promo)
            promo = promo.replace('\n', ' ')
        except Exception as e:
            promo = ''
            self.log('UPDATE:: Error getting Promo: %s', e)

        # Legend
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
        try:
            htmlscenes = html.xpath('//td[@class="scene"]')
            scenes = ''
            for item in htmlscenes:
                scenes = '{0}\n{1}'.format(scenes, ''.join(item.itertext()).strip())
            scenes = scenes.strip()
            self.log('UPDATE:: Scenes Found: %s', scenes)
        except Exception as e:
            scenes = ''
            self.log('UPDATE:: Error getting Scenes: %s', e)

        # combine and update
        metadata.summary = ' '
        legend = legend if scenes else ''
        summary = "{0}\n{1}\n{2}".format(promo, legend, scenes)
        if summary.strip():
            regex = r'View this scene at.*|found in compilation.*|see also.*'
            pattern = re.compile(regex, re.IGNORECASE)
            summary = re.sub(pattern, '', summary)
            metadata.summary = self.TranslateString(summary, lang)

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
            self.log('UPDATE:: Error getting Country(ies): %s', e)

        # 2c.   Rating (out of 4 Stars) = Rating can be a maximum of 10 - float value
        try:
            rating = html.xpath('//td[contains(text(),"rating out of 4")]//following-sibling::td[1]/text()')[0].strip()
            rating = rating.count('*') * 2.5
            self.log('UPDATE:: Film Rating %s', rating)
            metadata.rating = rating
        except Exception as e:
            metadata.rating = 0.0
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
        AbsentOnIAFD = u'\U0001F534'  # default value: red circle - not on IAFD
        castdict = {}
        filmcastLeft = []
        try:
            htmlcast = html.xpath('//td[@class="pd"]/a/text()')
            htmlcast = [x.split('(')[0].strip() if '(' in x else x.strip() for x in htmlcast]
            htmlcast = [x for x in htmlcast if x]      
            filmDict['Title'] = filmDict['Title'].replace(' - ', ':')         # iafd needs colons in place to search correctly

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
                    castdict[cast] = {'Photo': '', 'Role': AbsentOnIAFD}

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted(castdict):
                cast = metadata.roles.new()
                cast.name = key
                cast.photo = castdict[key]['Photo']
                cast.role = castdict[key]['Role']

        except Exception as e:
            self.log('UPDATE:: Error getting Cast: %s', e)

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
