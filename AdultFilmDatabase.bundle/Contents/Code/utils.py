#!/usr/bin/env python
# encoding=utf8
'''
General Functions found in all agents
                                                  Version History
                                                  ---------------
    Date            Modification
    27 Mar 2021     Added curly single quotes to string normalisation in addition to `, all quotes single quotes are now replaced by straight quotes
    03 May 2021     Issue #96 - Series Titles matching...
                    Added duration matching between filename duration and iafd duration
    08 May 2021     Merged GenFunctions.py with Utils.py created by codeanator to deal with cloudscraper protection issues in IAFD
    05 Jul 2021     Merged iafd.py with Utils
                    Improvements to name matching, Levenshtein and Soundex and translation
                    Changes to matching films against IAFD
                    Improved iafd matching and reduction of http requests to iafd
    20 Aug 2021     IAFD only searched after film found on Agent Website - Code Changes
                    improved code dealing with ffprobe duration garthering - as wmv returns were in a different arrangement, causing errors
                    show scraper name on summary legend line
    17 Jan 2022     implemented changes suggested by codeAnator a member of the group:
                        - film duration - using plex inbuilt process rather than ffprobe 
                        - using the original image from a website if cropping can not be achieved
                        - improve REGEX matching on filenames now includes stacking info
                    implemented change by Cody:
                        - duration matching optional on IAFD matching
    11 Mar 2022     #137 - Corrected creation of iafd url string as links now have https:\\iafd.com in them
    04 Apr 2022     #151 - Fixed: No Match when checking against No Duration on IAFD
    04 Apr 2022     #152 - Fixed: - in IAFD titles
    24 Apr 2022     improved search for first in series of collection as many series do not have the number "1" after the title
    13 May 2022     #162: duration matching had an error in the code - corrected
                    #137: Dual studio matching corrected
                    improved logging clarity
                    impoved cast matching - if a film is all male, female cast will not be scrapped
                    new code to strip Roman Numeral Suffices on IAFD Titles to increase matching opportunities
'''
# ----------------------------------------------------------------------------------------------------------------------------------
import cloudscraper, fake_useragent, os, platform, re, subprocess, unicodedata
from datetime import datetime
from unidecode import unidecode
from urlparse import urlparse

# IAFD Related variables
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/results.asp?searchtype=comprehensive&searchstring={0}'
IAFD_ABSENT = u'\U0000274C'        # red cross mark - not on IAFD
IAFD_FOUND = u'\U00002705'         # heavy white tick on green - on IAFD

# getHTTPRequest variable 
scraper = None

# -------------------------------------------------------------------------------------------------------------------------------
def getCast(agntCastList, FILMDICT):
    ''' Process and match cast list against IAFD '''

    if not agntCastList and not FILMDICT['Cast']: # nowt to do
        raise

    # clean up the Cast List make a copy then clear
    agntCastList = [x.split('(')[0].strip() if '(' in x else x.strip() for x in agntCastList]
    agntCastList = [String.StripDiacritics(x) for x in agntCastList]
    agntCastList = [x for x in agntCastList if x]
    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Agent Cast List'), agntCastList))

    excludeList = [string for string in agntCastList if [substr for substr in agntCastList if substr in string and substr != string]]
    if excludeList:
        agntCastList = [x for x in agntCastList if x not in excludeList]
        log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Exclude'), excludeList))
        log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Result'), agntCastList))

    # strip all non alphabetic characters from cast names / aliases so as to compare them to the list obtained from the website e.g. J.T. Sloan will render as jtsloan
    castDict = FILMDICT['Cast']
    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('IAFD Cast List'), sorted(castDict.keys())))

    IAFDCastList = [(re.sub(r'[\W\d_]', '', k).strip().lower(), re.sub(r'[\W\d_]', '', v['Alias']).strip().lower()) for k, v in castDict.items()] # list of tuples [name, alias]

    # remove entries from the website cast list which have been found on IAFD leaving unmatched cast
    unmatchedCastList = [x for x in agntCastList if re.sub(r'[\W\d_]', '', x).strip().lower() not in (item for namealias in IAFDCastList for item in namealias)]
    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Unmatched Cast List'), unmatchedCastList))
    log(LOG_SUBLINE)

    # search IAFD for specific cast and return matched cast
    matchedCastDict = matchCast(unmatchedCastList, FILMDICT)

    # update the Cast dictionary
    if matchedCastDict:
        castDict.update(matchedCastDict)

    return castDict

# -------------------------------------------------------------------------------------------------------------------------------
def getDirectors(agntDirectorList, FILMDICT):
    ''' Process and match director list against IAFD'''

    if not agntDirectorList and not FILMDICT['Directors']: # nowt to do
        raise

    # clean up the Director List 
    agntDirectorList = [x.split('(')[0].strip() if '(' in x else x.strip() for x in agntDirectorList]
    agntDirectorList = [String.StripDiacritics(x) for x in agntDirectorList]
    agntDirectorList = [x for x in agntDirectorList if x]
    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Agent Director List'), agntDirectorList))

    excludeList = [string for string in agntDirectorList if [substr for substr in agntDirectorList if substr in string and substr != string]]
    if excludeList:
        agntDirectorList = [x for x in agntDirectorList if x not in excludeList]
        log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Exclude'), excludeList))
        log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Result'), agntDirectorList))

    # strip all non alphabetic characters from director names / aliases so as to compare them to the list obtained from the website e.g. J.T. Sloan will render as jtsloan
    directorDict = FILMDICT['Directors']
    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('IAFD Director List'), sorted(directorDict.keys())))

    IAFDDirectorList = [(re.sub(r'[\W\d_]', '', k).strip().lower(), v) for k, v in directorDict.items()] # list of tuples [name, alias]

    # remove entries from the website cast list which have been found on IAFD leaving unmatched director
    unmatchedDirectorList = [x for x in agntDirectorList if re.sub(r'[\W\d_]', '', x).strip().lower() not in (item for namealias in IAFDDirectorList for item in namealias)]
    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Unmatched Director List'), unmatchedDirectorList))
    log(LOG_SUBLINE)

    # search IAFD for specific director and return matched directors
    matchedDirectorDict = matchDirectors(unmatchedDirectorList, FILMDICT)

    # update the Director dictionary
    if matchedDirectorDict:
        directorDict.update(matchedDirectorDict)

    return directorDict

# -------------------------------------------------------------------------------------------------------------------------------
def getFilmImages(imageType, imageURL, whRatio):
    ''' Only for Scene Agents: get Film images - posters/background art and crop if necessary '''
    from io import BytesIO
    from PIL import Image

    pic = imageURL
    picContent = ''
    picInfo = Image.open(BytesIO(HTTP.Request(pic).content))
    width, height = picInfo.size
    dispWidth = '{:,d}'.format(width)       # thousands separator
    dispHeight = '{:,d}'.format(height)     # thousands separator

    log('UTILS :: {0} Found: Width ({1}) x Height ({2}); URL: {3}'.format(imageType, dispWidth, dispHeight, imageURL))

    maxHeight = float(width * whRatio)      # Maximum allowable height

    cropHeight = float(maxHeight if maxHeight <= height else height)
    cropWidth = float(cropHeight / whRatio)

    DxHeight = 0.0 if cropHeight == height else (abs(cropHeight - height) / height) * 100.0
    DxWidth = 0.0 if cropWidth == width else (abs(cropWidth - width) / width) * 100.0

    cropRequired = True if DxWidth >= 10 or DxHeight >=10 else False
    cropWidth = int(cropWidth)
    cropHeight = int(cropHeight)
    desiredWidth = '{0:,d}'.format(cropWidth)     # thousands separator
    desiredHeight = '{0:,d}'.format(cropHeight)   # thousands separator
    DxWidth = '{0:.2f}'.format(DxWidth)    # percent format
    DxHeight = '{0:.2f}'.format(DxHeight)  # percent format
    log('UTILS :: Crop {0} {1}: Actual (w{2} x h{3}), Desired (w{4} x h{5}), % Dx = w[{6}%] x h[{7}%]'.format("Required:" if cropRequired else "Not Required:", imageType, dispWidth, dispHeight, desiredWidth, desiredHeight, DxWidth, DxHeight))
    cropped = False
    if cropRequired:
        try:
            log('UTILS :: Using Thumbor to crop image to: {0} x {1}'.format(desiredWidth, desiredHeight))
            pic = THUMBOR.format(cropWidth, cropHeight, imageURL)
            picContent = HTTP.Request(pic).content
            cropped = True
        except Exception as e:
            log('UTILS :: Error Thumbor Failed to Crop Image to: {0} x {1}: {2} - {3}'.format(desiredWidth, desiredHeight, pic, e))
            try:
                if os.name == 'nt':
                    log('UTILS :: Using Script to crop image to: {0} x {1}'.format(desiredWidth, desiredHeight))
                    envVar = os.environ
                    TempFolder = envVar['TEMP']
                    LocalAppDataFolder = envVar['LOCALAPPDATA']
                    pic = os.path.join(TempFolder, imageURL.split("/")[-1])
                    cmd = CROPPER.format(LocalAppDataFolder, imageURL, pic, cropWidth, cropHeight)
                    subprocess.call(cmd)
                    picContent = load_file(pic)
                    cropped = True
            except Exception as e:
                log('UTILS :: Error Script Failed to Crop Image to: {0} x {1}'.format(desiredWidth, desiredHeight))

    if not cropped:
        picContent = HTTP.Request(pic).content

    return pic, picContent

# -------------------------------------------------------------------------------------------------------------------------------
def getFilmOnIAFD(FILMDICT):
    ''' check IAFD web site for better quality thumbnails per movie'''
    FILMDICT['AllFemale'] = ''
    FILMDICT['AllMale'] = 'Yes' # default to yes as this is usually used on gay websites.
    FILMDICT['Cast'] = {}
    FILMDICT['Comments'] = ''
    FILMDICT['Directors'] = {}
    FILMDICT['FoundOnIAFD'] = 'No'
    FILMDICT['IAFDFilmURL'] = ''
    FILMDICT['Scenes'] = ''
    FILMDICT['Synopsis'] = ''

    # some agent websites don't monitor this, so default to No
    FILMDICT['Compilation'] = 'No' if 'Compilation' not in FILMDICT else FILMDICT['Compilation']

    # prepare IAFD Title and Search String
    FILMDICT['IAFDTitle'] = makeASCII(FILMDICT['ShortTitle']).replace(' - ', ': ').replace('- ', ': ')       # iafd needs colons in place to search correctly
    FILMDICT['IAFDTitle'] = FILMDICT['IAFDTitle'].replace(' &', ' and')                                      # iafd does not use &
    FILMDICT['IAFDTitle'] = FILMDICT['IAFDTitle'].replace('!', '')                                           # remove !

    # split and take up to first occurence of character
    splitChars = ['[', '(', ur'\u2013', ur'\u2014']
    pattern = ur'[{0}]'.format(''.join(splitChars))
    matched = re.search(pattern, FILMDICT['IAFDTitle'])  # match against whole string
    if matched:
        FILMDICT['IAFDTitle'] = FILMDICT['IAFDTitle'][:matched.start()]

    # split at standalone '1's'
    pattern = ur'(?<!\d)1(?!\d)'
    matched = re.search(pattern, FILMDICT['IAFDTitle'])  # match against whole string
    if matched:
        FILMDICT['IAFDTitle'] = FILMDICT['IAFDTitle'][:matched.start()]

    # strip definite and indefinite english articles
    pattern = ur'^(The|An|A) '
    matched = re.search(pattern, FILMDICT['IAFDTitle'], re.IGNORECASE)  # match against whole string
    if matched:
        FILMDICT['IAFDTitle'] = FILMDICT['IAFDTitle'][matched.end():]
        tempCompare = sortAlphaChars(NormaliseComparisonString(FILMDICT['IAFDTitle']))
        if tempCompare not in FILMDICT['IAFDCompareTitle']:
            FILMDICT['IAFDCompareTitle'].append(tempCompare)

    # if agent is IAFD split at first colon
    # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string, also remove '!'
    FILMDICT['IAFDSearchTitle'] = FILMDICT['IAFDTitle'] if FILMDICT['Agent'] != 'IAFD' else FILMDICT['IAFDTitle'].split(':')[0]
    FILMDICT['IAFDSearchTitle'] = String.StripDiacritics(FILMDICT['IAFDSearchTitle']).strip()
    FILMDICT['IAFDSearchTitle'] = String.URLEncode(FILMDICT['IAFDSearchTitle'])
    FILMDICT['IAFDSearchTitle'] = FILMDICT['IAFDSearchTitle'].replace('%25', '%').replace('*', '')

    # search for Film Title on IAFD
    log(LOG_BIGLINE)
    log('UTILS :: *** Find [%s] on IAFD ***', FILMDICT['Title'])
    log(LOG_BIGLINE)
    try:
        html = getURLElement(IAFD_SEARCH_URL.format(FILMDICT['IAFDSearchTitle']), UseAdditionalResults=True)

        # get films listed within 1 year of what is on agent - as IAFD may have a different year recorded
        filmList = []
        if FILMDICT['Year']:
            FILMDICT['Year'] = int(FILMDICT['Year'])
            filmList = html.xpath('//table[@id="titleresult"]/tbody/tr/td[2][.>="{0}" and .<="{1}"]/ancestor::tr'.format(FILMDICT['Year'] - 1, FILMDICT['Year'] + 1))
            log('UTILS :: Films found on IAFD           {0} between the years [{1}] and [{2}]'.format(len(filmList), FILMDICT['Year'] - 1, FILMDICT['Year'] + 1))

        if not filmList:
            filmList = html.xpath('//table[@id="titleresult"]/tbody/tr')
            log('UTILS :: Films found on IAFD           {0}'.format(len(filmList)))

        for film in filmList:
            # Site Title and Site AKA
            log(LOG_BIGLINE)
            try:
                iafdTitle = film.xpath('./td[1]/a/text()')[0].strip()
                # IAFD sometimes adds (I), (II), (III) to differentiate scenes from full movies - strip these out before matching - assume a max of 19
                pattern = ' \(X{0,1}(?:V?I{0,3}|I[VX])\)$'
                matched = re.search(pattern, iafdTitle)  # match against whole string
                if matched:
                    iafdTitle = re.sub(pattern, '', iafdTitle).strip()
                matchTitle(iafdTitle, FILMDICT)
            except Exception as e:
                log('UTILS :: Error getting IAFD Title: %s', e)
                try:
                    iafdAKA = film.xpath('./td[4]/text()')[0].strip()
                    pattern = ' \(X{0,1}(?:V?I{0,3}|I[VX])\)$'
                    matched = re.search(pattern, iafdAKA)  # match against whole string
                    if matched:
                        iafdAKA = re.sub(pattern, '', iafdAKA).strip()
                    matchTitle(iafdAKA, FILMDICT)
                except Exception as e:
                    log('UTILS :: Error getting IAFD AKA Title: %s', e)
                    continue

            # Film URL
            log(LOG_BIGLINE)
            try:
                iafdfilmURL = film.xpath('./td[1]/a/@href')[0].replace('+/', '/').replace('-.', '.')
                if IAFD_BASE not in iafdfilmURL:
                    iafdfilmURL = '{0}{1}'.format(IAFD_BASE, iafdfilmURL) if iafdfilmURL[0] == '/' else '{0}/{1}'.format(IAFD_BASE, iafdfilmURL)
                html = getURLElement(iafdfilmURL, UseAdditionalResults=False)
            except Exception as e:
                log('UTILS :: Error: IAFD URL Studio: %s', e)
                log(LOG_SUBLINE)
                continue

            # Film Studio and Distributor
            log(LOG_BIGLINE)
            studioList = []
            try:
                siteStudio = html.xpath('//p[@class="bioheading" and text()="Studio"]//following-sibling::p[1]/a/text()')[0].strip()
                studioList.append(siteStudio)
            except:
                pass

            # Film Distributor
            try:
               siteDistributor = html.xpath('//p[@class="bioheading" and text()="Distributor"]//following-sibling::p[1]/a/text()')[0].strip()
               studioList.append(siteDistributor)
            except:
                pass

            studioMatch = False
            for studio in studioList:
                try:
                    matchStudio(studio, FILMDICT, False if FILMDICT['IAFDStudio'] else True) # if an IAFD Studio was recorded on the filename - set last param to false
                    studioMatch = True
                    break           # break out of loop if it matches
                except Exception as e:
                    log('UTILS :: Error matching IAFD Studio: %s', e)
                    log(LOG_SUBLINE)
                    continue

            if not studioMatch:
                log('UTILS :: Error getting IAFD Studio')
                log(LOG_SUBLINE)
                continue

            # Film Duration
            log(LOG_BIGLINE)
            if MATCHIAFDDURATION:
                try:
                    iafdDuration = html.xpath('//p[@class="bioheading" and text()="Minutes"]//following-sibling::p[1]/text()')[0].strip()
                    if re.match(r'^[0-9]*$', iafdDuration):   # IAFD stores duration in whole minutes, regex match
                        matchDuration(iafdDuration, FILMDICT)
                    else:
                        log('UTILS :: Warning: No IAFD Duration declared: %s', iafdDuration)
                except Exception as e:
                    log('UTILS :: Error: IAFD Duration: %s', e)
                    log(LOG_SUBLINE)
                    continue
            else:
                log('UTILS :: Skipping: IAFD Duration Retrieval')

            # if we get here we have found a film match
            log(LOG_BIGLINE)
            FILMDICT['FoundOnIAFD'] = 'Yes'
            log('UTILS :: Found on IAFD:                %s', FILMDICT['FoundOnIAFD'])

            log(LOG_BIGLINE)
            # url address of film
            FILMDICT['IAFDFilmURL'] = iafdfilmURL
            log('UTILS :: IAFD Film URL:                %s', FILMDICT['IAFDFilmURL'])

            # check if film is a compilation
            log(LOG_BIGLINE)
            try:
                FILMDICT['Compilation'] = html.xpath('//p[@class="bioheading" and text()="Compilation"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: IAFD: Film Compilation?:      %s', FILMDICT['Compilation'])
            except Exception as e:
                log('UTILS :: Error Finding IAFD Compilation Information: %s', e)

            # check if film has an all male cast
            log(LOG_BIGLINE)
            try:
                FILMDICT['AllMale'] = html.xpath('//p[@class="bioheading" and text()="All-Male"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: IAFD: All Male Cast?:         %s', FILMDICT['AllMale'])
            except Exception as e:
                log('UTILS :: Error Finding All Male Cast: %s', e)

            # check if film has an all female cast
            log(LOG_BIGLINE)
            try:
                FILMDICT['AllFemale'] = html.xpath('//p[@class="bioheading" and text()="All-Female"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: IAFD: All Female Cast?:       %s', FILMDICT['AllFemale'])
            except Exception as e:
                log('UTILS :: Error Finding All Female Cast: %s', e)

            # get Film Cast info
            log(LOG_BIGLINE)
            try:
                FILMDICT['Cast'] = getRecordedCast(html)
            except Exception as e:
                log('UTILS :: Error Finding IAFD Cast Information: %s', e)

            # get Director info
            log(LOG_BIGLINE)
            try:
                FILMDICT['Directors'] = getRecordedDirectors(html)
            except Exception as e:
                log('UTILS :: Error Finding IAFD Director Information: %s', e)

            # synopsis
            log(LOG_BIGLINE)
            try:
                synopsis = html.xpath('//div[@id="synopsis"]/div/ul/li//text()')[0] # will error if no synopsis
                htmlsynopsis = html.xpath('//div[@id="synopsis"]/div/ul/li//text()')
                for synopsisNo, synopsis in enumerate(htmlsynopsis):
                    log('UTILS :: Film Synopsis:                %s', synopsis) if synopsisNo == 0 else log('UTILS ::                               %s', synopsis)
                FILMDICT['Synopsis'] = "\n".join(htmlsynopsis)               
            except Exception as e:
                log('UTILS :: Error getting IAFD Synopsis: %s', e)

            # get Scene Breakdown
            log(LOG_BIGLINE)
            try:
                scene = html.xpath('//div[@id="sceneinfo"]/ul/li//text()')[0] # will error if no scene breakdown
                htmlscenes = html.xpath('//div[@id="sceneinfo"]/ul/li//text()[normalize-space()]')
                for sceneNo, scene in enumerate(htmlscenes):
                    log('UTILS :: Film Scenes:                  %s', scene) if sceneNo == 0 else log('UTILS ::                               %s', scene)
                FILMDICT['Scenes'] = "##".join(htmlscenes)               
            except Exception as e:
                log('UTILS :: Error getting IAFD Scene Breakdown: %s', e)

            # get comments
            log(LOG_BIGLINE)
            try:
                comments = html.xpath('//div[@id="commentsection"]/ul/li//text()')[0] # will error if no comments
                htmlcomments = html.xpath('//div[@id="commentsection"]/ul/li//text()[normalize-space()]')
                listEven = htmlcomments[::2] # Elements from htmlcomments starting from 0 iterating by 2
                listOdd = htmlcomments[1::2] # Elements from htmlcomments starting from 1 iterating by 2
                comments = 'Comments:##'
                for sceneNo, movie in zip(listEven, listOdd):
                    comments += '{0} -- {1}##'.format(sceneNo, movie)
                FILMDICT['Comments'] = comments
                log('UTILS :: Film Comments:                %s', FILMDICT['Comments'])
            except Exception as e:
                log('UTILS :: Error getting IAFD Comments: %s', e)

            break
    except Exception as e:
        log('UTILS :: Error: IAFD Film Search Failure, %s', e)

    # set up the the legend that can be prefixed/suffixed to the film summary 
    IAFD_ThumbsUp = u'\U0001F44D'      # thumbs up unicode character
    IAFD_ThumbsDown = u'\U0001F44E'    # thumbs down unicode character
    IAFD_Stacked = u'\u2003Stacked \U0001F4FD\u2003::'
    agentName = u'\u2003{0}\u2003::'.format(FILMDICT['Agent'])
    IAFD_Legend = u'::\u2003Film on IAFD {2}\u2003::\u2003{1} / {0} Actor on Cast List?\u2003::{3}{4}'
    presentOnIAFD = IAFD_ThumbsUp if FILMDICT['FoundOnIAFD'] == 'Yes' else IAFD_ThumbsDown
    stackedStatus = IAFD_Stacked if FILMDICT['Stacked'] == 'Yes' else ''
    FILMDICT['Legend'] = IAFD_Legend.format(IAFD_ABSENT, IAFD_FOUND, presentOnIAFD, stackedStatus, agentName)

    return FILMDICT

# ----------------------------------------------------------------------------------------------------------------------------------
def getHTTPRequest(url, **kwargs):
    headers = kwargs.pop('headers', {})
    cookies = kwargs.pop('cookies', {})
    timeout = kwargs.pop('timeout', 20)
    proxies = {}

    global scraper

    if 'User-Agent' not in headers:
        headers['User-Agent'] = (fake_useragent.UserAgent(fallback=HTTP.Headers['User-agent'])).random

    # clean up url....
    ClearURL = url
    if url.startswith('http'):
        url = urlparse(url)
        path = url.path
        path = path.replace('//', '/')

        ClearURL = '%s://%s%s' % (url.scheme, url.netloc, path)
        if url.query:
            ClearURL += '?%s' % url.query

    url = ClearURL

    HTTPRequest = None
    try:
        log('UTILS :: CloudScraper Request:         %s', url)
        if scraper is None:
            scraper = cloudscraper.CloudScraper()
            scraper.headers.update(headers)
            scraper.cookies.update(cookies)

        HTTPRequest = scraper.request('GET', url, timeout=timeout, proxies=proxies)
        if not HTTPRequest.ok:
            msg = ('< CloudScraper Failed Request Status Code: %s >', HTTPRequest.status_code)
            raise Exception(msg)

        if HTTPRequest:
            HTTPRequest.encoding = 'UTF-8'

    except Exception as e:
        msg = ('< CloudScraper Failed: %s >', e)
        raise Exception(msg)

    return HTTPRequest

# -------------------------------------------------------------------------------------------------------------------------------
def getRecordedCast(html):
    ''' retrieve film cast from IAFD film page'''
    filmCast = {}
    try:
        castList = html.xpath('//div[@class[contains(.,"castbox")]]/p')
        log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Cast on IAFD'), len(castList)))
        for cast in castList:
            castName = cast.xpath('./a/text()[normalize-space()]')[0].strip()
            castURL = IAFD_BASE + cast.xpath('./a/@href')[0].strip()
            castPhoto = cast.xpath('./a/img/@src')[0].strip()
            castPhoto = '' if 'nophoto' in castPhoto or 'th_iafd_ad' in castPhoto else castPhoto
            
            # cast roles are sometimes not filled in
            try:
                castRole = cast.xpath('./text()[normalize-space()]')
                castRole = ' '.join(castRole).strip()
            except:
                castRole = ''

            # cast alias may be missing
            try:
                castAlias = cast.xpath('./i/text()')[0].split(':')[1].replace(')', '').strip()
            except:
                castAlias = ''

            castRole = castRole if castRole else 'AKA: {0}'.format(castAlias) if castAlias else IAFD_FOUND

            # log cast details
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Cast Name'), castName))
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Cast Alias'), castAlias if castAlias else 'No Cast Alias Recorded'))
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Cast URL'), castURL))
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Cast Photo'), castPhoto))
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Cast Role'), castRole))

            # Assign values to dictionary
            myDict = {}
            myDict['Photo'] = castPhoto
            myDict['Role'] = castRole
            myDict['Alias'] = castAlias
            myDict['CompareName'] = re.sub(r'[\W\d_]', '', castName).strip().lower()
            myDict['CompareAlias'] = re.sub(r'[\W\d_]', '', castAlias).strip().lower()
            filmCast[castName] = myDict
            log(LOG_SUBLINE)

    except Exception as e:
        log('UTILS :: Error: Processing IAFD Film Cast: %s', e)

    return filmCast

# -------------------------------------------------------------------------------------------------------------------------------
def getRecordedDirectors(html):
    ''' retrieve directors from IAFD film page'''
    filmDirectors = {}
    try:
        directorList = html.xpath('//p[@class="bioheading" and text()="Directors"]//following-sibling::p[1]/a')
        log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Directors on IAFD'), len(directorList)))
        for director in directorList:
            directorName = director.xpath('./text()')[0].split(' as ')[0]
            directorURL = director.xpath('./@href')[0]
            try:
                dhtml = getURLElement(directorURL, UseAdditionalResults=False)
                try:
                    directorPhoto = dhtml.xpath('//div[@id="headshot"]/img/@src')[0]
                    directorPhoto = '' if 'nophoto' in directorPhoto else directorPhoto
                except:
                    directorPhoto = ''
                try:
                    directorAliasList = dhtml.xpath('//p[@class="bioheading" and text()="Director AKA"]//following-sibling::p[1]/text()[normalize-space()]')
                    directorAliasList = [x.replace('No known aliases', '').strip() for x in directorAliasList]
                except:
                    directorAliasList = []

            except Exception as e:
                log('UTILS :: Error getting Director Page: %s', e)

            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Director Name'), directorName))
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Director Alias'), directorAliasList if directorAliasList else 'No Director Alias Recorded'))
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Director URL'), directorURL))
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Director Photo'), directorPhoto))
            log(LOG_SUBLINE)

            # Assign values to dictionary
            myDict = {}
            myDict['Photo'] = directorPhoto
            myDict['Alias'] = directorAliasList
            myDict['CompareName'] = re.sub(r'[\W\d_]', '', directorName).strip().lower()
            myDict['CompareAlias'] = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in directorAliasList]
            filmDirectors[directorName] = myDict

    except Exception as e:
        log('UTILS :: Error getting Film Director(s): %s', e)

    return filmDirectors

# ----------------------------------------------------------------------------------------------------------------------------------
def getURLElement(myString, UseAdditionalResults):
    ''' check IAFD web site for better quality thumbnails irrespective of whether we have a thumbnail or not '''
    # this variable will be set if IAFD fails to be read
    html = ''
    msg = ''
    try:
        HTTPRequest = getHTTPRequest(myString, timeout=20)
        html = HTML.ElementFromString(HTTPRequest.text)

        if UseAdditionalResults:
            try:
                searchQuery = html.xpath('//a[text()="See More Results..."]/@href')[0].strip().replace(' ', '+')
                if searchQuery:
                    searchQuery = IAFD_BASE + searchQuery if IAFD_BASE not in searchQuery else searchQuery
                    try:
                        HTTPRequest = getHTTPRequest(searchQuery, timeout=20)
                        html = HTML.ElementFromString(HTTPRequest.text)
                    except Exception as e:
                        html = ''
                        log('UTILS :: Failed to read Additional Search Results: %s', e)
            except Exception as e:
                pass
    except Exception as e:
        html = ''
        msg = '< Failed to read IAFD URL: {0} - Processing Abandoned >'.format(e)

    if not html:
        raise Exception(msg)

    return html

# ----------------------------------------------------------------------------------------------------------------------------------
def logHeaders(header, media, lang):
    ''' list header of search and update functions '''
    log(LOG_BIGLINE)
    log('%s:: Version:                      v.%s', header, VERSION_NO)
    log('%s:: Python:                       %s %s', header, platform.python_version(), platform.python_build())
    log('%s:: Platform:                     %s - %s %s', header, platform.machine(), platform.system(), platform.release())
    log('%s:: Preferences:', header)
    log('%s::  > Legend Before Summary:     %s', header, PREFIXLEGEND)
    log('%s::  > Initialise Collections:    %s', header, COLCLEAR)
    log('%s::  > Collection Gathering', header)
    log('%s::      > Cast:                  %s', header, COLCAST)
    log('%s::      > Director(s):           %s', header, COLDIRECTOR)
    log('%s::      > Studio:                %s', header, COLSTUDIO)
    log('%s::      > Film Title:            %s', header, COLTITLE)
    log('%s::      > Genres:                %s', header, COLGENRE)
    log('%s::  > Match IAFD Duration:       %s', header, MATCHIAFDDURATION)
    log('%s::  > Match Site Duration:       %s', header, MATCHSITEDURATION)
    log('%s::  > Duration Dx                ±%s Minutes', header, DURATIONDX)
    log('%s::  > Language Detection:        %s', header, DETECT)
    log('%s::  > Library:Site Language:     (%s:%s)', header, lang, SITE_LANGUAGE)
    log('%s::  > Network Request Delay:     %s Seconds', header, DELAY)    
    log('%s:: Media Title:                  %s', header, media.title)
    log('%s:: File Path:                    %s', header, media.items[0].parts[0].file)
    log(LOG_BIGLINE)

# -------------------------------------------------------------------------------------------------------------------------------
def makeASCII(myString):
    ''' standardise single quotes, double quotes and accented characters '''

    # standardise single quotes
    singleQuotes = ['`', '‘', '’']
    pattern = ur'[{0}]'.format(''.join(singleQuotes))
    myString = re.sub(pattern, "'", myString)

    # standardise double quotes
    doubleQuotes = ['“', '”']
    pattern = ur'[{0}]'.format(''.join(doubleQuotes))
    myString = re.sub(pattern, '"', myString)

    # convert to unicode
    myString = u'{0}'.format(myString)
    asciiString = ''
    for i, char in enumerate(myString):
        description = unicodedata.name(char)
        cutoff = description.find(' WITH ')
        if cutoff != -1:
            description = description[:cutoff]
            try:
                char = unicodedata.lookup(description)
                asciiString += char
            except KeyError:
                pass  # removing "WITH ..." produced an invalid name  
        else:
            asciiString += char

    asciiString = unidecode(asciiString)

    return asciiString

# ----------------------------------------------------------------------------------------------------------------------------------
def matchCast(agntCastList, FILMDICT):
    ''' check IAFD web site for individual cast'''
    matchedCastDict = {}

    if FILMDICT['Year']:
        FILMDICT['Year'] = int(FILMDICT['Year'])

    for agntCast in agntCastList:
        compareAgntCast = re.sub(r'[\W\d_]', '', agntCast).strip().lower()
        log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Unmatched Cast Name'), agntCast))

        # compare against IAFD Cast List - retrieved from the film's url page
        matchedName = False
        for key, value in FILMDICT['Cast'].items():
            IAFDName = makeASCII(key)
            IAFDAlias = makeASCII(value['Alias'])
            IAFDCompareName = makeASCII(value['CompareName'])
            IAFDCompareAlias = makeASCII(value['CompareAlias'])

            # 1st full match against Cast Name
            matchedName = False
            if compareAgntCast == IAFDCompareName:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Matched with IAFD Cast: Full Match - Cast Name'), agntCast))
                matchedName = True
                break

            # 2nd full match against Cast Alias
            if compareAgntCast == IAFDCompareAlias:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Matched with IAFD Cast: Full Match - Cast Alias'), agntCast))
                matchedName = True
                break

            # 3rd partial match against Cast Name
            if compareAgntCast in IAFDCompareName:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Matched with IAFD Cast: Partial Match - Cast Name'), agntCast))
                matchedName = True
                break

            # 4th partial match against Cast Alias
            if compareAgntCast in IAFDCompareAlias:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Matched with IAFD Cast: Partial Match - Cast Alias'), agntCast))
                matchedName = True
                break

            # Lehvensten and Soundex Matching
            levDistance = len(agntCast.split()) + 1 if len(agntCast.split()) > 1 else 1 # Set Lehvenstein Distance - one change/word+1 of cast names or set to 1
            testName = IAFDName if levDistance > 1 else IAFDName.split()[0] if IAFDName else ''
            testAlias = IAFDAlias if levDistance > 1 else IAFDAlias.split()[0] if IAFDAlias else ''
            testNameType = 'Full Names' if levDistance > 1 else 'Forename'

            # 5th Lehvenstein Match against Cast Name
            levScore = String.LevenshteinDistance(agntCast, testName)
            matchedName = levScore <= levDistance
            if matchedName:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Levenshtein Match'), testNameType))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  IAFD Cast Name'), testName))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Agent Cast Name'), agntCast))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Score:Distance'), '{0}:{1}'.format(levScore, levDistance)))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Matched'), matchedName))
                break

            # 6th Lehvenstein Match against Cast Alias
            if testAlias:
                levScore = String.LevenshteinDistance(agntCast, testAlias)
                matchedName = levScore <= levDistance
                if matchedName:
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Levenshtein Match'), testNameType))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  IAFD Cast Alias'), testAlias))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Agent Cast Name'), agntCast))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Score:Distance'), '{0}:{1}'.format(levScore, levDistance)))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Matched'), matchedName))
                    break

            # 7th Soundex Matching on Cast Name
            soundIAFD = soundex(testName)
            soundAgent = soundex(agntCast)
            matchedName = soundIAFD == soundAgent
            if matchedName:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('SoundEx Match'), testNameType))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  IAFD Cast Name'), testName))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Agent Cast Name'), agntCast))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Score:Distance'), '{0}:{1}'.format(soundIAFD, soundAgent)))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Matched'), matchedName))
                break

            # 8th Soundex Matching on Cast Alias
            if testAlias:
                soundIAFD = soundex(testAlias)
                soundAgent = soundex(agntCast)
                matchedName = soundIAFD == soundAgent
                if matchedName:
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('SoundEx Match'), testNameType))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  IAFD Cast Alias'), testAlias))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Agent Cast Name'), agntCast))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Score:Distance'), '{0}:{1}'.format(soundIAFD, soundAgent)))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Matched'), matchedName))
                    break

        if matchedName: # we have a match, on to the next cast
            continue

        # the cast on the website has not matched to those listed against the film in IAFD. So search for the cast's entry on IAFD
        matchedCastDict[agntCast] = {'Photo': '', 'Role': IAFD_ABSENT, 'Alias': '', 'CompareName': '', 'CompareAlias': ''} # initialise cast member's dictionary
        agntCastLower = agntCast.lower()
        try:
            html = getURLElement(IAFD_SEARCH_URL.format(String.URLEncode(agntCast)), UseAdditionalResults=False)

            # IAFD presents Cast searches in career start order, this needs to be changed as cast whose main name does not match the search name 
            # will appear first in the list because he has an alias that matches the search name. we need to reorder so that those whose main name matches
            # the search name are listed first
            # xpath to get matching Cast Main Name and Alias: start with male cast, then include female actresses (bi films)
            xPathMatchMainMale = '//table[@id="tblMal"]/tbody/tr[td[2]/a[(contains(@href, "/perfid={0}") or (.) = "{1}" or translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="{2}")]]//ancestor::tr'.format(compareAgntCast, agntCast, agntCastLower)
            xPathMatchAliasMale = '//table[@id="tblMal"]/tbody/tr[contains(td[3], "{0}")]//ancestor::tr'.format(agntCast) 
            xPathMatchMainFemale = '//table[@id="tblFem"]/tbody/tr[td[2]/a[(contains(@href, "/perfid={0}") or (.) = "{1}" or translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="{2}")]]//ancestor::tr'.format(compareAgntCast, agntCast, agntCastLower)
            xPathMatchAliasFemale = '//table[@id="tblFem"]/tbody/tr[contains(td[3], "{0}")]//ancestor::tr'.format(agntCast) 

            combinedList = []
            if FILMDICT['AllMale'] == 'Yes':
                xpathList = [xPathMatchMainMale, xPathMatchAliasMale]
            elif FILMDICT['AllFemale'] == 'Yes':
                xpathList = [xPathMatchMainFemale, xPathMatchAliasFemale]
            else:
                xpathList = [xPathMatchMainMale, xPathMatchAliasMale, xPathMatchMainFemale, xPathMatchAliasFemale]

            for xPath in xpathList:
                try:
                    mainList = html.xpath(xPath)
                except:
                    log('UTILS :: Error: Bad Main Name xPath: %s', xPath)
                    mainList = []

                combinedList.extend(mainList)

            castList = [j for x, j in enumerate(combinedList) if j not in combinedList[:x]]
            castFound = len(castList)
            searchResult = '{0} found {1}'.format(castFound, ', <Skipping: too many found>' if castFound > 13 else '')
            log('UTILS :: {0: <29} {1}'.format('Search Result', searchResult))
            
            if castFound == 0 or castFound > 13:    #skip cast
                log(LOG_SUBLINE)
                continue

            log(LOG_BIGLINE)
            for cast in castList:
                # get cast details and compare to Agent cast
                try:
                    castName = cast.xpath('./td[2]/a/text()[normalize-space()]')[0]
                    compareCastName = re.sub(r'[\W\d_]', '', castName).strip().lower()
                    log('UTILS :: {0: <29} {1}'.format('Cast Name', '{0} / {1}'.format(castName, compareCastName)))
                except Exception as e:
                    log('UTILS :: Error: Could not read Cast Name: %s', e)
                    continue   # next cast with

                try:
                    castAliasList = cast.xpath('./td[3]/text()[normalize-space()]')[0].split(',')
                    castAliasList = [x.strip() for x in castAliasList if x]
                    compareCastAliasList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in castAliasList]
                except:
                    castAliasList = []
                    compareCastAliasList = []

                try:
                    startCareer = int(cast.xpath('./td[4]/text()[normalize-space()]')[0]) - 1 # set start of career to 1 year before for pre-releases
                except:
                    startCareer = 0

                try:
                    endCareer = int(cast.xpath('./td[5]/text()[normalize-space()]')[0]) + 1   # set end of career to 1 year after to cater for late releases
                except:
                    endCareer = 0

                matchedUsing = ''

                # match iafd row with Agent Cast entry
                matchedCast = True if compareAgntCast == compareCastName else False
                matchedUsing = 'Cast Name' if matchedCast else matchedUsing

                if not matchedCast and castAliasList:
                    matchedItem = [i for (i, x) in enumerate(compareCastAliasList) if x == compareAgntCast]
                    matchedCast = True if matchedItem else False
                    matchedUsing = 'Cast Alias' if matchedCast else matchedUsing

                # Check Career - if we have a match - this can only be done if the film is not a compilation and we have a Year
                # only do this if we have more than one actor returned
                if castFound > 1 and matchedCast and FILMDICT['Compilation'] == "No" and FILMDICT['Year']:
                    matchedCast = (startCareer <= FILMDICT['Year'] <= endCareer)
                    matchedUsing = 'Career' if matchedCast else matchedUsing

                if not matchedCast:
                    log('UTILS :: Error: Could not match Cast: %s', agntCast)
                    log(LOG_SUBLINE)
                    continue # to next cast in the returned iafd search cast list

                # now check if any processed IAFD Cast (FILMDICT) have an alias that matches with this cast
                # this will only work if the film has cast recorded against it on IAFD
                matchedCastWithIAFD = False
                for key, value in FILMDICT['Cast'].items():
                    if not value['CompareAlias']:
                        continue
                    checkName = key
                    checkAlias = value['Alias']
                    checkCompareAlias = value['CompareAlias']
                    if checkCompareAlias in compareCastAliasList:
                        matchedCastWithIAFD = True
                        log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Skipping: Recorded Cast Name'), '{0} AKA {1} also known by this name: {2}'.format(checkName, checkAlias, castName)))
                        matchedCastDict.pop(agntCast)
                        break

                if matchedCastWithIAFD:
                    break

                # we have an cast who satisfies the conditions
                castURL = IAFD_BASE + cast.xpath('./td[2]/a/@href')[0]
                castPhoto = cast.xpath('./td[1]/a/img/@src')[0] # Cast Name on agent website - retrieve picture
                castPhoto = '' if 'nophoto' in castPhoto or 'th_iafd_ad' in castPhoto else castPhoto.replace('thumbs/th_', '')
                castRole = IAFD_FOUND  # default to found

                log('UTILS :: {0: <29} {1}'.format('Cast Alias', castAliasList))
                log('UTILS :: {0: <29} {1}'.format('Career', '{0} - {1}'.format(startCareer, endCareer)))
                log('UTILS :: {0: <29} {1}'.format('Cast URL', castURL))
                log('UTILS :: {0: <29} {1}'.format('Cast Photo', castPhoto))
                log('UTILS :: {0: <29} {1}'.format('Cast Role', castRole))
                log('UTILS :: {0: <29} {1}'.format('Matched Using', matchedUsing))

                # Assign found values to dictionary
                myDict = {}
                myDict['Photo'] = castPhoto
                myDict['Role'] = castRole
                myDict['Alias'] = ''
                myDict['CompareName'] = compareCastName
                myDict['CompareAlias'] = compareCastAliasList
                matchedCastDict[agntCast] = myDict

                log(LOG_SUBLINE)
                break   # # break out to next cast in agent cast list

        except Exception as e:
            log('UTILS :: Error: Cannot Process IAFD Cast Search Results: %s', e)
            log(LOG_SUBLINE)
            continue    # next cast in agent cast list  (agntCastList)

    return matchedCastDict
# ----------------------------------------------------------------------------------------------------------------------------------
def matchDirectors(agntDirectorList, FILMDICT):
    ''' check IAFD web site for individual directors'''
    matchedDirectorDict = {}

    if FILMDICT['Year']:
        FILMDICT['Year'] = int(FILMDICT['Year'])

    for agntDirector in agntDirectorList:
        compareAgntDirector = re.sub(r'[\W\d_]', '', agntDirector).strip().lower()

        # compare against IAFD Director List - retrieved from the film's url page
        matchedName = False
        for key, value in FILMDICT['Directors'].items():
            IAFDName = makeASCII(key)
            IAFDAlias = [makeASCII(x) for x in value['Alias']] if type(value['Alias']) is list else makeASCII(value['Alias'])
            IAFDCompareName = [makeASCII(x) for x in value['CompareName']] if type(value['CompareName']) is list else makeASCII(value['CompareName'])
            IAFDCompareAlias = [makeASCII(x) for x in value['CompareAlias']] if type(value['CompareAlias']) is list else makeASCII(value['CompareAlias'])

            # 1st full match against director name
            matchedName = False
            if compareAgntDirector == IAFDCompareName:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Matched with IAFD Director: Full Match - Director Name'), agntDirector))
                matchedName = True
                break

            # 2nd full match against director alias
            if [x for x in IAFDCompareAlias if x == compareAgntDirector]:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Matched with IAFD Director: Full Match - Director Alias'), agntDirector))
                matchedName = True
                break

            # 3rd partial match against director name
            if compareAgntDirector in IAFDCompareName:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Matched with IAFD Director: Partial Match - Director Name'), agntDirector))
                matchedName = True
                break

            # 4th partial match against director alias
            if compareAgntDirector in IAFDCompareAlias:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Matched with IAFD Director: Partial Match - Director Alias'), agntDirector))
                matchedName = True
                break

            # Lehvensten and Soundex Matching
            levDistance = len(agntDirector.split()) + 1 if len(agntDirector.split()) > 1 else 1 # Set Lehvenstein Distance - one change/word+1 of cast names or set to 1
            testNameType = 'Full Names' if levDistance > 1 else 'Forename' 
            testName = IAFDName if levDistance > 1 else IAFDName.split()[0] if IAFDName else ''
            if IAFDAlias is list:
                testAlias = [x if levDistance > 1 else x.split()[0] for x in IAFDAlias]
            else:
                testAlias = IAFDAlias if levDistance > 1 else IAFDAlias.split()[0] if IAFDAlias else ''

            # 5th Lehvenstein Match against Director Name
            levScore = String.LevenshteinDistance(agntDirector, testName)
            matchedName = levScore <= levDistance
            if matchedName:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Levenshtein Match'), testNameType))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  IAFD Director Name'), testName))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Agent Director Name'), agntDirector))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Score:Distance'), '{0}:{1}'.format(levScore, levDistance)))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Matched'), matchedName))
                break

            # 6th Lehvenstein Match against Director Alias
            if testAlias:
                levScore = [String.LevenshteinDistance(agntDirector, x) for x in testAlias] if type(testAlias) is list else String.LevenshteinDistance(agntDirector, testAlias)
                if type(levScore) is list:
                    for x in levScore:
                        matchedName = x <= levDistance
                        if matchedName:
                            break
                else:
                    matchedName = levScore <= levDistance
                
                if matchedName:
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Levenshtein Match'), testNameType))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  IAFD Director Alias'), testAlias))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Agent Director Name'), agntDirector))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Score:Distance'), '{0}:{1}'.format(levScore, levDistance)))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Matched'), matchedName))
                    break

            # 7th Soundex Matching on Director Name
            soundIAFD = [soundex(x) for x in testName] if type(testName) is list else soundex(testName)
            soundAgent = soundex(agntDirector)
            matchedName = True if soundAgent in soundIAFD else False
            if matchedName:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('SoundEx Match'), testNameType))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  IAFD Director Name'), testName))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Agent Director Name'), agntDirector))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Score:Distance'), '{0}:{1}'.format(soundIAFD, soundAgent)))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Matched'), matchedName))
                break

            # 8th Soundex Matching on Director Alias
            if testAlias:
                soundIAFD = [soundex(x) for x in testAlias] if type(testAlias) is list else soundex(testAlias)
                soundAgent = soundex(agntDirector)
                matchedName = True if soundAgent in soundIAFD else False
                if matchedName:
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('SoundEx Match'), testNameType))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  IAFD Director Alias'), testAlias))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Agent Director Name'), agntDirector))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Score:Distance'), '{0}:{1}'.format(soundIAFD, soundAgent)))
                    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('  Matched'), matchedName))
                    break

        if matchedName: # we have a match, on to the next director
            continue

        # the director on the website has not matched to those listed against the film in IAFD. So search for the director's entry on IAFD
        matchedDirectorDict[agntDirector] = '' # initialise director's dictionary
        try:
            html = getURLElement(IAFD_SEARCH_URL.format(String.URLEncode(agntDirector)), UseAdditionalResults=False)

            # IAFD presents director searches in career start order, this needs to be changed as directors whose main name does not match the search name 
            # will appear first in the list because he has an alias that matches the search name. we need to reorder so that those whose main name matches
            # the search name are listed first
            # xpath to get matching director Main Name and Alias
            xPathMatchMain = '//table[@id="tblDir"]/tbody/tr[td[2]="{0}"]//ancestor::tr'.format(agntDirector)
            xPathMatchAlias = '//table[@id="tblDir"]/tbody/tr[contains(td[3], "{0}")]//ancestor::tr'.format(agntDirector)
            try:
                mainList = html.xpath(xPathMatchMain)
            except:
                log('UTILS :: Error: Bad Main Name xPath')
                mainList = []
            try:
                aliasList = html.xpath(xPathMatchAlias)
            except:
                log('UTILS :: Error: Bad Alias xPath')
                aliasList = []

            combinedList = mainList + aliasList
            directorList = [i for x, i in enumerate(combinedList) if i not in combinedList[:x]]
            directorsFound = len(directorList)
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Search Result'), '{0}{1}'.format(directorsFound, ', [Skipping: too many found]' if directorsFound > 5 else '')))
            if directorsFound > 5:
                log(LOG_SUBLINE)
                continue

            log(LOG_BIGLINE)
            for director in directorList:
                # get director details and compare to Agent director
                try:
                    directorName = director.xpath('./td[2]/a/text()[normalize-space()]')[0]
                    compareDirectorName = re.sub(r'[\W\d_]', '', directorName).strip().lower()
                except Exception as e:
                    log('UTILS :: Error: Could not read Director Name: %s', e)
                    continue   # next director

                try:
                    directorAliasList = director.xpath('./td[3]/text()[normalize-space()]')[0].split(',')
                    directorAliasList = [x.strip() for x in directorAliasList if x]
                    compareDirectorAliasList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in directorAliasList]
                except:
                    directorAliasList = []
                    compareDirectorAliasList = []

                try:
                    startCareer = int(director.xpath('./td[4]/text()[normalize-space()]')[0]) # set start of career
                except:
                    startCareer = 0

                try:
                    endCareer = int(director.xpath('./td[5]/text()[normalize-space()]')[0])   # set end of career
                except:
                    endCareer = 0

                matchedUsing = ''

                # match iafd row with Agent Director entry
                matchedDirector = True if compareAgntDirector == compareDirectorName else False
                matchedUsing = 'Director Name' if matchedDirector else matchedUsing

                if not matchedDirector and directorAliasList:
                    matchedItem = [i for (i, x) in enumerate(compareDirectorAliasList) if x == compareAgntDirector]
                    matchedDirector = True if matchedItem else False
                    matchedUsing = 'Director Alias' if matchedDirector else matchedUsing

                # Check Career - if we have a match - this can only be done if we have a Year
                # only do this if we have more than one director returned
                if directorsFound > 1 and matchedDirector and FILMDICT['Year']:
                    matchedDirector = (startCareer <= FILMDICT['Year'] <= endCareer)
                    matchedUsing = 'Career' if matchedDirector else matchedUsing

                if not matchedDirector:
                    log('UTILS :: Error: Could not match Director: %s', agntDirector)
                    log(LOG_SUBLINE)
                    continue # to next director in the returned iafd search director list

                # now check if any processed IAFD Directors (FILMDICT) have an alias that matches with this director
                # this will only work if the film has directors recorded against it on IAFD
                matchedDirectorWithIAFD = False
                for key, value in FILMDICT['Directors'].items():
                    if not value['CompareAlias']:
                        continue
                    checkName = key
                    checkAlias = value['Alias']
                    checkCompareAlias = value['CompareAlias']
                    if checkCompareAlias in compareDirectorAliasList:
                        matchedDirectorWithIAFD = True
                        log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Skipping: Recorded Director Name'), '{0} AKA {1} also known by this name: {2}'.format(checkName, checkAlias, directorName)))
                        matchedDirectorDict.pop(agntDirector)
                        break

                if matchedDirectorWithIAFD:
                    break

                # we have an director who matches the conditions
                directorURL = IAFD_BASE + director.xpath('./td[2]/a/@href')[0]
                directorPhoto = director.xpath('./td[1]/a/img/@src')[0] # director name on agent website - retrieve picture
                directorPhoto = '' if 'th_iafd_ad.gif' in directorPhoto else directorPhoto.replace('thumbs/th_', '')

                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Director'), '{0} / {1}'.format(directorName, compareDirectorName)))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Alias'), directorAliasList  if directorAliasList else 'No Director Alias Recorded'))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Start Career'), startCareer if startCareer > 0 else 'N/A'))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('End Career'), endCareer if endCareer > 0 else 'N/A'))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Director URL'), directorURL))
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Director Photo'), directorPhoto))

                # Assign values to dictionary
                myDict = {}
                myDict['Photo'] = directorPhoto
                myDict['Alias'] = directorAliasList
                myDict['CompareName'] = compareDirectorName
                myDict['CompareAlias'] = compareDirectorAliasList
                matchedDirectorDict[agntDirector] = myDict

                break   # break out to next director in agent director list

        except Exception as e:
            log('UTILS :: Error: Cannot Process IAFD Director Search Results: %s', e)
            log(LOG_SUBLINE)
            continue    # next director in agent director list  (allDirectorList)

    return matchedDirectorDict

# -------------------------------------------------------------------------------------------------------------------------------
def matchFilename(media):
    ''' Check filename on disk corresponds to regex preference format '''
    filmVars = {}
    filmVars['Agent'] = PLUGIN_LOG_TITLE

    # file matching pattern
    filmPath = media.items[0].parts[0].file
    filmVars['FileName'] = os.path.splitext(os.path.basename(filmPath))[0]

    # film duration 
    filmDuration = 0.0
    try:
        for part in media.items[0].parts:
            filmDuration += long(getattr(part, 'duration'))
        filmDuration = int(filmDuration / 60000)   # convert miliseconds to full minutes
    except:
        filmDuration = 0.0

    filmVars['Duration'] = str(filmDuration) if filmDuration > 0 else ''

    REGEX = '^\((?P<fnSTUDIO>[^()]*)\) - (?P<fnTITLE>.+?)?(?: \((?P<fnYEAR>\d{4})\))?( - \[(?P<fnCAST>[^\]]*)\])?(?: - (?i)(?P<fnSTACK>(cd|disc|disk|dvd|part|pt|scene) [1-8]))?$'
    pattern = re.compile(REGEX)
    matched = pattern.search(filmVars['FileName'])
    if not matched:
        raise Exception('<File Name [{0}] not in the expected format: (Studio) - Title [(Year)] [- cd|disc|disk|dvd|part|pt|scene 1..8]>'.format(filmVars['FileName']))

    groups = matched.groupdict()
    log('UTILS :: File Name REGEX Matched Variables:')
    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Studio'), groups['fnSTUDIO']))
    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Title'), groups['fnTITLE']))
    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Year'), groups['fnYEAR']))
    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Cast'), groups['fnCAST']))
    log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Stack'), groups['fnSTACK']))
    log(LOG_SUBLINE)

    filmVars['Format'] = '(Studio) - Title' if groups['fnYEAR'] is None else '(Studio) - Title (Year)'
    filmVars['Studio'] = groups['fnSTUDIO'].split(';')[0].strip()
    filmVars['CompareStudio'] = NormaliseComparisonString(filmVars['Studio'])
    filmVars['IAFDStudio'] = groups['fnSTUDIO'].split(';')[1].strip() if ';' in groups['fnSTUDIO'] else ''
    filmVars['CompareIAFDStudio'] = NormaliseComparisonString(filmVars['IAFDStudio']) if filmVars['IAFDStudio'] else ''

    filmVars['Title'] =  groups['fnTITLE']
    filmVars['SearchTitle'] = filmVars['Title']
    filmVars['ShortTitle'] = filmVars['Title']
    filmVars['CompareTitle'] = [sortAlphaChars(NormaliseComparisonString(filmVars['ShortTitle']))]

    # if film starts with a determinate, strip the detrminate and add the title to the comparison list
    pattern = ur'^(The |An |A )'
    matched = re.search(pattern, filmVars['ShortTitle'], re.IGNORECASE)  # match against whole string
    if matched:
        filmVars['CompareTitle'].append(sortAlphaChars(NormaliseComparisonString(re.sub(pattern, '', filmVars['ShortTitle'], flags=re.IGNORECASE))))

    filmVars['IAFDTitle'] =  makeASCII(filmVars['Title'])
    filmVars['IAFDCompareTitle'] = filmVars['CompareTitle']

    filmVars['Year'] = groups['fnYEAR'] if groups['fnYEAR'] is not None else ''
    filmVars['Stacked'] = 'Yes' if groups['fnSTACK'] is not None else 'No'

    # if cast list exists - extract from filename as a list of names
    filmVars['FilenameCast'] = re.split(r',\s*', groups['fnCAST']) if groups['fnCAST'] else ''

    # default to 31 Dec of Filename year if Year provided in filename and is not 1900
    filmVars['CompareDate'] = datetime(int(filmVars['Year']), 12, 31).strftime(DATEFORMAT) if filmVars['Year'] else ''

    # For this title: (Raging Stallion Studios) - Hardcore Fetish Series - Pissing 1 - Piss Off (2009)
    #    Collections: [Hardcore Fetish Series, Pissing]
    #         Series: [Pissing 1]
    #    Short Title: Piss Off
    collections = []
    if COLSTUDIO:
        collections.append(filmVars['Studio'])                # All films have their Studio Name as a collection
    series = []
    splitFilmTitle = filmVars['Title'].split(' - ')
    splitFilmTitle = [x.strip() for x in splitFilmTitle]
    splitCount = len(splitFilmTitle) - 1
    for index, partTitle in enumerate(splitFilmTitle):
        pattern = r'(?<![-.])\b[0-9]+\b(?!\.[0-9])$'           # series matching = whole separate number at end of string
        matchedSeries = re.subn(pattern, '', partTitle)
        if matchedSeries[1]:
            if COLTITLE:
                collections.insert(0, matchedSeries[0].strip()) # e.g. Pissing
            series.insert(0, partTitle)                         # e.g. Pissing 1
            if index < splitCount:                              # only blank out series info in title if not last split
                splitFilmTitle[index] = ''
        else:
            if index < splitCount:                              # only add to collection if not last part of title e.g. Hardcore Fetish Series
                splitFilmTitle[index] = ''
                if COLTITLE:
                    collections.insert(0, partTitle)

    filmVars['Collection'] = collections
    filmVars['Series'] = series
    if filmVars['Agent'] != 'IAFD':
        filmVars['Title'] = filmVars['Title'] if '- ' not in filmVars['Title'] else re.sub(ur' - |- ', ': ', filmVars['Title']) # put colons back in as they can't be used in the filename
        pattern = ur'[' + re.escape(''.join(['.', '!', '%', '?'])) + ']+$'
        filmVars['ShortTitle'] = re.sub(pattern, '', ' '.join(splitFilmTitle).strip())                                          # strip punctuations at end of string
        if filmVars['ShortTitle'] not in filmVars['CompareTitle']:
            filmVars['CompareTitle'].append(sortAlphaChars(NormaliseComparisonString(filmVars['ShortTitle'])))
        filmVars['SearchTitle'] =  filmVars['ShortTitle']
    
    # if search title ends with a "1" drop it... as many first in series omit the number
    pattern = ur' 1$'
    matched = re.search(pattern, filmVars['SearchTitle'])  # match against whole string
    if matched:
        filmVars['SearchTitle'] = filmVars['SearchTitle'][:matched.start()]

    # print out dictionary values / normalise unicode
    printFilmInformation(filmVars)

    return filmVars

# ----------------------------------------------------------------------------------------------------------------------------------
def matchDuration(siteDuration, FILMDICT, matchDuration=True):
    ''' match file duration against iafd duration '''
    siteDuration = siteDuration.strip()
    fileDuration = int(FILMDICT['Duration'])
    testDuration = True

    if siteDuration and matchDuration == True and fileDuration > 0:
        if ':' in siteDuration:
            # convert hours and minutes to minutes if time is in format hh:mm:ss OR mm:ss (assume film can not be longer than 5 hours)
            siteDuration = siteDuration.split(':')
            siteDuration = [int(float(x)) for x in siteDuration]
            if len(siteDuration) == 3:
                siteDuration = siteDuration[0] * 60 + siteDuration[1]
            elif len(siteDuration) == 2 and siteDuration[0] <= 5:
                siteDuration = siteDuration[0] * 60 + siteDuration[1]
            else:
                siteDuration = siteDuration[0]
        else:
            # assume time is in minutes: first convert to float incase there is a decimal point
            siteDuration = int(float(siteDuration))

        testDuration = 'Passed' if abs(fileDuration - siteDuration) <= DURATIONDX else 'Failed'
    else:
        testDuration = 'Skipped - Duration Requirements Not Met'

    log('UTILS :: Site Duration                 %s Minutes', siteDuration)
    log('UTILS :: File Duration                 %s Minutes', fileDuration)
    log('UTILS :: Acceptable Deviation          ±%s Minutes', DURATIONDX)
    log('UTILS :: Duration Comparison Test      [%s]', testDuration)

    if testDuration == 'Failed':
        raise Exception('<Duration Match Failure!>')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def matchReleaseDate(siteReleaseDate, FILMDICT):
    ''' match file year against website release date: return formatted site date if no error or default to formated file date '''
    # if a year has being provided - default to 31st December of that year
    siteReleaseDate = datetime.strptime(siteReleaseDate + '1231', '%Y%m%d') if len(siteReleaseDate) == 4 else datetime.strptime(siteReleaseDate, DATEFORMAT)

    # there can not be a difference more than 366 days between FileName Date and siteReleaseDate
    if FILMDICT['CompareDate']:
        fileReleaseDate = datetime.strptime(FILMDICT['CompareDate'], DATEFORMAT)
        dx = abs((fileReleaseDate - siteReleaseDate).days)
        testReleaseDate = 'Failed' if dx > 366 else 'Passed'

        log('UTILS :: Site Release Date             %s', siteReleaseDate.strftime('%Y %m %d'))
        log('UTILS :: File Release Date             %s', fileReleaseDate.strftime('%Y %m %d'))
        log('UTILS :: Difference in Days            %s', dx)
        log('UTILS :: Release Date Comparison Test  [%s]', testReleaseDate )

        if dx > 366:
            raise Exception('<Release Date Match Failure!>')

    # reset comparison date to above scrapping result
    FILMDICT['CompareDate'] = siteReleaseDate.strftime(DATEFORMAT)
    FILMDICT['Year'] = siteReleaseDate.year

    return siteReleaseDate

# ----------------------------------------------------------------------------------------------------------------------------------
def matchStudio(siteStudio, FILMDICT, useAgent=True):
    ''' match file studio name against website studio/iafd name: Boolean Return '''
    compareSiteStudio = NormaliseComparisonString(siteStudio)
    dtStudio = FILMDICT['Studio'] if useAgent else FILMDICT['IAFDStudio']
    dtCompareStudio = FILMDICT['CompareStudio'] if useAgent else FILMDICT['CompareIAFDStudio']

    testStudio = 'Full Match' if compareSiteStudio == dtCompareStudio else 'Partial Match' if compareSiteStudio in dtCompareStudio or dtCompareStudio in compareSiteStudio else 'Failed Match'

    log('UTILS :: Match File Studio Against     %s Studio Name', 'Agent' if useAgent else 'IAFD')
    log('UTILS :: Site Studio                   %s', siteStudio)
    log('UTILS :: File Studio                   %s', dtStudio)
    log('UTILS :: Studio Comparison Test        [%s]', testStudio)

    if testStudio == 'Failed Match':
        raise Exception('<Studio Match Failure!>')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def matchTitle(siteTitle, FILMDICT):
    ''' match file title against website/iafd title: Boolean Return '''
    amendedSiteTitle = NormaliseComparisonString(siteTitle)
    amendedShortTitle = NormaliseComparisonString(FILMDICT['ShortTitle'])

    if amendedShortTitle in amendedSiteTitle:
        pattern = re.compile(re.escape(amendedShortTitle), re.IGNORECASE)
        amendedSiteTitle = '{0}{1}'.format(re.sub(pattern, '', amendedSiteTitle).strip(), amendedShortTitle) 

    sortedSiteTitle = sortAlphaChars(amendedSiteTitle)
    testTitle = 'Passed' if sortedSiteTitle in FILMDICT['CompareTitle'] else 'Passed (IAFD)' if sortedSiteTitle in FILMDICT['IAFDCompareTitle'] else 'Failed'

    log('UTILS :: Site Title                    %s', siteTitle)
    log('UTILS :: Amended Site Title            %s', amendedSiteTitle)
    log('UTILS :: File Title                    %s', FILMDICT['Title'])
    log('UTILS :: File Short Title              %s', FILMDICT['ShortTitle'])
    log('UTILS :: Compare Site Title            %s', sortedSiteTitle)
    log('UTILS ::         Agent Title           %s', FILMDICT['CompareTitle'])
    log('UTILS ::         IAFD Title            %s', FILMDICT['IAFDCompareTitle'])
    log('UTILS :: Title Comparison Test         [%s]', testTitle)

    if testTitle == 'Failed':
        raise Exception('<Title Match Failure!>')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def NormaliseComparisonString(myString):
    ''' Normalise string for, strip uneeded characters for comparison of web site values to file name regex group values '''
    # Check if string has roman numerals as in a series; note the letter I will be converted
    myString = '{0} '.format(myString)  # append space at end of string to match last characters 
    pattern = '\s(?=[MDCLXVI])M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3})$'
    matches = re.findall(pattern, myString, re.IGNORECASE)  # match against string
    if matches:
        RomanValues = {'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000}
        for count, match in enumerate(matches):
            myRoman = ''.join(match).upper()
            log('UTILS :: Found Roman Numeral: {0}.. {1} len[{2}]'.format(count, myRoman, len(myRoman)))
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

    # replace ampersand with 'and'
    myString = myString.replace('&', 'and')

    # replace ": " with " - "
    myString = myString.replace(': ', ' - ')

    # change string to ASCII
    myString = makeASCII(myString)

    # strip domain suffixes, vol., volume from string, standalone '1's'
    pattern = ur'[.]([a-z]{2,3}|co[.][a-z]{2})|Vol[.]|Vols[.]|Nr[.]|\bVolume\b|\bVolumes\b|(?<!\d)1(?!\d)|\bPart\b|[^A-Za-z0-9]+'
    myString = re.sub(pattern, '', myString, flags=re.IGNORECASE)

    return myString

# ----------------------------------------------------------------------------------------------------------------------------------
def printFilmInformation(myDictionary):
    # print out dictionary values / normalise unicode
    log('UTILS :: Film Dictionary Variables:')
    for key in sorted(myDictionary.keys()):
        myDictionary[key] = list(dict.fromkeys(myDictionary[key])) if type(myDictionary[key]) is list else myDictionary[key]
        log('UTILS :: {0: <29} {1}'.format('{0}:'.format(key), myDictionary[key]))

# ----------------------------------------------------------------------------------------------------------------------------------
def setDefaultMetadata(metadata, FILMDICT):
    '''
    The following bits of metadata need to be established and used to update the movie on plex
      1.  Metadata that is set by Agent as default
          a. Studio               : From studio group of filename - no need to process this as above
          b. Title                : From title group of filename - no need to process this as is used to find it on website
          c. Tag line             : Corresponds to the url of movie
          d. Originally Available : set from metadata.id (search result)
          e. Content Rating       : Always X
          f. Content Rating Age   : Always 18
          g. Collection Info      : From title group of filename 
    '''
    # 1a.   Set Studio
    metadata.studio = FILMDICT['Studio']
    log('UPDATE:: {0: <29} {1}'.format('{0}:'.format('Studio'), metadata.studio))

    # 1b.   Set Title
    metadata.title = FILMDICT['Title']
    log('UPDATE:: {0: <29} {1}'.format('{0}:'.format('Title'), metadata.title))

    # 1c/d. Set Tagline/Originally Available from metadata.id
    metadata.tagline = FILMDICT['SiteURL']
    log('UPDATE:: {0: <29} {1}'.format('{0}:'.format('Tagline'), metadata.tagline))

    if FILMDICT['Year']:
        metadata.originally_available_at = datetime.strptime(FILMDICT['CompareDate'], DATEFORMAT)
        metadata.year = metadata.originally_available_at.year
        log('UPDATE:: {0: <29} {1}'.format('{0}:'.format('Original Available Date'), metadata.originally_available_at))

    # 1e/f. Set Content Rating to Adult/18 years
    metadata.content_rating = 'X'
    metadata.content_rating_age = 18
    log('UPDATE:: {0: <29} {1}'.format('{0}:'.format('Content: Rating - Age'), 'X - 18'))

    # 1g. Collection
    if COLCLEAR:
        metadata.collections.clear()

    collections = FILMDICT['Collection']
    for collection in collections:
        metadata.collections.add(collection)
    log('UPDATE:: {0: <29} {1}'.format('{0}:'.format('Collection from filename'), collections))

# ----------------------------------------------------------------------------------------------------------------------------------
def sortAlphaChars(myString):
    numbers = re.sub('[^0-9]','', myString)
    letters = re.sub('[0-9]','', myString)
    myString = '{0}{1}'.format(numbers, ''.join(sorted(letters)))

    return myString

# ----------------------------------------------------------------------------------------------------------------------------------
def soundex(name, len=5):
    ''' soundex module conforming to Odell-Russell algorithm '''
    # digits holds the soundex values for the alphabet
    soundex_digits = '01230120022455012623010202'   # to match against eng + spanish use  '01230120002055012623010202'
    sndx = ''
    firstChar = ''

    # Translate letters in name to soundex digits
    name = name.upper()
    for i, char in enumerate(name):
        if char.isalpha():
            if not firstChar: firstChar = char   # Remember first letter
            d = soundex_digits[ord(char)-ord('A')]
            # Duplicate consecutive soundex digits are skipped
            if not sndx or (d != sndx[-1]):
                sndx += d

    # Replace first digit with first letter
    sndx = firstChar + sndx[1:]

    # Remove all 0s from the soundex code
    sndx = sndx.replace('0', '')

    # Return soundex code truncated or 0-padded to len characters
    return (sndx + (len * '0'))[:len]

# ----------------------------------------------------------------------------------------------------------------------------------
def TranslateString(myString, siteLanguage, plexLibLanguageCode, detectLanguage):
    ''' Translate string into Library language '''
    from google_translate import GoogleTranslator

    myString = myString.strip()
    saveString = myString
    msg = ''
    if plexLibLanguageCode == 'xn' or plexLibLanguageCode == 'xx':    # no language or language unknown
        log('UTILS :: Run Translation: [Skip] - Library Language: [%s]', 'No Language' if plexLibLanguageCode == 'xn' else 'Unknown')
    elif myString:
        dictLanguages = {'af' : 'afrikaans', 'sq' : 'albanian', 'ar' : 'arabic', 'hy' : 'armenian', 'az' : 'azerbaijani', 'eu' : 'basque', 'be' : 'belarusian', 'bn' : 'bengali', 'bs' : 'bosnian', 
                         'bg' : 'bulgarian', 'ca' : 'catalan', 'ceb' : 'cebuano', 'ny' : 'chichewa', 'zh-cn' : 'chinese simplified', 'zh-tw' : 'chinese traditional', 'zh-cn' : '#chinese simplified', 
                         'zh-tw' : '#chinese traditional', 'hr' : 'croatian', 'cs' : 'czech', 'da' : 'danish', 'nl' : 'dutch', 'en' : 'english', 'eo' : 'esperanto', 'et' : 'estonian', 
                         'tl' : 'filipino', 'fi' : 'finnish', 'fr' : 'french', 'gl' : 'galician', 'ka' : 'georgian', 'de' : 'german', 'el' : 'greek', 'gu' : 'gujarati', 'ht' : 'haitian creole', 
                         'ha' : 'hausa', 'iw' : 'hebrew', 'hi' : 'hindi', 'hmn' : 'hmong', 'hu' : 'hungarian', 'is' : 'icelandic', 'ig' : 'igbo', 'id' : 'indonesian', 'ga' : 'irish', 
                         'it' : 'italian', 'ja' : 'japanese', 'jw' : 'javanese', 'kn' : 'kannada', 'kk' : 'kazakh', 'km' : 'khmer', 'ko' : 'korean', 'lo' : 'lao', 'la' : 'latin', 'lv' : 'latvian', 
                         'lt' : 'lithuanian', 'mk' : 'macedonian', 'mg' : 'malagasy', 'ms' : 'malay', 'ml' : 'malayalam', 'mt' : 'maltese', 'mi' : 'maori', 'mr' : 'marathi', 'mn' : 'mongolian', 
                         'my' : 'myanmar (burmese)', 'ne' : 'nepali', 'no' : 'norwegian', 'fa' : 'persian', 'pl' : 'polish', 'pt' : 'portuguese', 'ma' : 'punjabi', 'ro' : 'romanian', 'ru' : 'russian', 
                         'sr' : 'serbian', 'st' : 'sesotho', 'si' : 'sinhala', 'sk' : 'slovak', 'sl' : 'slovenian', 'so' : 'somali', 'es' : 'spanish', 'su' : 'sudanese', 'sw' : 'swahili', 'sv' : 'swedish', 
                         'tg' : 'tajik', 'ta' : 'tamil', 'te' : 'telugu', 'th' : 'thai', 'tr' : 'turkish', 'uk' : 'ukrainian', 'ur' : 'urdu', 'uz' : 'uzbek', 'vi' : 'vietnamese', 'cy' : 'welsh', 'yi' : 'yiddish', 'yo' : 'yoruba', 'zu' : 'zulu'}
        language = dictLanguages.get(plexLibLanguageCode)

        translator = GoogleTranslator()
        runTranslation = 'Yes' if plexLibLanguageCode != siteLanguage else 'No'
        msg = '[{0}] - Site Language: [{1}] to Library Language: [{2}]'.format(runTranslation, dictLanguages.get(siteLanguage), language)
        if detectLanguage and runTranslation == 'No':
            try:
                detectString = re.findall(ur'.*?[.!?]', myString)[:4]   # take first 4 sentences of string to detect language
                detectString = ''.join(detectString)
                if detectString:
                    detectedTextLanguage = translator.detect(detectString)
                    runTranslation = 'Yes' if language != detectedTextLanguage else 'No'
                    msg = '[{0}] - Detected Language: [{1}] to Library Language: [{2}]'.format(runTranslation, detectedTextLanguage, language)
                else:
                    msg = '[{0}] - Not enough available text to detect language'.format(runTranslation)
            except Exception as e:
                log('UTILS :: Error Detecting Text Language: %s', e)

        log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Run Translation'), msg))

        if runTranslation == 'Yes':
            if language is not None:
                try:
                    myString = translator.translate(myString, language)
                    myString = saveString if myString is None else myString
                    log('UTILS :: %s Text: %s', 'Untranslated' if myString == saveString else 'Translated', myString)
                except Exception as e:
                    log('UTILS :: Error Translating Text: %s', e)
            else:
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Translation Skipped'), '{0}'.format(plexLibLanguageCode)))

    myString = myString if myString else ' ' # return single space to initialise metadata summary field
    return myString