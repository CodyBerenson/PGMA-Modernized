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
                    impoved cast matching - if a film is all male, Girl cast will not be scrapped
                    new code to strip Roman Numeral Suffices on IAFD Titles to increase matching opportunities
    05 Jun 2022     Error - incomplete raise statement in getCast and getDirectors
                    new routines to scrape chapter info from aebn, dvdgayempire and gay hot movies
    19 Aug 2022     New routines to implement Tidy Genres, Countries Collation, processing set and date time data via json
                    simplified routine to match cast and directors and Improved duplicate cast/director matching
                    Implemented Filtering of results in IAFD
                    improved logging
                    added routines to tidy genres and country files located in the plug-ins directory
                    use of sets to improve processing speed and reduce error logging
                    New routine to match film Titles
                    standardised update metadata routine
                    implemented Collection Grouping - Preference based
'''
# ----------------------------------------------------------------------------------------------------------------------------------
import cloudscraper, fake_useragent, os, platform, re, subprocess, unicodedata
from datetime import datetime, timedelta
from unidecode import unidecode
from urlparse import urlparse
from textwrap import wrap

# IAFD Related variables
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/results.asp?searchtype=comprehensive&searchstring={0}'
IAFD_FILTER = '&FirstYear={0}&LastYear={1}&Submit=Filter'
IAFD_ABSENT = u'\U0000274C'        # red cross mark - not on IAFD
IAFD_FOUND = u'\U00002705'         # heavy white tick on green - on IAFD

# Plex System Variables/Methods
PlexSupportPath = Core.app_support_path
PlexLoadFile = Core.storage.load

# log section separators
LOG_BIGLINE = '-' * 140
LOG_SUBLINE = '      ' + '-' * 100
LOG_ASTLINE = '*' * 140

# getHTTPRequest variable
scraper = None
# ----------------------------------------------------------------------------------------------------------------------------------
def findTidy(myItem):
    myItem = myItem.lower()
    myNewItem = TIDYDICT[myItem] if myItem in TIDYDICT else ''
    if myNewItem == 'x':
        myNewItem = None
    return myNewItem

# ----------------------------------------------------------------------------------------------------------------------------------
def getCast(agntCastList, FILMDICT):
    ''' Process and match cast list against IAFD '''

    if not agntCastList and 'Cast' not in FILMDICT: # nowt to do
        raise Exception('< No Cast Found! >')

    # clean up the Cast List make a copy then clear
    agntCastList = [x.split('(')[0].strip() if '(' in x else x.strip() for x in agntCastList]
    agntCastList = [String.StripDiacritics(x) for x in agntCastList]
    agntCastList = [x for x in agntCastList if x]
    log('UTILS :: {0:<29} {1}'.format('Agent Cast List', '{0:>2} - {1}'.format(len(agntCastList), agntCastList)))

    excludeList = [string for string in agntCastList if [substr for substr in agntCastList if substr in string and substr != string]]
    if excludeList:
        agntCastList = [x for x in agntCastList if x not in excludeList]
        log('UTILS :: {0:<29} {1}'.format('Exclude', '{0:>2} - {1}'.format(len(excludeList), excludeList)))
        log('UTILS :: {0:<29} {1}'.format('Result', '{0:>2} - {1}'.format(len(agntCastList), agntCastList)))

    # strip all non alphabetic characters from cast names / aliases so as to compare them to the list obtained from the website e.g. J.T. Sloan will render as jtsloan
    castDict = FILMDICT['Cast']
    log('UTILS :: {0:<29} {1}'.format('IAFD Cast List', '{0:>2} - {1}'.format(len(castDict), sorted(castDict.keys()))))

    IAFDCastList = [(re.sub(r'[\W\d_]', '', k).strip().lower(), re.sub(r'[\W\d_]', '', v['Alias']).strip().lower()) for k, v in castDict.items()] # list of tuples [name, alias]

    # remove entries from the website cast list which have been found on IAFD leaving unmatched cast
    unmatchedCastList = [x for x in agntCastList if re.sub(r'[\W\d_]', '', x).strip().lower() not in (item for namealias in IAFDCastList for item in namealias)]
    log('UTILS :: {0:<29} {1}'.format('Unmatched Cast List', '{0:>2} - {1}'.format(len(unmatchedCastList), unmatchedCastList)))
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

    if not agntDirectorList and 'Directors' not in FILMDICT: # nowt to do
        raise Exception('< No Directors Found! >')

    # clean up the Director List
    agntDirectorList = [x.split('(')[0].strip() if '(' in x else x.strip() for x in agntDirectorList]
    agntDirectorList = [String.StripDiacritics(x) for x in agntDirectorList]
    agntDirectorList = [x for x in agntDirectorList if x]
    log('UTILS :: {0:<29} {1}'.format('Agent Director List', '{0:>2} - {1}'.format(len(agntDirectorList), agntDirectorList)))

    excludeList = [string for string in agntDirectorList if [substr for substr in agntDirectorList if substr in string and substr != string]]
    if excludeList:
        agntDirectorList = [x for x in agntDirectorList if x not in excludeList]
        log('UTILS :: {0:<29} {1}'.format('Exclude', '{0:>2} - {1}'.format(len(excludeList), excludeList)))
        log('UTILS :: {0:<29} {1}'.format('Result', '{0:>2} - {1}'.format(len(agntDirectorList), agntDirectorList)))

    # strip all non alphabetic characters from director names / aliases so as to compare them to the list obtained from the website e.g. J.T. Sloan will render as jtsloan
    directorDict = FILMDICT['Directors']
    log('UTILS :: {0:<29} {1}'.format('IAFD Director List', '{0:>2} - {1}'.format(len(directorDict), sorted(directorDict.keys()))))

    IAFDDirectorList = [(re.sub(r'[\W\d_]', '', k).strip().lower(), v) for k, v in directorDict.items()] # list of tuples [name, alias]

    # remove entries from the website cast list which have been found on IAFD leaving unmatched director
    unmatchedDirectorList = [x for x in agntDirectorList if re.sub(r'[\W\d_]', '', x).strip().lower() not in (item for namealias in IAFDDirectorList for item in namealias)]
    log('UTILS :: {0:<29} {1}'.format('Unmatched Director List', '{0:>2} - {1}'.format(len(unmatchedDirectorList), unmatchedDirectorList)))
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

    Thumbor = Prefs['thumbor'] + "/0x0:{0}x{1}/{2}"
    Cropper = r'CScript.exe "{0}/Plex Media Server/Plug-ins/{1}.bundle/Contents/Code/ImageCropper.vbs" "{2}" "{3}" "{4}" "{5}"'

    pic = imageURL
    picContent = HTTP.Request(pic).content
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
    DxWidth = '{0:>2}'.format(DxWidth)    # percent format
    DxHeight = '{0:>2}'.format(DxHeight)  # percent format
    log('UTILS :: Crop {0} {1}: Actual (w{2} x h{3}), Desired (w{4} x h{5}), % Dx = w[{6}%] x h[{7}%]'.format("Required:" if cropRequired else "Not Required:", imageType, dispWidth, dispHeight, desiredWidth, desiredHeight, DxWidth, DxHeight))
    if cropRequired:
        try:
            log('UTILS :: Using Thumbor to crop image to: {0} x {1}'.format(desiredWidth, desiredHeight))
            pic = Thumbor.format(cropWidth, cropHeight, imageURL)
            picContent = HTTP.Request(pic).content
        except Exception as e:
            log('UTILS :: Error Thumbor Failed to Crop Image to: {0} x {1}: {2} - {3}'.format(desiredWidth, desiredHeight, pic, e))
            try:
                if os.name == 'nt':
                    log('UTILS :: Using Script to crop image to: {0} x {1}'.format(desiredWidth, desiredHeight))
                    envVar = os.environ
                    TempFolder = envVar['TEMP']
                    LocalAppDataFolder = envVar['LOCALAPPDATA']
                    pic = os.path.join(TempFolder, imageURL.split("/")[-1])
                    cmd = Cropper.format(LocalAppDataFolder, AGENT, imageURL, pic, cropWidth, cropHeight)
                    subprocess.call(cmd)
                    picContent = PlexLoadFile(pic)
            except Exception as e:
                log('UTILS :: Error Script Failed to Crop Image to: {0} x {1}'.format(desiredWidth, desiredHeight))

    return pic, picContent

# -------------------------------------------------------------------------------------------------------------------------------
def getFilmOnIAFD(FILMDICT):
    ''' check IAFD web site for better quality thumbnails per movie'''
    # search for Film Title on IAFD

    try:
        myYear = int(FILMDICT['Year'])
        html = getURLElement(IAFD_SEARCH_URL.format(FILMDICT['IAFDSearchTitle']), FilterYear=myYear, UseAdditionalResults=True)

        # get films listed within 1 year of what is on agent - as IAFD may have a different year recorded
        filmsList = []
        if myYear:
            filmsList = html.xpath('//table[@id="titleresult"]/tbody/tr/td[2][.>="{0}" and .<="{1}"]/ancestor::tr'.format(myYear - 2, myYear + 1))
            filmsFound = len(filmsList)
            log('UTILS :: {0:<29} {1}'.format('Films found on IAFD', '{0} between the years [{1}] and [{2}]'.format(filmsFound, myYear - 2, myYear + 1)))

        if not filmsList:
            filmsList = html.xpath('//table[@id="titleresult"]/tbody/tr')
            filmsFound = len(filmsList)
            log('UTILS :: {0:<29} {1}'.format('Films found on IAFD', filmsFound))

        log(LOG_BIGLINE)
        myYear = '({0})'.format(myYear) if myYear else ''
        for idx, film in enumerate(filmsList, start=1):
            log('UTILS :: {0:<29} {1}'.format('Processing', '{0} of {1} for {2} - {3} {4}'.format(idx, filmsFound, FILMDICT['Studio'], FILMDICT['Title'], myYear)))
            log(LOG_BIGLINE)

            # Site Title and Site AKA
            try:
                siteTitle = film.xpath('./td[1]/a/text()')[0].strip()
                # IAFD sometimes adds (I), (II), (III) to differentiate scenes from full movies - strip these out before matching - assume a max of 19 (XIX)
                pattern = ' \(X{0,1}(?:V?I{0,3}|I[VX])\)$'
                matched = re.search(pattern, siteTitle)  # match against whole string
                siteTitle = re.sub(pattern, '', siteTitle).strip() if matched else siteTitle
                matchTitle(siteTitle, FILMDICT)
                matchedTitle = True

            except Exception as e:
                matchedTitle = False
                log('UTILS :: Error getting IAFD Site Title, Try AKA Title: %s', e)

            try:
                filmAKA = film.xpath('./td[4]/text()')[0].strip()
                if not matchedTitle:
                    pattern = ' \(X{0,1}(?:V?I{0,3}|I[VX])\)$'
                    matched = re.search(pattern, filmAKA)  # match against whole string
                    filmAKA = re.sub(pattern, '', filmAKA).strip() if matched else filmAKA
                    matchTitle(filmAKA, FILMDICT)
                FILMDICT['FilmAKA'] = filmAKA
            except Exception as e:
                log('UTILS :: Error getting IAFD Site AKA Title: %s', e)
                if not matchedTitle:
                    log(LOG_SUBLINE)
                    continue

            # Site Title URL
            log(LOG_BIGLINE)
            try:
                filmURL = film.xpath('./td[1]/a/@href')[0].replace('+/', '/').replace('-.', '.')
                if IAFD_BASE not in filmURL:
                    filmURL = '{0}{1}'.format(IAFD_BASE, filmURL) if filmURL[0] == '/' else '{0}/{1}'.format(IAFD_BASE, filmURL)
                FILMDICT['IAFDFilmURL'] = filmURL
                vFilmURL = filmURL
                if FILMDICT['Agent'] == 'IAFD':
                    FILMDICT['FilmURL'] = filmURL
                log('UTILS :: {0:<29} {1}'.format('IAFD Site Title Url', filmURL))

            except Exception as e:
                log('UTILS :: Error getting IAFD Site Title Url: %s', e)
                log(LOG_SUBLINE)
                continue

            # Access Site URL for Studio, Release Date and Duration information
            log(LOG_BIGLINE)
            try:
                log('UTILS :: {0:<29} {1}'.format('Reading IAFD Film URL page', FILMDICT['IAFDFilmURL']))
                fhtml = getURLElement(FILMDICT['IAFDFilmURL'])
                vFilmHTML = fhtml

            except Exception as e:
                log('UTILS :: Error reading IAFD Film URL page: %s', e)
                log(LOG_SUBLINE)
                continue

            # Film Studio and Distributor
            log(LOG_BIGLINE)
            foundStudio = False
            try:
                fhtmlStudios = fhtml.xpath('//p[@class="bioheading" and (text()="Studio" or text()="Distributor")]//following-sibling::p[1]/a/text()')
                fhtmlStudios = {x.strip() for x in fhtmlStudios if x.strip()}
                studiosFound = len(fhtmlStudios)
                log('UTILS :: {0:<29} {1}'.format('Site URL Distributor/Studio', '{0:>2} - {1}'.format(studiosFound, fhtmlStudios)))
                for idx, item in enumerate(fhtmlStudios, start=1):
                    log('UTILS :: {0:<29} {1}'.format('Processing Studio', '{0} - {1} of {2}'.format(item, idx, studiosFound)))
                    try:
                        matchStudio(item, FILMDICT)
                        foundStudio = True
                        break

                    except Exception as e:
                        log('UTILS :: Error: %s', e)
                        log(LOG_SUBLINE)
                        continue

                if not foundStudio:
                    log('UTILS :: Error matching IAFD Site Studio/Distributor')
                    log(LOG_SUBLINE)
                    continue

            except Exception as e:
                log('UTILS :: Error getting IAFD Site Studio/Distributor: %s', e)
                log(LOG_SUBLINE)
                continue

            # At this point we have a match against default Studio and Title 
            # IAFD has links to External Sites for the Title - These sites may have different Release Dates and Duration Times
            # Release Dates and Durations must be retrieved - whether matching against them is needed
            # if matching match against all data returned and considered passed if any match
            log(LOG_BIGLINE)
            log('UTILS :: Access External Links in IAFD: Skip Current Agent Links: %s', FILMDICT['Agent'])
            externalIAFDSites = {'AdultEmpire': 'GayDVDEmpire', 'HotMovies': 'GayHotMovies', 'CD Universe': 'CDUniverse'}
            externalDict = {}
            try:
                webLinks = fhtml.xpath('//a[contains(@href, "/shopclick")]')[0]      # will error if none
                webLinks = fhtml.xpath('//a[contains(@href, "/shopclick")]')
                for idx, webLink in enumerate(webLinks, start=1):
                    webURL = webLink.xpath('./@href')[0]
                    webURL = '{0}{1}'.format(IAFD_BASE, webURL)
                    webName = webLink.xpath('./text()')[0]
                    log('UTILS :: {0:<29} {1}'.format('External Sites Found' if idx ==1 else '', '{0:>2} - {1:<15} - {2}'.format(idx, webName, webURL)))
                    if webName not in externalIAFDSites:
                        continue
                    if externalIAFDSites[webName] == FILMDICT['Agent']:
                        continue

                    externalDict[webName] = webURL

            except Exception as e:
                log('UTILS :: Error getting External Links: %s', e)

            log('UTILS :: {0:<29} {1}'.format('Valid Sites Left', '{0:>2} - {1}'.format(len(externalDict), sorted(externalDict.keys()))))
            for key in externalDict.keys():
                if key in FILMDICT:                    # only run once per External Site - VOD vs DVD
                    continue

                try:
                    value = externalDict[key]
                    ################################ needs looking at to get Location response header - ask group.......
                    xSiteHTML = HTML.ElementFromURL(value, timeout=60, errors='ignore', sleep=DELAY)
                    # xhtml = HTML.ElementFromURL(value, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36"},timeout=60, errors='ignore', sleep=DELAY)
                    # xhtml = getURLElement(value)
                    FILMDICT[key] = getSiteInfo(key, FILMDICT, kwFilmURL=value, kwFilmHTML=xSiteHTML)
                    # change Compilation to 'Yes' if one result is not the default 'No'
                    if 'Compilation' in FILMDICT[key] and FILMDICT[key]['Compilation'] == 'Yes':
                        FILMDICT['Compilation'] = FILMDICT[key]['Compilation'] 

                except Exception as e:
                    log('UTILS :: Error reading External %s URL Link: %s', key, e)
                    continue

            # Release Date Information: IAFD Fromat = MM DD, YYYY
            log(LOG_BIGLINE)
            productionDates = set()
            vReleaseDate = None
            try:
                # default to 31st December of Title Year
                if 'CompareDate' in FILMDICT and FILMDICT['CompareDate']:
                    log('UTILS :: {0:<29} {1}'.format('Default File Name Date', FILMDICT['CompareDate']))
                    productionDates.add(FILMDICT['CompareDate'])

                try:
                    fhtmlReleaseDate = fhtml.xpath('//p[@class="bioheading" and text()="Release Date"]//following-sibling::p[1]/text()')[0].strip()
                    log('UTILS :: {0:<29} {1}'.format('Site URL Release Date', fhtmlReleaseDate))
                    productionDates.add(datetime.strptime(fhtmlReleaseDate, '%b %d, %Y'))
                except: pass

                try:
                    fhtmlAddedDate = fhtml.xpath('//p[@class="bioheading" and text()="Date Added to IAFD"]//following-sibling::p[1]/text()')[0].strip()
                    log('UTILS :: {0:<29} {1}'.format('Site URL Added to IAFD Date', fhtmlAddedDate))
                    productionDates.add(datetime.strptime(fhtmlAddedDate, '%b %d, %Y'))
                except: pass

                log('UTILS :: {0:<29} {1}'.format('Release Dates', '{0} - {1}'.format(len(productionDates), sorted(productionDates))))

                # add external dates to list
                externalDates = False
                for value in externalIAFDSites.values():
                    try:
                        if value in FILMDICT and 'ReleaseDate' in FILMDICT[value] and FILMDICT[value]['ReleaseDate']:
                            productionDates.add(FILMDICT[value]['ReleaseDate'])
                            externalDates = True
                    except: pass

                if externalDates == True:
                    log('UTILS :: {0:<29} {1}'.format('Release Dates (+ External)', '{0} - {1}'.format(len(productionDates), sorted(productionDates))))

                # match against list
                try:
                    releaseDate = min(productionDates)
                    log('UTILS :: {0:<29} {1}'.format('Earliest Release Dates', '{0}'.format(releaseDate)))
                    matchReleaseDate(releaseDate, FILMDICT, UseTwoYearMatch = False if AGENT == 'IAFD' else True)
                    vReleaseDate = releaseDate
                except Exception as e:
                    log('UTILS :: Error Matching Release Date: %s', e)
                    continue

            except Exception as e:
                log('UTILS :: Error getting Site URL Release Dates: %s', e)
                if FILMDICT['Year']:                     # year in filename title so use release date as filter
                    log(LOG_SUBLINE)
                    continue

            # Film Duration
            log(LOG_BIGLINE)
            vDuration = FILMDICT['Duration']
            try:
                fhtmlduration = fhtml.xpath('//p[@class="bioheading" and text()="Minutes"]//following-sibling::p[1]/text()')[0].strip()
                duration = datetime.fromtimestamp(int(fhtmlduration) * 60)
                matchDuration(duration, FILMDICT)
                vDuration = duration
                FILMDICT['IAFDDuration'] = duration
            except ValueError as e:
                log('UTILS :: Error: IAFD Duration Not Numeric: Set Duration to File Length and Continue: %s', e)
                FILMDICT['IAFDDuration'] = FILMDICT['Duration']
            except Exception as e:
                if MATCHIAFDDURATION:           # if preference selected go to next
                    log('UTILS :: Error: getting IAFD Duration: %s', e)
                    log(LOG_SUBLINE)
                    continue

            # if we get here we have found a film match
            log(LOG_BIGLINE)
            FILMDICT['FoundOnIAFD'] = 'Yes'
            log('UTILS :: {0:<29} {1}'.format('Found on IAFD', FILMDICT['FoundOnIAFD']))

            # check if film has an all male cast
            log(LOG_BIGLINE)
            try:
                FILMDICT['AllMale'] = fhtml.xpath('//p[@class="bioheading" and text()="All-Male"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: {0:<29} {1}'.format('All Male Cast?', FILMDICT['AllMale']))
            except Exception as e:
                log('UTILS :: Error Finding All Male Cast: %s', e)

            # check if film has an all Girl cast
            log(LOG_BIGLINE)
            try:
                FILMDICT['AllGirl'] = fhtml.xpath('//p[@class="bioheading" and text()="All-Girl"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: {0:<29} {1}'.format('All Girl Cast?', FILMDICT['AllGirl']))
            except Exception as e:
                log('UTILS :: Error Finding All Girl Cast: %s', e)


            # use general routine to get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information
            log(LOG_BIGLINE)
            log('SEARCH:: Access Site URL Link:')
            FILMDICT['IAFD'] = getSiteInfo('IAFD', FILMDICT, kwFilmURL=vFilmURL, kwFilmHTML=vFilmHTML, kwReleaseDate=vReleaseDate, kwDuration=vDuration)

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
        log('UTILS :: {0:<29} {1}'.format('Cast on IAFD', len(castList)))
        for cast in castList:
            castName = cast.xpath('./a/text()[normalize-space()]')[0].strip()
            castName = 'Unknown Actor' if 'Unknown' in castName else castName
            castURL = IAFD_BASE + cast.xpath('./a/@href')[0].strip()
            castPhoto = cast.xpath('./a/img/@src')[0].strip()
            castPhoto = '' if 'nophoto' in castPhoto or 'th_iafd_ad' in castPhoto else castPhoto

            # cast roles are sometimes not filled in
            try:
                castRole = cast.xpath('./text()[normalize-space()]')
                castRole = ' '.join(castRole).replace('DVDOnly','').strip()
            except:
                castRole = ''

            # cast alias in current film may be missing
            try:
                castAlias = cast.xpath('./i/text()')[0].split(':')[1].replace(')', '').strip()
            except:
                castAlias = ''

            castRole = castRole if castRole else 'AKA: {0}'.format(castAlias) if castAlias else IAFD_FOUND

            # log cast details
            log('UTILS :: {0:<29} {1}'.format('Cast Name', castName))
            log('UTILS :: {0:<29} {1}'.format('Cast Alias', castAlias if castAlias else 'No Cast Alias Recorded'))
            log('UTILS :: {0:<29} {1}'.format('Cast URL', castURL))
            log('UTILS :: {0:<29} {1}'.format('Cast Photo', castPhoto))
            log('UTILS :: {0:<29} {1}'.format('Cast Role', castRole))

            # Assign values to dictionary
            myDict = {}
            myDict['Photo'] = castPhoto
            myDict['Role'] = castRole
            myDict['Alias'] = castAlias
            myDict['CompareName'] = re.sub(r'[\W\d_]', '', castName).strip().lower()
            myDict['CompareAlias'] = re.sub(r'[\W\d_]', '', castAlias).strip().lower()
            myDict['URL'] = castURL
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
        log('UTILS :: {0:<29} {1}'.format('Directors on IAFD', len(directorList)))
        for director in directorList:
            directorName = director.xpath('./text()')[0]
            directorURL = director.xpath('./@href')[0]
            try:
                dhtml = getURLElement(directorURL)
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

            log('UTILS :: {0:<29} {1}'.format('Director Name', directorName))
            log('UTILS :: {0:<29} {1}'.format('Director Alias', directorAliasList if directorAliasList else 'No Director Alias Recorded'))
            log('UTILS :: {0:<29} {1}'.format('Director URL', directorURL))
            log('UTILS :: {0:<29} {1}'.format('Director Photo', directorPhoto))
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
def getSiteInfo(myAgent, FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information from Selected Website

        Note: **Kwargs variables are used to pass on already scraped data, so that this does not need to be repeated in the getSiteInfo<XXX>
                routine. The variables indicated are only scrapped within the routine, if there is a link to an external agent in the main
                scraping Agent. For example if GEVI has a link to AEBN, there will be no **Kwargs and scraping for the field will occur
    '''
    siteInfoDict = {}
    log(LOG_BIGLINE)
    log('UTILS ::')
    kwFilmURL = kwargs.get('kwFilmURL')
    listHeaders = [' << {0}: Get Site Information >> '.format(myAgent), 
                   ' ({0}) - {1} ({2}) >> '.format(FILMDICT['Studio'], FILMDICT['Title'], FILMDICT['Year']),
                   ' {0} '.format(FILMDICT['FilmURL'] if kwFilmURL is None else kwFilmURL)]
    for header in listHeaders:
        log('UTILS :: %s', header.center(140, '*'))
    log('UTILS ::')

    if myAgent == 'AdultFilmDatabase':
        siteInfoDict = getSiteInfoAdultFilmDatabase(FILMDICT, **kwargs)
    elif myAgent == 'AEBNiii':
        siteInfoDict = getSiteInfoAEBNiii(FILMDICT, **kwargs)
    elif myAgent == 'AVEntertainments':
        siteInfoDict = getSiteInfoAVEntertainments(FILMDICT, **kwargs)
    elif myAgent == 'BestExclusivePorn':
        siteInfoDict = getSiteInfoBestExclusivePorn(FILMDICT, **kwargs)
    elif myAgent == 'CDUniverse':
        siteInfoDict = getSiteInfoCDUniverse(FILMDICT, **kwargs)
    elif myAgent == 'GayDVDEmpire':
        siteInfoDict = getSiteInfoGayDVDEmpire(FILMDICT, **kwargs)
    elif myAgent == 'Fagalicious':
        siteInfoDict = getSiteInfoFagalicious(FILMDICT, **kwargs)
    elif myAgent == 'GayHotMovies':
        siteInfoDict = getSiteInfoGayHotMovies(FILMDICT, **kwargs)
    elif myAgent == 'GayMovie':
        siteInfoDict = getSiteInfoGayMovie(FILMDICT, **kwargs)
    elif myAgent == 'GayFetishandBDSM':
        siteInfoDict = getSiteInfoGayFetishandBDSM(FILMDICT, **kwargs)
    elif myAgent == 'GayMovies':
        siteInfoDict = getSiteInfoGayMovie(FILMDICT, **kwargs)
    elif myAgent == 'GayRado':
        siteInfoDict = getSiteInfoGayRado(FILMDICT, **kwargs)
    elif myAgent == 'GayWorld':
        siteInfoDict = getSiteInfoGayWorld(FILMDICT, **kwargs)
    elif myAgent == 'GEVI':
        siteInfoDict = getSiteInfoGEVI(FILMDICT, **kwargs)
    elif myAgent == 'HFGPM':
        siteInfoDict = getSiteInfoHFGPM(FILMDICT, **kwargs)
    elif myAgent == 'HomoActive':
        siteInfoDict = getSiteInfoHomoActive(FILMDICT, **kwargs)
    elif myAgent == 'IAFD':
        siteInfoDict = getSiteInfoIAFD(FILMDICT, **kwargs)
    elif myAgent == 'QueerClick':
        siteInfoDict = getSiteInfoQueerClick(FILMDICT, **kwargs)
    elif myAgent == 'SimplyAdult':
        siteInfoDict = getSiteInfoSimplyAdult(FILMDICT, **kwargs)
    elif myAgent == 'WayBig':
        siteInfoDict = getSiteInfoWayBig(FILMDICT, **kwargs)
    elif myAgent == 'WolffVideo':
        siteInfoDict = getSiteInfoWolffVideo(FILMDICT, **kwargs)

    log('UTILS ::')
    footer = ' >> {0}: Site Information Retrieved << '.format(myAgent)
    log('UTILS :: %s', footer.center(140, '*'))
    log('UTILS ::')
    return siteInfoDict

# -------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoAdultFilmDatabase(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'AdultFilmDatabase'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//p[@itemprop="description"]/text()')
            synopsis = '\n'.join(htmlsynopsis).strip()
            siteInfoDict['Synopsis'] = synopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', synopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//span[@itemprop="director"]//text()[normalize-space()]')
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//span[@itemprop="actor"]//text()[normalize-space()]')
            htmlcast = [x.strip() for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections
        log(LOG_SUBLINE)
        try:
            htmlcollections = html.xpath('//a[contains(@href, "/videoseries/")]//text()')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            collections = list(set(htmlcollections))
            collections.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        countriesSet = set()
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//a[contains(@href,"&cf=")]/span/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem in COUNTRYSET:
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem if newItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation


        #   6.  Release Date - ADF Format = (YYYY)
        kwReleaseDate = kwargs.get('kwReleaseDate')
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmldate = html.xpath('//text()[contains(.,"Studio:")]/following::text()[2]')[0].replace('(', '').replace(')', '').strip()
                htmldate = '{0}1231'.format(htmldate)
                htmldate = datetime.strptime(htmldate, '%Y%m%d')
                siteInfoDict['ReleaseDate'] = htmldate
                log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration - AEBN Format = HH:MM:SS optional HH
        kwDuration = kwargs.get('kwDuration')
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlduration = html.xpath('//span[@itemprop="duration"]/text()')[0].replace('Runtime: ', '').strip()
                htmlDuration = htmlDuration.split(':')                                              # split into hr, mins, secs
                htmlDuration = [int(x) for x in htmlDuration if x.strip()]                          # convert to integer
                duration = htmlduration[0] * 3600 + htmlduration[1] * 60 + htmlduration[2]          # convert to seconds
                duration = datetime.fromtimestamp(duration)
                siteInfoDict['Duration'] = htmlduration
                log('UTILS :: {0:<29} {1}'.format('Duration', htmlduration.strftime('%H:%M:%S')))

            except Exception as e:
                siteInfoDict['Duration'] = datetime.fromtimestamp(0)
                log('UTILS :: Error getting Site Film Duration: %s', e)
        else:
            siteInfoDict['Duration'] = siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        kwBaseURL = kwargs.get('kwBaseURL')
        if kwReleaseDate is not None:
            log(LOG_SUBLINE)
            try:
                htmlimages = html.xpath('//img[@title]/@src')
                htmlimages = [('' if kwBaseURL in x else kwBaseURL) + x for x in htmlimages]
                poster = htmlimages[0]
                art = htmlimages[1]
                log('UTILS :: {0:<29} {1}'.format('Poster', poster))
                log('UTILS :: {0:<29} {1}'.format('Art', art))

            except Exception as e:
                poster = ''
                art = ''
                log('UTILS :: Error getting Images: %s', e)

            finally:
                siteInfoDict['Poster'] = poster
                siteInfoDict['Art'] = art
        else:
            log('UTILS :: No Base URL Provided to get full path to Posters\Art - Set to Null')
            siteInfoDict['Poster'] = ''
            siteInfoDict['Art'] = ''

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoAEBNiii(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'AEBNiii'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//div[@class="dts-section-page-detail-description-body"]/text()')[0].strip()
            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', htmlsynopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//li[@class="section-detail-list-item-director"]/span/a/span/text()')
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//div[@class="dts-star-name-overlay"]/text()')
            htmlcast = [x.strip() for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections
        log(LOG_SUBLINE)
        try:
            htmlcollections = html.xpath('//li[@class="section-detail-list-item-series"]/span/a/span/text()')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            collections = list(set(htmlcollections))
            collections.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        countriesSet = set()
        compilation = 'No'
        try:
            try:
                htmlgenres = html.xpath('//span[@class="dts-image-display-name"]/text()')
                htmlgenres.sort(key = lambda x: x.lower())
                log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))

            except Exception as e:
                htmlgenres = []
                log('UTILS :: Error Reading Site Info Genres: %s', e)

            try:
                htmlsexacts = html.xpath('//a[contains(@href,"sexActFilters")]/text()') # use sex acts as genresDict
                htmlsexacts.sort(key = lambda x: x.lower())
                log('UTILS :: {0:<29} {1}'.format('Sex Acts', '{0:>2} - {1}'.format(len(htmlsexacts), htmlsexacts)))

            except Exception as e:
                htmlsexacts = []
                log('UTILS :: Error Reading Site Info Sex Acts: %s', e)

            htmlgenres.extend(htmlsexacts)
            htmlgenres = list(set(htmlgenres))
            htmlgenres.sort(key = lambda x: x.lower())
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            log('UTILS :: {0:<29} {1}'.format('Combined Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem in COUNTRYSET:
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem if newItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   6.  Release Date - AEBN Format = mmm dd, YYYY
        kwReleaseDate = kwargs.get('kwReleaseDate')
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmldate = html.xpath('//li[@class="section-detail-list-item-release-date"]/text()[normalize-space()]')[0].strip()
                htmldate = htmldate.replace('July', 'Jul').replace('Sept', 'Sep')    # AEBN uses 4 letter abbreviation for September
                htmldate = datetime.strptime(htmldate, '%b %d, %Y')
                siteInfoDict['ReleaseDate'] = htmldate
                log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration - AEBN Format = HH:MM:SS optional HH
        kwDuration = kwargs.get('kwDuration')
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlduration = html.xpath('//span[text()="Running Time:"]/parent::li/text()')[0].strip()
                htmlduration = htmlduration.split(':')                                                      # split into hr, mins, secs
                htmlduration = [int(x) for x in htmlduration]                                               # convert to integer
                htmlduration = ['0{0}'.format(x) if x < 10 else '{0}'.format(x) for x in htmlduration]      # converted to zero padded items
                htmlduration = ['00'] + htmlduration if len(htmlduration) == 2 else htmlduration            # prefix with zero hours if string is only minutes and seconds
                htmlduration = '1970-01-01 {0}'.format(':'.join(htmlduration))                              # prefix with 1970-01-01 to conform to timestamp
                htmlduration = datetime.strptime(htmlduration, '%Y-%m-%d %H:%M:%S')                         # turn to date time object
                siteInfoDict['Duration'] = htmlduration
                log('UTILS :: {0:<29} {1}'.format('Duration', htmlduration.strftime('%H:%M:%S')))

            except Exception as e:
                siteInfoDict['Duration'] = datetime.fromtimestamp(0)
                log('UTILS :: Error getting Site Film Duration: %s', e)
        else:
            siteInfoDict['Duration'] = siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//*[contains(@class,"dts-movie-boxcover")]//img/@src')
            htmlimages = [x.replace('293', '1000') for x in htmlimages]
            htmlimages = ['http:{0}'.format(x) if 'http:' not in x else x for x in htmlimages]
            poster = htmlimages[0]
            art = htmlimages[1]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        scenesDict = {}
        chaptersDict = {}
        try:
            htmlscenes = html.xpath('//div[@class="dts-scene-info dts-list-attributes"]')
            log('UTILS :: {0:<29} {1}'.format('Possible Number of Scenes', len(htmlscenes)))
            if len(htmlscenes) == 0:
                raise Exception ('< No Scenes Found! >')

            htmlheadings = html.xpath('//header[@class="dts-panel-header"]/div/h1/span[contains(text(),"Scene")]//text()')
            htmldurations = html.xpath('//header[@class="dts-panel-header"]/div/h1/span[@class="dts-scene-title-metadata dts-no-panel-title-link"]/span/text()')
            htmldurations = [x.split()[0] for x in htmldurations]   # extract time strings format MM:SS

            # sum up the scenes' length: AEBN uses MM:SS format
            scenesDelta = timedelta()
            for htmlduration in htmldurations:
                (mm, ss) = htmlduration.split(':')
                scenesDelta += timedelta(minutes=int(mm), seconds=int(ss))

            # subtract the total scene length from the total films length to establish where the first scene begins: i.e the offset
            # TimeOffset = dx of duration of film - total of all scenes length, or 0 if film is stacked or scenes are strangely longer than the actual film
            durationTime = str(FILMDICT['Duration'].time())
            durationTime = datetime.strptime(str(durationTime),"%H:%M:%S")
            scenesTime = datetime.strptime(str(scenesDelta),"%H:%M:%S")
            if FILMDICT['Stacked'] == 'Yes':
                timeOffsetTime = datetime.fromtimestamp(0) if FILMDICT['Stacked'] == 'Yes' else datetime.fromtimestamp(0) if scenesTime > durationTime else durationTime - scenesTime
            else:
                
                timeOffsetTime = abs(durationTime - scenesTime)
                timeOffsetTime = datetime.strptime(str(timeOffsetTime),"%H:%M:%S")

            log('UTILS :: {0:<29} {1}'.format('Durations', 'Film: {0}, Scenes: {1}, Offset: {2} {3}'.format(durationTime.time(), scenesTime.time(), timeOffsetTime.time(), '(Stacked)' if FILMDICT['Stacked'] == 'Yes' else '')))

            log(LOG_SUBLINE)
            for sceneNo, (htmlheading, htmlscene, htmlduration) in enumerate(zip(htmlheadings, htmlscenes, htmldurations), start = 1):
                try:
                    # scene No
                    log('UTILS :: {0:<29} {1}'.format('Scene', sceneNo))

                    # Review Source - composed of cast list or iafd scenes cast or Film title in that order of preference
                    reviewSource = ''
                    try:
                        # fill with Cast names from external website
                        reviewSource = htmlscene.xpath('./ul/li/span/a[contains(@href, "/stars/")]/text()')
                        reviewSource = [x.split('(')[0] for x in reviewSource]
                        reviewSource = ', '.join(reviewSource)

                        # prep for review metadata
                        if len(reviewSource) > 40:
                            for i in range(40, -1, -1):
                                if reviewSource[i] == ' ':
                                    reviewSource = reviewSource[0:i]
                                    break
                        if reviewSource:
                            reviewSource = '{0}. {1}...'.format(sceneNo, reviewSource)
                        else:
                            mySource = 'N/A'
                            reviewSource = '{0}. {1}...'.format(sceneNo, FILMDICT['Title'])
                            log('UTILS :: Warning No Review Source (Used Film Title)')

                        log('UTILS :: {0:<29} {1}'.format('Review Source', '{0} - {1}'.format(mySource, reviewSource) if reviewSource else 'None Recorded'))

                    except Exception as e:
                        log('UTILS :: Error getting Review Source (Cast): %s', e)

                    # Review Author - composed of Settings
                    reviewAuthor = 'AEBNiii'
                    try:
                        reviewAuthor = htmlscene.xpath('./ul/li[descendant::span[text()="Settings:"]]/a/text()')
                        reviewAuthor = [x for x in reviewAuthor if x]
                        reviewAuthor = ', '.join(reviewAuthor)

                    except Exception as e:
                        log('UTILS :: Error getting Review Author (Settings): %s', e)

                    finally:
                        # prep for review metadata - Review Author = Scene Heading +  Settings) else use Scene Heading alone
                        reviewAuthor = ('{0}: {1}').format(htmlheading, reviewAuthor) if reviewAuthor else '{0}'.format(htmlheading)
                        log('UTILS :: {0:<29} {1}'.format('Review Author', reviewAuthor if reviewAuthor else 'None Recorded'))

                    # Review Text - composed of Sexual Acts / tidy genres
                    reviewText = ''
                    try:
                        reviewList = htmlscene.xpath('./ul/li[descendant::span[text()="Sex acts:"]]/a/text()')
                        reviewList = [x.strip() for x in reviewList if x.strip()]
                        reviewList.sort(key = lambda x: x.lower())
                        mySet = set()
                        for idx, item in enumerate(reviewList, start=1):
                            newItem = findTidy(item)
                            log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))
                            if newItem is None:
                                continue
                            mySet.add(newItem if newItem else item)

                        reviewList = list(mySet)
                        reviewList.sort(key = lambda x: x.lower())
                        reviewText = ', '.join(reviewList)

                    except Exception as e:
                        log('UTILS :: Error getting Review Text (Sex Acts): %s', e)

                    finally:
                        # prep for review metadata
                        if len(reviewText) > 275:
                            for i in range(275, -1, -1):
                                if reviewText[i] in ['.', '!', '?']:
                                    reviewText = reviewText[0:i + 1]
                                    break
                        log('UTILS :: {0:<29} {1}'.format('Review Text', reviewText if reviewText else 'None Recorded'))


                    # save Review - scene
                    scenesDict[sceneNo] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText, 'Link': filmURL}

                    chapterTitle = reviewSource
                    chapterStartTime = (timeOffsetTime.hour * 60 * 60 + timeOffsetTime.minute * 60 + timeOffsetTime.second) * 1000
                    (mm, ss) = htmlduration.strip().split(':')
                    timeOffsetTime += timedelta(minutes=int(mm), seconds=int(ss))
                    chapterEndTime = (timeOffsetTime.hour * 60 * 60 + timeOffsetTime.minute * 60 + timeOffsetTime.second) * 1000
                    # next scene starts a second after last scene
                    timeOffsetTime += timedelta(seconds=1)

                    log('UTILS :: {0:<29} {1}'.format('Chapter', '{0} - {1}:{2}'.format(sceneNo, mm, ss)))
                    log('UTILS :: {0:<29} {1}'.format('Title', chapterTitle))
                    log('UTILS :: {0:<29} {1}'.format('Time', '{0} - {1}'.format(datetime.fromtimestamp(chapterStartTime/1000).strftime('%H:%M:%S'), datetime.fromtimestamp(chapterEndTime/1000).strftime('%H:%M:%S'))))

                    # save chapter
                    chaptersDict[sceneNo] = {'Title': chapterTitle, 'StartTime': chapterStartTime, 'EndTime': chapterEndTime}

                except Exception as e:
                    log('UTILS :: Error getting Scene No. %s: %s', sceneNo, e)

        except Exception as e:
            log('UTILS :: Error getting Scenes: %s', e)

        finally:
            siteInfoDict['Scenes'] = scenesDict
            siteInfoDict['Chapters'] = chaptersDict

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoAVEntertainments(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'AVEntertainments'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//div[@class="product-description mt-20"]/text()')[0].strip()
            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', htmlsynopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Director"]/following-sibling::span/a/text()')
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Starring"]/following-sibling::span/a/text()')
            htmlcast = [x.strip() for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections
        log(LOG_SUBLINE)
        try:
            htmlcollections = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Series"]/following-sibling::span/a/text()')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            collections = list(set(htmlcollections))
            collections.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        countriesSet = set()
        try:
            htmlgenres = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Category"]/following-sibling::span/a/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem in COUNTRYSET:
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem if newItem else item)

            # AV Entertainments is mainly geared for Straight Porn - Not a lot of Gay Genres - process synopsis
            if siteInfoDict['Synopsis']:
                synopsis = re.sub(r'[^\w\s]',' ', siteInfoDict['Synopsis'])             # remove all punctuationion
                synopsis = re.sub(r'\b\w{1,3}\b', '', synopsis)                         # remove all short words (3 letters or less) - to avoid processing letters like you, us, him
                setSynopsis = set(synopsis.split())
                log('UTILS :: {0:<29} {1}'.format('Synopsis Word Count', '{0:>3} - {1}'.format(len(setSynopsis), setSynopsis)))
                for idx, item in enumerate(setSynopsis, start=1):
                    newItem = findTidy(item)
                    if not newItem or newItem is None:        # Don't process
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>3} - {1:<25} :: {2}'.format(idx, item, newItem)))
                    if newItem in COUNTRYSET:
                        countriesSet.add(newItem)
                    else:
                        genresSet.add(newItem)


            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet

        #   5b.  Compilation
        kwCompilation = kwargs.get('kwCompilation')
        siteInfoDict['Compilation'] = 'No' if kwCompilation is None else kwCompilation

        #   6.  Release Date
        log(LOG_SUBLINE)
        kwReleaseDate = kwargs.get('kwReleaseDate')
        log('UTILS :: {0:<29} {1}'.format('KW Release Date', kwReleaseDate))
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmldate = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Date"]/following-sibling::span/text()')[0].strip()
                htmldate = datetime.strptime(htmldate, '%-m/%-d/%Y')
                siteInfoDict['ReleaseDate'] = htmldate
                log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration
        kwDuration = kwargs.get('kwDuration')
        log('UTILS :: {0:<29} {1}'.format('KW Duration', kwDuration))
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlduration = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Play Time"]/following-sibling::span//text()')[0].strip()
                htmlduration = re.sub('Apx. | Mins| Min', '', htmlduration)
                htmlduration = re.sub('Hrs |Hr ', ':', htmlduration)
                htmlduration = htmlduration.split(':')                                                                # split into hr, mins
                htmlduration = [int(x) for x in htmlduration]                                                         # convert to integer
                duration = htmlduration[0] * 60 + htmlduration[1] if len(htmlduration) == 2 else htmlduration[0]      # convert to minutes
                duration = duration * 60                                                                              # convert to seconds
                duration = datetime.fromtimestamp(duration)
                siteInfoDict['Duration'] = duration
                log('UTILS :: {0:<29} {1}'.format('Duration', duration.strftime('%H:%M:%S')))

            except Exception as e:
                siteInfoDict['Duration'] = FILMDICT['Duration']
                log('UTILS :: Error getting Site Film Duration: Reset to File Name Duration %s', e)
        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimage = html.xpath('//a[text()="Cover Jacket"]/@href')[0]
            poster = htmlimage.replace('bigcover', 'jacket_images')     # replace text of dvd cover url to get poster
            art = htmlimage.replace('bigcover', 'screen_shot')          # replace text of dvd cover url to get background
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoBestExclusivePorn(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'BestExclusivePorn'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Description: ")]')[0].strip()
            synopsis = htmlsynopsis.replace('Description: ', '')
            siteInfoDict['Synopsis'] = synopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', synopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        log('UTILS :: No Director Info on Agent - Set to Null')
        siteInfoDict['Directors'] = []

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Starring: ")]')[0].strip().replace('Starring: ', '')
            htmlcast = htmlcast.split(',') 
            htmlcast = [x.strip() for x in htmlcast if x.strip() and 'n/a' not in x.lower()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres and Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        compilation = 'No'
        try:
            htmlgenres = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Genre: ")]')[0].strip().replace('Genre: ', '')
            htmlgenres = htmlgenres.split(',')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                genresSet.add(newItem if newItem else item)

            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Compilation'] = compilation

        #   5b.  Countries
        log(LOG_SUBLINE)
        countriesSet = set()
        try:
            htmlcountries = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Country: ")]')[0].strip().replace('Country: ', '')
            htmlcountries = htmlcountries.split(',')
            htmlcountries = [x.strip() for x in htmlcountries if x.strip()]
            htmlcountries.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Countries', '{0:>2} - {1}'.format(len(htmlcountries), htmlcountries)))
            for idx, item in enumerate(htmlcountries, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue
                
                countriesSet.add(newItem)

            showSetData(countriesSet, 'Countries (set*)')

        except Exception as e:
            log('UTILS :: Error getting Countries: %s', e)

        finally:
            siteInfoDict['Countries'] = countriesSet

        #   6.  Release Date
        log(LOG_SUBLINE)
        kwReleaseDate = kwargs.get('kwReleaseDate')
        log('UTILS :: {0:<29} {1}'.format('KW Release Date', kwReleaseDate))
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmldate = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Production year:")]')[0].strip().replace('Production year: ', '')
                htmldate = '31-12-{0}'.format(htmldate)
                htmldate = datetime.strptime(htmldate, '%d-%m-%Y')
                siteInfoDict['ReleaseDate'] = htmldate
                log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration 
        kwDuration = kwargs.get('kwDuration')
        log('UTILS :: {0:<29} {1}'.format('KW Duration', kwDuration))
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlduration = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Duration:")]')[0].strip().replace('Duration: ', '')
                htmlduration = [int(x.strip()) for x in htmlduration.split(':') if x.strip()]
                duration = htmlduration[0] * 3600 + htmlduration[1] * 60 + htmlduration[2]                       # convert to seconds
                duration = datetime.fromtimestamp(duration)
                siteInfoDict['Duration'] = duration
                log('UTILS :: {0:<29} {1}'.format('Duration', duration.strftime('%H:%M:%S')))

            except Exception as e:
                siteInfoDict['Duration'] = FILMDICT['Duration']
                log('UTILS :: Error getting Site Film Duration: Reset to File Name Duration %s', e)
        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        FILMDICT['SceneAgent'] = True                 # notify update routine to crop images
        try:
            htmlimages = html.xpath('//div[@class="entry"]/p//img/@src')
            poster = htmlimages[0]
            art = htmlimages[1]

            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoCDUniverse(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'CDUniverse'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('.//div[@id="Description"]/span/text()')[0].strip()
            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', htmlsynopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//td[text()="Director"]/following-sibling::td/a/text()')
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//td[text()="Starring"]/following-sibling::td/a/text()')
            htmlcast = [x.strip() for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        countriesSet = set()
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//td[text()="Category"]/following-sibling::td/a/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem in COUNTRYSET:
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem if newItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   6.  Release Date - CD Universe Format = mmm dd, YYYY
        kwReleaseDate = kwargs.get('kwReleaseDate')
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmldate = html.xpath('//li[@class="section-detail-list-item-release-date"]/text()[normalize-space()]')[0].strip()
                htmldate = datetime.strptime(htmldate, '%b %d, %Y')
                siteInfoDict['ReleaseDate'] = htmldate
                log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration - No Duration on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Duration Info on Agent - Set to File Duration')
        siteInfoDict['Duration'] = FILMDICT['Duration']
        log('UTILS :: {0:<29} {1}'.format('Duration', siteInfoDict['Duration'].strftime('%H:%M:%S')))

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            poster = html.xpath('//img[@id="PIMainImg"]/@src')[0]
            art = html.xpath('//img[@id="0"]/@src')[0]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info - CDUniverse retains actually reviews - so collect these rather than setting up scenes and chapters
        log(LOG_SUBLINE)
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        scenesDict = {}
        chaptersDict = {}               # always null in CDUniverse
        try:
            htmlscenes = html.xpath('//table[@id="singlereview"]')
            log('UTILS :: {0:<29} {1}'.format('Possible Number of Scenes', len(htmlscenes)))
            if len(htmlscenes) == 0:
                raise Exception ('< No Scenes Found! >')

            log(LOG_SUBLINE)
            for sceneNo, htmlscene in enumerate(htmlscenes, start=1):
                try:
                    # scene No
                    log('UTILS :: {0:<29} {1}'.format('Scene', sceneNo))

                    # Review Source - composed of cast list or iafd scenes cast or Film title in that order of preference
                    reviewSource = ''
                    try:
                        reviewSource = htmlscene.xpath('.//span[contains(@style,"font-weight:bold")]/text()[normalize-space()]')
                        reviewSource = ''.join(reviewSource).strip()

                    except Exception as e:
                        log('UTILS :: Error getting Review Source: %s', e)

                    finally:
                        # prep for review metadata
                        if len(reviewSource) > 40:
                            for i in range(40, -1, -1):
                                if reviewSource[i] == ' ':
                                    reviewSource = reviewSource[0:i]
                                    break
                        if reviewSource:
                            reviewSource = '{0}. {1}...'.format(sceneNo, reviewSource)
                        else:
                            mySource = 'N/A'
                            reviewSource = '{0}. {1}...'.format(sceneNo, FILMDICT['Title'])
                            log('UTILS :: Warning No Review Source (Used Film Title)')

                        log('UTILS :: {0:<29} {1}'.format('Review Source', '{0} - {1}'.format(mySource, reviewSource) if reviewSource else 'None Recorded'))

                    # Review Author - composed of Settings
                    reviewAuthor = mySource
                    try:
                        try:
                            stars = htmlscene.xpath('.//img[contains(@alt,"star")]/@alt')[0]
                            stars = re.sub('[^0-9]', '', stars)   # strip out non-numerics
                            stars = [u'\U00002B50'] * int(stars)  # change type to list of size
                            stars = ''.join(stars)                # convert back to str
                            log('UTILS :: {0:<29} {1}'.format('Review Stars', stars))
                        except:
                            stars = ''
                        try:
                            writer =  htmlscene.xpath('.//td[@rowspan="2"]//text()[normalize-space()]')
                            writer = ''.join(writer).strip()
                            writer = re.sub(ur'^.+By', '', writer).replace('By', '').strip()
                            log('UTILS :: {0:<29} {1}'.format('Review Writer', writer))
                        except:
                            writer = ''
                        if stars or writer:
                            reviewAuthor = '{0} - {1}'.format(stars, writer)

                        log('UTILS :: {0:<29} {1}'.format('Review Author', reviewAuthor if reviewAuthor else 'None Recorded'))

                    except Exception as e:
                        log('UTILS :: Error getting Review Author (Stars & Writer): %s', e)


                    # Review Text - composed of Sexual Acts / tidy genres
                    reviewText = ''
                    try:
                        reviewText = htmlscene.xpath('.//span[@class="reviewtext"]/text()[normalize-space()]')
                        reviewText = ''.join(reviewText)
                        log('UTILS :: Review Text: %s', reviewText)
                    except Exception as e:
                        log('UTILS :: Error getting Review Text: %s', e)

                    finally:
                        # prep for review metadata
                        if len(reviewText) > 275:
                            for i in range(275, -1, -1):
                                if reviewText[i] in ['.', '!', '?']:
                                    reviewText = reviewText[0:i + 1]
                                    break
                        log('UTILS :: {0:<29} {1}'.format('Review Text', reviewText if reviewText else 'None Recorded'))

                    # save Review - scene
                    scenesDict[sceneNo] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText, 'Link': filmURL}

                except Exception as e:
                    log('UTILS :: Error getting Scene No. %s: %s', sceneNo, e)

        except Exception as e:
            log('UTILS :: Error getting Scenes: %s', e)

        finally:
            siteInfoDict['Scenes'] = scenesDict
            siteInfoDict['Chapters'] = chaptersDict

        #   10.  Rating
        log(LOG_SUBLINE)
        try:
            htmlrating = html.xpath('//a[contains(@title, "out of 5 stars")]/@title')[0]
            rating = htmlrating.split()[0]
            rating = float(rating) * 2.0
            siteInfoDict['Rating'] = rating
        except Exception as e:
            log('UTILS :: Error getting Rating: %s', e)
            siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoFagalicious(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'Fagalicious'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//section[@class="entry-content"]/p')
            synopsis = [x.text_content() for x in htmlsynopsis]
            synopsis = '\n'.join(synopsis)

            regex = r'.*writes:'
            pattern = re.compile(regex, re.IGNORECASE | re.DOTALL)
            synopsis = re.sub(pattern, '', synopsis)

            regex = ur'– Get the .*|– Download the .*|– Watch .*'
            pattern = re.compile(regex, re.IGNORECASE)
            synopsis = re.sub(pattern, '', synopsis)

            siteInfoDict['Synopsis'] = synopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', synopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        log('UTILS :: No Director Info on Agent - Set to Null')
        siteInfoDict['Directors'] = []

        #   3.  Cast
        log(LOG_SUBLINE)
        log('UTILS :: No Cast List on Agent: Built From Tag List')
        siteInfoDict['Cast'] = []

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Tag List: Genres, Cast and possible Countries, Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        countriesSet = set()
        castSet = set()
        compilation = 'No'
        testStudio = FILMDICT['Studio'].lower().replace(' ', '')
        testCast = [x.strip().replace(' ', '') for x in FILMDICT['FilenameCast']]
        try:
            htmltags = html.xpath('//ul/a[contains(@href, "https://fagalicious.com/tag/")]/text()')
            htmltags = [x.strip() for x in htmltags if x.strip()]
            htmltags = [x for x in htmltags if not '.tv' in x.lower()]
            htmltags = [x for x in htmltags if not '.com' in x.lower()]
            htmltags = [x for x in htmltags if not '.net' in x.lower()]
            htmltags.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Tags', '{0:>2} - {1}'.format(len(htmltags), htmltags)))
            compilation = 'Yes' if 'Compilation' in htmltags else 'No'
            for idx, item in enumerate(htmltags, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:                                                       # Don't process
                    continue

                tempItem = item.lower().replace(' ', '')
                if tempItem in testStudio or 'Movie' in item or 'Series' in item:         # skip if tag is studio
                    continue

                if testCast and tempItem in testCast:                                     # Check in filename cast list
                    continue

                if newItem in COUNTRYSET:                                                 # check if country
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem) if newItem else castSet.add(item)

            # also use synopsis to populate genres/countries as sometimes Scenes are not tagged with genres
            if siteInfoDict['Synopsis']:
                synopsis = re.sub(r'[^\w\s]',' ', siteInfoDict['Synopsis'])             # remove all punctuationion
                synopsis = re.sub(r'\b\w{1,3}\b', '', synopsis)                         # remove all short words (3 letters or less) - to avoid processing letters like you, us, him
                setSynopsis = set(synopsis.split())
                log('UTILS :: {0:<29} {1}'.format('Synopsis Word Count', '{0:>3} - {1}'.format(len(setSynopsis), setSynopsis)))
                for idx, item in enumerate(setSynopsis, start=1):
                    newItem = findTidy(item)
                    if not newItem or newItem is None:        # Don't process
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>3} - {1:<25} :: {2}'.format(idx, item, newItem)))
                    if newItem in COUNTRYSET:
                        countriesSet.add(newItem)
                    else:
                        genresSet.add(newItem)

            showSetData(castSet, 'Cast (set*)')
            showSetData(genresSet, 'Genres (set*)')
            showSetData(countriesSet, 'Countries (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Tags: Genres/Countries/Cast: %s', e)

        finally:
            for x in castSet:
                siteInfoDict['Cast'].append(x)

            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   6.  Release Date
        log(LOG_SUBLINE)
        kwReleaseDate = kwargs.get('kwReleaseDate')
        log('UTILS :: {0:<29} {1}'.format('KW Release Date', kwReleaseDate))
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmldate = html.xpath('//li[@class="meta-date"]/a/text()')[0]
                htmldate = datetime.strptime(htmldate, '%B %d, %Y')
                siteInfoDict['ReleaseDate'] = htmldate
                log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration - No Duration on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Duration Info on Agent - Set to File Duration')
        siteInfoDict['Duration'] = FILMDICT['Duration']
        log('UTILS :: {0:<29} {1}'.format('Duration', siteInfoDict['Duration'].strftime('%H:%M:%S')))

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        FILMDICT['SceneAgent'] = True                 # notify update routine to crop images
        try:
            htmlimages = html.xpath('//div[@class="mypicsgallery"]/a//img/@src')
            htmlimages = [x for x in htmlimages if 'data:image' not in x]
            poster = htmlimages[0]
            art = htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]

            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoGayDVDEmpire(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'Gay DVD Empire'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//div[@class="col-xs-12 text-center p-y-2 bg-lightgrey"]/div/p')[0].text_content()
            htmlsynopsis = re.sub('<[^<]+?>', '', htmlsynopsis).strip()
            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', htmlsynopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//a[contains(@label, "Director - details")]/text()[normalize-space()]')
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//a[@class="PerformerName" and @label="Performers - detail"]/text()')
            htmlcast = [x.strip() for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections: none recorded on this website
        log(LOG_SUBLINE)
        try:
            htmlcollections = html.xpath('//a[contains(@label, "Series")]/text()[normalize-space()]')
            htmlcollections = [x.replace('"', '').replace('Series', '').strip() for x in htmlcollections]
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            collections = list(set(htmlcollections))
            collections.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        countriesSet = set()
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//ul[@class="list-unstyled m-b-2"]//a[@label="Category"]/text()[normalize-space()]')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem in COUNTRYSET:
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem if newItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   6.  Release Date - GayDVDEmpire Format = mmm dd YYYY
        #       First retrieve Production Year, then if release date is within the same year use it as the plex release date as it has month and day data
        kwReleaseDate = kwargs.get('kwReleaseDate')
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmlproductionyear = html.xpath('//li/small[text()="Production Year:"]/following::text()[normalize-space()]')[0].strip()
                htmlproductionyear = '{0}1231'.format(htmlproductionyear)
                htmlproductionyear = datetime.strptime(htmlproductionyear, '%Y%m%d')
                siteInfoDict['ReleaseDate'] = htmlproductionyear
                log('UTILS :: {0:<29} {1}'.format('Production Date', htmlproductionyear.strftime('%Y-%m-%d')))

            except Exception as e:
                htmlproductionyear = ''
                log('UTILS :: Warning, No Production Year: %s', e)

            try:
                htmldate = html.xpath('//li/small[text()="Released:"]/following::text()[normalize-space()]')[0].strip()
                htmldate = datetime.strptime(htmldate, '%b %d %Y')
                siteInfoDict['ReleaseDate'] = htmldate

                if htmlproductionyear and htmlproductionyear.year == htmldate.year:
                    siteInfoDict['ReleaseDate'] = htmldate
                    msg = 'Film Date set to Release Date'
                else:
                    msg = 'Film Date set to default: 31st Dec of Production Year'

                log('UTILS :: {0:<29} {1}'.format('Release Date', siteInfoDict['ReleaseDate'].strftime('%Y-%m-%d')))
                log('UTILS :: {0:<29} {1}'.format('Note', msg))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration - GayDVDEmpire Format = h hrs. m mins.
        kwDuration = kwargs.get('kwDuration')
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlduration = html.xpath('//li/small[text()="Length: "]/parent::li/text()')[0].strip()
                htmlduration = '{0}00'.format(htmlduration)                                                 # add seconds
                htmlduration = htmlduration.replace('hrs.', ':').replace('mins.', ':').replace(' ', '')     # replace time strings with ':'
                htmlduration = htmlduration.split(':')                                                      # split into hr, mins, secs
                htmlduration = [int(x) for x in htmlduration]                                               # convert to integer
                htmlduration = ['0{0}'.format(x) if x < 10 else '{0}'.format(x) for x in htmlduration]      # converted to zero padded items
                htmlduration = ['00'] + htmlduration if len(htmlduration) == 2 else htmlduration            # prefix with zero hours if string is only minutes and seconds
                htmlduration = '1970-01-01 {0}'.format(':'.join(htmlduration))                              # prefix with 1970-01-01 to conform to timestamp
                htmlduration = datetime.strptime(htmlduration, '%Y-%m-%d %H:%M:%S')                         # turn to date time object
                siteInfoDict['Duration'] = htmlduration
                log('UTILS :: {0:<29} {1}'.format('Duration', htmlduration.strftime('%H:%M:%S')))

            except Exception as e:
                siteInfoDict['Duration'] = datetime.fromtimestamp(0)
                log('UTILS :: Error getting Site Film Duration: %s', e)
        else:
            siteInfoDict['Duration'] = siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        poster = ''
        art = ''
        try:
            htmlimage = html.xpath('//*[@id="front-cover"]/img/@src')[0]
            poster = htmlimage
            art = htmlimage.replace('h.jpg', 'bh.jpg')
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        scenesDict = {}
        chaptersDict = {}
        try:
            htmlscenes = html.xpath('//div[@class="col-sm-6 m-b-1"]/h3/a[@label="Scene Title"]/text()[normalize-space()]')
            log('UTILS :: {0:<29} {1}'.format('Possible Number of Scenes', len(htmlscenes)))
            if len(htmlscenes) == 0:
                raise Exception ('< No Scenes Found! >')

            htmlheadings = html.xpath('//div[@class="col-sm-6 m-b-1"]')
            htmldurations = html.xpath('//div[@class="col-sm-6 m-b-1"]/span[contains(text(), " min")]/text()[normalize-space()]')
            htmldurations = ['{0}:00'.format(x.split()[0]) for x in htmldurations]   # extract time strings - format MM convert to MM:SS

            # sum up the scenes' length: Gay DVD Empire uses Min format but htmlduration converted to MM:SS
            scenesDelta = timedelta()
            for htmlduration in htmldurations:
                (mm, ss) = htmlduration.split(':')
                scenesDelta += timedelta(minutes=int(mm), seconds=int(ss))

            # subtract the total scene length from the total films length to establish where the first scene begins: i.e the offset
            # TimeOffset = dx of duration of film - total of all scenes length, or 0 if film is stacked or scenes are strangely longer than the actual film
            durationTime = str(FILMDICT['Duration'].time())
            durationTime = datetime.strptime(str(durationTime),"%H:%M:%S")
            scenesTime = datetime.strptime(str(scenesDelta),"%H:%M:%S")
            if FILMDICT['Stacked'] == 'Yes':
                timeOffsetTime = datetime.fromtimestamp(0)
            else:
                timeOffsetTime = abs(durationTime - scenesTime)
                timeOffsetTime = datetime.strptime(str(timeOffsetTime),"%H:%M:%S")

            log('UTILS :: {0:<29} {1}'.format('Durations', 'Film: {0}, Scenes: {1}, Offset: {2} {3}'.format(durationTime.time(), scenesTime.time(), timeOffsetTime.time(), '(Stacked)' if FILMDICT['Stacked'] == 'Yes' else '')))

            log(LOG_SUBLINE)
            for sceneNo, (htmlheading, htmlscene, htmlduration) in enumerate(zip(htmlheadings, htmlscenes, htmldurations), start = 1):
                try:
                    # scene No
                    log('UTILS :: {0:<29} {1}'.format('Scene', sceneNo))

                    # Review Source - GayDVDEmpire has no Cast List per Scene, use iafd scenes cast or Film title in that order of preference
                    reviewSource = '{0}. {1}...'.format(sceneNo, FILMDICT['Title'])
                    mySource = 'N/A'
                    log('UTILS :: Warning No Review Source (Used Film Title)')
                    log('UTILS :: {0:<29} {1}'.format('Review Source', '{0} - {1}'.format(mySource, reviewSource) if reviewSource else 'None Recorded'))

                    # Review Author - default to website name
                    reviewAuthor = 'Gay DVD Empire'
                    log('UTILS :: {0:<29} {1}'.format('Review Author', reviewAuthor))

                    # Review Text
                    reviewText = ''
                    try:
                        reviewText = htmlheading.xpath('.//span[@class="badge"]/text()[normalize-space()]')
                        reviewText = ''.join(reviewText)

                    except Exception as e:
                        log('UTILS :: Error getting Review Text: %s', e)

                    finally:
                        # prep for review metadata
                        if len(reviewText) > 275:
                            for i in range(275, -1, -1):
                                if reviewText[i] in ['.', '!', '?']:
                                    reviewText = reviewText[0:i + 1]
                                    break
                        log('UTILS :: {0:<29} {1}'.format('Review Text', reviewText if reviewText else 'None Recorded'))

                    # save Review - scene
                    scenesDict[sceneNo] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText, 'Link': filmURL}

                    chapterTitle = reviewSource
                    chapterStartTime = (timeOffsetTime.hour * 60 * 60 + timeOffsetTime.minute * 60 + timeOffsetTime.second) * 1000
                    (mm, ss) = htmlduration.strip().split(':')
                    timeOffsetTime += timedelta(minutes=int(mm), seconds=int(ss))
                    chapterEndTime = (timeOffsetTime.hour * 60 * 60 + timeOffsetTime.minute * 60 + timeOffsetTime.second) * 1000
                    # next scene starts a second after last scene
                    timeOffsetTime += timedelta(seconds=1)

                    log('UTILS :: {0:<29} {1}'.format('Chapter', '{0} - {1}:{2}'.format(sceneNo, mm, ss)))
                    log('UTILS :: {0:<29} {1}'.format('Title', chapterTitle))
                    log('UTILS :: {0:<29} {1}'.format('Time', '{0} - {1}'.format(datetime.fromtimestamp(chapterStartTime/1000).strftime('%H:%M:%S'), datetime.fromtimestamp(chapterEndTime/1000).strftime('%H:%M:%S'))))

                    # save chapter
                    chaptersDict[sceneNo] = {'Title': chapterTitle, 'StartTime': chapterStartTime, 'EndTime': chapterEndTime}

                except Exception as e:
                    log('UTILS :: Error getting Scene No. %s: %s', sceneNo, e)

        except Exception as e:
            log('UTILS :: Error getting Scenes: %s', e)

        finally:
            siteInfoDict['Scenes'] = scenesDict
            siteInfoDict['Chapters'] = chaptersDict

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoGayHotMovies(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information    '''
    mySource = 'GayHotMovies'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//span[contains(@class,"video_description")]//text()')[0]
            htmlsynopsis = re.sub('<[^<]+?>', '', htmlsynopsis).strip()

            regex = r'The movie you are enjoying was created by consenting adults.*'
            pattern = re.compile(regex, re.DOTALL | re.IGNORECASE)
            htmlsynopsis = re.sub(pattern, '', htmlsynopsis)

            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', htmlsynopsis))

        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/director/")]/span/text()[normalize-space()]')
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//div[@class="name"]/a/text()[normalize-space()]')
            htmlcast = [x.strip() for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections
        log(LOG_SUBLINE)
        try:
            htmlcollections = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/series/")]/text()[normalize-space()]')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            collections = list(set(htmlcollections))
            collections.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        countriesSet = set()
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/category/")]/@title[normalize-space()]')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem in COUNTRYSET:
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem if newItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   6.  Release Date - GayHotMovies = YYYY-mm-dd
        #       First retrieve Production Year format YYYY, then if release date is within the same year use it as the plex release date as it has month and day data
        kwReleaseDate = kwargs.get('kwReleaseDate')
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmlproductionyear = html.xpath('//strong[text()="Released:"]/following::text()[normalize-space()]')[0].strip()
                htmlproductionyear = '{0}1231'.format(htmlproductionyear)
                htmlproductionyear = datetime.strptime(htmlproductionyear, '%Y%m%d')
                siteInfoDict['ReleaseDate'] = htmlproductionyear
                log('UTILS :: {0:<29} {1}'.format('Production Date', htmlproductionyear.strftime('%Y-%m-%d')))

            except Exception as e:
                htmlproductionyear = ''
                log('UTILS :: Warning, No Production Year: %s', e)

            try:
                htmldate = html.xpath('//strong[text()="Date Added:"]/following::text()[normalize-space()]')[0].strip()
                htmldate = datetime.strptime(htmldate, '%Y-%m-%d')
                siteInfoDict['ReleaseDate'] = htmldate

                if htmlproductionyear and htmlproductionyear.year == htmldate.year:
                    siteInfoDict['ReleaseDate'] = htmldate
                    msg = 'Film Date set to Release Date'
                else:
                    msg = 'Film Date set to default: 31st Dec of Production Year'

                log('UTILS :: {0:<29} {1}'.format('Release Date', siteInfoDict['ReleaseDate'].strftime('%Y-%m-%d')))
                log('UTILS :: {0:<29} {1}'.format('Note', msg))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration - GayHotMovies Format = HH:MM:SS
        kwDuration = kwargs.get('kwDuration')
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlduration = html.xpath('//span[text()="Running Time:"]/parent::li/text()|//span[@datetime]/text()')[0].strip()
                htmlduration = '1970-01-01 {0}'.format(htmlduration)                                        # prefix with 1970-01-01 to conform to timestamp
                htmlduration = datetime.strptime(htmlduration, '%Y-%m-%d %H:%M:%S')                         # turn to date time object
                siteInfoDict['Duration'] = htmlduration
                log('UTILS :: {0:<29} {1}'.format('Duration', htmlduration.strftime('%H:%M:%S')))

            except Exception as e:
                siteInfoDict['Duration'] = datetime.fromtimestamp(0)
                log('UTILS :: Error getting Site Film Duration: %s', e)
        else:
            siteInfoDict['Duration'] = siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        #       there are 3 ways front/art images are stored on gay hot movies - end with h.jpg for front and bh.jpg for art
        #                                                                      - end xfront.1.jpg for front and xback.1.jpg for art - these first two use the same xpath
        #                                                                      - just one image (old style)
        log(LOG_SUBLINE)
        try:
            poster = html.xpath('//div[@class="lg_inside_wrap"]/@data-front')[0]
            art = html.xpath('//div[@class="lg_inside_wrap"]/@data-back')[0]

        except Exception as e:
            log('UTILS :: Error getting Images, Try Old Style: %s', e)
            try:
                # sometimes no back cover exists... on some old movies/ so use cover photo for both poster/art
                htmlimage = html.xpath('//img[@id="cover" and @class="cover"]/@src')[0]
                log('UTILS ::{0:<29} {1}'.format('Old Style Image', 'Using Old Style Image'))
            except Exception as e:
                poster = ''
                art = ''
                log('UTILS :: Error getting Old Style Images: %s', e)
            else:
                poster = htmlimage
                art = htmlimage

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        #   9.  Scene Info
        log(LOG_SUBLINE)
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        scenesDict = {}
        chaptersDict = {}
        try:
            htmlscenes = html.xpath('//div[@class="scene_details_sm"]')
            log('UTILS :: {0:<29} {1}'.format('Possible Number of Scenes', len(htmlscenes)))
            if len(htmlscenes) == 0:
                raise Exception ('< No Scenes Found! >')

            # scene headings format = Clip 4 - 24 mins 38 secs
            htmltemp = html.xpath('//span[@class="right time"]/text()[normalize-space()]')
            htmlheadings = [x.split(' - ')[0].strip() for x in htmltemp]
            htmldurations = [x.split(' - ')[1] for x in htmltemp]   # extract time strings
            htmldurations = [x.split(' sec')[0] for x in htmldurations]   # extract time strings
            htmldurations = [x.strip().replace(' mins ', ':') for x in htmldurations]   # extract time strings

            # sum up the scenes' length: Gay Hot Movies uses xx Mins xx Secs format
            scenesDelta = timedelta()
            for htmlduration in htmldurations:
                (mm, ss) = htmlduration.split(':')
                scenesDelta += timedelta(minutes=int(mm), seconds=int(ss))

            # subtract the total scene length from the total films length to establish where the first scene begins: i.e the offset
            # TimeOffset = dx of duration of film - total of all scenes length, or 0 if film is stacked or scenes are strangely longer than the actual film
            durationTime = str(FILMDICT['Duration'].time())
            durationTime = datetime.strptime(str(durationTime),"%H:%M:%S")
            scenesTime = datetime.strptime(str(scenesDelta),"%H:%M:%S")
            if FILMDICT['Stacked'] == 'Yes':
                timeOffsetTime = datetime.fromtimestamp(0)
            else:
                timeOffsetTime = abs(durationTime - scenesTime)
                timeOffsetTime = datetime.strptime(str(timeOffsetTime),"%H:%M:%S")

            log('UTILS :: {0:<29} {1}'.format('Durations', 'Film: {0}, Scenes: {1}, Offset: {2} {3}'.format(durationTime.time(), scenesTime.time(), timeOffsetTime.time(), '(Stacked)' if FILMDICT['Stacked'] == 'Yes' else '')))

            for sceneNo, (htmlheading, htmlscene, htmlduration) in enumerate(zip(htmlheadings, htmlscenes, htmldurations), start = 1):
                try:
                    # scene No
                    log('UTILS :: {0:<29} {1}'.format('Scene', sceneNo))

                    # Review Source - composed of cast list or iafd scenes cast or Film title in that order of preference
                    reviewSource = ''
                    try:
                        # fill with Cast names from external website
                        reviewSource = htmlscene.xpath('./div/span[@class="scene_stars"]/a/text()[normalize-space()]')
                        reviewSource = [x.split('(')[0] for x in reviewSource]
                        reviewSource = ', '.join(reviewSource)

                        # prep for review metadata
                        if len(reviewSource) > 40:
                            for i in range(40, -1, -1):
                                if reviewSource[i] == ' ':
                                    reviewSource = reviewSource[0:i]
                                    break
                        if reviewSource:
                            reviewSource = '{0}. {1}...'.format(sceneNo, reviewSource)
                        else:
                            mySource = 'N/A'
                            reviewSource = '{0}. {1}...'.format(sceneNo, FILMDICT['Title'])
                            log('UTILS :: Warning No Review Source (Used Film Title)')

                        log('UTILS :: {0:<29} {1}'.format('Review Source', '{0} - {1}'.format(mySource, reviewSource) if reviewSource else 'None Recorded'))

                    except Exception as e:
                        log('UTILS :: Error getting Review Source (Cast): %s', e)

                    # Review Author - composed of Settings
                    reviewAuthor = 'Gay Hot Movies'
                    log('UTILS :: {0:<29} {1}'.format('Review Author', reviewAuthor))

                    # Review Text - composed of Sexual Acts / tidy genres
                    reviewText = ''
                    try:
                        reviewList = htmlscene.xpath('/div/span[@class="list_attributes"]/a/text()[normalize-space()]')
                        reviewList = [x.strip() for x in reviewList if x.strip()]
                        reviewList.sort(key = lambda x: x.lower())
                        mySet = set()
                        for idx, item in enumerate(reviewList, start=1):
                            newItem = findTidy(item)
                            log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))
                            if newItem is None:
                                continue
                            mySet.add(newItem if newItem else item)

                        reviewList = list(mySet)
                        reviewList.sort(key = lambda x: x.lower())
                        reviewText = ', '.join(reviewList)

                    except Exception as e:
                        log('UTILS :: Error getting Review Text (Sex Acts): %s', e)

                    finally:
                        # prep for review metadata
                        if len(reviewText) > 275:
                            for i in range(275, -1, -1):
                                if reviewText[i] in ['.', '!', '?']:
                                    reviewText = reviewText[0:i + 1]
                                    break
                        log('UTILS :: {0:<29} {1}'.format('Review Text', reviewText if reviewText else 'None Recorded'))


                    # save Review - scene
                    scenesDict[sceneNo] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText, 'Link': filmURL}

                    chapterTitle = reviewSource
                    chapterStartTime = (timeOffsetTime.hour * 60 * 60 + timeOffsetTime.minute * 60 + timeOffsetTime.second) * 1000
                    (mm, ss) = htmlduration.strip().split(':')
                    timeOffsetTime += timedelta(minutes=int(mm), seconds=int(ss))
                    chapterEndTime = (timeOffsetTime.hour * 60 * 60 + timeOffsetTime.minute * 60 + timeOffsetTime.second) * 1000
                    # next scene starts a second after last scene
                    timeOffsetTime += timedelta(seconds=1)

                    log('UTILS :: {0:<29} {1}'.format('Chapter', '{0} - {1}:{2}'.format(sceneNo, mm, ss)))
                    log('UTILS :: {0:<29} {1}'.format('Title', chapterTitle))
                    log('UTILS :: {0:<29} {1}'.format('Time', '{0} - {1}'.format(datetime.fromtimestamp(chapterStartTime/1000).strftime('%H:%M:%S'), datetime.fromtimestamp(chapterEndTime/1000).strftime('%H:%M:%S'))))

                    # save chapter
                    chaptersDict[sceneNo] = {'Title': chapterTitle, 'StartTime': chapterStartTime, 'EndTime': chapterEndTime}

                except Exception as e:
                    log('UTILS :: Error getting Scene No. %s: %s', sceneNo, e)
        except Exception as e:
            log('UTILS :: Error getting Scenes: %s', e)

        finally:
            siteInfoDict['Scenes'] = scenesDict
            siteInfoDict['Chapters'] = chaptersDict

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoGayFetishandBDSM(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'GayFetishAndBDSM'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//strong[contains(.,"Description:")]//parent::p/text()')
            htmlsynopsis = '\n'.join(htmlsynopsis)
            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', htmlsynopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//strong[contains(.,"Director")]//following::text()[normalize-space()]')[0]
            htmldirectors = htmldirectors.replace(':', '').split(',') if 'fusion' not in htmldirectors else []
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//strong[contains(.,"Actors")]//following::text()[normalize-space()]')[0]
            htmlcast = htmlcast.replace(':', '').split(',') if 'fusion' not in htmlcast else []
            htmlcast = [x.strip() for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        log('UTILS :: No Genres, Countries or Compilation Info on Agent - Try to Extract Information from key words in synopsis')
        genresSet = set()
        countriesSet = set()
        try:
            if siteInfoDict['Synopsis']:
                synopsis = re.sub(r'[^\w\s]',' ', siteInfoDict['Synopsis'])             # remove all punctuationion
                synopsis = re.sub(r'\b\w{1,3}\b', '', synopsis)                         # remove all short words (3 letters or less) - to avoid processing letters like you, us, him
                setSynopsis = set(synopsis.split())
                log('UTILS :: {0:<29} {1}'.format('Synopsis Word Count', '{0:>3} - {1}'.format(len(setSynopsis), setSynopsis)))
                for idx, item in enumerate(setSynopsis, start=1):
                    newItem = findTidy(item)
                    if not newItem or newItem is None:        # Don't process
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>3} - {1:<25} :: {2}'.format(idx, item, newItem)))
                    if newItem in COUNTRYSET:
                        countriesSet.add(newItem)
                    else:
                        genresSet.add(newItem)

                showSetData(countriesSet, 'Countries (set*)')
                showSetData(genresSet, 'Genres (set*)')
            else:
                log('UTILS :: No Synopsis Recorded: %s', e)

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        siteInfoDict['Genres'] = genresSet
        siteInfoDict['Countries'] = countriesSet
        siteInfoDict['Compilation'] = 'No'

        #   6.  Release Date - No Release Date on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Release Date Info on Agent - Set to File Name Year Dec 31st')
        if FILMDICT['Year']:
            productionDate = '{0}1231'.format(FILMDICT['Year'])
            productionDate = datetime.strptime(productionDate, '%Y%m%d')
        else:
            productionDate = datetime.fromtimestamp(0)

        siteInfoDict['ReleaseDate'] = productionDate
        log('UTILS :: {0:<29} {1}'.format('Production Date', productionDate.strftime('%Y-%m-%d')))

        #   7.  Duration - No Duration on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Duration Info on Agent - Set to File Duration')
        siteInfoDict['Duration'] = FILMDICT['Duration']
        log('UTILS :: {0:<29} {1}'.format('Duration', siteInfoDict['Duration'].strftime('%H:%M:%S')))

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//a[@class="fusion-lightbox"]/@href')  # only need first two images
            log('UTILS :: {0:<29} {1}'.format('Images', '{0:>} - {1}'.format(len(htmlimages), htmlimages)))
            images = []
            [images.append(x) for x in htmlimages if x not in images]
            poster = images[0]
            art = images[1] if len(images) > 1 else poster
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoGayMovie(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'GayMovie'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//div[@class="fusion-text fusion-text-2"]/p/text()')
            htmlsynopsis = '\n'.join(htmlsynopsis)
            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', htmlsynopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//strong[contains(.,"Director")]/following::text()[normalize-space()]')[0]
            htmldirectors = htmldirectors.replace(':', '').split(',') if 'fusion' not in htmldirectors else []
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//strong[contains(.,"Actors")]/following::text()[normalize-space()]')[0]
            htmlcast = htmlcast.replace(':', '').split(',') if 'fusion' not in htmlcast else []
            htmlcast = [x.strip() for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        log('UTILS :: No Genres, Countries or Compilation Info on Agent - Try to Extract Information from key words in synopsis')
        genresSet = set()
        countriesSet = set()
        try:
            if siteInfoDict['Synopsis']:
                synopsis = re.sub(r'[^\w\s]',' ', siteInfoDict['Synopsis'])             # remove all punctuationion
                synopsis = re.sub(r'\b\w{1,3}\b', '', synopsis)                         # remove all short words (3 letters or less) - to avoid processing letters like you, us, him
                setSynopsis = set(synopsis.split())
                log('UTILS :: {0:<29} {1}'.format('Synopsis Word Count', '{0:>3} - {1}'.format(len(setSynopsis), setSynopsis)))
                for idx, item in enumerate(setSynopsis, start=1):
                    newItem = findTidy(item)
                    if not newItem or newItem is None:        # Don't process
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>3} - {1:<25} :: {2}'.format(idx, item, newItem)))
                    if newItem in COUNTRYSET:
                        countriesSet.add(newItem)
                    else:
                        genresSet.add(newItem)

                showSetData(countriesSet, 'Countries (set*)')
                showSetData(genresSet, 'Genres (set*)')
            else:
                log('UTILS :: No Synopsis Recorded: %s', e)

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        siteInfoDict['Genres'] = genresSet
        siteInfoDict['Countries'] = countriesSet
        siteInfoDict['Compilation'] = 'No'

        #   6.  Release Date - No Release Date on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Release Date Info on Agent - Set to File Name Year Dec 31st')
        if FILMDICT['Year']:
            productionDate = '{0}1231'.format(FILMDICT['Year'])
            productionDate = datetime.strptime(productionDate, '%Y%m%d')
        else:
            productionDate = datetime.fromtimestamp(0)

        siteInfoDict['ReleaseDate'] = productionDate
        log('UTILS :: {0:<29} {1}'.format('Production Date', productionDate.strftime('%Y-%m-%d')))

        #   7.  Duration - No Duration on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Duration Info on Agent - Set to File Duration')
        siteInfoDict['Duration'] = FILMDICT['Duration']
        log('UTILS :: {0:<29} {1}'.format('Duration', siteInfoDict['Duration'].strftime('%H:%M:%S')))

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//a[@class="fusion-lightbox"]/@href')  # only need first two images
            log('UTILS :: {0:<29} {1}'.format('Images', '{0:>} - {1}'.format(len(htmlimages), htmlimages)))
            images = []
            [images.append(x) for x in htmlimages if x not in images]
            poster = images[0]
            art = images[1] if len(images) > 1 else poster
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoGayRado(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'GayRado'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//div[@class="product-description"]/text()')[0].strip()
            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', htmlsynopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//p[@style]/text()[contains(.,"Director: ")]')[0].replace('Director: ', '').split(',')
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//p[@style]/text()[contains(.,"Starring: ")]')[0].replace('Starring: ', '').split(',')
            htmlcast = [x.strip() for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        countriesSet = set()
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//span[@style=""]/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem in COUNTRYSET:
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem if newItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   6.  Release Date - GayRado Format = mmm dd, YYYY
        log(LOG_SUBLINE)
        log('UTILS :: No Release Date on Agent: Set to Default 31st of Filename Year, if present')
        kwReleaseDate = kwargs.get('kwReleaseDate')
        siteInfoDict['Collections'] = kwReleaseDate

        #   7.  Duration 
        kwDuration = kwargs.get('kwDuration')
        log('UTILS :: {0:<29} {1}'.format('KW Duration', kwDuration))
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlduration = html.xpath('//p[@style]/text()[contains(.,"Running Time: ")]')[0]
                htmlduration = re.sub('[^0-9]', ' ', htmlduration).split()                                            # strip away alphabetic characters leaving hrs and mins sepated by space
                htmlduration = [int(x) for x in htmlduration if x.split()]                                            # convert to integer
                duration = htmlduration[0] * 60 + htmlduration[1] if len(htmlduration) == 2 else htmlduration[0]      # convert to minutes
                duration = duration  * 60                                                                             # convert to seconds
                duration = datetime.fromtimestamp(duration)
                siteInfoDict['Duration'] = duration
                log('UTILS :: {0:<29} {1}'.format('Duration', duration.strftime('%H:%M:%S')))

            except Exception as e:
                siteInfoDict['Duration'] = FILMDICT['Duration']
                log('UTILS :: Error getting Site Film Duration: Reset to File Name Duration %s', e)

        else:
            siteInfoDict['Duration'] = siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//a[contains(@class,"magictoolbox")]/@href')
            poster = htmlimages[0]
            art = htmlimages[1]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoGayWorld(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'GayWorld'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//strong[contains(.,"Description:")]//parent::p/text()')
            htmlsynopsis = '\n'.join(htmlsynopsis)
            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', htmlsynopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//strong[contains(.,"Director")]//following::text()[normalize-space()]')[0]
            htmldirectors = htmldirectors.replace(':', '').split(',') if 'fusion' not in htmldirectors else []
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//strong[contains(.,"Actors")]/following::text()[normalize-space()]')[0]
            htmlcast = htmlcast.replace(':', '').split(',') if 'fusion' not in htmlcast else []
            htmlcast = [x.strip() for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        log('UTILS :: No Genres, Countries or Compilation Info on Agent - Try to Extract Information from key words in synopsis')
        genresSet = set()
        countriesSet = set()
        try:
            if siteInfoDict['Synopsis']:
                synopsis = re.sub(r'[^\w\s]',' ', siteInfoDict['Synopsis'])             # remove all punctuationion
                synopsis = re.sub(r'\b\w{1,3}\b', '', synopsis)                         # remove all short words (3 letters or less) - to avoid processing letters like you, us, him
                setSynopsis = set(synopsis.split())
                log('UTILS :: {0:<29} {1}'.format('Synopsis Word Count', '{0:>3} - {1}'.format(len(setSynopsis), setSynopsis)))
                for idx, item in enumerate(setSynopsis, start=1):
                    newItem = findTidy(item)
                    if not newItem or newItem is None:        # Don't process
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>3} - {1:<25} :: {2}'.format(idx, item, newItem)))
                    if newItem in COUNTRYSET:
                        countriesSet.add(newItem)
                    else:
                        genresSet.add(newItem)

                showSetData(countriesSet, 'Countries (set*)')
                showSetData(genresSet, 'Genres (set*)')
            else:
                log('UTILS :: No Synopsis Recorded: %s', e)

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        siteInfoDict['Genres'] = genresSet
        siteInfoDict['Countries'] = countriesSet
        siteInfoDict['Compilation'] = 'No'

        #   6.  Release Date - No Release Date on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Release Date Info on Agent - Set to File Name Year Dec 31st')
        if FILMDICT['Year']:
            productionDate = '{0}1231'.format(FILMDICT['Year'])
            productionDate = datetime.strptime(productionDate, '%Y%m%d')
        else:
            productionDate = datetime.fromtimestamp(0)

        siteInfoDict['ReleaseDate'] = productionDate
        log('UTILS :: {0:<29} {1}'.format('Production Date', productionDate.strftime('%Y-%m-%d')))

        #   7.  Duration - No Duration on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Duration Info on Agent - Set to File Duration')
        siteInfoDict['Duration'] = FILMDICT['Duration']
        log('UTILS :: {0:<29} {1}'.format('Duration', siteInfoDict['Duration'].strftime('%H:%M:%S')))

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//a[@class="fusion-lightbox"]/@href')  # only need first two images
            log('UTILS :: {0:<29} {1}'.format('Images', '{0:>} - {1}'.format(len(htmlimages), htmlimages)))
            images = []
            [images.append(x) for x in htmlimages if x not in images]
            poster = images[0]
            art = images[1] if len(images) > 1 else poster
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoGEVI(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'GEVI'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        siteInfoDict['Synopsis'] = ''
        synopsis = ''
        try:
            htmlsynopsis = html.xpath('//td[contains(text(),"promo/")]//following-sibling::td//span[@style]/text()[following::br]')
            synopsis = '\n'.join(htmlsynopsis).strip()
            log('UTILS :: {0:<29} {1}'.format('Synopsis', synopsis))

            if synopsis:
                regex = r'View this scene at.*|found in compilation.*|see also.*|^\d+\.$'
                pattern = re.compile(regex, re.IGNORECASE | re.MULTILINE)
                synopsis = re.sub(pattern, '', synopsis).strip()

        except Exception as e:
            synopsis = ''
            log('UTILS :: Error getting GEVI Synopsis (Try External): %s', e)

        finally:
            if not synopsis:
                for key in ['AEBNiii', 'GayDVDEmpire', 'GayHotMovies']:
                    if key in FILMDICT and FILMDICT[key] != {}:
                        if 'Synopsis' in FILMDICT[key] and FILMDICT[key]['Synopsis']:
                            synopsis = FILMDICT[key]['Synopsis']
                            log('UTILS :: {0:<29} {1}'.format('Synopsis From', key))
                            break
            siteInfoDict['Synopsis'] = synopsis if synopsis else ''

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            # GEVI has access to external websites: AEBN, GayHotMovies, then GayDVDEmpire
            htmldirectors = html.xpath('//a[contains(@href, "/director/")]/text()')
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directorsLength = len(directors)
            directors.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('GEVI Directors', '{0:>2} - {1}'.format(len(directors), sorted(directors))))

            for key in ['AEBNiii', 'GayHotMovies', 'GayDVDEmpire']:
                if key in FILMDICT and FILMDICT[key] != {}:
                    if 'Directors' in FILMDICT[key] and FILMDICT[key]['Directors'] != set():
                        if len(FILMDICT[key]['Directors']) > directorsLength:
                            directors = FILMDICT[key]['Directors']
                            log('UTILS :: {0:<29} {1}'.format('External Directors', '{0} - {1}'.format(key), directors))
                            break

            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            # GEVI has access to external websites: AEBN, GayHotMovies, then GayDVDEmpire
            htmlcast = html.xpath('//a[contains(@href, "/performer/")]//text()')
            htmlcast = [x.strip() for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            castLength = len(cast)
            cast.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('GEVI Cast', '{0:>2} - {1}'.format(castLength, cast)))

            for key in ['AEBNiii', 'GayHotMovies', 'GayDVDEmpire']:
                if key in FILMDICT and FILMDICT[key] != {}:
                    if 'Cast' in FILMDICT[key] and FILMDICT[key]['Cast'] != set():
                        if len(FILMDICT[key]['Cast']) > castLength:
                            cast = FILMDICT[key]['Cast']
                            log('UTILS :: {0:<29} {1}'.format('External Cast', '{0} - {1}'.format(key), sorted(cast)))
                            break

            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        try:
            try:
                htmlbodytypes = html.xpath('//td[contains(text(),"body types")]//following-sibling::td[1]/text()')[0].strip()           # add GEVI body type to genres
                htmlbodytypes = htmlbodytypes.replace(';', ',')
                htmlbodytypes = [x.strip() for x in htmlbodytypes.split(',')]
                log('UTILS :: {0:<29} {1}'.format('Body Types', '{0:>2} - {1}'.format(len(htmlbodytypes), htmlbodytypes)))

            except Exception as e:
                htmlbodytypes = []
                log('UTILS :: Error getting Body Types: %s', e)

            try:
                htmlcategories = html.xpath('//td[contains(text(),"category")]//following-sibling::td[1]/text()')[0].strip()            # add GEVI categories to genres
                htmlcategories = [x.strip() for x in htmlcategories.split(',')]
                log('UTILS :: {0:<29} {1}'.format('Categories', '{0:>2} - {1}'.format(len(htmlcategories), htmlcategories)))

            except Exception as e:
                htmlcategories = []
                log('UTILS :: Error getting Categories: %s', e)

            try:
                htmltypes = html.xpath('//td[contains(text(),"type")]//following-sibling::td[1]/text()')[0].strip()                     # add GEVI types
                htmltypes = htmltypes.replace(';', ',')
                htmltypes = [x.strip() for x in htmltypes.split(',')]
                log('UTILS :: {0:<29} {1}'.format('Types', '{0:>2} - {1}'.format(len(htmltypes), htmltypes)))

            except Exception as e:
                htmltypes = []
                log('UTILS :: Error getting Types: %s', e)

            # GEVI has access to external websites: AEBN, GayHotMovies, GayDVDEmpire
            genresSet = set()
            for key in ['AEBNiii', 'GayHotMovies', 'GayDVDEmpire']:
                if key in FILMDICT and FILMDICT[key] != {}:
                    if 'Genres' in  FILMDICT[key] and FILMDICT[key]['Genres'] != set():
                        genresSet.update(FILMDICT[key]['Genres'])

            log('UTILS :: {0:<29} {1}'.format('External Genres', '{0:>2} - {1}'.format(len(genresSet), sorted(genresSet))))

            # process all genres, strip duplicates then add to genre metadata
            geviGenres = htmlbodytypes + htmlcategories + htmltypes
            log('UTILS :: {0:<29} {1}'.format('GEVI Genres', '{0:>2} - {1}'.format(len(geviGenres), geviGenres)))
            for idx, item in enumerate(geviGenres, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                genresSet.add(newItem if newItem else item)

            log('UTILS :: {0:<29} {1}'.format('Combined Genres', '{0:>2} - {1}'.format(len(genresSet), sorted(genresSet))))
            siteInfoDict['Genres'] = genresSet

        except Exception as e:
            siteInfoDict['Genres'] = set()
            log('UTILS :: Error getting Genres: %s', e)

        #   5b.   Countries
        log(LOG_SUBLINE)
        try:
            # GEVI has access to external websites: AEBN, GayHotMovies, then GayDVDEmpire
            countriesSet = set()
            for key in ['AEBNiii', 'GayHotMovies', 'GayDVDEmpire']:
                if key in FILMDICT and FILMDICT[key] != {}:
                    if 'Countries' in FILMDICT[key] and FILMDICT[key]['Countries'] != set():
                        countriesSet.update(FILMDICT[key]['Countries'])

            log('UTILS :: {0:<29} {1}'.format('External Countries', '{0:>2} - {1}'.format(len(countriesSet), sorted(countriesSet))))

            htmlcountries = html.xpath('//td[contains(text(),"location")]//following-sibling::td[1]/text()')[0].strip()
            htmlcountries = [x.strip() for x in htmlcountries.split(',')]
            log('UTILS :: {0:<29} {1}'.format('GEVI Countries', '{0:>2} - {1}'.format(len(htmlcountries), htmlcountries)))
            for idx, item in enumerate(htmlcountries, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))
                if newItem is None:        # Don't process
                    continue

                countriesSet.add(newItem if newItem else item)

            log('UTILS :: {0:<29} {1}'.format('Combined Countries', '{0:>2} - {1}'.format(len(countriesSet), sorted(countriesSet))))
            siteInfoDict['Countries'] = countriesSet

        except Exception as e:
            siteInfoDict['Countries'] = set()
            log('UTILS:: Error getting Countries: %s', e)

        #   5c.   Compilation
        kwCompilation = kwargs.get('kwCompilation')
        if kwCompilation is None:
            log(LOG_SUBLINE)
            siteInfoDict['Compilation'] = 'Yes' if 'Compilations' in siteInfoDict['Genres'] else 'No'
            log('UTILS :: {0:<29} {1}'.format('Compilation?', siteInfoDict['Compilation']))
        else:
            siteInfoDict['Compilation'] = kwCompilation

        #   6.  Release Date - GEVI Formats - 1. YYYY, 2. YYYY-YY, 3. YYYY,YYYY 4. cYYYY 5. ? 6. Null
        #                      The Date(s) can be different as they are released by different Distributors - compare against File Name Year
        kwReleaseDate = kwargs.get('kwReleaseDate')
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                compareYear = datetime.now().year + 2
                htmldate = html.xpath('//td[.="released" or .="produced"]/following-sibling::td[1]/text()[normalize-space()]')
                productionDates = set()
                for item in htmldate:
                    if not item or item == '?':                                                                     # format 5 & 6 - ignore if date is unknown
                        continue
                    if 'c' in item:                                                                                 # format 4
                        item = item.replace('c', '')
                    elif ',' in item:                                                                               # format 3 - take year after the comma
                        item = item.split(',')[1]
                    elif '-' in item:                                                                               # format 2 - take year after dash:
                        items = item.split('-')
                        items = [x.strip() for x in items]
                        if len(items[1]) == 1:              
                            item = '{0}{1}'.format(item[0][0:2], item.split('-')[1])                                # e.g 1995-7  -> 199 + 7
                        elif len(items[1]) == 2:             # e.g 1995-97
                            item = '{0}{1}'.format(item[0][0:1], item.split('-')[1])                                # e.g 1995-97 -> 19 + 97
                        else:
                            item = item[1]                                                                          # eg 1995-1997 -> 1997

                    # item should now be in YY or YYYY format, if year format YY is less than the comparison date it's 1999, convert to date and add to set
                    item = item if len(item) == 4 else '{0}{1}'.format(20 if item <= compareYear else 19, item)     # pad 2 digit years with correct century
                    item = '{0}1231'.format(item)
                    productionDates.add(datetime.strptime(item, '%Y%m%d'))

                siteInfoDict['ReleaseDate'] = min(productionDates) if productionDates else datetime.fromtimestamp(0)
                log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration - GEVI Format = MMM
        kwDuration = kwargs.get('kwDuration')
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlduration = html.xpath('//td[.="length"]/following-sibling::td[1]/text()[normalize-space()]')
                durations = {datetime.fromtimestamp(int(x) * 60) for x in htmlduration if x.strip()}
                siteInfoDict['Duration'] = sorted(durations)[-1] if durations else datetime.fromtimestamp(0)  # longest length or 0 time

            except Exception as e:
                siteInfoDict['Duration'] = datetime.fromtimestamp(0)
                log('UTILS :: Error getting Site Film Duration: %s', e)
        else:
            siteInfoDict['Duration'] = siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            # for posters - GayHotMovies comes last in priority as the other 2 have better qualty
            htmlimages = html.xpath('//img/@src[contains(.,"Covers")]')
            htmlimages = [(BASE_URL if BASE_URL not in image else '') + image.replace('/Icons/','/') for image in htmlimages]
            log('UTILS :: {0:<29} {1}'.format('Images', '{0:>} - {1}'.format(len(htmlimages), htmlimages)))
            images = []
            [images.append(x) for x in htmlimages if x not in images]
            poster = images[0]
            art = images[1] if len(images) > 1 else poster
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))
            log('UTILS :: Check if Better Quality External Poster/Art Exits')

            for key in ['AEBNiii', 'GayDVDEmpire', 'GayHotMovies']:
                if key in FILMDICT and FILMDICT[key] != {}:
                    if FILMDICT[key]['Poster'] != FILMDICT[key]['Art']:     # old gayhotmovies sometimes dont have background art - might as well use GEVI if that old
                        poster = FILMDICT[key]['Poster'] 
                        art = FILMDICT[key]['Art']
                        break
            log('UTILS :: {0:<29} {1}'.format('Possible External Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Possible External Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info: if GEVI Review Exists - Use by default, use chapter info from External if they Exist
        log(LOG_SUBLINE)
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        scenesDict = {}
        chaptersDict = {}
        try:
            htmlscenes = html.xpath('//td[@class="scene"]')
            log('UTILS :: {0:<29} {1}'.format('Possible Number of Scenes', len(htmlscenes)))

            for sceneNo, scene in enumerate(htmlscenes, start=1):
                try:
                    # scene No
                    log('UTILS :: {0:<29} {1}'.format('Scene', sceneNo))

                    # Review Source - composed of cast list or iafd scenes cast or Film title in that order of preference
                    reviewSource = ''
                    try:
                        reviewSource = scene.xpath('./span[@class="plist"]//text()[normalize-space()]')
                        reviewSource = [x for x in reviewSource if x[0] != ' ']
                        reviewSource = ''.join(reviewSource).strip()
                        reviewSource = re.sub(' \(.*?\)', '', reviewSource)    # GEVI sometimes has the studio in brackets after the cast name
                    except:
                        reviewSource = ''
                    finally:
                        # prep for review metadata
                        if len(reviewSource) > 40:
                            for i in range(40, -1, -1):
                                if reviewSource[i] == ' ':
                                    reviewSource = reviewSource[0:i]
                                    break
                        if reviewSource:
                            reviewSource = '{0}. {1}...'.format(sceneNo, reviewSource)
                        else:
                            mySource = 'N/A'
                            reviewSource = '{0}. {1}...'.format(sceneNo, FILMDICT['Title'])
                            log('UTILS :: Warning No Review Source (Used Film Title)')

                        log('UTILS :: {0:<29} {1}'.format('Review Source', '{0} - {1}'.format(mySource, reviewSource) if reviewSource else 'None Recorded'))

                    # Review Author - Agent Name
                    reviewAuthor = 'GEVI'

                    # Review Text
                    reviewText = ''
                    try:
                        reviewText = scene.xpath('./span[@style]//text()[normalize-space()]')
                        reviewText = ''.join(reviewText).strip()
                    except:
                        log('UTILS :: Error getting Review Text: %s', e)
                    finally:
                        # prep for review metadata
                        if len(reviewText) > 275:
                            for i in range(275, -1, -1):
                                if reviewText[i] in ['.', '!', '?']:
                                    reviewText = reviewText[0:i + 1]
                                    break
                        log('UTILS :: {0:<29} {1}'.format('Review Text', reviewText if reviewText else 'None Recorded'))

                    # save Review - scene
                    scenesDict[sceneNo] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText, 'Link': filmURL}

                except Exception as e:
                    log('UTILS :: Error getting Scene No. %s: %s', sceneNo, e)

            # External Reviews / Scenes
            for key in ['AEBNiii', 'GayHotMovies', 'GayDVDEmpire']:
                if key in FILMDICT and FILMDICT[key] != {}:
                    if scenesDict == {}:
                        log('UTILS :: {0:<29} {1}'.format('External Scenes', '{0} - {1}'.format('Yes', key)))
                        scenesDict = FILMDICT[key]['Scenes']
                    chaptersDict = FILMDICT[key]['Chapters']
                    log('UTILS :: {0:<29} {1}'.format('External Chapters', '{0} - {1}'.format('Yes', key)))
                    break

        except Exception as e:
            log('UTILS :: Error getting Scenes: %s', e)

        finally:
            siteInfoDict['Scenes'] = scenesDict
            siteInfoDict['Chapters'] = chaptersDict

        #   10.  Rating
        log(LOG_SUBLINE)
        try:
            htmlrating = html.xpath('//td[contains(text(),"rating out of 4")]//following-sibling::td[1]/text()')
            htmlrating = [x.strip() for x in htmlrating if '*' in x]
            maxStars = len(htmlrating) * 4                          # maximum of 4 stars per rating type where len is number of types
            if maxStars:
                log('UTILS :: {0:<29} {1}'.format('Maximum Possible Stars', '{0} Stars'.format(maxStars)))
                htmlrating = ''.join(htmlrating)
                starCount = htmlrating.count('*') 
                log('UTILS :: {0:<29} {1}'.format('Star Count', '{0} Stars'.format(starCount)))
                rating = (10.0 * starCount) / maxStars                # must be a float value
                log('UTILS :: {0:<29} {1}'.format('Film Rating', rating))
                siteInfoDict['Rating'] = rating
            else:
                raise Exception('< No Rated! >')
        except Exception as e:
            siteInfoDict['Rating'] = 0.0
            log('UTILS :: Error getting Rating: %s', e)

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoHFGPM(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'HFPGM'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//div[@class="base fullstory"]/div[@class="maincont clr"]//div[@id]/node()')[0]
            htmlsynopsis = htmlsynopsis.xpath('./node()')
            htmlsynopsis = [x for x in htmlsynopsis if 'ElementStringResult' in str(type(x))]
            synopsis = max(htmlsynopsis, key=len).strip()
            siteInfoDict['Synopsis'] = synopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', synopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//div[@class="base fullstory"]/div[@class="maincont clr"]//div/node()[((self::strong or self::b) and contains(.,"Director"))]/following-sibling::text()[1]')[0]
            htmldirectors = htmldirectors.replace(': ', '')
            htmldirectors = htmldirectors.split(',')
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//div[@class="base fullstory"]/div[@class="maincont clr"]//div/node()[((self::strong or self::b) and (contains(.,"Cast") or contains(.,"Stars")))]/following-sibling::text()[1]')[0]
            htmlcast = htmlcast.replace(': ', '')
            htmlcast = htmlcast.split(',') 
            htmlcast = [x.strip() for x in htmlcast if x.strip() and 'n/a' not in x.lower()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres and Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//div[@class="base fullstory"]/div[@class="maincont clr"]//div/node()[((self::strong or self::b) and (contains(.,"Categories:") or contains(.,"Genres:")))]/following-sibling::text()[1]')[0]
            htmlgenres = htmlgenres.replace('/', ',')
            htmlgenres = htmlgenres.split(',')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                genresSet.add(newItem if newItem else item)

            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Compilation'] = compilation

        #   5b.  Countries
        log(LOG_SUBLINE)
        countriesSet = set()
        try:
            htmlcountries = html.xpath('//div[@class="base fullstory"]/div[@class="maincont clr"]//div/node()[((self::strong or self::b) and (contains(.,"Country")))]/following-sibling::text()[1]')[0]
            htmlcountries = htmlcountries.replace(': ', '')
            htmlcountries = htmlcountries.split(',')
            htmlcountries = [x.strip() for x in htmlgenres if x.strip()]
            htmlcountries.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlcountries), htmlcountries)))
            for idx, item in enumerate(htmlcountries, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue
                
                countriesSet.add(newItem)

            showSetData(countriesSet, 'Countries (set*)')

        except Exception as e:
            log('UTILS :: Error getting Countries: %s', e)

        finally:
            siteInfoDict['Countries'] = countriesSet

        #   6.  Release Date
        log(LOG_SUBLINE)
        kwReleaseDate = kwargs.get('kwReleaseDate')
        log('UTILS :: {0:<29} {1}'.format('KW Release Date', kwReleaseDate))
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmldate = html.xpath('./div[@class="base shortstory"]/div[@class="maincont"]/div/text()[contains(.,"Release Year:")]')[0].strip()
                htmldate = datetime.strptime(htmldate, '%d-%m-%Y')
                siteInfoDict['ReleaseDate'] = htmldate
                log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration 
        kwDuration = kwargs.get('kwDuration')
        log('UTILS :: {0:<29} {1}'.format('KW Duration', kwDuration))
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlduration = html.xpath('./div[@class="base shortstory"]/div[@class="maincont"]/div/text()[contains(.,"mn ")]')[0].strip()
                durationM = htmlduration.partition('mn ')
                durationH = htmlduration.partition('h ')
                duration = int(durationH[0]) * 60 + int(durationM[1])
                duration = duration * 60                                                                              # convert to seconds
                duration = datetime.fromtimestamp(duration)
                siteInfoDict['Duration'] = duration
                log('UTILS :: {0:<29} {1}'.format('Duration', duration.strftime('%H:%M:%S')))

            except Exception as e:
                siteInfoDict['Duration'] = FILMDICT['Duration']
                log('UTILS :: Error getting Site Film Duration: Reset to File Name Duration %s', e)
        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//div[@class="base fullstory"]/div[@class="maincont clr"]//div//img/@src')
            for i, htmlimage in enumerate(htmlimages):
                htmlimages[i] = htmlimage if 'https:' in htmlimage else 'https:' + htmlimage

            if len(htmlimages) == 1:    # if only one image duplicate it
                htmlimages.append(htmlimages[0])

            poster = htmlimages[0]
            art = htmlimages[1]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoHomoActive(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'HomoActive'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//div[@class="description"]/div[@class="std"]/text()')
            synopsis = " ".join(htmlsynopsis).strip()
            siteInfoDict['Synopsis'] = synopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', synopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//dt[text()="Director:"]/following-sibling::dd[1]/text()[normalize-space()]')
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//dt[text()="Actors:"]/following-sibling::dd[1]/a/text()')
            htmlcast = [x.strip() for x in htmlcast if x.strip() and 'n/a' not in x.lower()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres and Compilation
        log(LOG_SUBLINE)
        log('UTILS :: No Genres or Compilation Info on Agent - Try to Extract Information from key words in synopsis')
        genresSet = set()
        compilation = 'No'
        try:
            if siteInfoDict['Synopsis']:
                synopsis = re.sub(r'[^\w\s]',' ', siteInfoDict['Synopsis'])             # remove all punctuationion
                synopsis = re.sub(r'\b\w{1,3}\b', '', synopsis)                         # remove all short words (3 letters or less) - to avoid processing letters like you, us, him
                setSynopsis = set(synopsis.split())
                log('UTILS :: {0:<29} {1}'.format('Synopsis Word Count', '{0:>3} - {1}'.format(len(setSynopsis), setSynopsis)))
                for idx, item in enumerate(setSynopsis, start=1):
                    newItem = findTidy(item)
                    if not newItem or newItem is None:        # Don't process
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>3} - {1:<25} :: {2}'.format(idx, item, newItem)))
                    genresSet.add(newItem)

                showSetData(genresSet, 'Genres (set*)')
            else:
                log('UTILS :: No Synopsis Recorded: %s', e)

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        siteInfoDict['Genres'] = genresSet
        siteInfoDict['Compilation'] = compilation

        #   5b.  Countries
        log(LOG_SUBLINE)
        countriesSet = set()
        try:
            htmlcountries = html.xpath('//dt[text()="Country:"]/following-sibling::dd[1]/text()[normalize-space()]')
            htmlcountries = [x.strip() for x in htmlcountries if x.strip()]
            htmlcountries.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Countries', '{0:>2} - {1}'.format(len(htmlcountries), htmlcountries)))
            for idx, item in enumerate(htmlcountries, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue
                
                countriesSet.add(newItem)

            showSetData(countriesSet, 'Countries (set*)')

        except Exception as e:
            log('UTILS :: Error getting Countries: %s', e)

        finally:
            siteInfoDict['Countries'] = countriesSet

        #   6.  Release Date
        log(LOG_SUBLINE)
        kwReleaseDate = kwargs.get('kwReleaseDate')
        log('UTILS :: {0:<29} {1}'.format('KW Release Date', kwReleaseDate))
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmldate = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Date"]/following-sibling::span/text()')[0].strip()
                htmldate = datetime.strptime(htmldate, '%-m/%-d/%Y')
                siteInfoDict['ReleaseDate'] = htmldate
                log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration 
        kwDuration = kwargs.get('kwDuration')
        log('UTILS :: {0:<29} {1}'.format('KW Duration', kwDuration))
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlduration = fhtml.xpath('//dt[text()="Run Time:"]/following-sibling::dd[1]/text()[normalize-space()]')[0].strip()
                htmlduration = re.sub('[^0-9]', '', htmlduration).strip()                      # strip away alphabetic characters leaving mins
                duration = int(duration) * 60                                                  # convert to seconds
                duration = datetime.fromtimestamp(duration)
                siteInfoDict['Duration'] = duration
                log('UTILS :: {0:<29} {1}'.format('Duration', duration.strftime('%H:%M:%S')))

            except Exception as e:
                siteInfoDict['Duration'] = FILMDICT['Duration']
                log('UTILS :: Error getting Site Film Duration: Reset to File Name Duration %s', e)
        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//img[@class="gallery-image"]/@src')
            poster = htmlimages[0]
            art = htmlimages[1]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoIAFD(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'IAFD'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            synopsis = html.xpath('//div[@id="synopsis"]/div/ul/li//text()')[0]         # will error if no synopsis
            htmlsynopsis = html.xpath('//div[@id="synopsis"]/div/ul/li//text()')
            for idx, synopsis in enumerate(htmlsynopsis):
                log('UTILS :: {0:<29} {1}'.format('Synopsis' if idx == 0 else '', synopsis))
            
            synopsis = '\n'.join(htmlsynopsis)
            siteInfoDict['Synopsis'] = synopsis
            FILMDICT['Synopsis'] = synopsis

        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            FILMDICT['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            directors = getRecordedDirectors(html)
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), sorted(directors))))
            siteInfoDict['Directors'] = directors
            FILMDICT['Directors'] = directors                         # this field holds the directos if the film is found on iafd

        except Exception as e:
            siteInfoDict['Directors'] = {}
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            cast  = getRecordedCast(html)
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), sorted(cast))))
            siteInfoDict['Cast'] = cast
            FILMDICT['Cast'] = cast                                  # this field holds the cast if the film is found on iafd

        except Exception as e:
            siteInfoDict['Cast'] = {}
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        log('UTILS :: No Genres, Countries or Compilation Info on Agent - Try to Extract Information from key words in synopsis/cast roles')
        genresSet = set()
        countriesSet = set()
        try:
            if siteInfoDict['Synopsis']:
                synopsis = re.sub(r'[^\w\s]',' ', siteInfoDict['Synopsis'])             # remove all punctuationion
                synopsis = re.sub(r'\b\w{1,3}\b', '', synopsis)                         # remove all short words (3 letters or less) - to avoid processing letters like you, us, him
                setSynopsis = set(synopsis.split())
                log('UTILS :: {0:<29} {1}'.format('Synopsis Word Count', '{0:>3} - {1}'.format(len(setSynopsis), setSynopsis)))
                for idx, item in enumerate(setSynopsis, start=1):
                    newItem = findTidy(item)
                    if not newItem or newItem is None:        # Don't process
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>3} - {1:<25} :: {2}'.format(idx, item, newItem)))
                    if newItem in COUNTRYSET:
                        countriesSet.add(newItem)
                    else:
                        genresSet.add(newItem)
            else:
                log('UTILS :: No Synopsis Recorded: %s', e)

            #   IAFD lists the sexual activities of the cast memebrs under their pictures at times
            if siteInfoDict['Cast']:
                roles = ' '.join({cast[x]['Role'] for x in siteInfoDict['Cast'].keys()})            # add all roles to string
                rolesSet = set(roles.split())                                                       # split into words and remove duplicates
                log('UTILS :: {0:<29} {1}'.format('Roles Word Count', '{0:>2} - {1}'.format(len(rolesSet), rolesSet)))
                for idx, item in enumerate(rolesSet, start=1):
                    newItem = findTidy(item)
                    if not newItem or newItem is None:        # Don't process
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))
                    genresSet.add(newItem)
            else:
                log('UTILS :: No Cast Recorded: %s', e)

                showSetData(countriesSet, 'Countries (set*)')
                showSetData(genresSet, 'Genres (set*)')

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet

        #   5b.  Compilation
        kwCompilation = kwargs.get('kwCompilation')
        if kwCompilation is None:
            log(LOG_SUBLINE)
            try:
                # if already set to yes by possible checking of external sources [AEBN, GayDVDMovies, GayHotMovies], dont change with IAFD value
                htmlcompilation = html.xpath('//p[@class="bioheading" and text()="Compilation"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: {0:<29} {1}'.format('Compilation?', htmlcompilation))
            except Exception as e:
                siteInfoDict['Compilation'] = 'No'
                log('UTILS :: Error getting Compilation Information: %s', e)
        else:
            siteInfoDict['Compilation'] = kwCompilation

        #   6.  Release Date - GEVI Formats - 1. YYYY, 2. YYYY-YY, 3. YYYY,YYYY 4. cYYYY 5. ? 6. Null
        #                      The Date(s) can be different as they are released by different Distributors - compare against File Name Year
        kwReleaseDate = kwargs.get('kwReleaseDate')
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            productionDates = set()
            # Add default date 31st December of Title Year
            if 'CompareDate' in FILMDICT and FILMDICT['CompareDate']:
                productionDates.add(FILMDICT['CompareDate'])

            try:
                htmlreleasedate = html.xpath('//p[@class="bioheading" and text()="Release Date"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: {0:<29} {1}'.format('Site URL Release Date', htmlreleasedate))
                productionDates.add(datetime.strptime(htmlreleasedate, '%b %d, %Y'))
            except: 
                htmlreleasedate = ''
                pass

            try:
                htmladdeddate = html.xpath('//p[@class="bioheading" and text()="Date Added to IAFD"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: {0:<29} {1}'.format('Site URL Added to IAFD Date', htmladdeddate))
                productionDates.add(datetime.strptime(htmladdeddate, '%b %d, %Y'))
            except: 
                htmladdeddate = ''
                pass

            if len(productionDates):
                siteInfoDict['ReleaseDate'] = min(productionDates)
            else:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration - IAFD Format = MMM
        kwDuration = kwargs.get('kwDuration')
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlduration = html.xpath('//p[@class="bioheading" and text()="Minutes"]//following-sibling::p[1]/text()')[0].strip()
                duration = datetime.fromtimestamp(int(htmlduration) * 60)
                siteInfoDict['Duration'] = duration

            except Exception as e:
                siteInfoDict['Duration'] = datetime.fromtimestamp(0)
                log('UTILS :: Error getting Site Film Duration: %s', e)
        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        log('UTILS :: No Posters/Background Art Info on Agent - Set to Null')
        siteInfoDict['Poster'] = ''
        siteInfoDict['Art'] = ''

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Chapter Info on Agent - Set to Null')
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        siteInfoDict['Chapters'] = {}
        scenesDict = {}
        try:
            scene = html.xpath('//div[@id="sceneinfo"]/ul/li//text()')[0] # will error if no scene breakdown
            htmlscenes = html.xpath('//div[@id="sceneinfo"]/ul/li//text()[normalize-space()]')
            log('UTILS :: {0:<29} {1}'.format('Possible Number of Scenes', len(htmlscenes)))
            for sceneNo, scene in enumerate(htmlscenes, start=1):
                # scene No
                log('UTILS :: {0:<29} {1}'.format('Scene', sceneNo))

                # Review Source - composed of cast list or iafd scenes cast or Film title in that order of preference
                reviewSource =  '{0}. {1}...'.format(sceneNo, FILMDICT['Title'])

                # Review Author - composed of Settings
                reviewAuthor = mySource

                reviewText = scene
                # prep for review metadata
                if len(reviewText) > 275:
                    for i in range(275, -1, -1):
                        if reviewText[i] in ['.', '!', '?']:
                            reviewText = reviewText[0:i + 1]
                            break

                log('UTILS :: {0:<29} {1}'.format('Review Text', reviewText if reviewText else 'None Recorded'))

                # save Review - scene
                scenesDict[sceneNo] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText, 'Link': filmURL}

        except Exception as e:
            log('UTILS :: Error getting Scenes: %s', e)

        finally:
            siteInfoDict['Scenes'] = scenesDict

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoQueerClick(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'QueerClick'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//article[@id and @class]/p')
            synopsis = [x.text_content() for x in htmlsynopsis]
            synopsis = '\n'.join(synopsis)

            pattern = re.compile(r'See more.*', re.IGNORECASE)
            synopsis = re.sub(pattern, '', synopsis)

            siteInfoDict['Synopsis'] = synopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', synopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        log('UTILS :: No Director Info on Agent - Set to Null')
        siteInfoDict['Directors'] = []

        #   3.  Cast
        log(LOG_SUBLINE)
        log('UTILS :: No Cast List on Agent: Built From Tag List')
        siteInfoDict['Cast'] = []

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Tag List: Genres, Cast and possible Countries, Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        countriesSet = set()
        castSet = set()
        compilation = 'No'
        testStudio = FILMDICT['Studio'].lower().replace(' ', '')
        testCast = [x.strip().replace(' ', '') for x in FILMDICT['FilenameCast']]
        try:
            htmltags = html.xpath('//div[@class="taxonomy"]/a/@title|//article[@id and @class]/p/a/text()[normalize-space()]')
            htmltags = [x.strip() for x in htmltags if x.strip()]
            htmltags = [x for x in htmltags if not '.tv' in x.lower()]
            htmltags = [x for x in htmltags if not '.com' in x.lower()]
            htmltags = [x for x in htmltags if not '.net' in x.lower()]
            htmltags = [x.replace(u'\u2019s', '') for x in htmltags]

            # remove all tags with non name characters such as colons
            htmltags = [x.replace("’", "'") for x in htmltags]                             # standardise apostrophes
            htmltags = [x for x in htmltags if not ':' in x]
            htmltags = [x for x in htmltags if not x + ':' in FILMDICT['Title']]
            htmltags = list(set(htmltags))
            htmltags.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Tags', '{0:>2} - {1}'.format(len(htmltags), htmltags)))
            compilation = 'Yes' if 'Compilation' in htmltags else 'No'
            for idx, item in enumerate(htmltags, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:                                                       # Don't process
                    continue

                tempItem = item.lower().replace(' ', '')
                if tempItem in testStudio or 'Movie' in item or 'Series' in item:         # skip if tag is studio
                    continue

                if testCast and tempItem in testCast:                                     # Check in filename cast list
                    continue

                if newItem in COUNTRYSET:                                                 # check if country
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem) if newItem else castSet.add(item)

            # also use synopsis to populate genres/countries as sometimes Scenes are not tagged with genres
            if siteInfoDict['Synopsis']:
                synopsis = re.sub(r'[^\w\s]',' ', siteInfoDict['Synopsis'])             # remove all punctuationion
                synopsis = re.sub(r'\b\w{1,3}\b', '', synopsis)                         # remove all short words (3 letters or less) - to avoid processing letters like you, us, him
                setSynopsis = set(synopsis.split())
                log('UTILS :: {0:<29} {1}'.format('Synopsis Word Count', '{0:>3} - {1}'.format(len(setSynopsis), setSynopsis)))
                for idx, item in enumerate(setSynopsis, start=1):
                    newItem = findTidy(item)
                    if not newItem or newItem is None:        # Don't process
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>3} - {1:<25} :: {2}'.format(idx, item, newItem)))
                    if newItem in COUNTRYSET:
                        countriesSet.add(newItem)
                    else:
                        genresSet.add(newItem)

            showSetData(castSet, 'Cast (set*)')
            showSetData(genresSet, 'Genres (set*)')
            showSetData(countriesSet, 'Countries (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Tags: Genres/Countries/Cast: %s', e)

        finally:
            for x in castSet:
                siteInfoDict['Cast'].append(x)

            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   6.  Release Date: Format dd mm YY
        log(LOG_SUBLINE)
        kwReleaseDate = kwargs.get('kwReleaseDate')
        log('UTILS :: {0:<29} {1}'.format('KW Release Date', kwReleaseDate))
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmldate = html.xpath('//div[@class="postdetails"]/span[@class="date updated"]/text()[normalize-space()]')[0]
                htmldate = datetime.strptime(htmldate, '%d %b %y')
                siteInfoDict['ReleaseDate'] = htmldate
                log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration - No Duration on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Duration Info on Agent - Set to File Duration')
        siteInfoDict['Duration'] = FILMDICT['Duration']
        log('UTILS :: {0:<29} {1}'.format('Duration', siteInfoDict['Duration'].strftime('%H:%M:%S')))

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        FILMDICT['SceneAgent'] = True                 # notify update routine to crop images
        try:
            htmlimages = html.xpath('.//a[@class="aimg"]/img/@data-lazy-src|.//p/img/@data-lazy-src')
            poster = htmlimages[0]
            art = htmlimages[1]

            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoSimplyAdult(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'SimplyAdult'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//div[@class="product_description"]/text()')[0].strip()
            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', htmlsynopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//div[@class="property-name"][text()="Director"]/following-sibling::div[@class="property-value"]/a/text()')
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//div[@class="property-name"][text()="Cast:"]/following-sibling::div[@class="property-value"]/a/text()')
            htmlcast = [x.strip() for x in htmlcast if x.strip() and 'n/a' not in x.lower()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections
        log(LOG_SUBLINE)
        try:
            htmlcollections = html.xpath('//div[@class="property-name"][text()="Series"]/following-sibling::div[@class="property-value"]/a/text()[normalize-space()]')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            collections = list(set(htmlcollections))
            collections.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        log('UTILS :: No Genres, Countries or Compilation Info on Agent - Try to Extract Information from key words in synopsis')
        genresSet = set()
        countriesSet = set()
        try:
            if siteInfoDict['Synopsis']:
                synopsis = re.sub(r'[^\w\s]',' ', siteInfoDict['Synopsis'])             # remove all punctuationion
                synopsis = re.sub(r'\b\w{1,3}\b', '', synopsis)                         # remove all short words (3 letters or less) - to avoid processing letters like you, us, him
                setSynopsis = set(synopsis.split())
                log('UTILS :: {0:<29} {1}'.format('Synopsis Word Count', '{0:>3} - {1}'.format(len(setSynopsis), setSynopsis)))
                for idx, item in enumerate(setSynopsis, start=1):
                    newItem = findTidy(item)
                    if not newItem or newItem is None:        # Don't process
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>3} - {1:<25} :: {2}'.format(idx, item, newItem)))
                    if newItem in COUNTRYSET:
                        countriesSet.add(newItem)
                    else:
                        genresSet.add(newItem)

                showSetData(countriesSet, 'Countries (set*)')
                showSetData(genresSet, 'Genres (set*)')
            else:
                log('UTILS :: No Synopsis Recorded: %s', e)

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        siteInfoDict['Genres'] = genresSet
        siteInfoDict['Countries'] = countriesSet
        siteInfoDict['Compilation'] = 'No'

        #   6.  Release Date - No Release Date on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Release Date Info on Agent - Set to File Name Year Dec 31st')
        if FILMDICT['Year']:
            productionDate = '{0}1231'.format(FILMDICT['Year'])
            productionDate = datetime.strptime(productionDate, '%Y%m%d')
        else:
            productionDate = datetime.fromtimestamp(0)

        siteInfoDict['ReleaseDate'] = productionDate
        log('UTILS :: {0:<29} {1}'.format('Production Date', productionDate.strftime('%Y-%m-%d')))

        #   7.  Duration - No Duration on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Duration Info on Agent - Set to File Duration')
        siteInfoDict['Duration'] = FILMDICT['Duration']
        log('UTILS :: {0:<29} {1}'.format('Duration', siteInfoDict['Duration'].strftime('%H:%M:%S')))

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//img[@id="product_thumbnail"]/@src')
            for i, htmlimage in enumerate(htmlimages):
                htmlimages[i] = htmlimage if 'https:' in htmlimage else 'https:' + htmlimage

            if len(htmlimages) == 1:    # if only one image duplicate it
                htmlimages.append(htmlimages[0])

            poster = htmlimages[0]
            art = htmlimages[1]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        try:
            htmlrating = html.xpath('//a[contains(@title, "out of 5 stars")]/@title')[0]
            rating = htmlrating.split()[0]
            rating = float(rating) * 2.0
            siteInfoDict['Rating'] = rating
        except Exception as e:
            log('UTILS :: Error getting Rating: %s', e)
            siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoWayBig(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'WayBig'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//div[@class="entry-content"]/p[not(descendant::script) and not(contains(., "Watch as"))]')
            synopsis = [x.text_content() for x in htmlsynopsis]
            synopsis = '\n'.join(synopsis)

            pattern = re.compile(r'Watch.*at.*', re.IGNORECASE)
            synopsis = re.sub(pattern, '', synopsis)

            siteInfoDict['Synopsis'] = synopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', synopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        log('UTILS :: No Director Info on Agent - Set to Null')
        siteInfoDict['Directors'] = []

        #   3.  Cast
        log(LOG_SUBLINE)
        log('UTILS :: No Cast List on Agent: Built From Tag List')
        siteInfoDict['Cast'] = []

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Tag List: Genres, Cast and possible Countries, Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        countriesSet = set()
        castSet = set()
        compilation = 'No'
        testStudio = FILMDICT['Studio'].lower().replace(' ', '')
        testCast = [x.strip().replace(' ', '') for x in FILMDICT['FilenameCast']]
        try:
            htmltags = html.xpath('//a[contains(@href,"https://www.waybig.com/blog/tag/")]/text()')
            htmltags = [x.strip() for x in htmltags if x.strip()]
            htmltags = [x for x in htmltags if not '.tv' in x.lower()]
            htmltags = [x for x in htmltags if not '.com' in x.lower()]
            htmltags = [x for x in htmltags if not '.net' in x.lower()]

            # remove all tags with non name characters such as colons
            htmltags = [x.replace(u'\u2019s', '') for x in htmltags]
            htmltags = [x for x in htmltags if not ':' in x]
            htmltags = [x for x in htmltags if not x + ':' in FILMDICT['Title']]
            htmltags = list(set(htmltags))
            htmltags.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Tags', '{0:>2} - {1}'.format(len(htmltags), htmltags)))
            compilation = 'Yes' if 'Compilation' in htmltags else 'No'
            for idx, item in enumerate(htmltags, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:                                                       # Don't process
                    continue

                tempItem = item.lower().replace(' ', '')
                if tempItem in testStudio or 'Movie' in item or 'Series' in item:         # skip if tag is studio
                    continue

                if testCast and tempItem in testCast:                                     # Check in filename cast list
                    continue

                if newItem in COUNTRYSET:                                                 # check if country
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem) if newItem else castSet.add(item)

            # also use synopsis to populate genres/countries as sometimes Scenes are not tagged with genres
            if siteInfoDict['Synopsis']:
                synopsis = re.sub(r'[^\w\s]',' ', siteInfoDict['Synopsis'])             # remove all punctuationion
                synopsis = re.sub(r'\b\w{1,3}\b', '', synopsis)                         # remove all short words (3 letters or less) - to avoid processing letters like you, us, him
                setSynopsis = set(synopsis.split())
                log('UTILS :: {0:<29} {1}'.format('Synopsis Word Count', '{0:>3} - {1}'.format(len(setSynopsis), setSynopsis)))
                for idx, item in enumerate(setSynopsis, start=1):
                    newItem = findTidy(item)
                    if not newItem or newItem is None:        # Don't process
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>3} - {1:<25} :: {2}'.format(idx, item, newItem)))
                    if newItem in COUNTRYSET:
                        countriesSet.add(newItem)
                    else:
                        genresSet.add(newItem)

            showSetData(castSet, 'Cast (set*)')
            showSetData(genresSet, 'Genres (set*)')
            showSetData(countriesSet, 'Countries (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Tags: Genres/Countries/Cast: %s', e)

        finally:
            for x in castSet:
                siteInfoDict['Cast'].append(x)

            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   6.  Release Date
        log(LOG_SUBLINE)
        kwReleaseDate = kwargs.get('kwReleaseDate')
        log('UTILS :: {0:<29} {1}'.format('KW Release Date', kwReleaseDate))
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmldate = html.xpath('//div/span[@class="meta-date"]/strong/text()[normalize-space()]')[0]
                htmldate = datetime.strptime(htmldate, '%B %d, %Y')
                siteInfoDict['ReleaseDate'] = htmldate
                log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration - No Duration on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Duration Info on Agent - Set to File Duration')
        siteInfoDict['Duration'] = FILMDICT['Duration']
        log('UTILS :: {0:<29} {1}'.format('Duration', siteInfoDict['Duration'].strftime('%H:%M:%S')))

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        FILMDICT['SceneAgent'] = True                 # notify update routine to crop images
        try:
            htmlimages = html.xpath('//a[@target="_self" or @target="_blank"]/img[(@height or @width) and @alt and contains(@src, "zing.waybig.com/reviews")]/@src')
            if len(htmlimages) == 1:
                htmlimages.append(htmlimages[0])

            poster = htmlimages[0]
            art = htmlimages[1]

            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        log('UTILS :: No Scene Info on Agent - Set to Null')
        siteInfoDict['Scenes'] = {}
        siteInfoDict['Chapters'] = {}

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoWolffVideo(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'WolffVideo'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//div[@class="col-7"]/p/text()')[0]
            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('Synopsis', htmlsynopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//a[@href[contains(.,"/director")]]/text()')
            htmldirectors = [x.strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//a[@href[contains(.,"/actor")]]/text()')
            htmlcast = [x.strip() for x in htmlcast if x.strip() and 'n/a' not in x.lower()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections
        log(LOG_SUBLINE)
        try:
            htmlcollections = html.xpath('//div[@class="property-name"][text()="Series"]/following-sibling::div[@class="property-value"]/a/text()[normalize-space()]')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            collections = list(set(htmlcollections))
            collections.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        genresSet = set()
        countriesSet = set()
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//p/a[@href[contains(.,"display-movies/category")]]/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                newItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem in COUNTRYSET:
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem if newItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   6.  Release Date
        log(LOG_SUBLINE)
        kwReleaseDate = kwargs.get('kwReleaseDate')
        log('UTILS :: {0:<29} {1}'.format('KW Release Date', kwReleaseDate))
        if kwReleaseDate is None:
            log(LOG_SUBLINE)
            try:
                htmldate = html.xpath('//*[text()="MOVIE RELEASE DATE:"]/following-sibling::text()')[0].strip()
                htmldate = datetime.strptime(htmldate, '%m/%d/%Y')
                siteInfoDict['ReleaseDate'] = htmldate
                log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

            except Exception as e:
                siteInfoDict['ReleaseDate'] = None
                log('UTILS :: Error getting Release Date: %s', e)
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration - No Duration on Agent Site
        log(LOG_SUBLINE)
        log('UTILS :: No Duration Info on Agent - Set to File Duration')
        siteInfoDict['Duration'] = FILMDICT['Duration']
        log('UTILS :: {0:<29} {1}'.format('Duration', siteInfoDict['Duration'].strftime('%H:%M:%S')))

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimage = html.xpath('//a[@id="view_cover"]/@href')[0]
            htmlimage = ('' if BASE_URL in htmlimage else BASE_URL) + htmlimage

            poster = htmlimage
            art = htmlimage
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = ''
            art = ''
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info - Wolff Video retains actually reviews - so collect these rather than setting up scenes and chapters
        log(LOG_SUBLINE)
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        scenesDict = {}
        chaptersDict = {}               # always null in Wolff Video
        try:
            htmlscenes = html.xpath('//table[@class="scene_holder"]')
            log('UTILS :: {0:<29} {1}'.format('Possible Number of Scenes', len(htmlscenes)))
            if len(htmlscenes) == 0:
                raise Exception ('< No Scenes Found! >')

            log(LOG_SUBLINE)
            for sceneNo, htmlscene in enumerate(htmlscenes, start=1):
                try:
                    # scene No
                    log('UTILS :: {0:<29} {1}'.format('Scene', sceneNo))

                    # Review Source - composed of cast list or iafd scenes cast or Film title in that order of preference
                    reviewSource = ''
                    try:
                        reviewSource = htmlscene.xpath('//td[@class="scene_description"]//text()')
                        reviewSource = ''.join(reviewSource).strip()

                    except Exception as e:
                        log('UTILS :: Error getting Review Source: %s', e)

                    finally:
                        # prep for review metadata
                        if len(reviewSource) > 40:
                            for i in range(40, -1, -1):
                                if reviewSource[i] == ' ':
                                    reviewSource = reviewSource[0:i]
                                    break
                        if reviewSource:
                            reviewSource = '{0}. {1}...'.format(sceneNo, reviewSource)
                        else:
                            mySource = 'N/A'
                            reviewSource = '{0}. {1}...'.format(sceneNo, FILMDICT['Title'])
                            log('UTILS :: Warning No Review Source (Used Film Title)')

                        log('UTILS :: {0:<29} {1}'.format('Review Source', '{0} - {1}'.format(mySource, reviewSource) if reviewSource else 'None Recorded'))

                    # Review Author - composed of Settings
                    reviewAuthor = mySource
                    log('UTILS :: {0:<29} {1}'.format('Review Author', reviewAuthor if reviewAuthor else 'None Recorded'))

                    # Review Text - composed of Sexual Acts / tidy genres
                    reviewText = ''
                    try:
                        reviewText = htmlscene.xpath('//td[@class="scene_description"]//text()')
                        reviewText = ''.join(reviewText).strip()
                        log('UTILS :: Review Text: %s', reviewText)
                    except Exception as e:
                        log('UTILS :: Error getting Review Text: %s', e)

                    finally:
                        # prep for review metadata
                        if len(reviewText) > 275:
                            for i in range(275, -1, -1):
                                if reviewText[i] in ['.', '!', '?']:
                                    reviewText = reviewText[0:i + 1]
                                    break
                        log('UTILS :: {0:<29} {1}'.format('Review Text', reviewText if reviewText else 'None Recorded'))

                    # save Review - scene
                    scenesDict[sceneNo] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText, 'Link': filmURL}

                except Exception as e:
                    log('UTILS :: Error getting Scene No. %s: %s', sceneNo, e)

        except Exception as e:
            log('UTILS :: Error getting Scenes: %s', e)

        finally:
            siteInfoDict['Scenes'] = scenesDict
            siteInfoDict['Chapters'] = chaptersDict

        #   10.  Rating
        log(LOG_SUBLINE)
        try:
            htmlrating = html.xpath('//a[contains(@title, "out of 5 stars")]/@title')[0]
            rating = htmlrating.split()[0]
            rating = float(rating) * 2.0
            siteInfoDict['Rating'] = rating
        except Exception as e:
            log('UTILS :: Error getting Rating: %s', e)
            siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getURLElement(myString, FilterYear = '', UseAdditionalResults = False):
    ''' check IAFD web site for better quality thumbnails irrespective of whether we have a thumbnail or not '''
    msg = ''    # this variable will be set if IAFD fails to be read
    html = ''
    try:
        if FilterYear:
            myString = '{0}{1}'.format(myString, IAFD_FILTER.format(FilterYear - 3, FilterYear + 1))

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
        msg = '< Failed to read IAFD URL: {0} - Processing Abandoned! >'.format(e)

    if not html:
        raise Exception(msg)

    return html

# ----------------------------------------------------------------------------------------------------------------------------------
def jsonDumper(obj):
    ''' DateTime and Set Objects can not be converted to json format'''
    if isinstance(obj, datetime):
        return obj.__str__()
    if isinstance(obj, set):
        obj = list(obj)
        obj.insert(0, '*SET*')
        return obj

# ----------------------------------------------------------------------------------------------------------------------------------
def jsonLoader(dict):
    ''' DateTime and Set Objects need to be reconstituted from string and list objects respectively from json format'''
    for (key, value) in dict.items():
        try:
            dict[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            log('UTILS :: {0:<29} {1}'.format(key, dict[key]))
            continue
        except:
            pass
        try:
            if '*SET*' in value:
                value = value[1:]
                dict[key] = set(value)
                log('UTILS :: {0:<29} {1}'.format(key, dict[key]))
        except:
            pass

    return dict

# ----------------------------------------------------------------------------------------------------------------------------------
def log(message, *args):
    ''' log messages '''
    if re.search('ERROR', message, re.IGNORECASE):
        Log.Error(AGENT + ' - ' + message, *args)
    elif re.search('WARNING', message, re.IGNORECASE):
        Log.Warn(AGENT + ' - ' + message, *args)
    else:
        Log.Info(AGENT + '  - ' + message, *args)

# ----------------------------------------------------------------------------------------------------------------------------------
def logHeader(myFunc, media, lang):
    ''' log header for search and update functions '''
    log(LOG_BIGLINE)
    log('%s:: Version:                      v.%s', myFunc, VERSION_NO)
    log('%s:: Python:                       %s %s', myFunc, platform.python_version(), platform.python_build())
    log('%s:: Platform:                     %s - %s %s', myFunc, platform.machine(), platform.system(), platform.release())
    log('%s:: Preferences:', myFunc)
    log('%s::  > Legend Before Summary:     %s', myFunc, PREFIXLEGEND)
    log('%s::  > Reset Metadata:            %s', myFunc, RESETMETA)
    log('%s::  > Collection Gathering', myFunc)
    log('%s::      > Cast:                  %s', myFunc, COLCAST)
    log('%s::      > Director(s):           %s', myFunc, COLDIRECTOR)
    log('%s::      > Studio:                %s', myFunc, COLSTUDIO)
    log('%s::      > Film Title:            %s', myFunc, COLSERIES)
    log('%s::      > Genres:                %s', myFunc, COLGENRE)
    log('%s::  > Match IAFD Duration:       %s', myFunc, MATCHIAFDDURATION)
    log('%s::  > Match Site Duration:       %s', myFunc, MATCHSITEDURATION)
    log('%s::  > Duration Dx                ±%s Minutes', myFunc, DURATIONDX)
    log('%s::  > Language Detection:        %s', myFunc, DETECT)
    log('%s::  > Library:Site Language:     (%s:%s)', myFunc, lang, SITE_LANGUAGE)
    log('%s::  > Network Request Delay:     %s Seconds', myFunc, DELAY)
    log('%s:: Media Title:                  %s', myFunc, media.title)
    log('%s:: File Path:                    %s', myFunc, media.items[0].parts[0].file)
    log(LOG_BIGLINE)

# -------------------------------------------------------------------------------------------------------------------------------
def logFooter(myFunc, FILMDICT):
    ''' log footer for search and update functions '''
    log(LOG_ASTLINE)
    for footer in [' << {0}: Finished {1} Routine >> '.format(FILMDICT['Agent'], myFunc.title()), 
                   ' << ({0}) - {1} ({2}) >> '.format(FILMDICT['Studio'], FILMDICT['Title'], FILMDICT['Year']),
                   ' << {0} >> '.format('Sucessful!!' if FILMDICT['Status'] else 'Failed')]:
        log('%s:: %s', myFunc, footer.center(140, '*'))
    log(LOG_ASTLINE)

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
def matchCast(unmatchedCastList, FILMDICT):
    ''' check IAFD web site for individual cast'''
    matchedCastDict = {}

    myYear = int(FILMDICT['Year'])

    for idx, unmatchedCast in enumerate(unmatchedCastList, start=1):
        compareUnmatchedCast = re.sub(r'[\W\d_]', '', unmatchedCast).strip().lower()
        log('UTILS :: {0:<29} {1}'.format('Unmatched Cast Name', '{0:>2} - {1}/{2}'.format(idx, unmatchedCast, compareUnmatchedCast)))

        # compare against IAFD Cast List - retrieved from the film's url page
        matchedName = False
        for key, value in FILMDICT['Cast'].items():
            IAFDName = makeASCII(key)
            IAFDAlias = makeASCII(value['Alias'])
            IAFDCompareName = makeASCII(value['CompareName'])
            IAFDCompareAlias = makeASCII(value['CompareAlias'])

            # 1st full match against Cast Name
            matchedName = False
            if compareUnmatchedCast == IAFDCompareName:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Cast: Full Match - Cast Name', unmatchedCast))
                matchedName = True
                break

            # 2nd full match against Cast Alias
            if compareUnmatchedCast == IAFDCompareAlias:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Cast: Full Match - Cast Alias', unmatchedCast))
                matchedName = True
                break

            # 3rd partial match against Cast Name
            if compareUnmatchedCast in IAFDCompareName:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Cast: Partial Match - Cast Name', unmatchedCast))
                matchedName = True
                break

            # 4th partial match against Cast Alias
            if compareUnmatchedCast in IAFDCompareAlias:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Cast: Partial Match - Cast Alias', unmatchedCast))
                matchedName = True
                break

            # Lehvensten and Soundex Matching
            levDistance = len(unmatchedCast.split()) + 1 if len(unmatchedCast.split()) > 1 else 1 # Set Lehvenstein Distance - one change/word+1 of cast names or set to 1
            testName = IAFDName if levDistance > 1 else IAFDName.split()[0] if IAFDName else ''
            testAlias = IAFDAlias if levDistance > 1 else IAFDAlias.split()[0] if IAFDAlias else ''
            testNameType = 'Full Names' if levDistance > 1 else 'Forename'

            # 5th Lehvenstein Match against Cast Name
            levScore = String.LevenshteinDistance(unmatchedCast, testName)
            matchedName = levScore <= levDistance
            if matchedName:
                log('UTILS :: {0:<29} {1}'.format('Levenshtein Match', testNameType))
                log('UTILS :: {0:<29} {1}'.format('  IAFD Cast Name', testName))
                log('UTILS :: {0:<29} {1}'.format('  Agent Cast Name', unmatchedCast))
                log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(levScore, levDistance)))
                log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                break

            # 6th Lehvenstein Match against Cast Alias
            if testAlias:
                levScore = String.LevenshteinDistance(unmatchedCast, testAlias)
                matchedName = levScore <= levDistance
                if matchedName:
                    log('UTILS :: {0:<29} {1}'.format('Levenshtein Match', testNameType))
                    log('UTILS :: {0:<29} {1}'.format('  IAFD Cast Alias', testAlias))
                    log('UTILS :: {0:<29} {1}'.format('  Agent Cast Name', unmatchedCast))
                    log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(levScore, levDistance)))
                    log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                    break

            # 7th Soundex Matching on Cast Name
            soundIAFD = soundex(testName)
            soundAgent = soundex(unmatchedCast)
            matchedName = soundIAFD == soundAgent
            if matchedName:
                log('UTILS :: {0:<29} {1}'.format('SoundEx Match', testNameType))
                log('UTILS :: {0:<29} {1}'.format('  IAFD Cast Name', testName))
                log('UTILS :: {0:<29} {1}'.format('  Agent Cast Name', unmatchedCast))
                log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(soundIAFD, soundAgent)))
                log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                break

            # 8th Soundex Matching on Cast Alias
            if testAlias:
                soundIAFD = soundex(testAlias)
                soundAgent = soundex(unmatchedCast)
                matchedName = soundIAFD == soundAgent
                if matchedName:
                    log('UTILS :: {0:<29} {1}'.format('SoundEx Match', testNameType))
                    log('UTILS :: {0:<29} {1}'.format('  IAFD Cast Alias', testAlias))
                    log('UTILS :: {0:<29} {1}'.format('  Agent Cast Name', unmatchedCast))
                    log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(soundIAFD, soundAgent)))
                    log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                    break

        if matchedName: # we have a match, on to the next cast
            continue

        # the cast on the website has not matched to those listed against the film in IAFD. So search for the cast's entry on IAFD
        matchedCastDict[unmatchedCast] = {'Photo': '', 'Role': IAFD_ABSENT, 'Alias': '', 'CompareName': '', 'CompareAlias': ''} # initialise cast member's dictionary
        xPathMale = '//table[@id="tblMal"]/tbody/tr'
        xPathGirl = '//table[@id="tblFem"]/tbody/tr'
        if 'AllMale' in FILMDICT and FILMDICT['AllMale'] == 'Yes':
            xPath = xPathMale
            xType = 'Gay'
        elif 'AllGirl' in FILMDICT and FILMDICT['AllGirl'] == 'Yes':
            xPath = xPathGirl
            xType = 'Lesbian'
        else:
            xPath = '{0}|{1}'.format(xPathMale, xPathGirl)
            xType = 'Straight'
        try:
            html = getURLElement(IAFD_SEARCH_URL.format(String.URLEncode(unmatchedCast)), FilterYear = myYear)
            castList = html.xpath(xPath)
            log('UTILS :: {0:<29} {1}'.format('{0} Cast xPath'.format(xType), xPath))

            castFound = len(castList)
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Cast Found'), '{0:>2} - {1}'.format(castFound, 'Skipping: > 25 Cast Names Returned' if castFound > 25 else 'Processing: <= 25 Cast Names Returned')))
            if castFound > 25:
                log(LOG_SUBLINE)
                continue            # next unmatchedCast

            log('UTILS :: {0:<29} {1}'.format('Cast Found', '{0:>2} - Matching Name: {1}'.format(castFound, unmatchedCast)))
            log(LOG_BIGLINE)
            for idx2, cast in enumerate(castList, start=1):
                # get cast details and compare to Agent cast
                try:
                    castName = cast.xpath('./td[2]/a/text()[normalize-space()]')[0]
                    compareCastName = re.sub(r'[\W\d_]', '', castName).strip().lower()
                    log('UTILS :: {0:<29} {1}'.format('Matching Cast Name', '{0:>2} - {1} / {2}'.format(idx2, castName, compareCastName)))
                except Exception as e:
                    log('UTILS :: Error: Could not read Cast Name: %s', e)
                    log(LOG_SUBLINE)
                    continue   # next cast 

                try:
                    castURL = IAFD_BASE + cast.xpath('./td[2]/a/@href')[0]
                    log('UTILS :: {0:<29} {1}'.format('Cast URL', castURL))
                except Exception as e:
                    log('UTILS :: Error: Could not read Cast URL: %s', e)
                    log(LOG_SUBLINE)
                    continue   # next cast 

                try:
                    castAliasList = cast.xpath('./td[3]/text()[normalize-space()]')[0].split(',')
                    castAliasList = [x.strip() for x in castAliasList if x]
                    compareCastAliasList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in castAliasList]
                    log('UTILS :: {0:<29} {1}'.format('Alias', castAliasList if castAliasList else 'No Cast Alias Recorded'))
                except:
                    castAliasList = []
                    compareCastAliasList = []

                if FILMDICT['FoundOnIAFD'] == 'Yes':                # look through FILMDICT['Cast']
                    previouslyMatched = False                       # check if the actor is in a move that has been found in IAFD
                    for key, value in FILMDICT['Cast'].items():
                        # Check if any of the Film's cast has an alias recorded against his name on the film page
                        checkName = key
                        if value['URL']:
                            checkURL = value['URL']
                            if castURL == checkURL:
                                previouslyMatched = True
                                log('UTILS :: {0:<29} {1}'.format('Note', '{0} URL in use: {1}'.format(checkName, checkURL)))
                                break
                        if value['CompareAlias']:
                            checkAlias = value['Alias']
                            checkCompareAlias = value['CompareAlias']
                            checkURL = value['URL']
                            if checkCompareAlias in compareCastAliasList:
                                previouslyMatched = True
                                log('UTILS :: {0:<29} {1}'.format('Note', '{0} AKA {1} also known by this name: {2}'.format(checkName, checkAlias, castName)))
                                break

                    if previouslyMatched:
                        matchedCastDict.pop(unmatchedCast, None)
                        log(LOG_SUBLINE)
                        continue

                # Check that cast member has acted in a gay film
                if FILMDICT['AllMale'] == 'Yes' or FILMDICT['AllGirl'] == 'Yes':
                    try:
                        chtml = getURLElement(castURL)
                        # if using a scene agent scraper include scenes.... Need to think this through!!!!!!
                    except Exception as e:
                        log('UTILS :: Error getting Cast Member Page, Cast Member: %s', e)

                    else:
                        xPath = '//table[@id="personal"]/tbody/tr[@class="ga" or @class="we"]' if FILMDICT['SceneAgent'] else '//table[@id="personal"]/tbody/tr[@class="ga"]'
                        gayFilmsList = chtml.xpath(xPath)
                        gayFilmsFound = len(gayFilmsList)
                        log('UTILS :: {0:<29} {1}'.format('Filmography', '{0:>2} - Gay/Bi Films'.format(gayFilmsFound)))
                        noCount = 0
                        for idx, gayFilm in enumerate(gayFilmsList, start=1):
                            gaySiteTitle = gayFilm.xpath('./td//text()')
                            gayNotes = gaySiteTitle[3].lower()
                            # log('UTILS :: {0:<29} {1}'.format('', '{0:>2}. {1:<35}\t - {2} - {3}'.format(idx, gaySiteTitle[0], gaySiteTitle[1], gaySiteTitle[3])))
                            if [x for x in ['mastonly', 'nonsex'] if (x in gayNotes)]:   # appeared in gay film in possible non gay role
                                noCount += 1

                        if noCount == gayFilmsFound:                        # all films in list were nonsex or masturbation only
                            log('UTILS :: {0:<29} {1}'.format('Skipped', 'Appeared in Zero Films or as Non Sex / Masturbation Roles Only'))
                            log(LOG_SUBLINE)
                            continue    # next cast in cast list

                try:
                    startCareer = int(cast.xpath('./td[4]/text()[normalize-space()]')[0]) - 1 # set start of career to 1 year before for pre-releases
                except:
                    startCareer = 0

                try:
                    endCareer = int(cast.xpath('./td[5]/text()[normalize-space()]')[0]) + 1   # set end of career to 1 year after to cater for late releases
                except:
                    endCareer = 0

                log('UTILS :: {0:<29} {1}'.format('Career', '{0} - {1}'.format(startCareer if startCareer > 0 else 'N/A', endCareer if endCareer > 0 else 'N/A')))

                matchedUsing = ''

                # match iafd row with Agent Cast entry
                matchedCast = True if compareUnmatchedCast == compareCastName else False
                if matchedCast:
                    matchedUsing = 'Name' 
                else:
                    log('UTILS :: {0:<29} {1}'.format('Failed Name Matching', '{0} != {1}'.format(compareUnmatchedCast, compareCastName)))

                # match iafd row with Agent Cast Alias entry
                if not matchedCast and castAliasList:
                    matchedItem = [x for x in compareCastAliasList if compareUnmatchedCast in x]
                    matchedCast = True if matchedItem else False
                    if matchedCast:
                        matchedUsing = 'Alias' 
                    else:
                        log('UTILS :: {0:<29} {1}'.format('Failed Alias List Matching', '{0} not in {1}'.format(compareUnmatchedCast, compareCastAliasList)))

                # Check Career - if we have a match - this can only be done if the film is not a compilation and we have a Year
                # only do this if we have more than one actor returned
                if castFound > 1 and matchedCast and FILMDICT['Compilation'] == "No" and myYear:
                    matchedCast = (startCareer <= myYear <= endCareer)
                    if matchedCast:
                        matchedUsing = 'Career' 
                    else:
                        log('UTILS :: {0:<29} {1}'.format('Failed Career Matching', '{0} <= {1} <= {2}'.format(startCareer, myYear, endCareer)))


                # we have a cast member who satisfies the conditions
                if matchedCast:
                    castPhoto = cast.xpath('./td[1]/a/img/@src')[0] # Cast Name on agent website - retrieve picture
                    castPhoto = '' if 'nophoto' in castPhoto or 'th_iafd_ad' in castPhoto else castPhoto.replace('thumbs/th_', '')
                    castRole = IAFD_FOUND  # default to found

                    log('UTILS :: {0:<29} {1}'.format('Cast URL', castURL))
                    log('UTILS :: {0:<29} {1}'.format('Cast Photo', castPhoto))
                    log('UTILS :: {0:<29} {1}'.format('Cast Role', castRole))
                    log('UTILS :: {0:<29} {1}'.format('Matched Using', matchedUsing))

                    # Assign found values to dictionary
                    myDict = {}
                    myDict['Photo'] = castPhoto
                    myDict['Role'] = '{0}:{1}'.format(castRole, matchedUsing)
                    myDict['Alias'] = ''
                    myDict['CompareName'] = compareCastName
                    myDict['CompareAlias'] = compareCastAliasList
                    matchedCastDict[unmatchedCast] = myDict

                    log(LOG_SUBLINE)
                    break   # matched - ignore any other entries

        except Exception as e:
            log('UTILS :: Error: Cannot Process IAFD Cast Search Results: %s', e)
            log(LOG_SUBLINE)

    return matchedCastDict
# ----------------------------------------------------------------------------------------------------------------------------------
def matchDirectors(unmatchedDirectorList, FILMDICT):
    ''' check IAFD web site for individual directors'''
    matchedDirectorDict = {}

    myYear = int(FILMDICT['Year'])
    for idx, unmatchedDirector in enumerate(unmatchedDirectorList, start=1):
        compareUnmatchedDirector = re.sub(r'[\W\d_]', '', unmatchedDirector).strip().lower()
        log('UTILS :: {0:<29} {1}'.format('Unmatched Director Name', '{0:>2} - {1}/{2}'.format(idx, unmatchedDirector, compareUnmatchedDirector)))
        log('UTILS :: {0:<29} {1}'.format('Unmatched Director Name', unmatchedDirector))

        # compare against IAFD Director List - retrieved from the film's url page
        matchedName = False
        for key, value in FILMDICT['Directors'].items():
            IAFDName = makeASCII(key)
            IAFDAlias = [makeASCII(x) for x in value['Alias']] if type(value['Alias']) is list else makeASCII(value['Alias'])
            IAFDCompareName = [makeASCII(x) for x in value['CompareName']] if type(value['CompareName']) is list else makeASCII(value['CompareName'])
            IAFDCompareAlias = [makeASCII(x) for x in value['CompareAlias']] if type(value['CompareAlias']) is list else makeASCII(value['CompareAlias'])

            # 1st full match against director name
            matchedName = False
            if compareUnmatchedDirector == IAFDCompareName:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Director: Full Match - Director Name', unmatchedDirector))
                matchedName = True
                break

            # 2nd full match against director alias
            if [x for x in IAFDCompareAlias if x == compareUnmatchedDirector]:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Director: Full Match - Director Alias', unmatchedDirector))
                matchedName = True
                break

            # 3rd partial match against director name
            if compareUnmatchedDirector in IAFDCompareName:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Director: Partial Match - Director Name', unmatchedDirector))
                matchedName = True
                break

            # 4th partial match against director alias
            if compareUnmatchedDirector in IAFDCompareAlias:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Director: Partial Match - Director Alias', unmatchedDirector))
                matchedName = True
                break

            # Lehvensten and Soundex Matching
            levDistance = len(unmatchedDirector.split()) + 1 if len(unmatchedDirector.split()) > 1 else 1 # Set Lehvenstein Distance - one change/word+1 of cast names or set to 1
            testNameType = 'Full Names' if levDistance > 1 else 'Forename'
            testName = IAFDName if levDistance > 1 else IAFDName.split()[0] if IAFDName else ''

            if isinstance(IAFDAlias, list):
                testAlias = [x if levDistance > 1 else x.split()[0] for x in IAFDAlias]
            else:
                testAlias = IAFDAlias if levDistance > 1 else IAFDAlias.split()[0] if IAFDAlias else ''

            # 5th Lehvenstein Match against Director Name
            levScore = String.LevenshteinDistance(unmatchedDirector, testName)
            matchedName = levScore <= levDistance
            if matchedName:
                log('UTILS :: {0:<29} {1}'.format('Levenshtein Match', testNameType))
                log('UTILS :: {0:<29} {1}'.format('  IAFD Director Name', testName))
                log('UTILS :: {0:<29} {1}'.format('  Agent Director Name', unmatchedDirector))
                log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(levScore, levDistance)))
                log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                break

            # 6th Lehvenstein Match against Director Alias
            if testAlias:
                levScore = [String.LevenshteinDistance(unmatchedDirector, x) for x in testAlias] if type(testAlias) is list else String.LevenshteinDistance(unmatchedDirector, testAlias)
                if type(levScore) is list:
                    for x in levScore:
                        matchedName = x <= levDistance
                        if matchedName:
                            break
                else:
                    matchedName = levScore <= levDistance

                if matchedName:
                    log('UTILS :: {0:<29} {1}'.format('Levenshtein Match', testNameType))
                    log('UTILS :: {0:<29} {1}'.format('  IAFD Director Alias', testAlias))
                    log('UTILS :: {0:<29} {1}'.format('  Agent Director Name', unmatchedDirector))
                    log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(levScore, levDistance)))
                    log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                    break

            # 7th Soundex Matching on Director Name
            soundIAFD = [soundex(x) for x in testName] if type(testName) is list else soundex(testName)
            soundAgent = soundex(unmatchedDirector)
            matchedName = True if soundAgent in soundIAFD else False
            if matchedName:
                log('UTILS :: {0:<29} {1}'.format('SoundEx Match', testNameType))
                log('UTILS :: {0:<29} {1}'.format('  IAFD Director Name', testName))
                log('UTILS :: {0:<29} {1}'.format('  Agent Director Name', unmatchedDirector))
                log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(soundIAFD, soundAgent)))
                log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                break

            # 8th Soundex Matching on Director Alias
            if testAlias:
                soundIAFD = [soundex(x) for x in testAlias] if type(testAlias) is list else soundex(testAlias)
                soundAgent = soundex(unmatchedDirector)
                matchedName = True if soundAgent in soundIAFD else False
                if matchedName:
                    log('UTILS :: {0:<29} {1}'.format('SoundEx Match', testNameType))
                    log('UTILS :: {0:<29} {1}'.format('  IAFD Director Alias', testAlias))
                    log('UTILS :: {0:<29} {1}'.format('  Agent Director Name', unmatchedDirector))
                    log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(soundIAFD, soundAgent)))
                    log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                    break

        if matchedName: # we have a match, on to the next director
            continue

        # the director on the website has not matched to those listed against the film in IAFD. So search for the director's entry on IAFD
        matchedDirectorDict[unmatchedDirector] = '' # initialise director's dictionary
        try:
            html = getURLElement(IAFD_SEARCH_URL.format(String.URLEncode(unmatchedDirector)), UseAdditionalResults=False)
            directorList = html.xpath('//table[@id="tblDir"]/tbody/tr')

            directorsFound = len(directorList)
            log('UTILS :: {0:<29} {1}'.format('Directors Found', '{0:>2} - Matching Name: {1}'.format(directorsFound, unmatchedDirector)))
            log(LOG_BIGLINE)
            for idx2, director in enumerate(directorList, start=1):
                # get director details and compare to Agent director
                try:
                    directorName = director.xpath('./td[2]/a/text()[normalize-space()]')[0]
                    compareDirectorName = re.sub(r'[\W\d_]', '', directorName).strip().lower()
                    log('UTILS :: {0:<29} {1}'.format('Matching Director', '{0:>2} - {1} / {1}'.format(idx2, directorName, compareDirectorName)))
                except Exception as e:
                    log('UTILS :: Error: Could not read Director Name: %s', e)
                    continue   # next director

                try:
                    directorAliasList = director.xpath('./td[3]/text()[normalize-space()]')[0].split(',')
                    directorAliasList = [x.strip() for x in directorAliasList if x]
                    compareDirectorAliasList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in directorAliasList]
                    log('UTILS :: {0:<29} {1}'.format('Alias', directorAliasList if directorAliasList else 'No Director Alias Recorded'))
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

                log('UTILS :: {0:<29} {1}'.format('Career', '{0} - {1}'.format(startCareer if startCareer > 0 else 'N/A', endCareer if endCareer > 0 else 'N/A')))

                matchedUsing = ''

                # match iafd row with Agent Director entry
                matchedDirector = True if compareUnmatchedDirector == compareDirectorName else False
                if matchedDirector:
                    matchedUsing = 'Name' 
                else:
                    log('UTILS :: {0:<29} {1}'.format('Failed Name Matching', '{0} != {1}'.format(compareUnmatchedDirector, compareDirectorName)))

                if not matchedDirector and directorAliasList:
                    matchedItem = x = [x for x in compareDirectorAliasList if compareUnmatchedDirector in x]
                    matchedDirector = True if matchedItem else False
                    if matchedDirector:
                        matchedUsing = 'Alias' 
                    else:
                        log('UTILS :: {0:<29} {1}'.format('Failed Alias List Matching', '{0} not in {1}'.format(compareUnmatchedDirector, compareDirectorAliasList)))

                # Check Career - if we have a match - this can only be done if we have a Year
                # only do this if we have more than one director returned
                if directorsFound > 1 and matchedDirector and myYear:
                    matchedDirector = (startCareer <= myYear <= endCareer)
                    if matchedDirector:
                        matchedUsing = 'Career' 
                    else:
                        log('UTILS :: {0:<29} {1}'.format('Failed Career Matching', '{0} <= {1} <= {2}'.format(startCareer, myYear, endCareer)))

                # now check if any processed IAFD Directors (FILMDICT) have an alias that matches with this director
                # this will only work if the film has directors recorded against it on IAFD
                # further matching with Cast if film is found on IAFD:
                if not matchedDirector and FILMDICT['Directors']:
                    for key, value in FILMDICT['Directors'].items():
                        if not value['CompareAlias']:
                            continue
                        checkName = key
                        checkAlias = value['Alias']
                        checkCompareAlias = value['CompareAlias']
                        if checkCompareAlias in compareDirectorAliasList:
                            matchedDirector = True
                            log('UTILS :: {0:<29} {1}'.format('Skipping: Recorded Director Name', '{0} AKA {1} also known by this name: {2}'.format(checkName, checkAlias, directorName)))
                            break

                if matchedDirector:
                    # we have an director who matches the conditions
                    directorURL = IAFD_BASE + director.xpath('./td[2]/a/@href')[0]
                    directorPhoto = director.xpath('./td[1]/a/img/@src')[0] # director name on agent website - retrieve picture
                    directorPhoto = '' if 'th_iafd_ad.gif' in directorPhoto else directorPhoto.replace('thumbs/th_', '')

                    log('UTILS :: {0:<29} {1}'.format('Director URL', directorURL))
                    log('UTILS :: {0:<29} {1}'.format('Director Photo', directorPhoto))
                    log('UTILS :: {0:<29} {1}'.format('Matched Using', matchedUsing))

                    # Assign values to dictionary
                    myDict = {}
                    myDict['Photo'] = directorPhoto
                    myDict['Alias'] = directorAliasList
                    myDict['CompareName'] = compareDirectorName
                    myDict['CompareAlias'] = compareDirectorAliasList
                    matchedDirectorDict[unmatchedDirector] = myDict

                    log(LOG_SUBLINE)
                    break   # matched - ignore any other entries

        except Exception as e:
            log('UTILS :: Error: Cannot Process IAFD Director Search Results: %s', e)
            log(LOG_SUBLINE)
            continue    # next director in agent director list  (allDirectorList)

    return matchedDirectorDict

# -------------------------------------------------------------------------------------------------------------------------------
def matchFilename(media):
    ''' Check filename on disk corresponds to regex preference format '''
    filmVars = {}
    filmVars['id'] = media.id
    filmVars['Status'] = False          # initial state before Search and Update Routine
    filmVars['Agent'] = AGENT
    filmVars['SceneAgent'] = False

    # file name
    filmPath = media.items[0].parts[0].file
    filmVars['FileName'] = os.path.splitext(os.path.basename(filmPath))[0]

    # film duration
    try:
        calcDuration = 0.0
        for part in media.items[0].parts:
            calcDuration += long(getattr(part, 'duration'))
        fileDuration = datetime.fromtimestamp(calcDuration // 1000) # convert miliseconds to seconds

    except:
        fileDuration = datetime.fromtimestamp(0)

    finally:
        filmVars['Duration'] = fileDuration

    # File name matching
    REGEX = '^\((?P<fnSTUDIO>[^()]*)\) - (?P<fnTITLE>.+?)?(?: \((?P<fnYEAR>\d{4})\))?( - \[(?P<fnCAST>[^\]]*)\])?(?: - (?i)(?P<fnSTACK>(cd|disc|disk|dvd|part|pt|scene) [1-8]))?$'
    pattern = re.compile(REGEX)
    matched = pattern.search(filmVars['FileName'])
    if not matched:
        raise Exception('< File Name [{0}] not in the expected format: (Studio) - Title [(Year)] [- cd|disc|disk|dvd|part|pt|scene 1..8]! >'.format(filmVars['FileName']))

    groups = matched.groupdict()
    log('UTILS :: File Name REGEX Matched Variables:')
    log('UTILS :: {0:<29} {1}'.format('Studio', groups['fnSTUDIO']))
    log('UTILS :: {0:<29} {1}'.format('Title', groups['fnTITLE']))
    log('UTILS :: {0:<29} {1}'.format('Year', groups['fnYEAR']))
    log('UTILS :: {0:<29} {1}'.format('Cast', groups['fnCAST']))
    log('UTILS :: {0:<29} {1}'.format('Stack', groups['fnSTACK']))
    log(LOG_SUBLINE)

    #   Studio
    filmVars['Studio'] = groups['fnSTUDIO'].split(';')[0].strip()
    filmVars['CompareStudio'] = Normalise(filmVars['Studio'])

    #   Title
    filmVars['Title'] = groups['fnTITLE']
    filmVars['CompareTitle'] = {sortAlphaChars(Normalise(filmVars['Title']))}

    #   Series - for use in creating collections - A Series is only considered if it is separated by space-dash-space
    series = []
    episode = []

    pattern = r'(?<![-.])\b[0-9]+\b(?!\.[0-9])$'                                        # series matching = whole separate number at end of string
    splitFilmTitle = filmVars['Title'].split(' - ')
    splitFilmTitle = [x.strip() for x in splitFilmTitle]
    splitCount = len(splitFilmTitle) - 1
    for index, partTitle in enumerate(splitFilmTitle):
        matchedSeries = re.subn(pattern, '', partTitle)
        if matchedSeries[1]:
            series.insert(0, matchedSeries[0].strip())                                  # e.g. Pissing
            episode.insert(0, partTitle)                                                # e.g. Pissing 1
            if index < splitCount:                                                      # only blank out series info in title if not last split
                splitFilmTitle[index] = ''
        else:
            if index < splitCount:                                                      # only add to collection if not last part of title e.g. Hardcore Fetish Series
                splitFilmTitle[index] = ''
                series.insert(0, partTitle)

    filmVars['Series'] = series
    filmVars['Episode'] = episode

    filmVars['Title'] = re.sub(ur' - |- ', ': ', filmVars['Title'])                     # replace dahes with colons
    pattern = ur'[' + re.escape(''.join(['.', '!', '%', '?'])) + ']+$'
    filmVars['ShortTitle'] = re.sub(pattern, '', ' '.join(splitFilmTitle).strip())      # strip punctuations at end of string
    filmVars['NormaliseShortTitle'] = Normalise(filmVars['ShortTitle'])
    filmVars['CompareShortTitle'] = sortAlphaChars(filmVars['NormaliseShortTitle'])

    #   Search Title: strip determinates - helpful for searching GEVI and GayDVD Empire
    #                 strip trailing '1' from search string
    pattern = ur'^(The |An |A )'
    filmVars['SearchTitle'] = re.sub(pattern, '', filmVars['ShortTitle'], flags=re.IGNORECASE).strip()

    pattern = ur' 1$'
    filmVars['SearchTitle'] = re.sub(pattern, '', filmVars['SearchTitle'], flags=re.IGNORECASE).strip()

    #   Prepare IAFD variables
    filmVars['IAFDDuration'] = datetime.fromtimestamp(0) # default 1970-01-01 00:00:00

    #       IAFD Studio
    filmVars['IAFDStudio'] = groups['fnSTUDIO'].split(';')[1].strip() if ';' in groups['fnSTUDIO'] else ''
    filmVars['CompareIAFDStudio'] = Normalise(filmVars['IAFDStudio']) if 'IAFDStudio' in filmVars and filmVars['IAFDStudio'] else ''

    #       IAFD Title - IAFD uses standard Latin Alphabet Characters for its entries.
    filmVars['IAFDTitle'] = makeASCII(groups['fnTITLE']).replace(' - ', ': ').replace('- ', ': ')       # iafd needs colons in place to search correctly
    filmVars['IAFDTitle'] = filmVars['IAFDTitle'].replace(' &', ' and')                                 # iafd does not use &
    filmVars['IAFDTitle'] = filmVars['IAFDTitle'].replace('!', '')                                      # remove !

    # split and take up to first occurence of character
    splitChars = ['[', '(', ur'\u2013', ur'\u2014']
    pattern = ur'[{0}]'.format(''.join(splitChars))
    matched = re.search(pattern, filmVars['IAFDTitle'])  # match against whole string
    filmVars['IAFDTitle'] = filmVars['IAFDTitle'][:matched.start()] if matched else filmVars['IAFDTitle']

    # split and take up to first standalone '1's'
    pattern = ur'(?<!\d)1(?!\d)'
    matched = re.search(pattern, filmVars['IAFDTitle'])  # match against whole string
    filmVars['IAFDTitle'] = filmVars['IAFDTitle'][:matched.start()] if matched else filmVars['IAFDTitle']

    # strip definite and indefinite english articles and take after articles
    pattern = ur'^(The|An|A) '
    filmVars['IAFDTitle']= re.sub(pattern, '', filmVars['IAFDTitle'], re.IGNORECASE)  # match against whole string
    filmVars['IAFDCompareTitle'] = sortAlphaChars(Normalise(filmVars['IAFDTitle']))

    # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
    searchString = filmVars['IAFDTitle'].split(':')[0]
    searchString = String.StripDiacritics(searchString).strip()
    searchString = String.URLEncode(searchString).replace('%25', '%').replace('%26', '&').replace('*', '')
    filmVars['IAFDSearchTitle'] = searchString

    #   Year / comparison date defaults to 31st Dec of Year
    try:
        filmVars['Year'] = int(groups['fnYEAR'])
        filmVars['CompareDate'] = datetime(filmVars['Year'], 12, 31)
    except:
        filmVars['Year'] = 0
        filmVars['CompareDate'] = datetime.fromtimestamp(0)

    #   Stacked
    filmVars['Stacked'] = 'Yes' if groups['fnSTACK'] is not None else 'No'

    #  Filname Cast List
    filmVars['FilenameCast'] = re.split(r',\s*', groups['fnCAST']) if groups['fnCAST'] else []

    # sort comparisons for matching strings
    # IAFD Variables used by other Agents
    filmVars['FilmAKA'] = ''            # default blank - only IAFD has AKA Titles
    filmVars['Compilation'] = 'No'      # default No
    filmVars['AllGirl'] = 'No'          # default No
    filmVars['AllMale'] = 'Yes'         # default Yes as this is usually used on gay websites.
    filmVars['Cast'] = {}
    filmVars['Directors'] = {}
    filmVars['FoundOnIAFD'] = 'No'      # default No
    filmVars['IAFDFilmURL'] = ''        # default blank

    # print out dictionary values / normalise unicode
    printFilmInformation(filmVars)

    return filmVars

# ----------------------------------------------------------------------------------------------------------------------------------
def matchDuration(siteDuration, FILMDICT, matchAgainstIAFD=False):
    ''' match file duration against iafd duration '''
    if matchAgainstIAFD:
        dx = abs((FILMDICT['IAFDDuration'] - siteDuration).total_seconds())     # compare Site Film Length against IAFD result
        dxmm, dxss = divmod(dx, 60)
    else:
        dx = abs((FILMDICT['Duration'] - siteDuration).total_seconds())         # compare Site film Length against Film File on Disk
        dxmm, dxss = divmod(dx, 60)

    testDuration = 'Passed' if dxmm <= DURATIONDX else 'Failed'

    log('UTILS :: {0:<29} {1}'.format('Match Against IAFD Duration', matchAgainstIAFD))
    log('UTILS :: {0:<29} {1}'.format('Site Duration', siteDuration.strftime('%H:%M:%S')))
    if matchAgainstIAFD:
        log('UTILS :: {0:<29} {1}'.format('IAFD Duration', FILMDICT['IAFDDuration'].strftime('%H:%M:%S')))
    else:
        log('UTILS :: {0:<29} {1}'.format('File Duration', FILMDICT['Duration'].strftime('%H:%M:%S')))
    log('UTILS :: {0:<29} {1}'.format('Delta', '{0} Minutes'.format(int(dxmm))))
    log('UTILS :: {0:<29} {1}'.format('Duration Comparison Test', '{0}{1}'.format('' if MATCHSITEDURATION else 'Ignore: ', testDuration)))

    if testDuration == 'Failed' and MATCHSITEDURATION:
        raise Exception('< Duration Match Failure! >')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def matchReleaseDate(siteReleaseDate, FILMDICT, UseTwoYearMatch=False):
    ''' match file year against website release date: return formatted site date if no error or default to formated file date '''

    # there can not be a difference more than 366 days between FileName Date and siteReleaseDate
    dx = abs((FILMDICT['CompareDate'] - siteReleaseDate).days)

    dxMaximum = 731 if UseTwoYearMatch else 366               # 2 years if matching film year with IAFD and 1 year for Agent
    testReleaseDate = 'Failed' if dx > dxMaximum else 'Passed'

    log('UTILS :: {0:<29} {1}'.format('Site Release Date', siteReleaseDate))
    log('UTILS :: {0:<29} {1}'.format('File Release Date', FILMDICT['CompareDate']))
    log('UTILS :: {0:<29} {1}'.format('Delta in Days', dx))
    log('UTILS :: {0:<29} {1}'.format('Release Date Comparison Test', testReleaseDate))

    if testReleaseDate == 'Failed':
        raise Exception('< Release Date Match Failure! >')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def matchStudio(siteStudio, FILMDICT):
    ''' match file studio name against website studio/iafd name: Boolean Return '''
    compareSiteStudio = Normalise(siteStudio)

    testStudio = 'Full Match' if compareSiteStudio == FILMDICT['CompareStudio'] else ''

    if not testStudio:
        testStudio = 'Full Match (IAFD)' if 'CompareIAFDStudio' in FILMDICT and FILMDICT['CompareIAFDStudio'] and compareSiteStudio == FILMDICT['CompareIAFDStudio'] else ''

    if not testStudio:
        testStudio = 'Partial Match' if (compareSiteStudio in FILMDICT['CompareStudio'] or FILMDICT['CompareStudio'] in compareSiteStudio) else ''

    if not testStudio:
        testStudio = 'Partial Match (IAFD)' if ('CompareIAFDStudio' in FILMDICT and FILMDICT['CompareIAFDStudio']) and \
                                               (compareSiteStudio in FILMDICT['CompareIAFDStudio'] or FILMDICT['CompareIAFDStudio'] in compareSiteStudio) else ''

    if not testStudio:
        testStudio = 'Failed Match'

    log('UTILS :: {0:<29} {1}'.format('Site Studio', siteStudio))
    log('UTILS :: {0:<29} {1}'.format('IAFD Studio', FILMDICT['IAFDStudio']))
    log('UTILS :: {0:<29} {1}'.format('Compare Site Studio', compareSiteStudio))
    log('UTILS :: {0:<29} {1}'.format('       Agent Studio', FILMDICT['CompareStudio']))
    log('UTILS :: {0:<29} {1}'.format('        IAFD Studio', FILMDICT['CompareIAFDStudio']))
    log('UTILS :: {0:<29} {1}'.format('Studio Comparison Test', testStudio))

    if testStudio == 'Failed Match':
        raise Exception('< Studio Match Failure! >')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def matchTitle(filmTitle, FILMDICT):
    ''' match file title against website/iafd title: Boolean Return '''
    # some agents have the studio name in the title within brackets - take these out before matching
    pattern = re.compile('\(({0}.*?)\)'.format(FILMDICT['Studio']), re.IGNORECASE)
    filmTitle = re.sub(pattern, '', filmTitle)
    filmTitleNormalise = Normalise(filmTitle)

    if FILMDICT['NormaliseShortTitle'] in filmTitleNormalise:
        pattern = re.compile(re.escape(FILMDICT['NormaliseShortTitle']), re.IGNORECASE)
        filmTitleNormalise = '{0}{1}'.format(re.sub(pattern, '', filmTitleNormalise).strip(), FILMDICT['NormaliseShortTitle'])

    filmTitleASort = sortAlphaChars(filmTitleNormalise)
    testTitle = 'Passed' if filmTitleASort in FILMDICT['CompareTitle'] else 'Passed (IAFD)' if filmTitleASort in FILMDICT['IAFDCompareTitle'] else 'Failed'

    log('UTILS :: {0:<29} {1}'.format('Site Title', filmTitle))
    log('UTILS :: {0:<29} {1}'.format('Normalised', filmTitleNormalise))
    log('UTILS :: {0:<29} {1}'.format('    Sorted', filmTitleASort))
    log('UTILS :: {0:<29} {1}'.format('File Full Title', FILMDICT['Title']))
    log('UTILS :: {0:<29} {1}'.format('    Short Title', FILMDICT['ShortTitle']))
    log('UTILS :: {0:<29} {1}'.format('     Normalised', FILMDICT['NormaliseShortTitle']))
    log('UTILS :: {0:<29} {1}'.format('         Sorted', FILMDICT['CompareShortTitle']))
    log('UTILS :: {0:<29} {1}'.format('IAFD Title', FILMDICT['IAFDTitle']))
    log('UTILS :: {0:<29} {1}'.format('    Sorted', FILMDICT['IAFDCompareTitle']))
    log('UTILS :: {0:<29} {1}'.format('Title Comparison Test', testTitle))

    if testTitle == 'Failed':
        raise Exception('< Title Match Failure! >')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def Normalise(myString):
    ''' Normalise string for, strip uneeded characters for comparison of web site values to file name regex group values '''
    # Check if string has roman numerals as in a series; note the letter I will be converted
    myString = '{0} '.format(myString)  # append space at end of string to match last characters
    pattern = r'(?=\b[MDCLXVI]+\b)M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})'
    matches = re.findall(pattern, myString, re.IGNORECASE)  # match against string
    if matches:
        RomanValues = {'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000}
        for match in matches:
            myRoman = ''.join(match).upper()
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
    # myString = makeASCII(myString)

    # strip domain suffixes, vol., volume, Pt, Part from string, standalone '1's' then strip all non alphanumeric characters
    # pattern = r'[.]([a-z]{2,3}|co[.][a-z]{2})|Vol[.]|Vols[.]|Nr[.]|\bVolume\b|\bVolumes\b|(?<!\d)1(?!\d)|Pt |\bPart\b[^A-Za-z0-9]+'
    pattern = r'[.]([a-z]{2,3}|co[.][a-z]{2})|Vol[.]|Vols[.]|Nr[.]|\bVolume\b|\bVolumes\b|Pt |\bPart\b[^A-Za-z0-9]+'
    myString = re.sub(pattern, '', myString, flags=re.IGNORECASE)
    myString = filter(str.isalnum, myString)
    myString = ''.join(myString)
    return myString

# ----------------------------------------------------------------------------------------------------------------------------------
def printFilmInformation(myDictionary):
    # print out dictionary values / normalise unicode
    log('UTILS :: Film Dictionary Variables:')
    for key in sorted(myDictionary.keys()):
        myDictionary[key] = list(dict.fromkeys(myDictionary[key])) if type(myDictionary[key]) is list else myDictionary[key]
        log('UTILS :: {0:<29} {1}'.format(key, myDictionary[key]))

# ----------------------------------------------------------------------------------------------------------------------------------
def setMetadata(metadata, FILMDICT):
    '''
    The following bits of metadata need to be established and used to update the movie on plex
    1.  Metadata that is set by Agent as default
        a. id.                              : Plex media id setting
        b. Studio                           : From studio group of filename - no need to process this as above
        c. Title                            : From title group of filename - no need to process this as is used to find it on website
        d. Content Rating                   : Always X
        e. Content Rating Age               : Always 18

    2.  Metadata retrieved from website
        a. Original Title                   : From IAFD - Also Known As Title
        b. Tag line                         : Corresponds to the url of film
        c. Originally Availiable Date       : Production Date, default to (Year) of File Name else Agent Website Date
        d. Ratings                          : Viewer Rating out of 100%
        e. Genres                           : List of Genres (alphabetic order)
        f. Countries
        g. Cast                             : List of Actors, Roles and Photos (alphabetic order) - Photos sourced from IAFD
        h. Directors                        : List of Directors and Photos (alphabetic order)
        i. Collections                      : retrieved from FILMDICT, Genres, Countries, Cast Directors
        j. Posters                          : Front Cover of DVD
        k. Art (Background)                 : Back Cover of DVF
        l. Reviews                          : Usually Scene Information OR Actual Reviews depending on Agent
        m. Chapters                         : Scene Lengths for Jump Tos in film
        n. Summary                          : Synopsis of film
    '''
    log('UTILS :: 1.  Set Metadata from File Name and Default Settings:')

    try:
        # 1a.   Set id
        log(LOG_SUBLINE)
        try:
            metadata.id = FILMDICT['id']
            log('UTILS :: {0:<29} {1}'.format('1a. ID', metadata.id))

        except Exception as e:
            log('UTILS :: Error setting Studio: %s', e)

        # 1b.   Set Studio
        log(LOG_SUBLINE)
        try:
            metadata.studio = FILMDICT['Studio']
            log('UTILS :: {0:<29} {1}'.format('1b. Studio', metadata.studio))

        except Exception as e:
            log('UTILS :: Error setting Studio: %s', e)

        # 1c.   Set Title
        log(LOG_SUBLINE)
        try:
            metadata.title = FILMDICT['Title']
            log('UTILS :: {0:<29} {1}'.format('1c. Title', metadata.title))

        except Exception as e:
            log('UTILS :: Error setting Title: %s', e)

        # 1d.   Set Content Rating to Adult
        log(LOG_SUBLINE)
        try:
            metadata.content_rating = 'X'
            log('UTILS :: {0:<29} {1}'.format('1d. Content Rating', 'X'))

        except Exception as e:
            log('UTILS :: Error setting Content Rating: %s', e)

        # 1e.   Set Content Rating Age to 18 years
        log(LOG_SUBLINE)
        try:
            metadata.content_rating_age = 18
            log('UTILS :: {0:<29} {1}'.format('1e. Content Rating Age', '18'))

        except Exception as e:
            log('UTILS :: Error setting Content Rating Age: %s', e)

        log(LOG_SUBLINE)
        log('UTILS :: 2.  Set Metadata from Scraped Website Resources:')

        # 2a.   Set Original Title
        log(LOG_SUBLINE)
        try:
            metadata.original_title = FILMDICT['FilmAKA']
            log('UTILS :: {0:<29} {1}'.format('2a. Original Title (AKA)', metadata.original_title))

        except Exception as e:
            log('UTILS :: Error setting Original Title: %s', e)

        # 2b.   Set Tagline
        log(LOG_SUBLINE)
        try:
            if AGENT == 'IAFD':
                metadata.tagline = FILMDICT['FilmURL']  

            elif FILMDICT['FoundOnIAFD'] == 'No':
                metadata.tagline = FILMDICT['FilmURL']  

            else:
                metadata.tagline = '{0} :: {1}'.format(FILMDICT['FilmURL'], FILMDICT['IAFDFilmURL'])

            for idx, tag in enumerate(metadata.tagline.split('::'), start=1):
                log('UTILS :: {0:<29} {1}'.format('2b. Tagline' if idx == 1 else '' , '{0} - {1}'.format(idx, tag.strip())))

        except Exception as e:
            log('UTILS :: Error setting Tag Line: %s', e)

        # 2c.   Set Originally Available Date - From website's release date if only it is earlier in the same year
        log(LOG_BIGLINE)
        try:
            log('UTILS :: {0:<29} {1}'.format('2c. Originally Available Date', ''))
            log('UTILS :: {0:<29} {1}'.format('Current Date', metadata.originally_available_at))
            log('UTILS :: {0:<29} {1}'.format('Current Year', metadata.year))
            releaseDate = FILMDICT[AGENT]['ReleaseDate'].date()
            log('UTILS :: {0:<29} {1}'.format('Agent Date', releaseDate))


            if RESETMETA or metadata.originally_available_at is None:
                metadata.originally_available_at = datetime.fromtimestamp(0).date()
                metadata.year = metadata.originally_available_at.year

            metadata.originally_available_at = releaseDate
            metadata.year = metadata.originally_available_at.year

        except Exception as e:
            log('UTILS :: Error setting Originally Available Date: %s', e)

        # 2d.   Rating  can be a maximum of 10 - float value
        log(LOG_SUBLINE)
        try:
            if RESETMETA:
                metadata.rating = 0.0

            metadata.rating = FILMDICT[AGENT]['Rating'] if metadata.rating < FILMDICT[AGENT]['Rating'] else metadata.rating
            log('UTILS :: {0:<29} {1}'.format('2d. Film Rating', metadata.rating))

        except Exception as e:
            log('UTILS :: Error setting Rating: %s', e)

        # 2e.   Genres - retrieved from website and in some case from the synopsis
        log(LOG_SUBLINE)
        try:
            if RESETMETA:
                metadata.genres.clear()

            listGenres = list(FILMDICT[AGENT]['Genres'])
            if AGENT != 'IAFD' and 'IAFD' in FILMDICT:
                listGenres.extend(FILMDICT['IAFD']['Genres'])
                listGenres = (list(set(listGenres)))

            listGenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('2e. Genres', '{0:>2} - {1}'.format(len(listGenres), listGenres)))
            for idx, item in enumerate(listGenres, start=1):
                metadata.genres.add(item)
                log('UTILS :: {0:<29} {1}'.format('Genre' if idx == 1 else '', '{0:>2} - {1}'.format(idx, item)))

        except Exception as e:
            log('UTILS :: Error setting Genres: %s', e)

        # 2f.   Countries
        log(LOG_SUBLINE)
        try:
            if RESETMETA:
                metadata.countries.clear()

            listCountries = list(FILMDICT[AGENT]['Countries'])
            if AGENT != 'IAFD' and 'IAFD' in FILMDICT:
                listCountries.extend(FILMDICT['IAFD']['Countries'])
                listCountries = (list(set(listCountries)))

            listCountries.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('2f. Countries', '{0:>2} - {1}'.format(len(listCountries), listCountries)))
            for idx, item in enumerate(listCountries, start=1):
                log('UTILS :: {0:<29} {1}'.format('Country' if idx == 1 else '', '{0:>2} - {1}'.format(idx, item)))
                metadata.countries.add(item)

        except Exception as e:
            log('UTILS :: Error setting Countries: %s', e)

        # 2g.   Cast: thumbnails, roles from IAFD. Use IAFD as main Source if film found on IAFD
        log(LOG_SUBLINE)
        cast = []
        try:
            if RESETMETA:
                metadata.roles.clear()

            log('UTILS :: {0:<29} {1}'.format('2g. Cast', ''))
            if FILMDICT['FilenameCast']:                      # Priority 1: user has defined the missing cast to be used in filename
                cast = FILMDICT['FilenameCast'][:]

            if FILMDICT[AGENT]['Cast']:                       # Priority 2: Add Cast from Agent
                cast.extend(FILMDICT[AGENT]['Cast'])

            tempDict = getCast(cast, FILMDICT)                # process cast names returning a dictionary
            castDict = {k.split('(')[0].strip():v for (k,v) in tempDict.items()}
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(castDict.keys()), sorted(castDict.keys()))))

            # sort the dictionary and add key(Name)- value(Photo, Role) to metadata
            for idx, key in enumerate(sorted(castDict), start=1):
                log('UTILS :: {0:<29} {1}'.format('Cast Name' if idx == 1 else '', '{0:>2} - {1}'.format(idx, key)))
                newRole = metadata.roles.new()
                newRole.name = key
                newRole.photo = castDict[key]['Photo']
                newRole.role = castDict[key]['Role']
                # add cast name to collection

        except Exception as e:
            log('UTILS :: Error setting Cast: %s', e)

        # 2h.   Directors
        log(LOG_SUBLINE)
        try:
            if RESETMETA:
                metadata.directors.clear()

            directors = FILMDICT[AGENT]['Directors']
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('2h. Director(s)'), '{0:>2} - {1}'.format(len(directors), directors)))
            tempDict = getDirectors(directors, FILMDICT)
            directorDict = {k.split('(')[0].strip():v for (k,v) in tempDict.items()}
            for idx, key in enumerate(sorted(directorDict), start=1):
                log('UTILS :: {0:<29} {1}'.format('Director' if idx == 1 else '', '{0:>2} - {1}'.format(idx, key)))
                newDirector = metadata.directors.new()
                newDirector.name = key
                newDirector.photo = directorDict[key]

        except Exception as e:
            log('UTILS :: Error setting Director(s): %s', e)

        # 2i.   Set Collection
        log(LOG_SUBLINE)
        listCollections = []
        log('UTILS :: {0: <29} {1}'.format('2i. Collections', ''))
        try:
            # scraped by agent collection - find all films scrapped by agent in case of errors missed
            defaultCollections = ['|~| {0}'.format(FILMDICT['Agent']), 
                                  '|~| {0}-IAFD'.format('On' if FILMDICT['FoundOnIAFD'] == 'Yes' else 'Not On'),
                                  '|~| Stacked' if FILMDICT['Stacked'] == 'Yes' else '|~| Not Stacked'
                                 ]
            for idx, item in enumerate(defaultCollections, start=1):
                listCollections.append(item)
                log('UTILS :: {0:<29} {1}'.format('{0}'.format('Default Collections' if idx == 1 else ''), '{0:>2} - {1}'.format(idx, item)))

            # Process Cast Members - Group prefix = |a|, Do not create Unknown Actor Collections
            if COLCAST:
                for idx, item in enumerate(sorted(castDict.keys()), start=1):
                    if item != 'Unknown Actor':      # do not create collections for unknown actors...
                        log('UTILS :: {0:<29} {1}'.format('{0}'.format('Cast Collections' if idx == 1 else ''), '{0:>2} - {1}'.format(idx, item)))
                        listCollections.append('|a| {0}'.format(item) if GROUPCOL else item)

            # Process Countries - Group Prefix |c|
            if COLCOUNTRY:
                for idx, item in enumerate(listCountries, start=1):
                    log('UTILS :: {0:<29} {1}'.format('{0}'.format('Country Collections' if idx == 1 else ''), '{0:>2} - {1}'.format(idx, item)))
                    listCollections.append('|c| {0}'.format(item) if GROUPCOL else item)

            # Process Directors - Group prefix = |d|
            if COLDIRECTOR:
                for idx, item in enumerate(sorted(directorDict.keys()), start=1):
                    log('UTILS :: {0:<29} {1}'.format('{0}'.format('Director Collections' if idx == 1 else ''), '{0:>2} - {1}'.format(idx, item)))
                    listCollections.append('|d| {0}'.format(item) if GROUPCOL else item)

            # Process Genres - Group Prefix |g|
            if COLGENRE:
                for idx, item in enumerate(listGenres, start=1):
                    log('UTILS :: {0:<29} {1}'.format('{0}'.format('Genre Collections' if idx == 1 else ''), '{0:>2} - {1}'.format(idx, item)))
                    if item == 'Compilations':
                        listCollections.append('|~| {0}'.format(item))
                    else:
                        listCollections.append('|g| {0}'.format(item) if GROUPCOL else item)

                if FILMDICT['Compilation'] == 'Yes':
                    log('UTILS :: {0:<29} {1}'.format('Compilation Collection', 'Yes'))
                    listCollections.append('|~| Compilations')

            # Process Studio Name
            if COLSTUDIO:
                studioList = []
                studioList.append(FILMDICT['Studio'])
                if FILMDICT['IAFDStudio']:
                    studioList.append(FILMDICT['IAFDStudio'])

                for idx, item in enumerate(studioList, start=1):
                    log('UTILS :: {0:<29} {1}'.format('{0}'.format('Studio Collections' if idx == 1 else ''), '{0:>2} - {1}'.format(idx, item)))
                    listCollections.append('|s| {0}'.format(item) if GROUPCOL else item) 

            # Process File Name Series: These are not grouped as they are present as data on some websites
            if COLSERIES:
                seriesList = FILMDICT['Series']
                for idx, item in enumerate(seriesList, start=1):
                    log('UTILS :: {0:<29} {1}'.format('{0}'.format('Series Collection' if idx == 1 else ''), '{0:>2} - {1}'.format(idx, item)))
                    listCollections.append(item) 

            # Process Website Series: These are not grouped and not an option
            if FILMDICT[AGENT]['Collections']:
                websiteCollectionList = FILMDICT[AGENT]['Collections']
                for idx, item in enumerate(websiteCollectionList, start=1):
                    log('UTILS :: {0:<29} {1}'.format('{0}'.format('Website Collections' if idx == 1 else ''), '{0:>2} - {1}'.format(idx, item)))
                    listCollections.append(item)

            # Add to Metadata
            if RESETMETA:
                metadata.collections.clear()

            log('UTILS ::')
            log('UTILS :: {0:<29} {1}'.format('Total Collections', len(listCollections)))
            listCollections = list(set(listCollections))
            log('UTILS :: {0:<29} {1}'.format('Unique Collections', len(listCollections)))
            listCollections.sort(key = lambda x: x.lower())
            for idx, item in enumerate(listCollections, start=1):
                metadata.collections.add(item)
                log('UTILS :: {0:<29} {1}'.format('{0}'.format('Adding Collections' if idx == 1 else ''), '{0:>2} - {1}'.format(idx, item)))

        except Exception as e:
            log('UTILS :: Error setting Collection: %s', e)

        # 2j.   Posters - Front Cover of DVD
        # There is no working way to reset posters
        log(LOG_SUBLINE)
        try:
            poster = FILMDICT[AGENT]['Poster']
            log('UTILS :: {0:<29} {1}'.format('2j. Poster Image', poster if poster else 'None Found'))
            if poster:
                if FILMDICT['SceneAgent']:
                    pic, picContent = getFilmImages(imageType='Poster', imageURL=poster, whRatio=1.5)
                    metadata.posters[pic] = Proxy.Media(picContent, sort_order=1)
                    metadata.posters.validate_keys([pic])
                else:
                    metadata.posters[poster] = Proxy.Media(HTTP.Request(poster).content, sort_order=1)
                    metadata.posters.validate_keys([poster])

        except Exception as e:
            log('UTILS :: Error setting Poster: %s', e)

        # 2k.   Art - Back Cover of DVD : Determined by user preference
        # There is no working way to reset Art
        log(LOG_SUBLINE)
        try:
            if USEBACKGROUNDART:
                art = FILMDICT[AGENT]['Art']
                log('UTILS :: {0:<29} {1}'.format('2k. Art Image', art if art else 'None Found'))
                if art:
                    if FILMDICT['SceneAgent']:
                        pic, picContent = getFilmImages(imageType='Art', imageURL=art, whRatio=0.5625)
                        metadata.art[pic] = Proxy.Media(picContent, sort_order=1)
                        metadata.art.validate_keys([pic])
                    else:
                        metadata.art[art] = Proxy.Media(HTTP.Request(art).content, sort_order=1)
                        metadata.art.validate_keys([art])
            else:
                log('UTILS :: {0:<29} {1}'.format('Art Image', 'Not Set By Preference'))

        except Exception as e:
            log('UTILS :: Error setting Art: %s', e)

        # 2l.   Reviews - Put all Scene information as default unless there are none and website has actual reviews
        log(LOG_SUBLINE)
        try:
            source = AGENT
            scenes = FILMDICT[source]['Scenes']
            if scenes == {} and 'IAFD' in FILMDICT and FILMDICT['IAFD']['Scenes'] != {}:
                scenes = FILMDICT['IAFD']['Scenes']
                source = 'IAFD'

            log('UTILS :: {0:<29} {1}'.format('2l. Scenes', '{0}: {1} - {2}'.format(source, len(scenes), scenes)))
            if scenes != {}:
                if RESETMETA:
                    metadata.reviews.clear()

                for idx, item in enumerate(scenes, start=1):
                    scene = str(idx)
                    newReview = metadata.reviews.new()
                    newReview.author = scenes[scene]['Author']
                    newReview.link  = scenes[scene]['Link']
                    newReview.source = scenes[scene]['Source']
                    newReview.text = scenes[scene]['Text']
                    log('UTILS :: {0:<29} {1}'.format('Created Reviews' if idx == 1 else '', '{0}: {1}'.format(scene, newReview.author)))
            else:
                raise Exception('< No Scenes / Reviews Found! >')

        except Exception as e:
            log('UTILS :: Error setting Reviews: %s', e)

        # 2m.   Chapters - Put all Chapter Information here
        log(LOG_SUBLINE)
        try:
            chapters = FILMDICT[AGENT]['Chapters']
            log('UTILS :: {0:<29} {1}'.format('2m. Chapters', '{0} - {1}'.format(len(chapters), chapters)))

            if chapters != {}:
                if RESETMETA:
                    metadata.chapters.clear()
                for idx, item in enumerate(chapters, start=1):
                    chapter = str(idx)
                    newChapter = metadata.chapters.new()
                    newChapter.title = chapters[chapter]['Title']
                    newChapter.start_time_offset = chapters[chapter]['StartTime']
                    newChapter.end_time_offset = chapters[chapter]['EndTime']
                    log('UTILS :: {0:<29} {1}'.format('Created Chapters' if idx == 1 else '', '{0}: {1}'.format(chapter, newChapter.title)))
            else:
                raise Exception('< No Chapters Found! >')

        except Exception as e:
            log('UTILS :: Error setting Chapters: %s', e)

        # 2n.   Summary = Synopsis with IAFD Legend
        log(LOG_SUBLINE)
        try:
            synopsis = FILMDICT[AGENT]['Synopsis']
            if not synopsis:
                if 'IAFD' in FILMDICT and FILMDICT['IAFD']['Synopsis']:
                    synopsis = FILMDICT['IAFD']['Synopsis']
                    log('UTILS :: {0:<29} {1}'.format('2n. IAFD Synopsis', 'Website Synopsis Absent'))

            # translate if synopsis not in library language
            synopsis = TranslateString(synopsis, SITE_LANGUAGE, FILMDICT['lang'], DETECT)

        except Exception as e:
            synopsis = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        else:
            # combine and update
            log(LOG_SUBLINE)
            summary = ('{0}\n{1}' if PREFIXLEGEND else '{1}\n{0}').format(FILMDICT['Legend'], synopsis.strip())
            summary = summary.replace('\n\n', '\n')
            summaryList = wrap(summary, 100)
            for idx, summaryLine in enumerate(summaryList):
                log('UTILS :: {0:<29} {1}'.format('2n. Summary with Legend' if idx == 0 else '', summaryLine.replace('\n', '')))

            if RESETMETA:
                metadata.summary = ' ' 

            metadata.summary = summary

        log('UTILS ::')

    except Exception as e:
        FILMDICT['Status'] = False

    else:
        FILMDICT['Status'] = True

# ----------------------------------------------------------------------------------------------------------------------------------
def setupStartVariables():
    ''' used by start routine to set up Tidy Genres, Countries List and Show Preference Settings'''

    #   1.    Preference Settings list json file entries
    log(LOG_SUBLINE)
    log('START :: {0:<29} {1}'.format('Plex Support Path', PlexSupportPath))

    defaultPrefs_json = os.path.join(PlexSupportPath, 'Plug-ins', '{0}.bundle'.format(AGENT), 'Contents', 'DefaultPrefs.json')
    log('START :: {0:<29} {1}'.format('Default Preferences', os.path.relpath(defaultPrefs_json, PlexSupportPath)))
    if os.path.isfile(defaultPrefs_json):
        try:
            json = JSON.ObjectFromString(PlexLoadFile(defaultPrefs_json), encoding=None)  ### Load 'DefaultPrefs.json' to have access to default settings ###
            if json:
                log('START :: {0:<29} {1}'.format('Loaded', defaultPrefs_json))
                log('START :: {0:<29} {1}'.format('Preferences:', len(json)))
                idx = 0
                for entry in json:                   #Build Pref_list dict from json file
                    idx += 1
                    prefName =  entry['id']
                    defSet =  entry['default']
                    setAs = Prefs[prefName]
                    log('START :: {0:<29} {1}'.format('{0:>2}. {1}'.format(idx, prefName), 'Default = {0:<10}| Set As = {1}'.format(defSet, setAs)))
        except Exception as e:
            log('START :: Error Loading Default Preferences File: %s', e)

    #   2. Country Set: create set containing countries from country.txt located in plugins code directory
    log(LOG_SUBLINE)
    log('START :: Prepare Set of Country Names')
    global COUNTRYSET
    try:
        countries_txt = os.path.join(PlexSupportPath, 'Plug-ins', 'Countries.txt')
        txtfile = PlexLoadFile(countries_txt)
        txtrows = txtfile.split('\n')
        for row in txtrows:
            COUNTRYSET.add(row.strip())

        log('START :: {0:<29} {1}'.format('Country Set', '{0:>2} - {1}'.format(len(COUNTRYSET), sorted(COUNTRYSET))))

    except Exception as e:
        log('START :: Error creating Country Set: %s', e)
        log('START :: Error: Country Source File: %s', countries_txt)

    #   2.     Tidy Genres: create dictionary containing the tidy genres from genres.tsv file located in plugins code directory
    log(LOG_SUBLINE)
    log('START :: Prepare Tidied Dictionary of Genre/Countries')
    global TIDYDICT
    tidiedCountriesSet = set()                    # used for debugging
    try:
        tidy_txt = os.path.join(PlexSupportPath, 'Plug-ins', 'GayTidy.txt')
        csvfile = PlexLoadFile(tidy_txt)
        csvrows = csvfile.split('\n')
        for idx, row in enumerate(csvrows, start=1):
            if '::' in row:
                keyValue = row.split('::')
                keyValue = [x.strip() for x in keyValue]
                key = keyValue[0].lower()
                value = keyValue[1]
                if key not in TIDYDICT and len(keyValue) == 2:
                    TIDYDICT[key] = value if value != 'x' else None
                    if value in COUNTRYSET:                 # useful for comparing cities, locations to the country they are in when debugging
                        tidiedCountriesSet.add('{0} : {1}'.format(keyValue[0], value))
                else:
                    log('START :: {0:<29} {1}'.format('Duplicate/Error Row', 'Row {0} - {1}'.format(idx, row)))
            else:
                log('START :: {0:<29} {1}'.format('Invalid Format Row', 'Row {0} - {1}'.format(idx, row)))

        tidiedSet = set(TIDYDICT.values())
        log('START :: {0:<29} {1}'.format('Original Categories', '{0:>2} - {1}'.format(len(TIDYDICT), sorted(TIDYDICT.keys()))))
        log('START :: {0:<29} {1}'.format('Tidied Categories', '{0:>2} - {1}'.format(len(tidiedSet), sorted(tidiedSet))))
        log('START :: {0:<29} {1}'.format('Tidied Countries', '{0:>2} - {1}'.format(len(tidiedCountriesSet), sorted(tidiedCountriesSet))))
        tidiedCountriesSet = None
        del(tidiedCountriesSet)


    except Exception as e:
        log('START :: Error creating Tidy Categories Dictionary: %s', e)   
        log('START :: Error: Tidy Categories Source File: %s', tidy_txt)   

# -------------------------------------------------------------------------------------------------------------------------------
def showSetData(mySet, myString):
    myList = list(mySet)
    myList.sort(key = lambda x: x.lower())
    log('UTILS :: {0:<29} {1}'.format(myString, '{0:>2} - {1}'.format(len(myList), myList)))

# ----------------------------------------------------------------------------------------------------------------------------------
def sortAlphaChars(myString):
    numbers = re.sub('[^0-9]','', myString)
    letters = re.sub('[0-9]','', myString)
    myString = '{0}{1}'.format(numbers, ''.join(sorted(letters)))
    myString = myString.replace(' ', '')

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
        dictLanguages = {'af': 'afrikaans', 'sq': 'albanian', 'ar': 'arabic', 'hy': 'armenian', 'az': 'azerbaijani', 'eu': 'basque', 'be': 'belarusian', 'bn': 'bengali', 'bs': 'bosnian',
                         'bg': 'bulgarian', 'ca': 'catalan', 'ceb': 'cebuano', 'ny': 'chichewa', 'zh-cn': 'chinese simplified', 'zh-tw': 'chinese traditional', 'zh-cn': '#chinese simplified',
                         'zh-tw': '#chinese traditional', 'hr': 'croatian', 'cs': 'czech', 'da': 'danish', 'nl': 'dutch', 'en': 'english', 'eo': 'esperanto', 'et': 'estonian',
                         'tl': 'filipino', 'fi': 'finnish', 'fr': 'french', 'gl': 'galician', 'ka': 'georgian', 'de': 'german', 'el': 'greek', 'gu': 'gujarati', 'ht': 'haitian creole',
                         'ha': 'hausa', 'iw': 'hebrew', 'hi': 'hindi', 'hmn': 'hmong', 'hu': 'hungarian', 'is': 'icelandic', 'ig': 'igbo', 'id': 'indonesian', 'ga': 'irish',
                         'it': 'italian', 'ja': 'japanese', 'jw': 'javanese', 'kn': 'kannada', 'kk': 'kazakh', 'km': 'khmer', 'ko': 'korean', 'lo': 'lao', 'la': 'latin', 'lv': 'latvian',
                         'lt': 'lithuanian', 'mk': 'macedonian', 'mg': 'malagasy', 'ms': 'malay', 'ml': 'malayalam', 'mt': 'maltese', 'mi': 'maori', 'mr': 'marathi', 'mn': 'mongolian',
                         'my': 'myanmar (burmese)', 'ne': 'nepali', 'no': 'norwegian', 'fa': 'persian', 'pl': 'polish', 'pt': 'portuguese', 'ma': 'punjabi', 'ro': 'romanian', 'ru': 'russian',
                         'sr': 'serbian', 'st': 'sesotho', 'si': 'sinhala', 'sk': 'slovak', 'sl': 'slovenian', 'so': 'somali', 'es': 'spanish', 'su': 'sudanese', 'sw': 'swahili', 'sv': 'swedish',
                         'tg': 'tajik', 'ta': 'tamil', 'te': 'telugu', 'th': 'thai', 'tr': 'turkish', 'uk': 'ukrainian', 'ur': 'urdu', 'uz': 'uzbek', 'vi': 'vietnamese', 'cy': 'welsh', 'yi': 'yiddish', 'yo': 'yoruba', 'zu': 'zulu'}
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

        log('UTILS :: {0:<29} {1}'.format('Run Translation', msg))

        if runTranslation == 'Yes':
            if language is not None:
                try:
                    myString = translator.translate(myString, language)
                    myString = saveString if myString is None else myString
                    log('UTILS :: %s Text: %s', 'Untranslated' if myString == saveString else 'Translated', myString)
                except Exception as e:
                    log('UTILS :: Error Translating Text: %s', e)
            else:
                log('UTILS :: {0:<29} {1}'.format('Translation Skipped', plexLibLanguageCode))

    myString = myString if myString else ' ' # return single space to initialise metadata summary field
    return myString