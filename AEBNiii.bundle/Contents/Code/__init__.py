# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# AEBNiii - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    21 May 2020   2020.05.21.01    Creation: using current AdultEntertainmentBroadcastNetwork website - added scene breakdown to summary
    01 Jun 2020   2020.05.21.02    Implemented translation of summary
                                   improved getIAFDActor search
    27 Jun 2020   2020.05.21.03    Improvement to Summary Translation: Translate into Plex Library Language
                                   stripping of intenet domain suffixes from studio names when matching
                                   handling of unicode characters in film titles and comparision string normalisation
    01 Jul 2020   2020.05.21.03	   Renamed to AEBNiii
    14 Jul 2020   2020.05.21.04    Enhanced seach to also look through the exact matches, as AEBN does not always put these
                                   in the general search results
    07 Oct 2020   2020.05.21.05    IAFD - change to https
    09 Jan 2021   2020.05.21.06    IAFD - New Search Routine + Auto Collection setting

-----------------------------------------------------------------------------------------------------------------------------------
'''
import datetime, platform, os, re, sys, unicodedata, json
from googletrans import Translator

# Version / Log Title
VERSION_NO = '2020.05.21.06'
PLUGIN_LOG_TITLE = 'AEBN iii'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
REGEX = Prefs['regex']

# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# detect the language the summary appears in on the web page
DETECT = Prefs['detect']

# URLS
BASE_URL = 'https://gay.aebn.com'
BASE_SEARCH_URL = [BASE_URL + '/gay/search/?sysQuery={0}', BASE_URL + '/gay/search/movies/page/1?sysQuery={0}&criteria=%7B%22sort%22%3A%22Relevance%22%7D']

# IAFD Related variables
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/results.asp?searchtype=comprehensive&searchstring={0}'

IAFD_ABSENT = u'\U0001F534'  # default value: red circle - not on IAFD
IAFD_NOROLE = u'\U0001F7E1'  # yellow circle - found actor with no role unassigned

# Date Formats used by website
DATE_YMD = '%Y%m%d'
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
class AEBNiii(Agent.Movies):
    ''' define Agent class '''
    name = 'AEBN iii (IAFD)'
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
    def matchTitle(self, ExactMatches, title, filmDict):
        ''' match Film in list returned by running the query '''
        matched = True

        # Site Title
        try:
            siteTitle = title.xpath('./section//h1/a/text()')[0] if ExactMatches else title.xpath('./a//img/@title')[0]
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
                matched = False
        except:
            self.log('SELF:: Error getting Site Title')
            matched = False

        # Site Title URL
        if matched:
            try:
                siteURL = title.xpath('./section//h1/a/@href')[0] if ExactMatches else title.xpath('./a/@href')[0]
                siteURL = ('' if BASE_URL in siteURL else BASE_URL) + siteURL
                filmDict['SiteURL'] = siteURL
                self.log('SELF:: Site Title url: %s', siteURL)
            except:
                self.log('SELF:: Error getting Site Title Url')
                matched = False

        # Access Site URL for Studio and Release Date information only when looking at non exact match titles
        if matched:
            if not ExactMatches:
                try:
                    html = HTML.ElementFromURL(filmDict['SiteURL'], sleep=DELAY)
                except Exception as e:
                    self.log('SELF:: Error reading Site URL page: %s', e)
                    matched = False

        # Site Studio
        if matched:
            foundStudio = False
            try:
                htmlSiteStudio = title.xpath('./section//li[contains(@class,"item-studio")]/a/text()') if ExactMatches else html.xpath('//div[@class="dts-studio-name-wrapper"]/a/text()')
                self.log('SELF:: %s Site URL Studios: %s', len(htmlSiteStudio), htmlSiteStudio)
                for siteStudio in htmlSiteStudio:
                    try:
                        self.log('SEARCH:: Studio: %s Compare against: %s', filmDict['CompareStudio'], siteStudio)
                        self.matchStudioName(filmDict['CompareStudio'], siteStudio)
                        foundStudio = True
                    except Exception as e:
                        self.log('SELF:: Error: %s', e)

                    if foundStudio:
                        break
            except Exception as e:
                self.log('SELF:: Error getting Site Studio %s', e)
                matched = False

            if not foundStudio:
                self.log('SELF:: Error No Matching Site Studio')
                matched = False

        # Site Release Date
        if matched:
            try:
                siteReleaseDate = title.xpath('./section//li[contains(@class,"item-release-date")]/text()')[0] if ExactMatches else html.xpath('//li[contains(@class,"item-release-date")]/text()')[0]
                siteReleaseDate = siteReleaseDate.strip().lower()
                siteReleaseDate = siteReleaseDate.replace('sept ', 'sep ').replace('july ', 'jul ')
                self.log('SELF:: Site URL Release Date: %s', siteReleaseDate)
                try:
                    siteReleaseDate = self.matchReleaseDate(filmDict['CompareDate'], siteReleaseDate)
                except Exception as e:
                    self.log('SELF:: Error getting Site URL Release Date: %s', e)
                    matched = False
            except:
                self.log('SELF:: Error getting Site URL Release Date: Default to Filename Date')
                siteReleaseDate = filmDict['CompareDate']

            filmDict['CompareDate'] = siteReleaseDate.strftime(DATE_YMD)

        return matched

    # -------------------------------------------------------------------------------------------------------------------------------
    def NormaliseComparisonString(self, myString):
        ''' Normalise string for, strip uneeded characters for comparison of web site values to file name regex group values '''
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

        # convert to lower case and trim and strip diacritics, fullstops, enquote
        myString = myString.replace('.', '').replace('-', '')
        myString = myString.lower().strip()
        myString = String.StripDiacritics(myString)

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
        myNormalString = String.URLEncode(myString).replace('%25', '%').replace('*', '')
        myQuotedString = String.URLEncode('"{0}"'.format(myString)).replace('%25', '%').replace('*', '')
        myString = [myNormalString, myQuotedString]
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
        searchTitleList = self.CleanSearchString(filmDict['SearchTitle'])
        for count, searchTitle in enumerate(searchTitleList, start=1):
            searchQuery = BASE_SEARCH_URL[0].format(searchTitle)
            self.log('SEARCH:: %s. Exact Match Search Query: %s', count, searchQuery)

            # first check exact matches
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
                titleList = html.xpath('//section[contains(@class,"dts-panel-exact-match")]/div[@class="dts-panel-content"]')
                for title in titleList:
                    matchedTitle = self.matchTitle(True, title, filmDict)

                    # we should have a match on studio, title and year now
                    if matchedTitle:
                        results.Append(MetadataSearchResult(id=json.dumps(filmDict), name=filmDict['Title'], score=100, lang=lang))
                        return
            except Exception as e:
                self.log('SEARCH:: Error: Search Query did find any Exact Movie Matches: %s', e)

            # if we get here there were no exact matches returned by the search query, so search through the rest
            searchQuery = BASE_SEARCH_URL[1].format(searchTitle)
            self.log('SEARCH:: %s. General Search Query: %s', count, searchQuery)
            morePages = True
            while morePages:
                self.log('SEARCH:: Search Query: %s', searchQuery)
                try:
                    html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
                    # Finds the entire media enclosure
                    titleList = html.xpath('//div[@class="dts-image-overlay-container"]')
                    if not titleList:
                        break   # out of WHILE loop to the FOR loop
                except Exception as e:
                    self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                    return

                try:
                    searchQuery = html.xpath('//ul[@class="dts-pagination"]/li[@class="active" and text()!="..."]/following::li/a[@class="dts-paginator-tagging"]/@href')[0]
                    searchQuery = (BASE_URL if BASE_URL not in searchQuery else '') + searchQuery
                    self.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                    pageNumber = int(html.xpath('//ul[@class="dts-pagination"]/li[@class="active" and text()!="..."]/text()')[0])
                    morePages = True if pageNumber <= 10 else False
                except:
                    searchQuery = ''
                    self.log('SEARCH:: No More Pages Found')
                    pageNumber = 1
                    morePages = False

                self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))
                for title in titleList:
                    # get film variables in dictionary format: if dict is filled we have a match
                    matchedTitle = self.matchTitle(False, title, filmDict)
                    if matchedTitle:
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
        #    2.  Metadata retrieved from website
        #        a. Summary              : Synopsis + Scene Breakdowns
        #        b. Genres
        #        c. Collections
        #        d. Directors            : List of Drectors (alphabetic order)
        #        e. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        f. Posters/Background

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

        # 2a.   Summary = Synopsis + Scene Information
        try:
            synopsis = html.xpath('//div[@class="dts-section-page-detail-description-body"]/text()')[0].strip()
            self.log('UPDATE:: Synopsis Found: %s', synopsis)
        except Exception as e:
            synopsis = ''
            self.log('UPDATE:: Error getting Synopsis: %s', e)

        # scene information
        allscenes = ''
        try:
            htmlheadings = html.xpath('//header[@class="dts-panel-header"]/div/h1[contains(text(),"Scene")]/text()')
            htmlscenes = html.xpath('//div[@class="dts-scene-info dts-list-attributes"]')
            self.log('UPDATE:: %s Scenes Found: %s', len(htmlscenes), htmlscenes)
            for (heading, htmlscene) in zip(htmlheadings, htmlscenes):
                settingsList = htmlscene.xpath('./ul/li[descendant::span[text()="Settings:"]]/a/text()')
                if settingsList:
                    self.log('UPDATE:: %s Setting Found: %s', len(settingsList), settingsList)
                    settings = ', '.join(settingsList)
                    scene = ('\n[ {0} ] . . . . Setting: {1}').format(heading.strip(), settings)
                else:
                    scene = '\n[ {0} ]'.format(heading.strip())
                starsList = htmlscene.xpath('./ul/li[descendant::span[text()="Stars:"]]/a/text()')
                if starsList:
                    starsList = [x.split('(')[0] for x in starsList]
                    self.log('UPDATE:: %s Stars Found: %s', len(starsList), starsList)
                    stars = ', '.join(starsList)
                    scene += '. . . . Stars: {0}'.format(stars)

                actsList = htmlscene.xpath('./ul/li[descendant::span[text()="Sex acts:"]]/a/text()')
                if actsList:
                    self.log('UPDATE:: %s Sex Acts Found: %s', len(actsList), actsList)
                    acts = ', '.join(actsList)
                    scene += '\nSex Acts: {0}'.format(acts)
                allscenes += scene
        except Exception as e:
            scene = ''
            self.log('UPDATE:: Error getting Scene Breakdown: %s', e)

        allscenes = '\nScene Breakdown:\n{0}'.format(allscenes) if allscenes else ''
        summary = synopsis + allscenes
        metadata.summary = self.TranslateString(summary, lang)

        # 2b.   Genres
        try:
            ignoreGenres = ['feature', 'exclusive', 'new release']
            genres = []
            htmlgenres = html.xpath('//span[@class="dts-image-display-name"]/text()')
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                genre = genre.strip()
                if not genre:
                    continue
                if anyOf(x in genre.lower() for x in ignoreGenres):
                    continue
                genres.append(genre)
                if 'compilation' in genre.lower():
                    filmDict['Compilation'] = 'Compilation'

            genres.sort()
            metadata.genres.clear()
            for genre in genres:
                metadata.genres.add(genre)
        except Exception as e:
            self.log('UPDATE:: Error getting Genres: %s', e)

        # 2c.   Collections
        try:
            htmlcollections = html.xpath('//li[@class="section-detail-list-item-series"]/span/a/span/text()')
            self.log('UPDATE:: %s Collections Found: %s', len(htmlcollections), htmlcollections)
            for collection in htmlcollections:
                collection = collection.strip()
                if not collection:
                    continue
                if filmDict['Collection'].lower() == collection.lower():    # if set by filename its already in the list
                    continue
                metadata.collections.add(collection)
                self.log('UPDATE:: %s Collection Added: %s', collection)
        except Exception as e:
            self.log('UPDATE:: Error getting Collections: %s', e)

        # 2d.   Directors
        try:
            directors = []
            htmldirector = html.xpath('//li[@class="section-detail-list-item-director"]/span/a/span/text()')
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
        except Exception as e:
            self.log('UPDATE:: Error getting Director(s): %s', e)

        # 2e.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list and have more actor photos than AdultEntertainmentBroadcastNetwork
        castdict = {}
        filmcastLeft = []
        try:
            htmlcast = html.xpath('//a[contains(@href,"/gay/stars/")]/@title')
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

        # 2f.   Posters/Background Art - Front Cover set to poster, Back Cover to background art
        # In this list we are going to save the posters that we want to keep
        try:
            htmlimages = html.xpath('//a[@class="dts-movie-boxcover"]//img/@src')
            self.log('UPDATE:: %s Poster/Background Art Found: %s', len(htmlimages), htmlimages)

            validPosterList = []
            image = htmlimages[0].split('?')[0]
            image = ('http:' if 'http:' not in image else '') + image
            self.log('UPDATE:: Movie Poster Found: %s', image)
            validPosterList.append(image)
            if image not in metadata.posters:
                metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

            validArtList = []
            image = htmlimages[1].split('?')[0]
            image = ('http:' if 'http:' not in image else '') + image
            self.log('UPDATE:: Movie Background Art Found: %s', image)
            validArtList.append(image)
            if image not in metadata.art:
                metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order=1)
            #  clean up and only keep the Art we have added
            metadata.art.validate_keys(validArtList)
        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Background Art: %s', e)
