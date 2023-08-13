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
    08 May 2021     Merged GenFunctions.py with py created by codeanator to deal with cloudscraper protection issues in IAFD
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
    08 Mar 2023     Error in Getting images BEP
    15 Apr 2023     Dealt with ² in titles as not used in IAFD titles
    27 Apr 2023     Improved code to retrieve cast from tags in WayBig, Fagalicious and QueerClick
    03 May 2023     Correction to tag processing in WayBig, Fagalicious and QueerClick
                    Standardise Quotes and Hyphens for matching between filenames and web entries
                    Remove Thumbor from preferences and put in Thumbor.txt file in _PGMA
    07 May 2023     Colour sets for Genre icons introduced
    14 May 2023     PGMA Discussion #241 - Cast Tags retrieval improved: Fagalicious, QueerClick and WayBig
                    Cast Tags - should be forename and surname unless actor has initials, strip trailing apostrophe from tags: Johns' becomes Johns
    19 May 2023     Cast Tags - assume Tags with special characters bar single apostrophe are not people
                    Included py latest modification date in Log Header
                    03 May 2023 update duplicated code in MakeASCII - duplicated code removed and replaced by enhanced MakeASCII
    23 May 2023     Correction to BEP to gather synopsis...
                    Correction to BEP to correctly capitalize collection titles
    27 May 2023     New scraper GEVIScenes - code added to accomodate it andregex altered. 
                    Detection of Gevi Scene No. in filename will stop processing in all other scrapers.
    25 Jun 2023     Correction to setting Cast
    01 Jul 2023     Waybig - change to xpath for retrieving images
    07 Jul 2023     GEVI/GEVIScenes - website design change - new xpath strings needed
                    Upgraded Warning Logs - to show file, function and line info
    10 Jul 2023     Error accessing watermark dictionary entry
    13 Jul 2023     Creation of IAFD 403 Error collection
                    Change in GEVI Scene, synopsis xpath
    16 Jul 2023     Correction to art image retrieval was failing in GEVI if only poster was present. similar code corrected for other agents
    27 Jul 2023     Solved IAFD 403 Issue: getHTTPRequest
                    Correction to code retrieving Library ID and Title
                    Correction to ContinueSetp code
                    Corrected code dealing with scenes for GEVI
                    disabled beautifulsoup for time being
    02 Aug 2023     Corrections to UpdateMetadata - was failing for IAFD...
                    Corections to "See More Results" link on IAFD - spaces in URL replace with %20
                    Corrections to removing roman numerals from IAFD Titles to improve matching
                    Added matching between recorded alternate studio names in Agent Websites against IAFD Distributor/Studios
                    Updated Legend Text
                    Corrected names of cast in reviews - GEVI
    09 Aug 2023     fixed reintroduced error... u'²' could not be searched for 
                    ¬ in filename title will be replaced with ? 
                    corrected updatemetadata routine no variable as FILMDICT['ReleaseDate']
    13 Aug 2023     Skip Release Date Matching if no File Year
                    Code correction in Duration matching
    '''
# ----------------------------------------------------------------------------------------------------------------------------------
import cloudscraper, copy, inspect, json, os, platform, plistlib, random, re, requests, subprocess, sys, time
#from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from io import BytesIO
from PIL import Image
from textwrap import wrap
from unidecode import unidecode

# Variables
UTILS_UPDATE = '13 Aug 2023'
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/ramesearch.asp?searchtype=comprehensive&searchstring={0}'
IAFD_FILTER = '&FirstYear={0}&LastYear={1}&Submit=Filter'
IAFD_THUMBSUP = u'\U0001F44D'      # thumbs up unicode character
IAFD_THUMBSDOWN = u'\U0001F44E'    # thumbs down unicode character
DEGREE = u'\U000000B0'             # Degree Symbol
DOUBLE_GREATER = u'\U00002AA2'     # Double Greater Than ⪢ Symbol
WRONG_TICK = u'\U0000274C'         # red cross mark - not on IAFD
WARNING_TICK = u'\U000026A0'       # Exclamation in Triangle
RIGHT_TICK = u'\U00002705'         # heavy white tick on green - on IAFD
ERR403_TICK = u'\U00002754'        # White question mark - for IAFD 403 error
BISEXUAL = u'\U000026A5'           # ⚥ - bisexual films
HOMOSEXUAL =  u'\U000026A5'        # ⚣ - gay films
HETEROSEXUAL = u'\U000026A4'       # ⚤ - straight films
NOBREAK_HYPHEN = u'\U00002011'     # Non Breaking Hyphen
NOBREAK_SPACE = u'\U000000A0'      # Non Breaking Space
EN_SPACE = u'\U00002002'           # Non Breaking En-Space
EM_SPACE = u'\U00002003'           # Non Breaking Em-Space
THIN_SPACE = u'\U00002009'         # Non Breaking Thin Space
STACKED = u'\U0001F4FD'            # Stacked Symbol
MONTHS = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
START_SCRAPE = 'Yes'

# Plex System Variables/Methods
PlexSupportPath = Core.app_support_path
PlexLoadFile = Core.storage.load
PlexSaveFile = Core.storage.save

# log section separators
LOG_BIGLINE = '-' * 140
LOG_SUBLINE = '      ' + '-' * 100
LOG_ASTLINE = '*' * 140

# ----------------------------------------------------------------------------------------------------------------------------------
def delay():
    delayList = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    delay = random.choice(delayList)
    return delay

# ----------------------------------------------------------------------------------------------------------------------------------
def findTidy(AGENTDICT, myItem):
    try:
        myItem = makeASCII(myItem.lower())
        pgmaTidyDict = AGENTDICT['pgmaTIDYDICT']
        myItem = pgmaTidyDict.get(myItem, '')
        myItem = None if myItem == 'x' else myItem
    except Exception as e:
        log('UTILS :: Error: Failed to Access Tidy Dictionary: {0}'.format(e))

    return myItem

# ----------------------------------------------------------------------------------------------------------------------------------
def getCast(agntCastList, AGENTDICT, FILMDICT):
    ''' Process and match cast list against IAFD '''

    if not agntCastList and 'Cast' not in FILMDICT: # nowt to do
        raise Exception('< No Cast Found! >')

    # clean up the Cast List make a copy then clear
    agntCastList = [x.split('(')[0].strip() for x in agntCastList]
    agntCastSet = {x.replace("St.", 'St ').replace("'s", '').replace('.', '') for x in agntCastList}      # remove all 's and initial dots from and duplicates
    agntCastList = sorted([String.StripDiacritics(x) for x in agntCastSet if x])

    # keep elements that are not a substring of another element
    tempList = agntCastList[:]
    for elem in tempList:
        agntCastList = [x for x in agntCastList if (x == elem) or (x not in elem)]    

    log('UTILS :: {0:<29} {1}'.format('Agent Cast List', '{0:>2} - {1}'.format(len(agntCastList), agntCastList)))

    # Determine which elements in the Agent Cast List are unmatched to entries in the IAFD List
    castDict = copy.deepcopy(FILMDICT['Cast'])
    log('UTILS :: {0:<29} {1}'.format('IAFD Cast List', '{0:>2} - {1}'.format(len(castDict), sorted(castDict.keys()))))
    unmatchedCastList = []
    for cast in agntCastList:
        matchedCast = False
        for castKey, castValue in FILMDICT['Cast'].items():
            if cast in castKey or cast in castValue['Bio']['AKA'] or cast in castValue['RealName'] or cast in castValue['Alias']:
                matchedCast = True
                break

        if matchedCast is False:
            unmatchedCastList.append(cast)

    log('UTILS :: {0:<29} {1}'.format('Unmatched Cast List', '{0:>2} - {1}'.format(len(unmatchedCastList), unmatchedCastList)))
    log(LOG_SUBLINE)

    # search IAFD for specific cast and return matched cast
    matchedCastDict = copy.deepcopy(matchCast(unmatchedCastList, AGENTDICT, FILMDICT))
    # update the Cast dictionary
    if matchedCastDict:
        castDict.update(matchedCastDict)

    return castDict

# -------------------------------------------------------------------------------------------------------------------------------
def getDirectors(agntDirectorList, AGENTDICT, FILMDICT):
    ''' Process and match director list against IAFD'''

    if not agntDirectorList and 'Directors' not in FILMDICT: # nowt to do
        raise Exception('< No Directors Found! >')

    # clean up the Director List
    agntDirectorList = [x.split('(')[0].strip() for x in agntDirectorList]                                          # remove AKA part of name eg James Dean (J. Deano) = James Dean
    agntDirectorSet = {x.replace("St.", 'St ').replace("'s", '').replace('.', '') for x in agntDirectorList}      # remove all 's and initial dots from and duplicates
    agntDirectorList = sorted([String.StripDiacritics(x) for x in agntDirectorSet if x])
    log('UTILS :: {0:<29} {1}'.format('Agent Director List', '{0:>2} - {1}'.format(len(agntDirectorList), agntDirectorList)))

    # keep elements that are not a substring of another element
    tempList = agntDirectorList[:]
    for elem in tempList:
        agntDirectorList = [x for x in agntDirectorList if (x == elem) or (x not in elem)]    

    log('UTILS :: {0:<29} {1}'.format('Agent Director List', '{0:>2} - {1}'.format(len(agntDirectorList), agntDirectorList)))

    # Determine which elements in the Agent Director List are unmatched to entries in the IAFD List
    directorDict = copy.deepcopy(FILMDICT['Directors'])
    log('UTILS :: {0:<29} {1}'.format('IAFD Director List', '{0:>2} - {1}'.format(len(directorDict), sorted(directorDict.keys()))))
    unmatchedDirectorList = []
    for director in agntDirectorList:
        matchedDirector = False
        for directorKey, directorValue in FILMDICT['Directors'].items():
            if director in directorKey or director in directorValue['Bio']['AKA'] or director in directorValue['RealName'] or director in directorValue['Alias']:
                matchedDirector = True
                break

        if matchedDirector is False:
            unmatchedDirectorList.append(director)

    # remove entries from the website cast list which have been found on IAFD leaving unmatched director
    log('UTILS :: {0:<29} {1}'.format('Unmatched Director List', '{0:>2} - {1}'.format(len(unmatchedDirectorList), unmatchedDirectorList)))
    log(LOG_SUBLINE)

    # search IAFD for specific director and return matched directors
    matchedDirectorDict = copy.deepcopy(matchDirectors(unmatchedDirectorList, AGENTDICT, FILMDICT))

    # update the Director dictionary
    if matchedDirectorDict:
        directorDict.update(matchedDirectorDict)

    return directorDict

# -------------------------------------------------------------------------------------------------------------------------------
def getFilmImages(imageType, imageLocation, whRatio, sceneAgent, thumborAddress, rotation):
    ''' Only for Scene Agents: get Film images - posters/background art and crop if necessary '''
    imageContent = ''
    if AGENT == 'GEVIScenes' and imageType == 'Poster':
        try:
            originalLocation = imageLocation
            imageContent = HTTP.Request(imageLocation).content

            envVar = os.environ
            TempFolder = envVar['TEMP']
            imageLocation = os.path.join(TempFolder, imageLocation.split("/")[-1])
            PlexSaveFile(imageLocation, imageContent)
            psScript = os.path.join(PlexSupportPath, 'Plug-ins', '_PGMA', 'Scripts', 'Rotate.ps1')
            cmd = r'powershell.exe -executionPolicy bypass -file "{0}" "{1}" {2}'.format(psScript, imageLocation, rotation)
            log('UTILS ::')
            log('UTILS :: {0:<29} {1}'.format('Script - Rotate Image 270{0}'.format(DEGREE), imageLocation))
            log('UTILS :: {0:<29} {1}'.format('Command Line', cmd))
            myProcess = subprocess.call(cmd)
            del myProcess
            time.sleep(2)
            imageContent = PlexLoadFile(imageLocation)

        except Exception as e:
            log('UTILS :: Error: Script Failed to Rotate Image: {0}'.format(e))

    else:
        Thumbor = thumborAddress + "/0x0:{0}x{1}/{2}"
        imageContent = HTTP.Request(imageLocation).content
        myImage = Image.open(BytesIO(imageContent))
        width, height = myImage.size
        dispWidth = '{:,d}'.format(width)       # thousands separator
        dispHeight = '{:,d}'.format(height)     # thousands separator

        log('UTILS :: {0:<29} {1}'.format('{0} Found'.format(imageType),'Actual Size: (w {0} x h {1}); URL: {2}'.format(dispWidth, dispHeight, imageLocation)))

        # Cropping only done on Scene Agents
        if sceneAgent is True:
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
            log('UTILS :: {0:<29} {1}'.format('Crop {0}'.format("Required" if cropRequired else "Not Required"), 'Desired Size: (w {0} x h {1}); Dx: w[{2}%] x h[{3}%]'.format(desiredWidth, desiredHeight, DxWidth, DxHeight)))
            if cropRequired:
                try:
                    width = cropWidth
                    height = cropHeight
                    imageLocation = Thumbor.format(width, height, imageLocation)
                    log('UTILS :: {0:<29} {1}'.format('Thumbor - Crop Image', imageLocation))
                    log('UTILS :: {0:<29} {1}'.format('  Desired Dimensions', '{0} x {1}'.format(desiredWidth, desiredHeight)))
                    imageContent = HTTP.Request(imageLocation).content

                except Exception as e:
                    log('UTILS :: Error: Thumbor Failed to Crop Image to: {0} x {1}: {2} - {3}'.format(desiredWidth, desiredHeight, imageLocation, e))
                    if os.name == 'nt':
                        try:
                            envVar = os.environ
                            TempFolder = envVar['TEMP']
                            imageLocation = os.path.join(TempFolder, imageLocation.split("/")[-1])
                            PlexSaveFile(imageLocation, imageContent)
                            vbScript = os.path.join(PlexSupportPath, 'Plug-ins', '_PGMA', 'Scripts', 'Cropper.vbs')
                            cmd = r'CScript.exe "{0}" "{1}" "{2}" "{3}"'.format(vbScript, imageLocation, cropWidth, cropHeight)
                            log('UTILS ::')
                            log('UTILS :: {0:<29} {1}'.format('Script - Crop Image', imageLocation))
                            log('UTILS :: {0:<29} {1}'.format('Command Line', cmd))
                            log('UTILS :: {0:<29} {1}'.format('Desired Dimensions', '{0} x {1}'.format(desiredWidth, desiredHeight)))
                            myProcess = subprocess.call(cmd)
                            del myProcess
                            time.sleep(2)
                            imageContent = PlexLoadFile(imageLocation)
                        except Exception as e:
                            log('UTILS :: Error: Script Failed to Crop Image to: {0} x {1}: {2} - {3}'.format(desiredWidth, desiredHeight, imageLocation, e))

    return imageLocation, imageContent

# -------------------------------------------------------------------------------------------------------------------------------
def getFilmOnIAFD(AGENTDICT, FILMDICT):
    ''' check IAFD web site for better quality thumbnails per movie'''
    romanPattern = '\(M{0,3}(CM|CD|D?C{0,3})?(XC|XL|L?X{0,3})?(IX|IV|V?I{0,3})?\)$'
    try:
        myYear = int(FILMDICT['Year'])
        html = getURLElement(IAFD_SEARCH_URL.format(FILMDICT['IAFDSearchTitle']), FilterYear=myYear, UseAdditionalResults=True)

        # get films listed within 1 year of what is on agent - as IAFD may have a different year recorded
        filmsList = []
        if myYear:
            startYear = myYear if AGENT == 'IAFD' else myYear - 3
            endYear = myYear if AGENT == 'IAFD' else myYear + 1
            xPathString = '//table[@id="titleresult"]/tbody/tr/td[2][.>="{0}" and .<="{1}"]/ancestor::tr'.format(startYear, endYear)
            log('UTILS :: {0:<29} {1}'.format('Films found on IAFD', 'xPath String: {0}'.format(xPathString)))
            filmsList = html.xpath(xPathString)
            filmsFound = len(filmsList)
            log('UTILS :: {0:<29} {1}'.format('Films found on IAFD', '{0} between the years [{1}] and [{2}]'.format(filmsFound, startYear, endYear)))

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
                siteTitle = re.sub(romanPattern, '', siteTitle).strip()
                matchTitle(siteTitle, FILMDICT, myAgent='IAFD')
                matchedTitle = True

            except Exception as e:
                matchedTitle = False
                log('UTILS :: Warning: Getting IAFD Site Title, Try AKA Title: {0}'.format(e))

            if matchedTitle is False:
                try:
                    filmAKA = film.xpath('./td[4]/text()')[0].strip()
                    filmAKA = re.sub(romanPattern, '', filmAKA).strip()
                    matchTitle(filmAKA, FILMDICT, myAgent='IAFD')
                    FILMDICT['FilmAKA'] = filmAKA
                except Exception as e:
                    log('UTILS :: Warning: Getting IAFD Site AKA Title: {0}'.format(e))
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
                log('UTILS :: Error: Getting IAFD Site Title Url: {0}'.format(e))
                log(LOG_SUBLINE)
                continue

            # Access Site URL for Studio, Release Date and Duration information
            log(LOG_BIGLINE)
            try:
                log('UTILS :: {0:<29} {1}'.format('Reading IAFD Film URL page', FILMDICT['IAFDFilmURL']))
                fhtml = getURLElement(FILMDICT['IAFDFilmURL'])
                vFilmHTML = fhtml

            except Exception as e:
                log('UTILS :: Error: reading IAFD Film URL page: {0}'.format(e))
                log(LOG_SUBLINE)
                continue

            # Film Studio and Distributor
            log(LOG_BIGLINE)
            foundStudio = False
            try:
                fhtmlStudios = fhtml.xpath('//p[@class="bioheading" and (text()="Studio" or text()="Distributor")]//following-sibling::p[1]/a/text()')
                iafdStudios = list({x.strip() for x in fhtmlStudios if x.strip()})
                studiosFound = len(fhtmlStudios)
                log('UTILS :: {0:<29} {1}'.format('Site URL Distributor/Studio', '{0:>2} - {1}'.format(studiosFound, iafdStudios)))
                for idx, item in enumerate(iafdStudios, start=1):
                    log('UTILS :: {0:<29} {1}'.format('Processing Studio', '{0} - {1} of {2}'.format(item, idx, studiosFound)))
                    try:
                        matchStudio(item, FILMDICT, myAgent='IAFD')
                        foundStudio = True
                        break

                    except Exception as e:
                        log('UTILS :: Error:: {0}'.format(e))
                        log(LOG_SUBLINE)
                        continue

            except Exception as e:
                log('UTILS :: Error: Getting IAFD Site Studio/Distributor: {0}'.format(e))
                log(LOG_SUBLINE)

            # Could not match filename studio to what is recorded on IAFD
            # Match IAFD Studios against all recorded studios
            if foundStudio is False and FILMDICT['RecordedStudios']:
                recordedStudiosFound = len(FILMDICT['RecordedStudios'])
                recordedCompareStudios = [Normalise(makeASCII(x)) for x in FILMDICT['RecordedStudios']]        # normalise recorded studios
                iafdCompareStudios = [Normalise(makeASCII(x)) for x in fhtmlStudios]                           # normalise iafd studios
                for idx2, recordedStudio in enumerate(FILMDICT['RecordedStudios']):
                    foundStudio = True if [x for x in iafdCompareStudios if recordedCompareStudios[idx2] in x or x in recordedCompareStudios[idx2]] else False
                    log('UTILS :: {0:<29} {1}'.format('{0} Studio'.format(AGENT), '{0} {1} {2}'.format(recordedStudio, '-Matched-' if foundStudio is True else '-Not Matched-', iafdStudios)))
                    if foundStudio is True:
                        break

            if foundStudio is False:
                log('UTILS :: Error: matching IAFD Site Studios/Distributors against {0} Recorded Studios'.format(AGENT))
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
                    for idx3, webLink in enumerate(webLinks, start=1):
                        webURL = webLink.xpath('./@href')[0]
                        webURL = '{0}{1}'.format(IAFD_BASE, webURL)
                        webName = webLink.xpath('./text()')[0]
                        log('UTILS :: {0:<29} {1}'.format('External Sites Found' if idx3 ==1 else '', '{0:>2} - {1:<15} - {2}'.format(idx3, webName, webURL)))
                        if webName not in externalIAFDSites:
                            continue
                        if externalIAFDSites[webName] == FILMDICT['Agent']:
                            continue

                        externalDict[webName] = webURL

                except Exception as e:
                    log('UTILS :: Warning: Getting External Links: {0}'.format(e))

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
                        FILMDICT[key] = getSiteInfo(key, AGENTDICT, FILMDICT, kwFilmURL=value, kwFilmHTML=xSiteHTML)
                        # change Compilation to 'Yes' if one result is not the default 'No'
                        if 'Compilation' in FILMDICT[key] and FILMDICT[key]['Compilation'] == 'Yes':
                            FILMDICT['Compilation'] = FILMDICT[key]['Compilation'] 

                    except Exception as e:
                        log('UTILS :: Error: reading External {0} URL Link: {1}'.format(key, e))
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
                    matchReleaseDate(releaseDate, FILMDICT, UseTwoYearMatch = False if AGENT == 'IAFD' else True, myAgent='IAFD')
                    vReleaseDate = releaseDate

                except Exception as e:
                    log('UTILS :: Error: Matching Release Date: {0}'.format(e))
                    continue

            except Exception as e:
                log('UTILS :: Warning: Getting Site URL Release Dates: {0}'.format(e))
                if FILMDICT['Year']:                     # year in filename title so use release date as filter
                    log(LOG_SUBLINE)
                    continue

            # Film Duration
            log(LOG_BIGLINE)
            vDuration = FILMDICT['Duration']
            try:
                fhtmlduration = fhtml.xpath('//p[@class="bioheading" and text()="Minutes"]//following-sibling::p[1]/text()')[0].strip()
                duration = datetime.fromtimestamp(int(fhtmlduration) * 60)
                matchDuration(duration, AGENTDICT, FILMDICT, matchAgainstIAFD=True, myAgent='IAFD')
                vDuration = duration
                FILMDICT['IAFDDuration'] = duration

            except ValueError as e:
                log('UTILS :: Warning: IAFD Duration Not Numeric: Set Duration to File Length and Continue: {0}'.format(e))
                FILMDICT['IAFDDuration'] = FILMDICT['Duration']

            except Exception as e:
                if AGENTDICT['prefMATCHIAFDDURATION'] is True:           # if preference selected go to next
                    log('UTILS :: Error: Getting IAFD Duration: {0}'.format(e))
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
                log('UTILS :: Error: Finding All Male Cast: {0}'.format(e))

            # check if film has an all Girl cast
            log(LOG_BIGLINE)
            try:
                FILMDICT['AllGirl'] = fhtml.xpath('//p[@class="bioheading" and text()="All-Girl"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: {0:<29} {1}'.format('All Girl Cast?', FILMDICT['AllGirl']))

            except Exception as e:
                log('UTILS :: Error: Finding All Girl Cast: {0}'.format(e))

            # check if film is a compilation
            log(LOG_BIGLINE)
            try:
                FILMDICT['Compilation'] = fhtml.xpath('//p[@class="bioheading" and text()="Compilation"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: {0:<29} {1}'.format('Compilation?', FILMDICT['Compilation']))

            except Exception as e:
                log('UTILS :: Error: Finding Compilation Status: {0}'.format(e))

            # use general routine to get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information
            log(LOG_BIGLINE)
            log('SEARCH:: Access Site URL Link:')
            FILMDICT['IAFD'] = getSiteInfo('IAFD', AGENTDICT, FILMDICT, kwFilmURL=vFilmURL, kwFilmHTML=vFilmHTML, kwReleaseDate=vReleaseDate, kwDuration=vDuration)

            break

    except Exception as e:
        log('UTILS :: Error:: IAFD Film Search Failure, {0}'.format(e))
        FILMDICT['IAFD403Err'].add('Film')

    return FILMDICT

# ----------------------------------------------------------------------------------------------------------------------------------
def getHTTPRequest(url, **kwargs):
    ''' Use CloudScraper utility to read url and return valid HTML'''
    headers = kwargs.pop('headers', {})
    cookies = kwargs.pop('cookies', {})
    timeout = kwargs.pop('timeout', 30)
    sleep = delay()
    proxies = {}

    HTTPRequest = None
    msg = ''
    try:
        log('UTILS :: {0:<29} {1}'.format('Plex Request', url))
        HTTPRequest = HTML.ElementFromURL(url, timeout=timeout, sleep=sleep)

    except Exception as e:
        log('UTILS :: {0:<29} {1}'.format('Plex Request Failed', e))
        try:
            headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
            headers['Accept-Language'] = 'gzip, deflate, br'
            headers['Accept-Encoding'] = 'en-GB,en;q=0.9,en-US;q=0.8'
            headers['User-Agent'] = getUserAgent()

            log('UTILS :: {0:<29} {1}'.format('CloudScraper Request', url))
            log('UTILS :: {0:<29} {1}'.format('CloudScraper User Agent', headers['User-Agent']))

            scraper = cloudscraper.CloudScraper()
            scraper.headers.update(headers)
            scraper.cookies.update(cookies)
            time.sleep(sleep)
            HTTPRequest = scraper.request('GET', url, timeout=timeout, proxies=proxies)
            if not HTTPRequest.ok:
                msg = 'CloudScraper Status Code: {0}'.format(HTTPRequest.status_code)

        except Exception as e:
            msg = 'CloudScraper Request Failed: {0}'.format(e)
    
    finally:
        if msg:
            raise Exception(msg)

    # determine whether the url is an image or not
    # Parse Output and repair any invalid html code - use lxml parser - https://stackoverflow.com/questions/73867545/validate-html-with-beautifulsoup
    # log('UTILS :: {0:<29} {1}'.format('Content Type', HTTPRequest.headers['Content-Type']))
    # if 'image' not in HTTPRequest.headers['Content-Type'].lower():
    #pattern = r'.jpeg|.jpg|.png|.webp'
    #matched = re.search(pattern, url, re.IGNORECASE)  # match against whole string
    #if not matched:
    #    try:
    #        soup = BeautifulSoup(HTTPRequest.text, "lxml")
    #        HTTPRequest = HTML.ElementFromString(str(soup))

    #    except Exception as e:
    #        msg = 'HTML Parsing Failed: {0}'.format(e)
    #        raise Exception(msg)

    return HTTPRequest

# -------------------------------------------------------------------------------------------------------------------------------
def getIAFDArtist(AGENTDICT, artistURL, artistHTML=''):
    ''' get artist's biography''' 
    artistType = 'Director' if 'gender=d' in artistURL else 'Cast'
    artist = {}
    artistRealName = ''
    artistPhoto = ''
    artistNationality = ''
    artistBirthNationality = ''
    artistFilms = []
    artistAwards = []
    artistBio = {'IAFD URL': artistURL}

    # initialise artist
    artist = {'Awards': artistAwards, 'Bio': copy.deepcopy(artistBio), 'Films': artistFilms, 'Photo': artistPhoto, 'Nationality': artistNationality, 'RealName': artistRealName}

    try:
        ahtml = artistHTML if artistHTML else getURLElement(artistURL)
        xpath = '//table[@id="{0}"]/tbody/tr[position()<=15]'.format('directoral' if artistType == 'Director' else 'personal')
        artistRealName = ahtml.xpath('//h1/text()[normalize-space()]')[0].strip()
        artistPhoto = ahtml.xpath('//div[@id="headshot"]//img/@src')[0]
        if not re.search(r'(?:jpg|jpeg|png|gif|bmp|webp)$', artistPhoto, re.IGNORECASE) or 'nophoto340.jpg' in artistPhoto:
            artistPhoto = ''

        if not artistPhoto and artistType == 'Director':                    # if no photo check if director has a performer page
            try:
                bhtml = getURLElement(artistURL.replace('gender=d', 'gender=m'))
                artistPhoto = bhtml.xpath('//div[@id="headshot"]/img/@src')[0].strip()
                if not re.search(r'(?:jpg|jpeg|png|gif|bmp|webp)$', artistPhoto, re.IGNORECASE) or 'nophoto340.jpg' in artistPhoto:
                    artistPhoto = ''

            except Exception as e:
                log('UTILS :: Warning: Getting Director Photo from "As Performer" Details Page: {0}'.format(e))
        
        try:
            processing = 'Biography'
            ahtmlBio = ahtml.xpath('//*[@class="bioheading"]')
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
                        tidyItem = findTidy(AGENTDICT, item)
                        if tidyItem is None:        # Don't process
                            continue
                        if tidyItem not in AGENTDICT['pgmaCOUNTRYSET']:
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
                        tidyItem = findTidy(AGENTDICT, item)
                        if tidyItem is None:        # Don't process
                            continue
                        if tidyItem not in AGENTDICT['pgmaCOUNTRYSET']:
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

                elif re.search(r'\bkg\b', biodata, re.IGNORECASE):                              # weight
                    biodataList = [int(x) for x in re.findall(r'\d+', biodata)]
                    usImperialWeight = '{0} lbs'.format(biodataList[0])
                    ukImperialStones, ukImperialLbs = divmod(biodataList[0], 14)
                    ukImperialWeight = "{0} st {1}".format(ukImperialStones, '{0} lbs'.format(ukImperialLbs) if ukImperialLbs else '').strip()
                    metricWeight = '{0} Kgs'.format(biodataList[1])
                    biodata = '{0} ({1} / {2})'.format(metricWeight, ukImperialWeight, usImperialWeight)
                    artistBio[bioheading] = biodata

                elif re.search(r'\bfeet\b', biodata, re.IGNORECASE):                            # height
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

        except Exception as e:
            log("UTILS :: Error: processing Artist's Biography {0}: {1}".format(processing, e))

        try:
            processing = 'Filmography'
            ahtmlFilms = ahtml.xpath(xpath)
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

            if artistFilms:
                artistFilms.sort(key = lambda x: x.lower())

        except Exception as e:
            log("UTILS :: Error: processing Artist's Filmography {0}: {1}".format(processing, e))

        processing = 'Collation'
        artist = {'Awards': artistAwards, 'Bio': artistBio, 'Films': artistFilms, 'Photo': artistPhoto, 'Nationality': artistNationality, 'RealName': artistRealName}

    except Exception as e:
        log('UTILS :: Error: Getting Artist Details Page: {0}'.format(e))

    return artist
# -------------------------------------------------------------------------------------------------------------------------------
def getImageContent(imageLocation, picType, entry, AGENTDICT):
    ''' Used for Getting flag images, actors and directors pictures - Deceased Actors/Directors shown in GrayScale'''
    imageContent = None
    fileOnDisk = False if 'http' in imageLocation else True
    log('UTILS :: {0:<29} {1}'.format('Location', 'On Disk' if fileOnDisk is True else 'On Web'))
    try:
        # Countries & System - IAFD, Stacked, Agent are stored on disk, AND posters under _PGMA + Agent.jpg
        if fileOnDisk is True:
            imageContent = PlexLoadFile(imageLocation)

        else:
            imageLocation = imageLocation.replace(' ', '%20').strip()
            ImageContent = getHTTPRequest(imageLocation).content
            myImage = Image.open(BytesIO(ImageContent))
            width, height = myImage.size
            width = int(width)
            height = int(width * 1.5)

    except Exception as e:
        if AGENTDICT['prefCOLCAST'] in entry:
            fileOnDisk = True
            imageContent = PlexLoadFile(AGENTDICT['pgmaNOCASTPOSTER'])
        elif AGENTDICT['prefCOLDIRECTOR'] in entry:
            fileOnDisk = True
            imageContent = PlexLoadFile(AGENTDICT['pgmaNODIRECTORPOSTER'])
        else:
            msg = '< No Image Content Loaded: {0}! >'.format(e)
            raise Exception(msg)

    if fileOnDisk is False:
        # Cast from IAFD
        if AGENTDICT['prefCOLCAST'] in entry:
            if '[d]' in entry:
                imageLocation = r'{0}/{1}x{2}/filters:stretch():grayscale()/{3}'.format(AGENTDICT['pgmaTHUMBOR'], width, height, imageLocation)
            else:
                imageLocation = r'{0}/{1}x{2}/filters:stretch()/{3}'.format(AGENTDICT['pgmaTHUMBOR'], width, height, imageLocation)

            log('UTILS :: {0:<29} {1}'.format('{0}Cast {1} Image URL'.format('Deceased ' if '[d]' in entry else '', picType), imageLocation))

        # Directors from IAFD - GrayScale + Watermark if deceased else just Watermark
        elif AGENTDICT['prefCOLDIRECTOR'] in entry:
            if '[d]' in entry:
                imageLocation = r'{0}/{1}x{2}/filters:stretch():grayscale():watermark({3},1,1,0)/{4}'.format(AGENTDICT['pgmaTHUMBOR'], width, height, AGENTDICT['pgmaWATERMARK'], imageLocation)
            else:
                imageLocation = r'{0}/{1}x{2}/filters:stretch():watermark({3},1,1,0)/{4}'.format(AGENTDICT['pgmaTHUMBOR'], 128, 192, AGENTDICT['pgmaWATERMARK'], imageLocation)

            log('UTILS :: {0:<29} {1}'.format('{0}Director {1} Image URL'.format('Deceased ' if '[d]' in entry else '', picType), imageLocation))

        # all other internet images need to be ratio wxh = 1x1.5
        else:
            imageLocation = r'{0}/fit-in/{1}x{2}/{3}'.format(AGENTDICT['pgmaTHUMBOR'], width, height, imageLocation)
            log('UTILS :: {0:<29} {1}'.format('{0} Genre Image URL'.format(picType), imageLocation))

        # get Thumborised Image Contemt
        try:
            imageContent = getHTTPRequest(imageLocation)

        except Exception as e:
            log('UTILS :: Error:: Failed to get Image Content: {0} - {1}'.format(e, imageLocation))
            if AGENTDICT['prefCOLCAST'] in entry:
                imageContent = PlexLoadFile(AGENTDICT['pgmaNOCASTPOSTER'])
            elif AGENTDICT['prefCOLDIRECTOR'] in entry:
                imageContent = PlexLoadFile(AGENTDICT['pgmaNODIRECTORPOSTER'])
            else:
                msg = '< No Thumbor Image Content Loaded: {0}! >'.format(e)
                raise Exception(msg)

    return imageContent

# -------------------------------------------------------------------------------------------------------------------------------
def getRecordedCast(html, AGENTDICT, FILMDICT):
    ''' retrieve film cast from IAFD film page'''
    filmCast = {}
    try:
        castList = html.xpath('//div[@class[contains(.,"castbox")]]/p')
        log('UTILS :: {0:<29} {1:>2}'.format('Cast on IAFD', len(castList)))
        log(LOG_SUBLINE)
        for cast in castList:
            castName = cast.xpath('./a/text()[normalize-space()]')[0].strip()
            castName = 'Unknown Actor' if 'Unknown' in castName else castName

            # cast alias in current film may be missing
            castAlias = ''
            try:
                castAlias = cast.xpath('./i/text()')[0].split(':')[1].replace(')', '').strip()
                castAlias = castAlias.replace(' or ', ',').split(',')
                castAlias = ', '.join(castAlias)

            except:
                pass

            # cast roles are sometimes not filled in
            castRole = ''
            try:
                castRole = cast.xpath('./text()[normalize-space()]')
                castRole = ' '.join(castRole).replace('DVDOnly','').strip()
                if not castRole:
                    castRole = 'AKA: {0}'.format(castAlias) if castAlias else RIGHT_TICK

            except:
                pass

            # get cast biography and filmography etc
            castURL = IAFD_BASE + cast.xpath('./a/@href')[0].strip()
            try:
                castDetails = getIAFDArtist(AGENTDICT, castURL)
            except:
                castDetails = {}
                castRole = ERR403_TICK          # indicate error accessing iafd
                FILMDICT['IAFD403Err'].add('Cast')

            castAwards = castDetails['Awards']
            castBio = castDetails['Bio']
            castFilms = castDetails['Films']
            castNationality = castDetails['Nationality']
            castPhoto = castDetails['Photo']
            castRealName = castDetails['RealName']

            castCompareName = re.sub(r'[\W\d_]', '', castName).strip().lower()
            castCompareAlias = re.sub(r'[\W\d_]', '', castAlias).strip().lower()

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
        log('UTILS :: Error:: Processing IAFD Film Cast: {0}'.format(e))

    return filmCast

# -------------------------------------------------------------------------------------------------------------------------------
def getRecordedDirectors(html, AGENTDICT, FILMDICT):
    ''' retrieve directors from IAFD film page'''
    filmDirectors = {}
    try:
        directorList = html.xpath('//p[@class="bioheading" and text()="Directors"]//following-sibling::p[1]/a')
        log('UTILS :: {0:<29} {1:>2}'.format('Directors on IAFD', len(directorList)))
        log(LOG_SUBLINE)
        for director in directorList:
            directorName = director.xpath('./text()')[0]
            directorURL = director.xpath('./@href')[0]

            # get director biography and filmography etc
            try:
                directorDetails = getIAFDArtist(AGENTDICT, directorURL)
            except:
                directorDetails = {}
                FILMDICT['IAFD403Err'].add('Director')

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
        log('UTILS :: Error: Processing IAFD Film Director(s): {0}'.format(e))
        FILMDICT['IAFD403Err'].add('Director')

    return filmDirectors

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfo(myAgent, AGENTDICT, FILMDICT, **kwargs):
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
        log('UTILS :: {0}'.format(header.center(131, '*')))

    log('UTILS ::')

    if myAgent == 'AdultFilmDatabase':
        siteInfoDict = getSiteInfoAdultFilmDatabase(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'AEBN':
        siteInfoDict = getSiteInfoAEBN(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'AVEntertainments':
        siteInfoDict = getSiteInfoAVEntertainments(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'BestExclusivePorn':
        siteInfoDict = getSiteInfoBestExclusivePorn(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'CDUniverse':
        siteInfoDict = getSiteInfoCDUniverse(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'GayEmpire':
        siteInfoDict = getSiteInfoGayEmpire(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'Fagalicious':
        siteInfoDict = getSiteInfoFagalicious(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'GayHotMovies':
        siteInfoDict = getSiteInfoGayHotMovies(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'GayMovie':
        siteInfoDict = getSiteInfoGayMovie(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'GayFetishandBDSM':
        siteInfoDict = getSiteInfoGayFetishandBDSM(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'GayMovies':
        siteInfoDict = getSiteInfoGayMovie(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'GayRado':
        siteInfoDict = getSiteInfoGayRado(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'GayWorld':
        siteInfoDict = getSiteInfoGayWorld(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'GEVI':
        siteInfoDict = getSiteInfoGEVI(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'GEVIScenes':
        siteInfoDict = getSiteInfoGEVIScenes(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'HFGPM':
        siteInfoDict = getSiteInfoHFGPM(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'HomoActive':
        siteInfoDict = getSiteInfoHomoActive(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'IAFD':
        siteInfoDict = getSiteInfoIAFD(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'QueerClick':
        siteInfoDict = getSiteInfoQueerClick(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'SimplyAdult':
        siteInfoDict = getSiteInfoSimplyAdult(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'WayBig':
        siteInfoDict = getSiteInfoWayBig(AGENTDICT, FILMDICT, **kwargs)
    elif myAgent == 'WolffVideo':
        siteInfoDict = getSiteInfoWolffVideo(AGENTDICT, FILMDICT, **kwargs)

    log('UTILS ::')
    listFooters = [' >> {0}: Site Information Retrieved << '.format(myAgent),
                   ' >> ({0}) - {1}{2} << '.format(FILMDICT['Studio'], FILMDICT['Title'], ' ({0})'.format(FILMDICT['Year']) if FILMDICT['Year'] else ''),
                   ' >> {0} << '.format(FILMDICT['FilmURL'] if kwFilmURL is None else kwFilmURL)]
    for footer in listFooters:
        log('UTILS :: {0}'.format(footer.center(131, '*')))

    log('UTILS ::')
    return siteInfoDict

# -------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoAdultFilmDatabase(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', synopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

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
            log('UTILS :: Error: Getting Collections: {0}'.format(e))

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//a[contains(@href,"&cf=")]/span/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in AGENTDICT['pgmaCOUNTRYSET']:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error: Getting Genres/Countries: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
                log('UTILS :: Error: Getting Site Film Duration: {0}'.format(e))
        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        kwBaseURL = kwargs.get('kwBaseURL')
        if kwReleaseDate is not None:
            log(LOG_SUBLINE)
            try:
                htmlimages = html.xpath('//img[@title]/@src')
                htmlimages = [('' if kwBaseURL in x else kwBaseURL) + x for x in htmlimages]
                log('UTILS :: {0:<29} {1}'.format('Images', htmlimages))
                poster = [htmlimages[0]]
                art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
                log('UTILS :: {0:<29} {1}'.format('Poster', poster))
                log('UTILS :: {0:<29} {1}'.format('Art', art))

            except Exception as e:
                poster = []
                art = []
                log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoAEBN(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', htmlsynopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

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
            log('UTILS :: Error: Getting Collections: {0}'.format(e))

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            try:
                htmlgenres = html.xpath('//span[@class="dts-image-display-name"]/text()')
                htmlgenres.sort(key = lambda x: x.lower())
                log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))

            except Exception as e:
                htmlgenres = []
                log('UTILS :: Error: Reading Site Info Genres: {0}'.format(e))

            try:
                htmlsexacts = html.xpath('//a[contains(@href,"sexActFilters")]/text()') # use sex acts as genres
                htmlsexacts.sort(key = lambda x: x.lower())
                log('UTILS :: {0:<29} {1}'.format('Sex Acts', '{0:>2} - {1}'.format(len(htmlsexacts), htmlsexacts)))

            except Exception as e:
                htmlsexacts = []
                log('UTILS :: Error: Reading Site Info Sex Acts: {0}'.format(e))

            htmlgenres.extend(htmlsexacts)
            htmlgenres = list(set(htmlgenres))
            htmlgenres.sort(key = lambda x: x.lower())
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            log('UTILS :: {0:<29} {1}'.format('Combined Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in AGENTDICT['pgmaCOUNTRYSET']:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error: Getting Genres/Countries: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
                log('UTILS :: Error: Getting Site Film Duration: {0}'.format(e))
        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//*[contains(@class,"dts-movie-boxcover")]//img/@src')
            htmlimages = [x.replace('=293', '=1000') for x in htmlimages]
            htmlimages = ['http:{0}'.format(x) if 'http:' not in x else x for x in htmlimages]
            log('UTILS :: {0:<29} {1}'.format('Images', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
                        log('UTILS :: Error: Getting Review Source (Cast): {0}'.format(e))

                    # Review Author - composed of Settings
                    reviewAuthor = 'AEBN'
                    try:
                        reviewAuthor = htmlscene.xpath('./ul/li[descendant::span[text()="Settings:"]]/a/text()')
                        reviewAuthor = [x for x in reviewAuthor if x]
                        reviewAuthor = ', '.join(reviewAuthor)

                    except Exception as e:
                        log('UTILS :: Error: Getting Review Author (Settings): {0}'.format(e))

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
                            tidyItem = findTidy(AGENTDICT, item)
                            log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))
                            if tidyItem is None:
                                continue
                            mySet.add(tidyItem if tidyItem else item)

                        reviewList = list(mySet)
                        reviewList.sort(key = lambda x: x.lower())
                        reviewText = ', '.join(reviewList)

                    except Exception as e:
                        log('UTILS :: Error: Getting Review Text (Sex Acts): {0}'.format(e))

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
                    log('UTILS :: Error: Getting Scene No. {0}: {1}'.format(sceneNo, e))

        except Exception as e:
            log('UTILS :: Error: Getting Scenes: {0}'.format(e))

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
def getSiteInfoAVEntertainments(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', htmlsynopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

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
            log('UTILS :: Error: Getting Collections: {0}'.format(e))

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//div[@class="single-info"]/span[@class="title" and text()="Category"]/following-sibling::span/a/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in AGENTDICT['pgmaCOUNTRYSET']:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error: Getting Genres/Countries: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
                log('UTILS :: Error: Getting Site Film Duration: Reset to File Name Duration {0}'.format(e))
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
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoBestExclusivePorn(AGENTDICT, FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'BestExclusivePorn'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('.//div[@class="entry"]/p/text()')
            ignoreStrings = ['Country:', 'Duration:', 'Genre:', 'Production year:', 'Studio:']
            pattern = u'({0})'.format('|'.join(ignoreStrings))
            synopsis = ' '
            for item in htmlsynopsis:
                item = item.replace('Description: ', '').strip()
                log('UTILS :: {0:<29} {1}'.format('item', item))
                matched = re.search(pattern, item, re.IGNORECASE)  # match against whole string
                if not item or matched:
                    continue
                synopsis = '{0}\n{1}'.format(synopsis, item)
            siteInfoDict['Synopsis'] = synopsis
            WrapText('Synopsis', synopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('.//div[@class="entry"]/p/text()[contains(.,"Genre: ")]')[0].strip().replace('Genre: ', '')
            htmlgenres = htmlgenres.split(',')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error: Getting Genres: {0}'.format(e))

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
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue
                
                countriesSet.add(tidyItem)

            showSetData(countriesSet, 'Countries (set*)')

        except Exception as e:
            log('UTILS :: Error: Getting Countries: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
                log('UTILS :: Error: Getting Site Film Duration: Reset to File Name Duration {0}'.format(e))
        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        FILMDICT['SceneAgent'] = True                 # notify update routine to crop images
        try:
            htmlimages = html.xpath('//div[@class="entry"]/p//img/@src')
            htmlimages = [x for x in htmlimages if 'jpg' in x]
            log('UTILS :: {0:<29} {1}'.format('Images', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
            poster = [htmlimages[0]]

            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoCDUniverse(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', htmlsynopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//td[text()="Category"]/following-sibling::td/a/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in AGENTDICT['pgmaCOUNTRYSET']:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error: Getting Genres/Countries: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
                        log('UTILS :: Error: Getting Review Source: {0}'.format(e))

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
                        log('UTILS :: Error: Getting Review Author (Stars & Writer): {0}'.format(e))


                    # Review Text - composed of Sexual Acts / tidy genres
                    reviewText = ''
                    try:
                        reviewText = htmlscene.xpath('.//span[@class="reviewtext"]/text()[normalize-space()]')
                        reviewText = ''.join(reviewText)
                        log('UTILS :: Review Text: {0}'.format(reviewText))
                    except Exception as e:
                        log('UTILS :: Error: Getting Review Text: {0}'.format(e))

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
                    log('UTILS :: Error: Getting Scene No. {0}: {1}'.format(sceneNo, e))

        except Exception as e:
            log('UTILS :: Error: Getting Scenes: {0}'.format(e))

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
            log('UTILS :: Error: Getting Rating: {0}'.format(e))
            siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoFagalicious(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', synopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        castSet = {x.strip() for x in siteInfoDict['Cast']}
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
            htmltags = [makeASCII(x) for x in htmltags]
            punctuation = ['!', ';', ':', '"', ',', '#', '$', '%', '^', '&', '*', '_', '~', '+', '?']
            pattern = re.escape(u'({0})'.format('|'.join(punctuation)))
            htmltags = [x for x in htmltags if not re.search(pattern, x)]
            htmltags = [x for x in htmltags if not x + ':' in FILMDICT['Title']]
            htmltags = [x for x in htmltags if not x.replace(' ', '').lower() in FILMDICT['CompareSiteStudio']]
            htmltags = [x for x in htmltags if not (len(x.split()) > 2 and not '.' in x)]       # most actors have forename/surname ignore if more than this and no initials in name
            htmltags = [(x[:-1]) if x[-1] == "'" else x for x in htmltags]                      # remove trailing apostrophes
            htmltags = list(set(htmltags))
            htmltags.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Tags', '{0:>2} - {1}'.format(len(htmltags), htmltags)))
            for idx, item in enumerate(htmltags, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))
                if tidyItem is None:                                      # If none skip
                    continue
                elif tidyItem:                                            # gayTidy returned an item
                    if tidyItem.lower() in AGENTDICT['pgmaGENRESDICT']:                    # check if genre
                        genresSet.add(tidyItem)
                    elif tidyItem in AGENTDICT['pgmaCOUNTRYSET']:                          # check if country
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
            log('UTILS :: Error: Getting Tags: Genres/Countries/Cast/Compilation: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoGayEmpire(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', htmlsynopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

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
            log('UTILS :: Error: Getting Collections: {0}'.format(e))

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//ul[@class="list-unstyled m-b-2"]//a[@label="Category"]/text()[normalize-space()]')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in AGENTDICT['pgmaCOUNTRYSET']:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error: Getting Genres/Countries: {0}'.format(e))

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
                log('UTILS :: Warning:, No Production Year: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
                log('UTILS :: Error: Getting Site Film Duration: {0}'.format(e))
        else:
            siteInfoDict['Duration'] = kwDuration

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
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
                        log('UTILS :: Error: Getting Review Text: {0}'.format(e))

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
                    log('UTILS :: Error: Getting Scene No. {0}: {1}'.format(sceneNo, e))

        except Exception as e:
            log('UTILS :: Error: Getting Scenes: {0}'.format(e))

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
def getSiteInfoGayHotMovies(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', htmlsynopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

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
            log('UTILS :: Error: Getting Collections: {0}'.format(e))

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//a[@label="Category"]/text()[normalize-space()]')
            genres = list(set(htmlgenres))
            genres = [x.strip() for x in genres if x.strip()]
            genres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(genres), genres)))
            compilation = 'Yes' if 'Compilation' in genres else 'No'
            for idx, item in enumerate(genres, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in AGENTDICT['pgmaCOUNTRYSET']:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error: Getting Genres/Countries: {0}'.format(e))

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
                log('UTILS :: Warning:, No Production Year: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
                log('UTILS :: Error: Getting Site Film Duration: {0}'.format(e))
        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        #       there are 3 ways front/art images are stored on gay hot movies - end with h.jpg for front and bh.jpg for art
        #                                                                      - end xfront.1.jpg for front and xback.1.jpg for art - these first two use the same xpath
        #                                                                      - just one image (old style)
        log(LOG_SUBLINE)
        try:
            poster = html.xpath('//img[@label="Front Boxcover"]/@src')
            art = html.xpath('//a[@class="fancy"]/@href')

        except Exception as e:
            log('UTILS :: Error: Getting Images: {0}'.format(e))
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
                    log('UTILS :: Error: Getting Scene No. {0}: {1}'.format(sceneNo, e))
        except Exception as e:
            log('UTILS :: Error: Getting Scenes: {0}'.format(e))

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
def getSiteInfoGayFetishandBDSM(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', htmlsynopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
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
            log('UTILS :: {0:<29} {1}'.format('Images', images))
            poster = [images[0]]
            art = [images[1] if len(images) > 1 else images[0]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoGayMovie(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', htmlsynopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
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
            log('UTILS :: {0:<29} {1}'.format('Images', images))
            poster = [images[0]]
            art = [images[1] if len(images) > 1 else images[0]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoGayRado(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', htmlsynopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//span[@style=""]/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in AGENTDICT['pgmaCOUNTRYSET']:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error: Getting Genres/Countries: {0}'.format(e))

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
                log('UTILS :: Error: Getting Site Film Duration: Reset to File Name Duration {0}'.format(e))

        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//a[contains(@class,"magictoolbox")]/@href')
            log('UTILS :: {0:<29} {1}'.format('Images', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoGayWorld(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', htmlsynopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
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
            log('UTILS :: {0:<29} {1}'.format('Images', images))
            poster = [images[0]]
            art = [images[1] if len(images) > 1 else images[0]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoGEVI(AGENTDICT, FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'GEVI'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        siteInfoDict['Synopsis'] = ' '
        synopsis = ''
        try:
            htmlsynopsis = html.xpath('//div[contains(@class,"text-justify wideCols-1")]/p[@class="mb-2"]/span[@style]/text()')
            synopsis = '\n'.join(htmlsynopsis).strip()
            if synopsis:
                regex = r'View this scene at.*|found in compilation.*|see also.*|^\d+\.$'
                pattern = re.compile(regex, re.IGNORECASE | re.MULTILINE)
                synopsis = re.sub(pattern, '', synopsis).strip()

        except Exception as e:
            log('UTILS :: Warning: Getting GEVI Synopsis (Try External): {0}'.format(e))

        if synopsis:
            key = 'GEVI'
        else:
            for key in ['AEBN', 'GayEmpire', 'GayHotMovies']:
                if key in FILMDICT and FILMDICT[key] != {}:
                    if 'Synopsis' in FILMDICT[key] and FILMDICT[key]['Synopsis']:
                        synopsis = FILMDICT[key]['Synopsis']
                        break
        siteInfoDict['Synopsis'] = synopsis if synopsis else ' '
        WrapText('Synopsis from {0}'.format(key), synopsis)

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            # GEVI has access to external websites: AEBN, GayHotMovies, then GayEmpire
            htmldirectors = html.xpath('//a[contains(@href, "director/")]/text()')
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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

        #   3.  Cast
        log(LOG_SUBLINE)
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
            try:
                # GEVI has access to external websites: AEBN, GayHotMovies, then GayEmpire
                htmlcast = html.xpath('//a[contains(@href, "performer/")]//text()')
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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        try:
            try:
                htmlbodytypes = html.xpath('//div[.="Body Type:"]/following-sibling::div/div/text()')[0].strip()           # add GEVI body type to genres
                htmlbodytypes = htmlbodytypes.replace(';', ',')
                htmlbodytypes = [x.strip() for x in htmlbodytypes.split(',') if x.strip()]
                log('UTILS :: {0:<29} {1}'.format('Body Types', '{0:>2} - {1}'.format(len(htmlbodytypes), htmlbodytypes)))

            except Exception as e:
                htmlbodytypes = []
                log('UTILS :: Warning: No Body Types: {0}'.format(e))

            try:
                htmlcategories = html.xpath('//div[.="Category:"]/following-sibling::div/text()')[0].strip()                # add GEVI categories to genres
                htmlcategories = [x.strip() for x in htmlcategories.split(',') if x.strip()]
                log('UTILS :: {0:<29} {1}'.format('Categories', '{0:>2} - {1}'.format(len(htmlcategories), htmlcategories)))

            except Exception as e:
                htmlcategories = []
                log('UTILS :: Warning: No Categories: {0}'.format(e))

            try:
                htmltypes = html.xpath('//div[.="Type:"]/following-sibling::div/div/text()')[0].strip()                     # add GEVI types
                htmltypes = htmltypes.replace(';', ',')
                htmltypes = [x.strip() for x in htmltypes.split(',') if x.strip()]
                log('UTILS :: {0:<29} {1}'.format('Types', '{0:>2} - {1}'.format(len(htmltypes), htmltypes)))

            except Exception as e:
                htmltypes = []
                log('UTILS :: Warning: No Types: {0}'.format(e))

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
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            log('UTILS :: {0:<29} {1}'.format('Combined Genres', '{0:>2} - {1}'.format(len(genresSet), sorted(genresSet))))
            siteInfoDict['Genres'] = genresSet

        except Exception as e:
            siteInfoDict['Genres'] = set()
            log('UTILS :: Error: Getting Genres: {0}'.format(e))

        #   5b.   Countries
        log(LOG_SUBLINE)
        try:
            # GEVI has access to external websites: AEBN, GayHotMovies, then GayEmpire
            for key in ['AEBN', 'GayHotMovies', 'GayEmpire']:
                if key in FILMDICT and FILMDICT[key] != {}:
                    if 'Countries' in FILMDICT[key] and FILMDICT[key]['Countries'] != set():
                        countriesSet.update(FILMDICT[key]['Countries'])

            log('UTILS :: {0:<29} {1}'.format('External Countries', '{0:>2} - {1}'.format(len(countriesSet), sorted(countriesSet))))

            htmlcountries = html.xpath('//div[.="Location:"]/following-sibling::div/text()')[0].strip()
            htmlcountries = [x.strip() for x in htmlcountries.split(',')]
            log('UTILS :: {0:<29} {1}'.format('GEVI Countries', '{0:>2} - {1}'.format(len(htmlcountries), htmlcountries)))
            for idx, item in enumerate(htmlcountries, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))
                if tidyItem is None:        # Don't process
                    continue

                countriesSet.add(tidyItem if tidyItem else item)

            log('UTILS :: {0:<29} {1}'.format('Combined Countries', '{0:>2} - {1}'.format(len(countriesSet), sorted(countriesSet))))
            siteInfoDict['Countries'] = countriesSet

        except Exception as e:
            siteInfoDict['Countries'] = set()
            log('UTILS :: Warning: No Countries: {0}'.format(e))        # countries not default field, so warning

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

                htmlTD = html.xpath('//td/text()[normalize-space()]')         # get all table data ** dirty coing as xpath is not working
                if 'Gay Erotic Video Index' in htmlTD:         # format 1 like Bring me a boy 68
                    htmlTD = html.xpath('//td/text()[normalize-space()]')         # get all table data ** dirty coing as xpath is not working
                    htmlIdx = [x for x in range(len(htmlTD)) if htmlTD[x] == 'released' or htmlTD[x] == 'produced']
                    htmldate = set()
                    [htmldate.add(htmlTD[x+1]) for x in htmlIdx]
                else:                                           # format 2 - normal
                    htmldate = html.xpath('//td[a[contains(@href,"company/")]]/following-sibling::td[1]/text()[normalize-space()]')
                    try:
                        htmldate.append(html.xpath('//div[contains(.,"Produced")]/following-sibling::div[1]/text()[normalize-space()]')[0])
                    except Exception as e:
                        pass

                productionDates = set()
                for item in htmldate:
                    item = item.strip()
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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration - GEVI Format = MMM
        kwDuration = kwargs.get('kwDuration')
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlTD = html.xpath('//td/text()[normalize-space()]')                           # get all table data ** dirty coing as xpath is not working
                durations = set()
                if 'Gay Erotic Video Index' in htmlTD:                                          # format 1 like Bring me a boy 68
                    htmlIdx = [x for x in range(len(htmlTD)) if htmlTD[x] == 'length']          # fhtmlTD determined in release date code above
                    [durations.add(htmlTD[x+1]) for x in htmlIdx]
                else:
                    durations.add(html.xpath('//td[a[contains(@href,"company/")]]/following-sibling::td[2]/text()[normalize-space()]')[0])

                durations = {datetime.fromtimestamp(int(htmlTD[x+1]) * 60) for x in durations if x.strip()}
                siteInfoDict['Duration'] = sorted(durations)[-1] if durations else datetime.fromtimestamp(0)  # longest length or 0 time

            except Exception as e:
                siteInfoDict['Duration'] = datetime.fromtimestamp(0)
                log('UTILS :: Error: Getting Site Film Duration: {0}'.format(e))
        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            # for posters - GayHotMovies comes last in priority as the other 2 have better qualty
            htmlimages = html.xpath('//img/@src[contains(.,"Covers/")]')
            htmlimages = [(BASE_URL + '/' if BASE_URL not in image else '') + image.replace('/Icons/','/') for image in htmlimages]
            log('UTILS :: {0:<29} {1}'.format('Images', '{0:>} - {1}'.format(len(htmlimages), htmlimages)))
            images = []
            [images.append(x) for x in htmlimages if x not in images]
            poster = [images[0]]
            art = [images[1] if len(images) > 1 else images[0]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))
            log('UTILS :: Add External Poster/Art')

            for key in ['AEBN', 'GayEmpire', 'GayHotMovies']:
                myExternalDict = FILMDICT.get(key, '')
                if myExternalDict:
                    externalPoster = myExternalDict.get('Poster', '')
                    poster.extend(externalPoster)
                    externalArt = myExternalDict.get('Art', '')
                    art.extend(externalArt)
                    break

            log('UTILS :: {0:<29} {1}'.format('Poster - After Addition', poster))
            log('UTILS :: {0:<29} {1}'.format('Art - After Addition', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
            htmlscenes = html.xpath('//div[contains(@class,"scene flex")]')
            log('UTILS :: {0:<29} {1}'.format('Possible Number of Scenes', len(htmlscenes)))

            for sceneNo, htmlscene in enumerate(htmlscenes, start=1):
                try:
                    # scene No
                    log('UTILS :: {0:<29} {1}'.format('Scene', sceneNo))

                    # Review Source - composed of cast list or iafd scenes cast or Film title in that order of preference
                    reviewSource = ''
                    try:
                        reviewSource = htmlscene.xpath('./div/a[contains(@href,"performer/")]/parent::div/a/span/text()[normalize-space()]')
                        reviewSource = ','.join(reviewSource).strip()
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
                        reviewText = htmlscene.xpath('./div/div/p[@class="mb-2"]/span/text()[normalize-space()]')
                        reviewText = '\n'.join(reviewText).strip()
                    except:
                        log('UTILS :: Error: Getting Review Text: {0}'.format(e))
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
                    log('UTILS :: Error: Getting Scene No. {0}: {1}'.format(sceneNo, e))

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
            log('UTILS :: Error: Getting Scenes: {0}'.format(e))

        finally:
            siteInfoDict['Scenes'] = scenesDict
            siteInfoDict['Chapters'] = chaptersDict

        #   10.  Rating
        log(LOG_SUBLINE)
        try:
            htmlrating = html.xpath('//div[.="Rating Out of 4:"]/following-sibling::div/text()|//div[.="Rating Out of 4:"]/following-sibling::div/div/text()')
            starCountList = []
            ratingList = []
            for x in htmlrating:
                if x == 'Produced:':
                    break
                if '*' in x:
                    starCountList.append(x.count('*'))

            rating = 0.0
            if starCountList:
                log('UTILS :: {0:<29} {1}'.format('Star Count', '{0} Stars'.format(starCountList)))
                ratingList = [x * 10 / 4 if x > 0 else 0.0 for x in starCountList]
                log('UTILS :: {0:<29} {1}'.format('Ratings', '{0}'.format(ratingList)))
                sumRating = 0.0
                for x in ratingList:
                    sumRating += x
                rating = (sumRating/len(ratingList)) * 1.0            # get average of rating

            log('UTILS :: {0:<29} {1}'.format('{0}Film Rating'.format('Avg. ' if len(ratingList) > 1 else ''), rating))

            siteInfoDict['Rating'] = rating

        except Exception as e:
            siteInfoDict['Rating'] = 0.0
            log('UTILS :: Error: Getting Rating: {0}'.format(e))

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoGEVIScenes(AGENTDICT, FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'GEVIScenes'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    try:
        #   1.  Synopsis
        log(LOG_SUBLINE)
        siteInfoDict['Synopsis'] = ' '
        synopsis = ' '
        try:
            htmlsynopsis = html.xpath('//p[@class="mb-2"]/span/text()')
            synopsis = '\n'.join(htmlsynopsis).strip()
            siteInfoDict['Synopsis'] = synopsis if synopsis else ' '
            WrapText('Synopsis', synopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

        #   2.  Directors
        log(LOG_SUBLINE)
        log('UTILS :: No Directors Listed on Agent')
        siteInfoDict['Directors'] = []

        #   3.  Cast
        log(LOG_SUBLINE)
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
            try:
                htmlcast = html.xpath('//a[contains(@href, "performer/")]//text()')
                cast = list(set(htmlcast))
                cast.sort(key = lambda x: x.lower())
                siteInfoDict['Cast'] = cast[:]
                log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

            except Exception as e:
                siteInfoDict['Cast'] = []
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            myDict = {'A': 'Anal Sex', 'O': 'Oral Sex', 'R': 'Rimming'}
            htmlgenres = html.xpath('//td/a[contains(@href, "performer/")]/parent::td/following-sibling::td[@class="pd"]/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            for idx, item in enumerate(htmlgenres, start=1):
                for myKey, myValue  in myDict.items():
                    if myKey in item:
                        log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, myValue)))
                        genresSet.add(myValue)

            siteInfoDict['Genres'] = genresSet
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error: Getting Genres: {0}'.format(e))

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Compilation'] = compilation

        #   5b.  Countries
        log(LOG_SUBLINE)
        log('UTILS :: No Countries Info on Agent - Country data retrieved from synopsis')
        siteInfoDict['Countries'] = countriesSet

        #   6.  Release Date
        log(LOG_SUBLINE)
        kwReleaseDate = kwargs.get('kwReleaseDate')
        log('UTILS :: {0:<29} {1}'.format('KW Release Date', kwReleaseDate))
        siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration 
        log(LOG_SUBLINE)
        kwDuration = kwargs.get('kwDuration')
        log('UTILS :: {0:<29} {1}'.format('KW Duration', kwDuration))
        siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimage = html.xpath('//img[contains(@src, "Episodes/")]/@src')[0].strip()
            htmlimage = (BASE_URL + '/' if BASE_URL not in htmlimage else '') + htmlimage
            log('UTILS :: {0:<29} {1}'.format('Image:', htmlimage))
            poster = [htmlimage]
            art = [htmlimage]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoHFGPM(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', synopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: No Cast - Try and Extract from Synopsis: {0}'.format(e))
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
                    log('UTILS :: Error: Getting Cast: {0}'.format(e))

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
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
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            log('UTILS :: {0:<29} {1}'.format('Combined Genres', '{0:>2} - {1}'.format(len(genresSet), sorted(genresSet))))
            siteInfoDict['Genres'] = genresSet

            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error: Getting Genres: {0}'.format(e))

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
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                countriesSet.add(tidyItem)

            showSetData(countriesSet, 'Countries (set*)')

        except Exception as e:
            log('UTILS :: Error: Getting Countries: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
                log('UTILS :: Error: Getting Site Film Duration: Reset to File Name Duration {0}'.format(e))
        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//div[@class="base fullstory"]/div[@class="maincont clr"]//div//img/@src')
            for i, htmlimage in enumerate(htmlimages):
                htmlimages[i] = htmlimage if 'https:' in htmlimage else 'https:' + htmlimage

            log('UTILS :: {0:<29} {1}'.format('Images', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoHomoActive(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', synopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
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
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if not tidyItem or tidyItem is None:        # Don't process
                    continue

                countriesSet.add(tidyItem)

            showSetData(countriesSet, 'Countries (set*)')

        except Exception as e:
            log('UTILS :: Error: Getting Countries: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
        else:
            siteInfoDict['ReleaseDate'] = kwReleaseDate

        #   7.  Duration 
        kwDuration = kwargs.get('kwDuration')
        log('UTILS :: {0:<29} {1}'.format('KW Duration', kwDuration))
        if kwDuration is None:
            log(LOG_SUBLINE)
            try:
                htmlduration = html.xpath('//dt[text()="Run Time:"]/following-sibling::dd[1]/text()[normalize-space()]')[0].strip()
                htmlduration = re.sub('[^0-9]', '', htmlduration).strip()                      # strip away alphabetic characters leaving mins
                duration = int(duration) * 60                                                  # convert to seconds
                duration = datetime.fromtimestamp(duration)
                siteInfoDict['Duration'] = duration
                log('UTILS :: {0:<29} {1}'.format('Duration', duration.strftime('%H:%M:%S')))

            except Exception as e:
                siteInfoDict['Duration'] = FILMDICT['Duration']
                log('UTILS :: Error: Getting Site Film Duration: Reset to File Name Duration {0}'.format(e))
        else:
            siteInfoDict['Duration'] = kwDuration

        #   8.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//img[@class="gallery-image"]/@src')
            log('UTILS :: {0:<29} {1}'.format('Images', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoIAFD(AGENTDICT, FILMDICT, **kwargs):
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
            synopsis = '\n'.join(htmlsynopsis)
            siteInfoDict['Synopsis'] = synopsis
            FILMDICT['Synopsis'] = synopsis
            WrapText('Synopsis', synopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            FILMDICT['Synopsis'] = ''
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

        #   2.  Directors
        log(LOG_SUBLINE)
        try:
            directors = getRecordedDirectors(html, AGENTDICT, FILMDICT)
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), sorted(directors))))
            siteInfoDict['Directors'] = directors
            FILMDICT['Directors'] = directors                         # this field holds the directos if the film is found on iafd

        except Exception as e:
            siteInfoDict['Directors'] = {}
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

        #   3.  Cast
        log(LOG_SUBLINE)
        if FILMDICT['FilenameCast']:        # if a cast list has been provided, use it and don't process html
            siteInfoDict['Cast'] = [x for x in FILMDICT['FilenameCast']]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(siteInfoDict['Cast']), siteInfoDict['Cast'])))
        else:
            try:
                cast  = getRecordedCast(html, AGENTDICT, FILMDICT)
                log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), sorted(cast))))
                siteInfoDict['Cast'] = cast
                FILMDICT['Cast'] = cast                                  # this field holds the cast if the film is found on iafd

            except Exception as e:
                siteInfoDict['Cast'] = {}
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        try:
            #   IAFD lists the sexual activities of the cast members under their pictures at times
            if siteInfoDict['Cast']:
                rolesSet = {cast[x]['Role'] for x in siteInfoDict['Cast'].keys()}
                rolesSet = {x for x in rolesSet if 'AKA' not in x and x != RIGHT_TICK}
                rolesSet = set(' '.join(rolesSet).split())
                log('UTILS :: {0:<29} {1}'.format('Roles Word Count', '{0:>2} - {1}'.format(len(rolesSet), rolesSet)))
                for idx, item in enumerate(rolesSet, start=1):
                    tidyItem = findTidy(AGENTDICT, item)
                    if not tidyItem or tidyItem is None:        # Don't process
                        continue

                    if tidyItem in AGENTDICT['pgmaCOUNTRYSET']:
                        continue

                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))
                    genresSet.add(tidyItem)

            else:
                log('UTILS :: No Cast Recorded')

                showSetData(countriesSet, 'Countries (set*)')
                showSetData(genresSet, 'Genres (set*)')

        except Exception as e:
            log('UTILS :: Error: Getting Genres/Countries: {0}'.format(e))

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet

        #   5b.  Compilation
        kwCompilation = kwargs.get('kwCompilation')
        compilation = 'No'
        if kwCompilation is None:
            log(LOG_SUBLINE)
            try:
                # if already set to yes by possible checking of external sources [AEBN, GayEmpire, GayHotMovies], dont change with IAFD value
                htmlcompilation = html.xpath('//p[@class="bioheading" and text()="Compilation"]//following-sibling::p[1]/text()')[0].strip()
                compilation = htmlcompilation.title()
                log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))
                siteInfoDict['Compilation'] = compilation if compilation == 'Yes' else 'No'

            except Exception as e:
                siteInfoDict['Compilation'] = compilation
                log('UTILS :: Error: Getting Compilation Information: {0}'.format(e))
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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
                log('UTILS :: Error: Getting Site Film Duration: {0}'.format(e))
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
            log('UTILS :: Error: Getting Scenes: {0}'.format(e))

        finally:
            siteInfoDict['Scenes'] = scenesDict

        #   10.  Rating
        log(LOG_SUBLINE)
        log('UTILS :: No Rating Info on Agent - Set to 0.0')
        siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoQueerClick(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', synopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

        #   4.  Collections - None in this Agent
        log(LOG_SUBLINE)
        log('UTILS :: No Collection Info on Agent')
        siteInfoDict['Collections'] = []

        #   5.  Tag List: Genres and possible Countries, Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        castSet = {x.strip() for x in siteInfoDict['Cast']}
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
            htmltags = [makeASCII(x) for x in htmltags]
            punctuation = ['!', ';', ':', '"', ',', '#', '$', '%', '^', '&', '*', '_', '~', '+', '?']
            pattern = re.escape(u'({0})'.format('|'.join(punctuation)))
            htmltags = [x for x in htmltags if not re.search(pattern, x)]
            htmltags = [x for x in htmltags if not ':' in x]
            htmltags = [x for x in htmltags if not x + ':' in FILMDICT['Title']]
            htmltags = [x for x in htmltags if not x.replace(' ', '').lower() in FILMDICT['CompareSiteStudio']]
            htmltags = [x for x in htmltags if not (len(x.split()) > 2 and not '.' in x)]       # most actors have forename/surname ignore if more than this and no initials in name
            htmltags = [(x[:-1]) if x[-1] == "'" else x for x in htmltags]                      # remove trailing apostrophes
            htmltags = list(set(htmltags))
            htmltags.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Tags', '{0:>2} - {1}'.format(len(htmltags), htmltags)))
            for idx, item in enumerate(htmltags, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))
                if tidyItem is None:                                      # If none skip
                    continue
                elif tidyItem:                                            # gayTidy returned an item
                    if tidyItem.lower() in AGENTDICT['pgmaGENRESDICT']:                    # check if genre
                        genresSet.add(tidyItem)
                    elif tidyItem in AGENTDICT['pgmaCOUNTRYSET']:                          # check if country
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
            log('UTILS :: Error: Getting Tags: Genres/Countries/Cast/Compilation: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
            log('UTILS :: {0:<29} {1}'.format('Images', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]

            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoSimplyAdult(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', htmlsynopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

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
            log('UTILS :: Error: Getting Collections: {0}'.format(e))

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
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

            log('UTILS :: {0:<29} {1}'.format('Images', htmlimages))
            poster = [htmlimages[0]]
            art = [htmlimages[0] if len(htmlimages) == 1 else htmlimages[1]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
            log('UTILS :: Error: Getting Rating: {0}'.format(e))
            siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoWayBig(AGENTDICT, FILMDICT, **kwargs):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    mySource = 'WayBig'
    siteInfoDict = {}
    kwFilmHTML = kwargs.get('kwFilmHTML')
    html = FILMDICT['FilmHTML'] if kwFilmHTML is None else kwFilmHTML
    log('UTILS :: HTML: {0}'.format(html))

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
            WrapText('Synopsis', synopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        castSet = {x.strip() for x in siteInfoDict['Cast']}
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
            htmltags = [makeASCII(x) for x in htmltags]
            punctuation = ['!', ';', ':', '"', ',', '#', '$', '%', '^', '&', '*', '_', '~', '+', '?']
            pattern = re.escape(u'({0})'.format('|'.join(punctuation)))
            htmltags = [x for x in htmltags if not re.search(pattern, x)]
            htmltags = [x for x in htmltags if not x + ':' in FILMDICT['Title']]
            htmltags = [x for x in htmltags if not x.replace(' ', '').lower() in FILMDICT['CompareSiteStudio']]
            htmltags = [x for x in htmltags if not (len(x.split()) > 2 and not '.' in x)]       # most actors have forename/surname ignore if more than this and no initials in name
            htmltags = [(x[:-1]) if x[-1] == "'" else x for x in htmltags]                      # remove trailing apostrophes
            htmltags = list(set(htmltags))
            htmltags.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Tags', '{0:>2} - {1}'.format(len(htmltags), htmltags)))
            for idx, item in enumerate(htmltags, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))
                if tidyItem is None:                                      # If none skip
                    continue
                elif tidyItem:                                            # gayTidy returned an item
                    if tidyItem.lower() in AGENTDICT['pgmaGENRESDICT']:                    # check if genre
                        genresSet.add(tidyItem)
                    elif tidyItem in AGENTDICT['pgmaCOUNTRYSET']:                          # check if country
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
            log('UTILS :: Error: Getting Tags: Genres/Countries/Cast/Compilation: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
            htmlimages = html.xpath('//img[contains(@src, "zing.waybig.com/reviews")]/@src')
            log('UTILS :: {0:<29} {1}'.format('Images', htmlimages))
            images = []
            [images.append(x.replace('\n', '')) for x in htmlimages if x not in images] # sometimes new lines are found in @src
            poster = [images[0]]
            art = [images[1] if len(images) > 1 else images[0]]
            log('UTILS :: {0:<29} {1}'.format('Poster', poster))
            log('UTILS :: {0:<29} {1}'.format('Art', art))

        except Exception as e:
            poster = []
            art = []
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
def getSiteInfoWolffVideo(AGENTDICT, FILMDICT, **kwargs):
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
            WrapText('Synopsis', htmlsynopsis)

        except Exception as e:
            siteInfoDict['Synopsis'] = ' '
            log('UTILS :: Error: Getting Synopsis: {0}'.format(e))

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
            log('UTILS :: Error: Getting Director(s): {0}'.format(e))

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
                log('UTILS :: Error: Getting Cast: {0}'.format(e))

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
            log('UTILS :: Error: Getting Collections: {0}'.format(e))

        #   5.  Genres, Countries and Compilation
        log(LOG_SUBLINE)
        countriesSet, genresSet = synopsisCountriesGenres(AGENTDICT, siteInfoDict['Synopsis'])         # extract possible genres and countries from the synopsis
        compilation = 'No'
        try:
            htmlgenres = html.xpath('//p/a[@href[contains(.,"display-movies/category")]]/text()')
            htmlgenres = [x.strip() for x in htmlgenres if x.strip()]
            htmlgenres.sort(key = lambda x: x.lower())
            log('UTILS :: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            compilation = 'Yes' if 'Compilation' in htmlgenres else 'No'
            for idx, item in enumerate(htmlgenres, start=1):
                tidyItem = findTidy(AGENTDICT, item)
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, tidyItem)))

                if tidyItem is None:        # Don't process
                    continue

                if tidyItem in AGENTDICT['pgmaCOUNTRYSET']:
                    countriesSet.add(tidyItem)
                    continue

                genresSet.add(tidyItem if tidyItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation?', compilation))

        except Exception as e:
            log('UTILS :: Error: Getting Genres/Countries: {0}'.format(e))

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
                log('UTILS :: Error: Getting Release Date: {0}'.format(e))
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
            log('UTILS :: Error: Getting Images: {0}'.format(e))

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
                        log('UTILS :: Error: Getting Review Source: {0}'.format(e))

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
                        log('UTILS :: Review Text: {0}'.format(reviewText))
                    except Exception as e:
                        log('UTILS :: Error: Getting Review Text: {0}'.format(e))

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
                    log('UTILS :: Error: Getting Scene No. {0}: {1}'.format(sceneNo, e))

        except Exception as e:
            log('UTILS :: Error: Getting Scenes: {0}'.format(e))

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
            log('UTILS :: Error: Getting Rating: {0}'.format(e))
            siteInfoDict['Rating'] = 0.0

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getURLElement(myString, FilterYear=0, UseAdditionalResults=False):
    ''' check IAFD web site for better quality thumbnails irrespective of whether we have a thumbnail or not '''
    msg = ''    # this variable will be set if IAFD fails to be read
    html = ''
    if FilterYear:
        FilterYear = int(FilterYear)
        startYear = FilterYear if AGENT == 'IAFD' else FilterYear - 3
        endYear = FilterYear if AGENT == 'IAFD' else FilterYear +1
        myString = '{0}{1}'.format(myString, IAFD_FILTER.format(startYear, endYear))

    try:
        html = getHTTPRequest(myString, timeout=20)
        if UseAdditionalResults:
            try:
                myString = html.xpath('//a[text()="See More Results..."]/@href')[0].strip().replace(' ', '%20')
                myString = IAFD_BASE + myString if IAFD_BASE not in myString else myString
                htmlAdditional = getHTTPRequest(myString, timeout=20)
                html = htmlAdditional

            except Exception as e:
                htmlAdditional = ''
                log('UTILS :: Warning: No Additional Search Results: {0}'.format(e))

    except Exception as e:
        html = ''
        msg = '< Failed to read IAFD URL: {0} - Processing Abandoned! >'.format(e)
        raise Exception(msg)

    return html
# ----------------------------------------------------------------------------------------------------------------------------------
def getUserAgent(*args):
    ''' Pick Random User-Agent '''
    from random_user_agent.user_agent import UserAgent
    from random_user_agent.params import SoftwareName, OperatingSystem, Popularity, HardwareType

    software_names = [SoftwareName.ANDROID, SoftwareName.SAFARI]
    '''
    os = platform.system()

    if os == 'Windows':
        operating_systems = [OperatingSystem.WINDOWS]
    elif os == 'Linux':
        operating_systems = [OperatingSystem.LINUX]
    elif os == 'Darwin':
        operating_systems = [OperatingSystem.DARWIN, OperatingSystem.MAC, OperatingSystem.MACOS, OperatingSystem.MAC_OS_X]
    elif os == 'FreeBSD':
        operating_systems = [OperatingSystem.FREEBSD]
    '''
    operating_systems = [OperatingSystem.ANDROID, OperatingSystem.IOS]
    popularity = [Popularity.UNCOMMON]
    hardware_types = [HardwareType.MOBILE]

    # set number of user agents required by providing `limit` as parameter
    limit = random.randint(60, 100)
    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, hardware_types=hardware_types, popularity=popularity, limit=limit)

    '''
    # Get list of user agents.
    pattern = r'Windows\sNT\s\d\d.'     # i.e Windows NT 10.0 and above
    matchedUserAgents = []
    user_agents = user_agent_rotator.get_user_agents()
    for item in user_agents:
        user_agent = item.get('user_agent', '')
        if re.search(pattern, user_agent):
            matchedUserAgents.append(user_agent)
    user_agent = random.choice(matchedUserAgents)
    '''

    # Get Random User Agent String.
    user_agent = user_agent_rotator.get_random_user_agent()
    return user_agent

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
            if '*SET*' in value:
                value = value[1:]
                dict[key] = set(value)
            else:
                dict[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

            log('UTILS :: {0:<29}    {1}'.format('    {0}'.format(key), dict[key]))
            continue

        except:
            pass

    return dict

# ----------------------------------------------------------------------------------------------------------------------------------
def log(message, *args):
    ''' log messages '''
    if re.search('ERROR|WARNING', message, re.IGNORECASE):
        exceptionTraceback = sys.exc_info()[2]
        try:
            fileName = os.path.basename(exceptionTraceback.tb_frame.f_code.co_filename)
        except:
            fileName = ''
        
        try:
            lineNo = exceptionTraceback.tb_lineno
        except:
            lineNo = ''

        myTick = WRONG_TICK if re.search('ERROR', message, re.IGNORECASE) else WARNING_TICK
        Log.Error(AGENT + ' - {0} {1} File: {2}, Line: {3}, Function: {4} -> {5} -> {6}'.format(message[0:8], myTick, fileName, lineNo, inspect.stack()[3][3], inspect.stack()[2][3], inspect.stack()[1][3]))
        Log.Error(AGENT + ' - {0}    {1}'.format(message[0:8], message[9:]))

    else:
        Log.Info(AGENT + '  - ' + message, *args)

# ----------------------------------------------------------------------------------------------------------------------------------
def logHeader(myFunc, AGENTDICT, media, lang):
    ''' log header for search and update functions '''
    log(LOG_ASTLINE)
    log(LOG_ASTLINE)
    log('{0}:: Version:                         v.{1}'.format(myFunc, VERSION_NO))
    log('{0}:: Utility Update Date:             {1}'.format(myFunc, UTILS_UPDATE))
    log('{0}:: Python:                          {1} ({2}): {3}'.format(myFunc, platform.python_version(), platform.architecture()[0], platform.python_build()))
    log('{0}:: Platform:'.format(myFunc))
    log('{0}::   > Operating System:            {1}'.format(myFunc, platform.system()))
    log('{0}::   > Release:                     {1}'.format(myFunc, platform.release()))
    log('{0}:: Preferences:'.format(myFunc))
    log('{0}::   > Legend Before Summary:       {1}'.format(myFunc, AGENTDICT['prefPREFIXLEGEND']))
    log('{0}::   > Collection Gathering:'.format(myFunc))
    log('{0}::      > System:                   {1}'.format(myFunc, RIGHT_TICK if AGENTDICT['prefCOLSYSTEM'] else WRONG_TICK))
    log('{0}::      > Genres:                   {1}; prefix with {2} symbol?: {3}'.format(myFunc, RIGHT_TICK if AGENTDICT['prefCOLGENRE'] else WRONG_TICK, AGENT_TYPE, RIGHT_TICK if AGENTDICT['prefPREFIXGENRE'] is True else WRONG_TICK))
    log('{0}::      > Countries                 {1}; display as {2}'.format(myFunc, RIGHT_TICK if AGENTDICT['prefCOLCOUNTRY'] else WRONG_TICK, AGENTDICT['prefCOUNTRYPOSTERTYPE']))
    log('{0}::      > Studio:                   {1}'.format(myFunc, RIGHT_TICK if AGENTDICT['prefCOLSTUDIO'] else WRONG_TICK))
    log('{0}::      > Series:                   {1}'.format(myFunc, RIGHT_TICK if AGENTDICT['prefCOLSERIES'] else WRONG_TICK))
    log('{0}::      > Directors:                {1}'.format(myFunc, RIGHT_TICK if AGENTDICT['prefCOLDIRECTOR'] else WRONG_TICK))
    log('{0}::      > Cast:                     {1}'.format(myFunc, RIGHT_TICK if AGENTDICT['prefCOLCAST'] else WRONG_TICK))
    log('{0}::   > Poster Source - Download?    {1}'.format(myFunc, AGENTDICT['prefPOSTERSOURCEDOWNLOAD']))
    log('{0}::   > Match IAFD Duration:         {1}'.format(myFunc, AGENTDICT['prefMATCHIAFDDURATION']))
    log('{0}::   > Match Site Duration:         {1}'.format(myFunc, AGENTDICT['prefMATCHSITEDURATION']))
    log('{0}::   > Duration Dx                  ±{1} minutes'.format(myFunc, AGENTDICT['prefDURATIONDX']))
    log('{0}::   > Language Detection:          {1}'.format(myFunc, AGENTDICT['prefDETECT']))
    log('{0}::   > Library:Site Language:       {1}:{2}'.format(myFunc, lang, SITE_LANGUAGE))
    log('{0}:: Media:'.format(myFunc))
    log('{0}::   > Library:                     {1}'.format(myFunc, AGENTDICT['pgmaLIBRARYTITLE']))
    log('{0}::   > Title:                       {1}'.format(myFunc, media.title))
    log('{0}::   > File Path:                   {1}'.format(myFunc, media.items[0].parts[0].file))
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
        log('{0}:: {1}'.format(myFunc, footer.center(131, '*')))
    log(LOG_ASTLINE)

# -------------------------------------------------------------------------------------------------------------------------------
def makeASCII(myString):
    ''' standardise single quotes, double quotes and accented characters '''
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

    myString = unidecode(myString)                          # strip all accents, umlauts etc and replace with ASCII equivalent

    return myString

# ----------------------------------------------------------------------------------------------------------------------------------
def matchCast(unmatchedCastList, AGENTDICT, FILMDICT):
    ''' check IAFD web site for individual cast'''
    matchedCastDict = {}
    castAliasList = []
    castAwards = []
    castBio = {}
    castCompareName = ''
    castCompareAliasList = []
    castFilms = []
    castNationality = ''
    castPhoto = AGENTDICT['pgmaNOCASTPOSTER']
    castRealName = ''
    castRole = WRONG_TICK
    castURL = ''
    blankCast = {'Alias': castAliasList, 'Awards': castAwards, 'Bio': castBio, 'CompareName': castCompareName, 'CompareAlias': castCompareAliasList, 
                 'Films': castFilms, 'Nationality': castNationality, 'Photo': castPhoto, 'RealName': castRealName, 'Role': castRole, 'URL': castURL}

    unmatchedCast = ''
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
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Cast: Partial Match - Cast Name', IAFDCompareName))
                matchedName = True
                break

            # 4th partial match against Cast Alias
            if compareUnmatchedCast in IAFDCompareAlias:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Cast: Partial Match - Cast Alias', IAFDCompareAlias))
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
            if matchedName is True:
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
                if matchedName is True:
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
            if matchedName is True:
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
                if matchedName is True:
                    log('UTILS :: {0:<29} {1}'.format('SoundEx Match', testNameType))
                    log('UTILS :: {0:<29} {1}'.format('  IAFD Cast Alias', testAlias))
                    log('UTILS :: {0:<29} {1}'.format('  Agent Cast Name', unmatchedCast))
                    log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(soundIAFD, soundAgent)))
                    log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                    break

        if matchedName is True: # we have a match
            log(LOG_SUBLINE)
            continue            # on to the next cast

        # the cast on the website has not matched to those listed against the film in IAFD. So search for the cast's entry on IAFD
        matchedCastDict[unmatchedCast] = copy.deepcopy(blankCast)

        # default is Gay/Bisexual/Straight
        castLimit = 50
        xPath = '//table[@id="tblFem" or @id="tblMal"]/tbody/tr'
        xType = 'Gay/Bisexual/Straight'
        if FILMDICT['FoundOnIAFD'] == 'Yes':
            if FILMDICT['AllMale'] == 'Yes' and FILMDICT['AllGirl'] == 'No':
                castLimit = 25
                xPath = '//table[@id="tblMal"]/tbody/tr'
                xType = 'Gay'
            
            elif FILMDICT['AllMale'] == 'No' and FILMDICT['AllGirl'] == 'Yes':
                castLimit = 25
                xPath = '//table[@id="tblFem"]/tbody/tr'
                xType = 'Lesbian'

            else:
                castLimit = 50
                xPath = '//table[@id="tblFem" or @id="tblMal"]/tbody/tr'
                xType = 'Bisexual/Straight'

        log('UTILS :: {0:<29} {1}'.format('{0} Cast xPath'.format(xType), xPath))
        try:
            html = getURLElement(IAFD_SEARCH_URL.format(String.URLEncode(unmatchedCast)), FilterYear = myYear) # remove full stops before encoding
            castList = html.xpath(xPath)
            castFound = len(castList)
            log('UTILS :: {0:<29} {1}'.format('Actors Found', castFound))
            if castFound == 0:
                log('UTILS :: {0:<29} {1}'.format('Skipping', 'No Actors'))
            elif castFound > castLimit:
                log('UTILS :: {0:<29} {1}'.format('Skipping', '>{0} Cast Names Limit'.format(castLimit)))
            elif castFound <= castLimit:
                log('UTILS :: {0:<29} {1}'.format('Processing', '<={0} Cast Names Limit'.format(castLimit)))

            if castFound == 0 or castFound > castLimit:
                log(LOG_SUBLINE)
                continue            # next unmatchedCast

            log('UTILS :: {0:<29} {1}'.format('Matching Name', unmatchedCast))
            log(LOG_SUBLINE)
            for idx2, cast in enumerate(castList, start=1):
                # get cast details and compare to Agent cast
                try:
                    castName = cast.xpath('./td[2]/a/text()[normalize-space()]')[0]
                    castCompareName = re.sub(r'[\W\d_]', '', castName).strip().lower()
                    log('UTILS :: {0:<29} {1}'.format('Matching Cast Name', '{0:>2}.{1} - {2} / {3}'.format(idx, idx2, castName, castCompareName)))
                except Exception as e:
                    log('UTILS :: Error:: Could not read Cast Name: {0}'.format(e))
                    log(LOG_SUBLINE)
                    continue   # next cast 

                try:
                    castURL = IAFD_BASE + cast.xpath('./td[2]/a/@href')[0]
                    log('UTILS :: {0:<29} {1}'.format('Cast URL', castURL))
                except Exception as e:
                    log('UTILS :: Error:: Could not read Cast URL: {0}'.format(e))
                    log(LOG_SUBLINE)
                    continue   # next cast 

                castAlias = ''
                castAliasList = []
                castCompareAliasList = []
                try:
                    castAliasList = cast.xpath('./td[3]/text()[normalize-space()]')[0].replace(' or ', ',')
                    castAliasList = castAliasList.split(',')
                    castAliasList = [x.strip() for x in castAliasList if x.strip()]
                    castAlias = ', '.join(castAliasList)
                    castCompareAliasList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in castAliasList]
                    log('UTILS :: {0:<29} {1}'.format('Alias', castAliasList if castAliasList else 'No Cast Alias Recorded'))
                except:
                    pass

                startCareer = 0
                endCareer = 0
                try:
                    startCareer = int(cast.xpath('./td[4]/text()[normalize-space()]')[0]) - 1 # set start of career to 1 year before for pre-releases
                    endCareer = int(cast.xpath('./td[5]/text()[normalize-space()]')[0]) + 1   # set end of career to 1 year after to cater for late releases
                    log('UTILS :: {0:<29} {1}'.format('Career', '{0} - {1}'.format(startCareer if startCareer > 0 else 'N/A', endCareer if endCareer > 0 else 'N/A')))
                except:
                    pass

                matchedUsing = ''

                # match iafd row with Agent Cast entry
                matchedUsing = 'Name' if compareUnmatchedCast == castCompareName else ''
                log('UTILS :: {0:<29} {1}'.format('Match Cast Name', '{0} = {1} ?: {2}'.format(compareUnmatchedCast, castCompareName, 'Pass' if matchedUsing == 'Name' else 'Failed')))

                # match iafd row with Agent Cast Alias entry if not matched by name
                check = 'Skipped'
                if not matchedUsing and castAliasList:
                    matchedItem = [x for x in castCompareAliasList if compareUnmatchedCast in x]
                    matchedUsing = 'Alias' if matchedItem else ''
                    check = 'Done'

                log('UTILS :: {0:<29} {1}'.format('Match Cast Alias', '{0} in {1} ?: {2}'.format(compareUnmatchedCast, castCompareAliasList, 'Pass' if matchedUsing == 'Alias' else 'Skipped' if check == 'Skipped' else 'Failed')))

                # Check Career - if we have a year and film is not a compilation
                check = 'Skipped'
                if myYear and FILMDICT['Compilation'] == "No":
                    matchedUsing = 'Career' if (startCareer <= myYear <= endCareer) is True else ''
                    check = 'Done'

                log('UTILS :: {0:<29} {1}'.format('Match Cast Career', '{0} <= {1} <= {2} ?: {3}'.format(startCareer, myYear, endCareer, 'Pass' if matchedUsing == 'Career' else 'Skipped' if check == 'Skipped' else 'Failed')))

                # go to next in list if we fail to match on Name, Alias or Career
                if not matchedUsing:
                    log('UTILS :: {0:<29} {1}'.format('Matching Cast', 'Failed'))
                    log(LOG_SUBLINE)
                    continue

                if FILMDICT['FoundOnIAFD'] == 'Yes':                # look through FILMDICT['Cast']
                    previouslyMatched = False                       # check if the actor is in a film that has been found in IAFD
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

                    if previouslyMatched is True:
                        matchedCastDict.pop(unmatchedCast, None)
                        log('UTILS :: {0:<29} {1}'.format('Skipped Matching Cast', 'Previously Matched on IAFD'))
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
                        log('UTILS :: {0:<29} {1}'.format('Skipped Matching Cast', 'Has not appeared in any {0} Films or only in a Non Sex / Masturbation Roles Only'.format(AGENT_TYPE)))
                        log(LOG_SUBLINE)
                        continue    # next cast in cast list

                    # get cast biography and filmography etc
                    castDetails = {}
                    try:
                        castDetails = copy.deepcopy(getIAFDArtist(AGENTDICT, castURL, chtml))      # provide html so that iafd does not have to be accessed a second time
                        castAwards = castDetails['Awards']
                        castBio = castDetails['Bio']
                        castFilms = castDetails['Films']
                        castNationality = castDetails['Nationality']
                        castPhoto = castDetails['Photo']
                        castRealName = castDetails['RealName']
                        castRole = RIGHT_TICK                                       # default to found

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

                    except:
                        castAwards = []
                        castBio = {}
                        castFilms = []
                        castNationality = ''
                        castPhoto = ''
                        castRealName = ''
                        castRole = ERR403_TICK         # indicate 403 Error when processing cast member - if role not previously set
                        FILMDICT['IAFD403Err'].add('Cast')
                        matchedCastDict[unmatchedCast] = {'Alias': castAliasList, 'Awards': castAwards, 'Bio': castBio, 'CompareName': castCompareName, 'CompareAlias': castCompareAliasList, 
                                                          'Films': castFilms, 'Nationality': castNationality, 'Photo': castPhoto, 'RealName': castRealName, 'Role': castRole, 'URL': castURL}

                except Exception as e:
                    log('UTILS :: Error:: Getting Cast Member Page, {0}: {1}'.format(unmatchedCast, e))
                    log(LOG_SUBLINE)
                    castRole = ERR403_TICK         # indicate 403 Error when processing cast member - if role not previously set
                    FILMDICT['IAFD403Err'].add('Cast')
                    # next cast member in unmatched agent cast list
                    continue

        except Exception as e:
            matchedCastDict[unmatchedCast] = copy.deepcopy(blankCast)
            matchedCastDict[unmatchedCast]['Role'] = ERR403_TICK       # usually due to a 403 Error and assign to dictionary
            FILMDICT['IAFD403Err'].add('Cast')
            log('UTILS :: Error:: Cannot Process IAFD Cast Search Results, {0}: {1}'.format(unmatchedCast, e))
            log(LOG_SUBLINE)

    return matchedCastDict
# ----------------------------------------------------------------------------------------------------------------------------------
def matchDirectors(unmatchedDirectorList, AGENTDICT, FILMDICT):
    ''' check IAFD web site for individual directors'''
    matchedDirectorDict = {}
    directorCompareName = ''
    directorAliasList = []
    directorAwards = []
    directorBio = {}
    directorFilms = []
    directorRealName = ''
    directorNationality = ''
    directorPhoto = AGENTDICT['pgmaNODIRECTORPOSTER']
    directorURL = ''
    blankDirector = {'Alias': directorAliasList, 'Awards': directorAwards, 'Bio': directorBio, 'Films': directorFilms, 
                     'RealName': directorRealName, 'Nationality': directorNationality, 'Photo': directorPhoto, 'URL': directorURL}

    myYear = int(FILMDICT['Year'])
    for idx, unmatchedDirector in enumerate(unmatchedDirectorList, start=1):
        compareUnmatchedDirector = re.sub(r'[\W\d_]', '', unmatchedDirector).strip().lower()
        log('UTILS :: {0:<29} {1}'.format('Unmatched Director Name', '{0:>2} - {1}/{2}'.format(idx, unmatchedDirector, compareUnmatchedDirector)))

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
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Director: Partial Match - Director Name', IAFDCompareName))
                matchedName = True
                break

            # 4th partial match against director alias
            if compareUnmatchedDirector in IAFDCompareAlias:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Director: Partial Match - Director Alias', IAFDCompareAlias))
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
            if matchedName is True:
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
                        if matchedName is True:
                            break
                else:
                    matchedName = levScore <= levDistance

                if matchedName is True:
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
            if matchedName is True:
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
                if matchedName is True:
                    log('UTILS :: {0:<29} {1}'.format('SoundEx Match', testNameType))
                    log('UTILS :: {0:<29} {1}'.format('  IAFD Director Alias', testAlias))
                    log('UTILS :: {0:<29} {1}'.format('  Agent Director Name', unmatchedDirector))
                    log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(soundIAFD, soundAgent)))
                    log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                    break

        if matchedName is True: # we have a match, on to the next director
            log(LOG_SUBLINE)
            continue

        # the director on the website has not matched to those listed against the film in IAFD. So search for the director's entry on IAFD
        matchedDirectorDict[unmatchedDirector] = blankDirector      # initialise director's dictionary

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
                    log('UTILS :: {0:<29} {1}'.format('Matching Director', '{0:>2}.{1} - {2} / {3}'.format(idx, idx2, directorName, directorCompareName)))
                except Exception as e:
                    log('UTILS :: Error:: Could not read Director Name: {0}'.format(e))
                    continue   # next director

                try:
                    directorURL = IAFD_BASE + director.xpath('./td[2]/a/@href')[0]
                    log('UTILS :: {0:<29} {1}'.format('Director URL', directorURL))
                except Exception as e:
                    log('UTILS :: Error:: Could not read Director URL: {0}'.format(e))
                    log(LOG_SUBLINE)
                    continue   # next director

                directorAliasList = []
                directorAlias = ''
                directorCompareAliasList = []
                try:
                    directorAliasList = director.xpath('./td[3]/text()[normalize-space()]')[0].split(',')
                    directorAliasList = [x.strip() for x in directorAliasList if x.strip()]
                    directorAlias = ', '.join(directorAliasList)
                    directorCompareAliasList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in directorAliasList]
                    log('UTILS :: {0:<29} {1}'.format('Alias', directorAliasList if directorAliasList else 'No Director Alias Recorded'))
                except:
                    pass

                startCareer = 0
                endCareer = 0
                try:
                    startCareer = int(director.xpath('./td[4]/text()[normalize-space()]')[0]) # set start of career
                    endCareer = int(director.xpath('./td[5]/text()[normalize-space()]')[0])   # set end of career
                    log('UTILS :: {0:<29} {1}'.format('Career', '{0} - {1}'.format(startCareer if startCareer > 0 else 'N/A', endCareer if endCareer > 0 else 'N/A')))
                except:
                    pass

                matchedUsing = ''

                # match iafd row with Agent Cast entry
                matchedUsing = 'Name' if compareUnmatchedDirector == directorCompareName else ''
                log('UTILS :: {0:<29} {1}'.format('Match Director Name', '{0} = {1} ?: {2}'.format(compareUnmatchedDirector, directorCompareName, 'Pass' if matchedUsing == 'Name' else 'Failed')))

                # match iafd row with Agent Cast Alias entry if not matched by name
                check = 'Skipped'
                if not matchedUsing and directorAliasList:
                    matchedItem = [x for x in directorCompareAliasList if compareUnmatchedDirector in x]
                    matchedUsing = 'Alias' if matchedItem else ''
                    check = 'Done'

                log('UTILS :: {0:<29} {1}'.format('Match Director Alias', '{0} in {1} ?: {2}'.format(compareUnmatchedDirector, directorCompareAliasList, 'Pass' if matchedUsing == 'Alias' else 'Skipped' if check == 'Skipped' else 'Failed')))

                # Check Career - if we have a year and film is not a compilation
                check = 'Skipped'
                if myYear and FILMDICT['Compilation'] == "No":
                    matchedUsing = 'Career' if (startCareer <= myYear <= endCareer) is True else ''
                    check = 'Done'

                log('UTILS :: {0:<29} {1}'.format('Match Director Career', '{0} <= {1} <= {2} ?: {3}'.format(startCareer, myYear, endCareer, 'Pass' if matchedUsing == 'Career' else 'Skipped' if check == 'Skipped' else 'Failed')))

                # go to next in list if we fail to match on Name, Alias or Career
                if not matchedUsing:
                    log('UTILS :: {0:<29} {1}'.format('Matching Director', 'Failed'))
                    log(LOG_SUBLINE)
                    continue

                # now check if any processed IAFD Directors (FILMDICT) have an alias that matches with this director
                # this will only work if the film has directors recorded against it on IAFD
                if FILMDICT['FoundOnIAFD'] == 'Yes':                # look through FILMDICT['Directors']
                    previouslyMatched = False                       # check if the director is in a film that has been found in IAFD
                    for key, value in FILMDICT['Directors'].items():
                        checkName = key
                        if value['URL']:
                            checkURL = value['URL']
                            if directorURL == checkURL:
                                previouslyMatched = True
                                log('UTILS :: {0:<29} {1}'.format('Note', '{0} URL in use: {1}'.format(checkName, checkURL)))
                                break
                        if value['CompareAlias']:
                            checkAlias = value['Alias']
                            checkCompareAlias = value['CompareAlias']
                            if checkCompareAlias in directorCompareAliasList:
                                previouslyMatched = True
                                log('UTILS :: {0:<29} {1}'.format('Note', '{0} AKA {1} also known by this name: {2}'.format(checkName, checkAlias, directorName)))
                                break

                    if previouslyMatched is True:
                        matchedDirectorDict.pop(unmatchedDirector, None)
                        log('UTILS :: {0:<29} {1}'.format('Skipped Matching Director', 'Previously Matched on IAFD'))
                        log(LOG_SUBLINE)
                        continue

                # we have an director who matches the conditions - get director biography and filmography etc
                directorDetails = copy.deepcopy(getIAFDArtist(AGENTDICT, directorURL))
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
                break   # matched - ignore any other entries

        except Exception as e:
            matchedDirectorDict[unmatchedDirector] = copy.deepcopy(blankDirector)
            log('UTILS :: Error:: Cannot Process IAFD Director Search Results, {0}: {1}'.format(unmatchedDirector, e))
            log(LOG_SUBLINE)
            continue    # next director in unmatched agent director list

    return matchedDirectorDict

# -------------------------------------------------------------------------------------------------------------------------------
def matchFilename(AGENTDICT, media):
    ''' Check filename on disk corresponds to regex preference format '''
    if START_SCRAPE == 'No':
        raise Exception('<QUIT: Scraping Parameters Not Set Up!>')

    filmVars = {}
    filmVars['id'] = media.id
    filmVars['Status'] = False          # initial state before Search and Update Routine
    filmVars['SceneAgent'] = False

    # file name
    filmPath = media.items[0].parts[0].file
    filmVars['FileName'] = os.path.splitext(os.path.basename(filmPath))[0]

    # film duration
    try:
        calcDuration = sum([getattr(part, 'duration') for part in media.items[0].parts])
        fileDuration = datetime.fromtimestamp(calcDuration // 1000) # convert miliseconds to seconds

    except:
        fileDuration = datetime.fromtimestamp(0)

    finally:
        filmVars['Duration'] = fileDuration

    # File name matching
    REGEX = '^\((?P<fnSTUDIO>[^()]*)\) - (?P<fnTITLE>.+?)?(?: - \{(?P<fnGEVISCENE>\d{3,6}[LNR])\})?(?: \((?P<fnYEAR>\d{4})\))?( - \[(?P<fnCAST>[^\]]*)\])?(?: - (?i)(?P<fnSTACK>(cd|disc|disk|dvd|part|pt|scene) [1-8]))?$'
    pattern = re.compile(REGEX)
    matched = pattern.search(filmVars['FileName'])
    if not matched:
        raise Exception('< File Name [{0}] not in the expected format: (Studio) - Title [(Year)] [- cd|disc|disk|dvd|part|pt|scene 1..8]! >'.format(filmVars['FileName']))

    groups = matched.groupdict()
    if (groups['fnGEVISCENE'] and AGENT not in ['GEVIScenes', 'IAFD']):         # if fnGEVISCENE only process if GEVIScenes or IAFD
        raise Exception('< File Name [{0}] - GEVI Scene {1} detected: Abort processing! >'.format(filmVars['FileName'], groups['fnGEVISCENE']))
    elif (not groups['fnGEVISCENE'] and AGENT == 'GEVIScenes'):                   # if no fnGEVISCENE abort if GEVIScenes
        raise Exception('< File Name [{0}] - GEVI Scene undetected: Abort processing! >'.format(filmVars['FileName']))

    log('UTILS :: File Name REGEX Matched Variables:')
    log('UTILS :: {0:<29} {1}'.format('    Studio', groups['fnSTUDIO']))
    log('UTILS :: {0:<29} {1}'.format('    Title', groups['fnTITLE']))
    log('UTILS :: {0:<29} {1}'.format('    Year', groups['fnYEAR']))
    log('UTILS :: {0:<29} {1}'.format('    Cast', groups['fnCAST']))
    log('UTILS :: {0:<29} {1}'.format('    Stack', groups['fnSTACK']))
    if groups['fnGEVISCENE']:
        log('UTILS :: {0:<29} {1}'.format('    Scene No.', groups['fnGEVISCENE']))

    log(LOG_SUBLINE)

    #   Studio
    filmVars['RecordedStudios'] = set()
    filmVars['Studio'] = groups['fnSTUDIO'].split(';')[0].strip()
    filmVars['CompareStudio'] = Normalise(makeASCII(filmVars['Studio']))

    #   Title
    filmVars['CompareTitle'] = set()
    filmVars['Title'] = groups['fnTITLE']
    squares = [i for i, char in enumerate(filmVars['Title']) if char == u'²']                   # check for mathematical square character in string
    filmVars['Title'] = filmVars['Title'].replace('~', '/').replace('¬','?')                    # ~ invalid character marker in filename
    tempTitle = filmVars['Title']
    filmVars['Title'] = makeASCII(filmVars['Title'])
    # make ascii casts u'²' as 2 messing up searches
    if squares:
        newTitle = []
        for idx, char in enumerate(tempTitle):
            newTitle.append(u'²' if idx in squares else char)
        filmVars['Title'] = ''.join(newTitle)

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

    # Only used by GEVIScenes Agent    
    # this will always be zero for non-gevscenes
    filmVars['Rotation'] = 0 if not groups['fnGEVISCENE'] else 90 if groups['fnGEVISCENE'][-1] == 'R' else 270 if groups['fnGEVISCENE'][-1] == 'L' else 0
    # remove trailing L, N or R - i.e. rotational instruction
    filmVars['GEVIScene'] = '' if not groups['fnGEVISCENE'] else re.sub(r'[LNR]$', '', groups['fnGEVISCENE'])

    # process Title
    # replace hyphens with colon-space
    filmVars['Title'] = re.sub(ur' - |- ', ': ', filmVars['Title'])

    # strip punctuations at end of string
    pattern = ur'[' + re.escape(''.join(['.', '!', '%', '?'])) + ']+$'
    shortTitle = re.sub(pattern, '', ' '.join(splitFilmTitle).strip())
    filmVars['ShortTitle'] = shortTitle
    filmVars['NormaliseShortTitle'] = Normalise(filmVars['ShortTitle'])
    filmVars['CompareTitle'].add(sortAlphaChars(filmVars['NormaliseShortTitle']))

    # add series individually and wholly + short Title in case episode number left out
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
    filmVars['IAFDTitle'] = filmVars['IAFDTitle'].replace('!', ' ').replace('*', ' ')                   # remove !, *
    filmVars['IAFDTitle'] = ' '.join(filmVars['IAFDTitle'].split())                                     # replace multi-spaces with space

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
    searchString = String.URLEncode(searchString).replace('%25', '%').replace('%26', '&').replace('*', '').replace('%2A', '+')
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
    filmVars['IAFD403Err'] = set()      # No Error 403 detected at start of scrape

    # delete unneeded dictionary keys
    del filmVars['NormaliseIAFDTitle']
    del filmVars['NormaliseTitle']
    del filmVars['ShortTitle']

    # print out dictionary values / normalise unicode
    log('UTILS :: {0:<29} {1}'.format('FilmVars Dictionary:', ''))
    printDictionary(filmVars)

    return filmVars

# ----------------------------------------------------------------------------------------------------------------------------------
def matchDuration(siteDuration, AGENTDICT, FILMDICT, matchAgainstIAFD=False, myAgent=AGENT):
    ''' match file duration against iafd or site as per request'''
    if matchAgainstIAFD is True:
        dx = abs(FILMDICT['IAFDDuration'] - siteDuration).total_seconds()
    else:
        dx = abs(FILMDICT['Duration'] - siteDuration).total_seconds()

    dxmm, dxss = divmod(dx, 60)
    testDuration = 'Passed' if dxmm <= AGENTDICT['prefDURATIONDX'] else 'Failed'
    log('UTILS :: {0:<29} {1}'.format('Match Against IAFD Duration', matchAgainstIAFD))
    log('UTILS :: {0:<29} {1}'.format('{0} Duration'.format(myAgent), siteDuration.strftime('%H:%M:%S')))
    if matchAgainstIAFD:
        log('UTILS :: {0:<29} {1}'.format('IAFD Duration', FILMDICT['IAFDDuration'].strftime('%H:%M:%S')))
    else:
        log('UTILS :: {0:<29} {1}'.format('File Duration', FILMDICT['Duration'].strftime('%H:%M:%S')))
    log('UTILS :: {0:<29} {1}'.format('Delta', '{0} Minutes'.format(int(dxmm))))
    log('UTILS :: {0:<29} {1}'.format('Duration Comparison Test', '{0}{1}'.format('' if AGENTDICT['prefMATCHSITEDURATION'] else 'Ignore: ', testDuration)))

    if testDuration == 'Failed' and AGENTDICT['prefMATCHSITEDURATION'] is True:
        raise Exception('< Duration Match Failure! >')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def matchReleaseDate(siteReleaseDate, FILMDICT, UseTwoYearMatch=False, myAgent=AGENT):
    ''' match file year against website release date: return formatted site date if no error or default to formated file date '''
    # there can not be a difference of more than 366 days between FileName Date and siteReleaseDate
    if FILMDICT['CompareDate'] is None:
        log('UTILS :: {0:<29} {1}'.format('Release Date Matching', 'Skipped: No File Year'))

    else:
        dx = abs((FILMDICT['CompareDate'] - siteReleaseDate).days)
        dxMaximum = 731 if UseTwoYearMatch else 366               # 2 years if matching film year with IAFD and 1 year for Agent
        testReleaseDate = 'Failed' if dx > dxMaximum else 'Passed'

        log('UTILS :: {0:<29} {1}'.format('{0} Release Date'.format(myAgent), siteReleaseDate))
        log('UTILS :: {0:<29} {1}'.format('File Release Date', FILMDICT['CompareDate']))
        log('UTILS :: {0:<29} {1}'.format('Delta in Days', dx))
        log('UTILS :: {0:<29} {1}'.format('Release Date Comparison Test', testReleaseDate))

        if testReleaseDate == 'Failed':
            raise Exception('< Release Date Match Failure! >')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def matchStudio(siteStudio, FILMDICT, myAgent=AGENT):
    ''' match file studio name against website studio/iafd name: Boolean Return '''
    compareSiteStudio = Normalise(siteStudio)
    FILMDICT['CompareSiteStudio'] = compareSiteStudio       #  used later to sort tags in scene agents
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

    log('UTILS :: {0:<29} {1}'.format('{0} Studio'.format(myAgent), siteStudio))
    log('UTILS :: {0:<29} {1}'.format('File Studio', FILMDICT['Studio']))
    log('UTILS :: {0:<29} {1}'.format('IAFD Studio', FILMDICT['IAFDStudio']))
    log('UTILS :: {0:<29} {1}'.format('Compare {0} Studio'.format(myAgent), compareSiteStudio))
    log('UTILS :: {0:<29} {1}'.format('        File Studio', FILMDICT['CompareStudio']))
    log('UTILS :: {0:<29} {1}'.format('        IAFD Studio', FILMDICT['CompareIAFDStudio']))
    log('UTILS :: {0:<29} {1}'.format('Studio Comparison Test', testStudio))

    if testStudio == 'Failed Match':
        raise Exception('< Studio Match Failure! >')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def matchTitle(filmTitle, FILMDICT, myAgent=AGENT):
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
        testTitle = 'Passed' if filmCompareTitle in FILMDICT['CompareTitle'] else 'Failed'

    if testTitle == 'Failed':                   # check if episode  i.e. series + number in agent title
        for item in FILMDICT['Episodes']:
            pattern = re.compile(re.escape(item), re.IGNORECASE)
            if re.search(pattern, filmTitle):  # match against whole string
                testTitle = 'Passed'
                break

    log('UTILS :: {0:<29} {1}'.format('{0} Title'.format(myAgent), filmTitle))
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
def printDictionary(myDictionary, spacesCount=0, subkeyPrintCount=0, prefixCount=''):
    ''' print out dictionary values / normalise unicode'''
    try:
        for idx, (key, value) in enumerate(sorted(myDictionary.items()), start=1):
            myLine = '{0}'.format(prefixCount) + str(idx)
            indent = ' ' * spacesCount if spacesCount > 0 else ''
            if isinstance(value, dict):
                log('UTILS :: {0:<29} {1}'.format('{0}{1}. {2}:'.format(indent, myLine, key), '<Dict>'))
                idx = 0
                printDictionary(value, spacesCount=(spacesCount + 2), subkeyPrintCount=subkeyPrintCount, prefixCount='{0}.'.format(myLine))

            else:
                log('UTILS :: {0:<29} {1}'.format('{0}{1}. {2}'.format(indent, myLine, key), value))
                # only do following on sub-dictionaries...  this will have line counts like 20.2.
                if subkeyPrintCount != 0 and len(myLine.split('.')) > 1 and idx == subkeyPrintCount:
                    log('UTILS :: {0:<29} {1}'.format('{0} + {1} more items'.format(indent, len(myDictionary) - idx), ''))
                    break

    except Exception as e:
        log('UTILS :: Error: Printing Dictionary: {0}'.format(e))

# ----------------------------------------------------------------------------------------------------------------------------------
def updateMetadata(metadata, media, lang, force=True):
    ''' Set Metadata variables with information gleaned from File Name and Agent website stored in FILMDICT. Any failure aborts the process'''
    backupMetadata = metadata
    FILMDICT = {}
    try:
        log(LOG_BIGLINE)
        AGENTDICT = copy.deepcopy(setupAgentVariables(media))
        logHeader('UPDATE', AGENTDICT, media, lang)

        log(LOG_BIGLINE)
        log('UTILS :: Convert Date Time & Set Objects:')
        FILMDICT = json.loads(metadata.id, object_hook=jsonLoader)
        FILMDICT['Status'] = True

        # use general routine to get Metadata
        log(LOG_BIGLINE)
        log('UTILS :: Access Site URL Link')
        try:
            fhtml = HTML.ElementFromURL(FILMDICT['FilmURL'], sleep=delay())
            FILMDICT['FilmHTML'] = fhtml
            if FILMDICT.get('vDuration') is None:
                FILMDICT['vDuration'] = FILMDICT['Duration']
            if FILMDICT.get('vReleaseDate') is None:
                FILMDICT['vReleaseDate'] = FILMDICT['CompareDate']
            if FILMDICT.get('vCompilation') is None:
                FILMDICT['vCompilation'] = FILMDICT['Compilation']

            FILMDICT[AGENT] = getSiteInfo(AGENT, AGENTDICT, FILMDICT, kwCompilation=FILMDICT['vCompilation'], kwReleaseDate=FILMDICT['vReleaseDate'], kwDuration=FILMDICT['vDuration'])
            log(LOG_BIGLINE)
            log('UTILS :: {0:<29} {1}'.format('FILMDICT:', ''))
            printDictionary(FILMDICT)

        except Exception as e:
            log('UTILS :: Error: Accessing Site URL page: {0}'.format(e))
            FILMDICT['Status'] = False

        # we should have a match on studio, title and year now. Find corresponding film on IAFD
        if FILMDICT['Status'] is True:
            log(LOG_BIGLINE)
            log('UTILS :: Check for Film on IAFD')
            try:
                getFilmOnIAFD(AGENTDICT, FILMDICT)
                log(LOG_BIGLINE)

            except: pass

    except Exception as e:
        log('UTILS :: Error: setting up Update Variables: {0}'.format(e))
        FILMDICT['Status'] = False

    if FILMDICT['Status'] is True:
        log(LOG_BIGLINE)
        log('UTILS :: Get Agent Metadata Fields')
        myAgent = FILMDICT.get('Agent', AGENT)
        myAgentDict = FILMDICT.get(myAgent, '')
        if not myAgentDict:
            FILMDICT['Status'] = False

    if FILMDICT['Status'] is True:
        log(LOG_BIGLINE)
        log('UTILS :: 1.  Set Metadata from File Name and Default Settings:')
        log(LOG_SUBLINE)

        # used to create collections that have extra information like cast photos, country flags etc ordered by Sort title
        collectionsDict = {}
        nationalities = set()
        prefix = '{0}{1}'.format(AGENT_TYPE, THIN_SPACE) if AGENTDICT['prefPREFIXGENRE'] is True else ''      # add prefix to genres and genre collections if preferenced
        deathRegex = r'Date of Death|Year of Death|would be'.replace(' ', NOBREAK_SPACE)
        errorCountryArt = os.path.join(AGENTDICT['pgmaCOUNTRYART'], '_Error.png')
        errorCountryPosterFlag = os.path.join(AGENTDICT['pgmaCOUNTRYPOSTERFLAGS'], '_Error.png')

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
            log('UTILS :: Error: setting ID: {0}'.format(e))
            metadata.id = ''
            FILMDICT['Status'] = False

        # 1b.   Set Studio
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                metadata.studio = FILMDICT['Studio']
                log('UTILS :: {0:<29} {1}'.format('1b. Studio', metadata.studio))

            except Exception as e:
                metadata.studio = ''
                log('UTILS :: Error: setting Studio: {0}'.format(e))
                FILMDICT['Status'] = False

        # 1c.   Set Title
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                if AGENT == 'BestExclusivePorn':        # BEP - file name has to be set to lowercase bar Actors Names, so restore
                    metadata.title = " ".join(word.capitalize() if "'s" in word or "'t" in word else word.title() for word in FILMDICT['Title'].split())
                else:
                    metadata.title = FILMDICT['Title']
                log('UTILS :: {0:<29} {1}'.format('1c. Title', metadata.title))

                # Showcase Collection - if "Best of" found in Title
                if AGENTDICT['prefCOLGENRE']:
                    pattern = r'Best Of'
                    matched = re.search(pattern, FILMDICT['Title'], re.IGNORECASE)
                    if matched:
                        item = 'Showcase'
                        entry = '{0} {1}'.format(AGENTDICT['prefCOLGENRE'], item)
                        collectionsDict[entry] = {'Poster': AGENTDICT['pgmaGENRESDICT'][item.lower()], 'Art': '', 'Summary': ''}

            except Exception as e:
                metadata.title = ''
                log('UTILS :: Error: setting Title: {0}'.format(e))
                FILMDICT['Status'] = False

        # 1d.   Set Content Rating to Adult
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                metadata.content_rating = 'X'
                log('UTILS :: {0:<29} {1}'.format('1d. Content Rating', 'X'))

            except Exception as e:
                metadata.content_rating = ''
                log('UTILS :: Error: setting Content Rating: {0}'.format(e))
                FILMDICT['Status'] = False

        # 1e.   Set Content Rating Age to 18 years
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                metadata.content_rating_age = 18
                log('UTILS :: {0:<29} {1}'.format('1e. Content Rating Age', '18'))

            except Exception as e:
                metadata.content_rating_age = 0
                log('UTILS :: Error: setting Content Rating Age: {0}'.format(e))
                FILMDICT['Status'] = False

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
        if FILMDICT['Status'] is True:
            log(LOG_BIGLINE)
            log('UTILS :: 2.  Set Metadata from Scraped Website Resources:')
            log(LOG_SUBLINE)

        # 2a.   Set Original Title
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                metadata.original_title = FILMDICT['FilmAKA']
                log('UTILS :: {0:<29} {1}'.format('2a. Original Title (AKA)', metadata.original_title))

            except Exception as e:
                metadata.original_title = ''
                log('UTILS :: Error: setting Original Title: {0}'.format(e))
                FILMDICT['Status'] = False

        # 2b.   Set Tagline
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                secondURL = ':: {0}'.format(FILMDICT['IAFDFilmURL']) if myAgent != 'IAFD' and FILMDICT['FoundOnIAFD'] == 'Yes' else ''
                metadata.tagline = '{0} {1}'.format(FILMDICT['FilmURL'], secondURL)
                for idx, tag in enumerate(metadata.tagline.split('::'), start=1):
                    log('UTILS :: {0:<29} {1}'.format('2b. Tagline' if idx == 1 else '' , '{0} - {1}'.format(idx, tag.strip())))

            except Exception as e:
                metadata.tagline = ''
                log('UTILS :: Error: setting Tag Line: {0}'.format(e))
                FILMDICT['Status'] = False

        # 2c.   Rating  can be a maximum of 10 - float value
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                metadata.rating = myAgentDict['Rating'] if metadata.rating < myAgentDict['Rating'] else metadata.rating
                log('UTILS :: {0:<29} {1}'.format('2c. Film Rating', metadata.rating))

            except Exception as e:
                metadata.rating = 0.0
                log('UTILS :: Error: setting Rating: {0}'.format(e))
                FILMDICT['Status'] = False

        # 2d.   Genres - retrieved from website and in some case from the synopsis
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
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
                    entry = '{0} {1}{2}'.format(AGENTDICT['prefCOLSYSTEM'], prefix, item) if 'Compilations' in item and AGENTDICT['prefCOLSYSTEM'] else ''
                    entry = '{0} {1}{2}'.format(AGENTDICT['prefCOLGENRE'], prefix, item) if not entry and AGENTDICT['prefCOLGENRE'] else ''
                    if entry:
                        collectionsDict[entry] = {'Poster': AGENTDICT['pgmaGENRESDICT'][item.lower()], 'Art': '', 'Summary': ''}

            except Exception as e:
                metadata.genres.clear()
                log('UTILS :: Error: setting Genres: {0}'.format(e))
                FILMDICT['Status'] = False

        # 2e.   Cast: thumbnails, roles from IAFD. Use IAFD as main Source if film found on IAFD
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                metadata.roles.clear()
                castList = myAgentDict.get('Cast', [])                  # Add Cast from Agent
                log('UTILS :: {0:<29} {1}'.format('2e. Cast', '{0:>2} - {1}'.format(len(castList), sorted(castList))))
                if FILMDICT['FilenameCast']:                        # User has defined the missing cast to be used in filename
                    castList.extend(FILMDICT['FilenameCast'])
                    log('UTILS :: {0:<29} {1}'.format('Cast: From File Name', '{0:>2} - {1}'.format(len(castList), sorted(castList))))

                castList = list(set(castList))
                castDict = getCast(castList, AGENTDICT, FILMDICT)       # process cast names returning a dictionary
                log('UTILS :: {0:<29} {1}'.format('Cast: Add to Metadata', '{0:>2} - {1}'.format(len(castDict), sorted(castDict.keys()))))
                for idx, (castKey, castValue) in enumerate(sorted(castDict.items()), start=1):
                    log(LOG_SUBLINE)
                    log('UTILS :: {0:<29} {1}'.format('Cast Dictionary:', '{0} - {1}'.format(idx, castKey)))
                    printDictionary(castValue)
                    newRole = metadata.roles.new()
                    castEntry = castValue['RealName'] if castValue['RealName'] else castKey.split('(')[0]
                    newRole.name = castEntry
                    newRole.role = castValue['Role']
                    newRole.photo = castValue['Photo']
                    if AGENTDICT['prefCOLCAST']:
                        if castKey == 'Unknown Actor':      # do not create collections for unknown actors...
                            continue

                        # check for user defined photo - this only works if the actor has an entry on IAFD
                        '''
                        if 'nophoto' in newRole.photo:      # actor has no photo but has entry on IAFD
                            castValue['Photo'] = AGENTDICT['pgmaNOCASTPOSTER']
                            if castValue['URL']:       # artiste has no photo but has entry on IAFD, check if there is a photo on disk #### still not fully implemented
                                #   https://www.iafd.com/person.rme/perfid=zakspears/gender=m/zak-spears.htm -> zakspears#zak-spears
                                castPhoto = castValue['URL'].split('perfid=')[1].split('.htm')[0].replace('/gender=m/', '#').replace('/gender=f/', '#')
                                castValue['Photo'] = AGENTDICT['pgmaCASTDICT.get(castPhoto, AGENTDICT['pgmaNOCASTPOSTER'])
                        '''
                        myBioList = []
                        myBioDict = copy.deepcopy(castValue['Bio'])
                        for count, bioKey in enumerate(sorted(myBioDict.keys()), start=1):
                            bioValue = myBioDict[bioKey]
                            bio = '{0}. {1}: {2}'.format(count, bioKey.upper(), bioValue).replace(' ', NOBREAK_SPACE).replace('-', NOBREAK_HYPHEN)
                            myBioList.append('{0}{1} '.format(bio, NOBREAK_SPACE * 3))

                        if castValue['Awards']:
                            myBioList.append('\n{0}{1} '.format('Awards:', NOBREAK_SPACE * 140))
                            myBioList.extend(castValue['Awards'])

                        if castValue['Films']:
                            myBioList.append('\n{0}{1} '.format('Filmography:', NOBREAK_SPACE * 137))
                            myBioList.extend(castValue['Films'])

                        summary = ' '.join(myBioList)

                        entry = '{0} {1}[d]'.format(AGENTDICT['prefCOLCAST'], castEntry) if re.search(deathRegex, summary, re.IGNORECASE) else '{0} {1}'.format(AGENTDICT['prefCOLCAST'], castEntry)
                        myNationality = castValue['Nationality'].split(',')[-1].strip() if castValue['Nationality'] else ''
                        if myNationality:
                            nationalities.add(myNationality)

                        myFlag = os.path.join(AGENTDICT['pgmaCOUNTRYART'], '{0}.png'.format(myNationality)) if myNationality else ''
                        art =  myFlag if os.path.exists(myFlag) else '' if not myFlag else errorCountryArt
                        collectionsDict[entry] = {'Poster': castValue['Photo'], 'Art': art, 'Summary': summary}

            except Exception as e:
                metadata.roles.clear()
                log('UTILS :: Error: setting Cast: {0}'.format(e))
                FILMDICT['Status'] = False

        # 2f.   Directors
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                metadata.directors.clear()
                directorsList = myAgentDict.get('Directors', [])
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('2f. Director(s)'), '{0:>2} - {1}'.format(len(directorsList), sorted(directorsList))))
                directorDict = getDirectors(directorsList, AGENTDICT, FILMDICT)
                log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Director(s): Add to Metadata'), '{0:>2} - {1}'.format(len(directorDict), sorted(directorDict.keys()))))
                for idx, (directorKey, directorValue) in enumerate(sorted(directorDict.items()), start=1):
                    log(LOG_SUBLINE)
                    log('UTILS :: {0:<29} {1}'.format('Director(s) Dictionary:', '{0} - {1}'.format(idx, directorKey)))
                    printDictionary(directorValue)
                    directorEntry = ((directorValue['RealName'] if directorValue['RealName'] else directorKey.split('(')[0]) + ' ').replace(' ', NOBREAK_SPACE)
                    newDirector = metadata.directors.new()
                    # to create unique cast vs direcotr entries - replace all spaces with no-break space and end with it
                    newDirector.name = directorEntry
                    newDirector.photo = directorValue['Photo']
                    if AGENTDICT['prefCOLDIRECTOR']:
                        '''
                        if 'nophoto' in newDirector.photo:
                            directorValue['Photo'] = AGENTDICT['pgmaNOCASTDIRECTOR']
                            if directorValue['URL']:      # artiste has no photo but has entry on IAFD, check if there is a photo on disk #### still not fully implemented
                                #   https://www.iafd.com/person.rme/perfid=zakspears/gender=d/zak-spears.htm -> zakspears#zak-spears
                                directorPhoto = directorValue['URL'].split('perfid=')[1].split('.htm')[0].replace('/gender=d/', '#')
                                directorValue['Photo'] = AGENTDICT['pgmaDIRECTORDICT.get(directorPhoto, AGENTDICT['pgmaNOCASTDIRECTOR'])
                        '''
                        myBioList = []
                        myBioDict = copy.deepcopy(directorValue['Bio'])
                        for count, bioKey in enumerate(sorted(myBioDict.keys()), start=1):
                            bioValue = myBioDict[bioKey]
                            bio = '{0}. {1}: {2}'.format(count, bioKey.upper(), bioValue).replace(' ', NOBREAK_SPACE).replace('-', NOBREAK_HYPHEN)
                            myBioList.append('{0}{1} '.format(bio, NOBREAK_SPACE * 3))

                        if directorValue['Awards']:
                            myBioList.append('\n{0}{1} '.format('Awards:', NOBREAK_SPACE * 140))
                            myBioList.extend(directorValue['Awards'])

                        if directorValue['Films']:
                            myBioList.append('\n{0}{1} '.format('Filmography:', NOBREAK_SPACE * 137))
                            myBioList.extend(directorValue['Films'])

                        summary = ' '.join(myBioList)
                        entry = '{0} {1}[d]'.format(AGENTDICT['prefCOLDIRECTOR'], directorEntry) if re.search(deathRegex, summary, re.IGNORECASE) else '{0} {1}'.format(AGENTDICT['prefCOLDIRECTOR'], directorEntry)
                        myNationality = directorValue['Nationality'].split(',')[-1].strip() if directorValue['Nationality'] else ''
                        if myNationality:
                            nationalities.add(myNationality)

                        myFlag = os.path.join(AGENTDICT['pgmaCOUNTRYART'], '{0}.png'.format(myNationality)) if myNationality else ''
                        art =  myFlag if os.path.exists(myFlag) else '' if not myFlag else errorCountryArt
                        collectionsDict[entry] = {'Poster': directorValue['Photo'], 'Art': art, 'Summary': summary}

            except Exception as e:
                metadata.directors.clear()
                log('UTILS :: Error: setting Director(s): {0}'.format(e))
                FILMDICT['Status'] = False

        # 2g.   Countries
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            countryArt = ''
            countryPoster = ''
            try:
                metadata.countries.clear()
                listCountries = [nationalities, myAgentDict['Countries']]
                if myAgent != 'IAFD' and 'IAFD' in FILMDICT:
                    listCountries.append(FILMDICT['IAFD']['Countries'])

                # at this stage listCountries is a list of 3 sets, do a union
                listCountries = list(set().union(*listCountries))
                listCountries.sort(key = lambda x: x.lower())
                log('UTILS :: {0:<29} {1}'.format('2g. Countries', '{0:>2} - {1}'.format(len(listCountries), listCountries)))
                for idx, item in enumerate(listCountries, start=1):
                    countryArt = os.path.join(AGENTDICT['pgmaCOUNTRYART'], '{0}.png'.format(item))
                    countryArt = countryArt if os.path.exists(countryArt) else errorCountryArt

                    # use map as country posters, if missing use vertical flag of country or error flag if that is also missing
                    flagPoster = os.path.join(AGENTDICT['pgmaCOUNTRYPOSTERFLAGS'], '{0}.png'.format(item))
                    if AGENTDICT['prefCOUNTRYPOSTERTYPE'] == 'Map':
                        mapPoster = os.path.join(AGENTDICT['pgmaCOUNTRYPOSTERMAPS'], '{0}.jpg'.format(item))
                        countryPoster = mapPoster if os.path.exists(mapPoster) else flagPoster if os.path.exists(flagPoster) else errorCountryPosterFlag
                    else:
                        # use vertical flag as poster or error flag if missing
                        countryPoster = flagPoster if os.path.exists(flagPoster) else errorCountryPosterFlag

                    log('UTILS :: {0:<29} {1}'.format('Country' if idx == 1 else '', '{0:>2} - {1}'.format(idx, item)))
                    metadata.countries.add(item)
                    # Process Countries
                    if AGENTDICT['prefCOLCOUNTRY']:
                        entry = '{0} {1}'.format(AGENTDICT['prefCOLCOUNTRY'], item)
                        collectionsDict[entry] = {'Poster': countryPoster, 'Art': countryArt, 'Summary': ''}

            except Exception as e:
                metadata.countries.clear()
                log('UTILS :: Error: setting Countries: {0}'.format(e))
                FILMDICT['Status'] = False

        # 2h.   Posters - Front Cover of DVD
        # There is no working way to reset Posters
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                for key in metadata.posters.keys():
                    del metadata.posters[key]
                    metadata.posters.validate_keys([])

                poster = myAgentDict['Poster']
                log('UTILS :: {0:<29} {1}'.format('2h. Poster Images', poster if poster else 'None Found'))
                image = ''
                imageContent = ''
                for idx, item in enumerate(poster, start=1):
                    image, imageContent = getFilmImages(imageType='Poster', imageLocation=item, whRatio=1.5, sceneAgent=FILMDICT['SceneAgent'], thumborAddress=AGENTDICT['pgmaTHUMBOR'], rotation=FILMDICT['Rotation']) 
                    log('UTILS :: {0:<29} {1}'.format('Poster' if idx == 1 else '', '{0:>2} - {1}'.format(idx, image)))
                    metadata.posters[image] = Proxy.Media(imageContent, sort_order=idx)

                # save poster to disk
                if poster and 'Yes' in AGENTDICT['prefPOSTERSOURCEDOWNLOAD']:
                    idx = 0 if 'Local' in AGENTDICT['prefPOSTERSOURCEDOWNLOAD'] else -1
                    item = poster[idx]
                    extension = item.split('.')[-1].split('?')[0]
                    filename = os.path.splitext(media.items[0].parts[0].file)[0]
                    downloadPoster = '{0}.{1}'.format(filename, extension)
                    PlexSaveFile(downloadPoster, imageContent)

            except Exception as e:
                log('UTILS :: Error: setting Poster: {0}'.format(e))         # do not fail scrape if poster can not be set
                FILMDICT['Status'] = False

        # 2i.   Art - Back Cover of DVD : Determined by user preference
        # There is no working way to reset Art
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                if AGENTDICT['prefUSEBACKGROUNDART'] is True:
                    for key in metadata.art.keys():
                        del metadata.art[key]
                        metadata.art.validate_keys([])

                    art = myAgentDict['Art']
                    log('UTILS :: {0:<29} {1}'.format('2i. Art Images', art if art else 'None Found'))
                    image = ''
                    imageContent = ''
                    for idx, item in enumerate(art, start=1):
                        image, imageContent = getFilmImages(imageType='Art', imageLocation=item, whRatio=1.5, sceneAgent=FILMDICT['SceneAgent'], thumborAddress=AGENTDICT['pgmaTHUMBOR'], rotation=FILMDICT['Rotation']) 
                        log('UTILS :: {0:<29} {1}'.format('Art' if idx == 1 else '', '{0:>2} - {1}'.format(idx, image)))
                        metadata.art[image] = Proxy.Media(imageContent, sort_order=idx)
                else:
                    log('UTILS :: {0:<29} {1}'.format('Art Image', 'Not Set By Preference'))

            except Exception as e:
                log('UTILS :: Error: setting Art: {0}'.format(e))          # do not fail scrape if art can not be set
                FILMDICT['Status'] = False

        # 2j.   Reviews - Put all Scene information as default unless there are none and website has actual reviews
        if FILMDICT['Status'] is True:
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
                        metadata.reviews.clear()
                        for idx, item in enumerate(scenes, start=1):
                            scene = str(idx)
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
                log('UTILS :: Error: setting Reviews: {0}'.format(e))
                FILMDICT['Status'] = False

        # 2k.   Chapters - Put all Chapter Information here
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                chapters = myAgentDict['Chapters']
                log('UTILS :: {0:<29} {1}'.format('2k. Chapters', '{0} - {1}'.format(len(chapters), chapters)))

                if chapters != {}:
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
                log('UTILS :: Error: setting Chapters: {0}'.format(e))
                FILMDICT['Status'] = False

        # 2l.   Summary = Synopsis with IAFD Legend
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            try:
                log('UTILS :: {0:<29} {1}'.format('2l. Summary', ''))
                synopsis = myAgentDict['Synopsis']
                if not synopsis:
                    if 'IAFD' in FILMDICT and FILMDICT['IAFD']['Synopsis']:
                        synopsis = FILMDICT['IAFD']['Synopsis']
                        log('UTILS :: {0:<29} {1}'.format('Website Synopsis Absent', 'Using IAFD Synopsis'))

                # set up the the legend that can be prefixed/suffixed to the film summary
                presentOnIAFDIcon = ERR403_TICK if 'Film' in FILMDICT['IAFD403Err'] else IAFD_THUMBSUP if FILMDICT['FoundOnIAFD'] == 'Yes' else IAFD_THUMBSDOWN
                presentOnIAFD = '{0} IAFD Film {1}{2}'.format(DOUBLE_GREATER, presentOnIAFDIcon, EM_SPACE)
                actorOnIAFD = '{0} IAFD Cast {1} Yes / {2} No{3}'.format(DOUBLE_GREATER, RIGHT_TICK, WRONG_TICK, EM_SPACE)
                FILMDICT['IAFD403Err'] = ', '.join(sorted(FILMDICT['IAFD403Err'], reverse=True)) if FILMDICT['IAFD403Err'] else ''
                error403OnIAFD = '{0} IAFD Error 403 {1}{2}{3}'.format(DOUBLE_GREATER, ERR403_TICK, FILMDICT['IAFD403Err'], EM_SPACE) if FILMDICT['IAFD403Err'] else ''
                agentName = u'{0} {1}{2}'.format(DOUBLE_GREATER, FILMDICT['Agent'], EM_SPACE)
                stackedStatus = '{0} Stacked {1}'.format(DOUBLE_GREATER, STACKED) if FILMDICT['Stacked'] == 'Yes' else ''
                legend = '{0}{1}{2}{3}{4}'.format(presentOnIAFD, actorOnIAFD, error403OnIAFD, agentName, stackedStatus)

                # translate if synopsis not in library language
                synopsis = TranslateString(synopsis, SITE_LANGUAGE, FILMDICT['lang'], AGENTDICT['prefDETECT'])

                # combine and update
                summary = ('{0}\n{1}' if AGENTDICT['prefPREFIXLEGEND'] is True else '{1}\n{0}').format(legend, synopsis.strip())
                summary = summary.replace('\n\n', '\n')
                WrapText('Summary with Legend', summary)
                metadata.summary = summary

            except Exception as e:
                synopsis = ' '
                log('UTILS :: Error: setting Synopsis: {0}'.format(e))
                FILMDICT['Status'] = False

        # 2m.   Set Collection
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            log('UTILS :: {0:<29} {1}'.format('2m. Collate Collections', ''))
            try:
                studio = FILMDICT['Studio']
                if AGENTDICT['prefCOLSERIES']:
                    # Process Agent Website Series
                    try:
                        if myAgentDict['Collections']:
                            websiteCollectionList = myAgentDict['Collections']
                            for idx, item in enumerate(websiteCollectionList, start=1):
                                entry = '{0} {1}: {2}'.format(AGENTDICT['prefCOLSTUDIO'] if AGENTDICT['prefCOLSTUDIO'] else AGENTDICT['prefCOLSERIES'], studio, item)
                                collectionsDict[entry] = {'Poster': '', 'Art': countryArt, 'Summary': ''}
                    except Exception as e:
                        log('UTILS :: Error: Collating Website Series Collections: {0}'.format(e))
                        FILMDICT['Status'] = False

                    # Process Series from File Name
                    if FILMDICT['Status'] is True:
                        try:
                            seriesList = FILMDICT['Series']
                            for idx, item in enumerate(seriesList, start=1):
                                item = item if AGENT != 'BestExclusivePorn' else " ".join(word.capitalize() if "'s" in word or "'t" in word else word.title() for word in item.split())
                                entry = '{0} {1}: {2}'.format(AGENTDICT['prefCOLSTUDIO'] if AGENTDICT['prefCOLSTUDIO'] else AGENTDICT['prefCOLSERIES'], studio, item)
                                collectionsDict[entry] = {'Poster': '', 'Art': countryArt, 'Summary': ''}

                        except Exception as e:
                            log('UTILS :: Error: Collating Derived Series Collections: {0}'.format(e))
                            FILMDICT['Status'] = False

                # Process Studio Name:
                if FILMDICT['Status'] is True:
                    if AGENTDICT['prefCOLSTUDIO']:
                        entry = '{0} {1}'.format(AGENTDICT['prefCOLSTUDIO'], studio)
                        collectionsDict[entry] = {'Poster': '', 'Art': countryArt, 'Summary': ''}

                # System Collections
                if FILMDICT['Status'] is True:
                    if AGENTDICT['prefCOLSYSTEM']:
                        try:
                            # Special Collections - Should appear in Library before all other Collections, but only if system preference selected
                            # 0.0 - IAFD 403 Error Collection
                            if FILMDICT['IAFD403Err']:
                                entry = '|0.0| IAFD 403 Error'
                                collectionsDict[entry] = {'Poster': AGENTDICT['pgmaIAFD403POSTER'], 
                                                          'Art': AGENTDICT['pgmaIAFD403POSTER'], 
                                                          'Summary': ''}

                            # 0.1/0.2 - IAFD : On or Not On - Collection
                            entry = '|0.1| On-IAFD' if FILMDICT['FoundOnIAFD'] == 'Yes' else '|0.2| Not On-IAFD'
                            collectionsDict[entry] = {'Poster': AGENTDICT['pgmaIAFDFOUNDPOSTER'] if FILMDICT['FoundOnIAFD'] == 'Yes' else AGENTDICT['pgmaIAFDNOTFOUNDPOSTER'], 
                                                      'Art': AGENTDICT['pgmaIAFDFOUNDPOSTER'] if FILMDICT['FoundOnIAFD'] == 'Yes' else AGENTDICT['pgmaIAFDNOTFOUNDPOSTER'], 
                                                      'Summary': ''}


                            # 0.3/0.4 - stacked or Not Stacked Collection
                            entry = '|0.3| Not Stacked' if FILMDICT['Stacked'] == 'No' else '|0.4| Stacked'
                            collectionsDict[entry] = {'Poster': AGENTDICT['pgmaSTACKEDPOSTER'] if FILMDICT['Stacked'] == 'Yes' else AGENTDICT['pgmaNOTSTACKEDPOSTER'], 
                                                      'Art': AGENTDICT['pgmaSTACKEDPOSTER'] if FILMDICT['Stacked'] == 'Yes' else AGENTDICT['pgmaNOTSTACKEDPOSTER'], 
                                                      'Summary': ''}

                            # 0.5 - Compilation Collection
                            if FILMDICT['Compilation'] == 'Yes':
                                entry = '|0.5| Compilations'
                                collectionsDict[entry] = {'Poster': AGENTDICT['pgmaCOMPILATIONSPOSTER'], 
                                                          'Art': AGENTDICT['pgmaCOMPILATIONSPOSTER'], 
                                                          'Summary': ''}

                            # Agent Collections
                            entry = '{0} {1}'.format(AGENTDICT['prefCOLSYSTEM'], myAgent)
                            collectionsDict[entry] = {'Poster': AGENTDICT['pgmaAGENTPOSTER'], 
                                                      'Art': '', 
                                                      'Summary': ''}

                        except Exception as e:
                            log('UTILS :: Error: Collating System Collections: {0}'.format(e))
                            FILMDICT['Status'] = False

                log('UTILS :: {0: <29} {1}'.format('Collections', '{0} Collated - {1}'.format(len(collectionsDict), sorted(collectionsDict.keys()))))

            except Exception as e:
                log('UTILS :: Error: collating Collections: {0}'.format(e))
                FILMDICT['Status'] = False

        # Add to Metadata
        if FILMDICT['Status'] is True:
            log(LOG_SUBLINE)
            metadata.collections.clear()

            log(LOG_SUBLINE)
            try:
                for idx, (collectionsKey, collectionsValue) in enumerate(sorted(collectionsDict.items()), start=1):
                    log('UTILS :: {0:<29} {1}'.format('Collection', '{0:>2} - {1}'.format(idx, collectionsKey)))
                    if not collectionsValue:
                        continue

                    # create collection title - depending on type of collection i.e. Cast, Director, Studio, Series - replace standard spaces with alternate spaces
                    try:
                        pattern2 = NOBREAK_SPACE if AGENTDICT['prefCOLDIRECTOR'] in collectionsKey else EN_SPACE if AGENTDICT['prefCOLSTUDIO'] in collectionsKey or AGENTDICT['prefCOLSERIES'] in collectionsKey else ' '
                        pattern1 = '\s\[d\]|\|\d\|\s|\|\d.\d\|\s'     # remove | number | pattern and death markers
                        title = re.sub(pattern1, '', collectionsKey).strip()
                        title = re.sub(' ', pattern2, title).strip()
                        title = '{0}{1}'.format(title, pattern2).strip()
                        log('UTILS :: {0:<29} {1}'.format('Collection Title', title))
                        metadata.collections.add(title)

                    except Exception as e:
                        log('UTILS :: Error: Creating Collection {0}'.format(e))
                        FILMDICT['Status'] = False
                        break

                    # get rating key if collection exists else create
                    if FILMDICT['Status'] is True:
                        try:
                            ratingKey = ''
                            createdRatingKey = False
                            plexBaseURL = 'http://127.0.0.1:32400'
                            ssn = AGENTDICT['pgmaSSN']
                            collections = ssn.get('{0}/library/sections/{1}/collections'.format(plexBaseURL, AGENTDICT['pgmaLIBRARYID'])).json()['MediaContainer'].get('Metadata',[])
                            for collection in collections:
                                if title == collection.get('title'):
                                    ratingKey = collection.get("ratingKey", '')
                                    break   #collection in collections:
                            else:
                                data = '{0}/library/collections'.format(plexBaseURL)
                                uri = 'server://{0}/com.plexapp.plugins.library/library/metadata/'.format(AGENTDICT['pgmaMACHINEID'])
                                parameters = {'title': title, 'smart': '0', 'sectionId': AGENTDICT['pgmaLIBRARYID'], 'type': 1, 'uri': uri}
                                r = ssn.post(data, params=parameters)
                                ratingKey = r.json()['MediaContainer']['Metadata'][0]['ratingKey']
                                createdRatingKey = True

                            if not ratingKey:
                                raise Exception('< Could Not Determine Collection Rating Key! >')
                            else:
                                log('UTILS :: {0:<29} {1}'.format('{0} Rating Key'.format('Created' if createdRatingKey else 'Found'), ratingKey))

                        except Exception as e:
                            log('UTILS :: Error: Establishing Enhanced Collection Rating Key {0}'.format(e))
                            FILMDICT['Status'] = False
                            break

                    #   Set Collection Sort Title: from collectionsKey string
                    if FILMDICT['Status'] is True:
                        try:
                            titleSort = collectionsKey.replace('[d]', '')                                       # remove death marker
                            log('UTILS :: {0:<29} {1}'.format('Sort Title:', titleSort))
                            payload = {'type': 18, 'id': ratingKey}
                            payload['titleSort.value'] = titleSort
                            payload['titleSort.locked'] = 1
                            ssn.put('{0}/library/sections/{1}/all'.format(plexBaseURL, AGENTDICT['pgmaLIBRARYID']), params=payload)

                        except Exception as e:
                            log('UTILS :: Error: setting Collection Sort Title: {0}'.format(e))
                            FILMDICT['Status'] = False
                            break

                    #   Set Collection Poster
                    if FILMDICT['Status'] is True:
                        try:
                            posterLocation = collectionsValue['Poster']
                            log('UTILS :: {0:<29} {1}'.format('Poster:', posterLocation if posterLocation else 'No Poster'))
                            if posterLocation:
                                data = getImageContent(posterLocation, 'Poster', collectionsKey, AGENTDICT)
                                ssn.post('{0}/library/collections/{1}/posters'.format(plexBaseURL, ratingKey), data=data, stream=True)

                        except Exception as e:
                            log('UTILS :: Error: setting Collection Poster: {0}'.format(e))
                            FILMDICT['Status'] = False
                            break

                    #   Set Collection Art
                    if FILMDICT['Status'] is True:
                        try:
                            artLocation = collectionsValue['Art']
                            log('UTILS :: {0:<29} {1}'.format('Art:', artLocation if artLocation else 'No Art'))
                            if artLocation:
                                data = getImageContent(artLocation, 'Art', collectionsKey, AGENTDICT)                 #data = ssn.get(art).content
                                ssn.post('{0}/library/collections/{1}/arts'.format(plexBaseURL, ratingKey), data=data, stream=True)

                        except Exception as e:
                            log('UTILS :: Error: setting Collection Art: {0}'.format(e))
                            FILMDICT['Status'] = False
                            break

                    #   Set Collection Summary: None set for Genres
                    if FILMDICT['Status'] is True:
                        try:
                            summary = collectionsValue['Summary']
                            if summary:
                                payload = {'type': 18, 'id': ratingKey}
                                payload['summary.value'] = summary
                                payload['summary.locked'] = 1
                                ssn.put('{0}/library/sections/{1}/all'.format(plexBaseURL, AGENTDICT['pgmaLIBRARYID']), params=payload)
                                summaryList = [x.strip() for x in summary.split(' ') if x.strip()]
                                for idx2, summaryLine in enumerate(summaryList, start=1):
                                    log('UTILS :: {0:<29} {1}'.format('Summary:' if idx2 == 1 else '', summaryLine.encode('utf-8').strip()))
                            else:
                                log('UTILS :: {0:<29} {1}'.format('Summary:', 'No Summary'))

                        except Exception as e:
                            log('UTILS :: Error: setting Collection Summary: {0}'.format(e))
                            FILMDICT['Status'] = False
                            break

                    log(LOG_SUBLINE)

            except Exception as e:
                log('UTILS :: Error: setting Collections: {0}'.format(e))
                FILMDICT['Status'] = False

        # 2o.   Set Originally Available Date - From website's release date if only it is earlier in the same year
        if FILMDICT['Status'] is True:
            log(LOG_BIGLINE)
            try:
                log('UTILS :: {0:<29} {1}'.format('2o. Originally Available Date', ''))
                releaseDate = myAgentDict['ReleaseDate']
                log('UTILS :: {0:<29} {1}'.format('Agent Date', releaseDate.date()))

                metadata.originally_available_at = releaseDate
                metadata.year = metadata.originally_available_at.year
                log('UTILS :: {0:<29} {1}'.format('Current Date', metadata.originally_available_at))
                log('UTILS :: {0:<29} {1}'.format('Current Year', metadata.year))

            except Exception as e:
                log('UTILS :: Error: setting Originally Available Date: {0}'.format(e))
                FILMDICT['Status'] = False

    # initialise all metadata if failed
    if FILMDICT['Status'] is False:
        metadata = backupMetadata

    logFooter('UPDATE', FILMDICT)

    # free up memomory
    AGENTDICT = None
    FILMDICT = None

# ----------------------------------------------------------------------------------------------------------------------------------
def setupAgentVariables(media):
    ''' used by start routine to set up Tidy Genres, Countries List and Show Preference Settings'''
    START_SCRAPE = 'No'

    log(LOG_ASTLINE)
    log(LOG_ASTLINE)
    #   1.    Plex Support Path and Preferences
    log('UTILS :: 1.\tPlex System')
    log('UTILS :: {0:<29} {1}'.format('\tAgent', '{0} v.{1}'.format(AGENT, VERSION_NO)))
    log('UTILS :: {0:<29} {1}'.format('\tUtility Update Date', '{0}'.format(UTILS_UPDATE)))
    log('UTILS :: {0:<29} {1}'.format('\tPython', '{0} - {1} - {2}'.format(platform.python_version(), platform.architecture()[0], platform.python_build())))
    log('UTILS :: {0:<29} {1}'.format('\tOperating System', platform.system()))
    log('UTILS :: {0:<29} {1}'.format('\tRelease:', platform.release()))
    log('UTILS :: {0:<29} {1}'.format('\tPlex Support Path', PlexSupportPath))
    log('UTILS :: {0:<29} {1}'.format('\tUser Agent', HTTP.Headers['User-Agent']))
    continueSetup = os.path.isdir(PlexSupportPath) 

    #   2.    Agent Preference Settings
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('UTILS :: 2.\tAgent Preference Settings')
        log('UTILS :: {0:<29} {1}'.format('\tAgent Type', AGENT_TYPE))
        defaultPrefs_json = os.path.join(PlexSupportPath, 'Plug-ins', '{0}.bundle'.format(AGENT), 'Contents', 'DefaultPrefs.json')
        log('UTILS :: {0:<29} {1}'.format('\tDefault Preferences', defaultPrefs_json))
        if os.path.isfile(defaultPrefs_json):
            try:
                json = JSON.ObjectFromString(PlexLoadFile(defaultPrefs_json), encoding=None)  ### Load 'DefaultPrefs.json' to have access to default settings ###
                if not json:
                    raise Exception('< Could Not Read Default Prefs! >')

                log('UTILS :: {0:<29} {1}'.format('\tLoaded', defaultPrefs_json))
                log('UTILS :: {0:<29} {1}'.format('\tPreferences:', len(json)))
                idx = 0
                for entry in json:                   #Build Pref_list dict from json file
                    idx += 1
                    prefName =  entry['id']
                    defSet =  entry['default']
                    if prefName == 'plextoken':              # hide token in logs
                        continue
                    elif defSet in ['true', 'false']:        # Boolean preference
                        setAs = 'true' if Prefs[prefName] == 1 else 'false'
                    else:
                        setAs = Prefs[prefName]

                    log('UTILS :: {0:<29} {1}'.format('\t{0:>2}. {1}'.format(idx, prefName), 'Default = {0:<15} Set As = {1:<15} {2}'.format(defSet, setAs, WRONG_TICK if setAs is None else RIGHT_TICK)))

                prefCOLSYSTEM = '|1|' if Prefs['systemcollection'] else ''
                prefCOLGENRE = '|2|' if Prefs['genrecollection'] != 'No' else ''        # if a colour set is chose - genre collection is on
                prefCOLCOUNTRY = '|3|' if Prefs['countrycollection'] else ''
                prefCOLSTUDIO = '|4|' if Prefs['studiocollection'] else ''
                prefCOLSERIES = '|5|' if Prefs['seriescollection'] else ''
                prefCOLDIRECTOR = '|6|' if Prefs['directorcollection'] else ''
                prefCOLCAST = '|7|' if Prefs['castcollection'] else ''

                # Other Preferences
                prefCOUNTRYPOSTERTYPE = Prefs['countrypostertype']        # show poster as map or vertical flag
                prefDETECT = Prefs['detect']                              # detect the language the summary appears in on the web page
                prefDURATIONDX = int(Prefs['durationdx'])                 # Acceptable difference between actual duration of video file and that on agent website
                prefPLEXTOKEN = Prefs['plextoken']                        # Preferences, plex token
                prefPREFIXGENRE = Prefs['prefixgenre']                    # prefix genres with agent sexuality type - useful for mixed content plex servers
                prefMATCHIAFDDURATION = Prefs['matchiafdduration']        # Match against IAFD Duration value
                prefMATCHSITEDURATION = Prefs['matchsiteduration']        # Match against Site Duration value
                prefPOSTERSOURCEDOWNLOAD = Prefs['postersourcedownload']  # Down film poster to disk, (renamed as film title + image extension)
                prefPREFIXLEGEND = Prefs['prefixlegend']                  # place cast legend at start of summary or end
                prefUSEBACKGROUNDART = Prefs['usebackgroundart']          # Use background art

            except Exception as e:
                log('UTILS :: Error: Loading Default Preferences File: {0}'.format(e))
                continueSetup = False

    #   3. PGMA - Folder Location, where all general files needed for the PGMA Agents are stored, like posters, gayTidy, Countries et cetera
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('UTILS :: 3.\tPGMA Usage Folder Locations')
        pgmaFOLDER = os.path.join(PlexSupportPath, 'Plug-ins', '_PGMA')
        pgmaCASTFACEFOLDER = os.path.join(pgmaFOLDER, 'Cast', 'Face')
        pgmaCASTPOSTERFOLDER = os.path.join(pgmaFOLDER, 'Cast', 'Poster')
        pgmaCOUNTRYART = os.path.join(pgmaFOLDER, 'Country', 'Art')
        pgmaCOUNTRYPOSTERFLAGS = os.path.join(pgmaFOLDER, 'Country', 'Poster', 'Flags')
        pgmaCOUNTRYPOSTERMAPS = os.path.join(pgmaFOLDER, 'Country', 'Poster', 'Maps')
        pgmaDIRECTORFACEFOLDER = os.path.join(pgmaFOLDER, 'Director', 'Face')
        pgmaDIRECTORPOSTERFOLDER = os.path.join(pgmaFOLDER, 'Director', 'Poster')
        pgmaGENREFOLDER = os.path.join(pgmaFOLDER, 'Genre', Prefs['genrecollection']) if Prefs['genrecollection'] != 'No' else os.path.join(pgmaFOLDER, 'Genre')
        pgmaSCRIPTSFOLDER = os.path.join(pgmaFOLDER, 'Scripts')
        pgmaSYSTEMFOLDER = os.path.join(pgmaFOLDER, 'System')

        pgmaFOLDER = pgmaFOLDER if os.path.isdir(pgmaFOLDER) else ''
        pgmaCASTFACEFOLDER = pgmaCASTFACEFOLDER if os.path.isdir(pgmaCASTFACEFOLDER) else ''
        pgmaCASTPOSTERFOLDER = pgmaCASTPOSTERFOLDER if os.path.isdir(pgmaCASTPOSTERFOLDER) else ''
        pgmaCOUNTRYART = pgmaCOUNTRYART if os.path.isdir(pgmaCOUNTRYART) else ''
        pgmaCOUNTRYPOSTERFLAGS = pgmaCOUNTRYPOSTERFLAGS if os.path.isdir(pgmaCOUNTRYPOSTERFLAGS) else ''
        pgmaCOUNTRYPOSTERMAPS = pgmaCOUNTRYPOSTERMAPS if os.path.isdir(pgmaCOUNTRYPOSTERMAPS) else ''
        pgmaDIRECTORPOSTERFOLDER = pgmaDIRECTORPOSTERFOLDER if os.path.isdir(pgmaDIRECTORPOSTERFOLDER) else ''
        pgmaDIRECTORFACEFOLDER = pgmaDIRECTORFACEFOLDER if os.path.isdir(pgmaDIRECTORFACEFOLDER) else ''
        pgmaGENREFOLDER = pgmaGENREFOLDER if os.path.isdir(pgmaGENREFOLDER) else ''
        pgmaSCRIPTSFOLDER = pgmaSCRIPTSFOLDER if os.path.isdir(pgmaSCRIPTSFOLDER) else ''
        pgmaSYSTEMFOLDER = pgmaSYSTEMFOLDER if os.path.isdir(pgmaSYSTEMFOLDER) else ''

        log('UTILS :: {0:<29} {1}'.format('\tPGMA Folder Location', pgmaFOLDER if pgmaFOLDER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\t          Cast Faces', pgmaCASTFACEFOLDER if pgmaCASTFACEFOLDER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\t        Cast Posters', pgmaCASTPOSTERFOLDER if pgmaCASTPOSTERFOLDER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\t         Country Art', pgmaCOUNTRYART if pgmaCOUNTRYART else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\tCountry Poster Flags', pgmaCOUNTRYPOSTERFLAGS if pgmaCOUNTRYPOSTERFLAGS else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\t Country Poster Maps', pgmaCOUNTRYPOSTERMAPS if pgmaCOUNTRYPOSTERMAPS else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\t      Director Faces', pgmaDIRECTORFACEFOLDER if pgmaDIRECTORFACEFOLDER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\t    Director Posters', pgmaDIRECTORPOSTERFOLDER if pgmaDIRECTORPOSTERFOLDER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\t              Genres', pgmaGENREFOLDER if pgmaGENREFOLDER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\t             Scripts', pgmaSCRIPTSFOLDER if pgmaSCRIPTSFOLDER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\t              System', pgmaSYSTEMFOLDER if pgmaSYSTEMFOLDER else WRONG_TICK))

        # only contunue with setup if all folders are present
        continueSetup = (bool(pgmaFOLDER) and bool(pgmaSCRIPTSFOLDER) and bool(pgmaSYSTEMFOLDER) and bool(pgmaCASTFACEFOLDER) and bool(pgmaDIRECTORFACEFOLDER) and bool(pgmaCASTPOSTERFOLDER) and 
                         bool(pgmaDIRECTORPOSTERFOLDER) and bool(pgmaCOUNTRYART) and bool(pgmaCOUNTRYPOSTERFLAGS) and bool(pgmaCOUNTRYPOSTERMAPS) and bool(pgmaGENREFOLDER))

    #   4. PGMA - On disk Cast and Director Collection Posters
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('UTILS :: 4.\tPGMA Cast and Director Collection Poster Dictionaries')
        pgmaCASTDICT = {}
        pgmaDIRECTORDICT = {}
        try:
            pgmaCASTDICT = {x.rsplit('.', 1)[0]:os.path.join(pgmaCASTPOSTERFOLDER, x) for x in os.listdir(pgmaCASTPOSTERFOLDER)}
            log('UTILS :: {0:<29} {1}'.format('\tCast Collection Posters', '{0:>4} - {1}'.format(len(pgmaCASTDICT), pgmaCASTDICT)))

            pgmaDIRECTORDICT = {x.rsplit('.', 1)[0]:os.path.join(pgmaDIRECTORPOSTERFOLDER, x) for x in os.listdir(pgmaDIRECTORPOSTERFOLDER)}
            log('UTILS :: {0:<29} {1}'.format('\tDirector Collection Posters', '{0:>4} - {1}'.format(len(pgmaDIRECTORDICT), pgmaDIRECTORDICT)))

        except Exception as e:
            log('UTILS :: Error: creating Local Cast and Director Collection Poster Dictionaries: {0}'.format(e))
            continueSetup = False

    #   5. Country Dictionary: create dictionary containing countries and flag urls from Country.txt located in plugins code directory
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('UTILS :: 5.\tPrepare Dictionary of Country Names and Flags')
        pgmaCOUNTRYSET = set() 
        try:
            countries_txt = os.path.join(pgmaFOLDER, 'Countries.txt')
            txtfile = PlexLoadFile(countries_txt)
            txtrows = txtfile.split('\n')
            for idx, row in enumerate(txtrows, start=1):
                pgmaCOUNTRYSET.add(row.strip())

            log('UTILS :: {0:<29} {1}'.format('\tCountry Dictionary', '{0:>4} - {1}'.format(len(pgmaCOUNTRYSET), sorted(pgmaCOUNTRYSET))))

        except Exception as e:
            log('UTILS :: Error: creating Country Dictionary: {0}'.format(e))
            log('UTILS :: Error:: Country Source File: {0}'.format(countries_txt))
            continueSetup = False

    #   6. Genres Dictionary: create dictionary containing genres and image urls from Genres.txt located in plugins code directory
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('UTILS :: 6.\tPrepare Dictionary of Genres and Symbols')
        pgmaGENRESDICT = {}
        try:
            genreFiles = ['Genres.txt', 'UserGenres.txt']
            genres_txt = ''
            log('UTILS :: {0:<29} {1}'.format('\tTidy Files', genreFiles))
            for genreFile in genreFiles:
                genres_txt = os.path.join(pgmaFOLDER, genreFile)
                if not os.path.isfile(genres_txt):        # skip files that are missing
                    continue

                txtfile = PlexLoadFile(genres_txt)
                txtrows = txtfile.split('\n')
                for idx, row in enumerate(txtrows, start=1):
                    if '::' not in row:
                        log('UTILS :: {0:<29} {1}'.format('\tInvalid Format Row', 'Row {0} - {1}'.format(idx, row)))
                        continue

                    keyValue = row.split('::')
                    keyValue = [x.strip() for x in keyValue]
                    key =  keyValue[0].lower()

                    if key in pgmaGENRESDICT:
                        log('UTILS :: {0:<29} {1}'.format('\t\t{0}: Duplicate Row - Replace Setting'.format(genreFile), 'Row {0} - {1}'.format(idx, row)))

                    value = os.path.join(pgmaGENREFOLDER, keyValue[1])
                    pgmaGENRESDICT[key] = value

            log('UTILS :: {0:<29} {1}'.format('\tGenres Dictionary', '{0:>4} - {1}'.format(len(pgmaGENRESDICT), sorted(pgmaGENRESDICT))))

        except Exception as e:
            log('UTILS :: Error: creating Genres Dictionary: {0}'.format(e))
            log('UTILS :: Error:: Genres Source File: {0}'.format(genres_txt))
            continueSetup = False

    #   7.     Tidy Genres: create dictionary containing the tidy genres from genres.txt file located in plugins code directory
    #                       unless second field is an 'x', it should appear in the pgmaCOUNTRYSET or pgmaGENRESDICT
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('UTILS :: 7.\tPrepare Tidied Dictionary of Genres and Countries')
        pgmaTIDYDICT = {}
        tidiedCountriesSet = set()                              # used for debugging
        tidiedGenresSet = set()                                 # used for debugging
        tidiedNullSet = set()                                   # used for debugging
        tidiedErrorSet = set()                                  # used for debugging
        try:
            # Main Tidy has to be first in list as user can make changes
            tidyFiles = ['GayTidy.txt', 'UserGayTidy.txt'] if AGENT_TYPE == '⚣' else ['StraightTidy.txt', 'UserStraightTidy.txt']
            tidy_txt = ''
            log('UTILS :: {0:<29} {1}'.format('\tTidy Files', tidyFiles))
            for tidy in tidyFiles:
                tidy_txt = os.path.join(pgmaFOLDER, tidy)
                if not os.path.isfile(tidy_txt):        # skip files that are missing
                    continue

                txtfile = PlexLoadFile(tidy_txt)
                txtrows = txtfile.split('\n')
                for idx, row in enumerate(txtrows, start=1):
                    if '::' not in row:
                        log('UTILS :: {0:<29} {1}'.format('\t\t{0}: Invalid Format Row'.format(tidy), 'Row {0} - {1}'.format(idx, row)))
                        continue

                    keyValue = row.split('::')
                    keyValue = [x.strip() for x in keyValue]
                    key = keyValue[0].lower()
                    value = keyValue[1]
                    if key in pgmaTIDYDICT:
                        log('UTILS :: {0:<29} {1}'.format('\t\t{0}: Duplicate Row - Replace Setting'.format(tidy), 'Row {0} - {1}'.format(idx, row)))

                    pgmaTIDYDICT[key] = value if value != 'x' else None
                    # The value must either be related to a Country, Genre or skipped otherwise its an error which is logged
                    if value in pgmaCOUNTRYSET:
                        tidiedCountriesSet.add('{0} : {1}'.format(keyValue[0], value))
                    elif value.lower() in pgmaGENRESDICT:
                        tidiedGenresSet.add('{0} : {1}'.format(keyValue[0], value))
                    elif value == 'x':
                        tidiedNullSet.add('{0} : {1}'.format(keyValue[0], value))
                    else:
                        log('UTILS :: {0:<29} {1}'.format('\t\t{0}: Not Found in Genres.txt'.format(tidy), 'Row {0} - {1}'.format(idx, row)))
                        tidiedErrorSet.add('{0} : {1}'.format(keyValue[0], value))

            log('UTILS :: {0:<29} {1}'.format('\tOriginal Categories', '{0:>4} - {1}'.format(len(pgmaTIDYDICT), sorted(pgmaTIDYDICT.keys()))))
            log('UTILS :: {0:<29} {1}'.format('\tTidied Countries', '{0:>4} - {1}'.format(len(tidiedCountriesSet), sorted(tidiedCountriesSet))))
            log('UTILS :: {0:<29} {1}'.format('\tTidied Genres', '{0:>4} - {1}'.format(len(tidiedGenresSet), sorted(tidiedGenresSet))))
            log('UTILS :: {0:<29} {1}'.format('\tEmpty Categories', '{0:>4} - {1}'.format(len(tidiedNullSet), sorted(tidiedNullSet))))
            log('UTILS :: {0:<29} {1}'.format('\tFlawed Categories', '{0:>4} - {1}'.format(len(tidiedErrorSet), sorted(tidiedErrorSet))))
            continueSetup = True if not tidiedErrorSet else False

        except Exception as e:
            log('UTILS :: Error: creating Tidy Categories Dictionary: {0}'.format(e))
            log('UTILS :: Error:: Tidy Categories Source File: {0}'.format(tidy_txt))
            continueSetup = False

    #   8. Retrieve Thumbor Address
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('UTILS :: 8.\tRetrieve Thumbor Address')
        try:
            # Main Tidy has to be first in list as user can make changes
            thumbor_txt = os.path.join(pgmaFOLDER, 'Thumbor.txt')
            log('UTILS :: {0:<29} {1}'.format('\tThumbor File', thumbor_txt))
            pgmaTHUMBOR = PlexLoadFile(thumbor_txt).strip()
            log('UTILS :: {0:<29} {1}'.format('\tThumbor Address', pgmaTHUMBOR))
            continueSetup = True if pgmaTHUMBOR else False

        except Exception as e:
            log('UTILS :: Error:: Thumbor File missing or Empty: {0}'.format(thumbor_txt))
            continueSetup = False

    #   9. Retrieve Plex Token
    if continueSetup is True and not prefPLEXTOKEN:
        preferences_file = ''
        if platform.system() == 'Windows':
            try:
                import winreg
                hKey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Plex, Inc.\Plex Media Server")
                prefPLEXTOKEN = winreg.QueryValueEx(hKey, "PlexOnlineToken")[0]

            except Exception as e:
                log('UTILS :: {0:<29} {1}'.format('Failed to read registry: Search for Token Preferences.xml file', e))
                try:
                    preferences_file = os.path.join(PlexSupportPath, 'Preferences.xml').replace('Plex', 'Plex\Plex')
                    preferenceFileContents = PlexLoadFile(preferences_file)
                    xml = XML.ElementFromString(preferenceFileContents)
                    prefPLEXTOKEN = xml.xpath('/Preferences/@PlexOnlineToken')[0].strip()

                except Exception as e:
                    log('UTILS :: Error: retrieving Plex Token: TO DO: Input Manually in Preferences: {0}'.format(e))

            finally:
                winreg.CloseKey(hKey)

        elif platform.system() == 'Linux':
            try:
                preferences_file = os.path.join(PlexSupportPath, 'Preferences.xml')
                preferenceFileContents = PlexLoadFile(preferences_file)
                xml = XML.ElementFromString(preferenceFileContents)
                prefPLEXTOKEN = xml.xpath('/Preferences/@PlexOnlineToken')[0]

            except Exception as e:
                log('UTILS :: Error: retrieving Plex Token: Input Manually in Preferences: {0}'.format(e))

        elif platform.system() == 'Darwin':     # MAC OS
            try:
                preferences_file = os.path.join(PlexSupportPath, 'Preferences', 'com.plexapp.plexmediaserver.plist').replace('Application Support/Plex Media Server', '')
                preferences = plistlib.readPlist(preferences_file)
                prefPLEXTOKEN = preferences['PlexOnlineToken']
                log('UTILS :: {0:<29} {1}'.format('\tPlex Token', prefPLEXTOKEN))

            except Exception as e:
                pass

        log('UTILS :: {0:<29} {1}'.format('\tPlex Token', prefPLEXTOKEN))
        continueSetup == True if prefPLEXTOKEN else False

    #   10. Get Machine ID, Request Session, Library ID and Library Title
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('UTILS :: 10.\tRetrieve Machine ID, Library ID and Library Title')
        try:               
            plexBaseURL = 'http://127.0.0.1:32400'
            pgmaSSN = requests.Session()
            pgmaSSN.headers.update({'Accept': 'application/json'})
            pgmaSSN.params.update({'X-Plex-Token': prefPLEXTOKEN})
            pgmaMACHINEID = pgmaSSN.get('{0}/'.format(plexBaseURL))
            pgmaMACHINEID = pgmaMACHINEID.json()['MediaContainer']['machineIdentifier']
            log('UTILS :: {0:<29} {1}'.format('\tMachine ID', pgmaMACHINEID))

        except Exception as e:
            pgmaMACHINEID = ''
            pgmaSSN = ''
            log('UTILS :: Error: Getting Machine ID: {0}'.format(e))

        # Plex Library, that media resides in
        try:
            metadataURL = '{0}/library/metadata/{1}?X-Plex-Token={2}'.format(plexBaseURL, media.id, prefPLEXTOKEN)
            JSon = JSON.ObjectFromURL(metadataURL, timeout=20, sleep=delay())
            pgmaLIBRARYID = JSon.get('MediaContainer').get('librarySectionID')
            pgmaLIBRARYTITLE = JSon.get('MediaContainer').get('librarySectionTitle')
            log('UTILS :: {0:<29} {1}'.format('\tLibrary ID', pgmaLIBRARYID))
            log('UTILS :: {0:<29} {1}'.format('\tLibrary Title', pgmaLIBRARYTITLE))

        except Exception as e:
            pgmaLIBRARYID = ''
            pgmaLIBRARYTITLE = ''
            log('UTILS :: Error: Getting Library ID & Title: {0}'.format(e))

        continueSetup = True if pgmaMACHINEID and pgmaSSN and pgmaLIBRARYID and pgmaLIBRARYTITLE else False

    #   11. Get paths to Default Posters for Agent, Compilations Genre, IAFD, Stacks
    if continueSetup is True:
        log(LOG_SUBLINE)
        log('UTILS :: 11.\tRetrieve Agent and Default Posters')
        pgmaAGENTPOSTER = os.path.join(pgmaSYSTEMFOLDER, '{0}.png'.format(AGENT))
        pgmaAGENTPOSTER = pgmaAGENTPOSTER if os.path.exists(pgmaAGENTPOSTER) else ''

        pgmaCOMPILATIONSPOSTER = os.path.join(pgmaSYSTEMFOLDER, 'Compilations.png')
        pgmaCOMPILATIONSPOSTER = pgmaCOMPILATIONSPOSTER if os.path.exists(pgmaCOMPILATIONSPOSTER) else ''
        
        pgmaIAFD403POSTER = os.path.join(pgmaSYSTEMFOLDER, 'IAFD-403.png')
        pgmaIAFD403POSTER = pgmaIAFD403POSTER if os.path.exists(pgmaIAFD403POSTER) else ''
        
        pgmaIAFDFOUNDPOSTER = os.path.join(pgmaSYSTEMFOLDER, 'IAFD-Found.png')
        pgmaIAFDFOUNDPOSTER = pgmaIAFDFOUNDPOSTER if os.path.exists(pgmaIAFDFOUNDPOSTER) else ''
        
        pgmaIAFDNOTFOUNDPOSTER = os.path.join(pgmaSYSTEMFOLDER, 'IAFD-NotFound.png')
        pgmaIAFDNOTFOUNDPOSTER = pgmaIAFDNOTFOUNDPOSTER if os.path.exists(pgmaIAFDNOTFOUNDPOSTER) else ''
        
        pgmaSTACKEDPOSTER = os.path.join(pgmaSYSTEMFOLDER, 'Stacked-Yes.png')
        pgmaSTACKEDPOSTER = pgmaSTACKEDPOSTER if os.path.exists(pgmaSTACKEDPOSTER) else ''
        
        pgmaNOTSTACKEDPOSTER = os.path.join(pgmaSYSTEMFOLDER, 'Stacked-No.png')
        pgmaNOTSTACKEDPOSTER = pgmaNOTSTACKEDPOSTER if os.path.exists(pgmaNOTSTACKEDPOSTER) else ''
        
        pgmaNOCASTPOSTER = os.path.join(pgmaSYSTEMFOLDER, 'NoCastPhoto.png')
        pgmaNOCASTPOSTER = pgmaNOCASTPOSTER if os.path.exists(pgmaNOCASTPOSTER) else ''
        
        pgmaNODIRECTORPOSTER = os.path.join(pgmaSYSTEMFOLDER, 'NoDirectorPhoto.png')
        pgmaNODIRECTORPOSTER = pgmaNODIRECTORPOSTER if os.path.exists(pgmaNODIRECTORPOSTER) else ''
        
        pgmaWATERMARK = String.URLEncode('https://cdn0.iconfinder.com/data/icons/mobile-device/512/lowcase-letter-d-latin-alphabet-keyboard-2-32.png')
        log('UTILS :: {0:<29} {1}'.format('\tAgent Poster', pgmaAGENTPOSTER if pgmaAGENTPOSTER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\tCompilations Poster', pgmaCOMPILATIONSPOSTER if pgmaCOMPILATIONSPOSTER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\tIAFD Poster', pgmaIAFDFOUNDPOSTER if pgmaIAFDFOUNDPOSTER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\tNot IAFD Poster', pgmaIAFDNOTFOUNDPOSTER if pgmaIAFDNOTFOUNDPOSTER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\tStacked Poster', pgmaSTACKEDPOSTER if pgmaSTACKEDPOSTER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\tNot Stacked Poster', pgmaNOTSTACKEDPOSTER if pgmaNOTSTACKEDPOSTER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\tNo Cast Poster', pgmaNOCASTPOSTER if pgmaNOCASTPOSTER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\tNo Director Poster', pgmaNODIRECTORPOSTER if pgmaNODIRECTORPOSTER else WRONG_TICK))
        log('UTILS :: {0:<29} {1}'.format('\tWatermark', pgmaWATERMARK if pgmaWATERMARK else WRONG_TICK))

        # if any of the posters do not resolve we have to stop the Search Process: set GLOBAL variable and use later
        continueSetup = True if not tidiedErrorSet and pgmaAGENTPOSTER != '' and pgmaCOMPILATIONSPOSTER != '' and pgmaIAFDFOUNDPOSTER != '' and pgmaIAFDNOTFOUNDPOSTER != '' and pgmaSTACKEDPOSTER != '' and pgmaNOTSTACKEDPOSTER != '' and pgmaNOCASTPOSTER != '' and pgmaNODIRECTORPOSTER != '' and pgmaWATERMARK != '' else False

    log(LOG_SUBLINE)
    AgentVars = {}
    START_SCRAPE = 'Yes' if continueSetup is True else 'No'
    log('UTILS :: {0:<29} {1} {2}'.format('\tStart Scrape Process', RIGHT_TICK if START_SCRAPE == 'Yes' else WRONG_TICK, START_SCRAPE))

    if START_SCRAPE == 'Yes':
        AgentVars = {'prefCOLCAST': prefCOLCAST,
                    'prefCOLCOUNTRY': prefCOLCOUNTRY,
                    'prefCOLDIRECTOR': prefCOLDIRECTOR,
                    'prefCOLGENRE': prefCOLGENRE,
                    'prefCOLSERIES': prefCOLSERIES,
                    'prefCOLSTUDIO': prefCOLSTUDIO,
                    'prefCOLSYSTEM': prefCOLSYSTEM,
                    'prefCOUNTRYPOSTERTYPE': prefCOUNTRYPOSTERTYPE,
                    'prefDETECT': prefDETECT,
                    'prefDURATIONDX': prefDURATIONDX,
                    'prefMATCHIAFDDURATION': prefMATCHIAFDDURATION,
                    'prefMATCHSITEDURATION': prefMATCHSITEDURATION,
                    'prefPLEXTOKEN': prefPLEXTOKEN,
                    'prefPOSTERSOURCEDOWNLOAD': prefPOSTERSOURCEDOWNLOAD,
                    'prefPREFIXGENRE': prefPREFIXGENRE,
                    'prefPREFIXLEGEND': prefPREFIXLEGEND,
                    'prefUSEBACKGROUNDART': prefUSEBACKGROUNDART,
                    'pgmaAGENTPOSTER': pgmaAGENTPOSTER,
                    'pgmaCASTFACEFOLDER': pgmaCASTFACEFOLDER,
                    'pgmaCASTPOSTERFOLDER': pgmaCASTPOSTERFOLDER,
                    'pgmaCOMPILATIONSPOSTER': pgmaCOMPILATIONSPOSTER,
                    'pgmaCOUNTRYART': pgmaCOUNTRYART,
                    'pgmaCOUNTRYPOSTERFLAGS': pgmaCOUNTRYPOSTERFLAGS,
                    'pgmaCOUNTRYPOSTERMAPS': pgmaCOUNTRYPOSTERMAPS,
                    'pgmaCOUNTRYSET': pgmaCOUNTRYSET,
                    'pgmaDIRECTORFACEFOLDER': pgmaDIRECTORFACEFOLDER,
                    'pgmaDIRECTORPOSTERFOLDER': pgmaDIRECTORPOSTERFOLDER,
                    'pgmaFOLDER': pgmaFOLDER,
                    'pgmaGENRESDICT': pgmaGENRESDICT,
                    'pgmaGENREFOLDER': pgmaGENREFOLDER,
                    'pgmaIAFD403POSTER': pgmaIAFD403POSTER,
                    'pgmaIAFDFOUNDPOSTER': pgmaIAFDFOUNDPOSTER,
                    'pgmaIAFDNOTFOUNDPOSTER': pgmaIAFDNOTFOUNDPOSTER,
                    'pgmaLIBRARYID': pgmaLIBRARYID,
                    'pgmaLIBRARYTITLE': pgmaLIBRARYTITLE,
                    'pgmaMACHINEID': pgmaMACHINEID,
                    'pgmaNOCASTPOSTER': pgmaNOCASTPOSTER,
                    'pgmaNODIRECTORPOSTER': pgmaNODIRECTORPOSTER,
                    'pgmaNOTSTACKEDPOSTER': pgmaNOTSTACKEDPOSTER,
                    'pgmaSSN': pgmaSSN,
                    'pgmaSTACKEDPOSTER': pgmaSTACKEDPOSTER,
                    'pgmaSYSTEMFOLDER': pgmaSYSTEMFOLDER,
                    'pgmaTIDYDICT': pgmaTIDYDICT,
                    'pgmaTHUMBOR': pgmaTHUMBOR,
                    'pgmaWATERMARK': pgmaWATERMARK}

        # print out dictionary values / normalise unicode
        log('UTILS :: {0:<29} {1}'.format('AgentVars Dictionary:', ''))
        printDictionary(AgentVars, spacesCount=0, subkeyPrintCount=20, prefixCount='')

    #   Finish: Tidy Up - free up memory
    tidiedCountriesSet = None
    tidiedGenresSet = None
    tidiedNullSet = None
    tidiedErrorSet = None
    del(tidiedCountriesSet)
    del(tidiedGenresSet)
    del(tidiedNullSet)
    del(tidiedErrorSet)

    log(LOG_ASTLINE)
    log(LOG_ASTLINE)

    return AgentVars

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
            d = soundex_digits[ord(char) - ord('A')]
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
def synopsisCountriesGenres(AGENTDICT, myString):
    ''' extract genres and countries from synopsis text'''
    genresSet = set()
    countriesSet = set()
    log('UTILS :: Extract Countries and Genres from Synopsis:')
    try:
        synopsis = myString.strip()
        if synopsis:
            idx = 0
            for key, value in AGENTDICT['pgmaTIDYDICT'].items():
                if value is None or value == 'x':                               # skip if tidied out
                    continue

                if len(key) < 3:                                                # skip American and Canadian State Abbreviations
                    continue

                pattern = r'(?<![^ .,?!;]){0}(?![^ .,?!;\r\n])'.format(key)     # look for genre followed by punctuation or whitespace - to prevent stuff like "rio" in "priority"
                if re.search(pattern, synopsis, flags=re.IGNORECASE):
                    idx += 1
                    log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, key, value)))

                    if value in AGENTDICT['pgmaCOUNTRYSET']:
                        countriesSet.add(value)
                        continue

                    genresSet.add(value)

        showSetData(countriesSet, 'Countries (set*)')
        showSetData(genresSet, 'Genres (set*)')

    except Exception as e:
        log('UTILS :: Error: Extract Countries and Genres from Synopsis: {0}'.format(e))

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
        log('UTILS :: Run Translation: [Skip] - Library Language: [{0}]]'.format('No Language' if plexLibLanguageCode == 'xn' else 'Unknown'))
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
                log('UTILS :: Error: Detecting Text Language: {0}'.format(e))

        log('UTILS :: {0:<29} {1}'.format('Run Translation', msg))

        if runTranslation == 'Yes':
            if language is not None:
                try:
                    myString = translator.translate(myString, language)
                    myString = saveString if myString is None else myString
                    log('UTILS :: {0} Text: {1}'.format('Untranslated' if myString == saveString else 'Translated', myString))
                except Exception as e:
                    log('UTILS :: Error: Translating Text: {0}'.format(e))
            else:
                log('UTILS :: {0:<29} {1}'.format('Translation Skipped', plexLibLanguageCode))

    myString = myString if myString else ' ' # return single space to initialise metadata summary field

    return myString
# ----------------------------------------------------------------------------------------------------------------------------------
def WrapText(myHeading, myString):
    myString = myString.replace('\n', '')
    textList = wrap(myString, 100)
    for idx, textLine in enumerate(textList):
        log('UTILS :: {0:<29} {1}'.format(myHeading if idx == 0 else '', textLine.strip()))