#!/usr/bin/env python
# encoding=utf8
'''
General Functions found in all agents
                                                  Version History
                                                  ---------------
    Date            Modification
    27 Mar 2021   Added curly single quotes to string normalisation in addition to `, all quotes single quotes are now replaced by straight quotes
    03 May 2021   Issue #96 - Series Titles matching...
                  Added duration matching between filename duration and iafd duration
    08 May 2021   Merged GenFunctions.py with Utils.py created by codeanator to deal with cloudscraper protection issues in IAFD
    05 Jul 2021   Merged iafd.py with Utils
                  Improvements to name matching, Levenshtein and Soundex and translation
                  Changes to matching films against IAFD
                  Improved iafd matching and reduction of http requests to iafd
    20 Aug 2021   IAFD only searched after film found on Agent Website - Code Changes
                  improved code dealing with ffprobe duration garthering - as wmv returns were in a different arrangement, causing errors
                  show scraper name on summary legend line
    11 Dec 2021   Remove ffprobe as it may causes issue on several configurations and is too ressource-consuming. Relying on Plex native duration
                  Using os.split to remove file extension prior retrieving all the necessary data
    13 Dec 2021   Cropping function is now more resilient by fallbacking to original image.
                  Added IAFD search by actor (for blogs)
                  Added title search by actor (for blogs)
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
    # clean up the Cast List make a copy then clear
    agntCastList = [x.split('(')[0].strip() if '(' in x else x.strip() for x in agntCastList]
    agntCastList = [String.StripDiacritics(x) for x in agntCastList]
    agntCastList = [x for x in agntCastList if x]
    log('UTILS :: Agent Cast List - Original    : %s', agntCastList)
    excludeList = [string for string in agntCastList if [substr for substr in agntCastList if substr in string and substr != string]]
    if excludeList:
        agntCastList = [x for x in agntCastList if x not in excludeList]
        log('UTILS :: Agent Cast List - Exclude     : %s', excludeList)
        log('UTILS :: Agent Cast List - Result      : %s', agntCastList)

    # strip all non alphabetic characters from cast names / aliases so as to compare them to the list obtained from the website e.g. J.T. Sloan will render as jtsloan
    castDict = FILMDICT['Cast']
    log('UTILS :: IAFD Cast List                : %s', castDict.keys())

    IAFDCastList = [(re.sub(r'[\W\d_]', '', k).strip().lower(), re.sub(r'[\W\d_]', '', v['Alias']).strip().lower()) for k, v in castDict.items()] # list of tuples [name, alias]
    log('UTILS :: IAFD Cast List Normalised     : %s', IAFDCastList)

    # remove entries from the website cast list which have been found on IAFD leaving unmatched cast
    unmatchedCastList = [x for x in agntCastList if re.sub(r'[\W\d_]', '', x).strip().lower() not in (item for namealias in IAFDCastList for item in namealias)]
    log('UTILS :: IAFD Unmatched Cast List      : %s', unmatchedCastList)
    log(LOG_SUBLINE)

    # search IAFD for specific cast and return matched cast
    matchedCastDict = matchCast(unmatchedCastList, FILMDICT)

    # update the Cast dictionary
    if matchedCastDict:
        castDict.update(matchedCastDict)

    log(LOG_SUBLINE)

    return castDict

# -------------------------------------------------------------------------------------------------------------------------------
def getDirectors(agntDirectorList, FILMDICT):
    ''' Process and match director list against IAFD'''
    # clean up the Director List 
    agntDirectorList = [x.split('(')[0].strip() if '(' in x else x.strip() for x in agntDirectorList]
    agntDirectorList = [String.StripDiacritics(x) for x in agntDirectorList]
    agntDirectorList = [x for x in agntDirectorList if x]
    log('UTILS :: Agent Director List - Original: %s', agntDirectorList)
    excludeList = [string for string in agntDirectorList if [substr for substr in agntDirectorList if substr in string and substr != string]]
    if excludeList:
        agntDirectorList = [x for x in agntDirectorList if x not in excludeList]
        log('UTILS :: Agent Director List - Exclude : %s', excludeList)
        log('UTILS :: Agent Director List - Result  : %s', agntDirectorList)

    # strip all non alphabetic characters from director names / aliases so as to compare them to the list obtained from the website e.g. J.T. Sloan will render as jtsloan
    directorDict = FILMDICT['Directors']
    log('UTILS :: IAFD Director List            : %s', directorDict.keys())

    IAFDDirectorList = [(re.sub(r'[\W\d_]', '', k).strip().lower(), v) for k, v in directorDict.items()] # list of tuples [name, alias]
    log('UTILS :: IAFD Director List Normalised : %s', IAFDDirectorList)

    # remove entries from the website cast list which have been found on IAFD leaving unmatched director
    unmatchedDirectorList = [x for x in agntDirectorList if re.sub(r'[\W\d_]', '', x).strip().lower() not in (item for namealias in IAFDDirectorList for item in namealias)]
    log('UTILS :: IAFD Unmatched Director List  : %s', unmatchedDirectorList)
    log(LOG_SUBLINE)

    # search IAFD for specific director and return matched directors
    matchedDirectorDict = matchDirectors(unmatchedDirectorList, FILMDICT)

    # update the Cast dictionary
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
    if cropRequired:
        try:
            log('UTILS :: Using Thumbor to crop image to: {0} x {1}'.format(desiredWidth, desiredHeight))
            pic = THUMBOR.format(cropWidth, cropHeight, imageURL)
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
                    cmd = CROPPER.format(LocalAppDataFolder, imageURL, pic, cropWidth, cropHeight)
                    subprocess.call(cmd)
                    picContent = load_file(pic)
                else:
                    pic = imageURL
                    picContent = HTTP.Request(imageURL).content
            except Exception as e:
                log('UTILS :: Error Script Failed to Crop Image to: {0} x {1}'.format(desiredWidth, desiredHeight))
                pic = imageURL
                picContent = HTTP.Request(imageURL).content
    else:
        picContent = HTTP.Request(pic).content

    log('UTILS :: Returning pic : %s', pic)
    return pic, picContent

# -------------------------------------------------------------------------------------------------------------------------------
def getFilmOnIAFD(FILMDICT):
    ''' check IAFD web site for better quality thumbnails per movie'''
    FILMDICT['Cast'] = {}
    FILMDICT['Comments'] = ''
    FILMDICT['Directors'] = {}
    FILMDICT['FoundOnIAFD'] = 'No'
    FILMDICT['IAFDFilmURL'] = ''
    FILMDICT['Scenes'] = ''
    FILMDICT['Synopsis'] = ''

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

    # strip standalone '1's'
    pattern = ur'(?<!\d)1(?!\d)'
    FILMDICT['IAFDTitle'] = re.sub(pattern, '', FILMDICT['IAFDTitle'])

    # strip definite and indefinite english articles
    pattern = ur'^(The|An|A) '
    matched = re.search(pattern, FILMDICT['IAFDTitle'], re.IGNORECASE)  # match against whole string
    if matched:
        FILMDICT['IAFDTitle'] = FILMDICT['IAFDTitle'][matched.end():]
        tempCompare = SortAlphaChars(NormaliseComparisonString(FILMDICT['IAFDTitle']))
        if tempCompare not in FILMDICT['IAFDCompareTitle']:
            FILMDICT['IAFDCompareTitle'].append(tempCompare)

    # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string, also remove '!'
    FILMDICT['IAFDSearchTitle'] = FILMDICT['IAFDTitle']
    FILMDICT['IAFDSearchTitle'] = String.StripDiacritics(FILMDICT['IAFDSearchTitle']).strip()
    FILMDICT['IAFDSearchTitle'] = String.URLEncode(FILMDICT['IAFDSearchTitle'])
    FILMDICT['IAFDSearchTitle'] = FILMDICT['IAFDSearchTitle'].replace('%25', '%').replace('*', '')

    # search for Film Title on IAFD
    try:
        html = getURLElement(IAFD_SEARCH_URL.format(FILMDICT['IAFDSearchTitle']), UseAdditionalResults=True)

        # get films listed within 1 year of what is on agent - as IAFD may have a different year recorded
        filmList = []
        if FILMDICT['Year']:
            FILMDICT['Year'] = int(FILMDICT['Year'])
            log ('UTILS :: XPath string [%s]', '//table[@id="titleresult"]/tbody/tr/td[2][.>="{0}" and .<="{1}"]/ancestor::tr'.format(FILMDICT['Year'] - 1, FILMDICT['Year'] + 1))
            filmList = html.xpath('//table[@id="titleresult"]/tbody/tr/td[2][.>="{0}" and .<="{1}"]/ancestor::tr'.format(FILMDICT['Year'] - 1, FILMDICT['Year'] + 1))
            log ('UTILS :: [{0}] Films found on IAFD between the years [{1}] and [{2}]'.format(len(filmList), FILMDICT['Year'] - 1, FILMDICT['Year'] + 1))

        if not filmList:
            filmList = html.xpath('//table[@id="titleresult"]/tbody/tr')
            log('UTILS :: [{0}] Films found on IAFD'.format(len(filmList)))

        log(LOG_BIGLINE)

        for film in filmList:
            # Site Title and Site AKA
            try:
                iafdTitle = film.xpath('./td[1]/a/text()')[0].strip()
                matchTitle(iafdTitle, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                try:
                    log('UTILS :: Error getting Site Title: %s', e)

                    iafdAKA = film.xpath('./td[4]/text()')[0].strip()
                    matchTitle(iafdAKA, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('UTILS :: Error getting Site AKA Title: %s', e)
                    log(LOG_SUBLINE)
                    continue

            # Film URL
            try:
                iafdfilmURL = film.xpath('./td[1]/a/@href')[0].replace('+/', '/').replace('-.', '.')
                iafdfilmURL = '{0}{1}'.format(IAFD_BASE, iafdfilmURL) if iafdfilmURL[0] == '/' else '{0}/{1}'.format(IAFD_BASE, iafdfilmURL)
                log('UTILS :: Site Title url                %s', iafdfilmURL)
                html = getURLElement(iafdfilmURL, UseAdditionalResults=False)
                log(LOG_BIGLINE)
            except Exception as e:
                log('UTILS :: Error: IAFD URL Studio: %s', e)
                log(LOG_SUBLINE)
                continue

            # Film Duration
            try:
                iafdDuration = html.xpath('//p[@class="bioheading" and text()="Minutes"]//following-sibling::p[1]/text()')[0].strip()
                matchDuration(iafdDuration, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                log('UTILS :: Error: IAFD Duration: %s', e)
                log(LOG_SUBLINE)
                continue

            # Film Studio and Distributor
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
                    log('UTILS :: Error: %s', e)
                    continue

            if not studioMatch:
                log('UTILS :: Error getting Site Studio')
                log(LOG_SUBLINE)
                continue

            # if we get here we have found a film match
            FILMDICT['FoundOnIAFD'] = 'Yes'
            FILMDICT['IAFDFilmURL'] = iafdfilmURL

            # check if film is a compilation
            try:
                FILMDICT['Compilation'] = html.xpath('//p[@class="bioheading" and text()="Compilation"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: Film Compilation Information: %s', FILMDICT['Compilation'])
            except Exception as e:
                log('UTILS :: Error Finding Compilation Information: %s', e)

            # get Film Cast info
            log(LOG_BIGLINE)
            try:
                FILMDICT['Cast'] = getRecordedCast(html)
            except Exception as e:
                log('UTILS :: Error Finding Cast Information: %s', e)

            # get Director info
            log(LOG_BIGLINE)
            try:
                FILMDICT['Directors'] = getRecordedDirectors(html)
            except Exception as e:
                log('UTILS :: Error Finding Director Information: %s', e)

            # synopsis
            log(LOG_BIGLINE)
            try:
                FILMDICT['Synopsis'] = html.xpath('//div[@id="synopsis"]/div/ul/li//text()')[0].strip()
                log('UTILS :: Film Synopsis: %s', FILMDICT['Synopsis'])
            except Exception as e:
                log('UTILS :: Error getting Synopsis: %s', e)

            # get Scene Breakdown
            log(LOG_BIGLINE)
            try:
                scene = html.xpath('//div[@id="sceneinfo"]/ul/li//text()')[0] # will error if no scenebreakdown
                htmlscenes = html.xpath('//div[@id="sceneinfo"]/ul/li//text()[normalize-space()]')
                FILMDICT['Scenes'] = "##".join(htmlscenes)
                log('UTILS :: Film Scenes: %s', FILMDICT['Scenes'])
            except Exception as e:
                log('UTILS :: Error getting Scene Breakdown: %s', e)

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
                log('UTILS :: Film Comments: %s', FILMDICT['Comments'])
            except Exception as e:
                log('UTILS :: Error getting Comments: %s', e)

            log(LOG_BIGLINE)
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


# -------------------------------------------------------------------------------------------------------------------------------
def getFilmOnIAFDActors(FILMDICT):
    ''' check IAFD web site for better quality thumbnails per movie'''
    FILMDICT['Cast'] = {}
    FILMDICT['Comments'] = ''
    FILMDICT['Directors'] = {}
    FILMDICT['FoundOnIAFD'] = 'No'
    FILMDICT['IAFDFilmURL'] = ''
    FILMDICT['Scenes'] = ''
    FILMDICT['Synopsis'] = ''

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

    # strip standalone '1's'
    pattern = ur'(?<!\d)1(?!\d)'
    FILMDICT['IAFDTitle'] = re.sub(pattern, '', FILMDICT['IAFDTitle'])

    # strip definite and indefinite english articles
    pattern = ur'^(The|An|A) '
    matched = re.search(pattern, FILMDICT['IAFDTitle'], re.IGNORECASE)  # match against whole string
    if matched:
        FILMDICT['IAFDTitle'] = FILMDICT['IAFDTitle'][matched.end():]
        tempCompare = SortAlphaChars(NormaliseComparisonString(FILMDICT['IAFDTitle']))
        if tempCompare not in FILMDICT['IAFDCompareTitle']:
            FILMDICT['IAFDCompareTitle'].append(tempCompare)

    # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string, also remove '!'
    FILMDICT['IAFDSearchTitle'] = re.split(',|and|fucks|barebacks',FILMDICT['IAFDTitle'])[0]
    FILMDICT['IAFDSearchTitle'] = String.StripDiacritics(FILMDICT['IAFDSearchTitle']).strip()
    FILMDICT['IAFDSearchTitle'] = String.URLEncode(FILMDICT['IAFDSearchTitle'])
    FILMDICT['IAFDSearchTitle'] = FILMDICT['IAFDSearchTitle'].replace('%25', '%').replace('*', '')

    # search for Film Title on IAFD
    try:
        html = getURLElement(IAFD_SEARCH_URL.format(FILMDICT['IAFDSearchTitle']), UseAdditionalResults=True)

        # get films listed within 1 year of what is on agent - as IAFD may have a different year recorded
        filmList = []
        if FILMDICT['Year']:
            FILMDICT['Year'] = int(FILMDICT['Year'])
            log ('UTILS :: XPath string [%s]', '//table[@id="titleresult"]/tbody/tr/td[2][.>="{0}" and .<="{1}"]/ancestor::tr'.format(FILMDICT['Year'] - 1, FILMDICT['Year'] + 1))
            filmList = html.xpath('//table[@id="titleresult"]/tbody/tr/td[2][.>="{0}" and .<="{1}"]/ancestor::tr'.format(FILMDICT['Year'] - 1, FILMDICT['Year'] + 1))
            log ('UTILS :: [{0}] Films found on IAFD between the years [{1}] and [{2}]'.format(len(filmList), FILMDICT['Year'] - 1, FILMDICT['Year'] + 1))

        if not filmList:
            filmList = html.xpath('//table[@id="titleresult"]/tbody/tr')
            log('UTILS :: [{0}] Films found on IAFD'.format(len(filmList)))

        log(LOG_BIGLINE)

        for film in filmList:
            # Site Title and Site AKA
            try:
                iafdTitle = film.xpath('./td[1]/a/text()')[0].strip()
                # separating the string to get the actors
                spaceChars = ['Fucks','Barebacks','Raw']
                pattern = u'({0})'.format('|'.join(spaceChars))
                matched = re.search(pattern, iafdTitle)  # match against whole string
                if matched:
                    iafdTitle = re.sub(pattern, ' ', iafdTitle)
                    iafdTitle = ' '.join(iafdTitle.split())   # remove continous white space
                matchTitleActors(iafdTitle, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                try:
                    log('UTILS :: Error getting Site Title: %s', e)
                    iafdAKA = film.xpath('./td[4]/text()')[0].strip()
                    # separating the string to get the actors
                    spaceChars = ['Fucks','Barebacks','Raw']
                    pattern = u'({0})'.format('|'.join(spaceChars))
                    matched = re.search(pattern, iafdAKA)  # match against whole string
                    if matched:
                        iafdAKA = re.sub(pattern, ' ', iafdAKA)
                        iafdAKA = ' '.join(iafdAKA.split())   # remove continous white space
                    matchTitleActors(iafdAKA, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('UTILS :: Error getting Site AKA Title: %s', e)
                    log(LOG_SUBLINE)
                    continue

            # Film URL
            try:
                iafdfilmURL = film.xpath('./td[1]/a/@href')[0].replace('+/', '/').replace('-.', '.')
                iafdfilmURL = '{0}{1}'.format(IAFD_BASE, iafdfilmURL) if iafdfilmURL[0] == '/' else '{0}/{1}'.format(IAFD_BASE, iafdfilmURL)
                log('UTILS :: Site Title url                %s', iafdfilmURL)
                html = getURLElement(iafdfilmURL, UseAdditionalResults=False)
                log(LOG_BIGLINE)
            except Exception as e:
                log('UTILS :: Error: IAFD URL Studio: %s', e)
                log(LOG_SUBLINE)
                continue

            # Film Duration
            try:
                iafdDuration = html.xpath('//p[@class="bioheading" and text()="Minutes"]//following-sibling::p[1]/text()')[0].strip()
                matchDuration(iafdDuration, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                log('UTILS :: Error: IAFD Duration: %s', e)
                log(LOG_SUBLINE)
                continue

            # Film Studio and Distributor
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
                    log('UTILS :: Error: %s', e)
                    continue

            if not studioMatch:
                log('UTILS :: Error getting Site Studio')
                log(LOG_SUBLINE)
                continue

            # if we get here we have found a film match
            FILMDICT['FoundOnIAFD'] = 'Yes'
            FILMDICT['IAFDFilmURL'] = iafdfilmURL

            # check if film is a compilation
            try:
                FILMDICT['Compilation'] = html.xpath('//p[@class="bioheading" and text()="Compilation"]//following-sibling::p[1]/text()')[0].strip()
                log('UTILS :: Film Compilation Information: %s', FILMDICT['Compilation'])
            except Exception as e:
                log('UTILS :: Error Finding Compilation Information: %s', e)

            # get Film Cast info
            log(LOG_BIGLINE)
            try:
                FILMDICT['Cast'] = getRecordedCast(html)
            except Exception as e:
                log('UTILS :: Error Finding Cast Information: %s', e)

            # get Director info
            log(LOG_BIGLINE)
            try:
                FILMDICT['Directors'] = getRecordedDirectors(html)
            except Exception as e:
                log('UTILS :: Error Finding Director Information: %s', e)

            # synopsis
            log(LOG_BIGLINE)
            try:
                FILMDICT['Synopsis'] = html.xpath('//div[@id="synopsis"]/div/ul/li//text()')[0].strip()
                log('UTILS :: Film Synopsis: %s', FILMDICT['Synopsis'])
            except Exception as e:
                log('UTILS :: Error getting Synopsis: %s', e)

            # get Scene Breakdown
            log(LOG_BIGLINE)
            try:
                scene = html.xpath('//div[@id="sceneinfo"]/ul/li//text()')[0] # will error if no scenebreakdown
                htmlscenes = html.xpath('//div[@id="sceneinfo"]/ul/li//text()[normalize-space()]')
                FILMDICT['Scenes'] = "##".join(htmlscenes)
                log('UTILS :: Film Scenes: %s', FILMDICT['Scenes'])
            except Exception as e:
                log('UTILS :: Error getting Scene Breakdown: %s', e)

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
                log('UTILS :: Film Comments: %s', FILMDICT['Comments'])
            except Exception as e:
                log('UTILS :: Error getting Comments: %s', e)

            log(LOG_BIGLINE)
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
        log('UTILS :: CloudScraper Request           %s', url)
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
        castList = html.xpath('//h3[.="Performers"]/ancestor::div[@class="panel panel-default"]//div[@class[contains(.,"castbox")]]/p')
        log('UTILS :: %s Cast on IAFD', len(castList))
        for cast in castList:
            castName = cast.xpath('./a/text()[normalize-space()]')[0].strip()
            castURL = IAFD_BASE + cast.xpath('./a/@href')[0].strip()
            castPhoto = cast.xpath('./a/img/@src')[0].strip()
            castPhoto = '' if 'nophoto' in castPhoto or 'th_iafd_ad' in castPhoto else castPhoto
            castRole = cast.xpath('./text()[normalize-space()]')
            castRole = ' '.join(castRole).strip()

            try:
                castAlias = cast.xpath('./i/text()')[0].split(':')[1].replace(')', '').strip()
            except:
                castAlias = ''

            castRole = castRole if castRole else 'AKA: {0}'.format(castAlias) if castAlias else IAFD_FOUND

            # log cast details
            log('UTILS :: Cast Name:                   \t%s', castName)
            log('UTILS :: Cast Alias:                  \t%s', castAlias)
            log('UTILS :: Cast URL:                    \t%s', castURL)
            log('UTILS :: Cast Photo:                  \t%s', castPhoto)
            log('UTILS :: Cast Role:                   \t%s', castRole)

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
        log('UTILS :: %s Directors on IAFD', len(directorList))
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

            log('UTILS :: Director Name:               \t%s', directorName)
            log('UTILS :: Director Alias:              \t%s', directorAliasList)
            log('UTILS :: Director URL:                \t%s', directorURL)
            log('UTILS :: Director Photo:              \t%s', directorPhoto)
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
                log('UTILS :: No Additional Search Results: %s', e)
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
    log('%s:: Version                      : v.%s', header, VERSION_NO)
    log('%s:: Python                       : %s %s', header, platform.python_version(), platform.python_build())
    log('%s:: Platform                     : %s - %s %s', header, platform.machine(), platform.system(), platform.release())
    log('%s:: Preferences:', header)
    log('%s::  > Cast Legend Before Summary: %s', header, PREFIXLEGEND)
    log('%s::  > Clear Previous Collections: %s - %s', header, COLCLEAR, type(COLCLEAR))
    log('%s::  > Collection Gathering', header)
    log('%s::      > Cast                  : %s - %s', header, COLCAST, type(COLCAST))
    log('%s::      > Director(s)           : %s - %s', header, COLDIRECTOR, type(COLDIRECTOR))
    log('%s::      > Studio                : %s - %s', header, COLSTUDIO, type(COLSTUDIO))
    log('%s::      > Film Title            : %s - %s', header, COLTITLE, type(COLTITLE))
    log('%s::      > Genres                : %s - %s', header, COLGENRE, type(COLGENRE))
    log('%s::  > Match Site Duration       : %s', header, MATCHSITEDURATION)
    log('%s::  > Duration Difference       : ±%s Minutes', header, DURATIONDX)
    log('%s::  > Language Detection        : %s', header, DETECT)
    log('%s::  > Library:Site Language     : (%s:%s)', header, lang, SITE_LANGUAGE)
    log('%s::  > Network Request Delay     : %s Seconds', header, DELAY)
    
    log('%s:: Media Title                  : %s', header, media.title)
    log('%s:: File Path                    : %s', header, media.items[0].parts[0].file)
    log(LOG_BIGLINE)

# -------------------------------------------------------------------------------------------------------------------------------
def matchCast(agntCastList, FILMDICT):
    ''' check IAFD web site for individual cast'''
    matchedCastDict = {}

    if FILMDICT['Year']:
        FILMDICT['Year'] = int(FILMDICT['Year'])

    useFullCareer = True if FILMDICT['Year'] else False  

    for agntCast in agntCastList:
        compareAgntCast = re.sub(r'[\W\d_]', '', agntCast).strip().lower()
        log('UTILS :: Unmatched Cast Name %s', agntCast)

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
                log('UTILS :: Matched with IAFD Cast:      \tFull Match - Cast Name: %s', agntCast)
                matchedName = True
                break

            # 2nd full match against Cast Alias
            if compareAgntCast == IAFDCompareAlias:
                log('UTILS :: Matched with IAFD Cast:      \tFull Match - Cast Alias: %s', agntCast)
                matchedName = True
                break

            # 3rd partial match against Cast Name
            if compareAgntCast in IAFDCompareName:
                log('UTILS :: Matched with IAFD Cast:      \tPartial Match - Cast Name: %s', agntCast)
                matchedName = True
                break

            # 4th partial match against Cast Alias
            if compareAgntCast in IAFDCompareAlias:
                log('UTILS :: Matched with IAFD Cast:      \tPartial Match - Cast Alias: %s', agntCast)
                matchedName = True
                break

            # Lehvensten and Soundex Matching
            levDistance = len(agntCast.split()) + 1 if len(agntCast.split()) > 1 else 1 # Set Lehvenstein Distance - one change/word+1 of cast names or set to 1
            testName = IAFDName if levDistance > 1 else IAFDName.split()[0] if IAFDName else ''
            testAlias = IAFDAlias if levDistance > 1 else IAFDAlias.split()[0] if IAFDAlias else ''
            testNameType = 'Full Names' if levDistance > 1 else 'First Name' 

            # 5th Lehvenstein Match against Cast Name
            levScore = String.LevenshteinDistance(agntCast, testName)
            matchedName = levScore <= levDistance
            if matchedName:
                log('UTILS :: Levenshtein Match:           \tUse %s on IAFD', testNameType)
                log('UTILS ::                              \tIAFD Cast Name  : %s', testName)
                log('UTILS ::                              \tAgent Cast Name : %s', agntCast)
                log('UTILS ::                              \tScore:Distance  : {%s:%s}', levScore, levDistance)
                log('UTILS ::                              \tMatched         : %s', matchedName)
                log(LOG_SUBLINE)
                break

            # 6th Lehvenstein Match against Cast Alias
            if testAlias:
                levScore = String.LevenshteinDistance(agntCast, testAlias)
                matchedName = levScore <= levDistance
                if matchedName:
                    log('UTILS :: Levenshtein Match:           \tUse %s on IAFD', testNameType)
                    log('UTILS ::                              \tIAFD Cast Alias : %s', testAlias)
                    log('UTILS ::                              \tAgent Cast Name : %s', agntCast)
                    log('UTILS ::                              \tScore:Distance  : {%s:%s}', levScore, levDistance)
                    log('UTILS ::                              \tMatched         : %s', matchedName)
                    log(LOG_SUBLINE)
                    break

            # 7th Soundex Matching on Cast Name
            soundIAFD = soundex(testName)
            soundAgent = soundex(agntCast)
            matchedName = soundIAFD == soundAgent
            if matchedName:
                log('UTILS :: SoundEx Match:               \tUse %s on IAFD', testNameType)
                log('UTILS ::                              \tIAFD Cast Name   : %s', testName)
                log('UTILS ::                              \tAgent Cast Name  : %s', agntCast)
                log('UTILS ::                              \tSound Scores I:A :{%s:%s}', soundIAFD, soundAgent)
                log('UTILS ::                              \tMatched          : %s', matchedName)
                break

            # 8th Soundex Matching on Cast Alias
            if testAlias:
                soundIAFD = soundex(testAlias)
                soundAgent = soundex(agntCast)
                matchedName = soundIAFD == soundAgent
                if matchedName:
                    log('UTILS :: SoundEx Match:               \tUse %s on IAFD', testNameType)
                    log('UTILS ::                              \tIAFD Cast Alias  : %s', testAlias)
                    log('UTILS ::                              \tAgent Cast Name  : %s', agntCast)
                    log('UTILS ::                              \tSound Scores I:A :{%s:%s}', soundIAFD, soundAgent)
                    log('UTILS ::                              \tMatched          : %s', matchedName)
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
            for i in range(2):
                if i == 0 and useFullCareer:
                    filter = 'Year'
                    useFullCareer = True
                    xPathMatchMainMale = '//table[@id="tblMal"]/tbody/tr[td[2]/a[(contains(@href, "/perfid={0}") or (.) = "{1}" or translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="{2}")] and {3}>=td[4] and {3}<=td[5]]//ancestor::tr'.format(compareAgntCast, agntCast, agntCastLower, FILMDICT['Year'])
                    xPathMatchAliasMale = '//table[@id="tblMal"]/tbody/tr[contains(td[3], "{0}") and {1}>=td[4] and {1}<=td[5]]//ancestor::tr'.format(agntCast, FILMDICT['Year'])
                    xPathMatchMainFemale = '//table[@id="tblFem"]/tbody/tr[td[2]/a[(contains(@href, "/perfid={0}") or (.) = "{1}" or translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="{2}")] and {3}>=td[4] and {3}<=td[5]]//ancestor::tr'.format(compareAgntCast, agntCast, agntCastLower, FILMDICT['Year'])
                    xPathMatchAliasFemale = '//table[@id="tblFem"]/tbody/tr[contains(td[3], "{0}") and {1}>=td[4] and {1}<=td[5]]//ancestor::tr'.format(agntCast, FILMDICT['Year'])
                else:
                    # some agents mislabel compilations, thus cast won't be found by the Film Year
                    filter = 'Name'
                    useFullCareer = False
                    xPathMatchMainMale = '//table[@id="tblMal"]/tbody/tr[td[2]/a[(contains(@href, "/perfid={0}") or (.) = "{1}" or translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="{2}")]]//ancestor::tr'.format(compareAgntCast, agntCast, agntCastLower)
                    xPathMatchAliasMale = '//table[@id="tblMal"]/tbody/tr[contains(td[3], "{0}")]//ancestor::tr'.format(agntCast) 
                    xPathMatchMainFemale = '//table[@id="tblFem"]/tbody/tr[td[2]/a[(contains(@href, "/perfid={0}") or (.) = "{1}" or translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="{2}")]]//ancestor::tr'.format(compareAgntCast, agntCast, agntCastLower)
                    xPathMatchAliasFemale = '//table[@id="tblFem"]/tbody/tr[contains(td[3], "{0}")]//ancestor::tr'.format(agntCast) 

                combinedList = []
                for xPath in [xPathMatchMainMale, xPathMatchAliasMale, xPathMatchMainFemale, xPathMatchAliasFemale]:
                    try:
                        mainList = html.xpath(xPath)
                    except:
                        log('UTILS :: Error: Bad Main Name xPath: %s', xPath)
                        mainList = []

                    combinedList.extend(mainList)

                castList = [j for x, j in enumerate(combinedList) if j not in combinedList[:x]]
                castFound = len(castList)
                log('UTILS :: %s Filter: %s\t[%s] Cast found named %s on Agent Website %s', filter, 'Career Match   ' if useFullCareer else 'No Career Match', castFound, agntCast, '<Skipping: too many found>' if castFound > 13 else '')
                if (i == 0 and castFound > 0) or castFound > 13:
                    break

            if castFound == 0 or castFound > 13:    #skip cast
                log(LOG_SUBLINE)
                continue

            for cast in castList:
                # get cast details and compare to Agent cast
                try:
                    castName = cast.xpath('./td[2]/a/text()[normalize-space()]')[0]
                    compareCastName = re.sub(r'[\W\d_]', '', castName).strip().lower()
                    log('UTILS :: Cast Name:                   \t%s / %s', castName, compareCastName)

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

                # match iafd row with Agent Cast entry
                matchedCast = True if compareAgntCast == compareCastName else False

                if not matchedCast and castAliasList:
                    matchedItem = [i for (i, x) in enumerate(compareCastAliasList) if x == compareAgntCast]
                    matchedCast = True if matchedItem else False

                # only perform career checks if title is not a compilation and we have not filtered the search results by the Film Year
                if not matchedCast and FILMDICT['Compilation'] == "No" and useFullCareer:
                    matchedCast = (startCareer <= FILMDICT['Year'] <= endCareer)

                if not matchedCast:
                    log('UTILS :: Error: Could not match Cast: %s', agntCast)
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
                        log('UTILS :: Skipping: Recorded Cast Name: %s AKA %s also known by this name: %s', checkName, checkAlias, castName)
                        matchedCastDict.pop(agntCast)
                        break

                if matchedCastWithIAFD:
                    break

                # we have an cast who satisfies the conditions
                castURL = IAFD_BASE + cast.xpath('./td[2]/a/@href')[0]
                castPhoto = cast.xpath('./td[1]/a/img/@src')[0] # Cast Name on agent website - retrieve picture
                castPhoto = '' if 'nophoto' in castPhoto or 'th_iafd_ad' in castPhoto else castPhoto.replace('thumbs/th_', '')
                castRole = IAFD_FOUND  # default to found

                log('UTILS :: Cast Alias:                  \t%s', castAliasList)
                log('UTILS :: Start Career:                \t%s', startCareer)
                log('UTILS :: End Career:                  \t%s', endCareer)
                log('UTILS :: Cast URL:                    \t%s', castURL)
                log('UTILS :: Cast Photo:                  \t%s', castPhoto)
                log('UTILS :: Cast Role:                   \t%s', castRole)

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

    useFullCareer = True if FILMDICT['Year'] else False  

    log('UTILS :: TEST Unmatched Directors %s', agntDirectorList)
    for agntDirector in agntDirectorList:
        compareAgntDirector = re.sub(r'[\W\d_]', '', agntDirector).strip().lower()

        log('UTILS :: Unmatched Director Name %s', agntDirector)

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
                log('UTILS :: Matched with IAFD Director:  \tFull Match - Director Name: %s', agntDirector)
                matchedName = True
                break

            # 2nd full match against director alias
            if [x for x in IAFDCompareAlias if x == compareAgntDirector]:
                log('UTILS :: Matched with IAFD Director:  \tFull Match - Director Alias: %s', agntDirector)
                matchedName = True
                break

            # 3rd partial match against director name
            if compareAgntDirector in IAFDCompareName:
                log('UTILS :: Matched with IAFD Director:  \tPartial Match - Director Name: %s', agntDirector)
                matchedName = True
                break

            # 4th partial match against director alias
            if compareAgntDirector in IAFDCompareAlias:
                log('UTILS :: Matched with IAFD Director:  \tPartial Match - Director Alias: %s', agntDirector)
                matchedName = True
                break

            # Lehvensten and Soundex Matching
            levDistance = len(agntDirector.split()) + 1 if len(agntDirector.split()) > 1 else 1 # Set Lehvenstein Distance - one change/word+1 of cast names or set to 1
            testNameType = 'Full Names' if levDistance > 1 else 'First Name' 
            testName = IAFDName if levDistance > 1 else IAFDName.split()[0] if IAFDName else ''
            if IAFDAlias is list:
                testAlias = [x if levDistance > 1 else x.split()[0] for x in IAFDAlias]
            else:
                testAlias = IAFDAlias if levDistance > 1 else IAFDAlias.split()[0] if IAFDAlias else ''

            # 5th Lehvenstein Match against Director Name
            levScore = String.LevenshteinDistance(agntDirector, testName)
            matchedName = levScore <= levDistance
            if matchedName:
                log('UTILS :: Levenshtein Match:           \tUse %s on IAFD', testNameType)
                log('UTILS ::                              \tIAFD Cast Name  : %s', testName)
                log('UTILS ::                              \tAgent Cast Name : %s', agntDirector)
                log('UTILS ::                              \tScore:Distance  : {%s:%s}', levScore, levDistance)
                log('UTILS ::                              \tMatched         : %s', matchedName)
                log(LOG_SUBLINE)
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
                    log('UTILS :: Levenshtein Match:           \tUse %s on IAFD', testNameType)
                    log('UTILS ::                              \tIAFD Director Alias : %s', testAlias)
                    log('UTILS ::                              \tAgent Director Name : %s', agntDirector)
                    log('UTILS ::                              \tScore:Distance      : {%s:%s}', levScore, levDistance)
                    log('UTILS ::                              \tMatched             : %s', matchedName)
                    log(LOG_SUBLINE)
                    break

            # 7th Soundex Matching on Cast Name
            soundIAFD = [soundex(x) for x in testName] if type(testName) is list else soundex(testName)
            soundAgent = soundex(agntDirector)
            matchedName = True if soundAgent in soundIAFD else False
            if matchedName:
                log('UTILS :: SoundEx Match:               \tUse %s on IAFD', testNameType)
                log('UTILS ::                              \tIAFD Director Name   : %s', testName)
                log('UTILS ::                              \tAgent Director Name  : %s', agntDirector)
                log('UTILS ::                              \tSound Scores I:A     :{%s:%s}', soundIAFD, soundAgent)
                log('UTILS ::                              \tMatched              : %s', matchedName)
                break

            # 8th Soundex Matching on Director Alias
            if testAlias:
                soundIAFD = [soundex(x) for x in testAlias] if type(testAlias) is list else soundex(testAlias)
                soundAgent = soundex(agntDirector)
                matchedName = True if soundAgent in soundIAFD else False
                if matchedName:
                    log('UTILS :: SoundEx Match:               \tUse %s on IAFD', testNameType)
                    log('UTILS ::                              \tIAFD Director Alias : %s', testAlias)
                    log('UTILS ::                              \tAgent Director Name : %s', agntDirector)
                    log('UTILS ::                              \tSound Scores I:A    :{%s:%s}', soundIAFD, soundAgent)
                    log('UTILS ::                              \tMatched             : %s', matchedName)
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
            log('UTILS :: [%s] Director Found named %s on IAFD %s', directorsFound, agntDirector, '[Skipping: too many found]' if directorsFound > 5 else '')
            if directorsFound > 5:
                continue

            for director in directorList:
                # get director details and compare to Agent director
                try:
                    directorName = director.xpath('./td[2]/a/text()[normalize-space()]')[0]
                    compareDirectorName = re.sub(r'[\W\d_]', '', directorName).strip().lower()
                    log('UTILS :: Director:                    \t%s / %s', directorName, compareDirectorName)

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
                    log('UTILS :: Error: Could not read Director Alias')

                try:
                    startCareer = int(director.xpath('./td[4]/text()[normalize-space()]')[0]) # set start of career
                except:
                    startCareer = 0
                    log('UTILS :: Error: Could not read Director Start Career')

                try:
                    endCareer = int(director.xpath('./td[5]/text()[normalize-space()]')[0])   # set end of career
                except:
                    endCareer = 0
                    log('UTILS :: Error: Could not read Director End Career')

                # match iafd row with Agent Director entry
                matchedDirector = True if compareAgntDirector == compareDirectorName else False

                if not matchedDirector and directorAliasList:
                    matchedItem = [i for (i, x) in enumerate(compareDirectorAliasList) if x == compareAgntDirector]
                    matchedDirector = True if matchedItem else False

                # only perform career checks if title is not a compilation and we have not filtered the search results by the Film Year
                if not matchedDirector and FILMDICT['Compilation'] == "No" and useFullCareer:
                    matchedDirector = (startCareer <= FILMDICT['Year'] <= endCareer)

                if not matchedDirector:
                    log('UTILS :: Error: Could not match Director: %s', agntDirector)
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
                        log('UTILS :: Skipping: Recorded Director Name: %s AKA %s also known by this name: %s', checkName, checkAlias, directorName)
                        matchedDirectorDict.pop(agntDirector)
                        break

                if matchedDirectorWithIAFD:
                    break

                # we have an director who matches the conditions
                directorURL = IAFD_BASE + director.xpath('./td[2]/a/@href')[0]
                directorPhoto = director.xpath('./td[1]/a/img/@src')[0] # director name on agent website - retrieve picture
                directorPhoto = '' if 'th_iafd_ad.gif' in directorPhoto else directorPhoto.replace('thumbs/th_', '')

                log('UTILS :: Alias:                       \t%s', directorAliasList)
                log('UTILS :: Start Career:                \t%s', startCareer)
                log('UTILS :: End Career:                  \t%s', endCareer)
                log('UTILS :: Director URL:                \t%s', directorURL)
                log('UTILS :: Director Photo:              \t%s', directorPhoto)

                # Assign values to dictionary
                myDict = {}
                myDict['Photo'] = directorPhoto
                myDict['Alias'] = directorAliasList
                myDict['CompareName'] = compareDirectorName
                myDict['CompareAlias'] = compareDirectorAliasList
                matchedDirectorDict[agntDirector] = myDict

                log(LOG_SUBLINE)
                break   # break out to next director in agent director list

        except Exception as e:
            log('UTILS :: Error: Cannot Process IAFD Director Search Results: %s', e)
            log(LOG_SUBLINE)
            continue    # next director in agent director list  (allDirectorList)

    return matchedDirectorDict

# -------------------------------------------------------------------------------------------------------------------------------
def matchFilename(filmPath, filmDuration):
    ''' Check filename on disk corresponds to regex preference format '''
    filmVars = {}
    filmVars['Agent'] = PLUGIN_LOG_TITLE

    # file matching pattern
    filmVars['FileFolder'], filmVars['FileName'] = os.path.split(os.path.splitext(filmPath)[0])
    log('Filename %s', filmVars['FileName'])

    pattern = re.compile(r' -\s?(cd|disc|disk|dvd|part|pt|scene)\s?[1-8].*$', re.IGNORECASE)
    matched = re.search(pattern, filmVars['FileName'])  # match against end of string
    filmVars['Stacked'] = 'Yes' if matched else 'No'

    REGEX = '^\((?P<Studio0>.+)\) - (?P<Title0>.+) \((?P<Year0>\d{4})\) (-\s?(cd|disc|disk|dvd|part|pt|scene)\s?[1-8].*$)?|^\((?P<Studio1>.+)\) - (?P<Title1>.+) (-\s?(cd|disc|disk|dvd|part|pt|scene)\s?[1-8].*$)?'
    pattern = re.compile(REGEX)
    matched = pattern.search(filmVars['FileName'])
    if not matched:
        raise Exception('<File Name [{0}] not in the expected format: (Studio) - Title (Year)>'.format(filmVars['FileName']))

    groups = matched.groupdict()
    filmVars['Format'] = '(Studio) - Title' if groups['Year0'] is None else '(Studio) - Title (Year)'
    filmVars['FileStudio'] = groups['Studio1'] if groups['Year0'] is None else groups['Studio0']
    filmVars['Studio'] = filmVars['FileStudio'].split(';')[0].strip() if ';' in filmVars['FileStudio'] else filmVars['FileStudio']
    filmVars['CompareStudio'] = NormaliseComparisonString(filmVars['Studio'])
    filmVars['IAFDStudio'] = filmVars['FileStudio'].split(';')[1].strip() if ';' in filmVars['FileStudio'] else ''
    filmVars['CompareIAFDStudio'] = NormaliseComparisonString(filmVars['IAFDStudio']) if filmVars['IAFDStudio'] else ''

    filmVars['Title'] =  groups['Title1'] if groups['Year0'] is None else groups['Title0']
    filmVars['SearchTitle'] = filmVars['Title']
    filmVars['ShortTitle'] = filmVars['Title']
    filmVars['CompareTitle'] = [SortAlphaChars(NormaliseComparisonString(filmVars['ShortTitle']))]

    # if film starts with a determinate, strip the detrminate and add the title to the comparison list
    pattern = ur'^(The |An |A )'
    matched = re.search(pattern, filmVars['ShortTitle'], re.IGNORECASE)  # match against whole string
    if matched:
        filmVars['CompareTitle'].append(SortAlphaChars(NormaliseComparisonString(re.sub(pattern, '', filmVars['ShortTitle'], flags=re.IGNORECASE))))

    filmVars['IAFDTitle'] =  makeASCII(filmVars['Title'])
    filmVars['IAFDCompareTitle'] = filmVars['CompareTitle']

    filmVars['Year'] = groups['Year0'] if groups['Year0'] is not None else ''
    # default to 31 Dec of Filename year if Year provided in filename and is not 1900
    filmVars['CompareDate'] = datetime(int(filmVars['Year']), 12, 31).strftime(DATEFORMAT) if filmVars['Year'] else ''

    # film duration
    filmVars['Duration'] = filmDuration / 60000 if filmDuration != None else '' # Converting from ms to mins

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
    filmVars['Title'] = filmVars['Title'] if '- ' not in filmVars['Title'] else re.sub(ur' - |- ', ': ', filmVars['Title']) # put colons back in as they can't be used in the filename
    pattern = ur'[' + re.escape(''.join(['.', '!', '%', '?'])) + ']+$'
    filmVars['ShortTitle'] = re.sub(pattern, '', ' '.join(splitFilmTitle).strip())                                          # strip punctuations at end of string
    if filmVars['ShortTitle'] not in filmVars['CompareTitle']:
        filmVars['CompareTitle'].append(SortAlphaChars(NormaliseComparisonString(filmVars['ShortTitle'])))
    filmVars['SearchTitle'] = filmVars['ShortTitle']
    
    # print out dictionary values / normalise unicode
    log('UTILS :: Film Dictionary Variables:')
    for key in sorted(filmVars.keys()):
        filmVars[key] = list(dict.fromkeys(filmVars[key])) if type(filmVars[key]) is list else filmVars[key]
        log('UTILS :: {0: <29}: {1}'.format(key, filmVars[key]))

    return filmVars

# ----------------------------------------------------------------------------------------------------------------------------------
def matchDuration(siteDuration, FILMDICT, matchDuration=True):
    ''' match file duration against iafd duration: Only works if ffmpeg is installed and duration recorded: Boolean Return '''
    siteDuration = siteDuration.strip()
    fileDuration = int(FILMDICT['Duration'])
    testDuration = True

    # if the siteDuration is not available, return True
    if not re.search(r'\d', siteDuration) :
        return True

    if FILMDICT['Stacked'] == 'Yes':
        testDuration = 'Skipped - Movie in Parts [Stacked]'
    elif siteDuration and matchDuration == True and fileDuration > 0:
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

    compareSiteTitle = SortAlphaChars(amendedSiteTitle)
    testTitle = 'Passed' if compareSiteTitle in FILMDICT['CompareTitle'] else 'Passed (IAFD)' if compareSiteTitle in FILMDICT['IAFDCompareTitle'] else 'Failed'

    log('UTILS :: Site Title                    %s', siteTitle)
    log('UTILS :: Amended Site Title            %s', amendedSiteTitle)
    log('UTILS :: File Title                    %s', FILMDICT['Title'])
    log('UTILS :: File Short Title              %s', FILMDICT['ShortTitle'])
    log('UTILS :: Amended Short Title           %s', amendedShortTitle)
    log('UTILS :: Compare Site Title            %s', compareSiteTitle)
    log('UTILS ::         Agent Title           %s', FILMDICT['CompareTitle'])
    log('UTILS ::         IAFD Title            %s', FILMDICT['IAFDCompareTitle'])
    log('UTILS :: Title Comparison Test         [%s]', testTitle)

    if testTitle == 'Failed':
        raise Exception('<Title Match Failure!>')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def matchTitleActors(siteTitle, FILMDICT):
    ''' match file title against website/iafd title: Boolean Return '''

    siteTitleActorList = re.findall('\\b[A-Z]\\w*', siteTitle, re.UNICODE)
    siteTitleActors = ' '.join(siteTitleActorList)
    shortTitleActorList = re.findall('\\b[A-Z]\\w*', FILMDICT['ShortTitle'], re.UNICODE)
    shortTitleActors = ' '.join(shortTitleActorList)

    compareSiteActors = SortAlphaChars(NormaliseComparisonString(siteTitleActors))
    compareShortActors = SortAlphaChars(NormaliseComparisonString(shortTitleActors))

    testActors = 'Passed' if compareSiteActors == compareShortActors else 'Failed'

    log('UTILS :: Site Actors                    %s', siteTitleActors)
    log('UTILS :: Title Actors                  %s', shortTitleActors)
    log('UTILS :: Title Comparison Test         [%s]', testActors)

    if testActors == 'Failed':
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
    pattern = ur'[.]([a-z]{2,3}|co[.][a-z]{2})|Vol[.]|Vols[.]|\bVolume\b|\bVolumes\b|(?<!\d)1(?!\d)|\bPart\b|[^A-Za-z0-9]+'
    myString = re.sub(pattern, '', myString, flags=re.IGNORECASE)

    return myString

# ----------------------------------------------------------------------------------------------------------------------------------
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
def SortAlphaChars(myString):
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
        msg = 'Run Translation: [{0}] - Site Language: [{1}] to Library Language: [{2}]'.format(runTranslation, dictLanguages.get(siteLanguage), language)
        if detectLanguage and runTranslation == 'No':
            try:
                detectString = re.findall(ur'.*?[.!?]', myString)[:4]   # take first 4 sentences of string to detect language
                detectString = ''.join(detectString)
                if detectString:
                    detectedTextLanguage = translator.detect(detectString)
                    runTranslation = 'Yes' if language != detectedTextLanguage else 'No'
                    msg = 'Run Translation: [{0}] - Detected Language: [{1}] to Library Language: [{2}]'.format(runTranslation, detectedTextLanguage, language)
                else:
                    msg = 'Run Translation: [{0}] - Not enough available text to detect language'.format(runTranslation)
            except Exception as e:
                log('UTILS :: Error Detecting Text Language: %s', e)

        log('UTILS :: %s', msg)

        if runTranslation == 'Yes':
            if language is not None:
                try:
                    myString = translator.translate(myString, language)
                    myString = saveString if myString is None else myString
                    log('UTILS :: %s Text: %s', 'Untranslated' if myString == saveString else 'Translated', myString)
                except Exception as e:
                    log('UTILS :: Error Translating Text: %s', e)
            else:
                log('UTILS :: Translation Skipped: Language Code [%s] not recognised', plexLibLanguageCode)

    myString = myString if myString else ' ' # return single space to initialise metadata summary field
    return myString