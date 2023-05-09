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
    19 Dec 2022     Roman Numeral and Title Matching, corrections
                    Add Director and Cast Nationalities to Country Metadata
    29 Dec 2022     Correction to Poster/Art images - Scene Agents cropped images were not been saved to metadata
                    Queerclick - managed to determine cast from other tags.... will need further testing
    06 Jan 2023     Allow scrape to continue if poster/art processing fails
    22 Jan 2023     ~ in filename on disk is a marker for / in film title on website
                    processing preferences plist file for MAC OS
                    Correction to setup scraping code
    29 Jan 2023     Check for UserGayTidy - if missing continue processing. This is because I provide the file as _UserGayTidy so as not to overwrite other users customised files
    03 Feb 2023     if curly quotes and ` are found in film title replace with straight quotes
                    changes to homoactive code - was retrieving countries as genre
    08 Feb 2023     BEP - filtered out all non jpg from image list retrieved for posters and art
                    art image = poster image if only 1 image retrieved - change made after error in queerclick realised
                    castlist for processing corrected - elements that were substrings of other elements wer being picked rather than kept i.e. "Leo" over "Leo Rocha"
                    fixed code to sort out replacing roman numerals with arabic ones
    11 Feb 2023     Improved logging in START section to identify invalid entries in usergaytidy.txt and indented entries and identify operating system
                    added UserGenres.txt file to hold user configured genres
    19 Feb 2023     Standardised the use of cast added to filename for all agents
                    corrected errors in HFGPM
                    All agents now extract genres and countries from the synopsis as standard
                    Warnings now gave in scene agent if tidied genre not set, Studios can also be given a tidied genre
    23 Feb 2023     Improve genre/country retrieval from synopsis
    26 Feb 2023     Restrict IAFD search string to 72 Characters
    08 Mar 2023     Error in getting images BEP
    15 Apr 2023     Dealt with ² in titles as not used in IAFD titles
    27 Apr 2023     Improved code to retrieve cast from tags in WayBig, Fagalicious and QueerClick
    03 May 2023     Correction to tag processing in WayBig, Fagalicious and QueerClick
                    Standardise Quotes and Hyphens for matching between filenames and web entries
                    Remove Thumbor from preferences and put in Thumbor.txt file in _PGMA
    07 May 2023     Colour sets for Genre icons introduced
    '''
# ----------------------------------------------------------------------------------------------------------------------------------
import cloudscraper, fake_useragent, os, platform, plistlib, random, re, requests, subprocess, time, unicodedata
from datetime import datetime, timedelta
from collections import OrderedDict
from unidecode import unidecode
from urlparse import urlparse
from textwrap import wrap
from io import BytesIO
from PIL import Image

# IAFD Related variables
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/ramesearch.asp?searchtype=comprehensive&searchstring={0}'
IAFD_FILTER = '&FirstYear={0}&LastYear={1}&Submit=Filter'
IAFD_ABSENT = u'\U0000274C'        # red cross mark - not on IAFD
IAFD_FOUND = u'\U00002705'         # heavy white tick on green - on IAFD
BISEXUAL = u'\U000026A5'           # ⚥ - bisexual films
HOMOSEXUAL =  u'\U000026A5'        # ⚣ - gay films
HETEROSEXUAL = u'\U000026A4'       # ⚤ - straight films
NOBREAK_HYPHEN = u'\U00002011'     # Non Breaking Hyphen
NOBREAK_SPACE = u'\U000000A0'      # Non Breaking Space
EN_SPACE = u'\U00002002'           # Non Breaking Space
THIN_SPACE = u'\U00002009'         # Thin Space (Non-Breaking)
MONTHS = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}

# Plex System Variables/Methods
PlexSupportPath = Core.app_support_path
PlexLoadFile = Core.storage.load
PlexSaveFile = Core.storage.save

# log section separators
LOG_BIGLINE = '-' * 140
LOG_SUBLINE = '      ' + '-' * 100
LOG_ASTLINE = '*' * 140

# getHTTPRequest variable
scraper = None
# ----------------------------------------------------------------------------------------------------------------------------------
def delay():
    delayList = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
    delay = random.choice(delayList)
    return delay

# ----------------------------------------------------------------------------------------------------------------------------------
def findTidy(myItem):
    myItem = makeASCII(myItem.lower())
    myItem = TIDYDICT.get(myItem, '')
    myItem = None if myItem == 'x' else myItem
    return myItem

# ----------------------------------------------------------------------------------------------------------------------------------
def getCast(agntCastList, FILMDICT):
    ''' Process and match cast list against IAFD '''

    if not agntCastList and 'Cast' not in FILMDICT: # nowt to do
        raise Exception('< No Cast Found! >')

    # clean up the Cast List make a copy then clear
    agntCastList = [x.split('(')[0].strip() if '(' in x else x.strip() for x in agntCastList]
    agntCastList = sorted({String.StripDiacritics(x) for x in agntCastList if x})
    log('UTILS :: {0:<29} {1}'.format('Agent Cast List', '{0:>2} - {1}'.format(len(agntCastList), agntCastList)))

    # keep elements that are not a substring of another element
    tempList = agntCastList[:]
    for elem in tempList:
        agntCastList = [x for x in agntCastList if (x == elem) or (x not in elem)]    

    log('UTILS :: {0:<29} {1}'.format('Substrings Removed', '{0:>2} - {1}'.format(len(agntCastList), agntCastList)))

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
def getFilmImages(imageType, imageLocation, whRatio):
    ''' Only for Scene Agents: get Film images - posters/background art and crop if necessary '''
    Thumbor = THUMBOR + "/0x0:{0}x{1}/{2}"
    vbScript = os.path.join(PlexSupportPath, 'Plug-ins', '{0}.bundle'.format(AGENT), 'Contents', 'Code', 'ImageCropper.vbs')
    Cropper = r'CScript.exe "{0}" "{1}" "{2}" "{3}"'

    imageContent = HTTP.Request(imageLocation).content
    myImage = Image.open(BytesIO(imageContent))
    width, height = myImage.size
    dispWidth = '{:,d}'.format(width)       # thousands separator
    dispHeight = '{:,d}'.format(height)     # thousands separator

    log('UTILS :: {0} Found: Width ({1}) x Height ({2}); URL: {3}'.format(imageType, dispWidth, dispHeight, imageLocation))

    maxHeight = float(width * whRatio)      # Maximum allowable height

    cropHeight = float(maxHeight if maxHeight <= height else height)
    cropWidth = float(cropHeight / whRatio)

    DxHeight = 0.0 if cropHeight == height else (abs(cropHeight - height) / height) * 100.0
    DxWidth = 0.0 if cropWidth == width else (abs(cropWidth - width) / width) * 100.0

    cropRequired = True if DxWidth >= 15 or DxHeight >=15 else False
    cropWidth = int(cropWidth)
    cropHeight = int(cropHeight)
    desiredWidth = '{0:,d}'.format(cropWidth)     # thousands separator
    desiredHeight = '{0:,d}'.format(cropHeight)   # thousands separator
    DxWidth = '{0:>2}'.format(DxWidth)    # percent format
    DxHeight = '{0:>2}'.format(DxHeight)  # percent format
    log('UTILS :: Crop {0} {1}: Actual (w{2} x h{3}), Desired (w{4} x h{5}), % Dx = w[{6}%] x h[{7}%]'.format("Required:" if cropRequired else "Not Required:", imageType, dispWidth, dispHeight, desiredWidth, desiredHeight, DxWidth, DxHeight))
    if cropRequired:
        try:
            imageLocation = Thumbor.format(cropWidth, cropHeight, imageLocation)
            log('UTILS :: Thumbor - Crop Image: {0}'.format(imageLocation))
            log('UTILS ::   Desired Dimensions: {0} x {1}'.format(desiredWidth, desiredHeight))
            imageContent = HTTP.Request(imageLocation).content

        except Exception as e:
            log('UTILS :: Error Thumbor Failed to Crop Image to: {0} x {1}: {2} - {3}'.format(desiredWidth, desiredHeight, imageLocation, e))
            if os.name == 'nt':
                try:
                    envVar = os.environ
                    TempFolder = envVar['TEMP']
                    imageLocation = os.path.join(TempFolder, imageLocation.split("/")[-1])
                    PlexSaveFile(imageLocation, imageContent)
                    cmd = Cropper.format(vbScript, imageLocation, cropWidth, cropHeight)
                    log('UTILS ::')
                    log('UTILS :: Script - Crop Image: {0}'.format(imageLocation))
                    log('UTILS ::  Desired Dimensions: {0} x {1}'.format(desiredWidth, desiredHeight))
                    log('UTILS ::        Command Line: {0}'.format(cmd))
                    subprocess.call(cmd)
                    time.sleep(2)
                    imageContent = PlexLoadFile(imageLocation)
                except Exception as e:
                    log('UTILS :: Error Script Failed to Crop Image to: {0} x {1}: {2} - {3}'.format(desiredWidth, desiredHeight, imageLocation, e))

    return imageLocation, imageContent

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
                pattern = ' \(X{0,1}(?:V?I{0,3}I[VX])\)$'
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
                    pattern = ' \(X{0,1}(?:V?I{0,3}I[VX])\)$'
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
            if FILMDICT['Agent'] == 'IAFD':
                log(LOG_BIGLINE)
                log('UTILS :: Access External Links in IAFD:')
                externalIAFDSites = {'AdultEmpire': 'GayEmpire', 'HotMovies': 'GayHotMovies', 'CD Universe': 'CDUniverse'}
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
                        xSiteHTML = HTML.ElementFromURL(value, timeout=60, errors='ignore', sleep=delay())
                        # xhtml = HTML.ElementFromURL(value, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36"},timeout=60, errors='ignore', sleep=delay())
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
                if FILMDICT['Agent'] == 'IAFD':
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
        headers['User-Agent'] = (fake_useragent.UserAgent(fallback=HTTP.Headers['User-Agent'])).random

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

        time.sleep(random.randint(1, 7))
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
def getIAFDArtist(artistURL):
    # get artist country of origin
    artist = {}
    artistRealName = ''
    artistPhoto = ''
    artistNationality = ''
    artistBirthNationality = ''
    artistAwards = []
    artistBio = {'IAFD URL': artistURL}

    try:
        artistType = 'Director' if 'gender=d' in artistURL else 'Cast'
        ahtml = getURLElement(artistURL)
        ahtmlBio = ahtml.xpath('//*[@class="bioheading"]')
        xpath = '//table[@id="{0}"]/tbody/tr[position()<=15]'.format('directoral' if artistType == 'Director' else 'personal')
        ahtmlFilms = ahtml.xpath(xpath)

        artistRealName = ahtml.xpath('//h1/text()[normalize-space()]')[0].strip()
        artistPhoto = ahtml.xpath('//div[@id="headshot"]/img/@src')[0].strip()
        if 'nophoto' in artistPhoto and artistType == 'Director':               # if no photo check if he has a performer page
            try:
                bhtml = getURLElement(artistURL.replace('gender=d', 'gender=m'))
                artistPhoto = bhtml.xpath('//div[@id="headshot"]/img/@src')[0].strip()
                if not re.search(r'(?:jpg|jpeg|png|gif|bmp|webp)$', artistPhoto, re.IGNORECASE):
                    artistPhoto = ''

            except Exception as e:
                log('UTILS :: Error getting Director Photo from "As Performer" Details Page: %s', e)

    except Exception as e:
        log('UTILS :: Error getting Artist Details Page: %s', e)

    try:
        for item in ahtmlBio:
            bioheading = ' '.join(item.text.split()).replace('Color', 'Colour')
            biodata = item.xpath('./following-sibling::*[@class="biodata"][1]//text()')
            biodata = ' '.join(biodata)
            biodata = re.sub('\s', ' ', biodata).strip()                                # replace all whitespace with actual space
            biodata = re.sub('\(\s*details\s*\)', '', biodata).strip()                  # replace all links with null

            if re.search(r'No Data|None|No Known', biodata, re.IGNORECASE) or not biodata:
                continue

            if re.search(r'Nationality', bioheading, re.IGNORECASE):                    # tidy the nationality
                artistNationality = ''
                tempNations = [x.strip() for x in biodata.split(',') if x.strip()]
                nations = set()
                for idx, item in enumerate(tempNations):
                    tidyItem = findTidy(item)
                    if tidyItem is None:        # Don't process
                        continue
                    if tidyItem not in COUNTRYSET:
                        continue
                    nations.add(tidyItem)

                # pick first nationality
                nations = list(nations)
                nations.sort(key = lambda x: x.lower())
                artistNationality = nations[0] if nations else ''

                biodata = ', '.join(nations)                                            # list of nations as nationality
                artistBio[bioheading] = biodata

            elif re.search(r'Birthplace', bioheading, re.IGNORECASE):                   # Birthplace format = town, state, country
                artistBirthNationality = ''
                tempNations = [x.strip() for x in biodata.split(',') if x.strip()]
                nations = set()
                for idx, item in enumerate(tempNations):
                    tidyItem = findTidy(item)
                    if tidyItem is None:        # Don't process
                        continue
                    if tidyItem not in COUNTRYSET:
                        continue
                    nations.add(tidyItem)

                # pick first nationality
                nations = list(nations)
                nations.sort(key = lambda x: x.lower())
                artistBirthNationality = nations[0] if nations else ''

                artistBio[bioheading] = biodata

            elif biodata.count('/') == 2:                                               # date format mm/dd/yyyy convert to mmm dd, yyyy - cater for years such as 19??
                try:
                    m, d, y = biodata.split('/')
                    biodata = '{0} {1}, {2}'.format(MONTHS[int(m)], d, y)
                except:
                    pass
                artistBio[bioheading] = biodata

            elif re.search(r'kg', biodata, re.IGNORECASE):                              # weight
                biodataList = [int(x) for x in re.findall(r'\d+', biodata)]
                usImperialWeight = '{0} lbs'.format(biodataList[0])
                ukImperialStones, ukImperialLbs = divmod(biodataList[0], 14)
                ukImperialWeight = "{0} st {1}".format(ukImperialStones, '{0} lbs'.format(ukImperialLbs) if ukImperialLbs else '').strip()
                metricWeight = '{0} Kgs'.format(biodataList[1])
                biodata = '{0} ({1} / {2})'.format(metricWeight, ukImperialWeight, usImperialWeight)
                artistBio[bioheading] = biodata

            elif re.search(r'feet', biodata, re.IGNORECASE):                            # height
                biodataList =  [int(x) for x in re.findall(r'\d+', biodata)]
                metricHeight = '{0} cms'.format(biodataList[2])
                imperialHeight = "{0}'{1}".format(biodataList[0], '{0}"'.format(biodataList[1]) if biodataList[1] else '').strip()
                biodata = '{0} ({1})'.format(metricHeight, imperialHeight)
                artistBio[bioheading] = biodata

            elif re.search(r'award|gayvn', bioheading, re.IGNORECASE) or re.search(r'nominee', biodata, re.IGNORECASE):
                award = '{0} - {1}'.format(bioheading, biodata)
                award = re.sub(r'\s+', NOBREAK_SPACE, award).replace('-', NOBREAK_HYPHEN)
                award = award.ljust(100)[:100] + ' '
                artistAwards.append(award)

            else:
                artistBio[bioheading] = biodata

            artistNationality = artistNationality if artistNationality else artistBirthNationality
            artistAwards.sort(key = lambda x: x.lower())

            # ALL AKA entries put in a simplified AKA Header
            akas = ''
            for key in artistBio.keys():
                if re.search(r'AKA', key, re.IGNORECASE):
                    akas = '{0},{1}'.format(akas, artistBio[key])
            if akas:
                akas = akas.split(',')
                akas = [x.strip() for x in akas if x.strip()]
                akas = list(set(akas))
                akas = ', '.join(akas)
                for key in artistBio.keys():
                    if re.search(r'AKA', key, re.IGNORECASE):
                        del artistBio[key]
                artistBio['AKA'] = akas

        artistFilms = []
        for artistFilm in ahtmlFilms:
            artistFilmLine = artistFilm.xpath('./td//text()')
            if artistType == 'Director':
                artistFilmStudio = re.sub('.com|.net|.org|.tv|\(\s*\)', '', artistFilmLine[2], re.IGNORECASE).strip()       # remove internet domains and bracketed information
                artistFilmTitle = artistFilmLine[0]
                artistFilmYear = artistFilmLine[3]
            else:
                artistFilmStudio = re.sub('.com|.net|.org|.tv|\(\s*\)', '', artistFilmLine[2], re.IGNORECASE).strip()       # remove internet domains and bracketed information
                artistFilmStudio = artistFilmStudio.split('(')[-1].replace(')', '')
                artistFilmTitle = artistFilmLine[0]
                artistFilmYear = artistFilmLine[1]

            film = '({0}) - {1} ({2})'.format(artistFilmStudio, artistFilmTitle, artistFilmYear)
            film = re.sub(r'\s+', NOBREAK_SPACE, film).replace('-', NOBREAK_HYPHEN)
            film = film.ljust(100)[:100] + ' '
            artistFilms.append(film)

            artistFilms.sort(key = lambda x: x.lower())

    except Exception as e:
        log('UTILS :: Error processing Artist Details Page: %s', e)
        artist = {'Awards': [], 'Bio': {}, 'Films': [], 'Photo': '', 'Nationality': '', 'RealName': ''}

    else:
        artist = {'Awards': artistAwards, 'Bio': artistBio, 'Films': artistFilms, 'Photo': artistPhoto, 'Nationality': artistNationality, 'RealName': artistRealName}

    return artist
# -------------------------------------------------------------------------------------------------------------------------------
def getImage(imageLocation, entry, picType):
    ''' Used for getting flag images, actors and directors pictures - Deceased Actors/Directors shown in GrayScale'''

    imageContent = None
    fileOnDisk = False if 'http' in imageLocation else True
    if not fileOnDisk:
        imageLocation = imageLocation.replace(' ', '%20').strip()
        ImageContent = HTTP.Request(imageLocation).content
        myImage = Image.open(BytesIO(ImageContent))
        width, height = myImage.size
        width = int(width)
        height = int(width * 1.5)

    log('UTILS :: {0:<29} {1}'.format('Location', 'On Disk' if fileOnDisk else 'On Web'))

    # Countries & System - IAFD, Stacked, Agent are stored on disk, AND posters under _PGMA + Agent.jpg
    if fileOnDisk:
        log('UTILS :: {0:<29} {1}'.format('{0} Image Location'.format(picType), imageLocation))
        imageContent = PlexLoadFile(imageLocation)

    # Cast from IAFD
    elif COLCAST in entry:
        if '[d]' in entry:
            imageLocation = r'{0}/{1}x{2}/filters:stretch():grayscale()/{3}'.format(THUMBOR, width, height, imageLocation)
        else:
            imageLocation = r'{0}/{1}x{2}/filters:stretch()/{3}'.format(THUMBOR, width, height, imageLocation)

        imageContent = HTTP.Request(imageLocation).content
        log('UTILS :: {0:<29} {1}'.format('{0}Cast {1} Image URL'.format('Deceased ' if '[d]' in entry else '', picType), imageLocation))

    # Directors from IAFD - GrayScale + Watermark if deceased else just Watermark
    elif COLDIRECTOR in entry:
        if '[d]' in entry:
            imageLocation = r'{0}/{1}x{2}/filters:stretch():grayscale():watermark({3},1,1,0)/{4}'.format(THUMBOR, width, height, WATERMARK, imageLocation)
        else:
            imageLocation = r'{0}/{1}x{2}/filters:stretch():watermark({3},1,1,0)/{4}'.format(THUMBOR, 128, 192, WATERMARK, imageLocation)

        imageContent = HTTP.Request(imageLocation).content
        log('UTILS :: {0:<29} {1}'.format('{0}Director {1} Image URL'.format('Deceased ' if '[d]' in entry else '', picType), imageLocation))

    # all other internet images need to be ratio wxh = 1x1.5
    else:
        ImageContent = HTTP.Request(imageLocation).content
        ImageInfo = Image.open(BytesIO(ImageContent))
        width, height = ImageInfo.size
        height = int(width * 1.5)
        imageLocation = r'{0}/fit-in/{1}x{2}/{3}'.format(THUMBOR, width, height, imageLocation)
        imageContent = HTTP.Request(imageLocation).content
        log('UTILS :: {0:<29} {1}'.format('{0} Genre Image URL'.format(picType), imageLocation))

    return imageContent

# -------------------------------------------------------------------------------------------------------------------------------
def getRecordedCast(html):
    ''' retrieve film cast from IAFD film page'''
    filmCast = {}
    try:
        castList = html.xpath('//div[@class[contains(.,"castbox")]]/p')
        log('UTILS :: {0:<29} {1:>2}'.format('Cast on IAFD', len(castList)))
        for cast in castList:
            castName = cast.xpath('./a/text()[normalize-space()]')[0].strip()
            castName = 'Unknown Actor' if 'Unknown' in castName else castName
            castURL = IAFD_BASE + cast.xpath('./a/@href')[0].strip()

            # cast roles are sometimes not filled in
            try:
                castRole = cast.xpath('./text()[normalize-space()]')
                castRole = ' '.join(castRole).replace('DVDOnly','').strip()
            except:
                castRole = ''

            # cast alias in current film may be missing
            try:
                castAlias = cast.xpath('./i/text()')[0].split(':')[1].replace(')', '').strip()
                castAlias = castAlias.replace(' or ', ',').split(',')
                castAlias = ', '.join(castAlias)
            except:
                castAlias = ''

            # get cast biography and filmography etc
            castDetails = getIAFDArtist(castURL)
            castAwards = castDetails['Awards']
            castBio = castDetails['Bio']
            castFilms = castDetails['Films']
            castNationality = castDetails['Nationality']
            castPhoto = castDetails['Photo']
            castRealName = castDetails['RealName']

            castCompareName = re.sub(r'[\W\d_]', '', castName).strip().lower()
            castCompareAlias = re.sub(r'[\W\d_]', '', castAlias).strip().lower()
            castRole = castRole if castRole else 'AKA: {0}'.format(castAlias) if castAlias else IAFD_FOUND

            # log cast details
            log('UTILS :: {0:<29} {1}'.format('Recorded Cast Details:', ''))
            log('UTILS :: {0:<29} {1}'.format('Cast Real Name', castRealName))
            log('UTILS :: {0:<29} {1}'.format('Cast Alias', castAlias if castAlias else 'No Cast Alias Recorded'))
            log('UTILS :: {0:<29} {1}'.format('Cast Awards', castAwards))
            log('UTILS :: {0:<29} {1}'.format('Cast Bio', castBio))
            log('UTILS :: {0:<29} {1}'.format('Cast Films', castFilms))
            log('UTILS :: {0:<29} {1}'.format('Cast Name', castName))
            log('UTILS :: {0:<29} {1}'.format('Cast Nationality', castNationality))
            log('UTILS :: {0:<29} {1}'.format('Cast Photo', castPhoto))
            log('UTILS :: {0:<29} {1}'.format('Cast Role', castRole))
            log('UTILS :: {0:<29} {1}'.format('Cast URL', castURL))
            log(LOG_SUBLINE)

            # Assign values to dictionary
            filmCast[castName] = {'Alias': castAlias, 'Awards': castAwards,'Bio': castBio, 'CompareName': castCompareName, 'CompareAlias': castCompareAlias, 
                                  'Films': castFilms, 'Nationality': castNationality, 'Photo': castPhoto, 'RealName': castRealName, 'Role': castRole, 'URL': castURL}

    except Exception as e:
        log('UTILS :: Error: Processing IAFD Film Cast: %s', e)

    return filmCast

# -------------------------------------------------------------------------------------------------------------------------------
def getRecordedDirectors(html):
    ''' retrieve directors from IAFD film page'''
    filmDirectors = {}
    try:
        directorList = html.xpath('//p[@class="bioheading" and text()="Directors"]//following-sibling::p[1]/a')
        log('UTILS :: {0:<29} {1:>2}'.format('Directors on IAFD', len(directorList)))
        for director in directorList:
            directorName = director.xpath('./text()')[0]
            directorURL = director.xpath('./@href')[0]

            # get director biography and filmography etc
            directorDetails = getIAFDArtist(directorURL)
            directorAwards = directorDetails['Awards']
            directorBio = directorDetails['Bio']
            directorFilms = directorDetails['Films']
            directorNationality = directorDetails['Nationality']
            directorPhoto = directorDetails['Photo']
            directorRealName = directorDetails['RealName']

            directorCompareName = re.sub(r'[\W\d_]', '', directorName).strip().lower()

            log('UTILS :: {0:<29} {1}'.format('Recorded Director Details:', ''))
            log('UTILS :: {0:<29} {1}'.format('Director Awards', directorAwards))
            log('UTILS :: {0:<29} {1}'.format('Director Bio', directorBio))
            log('UTILS :: {0:<29} {1}'.format('Director Films', directorFilms))
            log('UTILS :: {0:<29} {1}'.format('Director Name', directorName))
            log('UTILS :: {0:<29} {1}'.format('Director Nationality', directorNationality))
            log('UTILS :: {0:<29} {1}'.format('Director Photo', directorPhoto))
            log('UTILS :: {0:<29} {1}'.format('Director Real Name', directorRealName))
            log('UTILS :: {0:<29} {1}'.format('Director URL', directorURL))
            log(LOG_SUBLINE)

            # Assign values to dictionary
            filmDirectors[directorName] = {'Alias': '', 'Awards': directorAwards, 'Bio': directorBio, 'CompareName': directorCompareName, 'CompareAlias': '', 'Films': directorFilms, 
                                           'Nationality': directorNationality, 'RealName': directorRealName, 'Photo': directorPhoto, 'URL': directorURL}

    except Exception as e:
        log('UTILS :: Error Processing IAFD Film Director(s): %s', e)

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
                   ' << ({0}) - {1} ({2}) >> '.format(FILMDICT['Studio'], FILMDICT['Title'], FILMDICT['Year']),
                   ' << {0} >> '.format(FILMDICT['FilmURL'] if kwFilmURL is None else kwFilmURL)]
    for header in listHeaders:
        log('UTILS :: %s', header.center(131, '*'))

    log('UTILS ::')

    if myAgent == 'AdultFilmDatabase':
        siteInfoDict = getSiteInfoAdultFilmDatabase(FILMDICT, **kwargs)
    elif myAgent == 'AEBN':
        siteInfoDict = getSiteInfoAEBN(FILMDICT, **kwargs)
    elif myAgent == 'AVEntertainments':
        siteInfoDict = getSiteInfoAVEntertainments(FILMDICT, **kwargs)
    elif myAgent == 'BestExclusivePorn':
        siteInfoDict = getSiteInfoBestExclusivePorn(FILMDICT, **kwargs)
    elif myAgent == 'CDUniverse':
        siteInfoDict = getSiteInfoCDUniverse(FILMDICT, **kwargs)
    elif myAgent == 'GayEmpire':
        siteInfoDict = getSiteInfoGayEmpire(FILMDICT, **kwargs)
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
    listFooters = [' >> {0}: Site Information Retrieved << '.format(myAgent),
                   ' >> ({0}) - {1} ({2}) << '.format(FILMDICT['Studio'], FILMDICT['Title'], FILMDICT['Year']),
                   ' >> {0} << '.format(FILMDICT['FilmURL'] if kwFilmURL is None else kwFilmURL)]
    for footer in listFooters:
        log('UTILS :: %s', footer.center(131, '*'))

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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} - {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//a[contains(@href,"&cf=")]/span/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in COUNTRYSET:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

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
                log('UTILS :: {0:<29} {1}'.format('Images:', htmlimages))
                poster = [htmlimages[0]]
                art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
                log('UTILS :: {0:<29} {1}'.format('Poster', poster))
                log('UTILS :: {0:<29} {1}'.format('Art', art))

            except Exception as e:
                poster = []
                art = []
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
def getSiteInfoAEBN(FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'AEBN'
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} - {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
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
                htmlsexacts = html.xpath('//a[contains(@href,"sexActFilters")]/text()') # use sex acts as genres
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
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in COUNTRYSET:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

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
            htmlimages = [x.replace('=293', '=1000') for x in htmlimages]
            htmlimages = ['http:{0}'.format(x) if 'http:' not in x else x for x in htmlimages]
            log('UTILS :: {0:<29} {1}'.format('Images:', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        scenesDict = {'Link': filmURL}
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
                            log('UTILS :: Warning: No Review Source (Used Film Title)')

                        log('UTILS :: {0:<29} {1}'.format('Review Source', '{0} - {1}'.format(mySource, reviewSource) if reviewSource else 'None Recorded'))

                    except Exception as e:
                        log('UTILS :: Error getting Review Source (Cast): %s', e)

                    # Review Author - composed of Settings
                    reviewAuthor = 'AEBN'
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
                            tidyItem = findTidy(item)
                            log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))
                            if tidyItem is None:
                                continue
                            mySet.add(tidyItem if tidyItem else item)

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
                    scenesDict[str(sceneNo)] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText}
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
                    chaptersDict[str(sceneNo)] = {'Title': chapterTitle, 'StartTime': chapterStartTime, 'EndTime': chapterEndTime}

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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} - {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Category"]/following-sibling::span/a/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in COUNTRYSET:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

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
        siteInfoDict['Compilation'] = compilation if kwCompilation is None else kwCompilation

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
            poster = [htmlimage.replace('bigcover', 'jacket_images')]     # replace text of dvd cover url to get poster
            art = [htmlimage.replace('bigcover', 'screen_shot')]          # replace text of dvd cover url to get background
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Genre: ")]')[0].strip().replace('Genre: ', '')
            htmlgenres = htmlgenres.split(',')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                genresSet.add(tidyItem if tidyItem else item)

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
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue
                
                countriesSet.add(tidyItem)

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
            htmlimages = [x for x in htmlimages if 'jpg' in x]
            log('UTILS :: {0:<29} {1}'.format('Images:', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
            poster = [htmlimages[0]]

            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//td[text()="Category"]/following-sibling::td/a/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in COUNTRYSET:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

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
            poster = [html.xpath('//img[@id="PIMainImg"]/@src')[0]]
            art = [html.xpath('//img[@id="0"]/@src')[0]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info - CDUniverse retains actually reviews - so collect these rather than setting up scenes and chapters
        log(LOG_SUBLINE)
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        scenesDict = {'Link': filmURL}
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
                            log('UTILS :: Warning: No Review Source (Used Film Title)')

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
                    scenesDict[str(sceneNo)] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText}

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

            regex = ur'– Get the .*|– Download the .*|– Watch .*|– Check out .*'
            pattern = re.compile(regex, re.IGNORECASE)
            synopsis = re.sub(pattern, '', synopsis).strip()

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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
            log('UTILS :: No Cast List on Agent: Built From Tag List')
            siteInfoDict['Cast'] = []

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Tag List: Genres, Cast and possible Countries, Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        castSet = {x.strip() for x in FILMDICT['FilenameCast']}
        log('UTILS :: {0:<29} {1}'.format('FileName Cast', '{0}'.format(castSet)))

        tempCastSet = {x.strip().replace(' ', '') for x in FILMDICT['FilenameCast']}
        testStudio = [FILMDICT['Studio'].lower().replace(' ', ''), FILMDICT['CompareStudio']]
        try:
            htmltags = html.xpath('//ul/a[contains(@href, "https://fagalicious.com/tag/")]/text()')
            htmltags = [x.strip() for x in htmltags if x.strip()]
            htmltags = [x for x in htmltags if not 'compilation' in x.lower()]
            htmltags = [x for x in htmltags if not 'movie' in x.lower()]
            htmltags = [x for x in htmltags if not 'series' in x.lower()]
            htmltags = [x for x in htmltags if not '.tv' in x.lower()]
            htmltags = [x for x in htmltags if not '.com' in x.lower()]
            htmltags = [x for x in htmltags if not '.net' in x.lower()]
            htmltags = [x for x in htmltags if not x.lower().replace(' ', '') in testStudio]

            # remove all tags with non name characters such as colons
            htmltags = [setDashesQuotes(x) for x in htmltags]
            htmltags = [x for x in htmltags if not ':' in x]
            htmltags = [x for x in htmltags if not x + ':' in FILMDICT['Title']]
            htmltags = list(set(htmltags))
            htmltags.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Tags', '{0:>2} - {1}'.format(len(htmltags), htmltags)))
            for idx, item in enumerate(htmltags, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))
                if tidyItem is None:                                      # If none skip
                    continue
                elif tidyItem:                                            # gayTidy returned an item
                    if tidyItem.lower() in GENRESDICT:                    # check if genre
                        genresSet.add(tidyItem)
                    elif tidyItem in COUNTRYSET:                          # check if country
                        countriesSet.add(tidyItem)
                    else:
                        log('UTILS :: {0:<29} {1}'.format('Warning', 'Tidied Item is neither Country nor Genre'))
                else:                                                     # tag is most probably cast
                    castSet.add(item)

            showSetData(genresSet, 'Genres (set*)')
            showSetData(countriesSet, 'Countries (set*)')
            showSetData(castSet, 'Cast (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Tags: Genres/Countries/Cast/Compilation: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Cast'] = sorted(castSet)
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
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]

            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
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
def getSiteInfoGayEmpire(FILMDICT, **kwargs):
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} - {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//ul[@class="list-unstyled m-b-2"]//a[@label="Category"]/text()[normalize-space()]')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in COUNTRYSET:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   6.  Release Date - GayEmpire Format = mmm dd YYYY
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

        #   7.  Duration - GayEmpire Format = h hrs. m mins.
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
        try:
            # some films do not have a back cover - so replace with poster
            htmlimages = html.xpath('//img[@itemprop="image"]/@src')
            poster = [htmlimages[0]] if htmlimages else []
            htmlimages = html.xpath('//a[@id="back-cover"]/@href')
            art = [htmlimages[0]] if htmlimages else []         # empty list if nowt found
            art = [poster[0]] if not art and poster else art    # use poster element if empty

            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info
        log(LOG_SUBLINE)
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        scenesDict = {'Link': filmURL}
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

                    # Review Source - GayEmpire has no Cast List per Scene, use iafd scenes cast or Film title in that order of preference
                    reviewSource = '{0}. {1}...'.format(sceneNo, FILMDICT['Title'])
                    mySource = 'N/A'
                    log('UTILS :: Warning: No Review Source (Used Film Title)')
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
                    scenesDict[str(sceneNo)] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText}

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
                    chaptersDict[str(sceneNo)] = {'Title': chapterTitle, 'StartTime': chapterStartTime, 'EndTime': chapterEndTime}

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
            htmlsynopsis = html.xpath('//article//text()')
            htmlsynopsis = ' '.join(htmlsynopsis)
            htmlsynopsis = re.sub('<[^<]+?>', '', htmlsynopsis).strip()

            regex = r'The movie you are enjoying was created by consenting adults.*'
            pattern = re.compile(regex, re.DOTALL | re.IGNORECASE)
            htmlsynopsis = re.sub(pattern, '', htmlsynopsis)

            regex = r'This title ships*'
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
            htmldirectors = html.xpath('//a[@label="Director"]/text()[normalize-space()]')
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
            try:
                htmlcast = html.xpath('//a[@label="Performer"]/text()[normalize-space()]')
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
            htmlcollections = html.xpath('//strong[text()="Series:"]/following-sibling::text()[1]')[0].strip()
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            collections = list(set(htmlcollections))
            collections.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} - {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//a[@label="Category"]/text()[normalize-space()]')
            genres = list(set(htmlgenres))
            genres = [x.strip() for x in genres if x.strip()]
            genres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(genres), genres)))
            compilation = 'Yes' if 'Compilation' in genres else 'No'
            for idx, item in enumerate(genres, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in COUNTRYSET:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

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
                htmlproductionyear = html.xpath('//strong[text()="Release Year:"]/following-sibling::text()[1]')[0].strip()
                htmlproductionyear = '{0}1231'.format(htmlproductionyear)
                htmlproductionyear = datetime.strptime(htmlproductionyear, '%Y%m%d')
                siteInfoDict['ReleaseDate'] = htmlproductionyear
                log('UTILS :: {0:<29} {1}'.format('Production Date', htmlproductionyear.strftime('%Y-%m-%d')))

            except Exception as e:
                htmlproductionyear = ''
                log('UTILS :: Warning, No Production Year: %s', e)

            try:
                htmldate = html.xpath('//strong[text()="Released:"]/following-sibling::text()[1]')[0].strip()
                htmldate = datetime.strptime(htmldate, '%b %d %Y')
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
                htmlduration = html.xpath('//strong[text()="Run Time: "]/following-sibling::text()[1]')[0].strip()
                htmlduration = htmlduration.replace(' hrs.', '').replace(' mins.', '').split()
                htmlduration = [int(x) for x in htmlduration if x.strip()]
                htmlduration = htmlduration[0] * 3600 + htmlduration[1] * 60 if len(htmlduration) == 2 else htmlduration[0] * 60
                htmlduration = datetime.fromtimestamp(htmlduration)
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
            poster = html.xpath('//img[@label="Front Boxcover"]/@src')
            art = html.xpath('//a[@class="fancy"]/@href')

        except Exception as e:
            log('UTILS :: Error getting Images: %s', e)
            poster = []
            art = []

        finally:
            if not art and poster:
                art = [poster[0]]
            if not poster and art:
                poster = [art[0].replace('bh', 'h')]

            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        #   9.  Scene Info
        log(LOG_SUBLINE)
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        scenesDict = {'Link': filmURL}
        chaptersDict = {}
        try:
            htmlscenes = html.xpath('//a[@label="Scene Title"]')
            log('UTILS :: {0:<29} {1}'.format('Possible Number of Scenes', len(htmlscenes)))
            if len(htmlscenes) == 0:
                raise Exception ('< No Scenes Found! >')

            # scene headings format = Scene 1..2..3..
            htmltemp = html.xpath('//a[@label="Scene Title"]/text()[normalize-space()]')
            htmlheadings = [x.strip() for x in htmltemp]

            # scene durations format = 99 min
            htmltemp = html.xpath('//small[@class="badge"]/text()[normalize-space()]')
            htmldurations = [x.split()[0] for x in htmltemp]   # extract time strings

            # sum up the scenes' length: Gay Hot Movies uses xx Mins format
            scenesDelta = timedelta()
            for htmlduration in htmldurations:
                scenesDelta += timedelta(minutes=int(htmlduration))

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
                    reviewSource = '{0}. {1}...'.format(sceneNo, FILMDICT['Title'])
                    log('UTILS :: Warning: No Review Source (Used Film Title)')

                    # Review Author - composed of Settings
                    reviewAuthor = 'Gay Hot Movies'
                    log('UTILS :: {0:<29} {1}'.format('Review Author', reviewAuthor))

                    # Review Text - composed of Sexual Acts / tidy genres
                    reviewText = ''
                    log('UTILS :: {0:<29} {1}'.format('Review Text', reviewText if reviewText else 'None Recorded'))

                    # save Review - scene
                    scenesDict[str(sceneNo)] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText}

                    chapterTitle = reviewSource
                    chapterStartTime = (timeOffsetTime.hour * 60 * 60 + timeOffsetTime.minute * 60 + timeOffsetTime.second) * 1000
                    timeOffsetTime += timedelta(minutes=int(htmlduration))
                    chapterEndTime = (timeOffsetTime.hour * 60 * 60 + timeOffsetTime.minute * 60 + timeOffsetTime.second) * 1000

                    # next scene starts a second after last scene
                    timeOffsetTime += timedelta(seconds=1)

                    log('UTILS :: {0:<29} {1}'.format('Chapter', '{0} - {1}:00'.format(sceneNo, htmlduration)))
                    log('UTILS :: {0:<29} {1}'.format('Title', chapterTitle))
                    log('UTILS :: {0:<29} {1}'.format('Time', '{0} - {1}'.format(datetime.fromtimestamp(chapterStartTime/1000).strftime('%H:%M:%S'), datetime.fromtimestamp(chapterEndTime/1000).strftime('%H:%M:%S'))))

                    # save chapter
                    chaptersDict[str(sceneNo)] = {'Title': chapterTitle, 'StartTime': chapterStartTime, 'EndTime': chapterEndTime}

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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'

        siteInfoDict['Genres'] = genresSet
        siteInfoDict['Countries'] = countriesSet
        siteInfoDict['Compilation'] = compilation

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
            log('UTILS :: {0:<29} {1}'.format('Images:', images))
            poster = [images[0]]
            art = [images[0] if len(images) == 1 else images[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        siteInfoDict['Genres'] = genresSet
        siteInfoDict['Countries'] = countriesSet
        siteInfoDict['Compilation'] = compilation

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
            log('UTILS :: {0:<29} {1}'.format('Images:', images))
            poster = [images[0]]
            art = [images[0] if len(images) == 1 else images[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//span[@style=""]/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in COUNTRYSET:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

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
            log('UTILS :: {0:<29} {1}'.format('Images:', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        siteInfoDict['Genres'] = genresSet
        siteInfoDict['Countries'] = countriesSet
        siteInfoDict['Compilation'] = compilation

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
            log('UTILS :: {0:<29} {1}'.format('Images:', images))
            poster = [images[0]]
            art = [images[0] if len(images) == 1 else images[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
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
                for key in ['AEBN', 'GayEmpire', 'GayHotMovies']:
                    if key in FILMDICT and FILMDICT[key] != {}:
                        if 'Synopsis' in FILMDICT[key] and FILMDICT[key]['Synopsis']:
                            synopsis = FILMDICT[key]['Synopsis']
                            log('UTILS :: {0:<29} {1}'.format('Synopsis From', key))
                            break
            siteInfoDict['Synopsis'] = synopsis if synopsis else ''

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            # GEVI has access to external websites: AEBN, GayHotMovies, then GayEmpire
            htmldirectors = html.xpath('//a[contains(@href, "/director/")]/text()')
            htmldirectors = [x.split('(')[0].strip() for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directorsLength = len(directors)
            directors.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('GEVI Directors', '{0:>2} - {1}'.format(len(directors), sorted(directors))))
            for key in ['AEBN', 'GayHotMovies', 'GayEmpire']:
                myExternalAgentDict = FILMDICT.get(key, '')
                if myExternalAgentDict:
                    myExternalDirectors = myExternalAgentDict.get('Directors', '')
                    if myExternalDirectors:
                        log('UTILS :: {0:<29} {1}'.format('{0} Directors'.format(key), '{0:>2} - {1}'.format(len(myExternalDirectors), sorted(myExternalDirectors))))
                        directors = list(set(directors + myExternalDirectors))
                        # combine both lists and create a case insensitive List
                        combinedDirectors = list(set(directors + myExternalDirectors))
                        s = set()
                        directors = []
                        for x in combinedDirectors:
                            if x.lower() not in s:
                                s.add(x.lower())
                                directors.append(x)                        
                        directors.sort(key = lambda x: x.lower())

            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Combined Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   3.  Cast
        log(LOG_SUBLINE)
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
            try:
                # GEVI has access to external websites: AEBN, GayHotMovies, then GayEmpire
                htmlcast = html.xpath('//a[contains(@href, "/performer/")]//text()')
                htmlcast = [x.split('(')[0].strip() for x in htmlcast if x.strip()]
                cast = list(set(htmlcast))
                castLength = len(cast)
                cast.sort(key = lambda x: x.lower())
                log('UTILS :: {0:<29} {1}'.format('GEVI Cast', '{0:>2} - {1}'.format(castLength, cast)))
                for key in ['AEBN', 'GayHotMovies', 'GayEmpire']:
                    myExternalAgentDict = FILMDICT.get(key, '')
                    if myExternalAgentDict:
                        myExternalCast = myExternalAgentDict.get('Cast', '')
                        if myExternalCast:
                            log('UTILS :: {0:<29} {1}'.format('{0} Cast'.format(key), '{0:>2} - {1}'.format(len(myExternalCast), sorted(myExternalCast))))
                            # combine both lists and create a case insensitive List
                            combinedCast = list(set(cast + myExternalCast))
                            s = set()
                            cast = []
                            for x in combinedCast:
                                if x.lower() not in s:
                                    s.add(x.lower())
                                    cast.append(x)                        
                            cast.sort(key = lambda x: x.lower())

                siteInfoDict['Cast'] = cast[:]
                log('UTILS :: {0:<29} {1}'.format('Combined Cast', '{0:>2} - {1}'.format(len(cast), cast)))

            except Exception as e:
                siteInfoDict['Cast'] = []
                log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        try:
            try:
                htmlbodytypes = html.xpath('//td[contains(text(),"body types")]//following-sibling::td[1]/text()')[0].strip()           # add GEVI body type to genres
                htmlbodytypes = htmlbodytypes.replace(';', ',')
                htmlbodytypes = [x.strip() for x in htmlbodytypes.split(',') if x.strip()]
                log('UTILS :: {0:<29} {1}'.format('Body Types', '{0:>2} - {1}'.format(len(htmlbodytypes), htmlbodytypes)))

            except Exception as e:
                htmlbodytypes = []
                log('UTILS :: Error getting Body Types: %s', e)

            try:
                htmlcategories = html.xpath('//td[contains(text(),"category")]//following-sibling::td[1]/text()')[0].strip()            # add GEVI categories to genres
                htmlcategories = [x.strip() for x in htmlcategories.split(',') if x.strip()]
                log('UTILS :: {0:<29} {1}'.format('Categories', '{0:>2} - {1}'.format(len(htmlcategories), htmlcategories)))

            except Exception as e:
                htmlcategories = []
                log('UTILS :: Error getting Categories: %s', e)

            try:
                htmltypes = html.xpath('//td[contains(text(),"type")]//following-sibling::td[1]/text()')[0].strip()                     # add GEVI types
                htmltypes = htmltypes.replace(';', ',')
                htmltypes = [x.strip() for x in htmltypes.split(',') if x.strip()]
                log('UTILS :: {0:<29} {1}'.format('Types', '{0:>2} - {1}'.format(len(htmltypes), htmltypes)))

            except Exception as e:
                htmltypes = []
                log('UTILS :: Error getting Types: %s', e)

            # GEVI has access to external websites: AEBN, GayHotMovies, GayEmpire
            for key in ['AEBN', 'GayHotMovies', 'GayEmpire']:
                if key in FILMDICT and FILMDICT[key] != {}:
                    if 'Genres' in  FILMDICT[key] and FILMDICT[key]['Genres'] != set():
                        genresSet.update(FILMDICT[key]['Genres'])

            log('UTILS :: {0:<29} {1}'.format('External Genres', '{0:>2} - {1}'.format(len(genresSet), sorted(genresSet))))

            # process all genres, strip duplicates then add to genre metadata
            geviGenres = htmlbodytypes + htmlcategories + htmltypes
            log('UTILS :: {0:<29} {1}'.format('GEVI Genres', '{0:>2} - {1}'.format(len(geviGenres), geviGenres)))
            for idx, item in enumerate(geviGenres, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            log('UTILS :: {0:<29} {1}'.format('Combined Genres', '{0:>2} - {1}'.format(len(genresSet), sorted(genresSet))))
            siteInfoDict['Genres'] = genresSet

        except Exception as e:
            siteInfoDict['Genres'] = set()
            log('UTILS :: Error getting Genres: %s', e)

        #   5b.   Countries
        log(LOG_SUBLINE)
        try:
            # GEVI has access to external websites: AEBN, GayHotMovies, then GayEmpire
            for key in ['AEBN', 'GayHotMovies', 'GayEmpire']:
                if key in FILMDICT and FILMDICT[key] != {}:
                    if 'Countries' in FILMDICT[key] and FILMDICT[key]['Countries'] != set():
                        countriesSet.update(FILMDICT[key]['Countries'])

            log('UTILS :: {0:<29} {1}'.format('External Countries', '{0:>2} - {1}'.format(len(countriesSet), sorted(countriesSet))))

            htmlcountries = html.xpath('//td[text()="stats/info"]//following-sibling::td//td[text()="location"]//following-sibling::td[1]/text()')[0].strip()
            htmlcountries = [x.strip() for x in htmlcountries.split(',')]
            log('UTILS :: {0:<29} {1}'.format('GEVI Countries', '{0:>2} - {1}'.format(len(htmlcountries), htmlcountries)))
            for idx, item in enumerate(htmlcountries, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))
                if tidyItem is None:        # Don't process
                    continue

                countriesSet.add(tidyItem if tidyItem else item)

            log('UTILS :: {0:<29} {1}'.format('Combined Countries', '{0:>2} - {1}'.format(len(countriesSet), sorted(countriesSet))))
            siteInfoDict['Countries'] = countriesSet

        except Exception as e:
            siteInfoDict['Countries'] = set()
            log('UTILS :: Error getting Countries: %s', e)

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

                htmldate = min(productionDates) if productionDates else datetime.fromtimestamp(0)
                siteInfoDict['ReleaseDate'] = htmldate
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
            log('UTILS :: {0:<29} {1}'.format('Images:', images))
            poster = [images[0]]
            art = [images[0] if len(images) == 1 else images[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))
            log('UTILS :: Add External Poster/Art')

            for key in ['AEBN', 'GayEmpire', 'GayHotMovies']:
                myExternalDict = FILMDICT.get(key, '')
                if myExternalDict:
                    externalPoster = myExternalDict.get('Poster', '')
                    poster += externalPoster
                    externalArt = myExternalDict.get('Art', '')
                    art += externalArt
                    break

            log('UTILS :: {0:<29} {1}'.format('Poster - After Addition', poster))
            log('UTILS :: {0:<29} {1}'.format('Art - After Addition', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info: if GEVI Review Exists - Use by default, use chapter info from External if they Exist
        log(LOG_SUBLINE)
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        scenesDict = {'Link': filmURL}
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
                            log('UTILS :: Warning: No Review Source (Used Film Title)')

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
                    scenesDict[str(sceneNo)] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText}

                except Exception as e:
                    log('UTILS :: Error getting Scene No. %s: %s', sceneNo, e)

            # External Reviews / Scenes
            for key in ['AEBN', 'GayHotMovies', 'GayEmpire']:
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
                raise Exception('< Not Rated! >')
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
            htmlsynopsis = html.xpath('//div[@class="base fullstory"]/div[@class="maincont clr"]//div[@id]/node()')
            htmlsynopsis = [x for x in htmlsynopsis if len(x) > 1]
            tempsynopsis = '\n'.join(htmlsynopsis)
            tempsynopsis = tempsynopsis.split('\n')
            synopsisList = []
            for item in tempsynopsis:
                if 'MiB' in item or 'GiB' in item:
                    break
                synopsisList.append(item)

            synopsis = '\n'.join(synopsisList)
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
            try:
                htmlcast = html.xpath('//div[@class="base fullstory"]/div[@class="maincont clr"]//div/node()[((self::strong or self::b) and (contains(.,"Cast") or contains(.,"Actors") or contains(.,"Stars")))]/following-sibling::text()[1]')[0]
                htmlcast = htmlcast.replace(': ', '')
                htmlcast = htmlcast.split(',') 
                htmlcast = [x.strip() for x in htmlcast if x.strip() and 'n/a' not in x.lower()]
                cast = list(set(htmlcast))
                cast.sort(key = lambda x: x.lower())
                siteInfoDict['Cast'] = cast[:]
                log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

            except Exception as e:
                # HFGPM sometimes lists the cast in the first line of the synopsis separated by commas or and
                log('UTILS :: No Cast - Try and Extract from Synopsis: %s', e)
                try:
                    if siteInfoDict['Synopsis']:
                        cast = siteInfoDict['Synopsis'].split('\n')[0]
                        pattern = r', | and |\. '
                        cast = re.sub(pattern, ',', cast, flags=re.IGNORECASE)
                        cast = cast.split(',')
                        cast = [x for x in cast if len(x.split()) < 3]      # names are usually 1 or 2 words
                        cast = sorted(cast) if len(cast) > 3 else []        # assume that if there are greater than 3 elements in the list - that it is possibly a cast list
                        log('UTILS :: {0:<29} {1}'.format('Synopsis Cast', '{0:>2} - {1}'.format(len(cast), cast)))
                        siteInfoDict['Cast'] = cast
                    else:
                        siteInfoDict['Cast'] = []
                except Exception as e:
                    siteInfoDict['Cast'] = []
                    log('UTILS :: Error getting Cast: %s', e)

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
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
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            log('UTILS :: {0:<29} {1}'.format('Combined Genres', '{0:>2} - {1}'.format(len(genresSet), sorted(genresSet))))
            siteInfoDict['Genres'] = genresSet

            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Compilation'] = compilation

        #   5b.  Countries
        log(LOG_SUBLINE)
        try:
            htmlcountries = html.xpath('//div[@class="base fullstory"]/div[@class="maincont clr"]//div/node()[((self::strong or self::b) and (contains(.,"Country")))]/following-sibling::text()[1]')[0]
            htmlcountries = htmlcountries.replace(': ', '')
            htmlcountries = htmlcountries.split(',')
            htmlcountries = [x.strip() for x in htmlcountries if x.strip()]
            htmlcountries.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlcountries), htmlcountries)))
            for idx, item in enumerate(htmlcountries, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                countriesSet.add(tidyItem)

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

            log('UTILS :: {0:<29} {1}'.format('Images:', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
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
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if not tidyItem or tidyItem is None:        # Don't process
                    continue

                countriesSet.add(tidyItem)

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
            log('UTILS :: {0:<29} {1}'.format('Images:', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        try:
            #   IAFD lists the sexual activities of the cast members under their pictures at times
            if siteInfoDict['Cast']:
                rolesSet = {cast[x]['Role'] for x in siteInfoDict['Cast'].keys()}
                rolesSet = {x for x in rolesSet if 'AKA' not in x and x != IAFD_FOUND}
                rolesSet = set(' '.join(rolesSet).split())
                log('UTILS :: {0:<29} {1}'.format('Roles Word Count', '{0:>2} - {1}'.format(len(rolesSet), rolesSet)))
                for idx, item in enumerate(rolesSet, start=1):
                    tidyItem = findTidy(item)
                    if not tidyItem or tidyItem is None:        # Don't process
                        continue
                    if tidyItem in COUNTRYSET:
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))
                    genresSet.add(tidyItem)
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
                # if already set to yes by possible checking of external sources [AEBN, GayEmpire, GayHotMovies], dont change with IAFD value
                htmlcompilation = html.xpath('//p[@class="bioheading" and text()="Compilation"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: {0:<29} {1}'.format('Compilation?', htmlcompilation))
            except Exception as e:
                siteInfoDict['Compilation'] = compilation
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
        scenesDict = {'Link': filmURL}
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
                scenesDict[str(sceneNo)] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText}

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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
            try:
                htmlcast = html.xpath('//a[@class="titletags"]/text()')
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

        #   5.  Tag List: Genres and possible Countries, Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        castSet = {x.strip() for x in FILMDICT['FilenameCast']}
        tempCastSet = {x.strip().replace(' ', '') for x in FILMDICT['FilenameCast']}
        testStudio = [FILMDICT['Studio'].lower().replace(' ', ''), FILMDICT['CompareStudio']]
        try:
            htmltags = html.xpath('//div[@class="taxonomy"]/a/@title|//article[@id and @class]/p/a/text()[normalize-space()]')
            htmltags = [x.strip() for x in htmltags if x.strip()]
            htmltags = [x for x in htmltags if not 'compilation' in x.lower()]
            htmltags = [x for x in htmltags if not 'movie' in x.lower()]
            htmltags = [x for x in htmltags if not 'series' in x.lower()]
            htmltags = [x for x in htmltags if not '.tv' in x.lower()]
            htmltags = [x for x in htmltags if not '.com' in x.lower()]
            htmltags = [x for x in htmltags if not '.net' in x.lower()]
            htmltags = [x for x in htmltags if not x.lower().replace(' ', '') in testStudio]

            # remove all tags with non name characters such as colons
            htmltags = [setDashesQuotes(x) for x in htmltags]
            htmltags = [x for x in htmltags if not ':' in x]
            htmltags = [x for x in htmltags if not x + ':' in FILMDICT['Title']]
            htmltags = list(set(htmltags))
            htmltags.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Tags', '{0:>2} - {1}'.format(len(htmltags), htmltags)))
            for idx, item in enumerate(htmltags, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))
                if tidyItem is None:                                      # If none skip
                    continue
                elif tidyItem:                                            # gayTidy returned an item
                    if tidyItem.lower() in GENRESDICT:                    # check if genre
                        genresSet.add(tidyItem)
                    elif tidyItem in COUNTRYSET:                          # check if country
                        countriesSet.add(tidyItem)
                    else:
                        log('UTILS :: {0:<29} {1}'.format('Warning', 'Tidied Item is neither Country nor Genre'))
                else:                                                     # tag is most probably cast
                    castSet.add(item)

            showSetData(genresSet, 'Genres (set*)')
            showSetData(countriesSet, 'Countries (set*)')
            showSetData(castSet, 'Cast (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Tags: Genres/Countries/Cast/Compilation: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Cast'] = sorted(castSet)
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
            log('UTILS :: {0:<29} {1}'.format('Images:', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]

            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} - {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        siteInfoDict['Genres'] = genresSet
        siteInfoDict['Countries'] = countriesSet
        siteInfoDict['Compilation'] = compilation

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

            log('UTILS :: {0:<29} {1}'.format('Images:', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
            log('UTILS :: No Cast List on Agent: Built From Tag List')
            siteInfoDict['Cast'] = []

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Tag List: Genres, Cast and possible Countries, Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        castSet = {x.strip() for x in FILMDICT['FilenameCast']}
        tempCastSet = {x.strip().replace(' ', '') for x in FILMDICT['FilenameCast']}
        testStudio = [FILMDICT['Studio'].lower().replace(' ', ''), FILMDICT['CompareStudio']]
        try:
            htmltags = html.xpath('//a[contains(@href,"https://www.waybig.com/blog/tag/")]/text()')
            htmltags = [x.strip() for x in htmltags if x.strip()]
            htmltags = [x for x in htmltags if not 'compilation' in x.lower()]
            htmltags = [x for x in htmltags if not 'movie' in x.lower()]
            htmltags = [x for x in htmltags if not 'series' in x.lower()]
            htmltags = [x for x in htmltags if not '.tv' in x.lower()]
            htmltags = [x for x in htmltags if not '.com' in x.lower()]
            htmltags = [x for x in htmltags if not '.net' in x.lower()]
            htmltags = [x for x in htmltags if not x.lower().replace(' ', '') in testStudio]

            # remove all tags with non name characters such as colons
            htmltags = [setDashesQuotes(x) for x in htmltags]
            htmltags = [x for x in htmltags if not ':' in x]
            htmltags = [x for x in htmltags if not x + ':' in FILMDICT['Title']]
            htmltags = list(set(htmltags))
            htmltags.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Tags', '{0:>2} - {1}'.format(len(htmltags), htmltags)))
            for idx, item in enumerate(htmltags, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))
                if tidyItem is None:                                      # If none skip
                    continue
                elif tidyItem:                                            # gayTidy returned an item
                    if tidyItem.lower() in GENRESDICT:                    # check if genre
                        genresSet.add(tidyItem)
                    elif tidyItem in COUNTRYSET:                          # check if country
                        countriesSet.add(tidyItem)
                    else:
                        log('UTILS :: {0:<29} {1}'.format('Warning', 'Tidied Item is neither Country nor Genre'))
                else:                                                     # tag is most probably cast
                    castSet.add(item)

            showSetData(genresSet, 'Genres (set*)')
            showSetData(countriesSet, 'Countries (set*)')
            showSetData(castSet, 'Cast (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error getting Tags: Genres/Countries/Cast/Compilation: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Cast'] = sorted(castSet)
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
            log('UTILS :: {0:<29} {1}'.format('Images:', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]

            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
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
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
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
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Collections'), '{0:>2} - {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = []
            log('UTILS :: Error getting Collections: %s', e)

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//p/a[@href[contains(.,"display-movies/category")]]/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in COUNTRYSET:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

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

            poster = [htmlimage]
            art = [htmlimage]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error getting Images: %s', e)

        finally:
            siteInfoDict['Poster'] = poster
            siteInfoDict['Art'] = art

        #   9.  Scene Info - Wolff Video retains actually reviews - so collect these rather than setting up scenes and chapters
        log(LOG_SUBLINE)
        kwFilmURL = kwargs.get('kwFilmURL')
        filmURL = kwFilmURL if kwFilmURL is not None else FILMDICT['FilmURL']
        scenesDict = {'Link': filmURL}
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
                            log('UTILS :: Warning: No Review Source (Used Film Title)')

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
                    scenesDict[str(sceneNo)] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText}

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
    log(LOG_ASTLINE)
    log(LOG_ASTLINE)
    log('%s:: Version:                              v.%s', myFunc, VERSION_NO)
    log('%s:: Python:                               %s (%s): %s', myFunc, platform.python_version(), platform.architecture()[0], platform.python_build())
    log('%s:: Platform:', myFunc)
    log('%s::   > Operating System:                 %s', myFunc, platform.system())
    log('%s::   > Release:                          %s', myFunc, platform.release())
    log('%s:: Preferences:', myFunc)
    log('%s::   > Legend Before Summary:            %s', myFunc, PREFIXLEGEND)
    log('%s::   > Reset Metadata:                   %s', myFunc, RESETMETA)
    log('%s::   > Collection Gathering:', myFunc)
    log('%s::      > System:                        %s', myFunc, 'Yes' if COLSYSTEM else 'No')
    log('%s::      > Genres:                        %s, Prefix genres with %s symbol?: %s', myFunc, 'Yes' if COLGENRE else 'No', AGENT_TYPE, 'Yes' if PREFIXGENRE is True else 'No')
    log('%s::      > Countries                      %s, Display poster as %s', myFunc, 'Yes' if COLCOUNTRY else 'No', COUNTRYPOSTERTYPE)
    log('%s::      > Studio:                        %s', myFunc, 'Yes' if COLSTUDIO else 'No')
    log('%s::      > Series:                        %s', myFunc, 'Yes' if COLSERIES else 'No')
    log('%s::      > Directors:                     %s', myFunc, 'Yes' if COLDIRECTOR else 'No')
    log('%s::      > Cast:                          %s', myFunc, 'Yes' if COLCAST else 'No')
    log('%s::   > Poster Source - Download?         %s', myFunc, POSTERSOURCEDOWNLOAD)
    log('%s::   > Match IAFD Duration:              %s', myFunc, MATCHIAFDDURATION)
    log('%s::   > Match Site Duration:              %s', myFunc, MATCHSITEDURATION)
    log('%s::   > Duration Dx                       ±%s Minutes', myFunc, DURATIONDX)
    log('%s::   > Language Detection:               %s', myFunc, DETECT)
    log('%s::   > Library:Site Language:            (%s:%s)', myFunc, lang, SITE_LANGUAGE)
    log('%s:: Media Title:                          %s', myFunc, media.title)
    log('%s:: File Path:                            %s', myFunc, media.items[0].parts[0].file)
    log(LOG_ASTLINE)
    log(LOG_ASTLINE)

# -------------------------------------------------------------------------------------------------------------------------------
def logFooter(myFunc, FILMDICT):
    ''' log footer for search and update functions '''
    log(LOG_ASTLINE)
    for footer in [' >> {0}: Finished {1} Routine << '.format(FILMDICT['Agent'], myFunc.title()), 
                   ' >> ({0}) - {1} ({2}) << '.format(FILMDICT['Studio'], FILMDICT['Title'], FILMDICT['Year']),
                   ' >> {0} << '.format(FILMDICT['FilmURL']),
                   ' >> {0} << '.format('Successful!!' if FILMDICT['Status'] else 'Failed')]:
        log('%s:: %s', myFunc, footer.center(131, '*'))
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

    '''
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
    '''

    asciiString = unidecode(myString)

    return asciiString

# ----------------------------------------------------------------------------------------------------------------------------------
def matchCast(unmatchedCastList, FILMDICT):
    ''' check IAFD web site for individual cast'''
    matchedCastDict = {}

    myYear = int(FILMDICT['Year'])

    for idx, unmatchedCast in enumerate(unmatchedCastList, start=1):
        compareUnmatchedCast = re.sub(r'[\W\d_]', '', unmatchedCast).strip().lower()
        log('UTILS :: {0:<29} {1}'.format('Unmatched Cast Name', '{0:>2} - {1}/{2}'.format(idx, unmatchedCast, compareUnmatchedCast)))

        # the cast on the website has not matched to those listed against the film in IAFD. So search for the cast's entry on IAFD
        matchedCastDict[unmatchedCast] = {'Awards': [], 'Bio': {}, 'CompareName': '', 'CompareAlias': [], 'Films': [],
                                          'Nationality': '', 'Photo': '', 'RealName': '', 'Role': IAFD_ABSENT, 'URL': ''}   # initialise cast member's dictionary

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

        if FILMDICT['AllMale'] == 'Yes':
            xPath = '//table[@id="tblMal"]/tbody/tr'
            xType = 'Gay'
        elif FILMDICT['AllGirl'] == 'Yes':
            xPath = '//table[@id="tblFem"]/tbody/tr'
            xType = 'Lesbian'
        else:
            xPath = '//table[@id="tblFem" or @id="tblMal"]/tbody/tr'
            xType = 'Bisexual/Straight'

        try:
            html = getURLElement(IAFD_SEARCH_URL.format(String.URLEncode(unmatchedCast)), FilterYear = myYear) # remove full stops before encoding
            castList = html.xpath(xPath)
            log('UTILS :: {0:<29} {1}'.format('{0} Cast xPath'.format(xType), xPath))

            castFound = len(castList)
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Cast Found'), '{0:>2} - {1}'.format(castFound, 'Skipping: > 25 Cast Names Returned' if castFound > 25 else 'Processing: <= 25 Cast Names Returned')))
            if castFound == 0 or castFound > 25:
                log(LOG_SUBLINE)
                continue            # next unmatchedCast

            log('UTILS :: {0:<29} {1}'.format('Cast Found', '{0:>2} - Matching Name: {1}'.format(castFound, unmatchedCast)))
            log(LOG_BIGLINE)
            for idx2, cast in enumerate(castList, start=1):
                # get cast details and compare to Agent cast
                try:
                    castName = cast.xpath('./td[2]/a/text()[normalize-space()]')[0]
                    castCompareName = re.sub(r'[\W\d_]', '', castName).strip().lower()
                    log('UTILS :: {0:<29} {1}'.format('Matching Cast Name', '{0:>2} - {1} / {2}'.format(idx2, castName, castCompareName)))
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
                    castAliasList = cast.xpath('./td[3]/text()[normalize-space()]')[0].replace(' or ', ',')
                    castAliasList = castAliasList.split(',')
                    castAliasList = [x.strip() for x in castAliasList if x.strip()]
                    castAlias = ', '.join(castAliasList)
                    castCompareAliasList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in castAliasList]
                    log('UTILS :: {0:<29} {1}'.format('Alias', castAliasList if castAliasList else 'No Cast Alias Recorded'))
                except:
                    castAlias = ''
                    castAliasList = []
                    castCompareAliasList = []

                try:
                    startCareer = int(cast.xpath('./td[4]/text()[normalize-space()]')[0]) - 1 # set start of career to 1 year before for pre-releases
                except:
                    startCareer = 0

                try:
                    endCareer = int(cast.xpath('./td[5]/text()[normalize-space()]')[0]) + 1   # set end of career to 1 year after to cater for late releases
                except:
                    endCareer = 0

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
                            if checkCompareAlias in castCompareAliasList:
                                previouslyMatched = True
                                log('UTILS :: {0:<29} {1}'.format('Note', '{0} AKA {1} also known by this name: {2}'.format(checkName, checkAlias, castName)))
                                break

                    if previouslyMatched:
                        matchedCastDict.pop(unmatchedCast, None)
                        log(LOG_SUBLINE)
                        continue

                # Check that cast member has acted in a gay film
                try:
                    chtml = getURLElement(castURL)
                    xPath = '//table[@id="personal"]/tbody/tr[@class="ga" or @class="we"]' if FILMDICT['SceneAgent'] is True else '//table[@id="personal"]/tbody/tr[@class="ga"]'
                    gayFilmsList = chtml.xpath(xPath)
                    gayFilmsFound = len(gayFilmsList)
                    log('UTILS :: {0:<29} {1}'.format('Filmography', '{0:>2} - Gay/Bi Films'.format(gayFilmsFound)))
                    noCount = 0
                    for idx, gayFilm in enumerate(gayFilmsList, start=1):
                        gaySiteTitle = gayFilm.xpath('./td//text()')
                        gayNotes = gaySiteTitle[3].lower()
                        if [x for x in ['mastonly', 'nonsex'] if (x in gayNotes)]:   # appeared in gay film in possible non gay role
                            noCount += 1

                    if noCount == gayFilmsFound:                        # all films in list were nonsex or masturbation only
                        log('UTILS :: {0:<29} {1}'.format('Skipped', 'Appeared in Zero Films or as Non Sex / Masturbation Roles Only'))
                        log(LOG_SUBLINE)
                        continue    # next cast in cast list
                except Exception as e:
                    log('UTILS :: Error getting Cast Member Page, Cast Member: %s', e)

                log('UTILS :: {0:<29} {1}'.format('Career', '{0} - {1}'.format(startCareer if startCareer > 0 else 'N/A', endCareer if endCareer > 0 else 'N/A')))

                matchedUsing = ''

                # match iafd row with Agent Cast entry
                matchedCast = True if compareUnmatchedCast == castCompareName else False
                if matchedCast:
                    matchedUsing = 'Name' 
                else:
                    log('UTILS :: {0:<29} {1}'.format('Failed Name Matching', '{0} != {1}'.format(compareUnmatchedCast, castCompareName)))

                # match iafd row with Agent Cast Alias entry
                if not matchedCast and castAliasList:
                    matchedItem = [x for x in castCompareAliasList if compareUnmatchedCast in x]
                    matchedCast = True if matchedItem else False
                    if matchedCast:
                        matchedUsing = 'Alias' 
                    else:
                        log('UTILS :: {0:<29} {1}'.format('Failed Alias List Matching', '{0} not in {1}'.format(compareUnmatchedCast, castCompareAliasList)))

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
                    # get cast biography and filmography etc
                    castDetails = getIAFDArtist(castURL)
                    castAwards = castDetails['Awards']
                    castBio = castDetails['Bio']
                    castFilms = castDetails['Films']
                    castNationality = castDetails['Nationality']
                    castPhoto = castDetails['Photo']
                    castRealName = castDetails['RealName']
                    castRole = IAFD_FOUND  # default to found

                    # log cast details
                    log('UTILS :: {0:<29} {1}'.format('Matched Cast Details:', ''))
                    log('UTILS :: {0:<29} {1}'.format('Cast Real Name', castRealName))
                    log('UTILS :: {0:<29} {1}'.format('Cast Alias', castAlias if castAlias else 'No Cast Alias Recorded'))
                    log('UTILS :: {0:<29} {1}'.format('Cast Awards', castAwards))
                    log('UTILS :: {0:<29} {1}'.format('Cast Bio', castBio))
                    log('UTILS :: {0:<29} {1}'.format('Cast Films', castFilms))
                    log('UTILS :: {0:<29} {1}'.format('Cast Name', castName))
                    log('UTILS :: {0:<29} {1}'.format('Cast Nationality', castNationality))
                    log('UTILS :: {0:<29} {1}'.format('Cast Photo', castPhoto))
                    log('UTILS :: {0:<29} {1}'.format('Cast Role', castRole))
                    log('UTILS :: {0:<29} {1}'.format('Cast URL', castURL))
                    log('UTILS :: {0:<29} {1}'.format('Matched Using', matchedUsing))
                    log(LOG_SUBLINE)

                    # Assign values to dictionary
                    matchedCastDict[unmatchedCast] = {'Alias': castAliasList, 'Awards': castAwards, 'Bio': castBio, 'CompareName': castCompareName, 'CompareAlias': castCompareAliasList, 
                                                      'Films': castFilms, 'Nationality': castNationality, 'Photo': castPhoto, 'RealName': castRealName, 'Role': castRole, 'URL': castURL}
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

        # the director on the website has not matched to those listed against the film in IAFD. So search for the director's entry on IAFD
        matchedDirectorDict[unmatchedDirector] = {'Alias': '', 'Awards': [], 'Bio': {}, 'Films': [], 'RealName': '', 'Nationality': '', 'Photo': '', 'URL': ''}    # initialise director's dictionary
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
            if compareUnmatchedDirector == IAFDCompareAlias:
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
                    directorCompareName = re.sub(r'[\W\d_]', '', directorName).strip().lower()
                    log('UTILS :: {0:<29} {1}'.format('Matching Director', '{0:>2} - {1} / {1}'.format(idx2, directorName, directorCompareName)))
                except Exception as e:
                    log('UTILS :: Error: Could not read Director Name: %s', e)
                    continue   # next director

                try:
                    directorAliasList = director.xpath('./td[3]/text()[normalize-space()]')[0].split(',')
                    directorAliasList = [x.strip() for x in directorAliasList if x.strip()]
                    directorAlias = ', '.join(directorAliasList)
                    directorCompareAliasList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in directorAliasList]
                    log('UTILS :: {0:<29} {1}'.format('Alias', directorAliasList if directorAliasList else 'No Director Alias Recorded'))
                except:
                    directorAliasList = []
                    directorAlias = ''
                    directorCompareAliasList = []

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
                matchedDirector = True if compareUnmatchedDirector == directorCompareName else False
                if matchedDirector:
                    matchedUsing = 'Name' 
                else:
                    log('UTILS :: {0:<29} {1}'.format('Failed Name Matching', '{0} != {1}'.format(compareUnmatchedDirector, directorCompareName)))

                if not matchedDirector and directorAliasList:
                    matchedItem = [x for x in directorCompareAliasList if compareUnmatchedDirector in x]
                    matchedDirector = True if matchedItem else False
                    if matchedDirector:
                        matchedUsing = 'Alias' 
                    else:
                        log('UTILS :: {0:<29} {1}'.format('Failed Alias List Matching', '{0} not in {1}'.format(compareUnmatchedDirector, directorCompareAliasList)))

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
                        if checkCompareAlias in directorCompareAliasList:
                            matchedDirector = True
                            log('UTILS :: {0:<29} {1}'.format('Skipping: Recorded Director Name', '{0} AKA {1} also known by this name: {2}'.format(checkName, checkAlias, directorName)))
                            break

                # we have an director who matches the conditions
                if matchedDirector:
                    # get director biography and filmography etc
                    directorURL = IAFD_BASE + director.xpath('./td[2]/a/@href')[0]
                    directorDetails = getIAFDArtist(directorURL)
                    directorAwards = directorDetails['Awards']
                    directorBio = directorDetails['Bio']
                    directorFilms = directorDetails['Films']
                    directorNationality = directorDetails['Nationality']
                    directorPhoto = directorDetails['Photo']
                    directorRealName = directorDetails['RealName']

                    log('UTILS :: {0:<29} {1}'.format('Recorded Director Details:', ''))
                    log('UTILS :: {0:<29} {1}'.format('Director Alias', directorAliasList if directorAliasList else 'No Director Alias Recorded'))
                    log('UTILS :: {0:<29} {1}'.format('Director Awards', directorAwards))
                    log('UTILS :: {0:<29} {1}'.format('Director Bio', directorBio))
                    log('UTILS :: {0:<29} {1}'.format('Director Films', directorFilms))
                    log('UTILS :: {0:<29} {1}'.format('Director Name', directorName))
                    log('UTILS :: {0:<29} {1}'.format('Director Nationality', directorNationality))
                    log('UTILS :: {0:<29} {1}'.format('Director Photo', directorPhoto))
                    log('UTILS :: {0:<29} {1}'.format('Director Real Name', directorRealName))
                    log('UTILS :: {0:<29} {1}'.format('Director URL', directorURL))
                    log('UTILS :: {0:<29} {1}'.format('Matched Using', matchedUsing))
                    log(LOG_SUBLINE)

                    # Assign values to dictionary
                    matchedDirectorDict[unmatchedDirector] = {'Alias': directorAliasList, 'Awards': directorAwards, 'Bio': directorBio, 'Films': directorFilms, 
                                                              'RealName': directorRealName, 'Nationality': directorNationality, 'Photo': directorPhoto, 'URL': directorURL}
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
    if START_SCRAPE == 'No':
        raise Exception('<QUIT: Scraping Parameters Not Set Up!>')

    filmVars = {}
    filmVars['id'] = media.id
    filmVars['Status'] = False          # initial state before Search and Update Routine
    filmVars['SceneAgent'] = False

    # Plex Library, that media resides in
    plexBaseURL = 'http://{0}:{1}'.format('127.0.0.1', '32400')
    metadataURL = '{0}/library/metadata/{1}?X-Plex-Token={2}'.format(plexBaseURL, media.id, PLEXTOKEN)
    xml = XML.ElementFromURL(metadataURL, sleep=5)
    xml = XML.StringFromElement(xml)
    filmVars['LibraryID'] = xml.split('librarySectionID="')[1].split('"')[0]
    filmVars['LibraryTitle'] = xml.split('librarySectionTitle="')[1].split('"')[0]

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
    filmVars['CompareStudio'] = Normalise(makeASCII(filmVars['Studio']))

    #   Title
    filmVars['CompareTitle'] = set()
    filmVars['Title'] = groups['fnTITLE']
    filmVars['Title'] = filmVars['Title'].replace('~', '/')                             # ~ invalid character marker in filename
    filmVars['Title'] = setDashesQuotes(filmVars['Title'])
    filmVars['NormaliseTitle'] = Normalise(filmVars['Title'])
    filmVars['CompareTitle'].add(sortAlphaChars(filmVars['NormaliseTitle']))

    #   Search Strings - A Title is split into Search Strings if a Dash-space is found
    searchTitlesTemp = []
    pattern = r'(?<![-.])\b[0-9]+\b(?!\.[0-9])$'                                        # series matching = whole separate number at end of string
    splitFilmTitle = filmVars['Title'].split('- ')
    splitFilmTitle = [x.strip() for x in splitFilmTitle]
    splitCount = len(splitFilmTitle) - 1
    for index, partTitle in enumerate(splitFilmTitle):
        matchedSearchTitle = re.subn(pattern, '', partTitle)
        if matchedSearchTitle[1]:
            searchTitlesTemp.insert(0, matchedSearchTitle[0].strip())                   # e.g. Pissing
        else:
            if index < splitCount:                                                      # only add to collection if not last part of title e.g. Hardcore Fetish Series
                searchTitlesTemp.insert(0, partTitle)

    #   Series - for use in creating collections - A Series is only considered if it is separated by space-dash-space
    series = []
    episodes = []
    pattern = r'(?<![-.])\b[0-9]+\b(?!\.[0-9])$'                                        # series matching = whole separate number at end of string
    splitFilmTitle = filmVars['Title'].split(' - ')
    splitFilmTitle = [x.strip() for x in splitFilmTitle]
    splitCount = len(splitFilmTitle) - 1
    for index, partTitle in enumerate(splitFilmTitle):
        matchedSeries = re.subn(pattern, '', partTitle)
        if matchedSeries[1]:
            series.insert(0, matchedSeries[0].strip())                                  # e.g. Pissing
            episodes.insert(0, partTitle)                                               # e.g. Pissing 1
            if index < splitCount:                                                      # only blank out series info in title if not last split
                splitFilmTitle[index] = ''
        else:
            if index < splitCount:                                                      # only add to collection if not last part of title e.g. Hardcore Fetish Series
                splitFilmTitle[index] = ''
                series.insert(0, partTitle)

    filmVars['Series'] = series
    filmVars['Episodes'] = episodes
    for item in episodes:
        filmVars['CompareTitle'].add(sortAlphaChars(Normalise(item)))

    # process Title
    # replace hyphens with colon-space
    filmVars['Title'] = re.sub(ur' - |- ', ': ', filmVars['Title'])

    # strip punctuations at end of string
    pattern = ur'[' + re.escape(''.join(['.', '!', '%', '?'])) + ']+$'
    shortTitle = re.sub(pattern, '', ' '.join(splitFilmTitle).strip())
    filmVars['ShortTitle'] = shortTitle
    filmVars['NormaliseShortTitle'] = Normalise(filmVars['ShortTitle'])
    filmVars['CompareTitle'].add(sortAlphaChars(filmVars['NormaliseShortTitle']))

    # add series inividually and wholly + short Title in case episode number left out
    for item in filmVars['Series']:
        filmVars['CompareTitle'].add(sortAlphaChars(Normalise('{0}{1}'.format(item, filmVars['ShortTitle']))))

    allSeries = ''.join(filmVars['Series'])
    filmVars['CompareTitle'].add(sortAlphaChars(Normalise('{0}{1}'.format(allSeries, filmVars['ShortTitle']))))

    #   Search Title: Add Short Title to the list, strip determinates and strip trailing '1' from search string
    pattern = ur'^(The |An |A )'
    filmVars['ShortTitle'] = re.sub(pattern, '', filmVars['ShortTitle'], flags=re.IGNORECASE).strip()

    pattern = ur' 1$'
    filmVars['ShortTitle'] = re.sub(pattern, '', filmVars['ShortTitle'], flags=re.IGNORECASE).strip()

    #   insert short title and whole whole title as first and second search titles and remove any duplicates
    searchTitlesTemp.append(shortTitle)
    fullSearchTitle = ' '.join(searchTitlesTemp)
    searchTitlesTemp.insert(0, fullSearchTitle)
    searchTitles = []
    [searchTitles.append(i) for i in searchTitlesTemp if not i in searchTitles]
    filmVars['SearchTitles'] = searchTitles                         # for GEVI and AEBN - multiple searches allowed
    filmVars['SearchTitle'] = filmVars['ShortTitle']                # for rest - search on shortTitle - temporary - to be upgraded

    #   Prepare IAFD variables
    filmVars['IAFDDuration'] = datetime.fromtimestamp(0) # default 1970-01-01 00:00:00

    #       IAFD Studio
    filmVars['IAFDStudio'] = groups['fnSTUDIO'].split(';')[1].strip() if ';' in groups['fnSTUDIO'] else ''
    filmVars['CompareIAFDStudio'] = Normalise(filmVars['IAFDStudio']) if 'IAFDStudio' in filmVars and filmVars['IAFDStudio'] else ''

    #       IAFD Title - IAFD uses standard Latin Alphabet Characters for its entries.
    #                  - deal with ² in title - replace with the word Squared
    pattern = u'²'
    matched = re.search(pattern, groups['fnTITLE'])  # match against whole string
    groups['fnTITLE'] = re.sub(pattern, ' Squared', groups['fnTITLE']) if matched else groups['fnTITLE']
    filmVars['IAFDTitle'] = makeASCII(groups['fnTITLE']).replace(' - ', ': ').replace('- ', ': ')       # iafd needs colons in place to search correctly
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
    filmVars['IAFDTitle'] = re.sub(pattern, '', filmVars['IAFDTitle'], re.IGNORECASE)  # match against whole string
    filmVars['NormaliseIAFDTitle'] = Normalise(filmVars['IAFDTitle'])
    filmVars['CompareTitle'].add(sortAlphaChars(filmVars['NormaliseIAFDTitle']))
    filmVars['CompareTitle'] = sorted(list(filmVars['CompareTitle']))

    # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string
    searchString = filmVars['IAFDTitle'].split(':')[0]
    searchString = searchString.replace('~', '/')
    # iafd search string can not be longer than 73 characters
    if len(searchString) > 72:
        lastSpace = searchString[:73].rfind(' ')
        searchString = searchString[:lastSpace]
        log('UTILS :: {0:<29} {1}'.format('Search Query', '{0}: "{1} <= 72"'.format('Search Query Length', lastSpace)))
        log('UTILS :: {0:<29} {1}'.format('Search Query', '{0}: "{1}"'.format('Shorten Search Query', searchString[:lastSpace])))

    searchString = String.StripDiacritics(searchString).strip()
    searchString = String.URLEncode(searchString).replace('%25', '%').replace('%26', '&').replace('*', '')
    filmVars['IAFDSearchTitle'] = searchString

    #   Year / comparison date defaults to 31st Dec of Year
    try:
        filmVars['Year'] = int(groups['fnYEAR'])
        filmVars['CompareDate'] = datetime(filmVars['Year'], 12, 31)
    except:
        filmVars['Year'] = 0
        filmVars['CompareDate'] = None

    #   Stacked
    filmVars['Stacked'] = 'No' if groups['fnSTACK'] is None else 'Yes'

    #  Filname Cast List
    filmVars['FilenameCast'] = re.split(r',\s*', groups['fnCAST']) if groups['fnCAST'] else []

    # sort comparisons for matching strings
    # IAFD Variables used by other Agents
    filmVars['FilmAKA'] = ''            # default blank - only IAFD has AKA Titles
    filmVars['Compilation'] = 'No'      # default No
    filmVars['AllGirl'] = ''            # default No
    filmVars['AllMale'] = ''            # default Yes as this is usually used on gay websites.
    filmVars['Cast'] = {}
    filmVars['Directors'] = {}
    filmVars['FoundOnIAFD'] = 'No'      # default No
    filmVars['IAFDFilmURL'] = ''        # default blank
    filmVars['FilmURL'] = ''            # default blank

    # delete unneeded dictionary keys
    del filmVars['NormaliseIAFDTitle']
    del filmVars['NormaliseTitle']
    del filmVars['ShortTitle']

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
    log('UTILS :: {0:<29} {1}'.format('{0} Duration'.format(AGENT), siteDuration.strftime('%H:%M:%S')))
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

    log('UTILS :: {0:<29} {1}'.format('{0} Release Date'.format(AGENT), siteReleaseDate))
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

    log('UTILS :: {0:<29} {1}'.format('{0} Studio'.format(AGENT), siteStudio))
    log('UTILS :: {0:<29} {1}'.format('File Studio', FILMDICT['Studio']))
    log('UTILS :: {0:<29} {1}'.format('IAFD Studio', FILMDICT['IAFDStudio']))
    log('UTILS :: {0:<29} {1}'.format('Compare {0} Studio'.format(AGENT), compareSiteStudio))
    log('UTILS :: {0:<29} {1}'.format('        File Studio', FILMDICT['CompareStudio']))
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
    filmTitleNormaliseA = Normalise(filmTitle)

    filmTitleNormaliseB = ''
    if FILMDICT['NormaliseShortTitle'] in filmTitleNormaliseA and FILMDICT['NormaliseShortTitle'] != filmTitleNormaliseA:
        pattern = re.compile(re.escape(FILMDICT['NormaliseShortTitle']), re.IGNORECASE)
        filmTitleNormaliseB = '{0}{1}'.format(re.sub(pattern, '', filmTitleNormaliseA).strip(), FILMDICT['NormaliseShortTitle'])

    filmCompareTitle = sortAlphaChars(filmTitleNormaliseA)
    testTitle = 'Passed' if filmCompareTitle in FILMDICT['CompareTitle'] else 'Failed'
    if testTitle == 'Failed' and filmTitleNormaliseB:
        filmCompareTitle = sortAlphaChars(filmTitleNormaliseB)
        log('UTILS :: {0:<29} {1}'.format('Comparison Title B', filmCompareTitle))
        testTitle = 'Passed' if filmCompareTitle in FILMDICT['CompareTitle'] else 'Failed'

    if testTitle == 'Failed':                   # check if episode  i.e. series + number in agent title
        for item in FILMDICT['Episodes']:
            pattern = re.compile(re.escape(item), re.IGNORECASE)
            if re.search(pattern, filmTitle):  # match against whole string
                testTitle = 'Passed'
                break

    log('UTILS :: {0:<29} {1}'.format('{0} Title'.format(AGENT), filmTitle))
    log('UTILS :: {0:<29} {1}'.format('Comparison Title', filmCompareTitle))
    log('UTILS :: {0:<29} {1}'.format('File Title', FILMDICT['Title']))
    log('UTILS :: {0:<29} {1}'.format('Comparison Title List', FILMDICT['CompareTitle']))
    log('UTILS :: {0:<29} {1}'.format('Title Comparison Test', testTitle))

    if testTitle == 'Failed':
        raise Exception('< Title Match Failure! >')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def Normalise(myString):
    ''' Normalise string for, strip uneeded characters for comparison of web site values to file name regex group values '''
   
    # Check if string has roman numerals as in a series; note the letter I will be converted
    # myString = '{0} '.format(myString)  # append space at end of string to match last characters
    pattern = r'(?=\b[MDCLXVI]+\b)M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})$'
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

            myArabic = '{0}'.format(myArabic)
            myString = re.sub(pattern, myArabic, myString)

    # convert to lower case and trim
    myString = myString.strip().lower()

    # replace ampersand with 'and'
    myString = myString.replace('&', 'and') if AGENT != 'IAFD' else myString

    # replace ": " with " - "
    myString = myString.replace(': ', ' - ')

    # change string to ASCII
    myString = makeASCII(myString)

    # strip domain suffixes, vol., volume, Pt, Part from string, standalone '1's' then strip all non alphanumeric characters
    # pattern = r'[.]([a-z]{2,3}co[.][a-z]{2})|Vol[.]|Vols[.]|Nr[.]|\bVolume\b|\bVolumes\b|Pt |\bPart\b[^A-Za-z0-9]+'
    pattern = r'[.]([a-z]{2,3}co[.][a-z]{2})|Vol[.]|Vols[.]|Nr[.]|\bVolume\b|\bVolumes\b|(?<!\d)1(?!\d)|Pt |\bPart\b[^A-Za-z0-9]+'
    myString = re.sub(pattern, '', myString, flags=re.IGNORECASE)
    myString = filter(str.isalnum, myString)
    myString = ''.join(myString)
    return myString

# ----------------------------------------------------------------------------------------------------------------------------------
def printFilmInformation(myDictionary):
    ''' print out dictionary values / normalise unicode'''
    log('UTILS :: Film Dictionary Variables:')
    for key in sorted(myDictionary.keys()):
        myDictionary[key] = list(dict.fromkeys(myDictionary[key])) if type(myDictionary[key]) is list else myDictionary[key]
        log('UTILS :: {0:<29} {1}'.format(key, myDictionary[key]))

# ----------------------------------------------------------------------------------------------------------------------------------
def setMetadata(metadata, media, FILMDICT):
    ''' Set Metadata variables with information gleaned from File Name and Agent website stored in FILMDICT. Any failure aborts the process'''
    myAgent = FILMDICT.get('Agent', AGENT)
    myAgentDict = FILMDICT.get(myAgent, '')
    if not myAgentDict:
        FILMDICT['Status'] = False
        return

    collectionsDict = {}                                                            # used to create collections that have extra information like cast photos, country flags etc order by Sort title
    nationalities = set()
    prefix = '{0}{1}'.format(AGENT_TYPE, THIN_SPACE) if PREFIXGENRE else ''         # add prefix to genres and genre collections if preferenced
    deathRegex = r'Date of Death|Year of Death|would be'.replace(' ', NOBREAK_SPACE)
    errorCountryArt = os.path.join(PGMA_COUNTRYART, '_Error.png')
    errorCountryPosterFlag = os.path.join(PGMA_COUNTRYPOSTERFLAGS, '_Error.png')

    log('UTILS :: 1.  Set Metadata from File Name and Default Settings:')

    try:
        '''
        The following bits of metadata need to be established and used to update the movie on plex
        1.  Metadata that is set by Agent as default
            a. id.                              : Plex media id setting
            b. Studio                           : From studio group of filename - no need to process this as above
            c. Title                            : From title group of filename - no need to process this as is used to find it on website
            d. Content Rating                   : Always X
            e. Content Rating Age               : Always 18
        '''
        # 1a.   Show id
        log(LOG_SUBLINE)
        try:
            metadata.id = '{0}:{1}'.format(myAgent, re.sub('[^0-9]', '', FILMDICT['FilmURL']))
            log('UTILS :: {0:<29} {1}'.format('1a. ID', metadata.id))

        except Exception as e:
            log('UTILS :: Error setting ID: %s', e)
            FILMDICT['Status'] = False
            return

        # 1b.   Set Studio
        log(LOG_SUBLINE)
        try:
            metadata.studio = FILMDICT['Studio']
            log('UTILS :: {0:<29} {1}'.format('1b. Studio', metadata.studio))

        except Exception as e:
            log('UTILS :: Error setting Studio: %s', e)
            FILMDICT['Status'] = False
            return

        # 1c.   Set Title
        log(LOG_SUBLINE)
        try:
            if AGENT == 'BestExclusivePorn':        # BEP - file name has to be set to lowercase bar Actors Names, so restore
                metadata.title = " ".join(word.capitalize() if "'s" in word or "’s" in word or "'t" in word or "’t" in word else word.title() for word in FILMDICT['Title'].split())
            else:
                metadata.title = FILMDICT['Title']
            log('UTILS :: {0:<29} {1}'.format('1c. Title', metadata.title))

            # Showcase Collection - if "Best of" found in Title
            if COLGENRE:
                pattern = r'Best Of'
                matched = re.search(pattern, FILMDICT['Title'], re.IGNORECASE)
                if matched:
                    item = 'Showcase'
                    entry = '{0} {1}'.format(COLGENRE, item)
                    collectionsDict[entry] = {'Poster': GENRESDICT[item.lower()], 'Art': '', 'Summary': ''}

        except Exception as e:
            log('UTILS :: Error setting Title: %s', e)
            FILMDICT['Status'] = False
            return

        # 1d.   Set Content Rating to Adult
        log(LOG_SUBLINE)
        try:
            metadata.content_rating = 'X'
            log('UTILS :: {0:<29} {1}'.format('1d. Content Rating', 'X'))

        except Exception as e:
            log('UTILS :: Error setting Content Rating: %s', e)
            FILMDICT['Status'] = False
            return

        # 1e.   Set Content Rating Age to 18 years
        log(LOG_SUBLINE)
        try:
            metadata.content_rating_age = 18
            log('UTILS :: {0:<29} {1}'.format('1e. Content Rating Age', '18'))

        except Exception as e:
            log('UTILS :: Error setting Content Rating Age: %s', e)
            FILMDICT['Status'] = False
            return

        '''
        The following bits of metadata need to be established and used to update the movie on plex
        2.  Metadata retrieved from website
            a. Original Title                   : From IAFD - Also Known As Title
            b. Tag line                         : Corresponds to the url of film
            c. Ratings                          : Viewer Rating out of 100%
            d. Genres                           : List of Genres (alphabetic order)
            e. Cast                             : List of Actors, Roles and Photos (alphabetic order) - Photos sourced from IAFD
            f. Directors                        : List of Directors and Photos (alphabetic order)
            g. Countries
            h. Posters                          : Front Cover of DVD
            i. Art (Background)                 : Back Cover of DVF
            j. Reviews                          : Usually Scene Information OR Actual Reviews depending on Agent
            k. Chapters                         : Scene Lengths for Jump Tos in film
            l. Summary                          : Synopsis of film
            m. Collections                      : retrieved from FILMDICT, Genres, Countries, Cast Directors
            n. Originally Availiable Date       : Production Date, default to (Year) of File Name else Agent Website Date
        '''
        log(LOG_SUBLINE)
        log('UTILS :: 2.  Set Metadata from Scraped Website Resources:')

        # 2a.   Set Original Title
        log(LOG_SUBLINE)
        try:
            metadata.original_title = FILMDICT['FilmAKA']
            log('UTILS :: {0:<29} {1}'.format('2a. Original Title (AKA)', metadata.original_title))

        except Exception as e:
            log('UTILS :: Error setting Original Title: %s', e)
            FILMDICT['Status'] = False
            return

        # 2b.   Set Tagline
        log(LOG_SUBLINE)
        try:
            if myAgent == 'IAFD':
                metadata.tagline = FILMDICT['FilmURL']

            elif FILMDICT['FoundOnIAFD'] == 'No':
                metadata.tagline = FILMDICT['FilmURL']

            else:
                metadata.tagline = '{0} :: {1}'.format(FILMDICT['FilmURL'], FILMDICT['IAFDFilmURL'])

            for idx, tag in enumerate(metadata.tagline.split('::'), start=1):
                log('UTILS :: {0:<29} {1}'.format('2b. Tagline' if idx == 1 else '' , '{0} - {1}'.format(idx, tag.strip())))

        except Exception as e:
            log('UTILS :: Error setting Tag Line: %s', e)
            FILMDICT['Status'] = False
            return

        # 2c.   Rating  can be a maximum of 10 - float value
        log(LOG_SUBLINE)
        try:
            if RESETMETA:
                metadata.rating = 0.0

            metadata.rating = myAgentDict['Rating'] if metadata.rating < myAgentDict['Rating'] else metadata.rating
            log('UTILS :: {0:<29} {1}'.format('2c. Film Rating', metadata.rating))

        except Exception as e:
            log('UTILS :: Error setting Rating: %s', e)
            FILMDICT['Status'] = False
            return

        # 2d.   Genres - retrieved from website and in some case from the synopsis
        log(LOG_SUBLINE)
        try:
            if RESETMETA:
                metadata.genres.clear()

            listGenres = list(myAgentDict['Genres'])
            if myAgent != 'IAFD' and 'IAFD' in FILMDICT:
                listGenres.extend(FILMDICT['IAFD']['Genres'])

            listGenres = (list(set(listGenres)))
            listGenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('2d. Genres', '{0:>2} - {1}'.format(len(listGenres), listGenres)))

            # Process Genres
            for idx, item in enumerate(listGenres, start=1):
                metadata.genres.add('{0}{1}'.format(prefix, item))
                log('UTILS :: {0:<29} {1}'.format('Genre' if idx == 1 else '', '{0:>2} - {1}{2}'.format(idx, prefix, item)))
                entry = '{0} {1}{2}'.format(COLSYSTEM, prefix, item) if 'Compilations' in item and COLSYSTEM else ''
                entry = '{0} {1}{2}'.format(COLGENRE, prefix, item) if not entry and COLGENRE else ''
                if entry:
                    collectionsDict[entry] = {'Poster': GENRESDICT[item.lower()], 'Art': '', 'Summary': ''}

        except Exception as e:
            log('UTILS :: Error setting Genres: %s', e)
            FILMDICT['Status'] = False
            return

        # 2e.   Cast: thumbnails, roles from IAFD. Use IAFD as main Source if film found on IAFD
        log(LOG_SUBLINE)
        cast = []
        try:
            if RESETMETA:
                metadata.roles.clear()

            log('UTILS :: {0:<29} {1}'.format('2e. Cast', ''))
            if FILMDICT['FilenameCast']:                      # Priority 1: user has defined the missing cast to be used in filename
                cast = FILMDICT['FilenameCast'][:]

            if myAgentDict['Cast']:                       # Priority 2: Add Cast from Agent
                cast.extend(myAgentDict['Cast'])

            tempDict = getCast(cast, FILMDICT)                # process cast names returning a dictionary
            castDict = {k.split('(')[0].strip():v for (k,v) in tempDict.items()}
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(castDict.keys()), sorted(castDict.keys()))))

            # sort the dictionary and add key(Name)- value(Photo, Role) to metadata
            for idx, item in enumerate(sorted(castDict), start=1):
                entry = castDict[item]['RealName'] if castDict[item]['RealName'] else item
                newRole = metadata.roles.new()
                newRole.name = entry
                newRole.role = castDict[item]['Role']
                newRole.photo = castDict[item]['Photo'] if 'iafd_ad' not in castDict[item]['Photo'] and castDict[item]['Photo'] else 'https://www.iafd.com/graphics/headshots/nophoto340.jpg'
                log('UTILS :: {0:<29} {1}'.format('Cast Name' if idx == 1 else '', '{0:>2} - {1}'.format(idx, item)))
                if COLCAST:
                    if item == 'Unknown Actor':      # do not create collections for unknown actors...
                        continue

                    # check for user defined photo - this only works if the actor has an entry on IAFD
                    if 'nophoto' in newRole.photo:      # actor has no photo but has entry on IAFD
                        castDict[item]['Photo'] = NOCAST_POSTER
                        if castDict[item]['URL']:       # artiste has no photo but has entry on IAFD, check if there is a photo on disk #### still not fully implemented
                            #   https://www.iafd.com/person.rme/perfid=zakspears/gender=m/zak-spears.htm -> zakspears#zak-spears
                            castPhoto = castDict[item]['URL'].split('perfid=')[1].split('.htm')[0].replace('/gender=m/', '#').replace('/gender=f/', '#')
                            castDict[item]['Photo'] = PGMA_CASTDICT.get(castPhoto, NOCAST_POSTER)

                    myBioList = []
                    myBioDict = OrderedDict(sorted(castDict[item]['Bio'].items()))
                    for count, (k, v) in enumerate(myBioDict.items(), start=1):
                        bio = '{0}. {1}: {2}'.format(count, k.upper(), v).replace(' ', NOBREAK_SPACE).replace('-', NOBREAK_HYPHEN)
                        myBioList.append(bio + NOBREAK_SPACE * 3 + ' ')    # add space to use as a line break if needed

                    if castDict[item]['Awards']:
                        myBioList.append('\nAwards:' + NOBREAK_SPACE * 150)
                        myBioList.extend(castDict[item]['Awards'])

                    if castDict[item]['Films']:
                        myBioList.append('\nFilmography:' + NOBREAK_SPACE * 150)
                        myBioList.extend(castDict[item]['Films'])

                    summary = ' '.join(myBioList)

                    entry = '{0} {1}[d]'.format(COLCAST, entry) if re.search(deathRegex, summary, re.IGNORECASE) else '{0} {1}'.format(COLCAST, entry)
                    myNationality = castDict[item]['Nationality'].split(',')[-1].strip() if castDict[item]['Nationality'] else ''
                    if myNationality:
                        nationalities.add(myNationality)
                    myFlag = os.path.join(PGMA_COUNTRYART, '{0}.png'.format(myNationality)) if myNationality else ''
                    art =  myFlag if os.path.exists(myFlag) else '' if not myFlag else errorCountryArt
                    collectionsDict[entry] = {'Poster': castDict[item]['Photo'], 'Art': art, 'Summary': summary}

        except Exception as e:
            log('UTILS :: Error setting Cast: %s', e)
            FILMDICT['Status'] = False
            return

        # 2f.   Directors
        log(LOG_SUBLINE)
        try:
            if RESETMETA:
                metadata.directors.clear()

            directors = myAgentDict['Directors']
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('2f. Director(s)'), '{0:>2} - {1}'.format(len(directors), directors)))
            tempDict = getDirectors(directors, FILMDICT)
            directorDict = {k.split('(')[0].strip():v for (k,v) in tempDict.items()}
            for idx, item in enumerate(sorted(directorDict), start=1):
                # to create unique cast vs direcotr entries - replace all spaces with no-break space and end with it
                entry = directorDict[item]['RealName'] if directorDict[item]['RealName'] else item
                entry += ' '
                entry = entry.replace(' ', NOBREAK_SPACE)
                newDirector = metadata.directors.new()
                newDirector.name = entry
                newDirector.photo = directorDict[item]['Photo'] if 'iafd_ad' not in directorDict[item]['Photo'] and directorDict[item]['Photo'] else 'https://www.iafd.com/graphics/headshots/nophoto340.jpg'
                log('UTILS :: {0:<29} {1}'.format('Director' if idx == 1 else '', '{0:>2} - {1}'.format(idx, item)))
                if COLDIRECTOR:
                    if 'nophoto' in newDirector.photo:
                        directorDict[item]['Photo'] = NODIRECTOR_POSTER
                        if directorDict[item]['URL']:      # artiste has no photo but has entry on IAFD, check if there is a photo on disk #### still not fully implemented
                            #   https://www.iafd.com/person.rme/perfid=zakspears/gender=d/zak-spears.htm -> zakspears#zak-spears
                            directorPhoto = directorDict[item]['URL'].split('perfid=')[1].split('.htm')[0].replace('/gender=d/', '#')
                            directorDict[item]['Photo'] = PGMA_DIRECTORDICT.get(directorPhoto, NODIRECTOR_POSTER)

                    myBioList = []
                    myBioDict = OrderedDict(sorted(directorDict[item]['Bio'].items()))
                    for count, (k, v) in enumerate(myBioDict.items(), start=1):
                        bio = '{0}. {1}: {2}'.format(count, k.upper(), v).replace(' ', NOBREAK_SPACE).replace('-', NOBREAK_HYPHEN)
                        myBioList.append(bio + NOBREAK_SPACE * 3 + ' ')    # add space to use as a line break if needed

                    if directorDict[item]['Awards']:
                        myBioList.append('\nAwards:' + NOBREAK_SPACE * 150)
                        myBioList.extend(directorDict[item]['Awards'])

                    if directorDict[item]['Films']:
                        myBioList.append('\nFilmography:' + NOBREAK_SPACE * 150)
                        myBioList.extend(directorDict[item]['Films'])

                    summary = ' '.join(myBioList)
                    entry = '{0} {1}[d]'.format(COLDIRECTOR, entry) if re.search(deathRegex, summary, re.IGNORECASE) else '{0} {1}'.format(COLDIRECTOR, entry)
                    myNationality = directorDict[item]['Nationality'].split(',')[-1].strip() if directorDict[item]['Nationality'] else ''
                    if myNationality:
                        nationalities.add(myNationality)
                    myFlag = os.path.join(PGMA_COUNTRYART, '{0}.png'.format(myNationality)) if myNationality else ''
                    art =  myFlag if os.path.exists(myFlag) else '' if not myFlag else errorCountryArt
                    collectionsDict[entry] = {'Poster': directorDict[item]['Photo'], 'Art': art, 'Summary': summary}

        except Exception as e:
            log('UTILS :: Error setting Director(s): %s', e)
            FILMDICT['Status'] = False
            return

        # 2g.   Countries
        log(LOG_SUBLINE)
        countryArt = ''
        countryPoster = ''
        try:
            if RESETMETA:
                metadata.countries.clear()

            listCountries = [nationalities, myAgentDict['Countries']]
            if myAgent != 'IAFD' and 'IAFD' in FILMDICT:
                listCountries.append(FILMDICT['IAFD']['Countries'])

            # at this stage listCountries is a list of 3 sets, do a union
            listCountries = list(set().union(*listCountries))
            listCountries.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('2g. Countries', '{0:>2} - {1}'.format(len(listCountries), listCountries)))
            for idx, item in enumerate(listCountries, start=1):
                countryArt = os.path.join(PGMA_COUNTRYART, '{0}.png'.format(item))
                countryArt = countryArt if os.path.exists(countryArt) else errorCountryArt

                # use map as country posters, if missing use vertical flag of country or error flag if that is also missing
                flagPoster = os.path.join(PGMA_COUNTRYPOSTERFLAGS, '{0}.png'.format(item))
                if COUNTRYPOSTERTYPE == 'Map':
                    mapPoster = os.path.join(PGMA_COUNTRYPOSTERMAPS, '{0}.jpg'.format(item))
                    countryPoster = mapPoster if os.path.exists(mapPoster) else flagPoster if os.path.exists(flagPoster) else errorCountryPosterFlag
                else:
                    # use vertical flag as poster or error flag if missing
                    countryPoster = flagPoster if os.path.exists(flagPoster) else errorCountryPosterFlag

                log('UTILS :: {0:<29} {1}'.format('Country' if idx == 1 else '', '{0:>2} - {1}'.format(idx, item)))
                metadata.countries.add(item)
                # Process Countries
                if COLCOUNTRY:
                    entry = '{0} {1}'.format(COLCOUNTRY, item)
                    collectionsDict[entry] = {'Poster': countryPoster, 'Art': countryArt, 'Summary': ''}

        except Exception as e:
            log('UTILS :: Error setting Countries: %s', e)
            FILMDICT['Status'] = False
            return

        # 2h.   Posters - Front Cover of DVD
        # There is no working way to reset posters
        log(LOG_SUBLINE)
        try:
            if RESETMETA:
                for key in metadata.posters.keys():
                    del metadata.posters[key]
                    metadata.posters.validate_keys([])

            poster = myAgentDict['Poster']
            log('UTILS :: {0:<29} {1}'.format('2h. Poster Images', poster if poster else 'None Found'))
            for idx, item in enumerate(poster, start=1):
                if FILMDICT['SceneAgent'] is True:
                    image, imageContent = getFilmImages(imageType='Poster', imageLocation=item, whRatio=1.5) 
                else:
                    image = item
                    imageContent = HTTP.Request(image).content

                log('UTILS :: {0:<29} {1}'.format('Poster' if idx == 1 else '', '{0:>2} - {1}'.format(idx, image)))
                metadata.posters[image] = Proxy.Media(imageContent, sort_order=idx)

            # save poster to disk
            if poster and 'Yes' in POSTERSOURCEDOWNLOAD:
                idx = 0 if 'Local' in POSTERSOURCEDOWNLOAD else -1
                item = poster[idx]
                extension = item.split('.')[-1].split('?')[0]
                filename = os.path.splitext(media.items[0].parts[0].file)[0]
                downloadPoster = '{0}.{1}'.format(filename, extension)
                PlexSaveFile(downloadPoster, imageContent)

        except Exception as e:
            log('UTILS :: Error setting Poster: %s', e)         # do not fail scrape if poster can not be set

        # 2i.   Art - Back Cover of DVD : Determined by user preference
        # There is no working way to reset Art
        log(LOG_SUBLINE)
        try:
            if USEBACKGROUNDART:
                if RESETMETA:
                    for key in metadata.art.keys():
                        del metadata.art[key]
                        metadata.art.validate_keys([])

                art = myAgentDict['Art']
                log('UTILS :: {0:<29} {1}'.format('2i. Art Images', art if art else 'None Found'))
                for idx, item in enumerate(art, start=1):
                    if FILMDICT['SceneAgent'] is True:
                        image, imageContent = getFilmImages(imageType='Art', imageLocation=item, whRatio=1.5) 
                    else:
                        image = item
                        imageContent = HTTP.Request(image).content

                    log('UTILS :: {0:<29} {1}'.format('Art' if idx == 1 else '', '{0:>2} - {1}'.format(idx, image)))
                    metadata.art[image] = Proxy.Media(imageContent, sort_order=idx)
            else:
                log('UTILS :: {0:<29} {1}'.format('Art Image', 'Not Set By Preference'))

        except Exception as e:
            log('UTILS :: Error setting Art: %s', e)          # do not fail scrape if art can not be set

        # 2j.   Reviews - Put all Scene information as default unless there are none and website has actual reviews
        log(LOG_SUBLINE)
        try:
            source = AGENT
            scenes = FILMDICT[source]['Scenes']
            if scenes == {} and 'IAFD' in FILMDICT and FILMDICT['IAFD']['Scenes'] != {}:
                scenes = FILMDICT['IAFD']['Scenes']
                source = 'IAFD'

            scenesLink = scenes.get('Link', '')
            if scenesLink:
                del scenes['Link']
                log('UTILS :: {0:<29} {1}'.format('2j. Scenes Link', '{0}: {1}'.format(source, scenesLink)))
                log('UTILS :: {0:<29} {1}'.format('Scenes', '{0}: {1} - {2}'.format(source, len(scenes), scenes)))
                if scenes != {}:
                    if RESETMETA:
                        metadata.reviews.clear()

                    for idx, item in enumerate(scenes, start=1):
                        scene = str(idx)
                        if not scenes[scene]['Text']:                     # if no review text - skip
                            continue
                        newReview = metadata.reviews.new()
                        newReview.author = scenes[scene]['Author']
                        newReview.link  = scenesLink
                        newReview.source = scenes[scene]['Source']
                        newReview.text = scenes[scene]['Text']
                        log('UTILS :: {0:<29} {1}'.format('Created Reviews' if idx == 1 else '', '{0}: {1}'.format(idx, newReview.author)))
                else:
                    log('UTILS :: Warning: No Scenes / Reviews Found!')

            else:
                log('UTILS :: Warning: Agent Has No Scenes / Reviews Set!')

        except Exception as e:
            log('UTILS :: Error setting Reviews: %s', e)
            FILMDICT['Status'] = False
            return

        # 2k.   Chapters - Put all Chapter Information here
        log(LOG_SUBLINE)
        try:
            chapters = myAgentDict['Chapters']
            log('UTILS :: {0:<29} {1}'.format('2k. Chapters', '{0} - {1}'.format(len(chapters), chapters)))

            if chapters != {}:
                if RESETMETA:
                    metadata.chapters.clear()
                for idx, item in enumerate(chapters, start=1):
                    chapter = str(idx)
                    newChapter = metadata.chapters.new()
                    newChapter.title = chapters[chapter]['Title']
                    newChapter.start_time_offset = chapters[chapter]['StartTime']
                    newChapter.end_time_offset = chapters[chapter]['EndTime']
                    log('UTILS :: {0:<29} {1}'.format('Created Chapters' if idx == 1 else '', '{0}: {1}'.format(idx, newChapter.title)))
            else:
                log('UTILS :: Warning: No Chapters Found!')

        except Exception as e:
            log('UTILS :: Error setting Chapters: %s', e)
            FILMDICT['Status'] = False
            return

        # 2l.   Summary = Synopsis with IAFD Legend
        log(LOG_SUBLINE)
        try:
            log('UTILS :: {0:<29} {1}'.format('2l. Summary', ''))
            synopsis = myAgentDict['Synopsis']
            if not synopsis:
                if 'IAFD' in FILMDICT and FILMDICT['IAFD']['Synopsis']:
                    synopsis = FILMDICT['IAFD']['Synopsis']
                    log('UTILS :: {0:<29} {1}'.format('IAFD Synopsis', 'Website Synopsis Absent'))

            # translate if synopsis not in library language
            synopsis = TranslateString(synopsis, SITE_LANGUAGE, FILMDICT['lang'], DETECT)

            # combine and update
            log(LOG_SUBLINE)
            summary = ('{0}\n{1}' if PREFIXLEGEND else '{1}\n{0}').format(FILMDICT['Legend'], synopsis.strip())
            summary = summary.replace('\n\n', '\n')
            summaryList = wrap(summary, 100)
            for idx, summaryLine in enumerate(summaryList):
                log('UTILS :: {0:<29} {1}'.format('Summary with Legend' if idx == 0 else '', summaryLine.replace('\n', '')))

            if RESETMETA:
                metadata.summary = ' ' 

            metadata.summary = summary

        except Exception as e:
            synopsis = ''
            log('UTILS :: Error getting Synopsis: %s', e)
            FILMDICT['Status'] = False
            return

        # 2m.   Set Collection
        log(LOG_SUBLINE)
        log('UTILS :: {0: <29} {1}'.format('2m. Collections', ''))
        try:
            studio = FILMDICT['Studio']
            if COLSERIES:
                # Process Agent Website Series
                try:
                    if myAgentDict['Collections']:
                        websiteCollectionList = myAgentDict['Collections']
                        for idx, item in enumerate(websiteCollectionList, start=1):
                            entry = '{0} {1}: {2}'.format(COLSTUDIO if COLSTUDIO else COLSERIES, studio, item)
                            collectionsDict[entry] = {'Poster': '', 'Art': countryArt, 'Summary': ''}
                except Exception as e:
                    log('UTILS :: Error Collating Website Series Collections: %s', e)

                # Process Series from File Name
                try:
                    seriesList = FILMDICT['Series']
                    for idx, item in enumerate(seriesList, start=1):
                        entry = '{0} {1}: {2}'.format(COLSTUDIO if COLSTUDIO else COLSERIES, studio, item)
                        collectionsDict[entry] = {'Poster': '', 'Art': countryArt, 'Summary': ''}

                except Exception as e:
                    log('UTILS :: Error Collating Derived Series Collections: %s', e)

            # Process Studio Name:
            if COLSTUDIO:
                entry = '{0} {1}'.format(COLSTUDIO, studio)
                collectionsDict[entry] = {'Poster': '', 'Art': countryArt, 'Summary': ''}

            # System Collections
            if COLSYSTEM:
                try:
                    # Agent Collection
                    entry = '{0} {1}'.format(COLSYSTEM, myAgent)
                    collectionsDict[entry] = {'Poster': AGENT_POSTER, 'Art': '', 'Summary': ''}

                    # IAFD : On or Not On - Collection
                    entry = '{0} {1}-IAFD'.format(COLSYSTEM, 'On' if FILMDICT['FoundOnIAFD'] == 'Yes' else 'Not On')
                    collectionsDict[entry] = {'Poster': IAFDFOUND_POSTER if FILMDICT['FoundOnIAFD'] == 'Yes' else IAFDNOTFOUND_POSTER, 
                                              'Art': IAFDFOUND_POSTER if FILMDICT['FoundOnIAFD'] == 'Yes' else IAFDNOTFOUND_POSTER, 
                                              'Summary': ''}

                    # stacked or Not Stacked Collection
                    entry = '{0} {1}'.format(COLSYSTEM, 'Stacked' if FILMDICT['Stacked'] == 'Yes' else 'Not Stacked')
                    collectionsDict[entry] = {'Poster': STACKED_POSTER if FILMDICT['Stacked'] == 'Yes' else NOTSTACKED_POSTER, 
                                              'Art': STACKED_POSTER if FILMDICT['Stacked'] == 'Yes' else NOTSTACKED_POSTER, 
                                              'Summary': ''}

                    # Compilation Collection
                    if FILMDICT['Compilation'] == 'Yes':
                        entry = '{0} {1}{2}'.format(COLSYSTEM, prefix, 'Compilations')
                        collectionsDict[entry] = {'Poster': COMPILATIONS_POSTER, 
                                                  'Art': COMPILATIONS_POSTER, 
                                                  'Summary': ''}

                except Exception as e:
                    log('UTILS :: Error Collating System Collections: %s', e)

            # List the collections
            for idx, item in enumerate(sorted(collectionsDict.keys()), start=1):
                log('UTILS :: {0:<29} {1}'.format('{0}'.format('Collections' if idx == 1 else ''), '{0:>2} - {1:<30} - {2}'.format(idx, item, collectionsDict[item])))

        except Exception as e:
            log('UTILS :: Error collating Collections: %s', e)
            FILMDICT['Status'] = False
            return

        # Add to Metadata
        if RESETMETA:
            metadata.collections.clear()

        log(LOG_SUBLINE)
        try:
            plexBaseURL = 'http://127.0.0.1:32400'

            ssn = requests.Session()
            ssn.headers.update({'Accept': 'application/json'})
            ssn.params.update({'X-Plex-Token': PLEXTOKEN})
            machineID = ssn.get('{0}/'.format(plexBaseURL)).json()['MediaContainer']['machineIdentifier']

            for idx, entry in enumerate(sorted(collectionsDict.keys()), start=1):
                myDictionary = collectionsDict.get(entry)
                if myDictionary is None:
                    continue

                log('UTILS :: {0:<29} {1}'.format('{0}'.format('Entry'), '{0:>2} - {1} - {2}'.format(idx, entry, myDictionary)))

                # create collection title - depending on type of collection i.e. Cast, Director, Studio, Series - replace standard spaces with alternate spaces
                if COLCAST in entry:
                    title = entry.replace(COLCAST, '').replace('[d]', '').strip()
                elif COLDIRECTOR in entry:            # add space to string then replace spaces with no-break space - to give differention to single name director artists to single named cast artists
                    title = entry.replace(COLDIRECTOR, '').replace('[d]', '').strip()
                    title += ' '
                    title = title.replace(' ', NOBREAK_SPACE)
                elif COLSTUDIO in entry:             # add space to string then replace spaces with en-space
                    title = entry.replace(COLSTUDIO, '').strip()
                    title += ' '
                    title = title.replace(' ', EN_SPACE)
                elif COLSERIES in entry:             # add space to string then replace spaces with en-space
                    title = entry.replace(COLSERIES, '').strip()
                    title += ' '
                    title = title.replace(' ', EN_SPACE)
                else:
                    title = re.sub('\|\d\|', '', entry).strip()

                log('UTILS :: {0:<29} {1}'.format('Collection Title', title))
                metadata.collections.add(title)

                # get rating key if collection exists else create
                ratingKey = ''
                createdRatingKey = False
                collections = ssn.get('{0}/library/sections/{1}/collections'.format(plexBaseURL, FILMDICT['LibraryID'])).json()['MediaContainer'].get('Metadata',[])
                for collection in collections:
                    if title == collection.get('title'):
                        ratingKey = collection.get("ratingKey", '')
                        break
                else:
                    data = '{0}/library/collections'.format(plexBaseURL)
                    uri = 'server://{0}/com.plexapp.plugins.library/library/metadata/'.format(machineID)
                    parameters = {'title': title, 'smart': '0', 'sectionId': FILMDICT['LibraryID'], 'type': 1, 'uri': uri}
                    r = ssn.post(data, params=parameters)
                    ratingKey = r.json()['MediaContainer']['Metadata'][0]['ratingKey']
                    createdRatingKey = True

                if not ratingKey:
                    log('UTILS :: Error Establishing Enhanced Collection Rating Key')
                    log(LOG_SUBLINE)
                    continue

                log('UTILS :: {0:<29} {1}'.format('{0} Rating Key'.format('Created' if createdRatingKey else 'Found'), ratingKey))

                #   Set Sort Title: from entry string
                try:
                    # place the default system icons before the agent icons in the following order
                    if entry == '|1| On-IAFD':
                        titleSort = entry.replace('|1| On-IAFD', '|0.0| IAFD:Yes').replace('|1|', '|0|')             # on IAFD
                    elif entry == '|1| Not On-IAFD':
                        titleSort = entry.replace('|1| Not On-IAFD', '|0.1| IAFD:No').replace('|1|', '|0|')          # Not on IAFD
                    elif entry == '|1| Not Stacked':
                        titleSort = entry.replace('|1| Not Stacked', '|0.2| Stacked:No').replace('|1|', '|0|')       # films in parts/disks
                    elif entry == '|1| Stacked':
                        titleSort = entry.replace('|1| Stacked', '|0.3| Stacked:Yes').replace('|1|', '|0|')          # full films
                    elif entry == '|1| Compilations':
                        titleSort = entry.replace('|1| Compilations', '|0.4| Compilations')                          # place after IAFD and Stacked
                    elif '[d]' in entry:
                        titleSort = entry.replace('[d]', '')                                                         # remove death marker
                    else:
                        titleSort = entry

                    log('UTILS :: {0:<29} {1}'.format('Sort Title:', titleSort))
                    payload = {'type': 18, 'id': ratingKey}
                    payload['titleSort.value'] = titleSort
                    payload['titleSort.locked'] = 1
                    ssn.put('{0}/library/sections/{1}/all'.format(plexBaseURL, FILMDICT['LibraryID']), params=payload)
                except Exception as e:
                    log('UTILS :: Error setting Collection Sort Title: %s', e)

                #   Set poster
                poster = myDictionary.get('Poster', '')
                if poster:
                    try:
                        log('UTILS :: {0:<29} {1}'.format('Poster:', poster))
                        data = getImage(poster, entry, 'Poster')
                        ssn.post('{0}/library/collections/{1}/posters'.format(plexBaseURL, ratingKey), data=data, stream=True)
                    except Exception as e:
                        log('UTILS :: Error setting Collection Poster: %s', e)

                #   Set Collection Art
                art = myDictionary.get('Art', '')
                if art:
                    try:
                        log('UTILS :: {0:<29} {1}'.format('Art:', art))
                        data = getImage(art, entry, 'Art')                 #data = ssn.get(art).content
                        ssn.post('{0}/library/collections/{1}/arts'.format(plexBaseURL, ratingKey), data=data, stream=True)
                    except Exception as e:
                        log('UTILS :: Error setting Collection Art: %s', e)

                #   Set Summary: None set for Genres
                summary = myDictionary.get('Summary', '')
                if summary:
                    try:
                        payload = {'type': 18, 'id': ratingKey}
                        payload['summary.value'] = summary
                        payload['summary.locked'] = 1
                        ssn.put('{0}/library/sections/{1}/all'.format(plexBaseURL, FILMDICT['LibraryID']), params=payload)
                        summary = [x.strip() for x in summary.split(' ') if x.strip()]
                        for idx2, item in enumerate(summary, start=1):
                            log('UTILS :: {0:<29} {1}'.format('Summary:' if idx2 == 1 else '', item))
                    except Exception as e:
                        log('UTILS :: Error setting Collection Summary: %s', e)

                log(LOG_BIGLINE)

        except Exception as e:
            log('UTILS :: Error Creating Enhanced Collections: %s', e)
            FILMDICT['Status'] = False
            return

        # 2n.   Set Originally Available Date - From website's release date if only it is earlier in the same year
        log(LOG_BIGLINE)
        try:
            log('UTILS :: {0:<29} {1}'.format('2n. Originally Available Date', ''))
            releaseDate = myAgentDict['ReleaseDate'].date()
            log('UTILS :: {0:<29} {1}'.format('Agent Date', releaseDate))

            metadata.originally_available_at = releaseDate
            metadata.year = metadata.originally_available_at.year
            log('UTILS :: {0:<29} {1}'.format('Current Date', metadata.originally_available_at))
            log('UTILS :: {0:<29} {1}'.format('Current Year', metadata.year))

        except Exception as e:
            log('UTILS :: Error setting Originally Available Date: %s', e)
            FILMDICT['Status'] = False
            return

    except Exception as e:
        FILMDICT['Status'] = False
    else:
        FILMDICT['Status'] = True

# ----------------------------------------------------------------------------------------------------------------------------------
def setupStartVariables():
    ''' used by start routine to set up Tidy Genres, Countries List and Show Preference Settings'''
    global START_SCRAPE

    # preferences
    global COLCAST, COLCOUNTRY, COLGENRE, COLDIRECTOR, COLSERIES, COLSTUDIO, COLSYSTEM
    global COUNTRYPOSTERTYPE, POSTERSOURCEDOWNLOAD, DETECT, DURATIONDX, PREFIXGENRE
    global MATCHIAFDDURATION, MATCHSITEDURATION, PLEXTOKEN, PREFIXLEGEND, RESETMETA, THUMBOR, USEBACKGROUNDART

    # variables
    global COUNTRYSET, GENRESDICT, TIDYDICT, PGMA_CASTDICT, PGMA_DIRECTORDICT

    START_SCRAPE = 'No'

    log(LOG_ASTLINE)
    log(LOG_ASTLINE)
    #   1.    Plex Support Path and preferences
    log('START :: 1.\tPlex System')
    log('START :: {0:<29} {1}'.format('\tAgent', '{0} v.{1}'.format(AGENT, VERSION_NO)))
    log('START :: {0:<29} {1}'.format('\tPython', '{0} - {1} - {2}'.format(platform.python_version(), platform.architecture()[0], platform.python_build())))
    log('START :: {0:<29} {1}'.format('\tOperating System', platform.system()))
    log('START :: {0:<29} {1}'.format('\tRelease:', platform.release()))
    log('START :: {0:<29} {1}'.format('\tPlex Support Path', PlexSupportPath))
    continueSetup = True if os.path.isdir(PlexSupportPath) else False

    #   2.    Agent Preference Settings
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('START :: 2.\tAgent Preference Settings')
        log('START :: {0:<29} {1}'.format('\tAgent Type', AGENT_TYPE))
        defaultPrefs_json = os.path.join(PlexSupportPath, 'Plug-ins', '{0}.bundle'.format(AGENT), 'Contents', 'DefaultPrefs.json')
        log('START :: {0:<29} {1}'.format('\tDefault Preferences', os.path.relpath(defaultPrefs_json, PlexSupportPath)))
        if os.path.isfile(defaultPrefs_json):
            try:
                json = JSON.ObjectFromString(PlexLoadFile(defaultPrefs_json), encoding=None)  ### Load 'DefaultPrefs.json' to have access to default settings ###
                if not json:
                    raise Exception('< Could Not Read Default Prefs! >')

                log('START :: {0:<29} {1}'.format('\tLoaded', defaultPrefs_json))
                log('START :: {0:<29} {1}'.format('\tPreferences:', len(json)))
                idx = 0
                for entry in json:                   #Build Pref_list dict from json file
                    idx += 1
                    prefName =  entry['id']
                    defSet =  entry['default']
                    setAs = Prefs[prefName] if prefName != 'plextoken' else '********'              # hide token in logs
                    log('START :: {0:<29} {1}'.format('\t{0:>2}. {1}'.format(idx, prefName), 'Default = {0:<10} Set As = {1}'.format(defSet, setAs)))

                COLSYSTEM = '|1|' if Prefs['systemcollection'] else ''
                COLGENRE = '|2|' if Prefs['genrecollection'] != 'No' else ''        # if a colour set is chose - genre collection is on
                COLCOUNTRY = '|3|' if Prefs['countrycollection'] else ''
                COLSTUDIO = '|4|' if Prefs['studiocollection'] else ''
                COLSERIES = '|5|' if Prefs['seriescollection'] else ''
                COLDIRECTOR = '|6|' if Prefs['directorcollection']  else ''
                COLCAST = '|7|' if Prefs['castcollection'] else ''

                # Other Preferences
                COUNTRYPOSTERTYPE = Prefs['countrypostertype']        # show poster as map or vertical flag
                DETECT = Prefs['detect']                              # detect the language the summary appears in on the web page
                DURATIONDX = int(Prefs['durationdx'])                 # Acceptable difference between actual duration of video file and that on agent website
                PREFIXGENRE = Prefs['prefixgenre']                    # prefix genres with agent sexuality type - useful for mixed content plex servers
                MATCHIAFDDURATION = Prefs['matchiafdduration']        # Match against IAFD Duration value
                MATCHSITEDURATION = Prefs['matchsiteduration']        # Match against Site Duration value
                PLEXTOKEN = Prefs['plextoken']                        # Plex token from View XML of any library item
                POSTERSOURCEDOWNLOAD = Prefs['postersourcedownload']  # Down film poster to disk, (renamed as film title + image extension)
                PREFIXLEGEND = Prefs['prefixlegend']                  # place cast legend at start of summary or end
                RESETMETA = Prefs['resetmeta']                        # clear previously set metadata
                USEBACKGROUNDART = Prefs['usebackgroundart']          # Use background art

            except Exception as e:
                log('START :: Error Loading Default Preferences File: %s', e)
                continueSetup = False


    #   3. PGMA - Folder Location, where all general files needed for the PGMA Agents are stored, like posters, gayTidy, Countries et cetera
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('START :: 3.\tPGMA Usage Folder Locations')
        global PGMA_FOLDER, PGMA_CASTFACEFOLDER, PGMA_DIRECTORFACEFOLDER, PGMA_CASTPOSTERFOLDER, PGMA_DIRECTORPOSTERFOLDER, PGMA_COUNTRYART, PGMA_COUNTRYPOSTERFLAGS, PGMA_COUNTRYPOSTERMAPS, PGMA_GENREFOLDER
        PGMA_FOLDER = os.path.join(PlexSupportPath, 'Plug-ins', '_PGMA')
        PGMA_SYSTEMFOLDER = os.path.join(PGMA_FOLDER, 'System')
        PGMA_CASTFACEFOLDER = os.path.join(PGMA_FOLDER, 'Cast', 'Face')
        PGMA_CASTPOSTERFOLDER = os.path.join(PGMA_FOLDER, 'Cast', 'Poster')
        PGMA_DIRECTORFACEFOLDER = os.path.join(PGMA_FOLDER, 'Director', 'Face')
        PGMA_DIRECTORPOSTERFOLDER = os.path.join(PGMA_FOLDER, 'Director', 'Poster')
        PGMA_COUNTRYART = os.path.join(PGMA_FOLDER, 'Country', 'Art')
        PGMA_COUNTRYPOSTERFLAGS = os.path.join(PGMA_FOLDER, 'Country', 'Poster', 'Flags')
        PGMA_COUNTRYPOSTERMAPS = os.path.join(PGMA_FOLDER, 'Country', 'Poster', 'Maps')
        PGMA_GENREFOLDER = os.path.join(PGMA_FOLDER, 'Genre', Prefs['genrecollection']) if Prefs['genrecollection'] != 'No' else os.path.join(PGMA_FOLDER, 'Genre')

        PGMA_FOLDER = PGMA_FOLDER if os.path.isdir(PGMA_FOLDER) else ''
        PGMA_SYSTEMFOLDER = PGMA_SYSTEMFOLDER if os.path.isdir(PGMA_SYSTEMFOLDER) else ''
        PGMA_GENREFOLDER = PGMA_GENREFOLDER if os.path.isdir(PGMA_GENREFOLDER) else ''
        PGMA_COUNTRYART = PGMA_COUNTRYART if os.path.isdir(PGMA_COUNTRYART) else ''
        PGMA_COUNTRYPOSTERFLAGS = PGMA_COUNTRYPOSTERFLAGS if os.path.isdir(PGMA_COUNTRYPOSTERFLAGS) else ''
        PGMA_COUNTRYPOSTERMAPS = PGMA_COUNTRYPOSTERMAPS if os.path.isdir(PGMA_COUNTRYPOSTERMAPS) else ''
        PGMA_CASTFACEFOLDER = PGMA_CASTFACEFOLDER if os.path.isdir(PGMA_CASTFACEFOLDER) else ''
        PGMA_DIRECTORFACEFOLDER = PGMA_DIRECTORFACEFOLDER if os.path.isdir(PGMA_DIRECTORFACEFOLDER) else ''
        PGMA_CASTPOSTERFOLDER = PGMA_CASTPOSTERFOLDER if os.path.isdir(PGMA_CASTPOSTERFOLDER) else ''
        PGMA_DIRECTORPOSTERFOLDER = PGMA_DIRECTORPOSTERFOLDER if os.path.isdir(PGMA_DIRECTORPOSTERFOLDER) else ''

        log('START :: {0:<29} {1}'.format('\tPGMA Folder Location', PGMA_FOLDER if PGMA_FOLDER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\t              System', PGMA_SYSTEMFOLDER if PGMA_SYSTEMFOLDER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\t              Genres', PGMA_GENREFOLDER if PGMA_GENREFOLDER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\t         Country Art', PGMA_COUNTRYART if PGMA_COUNTRYART else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\tCountry Poster Flags', PGMA_COUNTRYPOSTERFLAGS if PGMA_COUNTRYPOSTERFLAGS else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\t Country Poster Maps', PGMA_COUNTRYPOSTERMAPS if PGMA_COUNTRYPOSTERMAPS else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\t          Cast Faces', PGMA_CASTFACEFOLDER if PGMA_CASTFACEFOLDER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\t        Cast Posters', PGMA_CASTPOSTERFOLDER if PGMA_CASTPOSTERFOLDER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\t      Director Faces', PGMA_DIRECTORFACEFOLDER if PGMA_DIRECTORFACEFOLDER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\t    Director Posters', PGMA_DIRECTORPOSTERFOLDER if PGMA_DIRECTORPOSTERFOLDER else '** FAIL **'))

        # only contunue with setup if all folders are present
        continueSetup = (bool(PGMA_FOLDER) and bool(PGMA_SYSTEMFOLDER) and bool(PGMA_CASTFACEFOLDER) and bool(PGMA_DIRECTORFACEFOLDER) and bool(PGMA_CASTPOSTERFOLDER) and 
                         bool(PGMA_DIRECTORPOSTERFOLDER) and bool(PGMA_COUNTRYART) and bool(PGMA_COUNTRYPOSTERFLAGS) and bool(PGMA_COUNTRYPOSTERMAPS) and bool(PGMA_GENREFOLDER))

    #   4. PGMA - On disk Cast and Director Collection Posters
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('START :: 4.\tPGMA Cast and Director Collection Poster Dictionaries')
        PGMA_CASTDICT = {}
        PGMA_DIRECTORDICT = {}
        try:
            PGMA_CASTDICT = {x.rsplit('.', 1)[0]:os.path.join(PGMA_CASTPOSTERFOLDER, x) for x in os.listdir(PGMA_CASTPOSTERFOLDER)}
            log('START :: {0:<29} {1}'.format('\tCast Collection Posters', '{0:>4} - {1}'.format(len(PGMA_CASTDICT), PGMA_CASTDICT)))

            PGMA_DIRECTORDICT = {x.rsplit('.', 1)[0]:os.path.join(PGMA_DIRECTORPOSTERFOLDER, x) for x in os.listdir(PGMA_DIRECTORPOSTERFOLDER)}
            log('START :: {0:<29} {1}'.format('\tDirector Collection Posters', '{0:>4} - {1}'.format(len(PGMA_DIRECTORDICT), PGMA_DIRECTORDICT)))

        except Exception as e:
            log('START :: Error creating Local Cast and Director Collection Poster Dictionaries: %s', e)
            continueSetup = False

    #   5. Country Dictionary: create dictionary containing countries and flag urls from Country.txt located in plugins code directory
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('START :: 5.\tPrepare Dictionary of Country Names and Flags')
        COUNTRYSET = set() 
        try:
            countries_txt = os.path.join(PGMA_FOLDER, 'Countries.txt')
            txtfile = PlexLoadFile(countries_txt)
            txtrows = txtfile.split('\n')
            for idx, row in enumerate(txtrows, start=1):
                COUNTRYSET.add(row.strip())

            log('START :: {0:<29} {1}'.format('\tCountry Dictionary', '{0:>4} - {1}'.format(len(COUNTRYSET), sorted(COUNTRYSET))))

        except Exception as e:
            log('START :: Error creating Country Dictionary: %s', e)
            log('START :: Error: Country Source File: %s', countries_txt)
            continueSetup = False

    #   6. Genres Dictionary: create dictionary containing genres and image urls from Genres.txt located in plugins code directory
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('START :: 6.\tPrepare Dictionary of Genres and Symbols')
        GENRESDICT = {}
        try:
            genreFiles = ['Genres.txt', 'UserGenres.txt']
            genres_txt = ''
            log('START :: {0:<29} {1}'.format('\tTidy Files', genreFiles))
            for genreFile in genreFiles:
                genres_txt = os.path.join(PGMA_FOLDER, genreFile)
                if not os.path.isfile(genres_txt):        # skip files that are missing
                    continue

                txtfile = PlexLoadFile(genres_txt)
                txtrows = txtfile.split('\n')
                for idx, row in enumerate(txtrows, start=1):
                    if '::' not in row:
                        log('START :: {0:<29} {1}'.format('\tInvalid Format Row', 'Row {0} - {1}'.format(idx, row)))
                        continue

                    keyValue = row.split('::')
                    keyValue = [x.strip() for x in keyValue]
                    key =  keyValue[0].lower()

                    if key in GENRESDICT:
                        log('START :: {0:<29} {1}'.format('\t\t{0}: Duplicate Row - Replace Setting'.format(genreFile), 'Row {0} - {1}'.format(idx, row)))

                    value = os.path.join(PGMA_GENREFOLDER, keyValue[1])
                    GENRESDICT[key] = value

            log('START :: {0:<29} {1}'.format('\tGenres Dictionary', '{0:>4} - {1}'.format(len(GENRESDICT), sorted(GENRESDICT))))

        except Exception as e:
            log('START :: Error creating Genres Dictionary: %s', e)
            log('START :: Error: Genres Source File: %s', genres_txt)
            continueSetup = False

    #   7.     Tidy Genres: create dictionary containing the tidy genres from genres.txt file located in plugins code directory
    #                       unless second field is an 'x', it should appear in the COUNTRYSET or GENRESDICT
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('START :: 7.\tPrepare Tidied Dictionary of Genres and Countries')
        TIDYDICT = {}
        tidiedCountriesSet = set()                              # used for debugging
        tidiedGenresSet = set()                                 # used for debugging
        tidiedNullSet = set()                                   # used for debugging
        tidiedErrorSet = set()                                  # used for debugging
        try:
            # Main Tidy has to be first in list as user can make changes
            tidyFiles = ['GayTidy.txt', 'UserGayTidy.txt'] if AGENT_TYPE == '⚣' else ['StraightTidy.txt', 'UserStraightTidy.txt']
            tidy_txt = ''
            log('START :: {0:<29} {1}'.format('\tTidy Files', tidyFiles))
            for tidy in tidyFiles:
                tidy_txt = os.path.join(PGMA_FOLDER, tidy)
                if not os.path.isfile(tidy_txt):        # skip files that are missing
                    continue

                txtfile = PlexLoadFile(tidy_txt)
                txtrows = txtfile.split('\n')
                for idx, row in enumerate(txtrows, start=1):
                    if '::' not in row:
                        log('START :: {0:<29} {1}'.format('\t\t{0}: Invalid Format Row'.format(tidy), 'Row {0} - {1}'.format(idx, row)))
                        continue

                    keyValue = row.split('::')
                    keyValue = [x.strip() for x in keyValue]
                    key = keyValue[0].lower()
                    value = keyValue[1]
                    if key in TIDYDICT:
                        log('START :: {0:<29} {1}'.format('\t\t{0}: Duplicate Row - Replace Setting'.format(tidy), 'Row {0} - {1}'.format(idx, row)))

                    TIDYDICT[key] = value if value != 'x' else None
                    # The value must either be related to a Country, Genre or skipped otherwise its an error which is logged
                    if value in COUNTRYSET:
                        tidiedCountriesSet.add('{0} : {1}'.format(keyValue[0], value))
                    elif value.lower() in GENRESDICT:
                        tidiedGenresSet.add('{0} : {1}'.format(keyValue[0], value))
                    elif value == 'x':
                        tidiedNullSet.add('{0} : {1}'.format(keyValue[0], value))
                    else:
                        log('START :: {0:<29} {1}'.format('\t\t{0}: Not Found in Genres.txt'.format(tidy), 'Row {0} - {1}'.format(idx, row)))
                        tidiedErrorSet.add('{0} : {1}'.format(keyValue[0], value))

            log('START :: {0:<29} {1}'.format('\tOriginal Categories', '{0:>4} - {1}'.format(len(TIDYDICT), sorted(TIDYDICT.keys()))))
            log('START :: {0:<29} {1}'.format('\tTidied Countries', '{0:>4} - {1}'.format(len(tidiedCountriesSet), sorted(tidiedCountriesSet))))
            log('START :: {0:<29} {1}'.format('\tTidied Genres', '{0:>4} - {1}'.format(len(tidiedGenresSet), sorted(tidiedGenresSet))))
            log('START :: {0:<29} {1}'.format('\tNull Categories', '{0:>4} - {1}'.format(len(tidiedNullSet), sorted(tidiedNullSet))))
            log('START :: {0:<29} {1}'.format('\tError Categories', '{0:>4} - {1}'.format(len(tidiedErrorSet), sorted(tidiedErrorSet))))
            continueSetup = True if not tidiedErrorSet else False

        except Exception as e:
            log('START :: Error creating Tidy Categories Dictionary: %s', e)   
            log('START :: Error: Tidy Categories Source File: %s', tidy_txt)   
            continueSetup = False

    #   8.     Retrieve Plex Token
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('START :: 8.\tRetrieve Plex Token and Machine ID')
        PLEXTOKEN = Prefs['plextoken']
        if not PLEXTOKEN:
            preferences_file = ''
            if platform.system() == 'Windows':
                try:
                    import winreg
                    hKey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Plex, Inc.\Plex Media Server")
                    PLEXTOKEN = winreg.QueryValueEx(hKey, "PlexOnlineToken")[0]

                except Exception as e:
                    log('START :: {0:<29} {1}'.format('Failed to read registry: Search for Token Preferences.xml file', e))
                    try:
                        preferences_file = os.path.join(PlexSupportPath, 'Preferences.xml').replace('Plex', 'Plex\Plex')
                        preferenceFileContents = PlexLoadFile(preferences_file)
                        xml = XML.ElementFromString(preferenceFileContents)
                        PLEXTOKEN = xml.xpath('/Preferences/@PlexOnlineToken')[0]

                    except Exception as e:
                        log('START :: Error retrieving Plex Token: Input Manually in Preferences: %s', e)

                finally:
                    winreg.CloseKey(hKey)

            elif platform.system() == 'Linux':
                try:
                    preferences_file = os.path.join(PlexSupportPath, 'Preferences.xml')
                    preferenceFileContents = PlexLoadFile(preferences_file)
                    xml = XML.ElementFromString(preferenceFileContents)
                    PLEXTOKEN = xml.xpath('/Preferences/@PlexOnlineToken')[0]

                except Exception as e:
                    log('START :: Error retrieving Plex Token: Input Manually in Preferences: %s', e)

            elif platform.system() == 'Darwin':     # MAC OS
                try:
                    preferences_file = os.path.join(PlexSupportPath, 'Preferences', 'com.plexapp.plexmediaserver.plist').replace('Application Support/Plex Media Server', '')
                    preferences = plistlib.readPlist(preferences_file)
                    PLEXTOKEN = preferences['PlexOnlineToken']

                except Exception as e:
                    log('START :: Error retrieving Plex Token: Input Manually in Preferences: %s', e)

        log('START :: {0:<29} {1}'.format('\tPlex Token', 'Found' if PLEXTOKEN else 'Not Found'))

        continueSetup = True if PLEXTOKEN else False

    #   9. Retrieve Thumbor Address
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('START :: 9.\tRetrieve Thumbor Address')
        try:
            # Main Tidy has to be first in list as user can make changes
            thumbor_txt = os.path.join(PGMA_FOLDER, 'Thumbor.txt')
            log('START :: {0:<29} {1}'.format('\tThumbor File', thumbor_txt))
            THUMBOR = PlexLoadFile(thumbor_txt).strip()
            log('START :: {0:<29} {1}'.format('\tThumbor Address', THUMBOR))
            continueSetup = True if THUMBOR else False

        except Exception as e:
            log('START :: Error: Thumbor File missing or Empty: %s', thumbor_txt)   
            continueSetup = False

    #   10. Get paths to Default Posters for Agent, Compilations Genre, IAFD, Stacks
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('START :: 10.\tRetrieve Agent and Default Posters')
        global AGENT_POSTER, COMPILATIONS_POSTER, IAFDFOUND_POSTER, IAFDNOTFOUND_POSTER, STACKED_POSTER, NOTSTACKED_POSTER, NOCAST_POSTER, NODIRECTOR_POSTER, WATERMARK
        AGENT_POSTER = os.path.join(PGMA_SYSTEMFOLDER, '{0}.png'.format(AGENT))
        AGENT_POSTER = AGENT_POSTER if os.path.exists(AGENT_POSTER) else ''

        COMPILATIONS_POSTER = os.path.join(PGMA_SYSTEMFOLDER, 'Compilations.png')
        COMPILATIONS_POSTER = COMPILATIONS_POSTER if os.path.exists(COMPILATIONS_POSTER) else ''

        IAFDFOUND_POSTER = os.path.join(PGMA_SYSTEMFOLDER, 'IAFD-Found.png')
        IAFDFOUND_POSTER = IAFDFOUND_POSTER if os.path.exists(IAFDFOUND_POSTER) else ''

        IAFDNOTFOUND_POSTER = os.path.join(PGMA_SYSTEMFOLDER, 'IAFD-NotFound.png')
        IAFDNOTFOUND_POSTER = IAFDNOTFOUND_POSTER if os.path.exists(IAFDNOTFOUND_POSTER) else ''

        STACKED_POSTER = os.path.join(PGMA_SYSTEMFOLDER, 'Stacked-Yes.png')
        STACKED_POSTER = STACKED_POSTER if os.path.exists(STACKED_POSTER) else ''

        NOTSTACKED_POSTER = os.path.join(PGMA_SYSTEMFOLDER, 'Stacked-No.png')
        NOTSTACKED_POSTER = NOTSTACKED_POSTER if os.path.exists(NOTSTACKED_POSTER) else ''

        NOCAST_POSTER = os.path.join(PGMA_SYSTEMFOLDER, 'NoCast.png')
        NOCAST_POSTER = NOCAST_POSTER if os.path.exists(NOCAST_POSTER) else ''

        NODIRECTOR_POSTER = os.path.join(PGMA_SYSTEMFOLDER, 'NoDirector.png')
        NODIRECTOR_POSTER = NODIRECTOR_POSTER if os.path.exists(NODIRECTOR_POSTER) else ''

        WATERMARK = String.URLEncode(WATERMARK)

        log('START :: {0:<29} {1}'.format('\tAgent Poster', AGENT_POSTER if AGENT_POSTER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\tCompilations Poster', COMPILATIONS_POSTER if COMPILATIONS_POSTER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\tIAFD Poster', IAFDFOUND_POSTER if IAFDFOUND_POSTER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\tNot IAFD Poster', IAFDNOTFOUND_POSTER if IAFDNOTFOUND_POSTER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\tStacked Poster', STACKED_POSTER if STACKED_POSTER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\tNot Stacked Poster', NOTSTACKED_POSTER if NOTSTACKED_POSTER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\tNo Cast Poster', NOCAST_POSTER if NOCAST_POSTER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\tNo Director Poster', NODIRECTOR_POSTER if NODIRECTOR_POSTER else '** FAIL **'))
        log('START :: {0:<29} {1}'.format('\tWatermark', WATERMARK if WATERMARK else '** FAIL **'))

        # if any of the posters do not resolve we have to stop the Search Process: set GLOBAL variable and use later
        continueSetup = True if not tidiedErrorSet and AGENT_POSTER != '' and COMPILATIONS_POSTER != '' and IAFDFOUND_POSTER != '' and IAFDNOTFOUND_POSTER != '' and STACKED_POSTER != '' and NOTSTACKED_POSTER != '' and NOCAST_POSTER != '' and NODIRECTOR_POSTER != '' and PLEXTOKEN != '' and WATERMARK != '' else False

    #   Finish: Tidy Up - free up memory
    tidiedCountriesSet = None
    tidiedGenresSet = None
    tidiedNullSet = None
    tidiedErrorSet = None
    del(tidiedCountriesSet)
    del(tidiedGenresSet)
    del(tidiedNullSet)
    del(tidiedErrorSet)

    log(LOG_SUBLINE)
    log(LOG_SUBLINE)
    START_SCRAPE = 'Yes' if continueSetup is True else 'No'
    log('START :: {0:<29} {1}'.format('\tStart Scrape Process', START_SCRAPE))

    log(LOG_ASTLINE)
    log(LOG_ASTLINE)
    return True

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
def setDashesQuotes(myString):
    ''' replace all curly quotes and accent marks with their straight versions - replace all hyphes with a simple dash (minus) '''
    # replace single curly quotes and accent marks with straight quotes
    singleQuoteChars = [ur'\u2018', ur'\u2019', ur'\u0060', ur'\u00B4']
    pattern = u'({0})'.format('|'.join(singleQuoteChars))
    matched = re.search(pattern, myString)                  # match against whole string
    if matched:
        myString = re.sub(pattern, "'", myString)
        myString = ' '.join(myString.split())               # remove continous white space

    # replace double curly quotes with straight ones
    doubleQuoteChars = [ur'\u201C', ur'\u201D']
    pattern = u'({0})'.format('|'.join(doubleQuoteChars))
    matched = re.search(pattern, myString)                  # match against whole string
    if matched:
        myString = re.sub(pattern, '"', myString)
        myString = ' '.join(myString.split())               # remove continous white space

    dashChars = [ur'\u002D', ur'\u00AD', ur'\u207B', ur'\u208B', ur'\u2212', ur'\u02D7', ur'\u058A', ur'\u05BE', ur'\u1400', ur'\u1806', ur'\u2010', ur'\u2015', ur'\u2E17', ur'\u2E1A', ur'\u2E3A', ur'\u2E3B', ur'\u2E40', ur'\u301C', ur'\u3030', ur'\u30A0', ur'\uFE31', ur'\uFE32', ur'\uFE58', ur'\uFE63', ur'\uFF0D']
    pattern = u'({0})'.format('|'.join(dashChars))
    matched = re.search(pattern, myString)                  # match against whole string
    if matched:
        myString = re.sub(pattern, '-', myString)
        myString = ' '.join(myString.split())               # remove continous white space

    return myString

# ----------------------------------------------------------------------------------------------------------------------------------
def synopsisCountriesGenres(myString):
    ''' extract genres and countries from synopsis text'''
    genresSet = set()
    countriesSet = set()
    log('UTILS :: Extract Countries and Genres from Synopsis:')
    try:
        synopsis = myString.strip()
        if synopsis:
            idx = 0
            for key, value in TIDYDICT.items():
                if value is None or value == 'x':                               # skip if tidied out
                    continue

                if len(key) < 3:                                                # skip American and Canadian State Abbreviations
                    continue

                pattern = r'(?<![^ .,?!;]){0}(?![^ .,?!;\r\n])'.format(key)     # look for genre followed by punctuation or whitespace - to prevent stuff like "rio" in "priority"
                if re.search(pattern, synopsis, flags=re.IGNORECASE):
                    idx += 1
                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, key, value)))

                    if value in COUNTRYSET:
                        countriesSet.add(value)
                        continue

                    genresSet.add(value)

        showSetData(countriesSet, 'Countries (set*)')
        showSetData(genresSet, 'Genres (set*)')

    except Exception as e:
        log('UTILS :: Error Extract Countries and Genres from Synopsis: %s', e)

    finally:
        log(LOG_SUBLINE)

    return countriesSet, genresSet
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