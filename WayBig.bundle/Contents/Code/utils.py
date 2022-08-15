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
    05 Jun 2022     Error - incomplete raise statement in getCast and getDirectors
                    new routines to scrape chapter info from aebn, dvdgayempire and gay hot movies
    14 Jul 2022     New routines to implement Tidy Genres, Countries Collation, processing set and date time data via json
                    simplified routine to match cast and directors
                    improved logging
                    added routines to read tidy genres and country files from the plug-ins directory
                    use of sets to improve processing speed and reduce error logging
'''
# ----------------------------------------------------------------------------------------------------------------------------------
import cloudscraper, fake_useragent, os, platform, re, subprocess, unicodedata
from datetime import datetime, timedelta
from unidecode import unidecode
from urlparse import urlparse

# IAFD Related variables
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/results.asp?searchtype=comprehensive&searchstring={0}'
IAFD_ABSENT = u'\U0000274C'        # red cross mark - not on IAFD
IAFD_FOUND = u'\U00002705'         # heavy white tick on green - on IAFD

# Plex System Variables/Methods
PlexSupportPath = Core.app_support_path
PlexLoadFile = Core.storage.load

# log section separators
LOG_BIGLINE = '----------------------------------------------------------------------------------'
LOG_SUBLINE = '      ----------------------------------------------------------------------------'
LOG_ASTLINE = '**********************************************************************************'

# getHTTPRequest variable
scraper = None

# ----------------------------------------------------------------------------------------------------------------------------------
def anyOf(iterable):
    '''  used for matching strings in lists '''
    for element in iterable:
        if element:
            return element
    return None

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
def getSiteInfo(myAgent, html, webURL, FILMDICT):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information from Selected Website'''
    siteInfoDict = {}
    log(LOG_BIGLINE)
    listHeaders = [' << {0}: Get Site Information >> '.format(myAgent), 
                   ' ({0}) - {1} ({2}) >> '.format(FILMDICT['Studio'], FILMDICT['Title'], FILMDICT['Year']),
                   ' {0} '.format(webURL)]
    for header in listHeaders:
        log('UTILS :: %s', header.center(72, '*'))
    log(LOG_BIGLINE)

    if myAgent == 'AEBNiii':
        siteInfoDict = getSiteInfoAEBNiii(myAgent, html, webURL, FILMDICT)
    elif myAgent == 'GayDVDEmpire':
        siteInfoDict = getSiteInfoGayDVDEmpire(myAgent, html, webURL, FILMDICT)
    elif myAgent == 'GayHotMovies':
        siteInfoDict = getSiteInfoGayHotMovies(myAgent,html, webURL, FILMDICT)

    footer = ' >> {0}: Site Information Retrieved << '.format(myAgent)
    log('UTILS :: %s', footer.center(72, '*'))
    return siteInfoDict
# -------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoAEBNiii(myAgent, html, webURL, FILMDICT):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    siteInfoDict = {}
    try:
        #   1.  Release Date - AEBN Format = mmm dd, YYYY
        try:
            htmldate = html.xpath('//li[@class="section-detail-list-item-release-date"]/text()[normalize-space()]')[0].strip()
            htmldate = htmldate.replace('July', 'Jul').replace('Sept', 'Sep')    # AEBN uses 4 letter abbreviation for September
            htmldate = datetime.strptime(htmldate, '%b %d, %Y')
            siteInfoDict['ReleaseDate'] = htmldate
            log('UTILS :: {0:<29} {1}'.format('Release Date', htmldate.strftime('%Y-%m-%d')))

        except Exception as e:
            siteInfoDict['ReleaseDate'] = datetime.fromtimestamp(0)
            log('UTILS :: Error getting Release Date: %s', e)

        #   2.  Duration - AEBN Format = HH:MM:SS optional HH
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

        #   3.  Genres, Countries and Compilation
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
                newItem = TIDYDICT[item] if item in TIDYDICT else ''
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem in COUNTRYSET:
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem if newItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation', compilation))


        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   4.  Poster and Art URLs
        log(LOG_SUBLINE)
        try:
            htmlimages = html.xpath('//*[contains(@class,"dts-movie-boxcover")]//img/@src')
            htmlimages = [x.split('?')[0] for x in htmlimages]
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

        #   5.  Scene Info
        log(LOG_SUBLINE)
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
                        mySource = 'AEBN'
                        reviewSource = htmlscene.xpath('./ul/li/span/a[contains(@href, "/stars/")]/text()')
                        reviewSource = [x.split('(')[0] for x in reviewSource]
                        reviewSource = ', '.join(reviewSource)

                    except Exception as e:
                        log('UTILS :: Error getting Review Source (Cast): %s', e)
                        if 'Scenes' in FILMDICT and FILMDICT['Scenes']:
                            mySource = 'IAFD'
                            reviewSource = FILMDICT['Scenes'].split('##')[sceneNo - 1]
                            reviewSource = reviewSource .split('. ')[1]
                        else:
                            log('UTILS :: Warning No Review Source (IAFD Cast): %s', e)

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
                    reviewAuthor = ''
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
                            newItem = TIDYDICT[item] if item in TIDYDICT else ''
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
                    scenesDict[sceneNo] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText, 'Link': webURL}

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

        #   6.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//li[@class="section-detail-list-item-director"]/span/a/span/text()')
            htmldirectors = ['{0}'.format(x.strip()) for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   7.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//div[@class="dts-star-name-overlay"]/text()')
            htmlcast = ['{0}'.format(x.strip()) for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   8.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//div[@class="dts-section-page-detail-description-body"]/text()')[0].strip()
            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Synopsis'), htmlsynopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = []
            log('UTILS :: Error getting Synopsis: %s', e)

        #   9.  Collections
        log(LOG_SUBLINE)
        try:
            htmlcollections = html.xpath('//li[@class="section-detail-list-item-series"]/span/a/span/text()')
            htmlcollections = [x for x in htmlcollections if x.strip()]
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Collections'), '{0:>2} {1}'.format(len(htmlcollections), htmlcollections)))
            listCollections = [x for x in htmlcollections if x.lower() not in (y.lower() for y in FILMDICT['Collection'])]
            collections = list(set(listCollections))
            collections.sort(key = lambda x: x.lower())
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Collections (unique)'), '{0:>2} {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = collections[:]
            log('UPDATE:: Error getting Collections: %s', e)

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoGayDVDEmpire(myAgent, html, webURL, FILMDICT):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information '''
    siteInfoDict = {}
    try:
        #   1.  Release Date - GayDVDEmpire Format = mmm dd YYYY
        #       First retrieve Production Year, then if release date is within the same year use it as the plex release date as it has month and day data
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
            siteInfoDict['ReleaseDate'] = datetime.fromtimestamp(0)
            log('UTILS :: Error getting Release Date: %s', e)

        #   2.  Duration - GayDVDEmpire Format = h hrs. m mins.
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

        #   3.  Genres, Countries and Compilation
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
                newItem = TIDYDICT[item] if item in TIDYDICT else ''
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem in COUNTRYSET:
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem if newItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation', compilation))


        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   4.  Poster and Art URLs
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

        #   5.  Scene Info
        log(LOG_SUBLINE)
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
                    reviewSource = ''
                    if 'Scenes' in FILMDICT and FILMDICT['Scenes']:
                        mySource = 'IAFD: '
                        reviewSource = FILMDICT['Scenes'].split('##')[sceneNo - 1]
                        reviewSource = castList.split('. ')[1]
                    else:
                        log('UTILS :: Warning No Review Source (IAFD Cast)')

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
                    scenesDict[sceneNo] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText, 'Link': webURL}

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

        #   6.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//a[contains(@label, "Director - details")]/text()[normalize-space()]')
            htmldirectors = ['{0}'.format(x.strip()) for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   7.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//a[@class="PerformerName" and @label="Performers - detail"]/text()')
            htmlcast = ['{0}'.format(x.strip()) for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   8.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//div[@class="col-xs-12 text-center p-y-2 bg-lightgrey"]/div/p')[0].text_content()
            htmlsynopsis = re.sub('<[^<]+?>', '', htmlsynopsis).strip()
            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Synopsis'), htmlsynopsis))
        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   9.  Collections: none recorded on this website
        log(LOG_SUBLINE)
        try:
            htmlcollections = html.xpath('//a[contains(@label, "Series")]/text()[normalize-space()]')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            htmlcollections = [x.replace('"', '').replace('Series', '').strip() for x in htmlcollections]
            collections = list(set(htmlcollections))
            collections.sort(key = lambda x: x.lower())
            siteInfoDict['Collections'] = collections[:]
            log('UTILS :: {0:<29} {1}'.format('Collections', '{0:>2} - {1}'.format(len(collections), collections)))

        except Exception as e:
            siteInfoDict['Collections'] = ''
            log('UPDATE:: Error getting Collections: %s', e)

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
def getSiteInfoGayHotMovies(myAgent, html, webURL, FILMDICT):
    ''' get Release Date, Genres, Countries, IsCompilation, Poster & Art Images, Scene and Chapter information    '''
    siteInfoDict = {}
    try:
        #   1.  Release Date - GayHotMovies = YYYY-mm-dd
        #       First retrieve Production Year format YYYY, then if release date is within the same year use it as the plex release date as it has month and day data
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
            siteInfoDict['ReleaseDate'] = datetime.fromtimestamp(0)
            log('UTILS :: Error getting Release Date: %s', e)

        #   2.  Duration - GayHotMovies Format = HH:MM:SS
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

        #   3.  Genres, Countries and Compilation
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
                newItem = TIDYDICT[item] if item in TIDYDICT else ''
                log('UTILS :: {0:<29} {1}'.format('Item: Old :: New', '{0:>2} - {1:<25} :: {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem in COUNTRYSET:
                    countriesSet.add(newItem)
                    continue

                genresSet.add(newItem if newItem else item)

            showSetData(countriesSet, 'Countries (set*)')
            showSetData(genresSet, 'Genres (set*)')
            log('UTILS :: {0:<29} {1}'.format('Compilation', compilation))

        except Exception as e:
            log('UTILS :: Error getting Genres/Countries: %s', e)

        finally:
            siteInfoDict['Genres'] = genresSet
            siteInfoDict['Countries'] = countriesSet
            siteInfoDict['Compilation'] = compilation

        #   4.  Poster and Art URLs
        #       there are 3 ways front/art images are stored on gay hot movies - end with h.jpg for front and bh.jpg for art
        #                                                                      - end xfront.1.jpg for front and xback.1.jpg for art - these first two use the same xpath
        #                                                                      - just one image (old style)
        log(LOG_SUBLINE)
        try:
            htmlimage = html.xpath('//div[@class="lg_inside_wrap"]/@data-front')[0]
            poster = htmlimage
            htmlimage = html.xpath('//div[@class="lg_inside_wrap"]/@data-back')[0]
            art = htmlimage.replace('h.jpg', 'bh.jpg')

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

        #   5.  Scene Info
        log(LOG_SUBLINE)
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
                        mySource = 'GayHotMovies'
                        reviewSource = htmlscene.xpath('./div/span[@class="scene_stars"]/a/text()[normalize-space()]')
                        reviewSource = [x.split('(')[0] for x in reviewSource]
                        reviewSource = ', '.join(reviewSource)

                    except Exception as e:
                        log('UTILS :: Error getting Review Source (Cast): %s', e)
                        if 'Scenes' in FILMDICT and FILMDICT['Scenes']:
                            mySource = 'IAFD'
                            reviewSource = FILMDICT['Scenes'].split('##')[sceneNo - 1]
                            reviewSource = reviewSource .split('. ')[1]
                        else:
                            log('UTILS :: Warning No Review Source (IAFD Cast)')

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
                            newItem = TIDYDICT[item] if item in TIDYDICT else ''
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
                    scenesDict[sceneNo] = {'Author': reviewAuthor, 'Source': reviewSource, 'Text': reviewText, 'Link': webURL}

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

        #   6.  Directors
        log(LOG_SUBLINE)
        try:
            htmldirectors = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/director/")]/span/text()[normalize-space()]')
            htmldirectors = ['{0}'.format(x.strip()) for x in htmldirectors if x.strip()]
            directors = list(set(htmldirectors))
            directors.sort(key = lambda x: x.lower())
            siteInfoDict['Directors'] = directors[:]
            log('UTILS :: {0:<29} {1}'.format('Director(s)', '{0:>2} - {1}'.format(len(directors), directors)))

        except Exception as e:
            siteInfoDict['Directors'] = []
            log('UTILS :: Error getting Director(s): %s', e)

        #   7.  Cast
        log(LOG_SUBLINE)
        try:
            htmlcast = html.xpath('//div[@class="name"]/a/text()[normalize-space()]')
            htmlcast = ['{0}'.format(x.strip()) for x in htmlcast if x.strip()]
            cast = list(set(htmlcast))
            cast.sort(key = lambda x: x.lower())
            siteInfoDict['Cast'] = cast[:]
            log('UTILS :: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(cast), cast)))

        except Exception as e:
            siteInfoDict['Cast'] = []
            log('UTILS :: Error getting Cast: %s', e)

        #   8.  Synopsis
        log(LOG_SUBLINE)
        try:
            htmlsynopsis = html.xpath('//span[contains(@class,"video_description")]//text()')[0]
            htmlsynopsis = re.sub('<[^<]+?>', '', htmlsynopsis).strip()

            regex = r'The movie you are enjoying was created by consenting adults.*'
            pattern = re.compile(regex, re.DOTALL | re.IGNORECASE)
            htmlsynopsis = re.sub(pattern, '', htmlsynopsis)

            siteInfoDict['Synopsis'] = htmlsynopsis
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Synopsis'), htmlsynopsis))

        except Exception as e:
            siteInfoDict['Synopsis'] = ''
            log('UTILS :: Error getting Synopsis: %s', e)

        #   9.  Collections
        log(LOG_SUBLINE)
        try:
            htmlcollections = html.xpath('//a[contains(@href,"https://www.gayhotmovies.com/series/")]/text()[normalize-space()]')
            htmlcollections = [x.strip() for x in htmlcollections if x.strip()]
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Collections'), '{0:>2} {1}'.format(len(htmlcollections), htmlcollections)))
            listCollections = [x for x in htmlcollections if x.lower() not in (y.lower() for y in FILMDICT['Collection'])]
            collections = list(set(listCollections))
            collections.sort(key = lambda x: x.lower())
            log('UTILS :: {0: <29} {1}'.format('{0}:'.format('Collections (unique)'), '{0:>2} {1}'.format(len(collections), collections)))
            siteInfoDict['Collections'] = collections[:]

        except Exception as e:
            siteInfoDict['Collections'] = collections[:]
            log('UPDATE:: Error getting Collections: %s', e)

    finally:
        return siteInfoDict if siteInfoDict != {} else None

# ----------------------------------------------------------------------------------------------------------------------------------
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
    DxWidth = '{0:>2}'.format(DxWidth)    # percent format
    DxHeight = '{0:>2}'.format(DxHeight)  # percent format
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
                    picContent = PlexLoadFile(pic)
                    cropped = True
            except Exception as e:
                log('UTILS :: Error Script Failed to Crop Image to: {0} x {1}'.format(desiredWidth, desiredHeight))

    if not cropped:
        picContent = HTTP.Request(pic).content

    return pic, picContent

# -------------------------------------------------------------------------------------------------------------------------------
def getFilmOnIAFD(FILMDICT):
    ''' check IAFD web site for better quality thumbnails per movie'''
    FILMDICT['AllFemale'] = 'No'
    FILMDICT['AllMale'] = 'Yes'  # default to yes as this is usually used on gay websites.
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
    FILMDICT['IAFDSearchTitle'] = FILMDICT['IAFDTitle'] if 'Agent' in FILMDICT and FILMDICT['Agent'] != 'IAFD' else FILMDICT['IAFDTitle'].split(':')[0]
    FILMDICT['IAFDSearchTitle'] = String.StripDiacritics(FILMDICT['IAFDSearchTitle']).strip()
    FILMDICT['IAFDSearchTitle'] = String.URLEncode(FILMDICT['IAFDSearchTitle'])
    FILMDICT['IAFDSearchTitle'] = FILMDICT['IAFDSearchTitle'].replace('%25', '%').replace('*', '')

    # search for Film Title on IAFD
    log(LOG_BIGLINE)
    listHeaders = [' << IAFD: Get Site Information >> ', ' ({0}) - {1} ({2}) '.format(FILMDICT['Studio'], FILMDICT['Title'], FILMDICT['Year'])]
    for header in listHeaders:
        log('UTILS :: %s', header.center(72, '*'))
    log(LOG_BIGLINE)

    try:
        html = getURLElement(IAFD_SEARCH_URL.format(FILMDICT['IAFDSearchTitle']), UseAdditionalResults=True)

        # get films listed within 1 year of what is on agent - as IAFD may have a different year recorded
        filmList = []
        if 'Year' in FILMDICT and FILMDICT['Year']:
            myYear = int(FILMDICT['Year'])
            filmList = html.xpath('//table[@id="titleresult"]/tbody/tr/td[2][.>="{0}" and .<="{1}"]/ancestor::tr'.format(myYear - 1, myYear + 1))
            filmListLength = len(filmList)
            log('UTILS :: Films found on IAFD           {0} between the years [{1}] and [{2}]'.format(filmListLength, myYear - 1, myYear + 1))

        if not filmList:
            filmList = html.xpath('//table[@id="titleresult"]/tbody/tr')
            filmListLength = len(filmList)
            log('UTILS :: Films found on IAFD           {0}'.format(filmListLength))

        log(LOG_BIGLINE)
        for idx, film in enumerate(filmList, start=1):
            log('SEARCH:: {0:<29} {1}'.format('Processing', '{0} of {1}'.format(idx, filmListLength)))

            # Site Title and Site AKA
            log(LOG_BIGLINE)
            try:
                iafdTitle = film.xpath('./td[1]/a/text()')[0].strip()
                # IAFD sometimes adds (I), (II), (III) to differentiate scenes from full movies - strip these out before matching - assume a max of 19 (XIX)
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
                    matchStudio(studio, FILMDICT) # if an IAFD Studio was recorded on the filename - set last param to false
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
            try:
                iafdDuration = html.xpath('//p[@class="bioheading" and text()="Minutes"]//following-sibling::p[1]/text()')[0].strip()
                hh, mm = divmod(int(iafdDuration), 60)                                                      # convert minutes to hh:mm
                iafdDuration = [hh, mm, 0]
                iafdDuration = ['0{0}'.format(x) if x < 10 else '{0}'.format(x) for x in iafdDuration]      # convert to zero padded items
                iafdDuration = '1970-01-01 {0}'.format(':'.join(iafdDuration))                              # prefix with 1970-01-01 to conform to timestamp
                iafdDuration = datetime.strptime(iafdDuration, '%Y-%m-%d %H:%M:%S')                         # turn to date time object
                FILMDICT['IAFDDuration'] = iafdDuration
                matchDuration(iafdDuration, FILMDICT)

            except Exception as e:
                log('UTILS :: Error: getting IAFD Duration: %s', e)
                log(LOG_SUBLINE)
                if MATCHIAFDDURATION:   # if preference selected go to next
                    continue

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
                # if already set to yes by possible checking of external sources [AEBN, GayDVDMovies, GayHotMovies], dont change with IAFD value
                if 'Compilation' in FILMDICT and FILMDICT['Compilation'] == 'No':
                    FILMDICT['Compilation'] = html.xpath('//p[@class="bioheading" and text()="Compilation"]//following-sibling::p[1]/text()')[0].strip()
                    log('UTILS :: IAFD: Film Compilation?:      %s', FILMDICT['Compilation'])
                else:
                    log('UTILS :: IAFD: Externally Set:         %s', FILMDICT['Compilation'])
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
                FILMDICT['Scenes'] = '##'.join(htmlscenes)
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

            footer = ' >> IAFD: Site Information Retrieved << '
            log('UTILS :: %s', footer.center(72, '*'))

            break
    except Exception as e:
        log('UTILS :: Error: IAFD Film Search Failure, %s', e)

    # set up the the legend that can be prefixed/suffixed to the film summary
    IAFD_ThumbsUp = u'\U0001F44D'      # thumbs up unicode character
    IAFD_ThumbsDown = u'\U0001F44E'    # thumbs down unicode character
    IAFD_Stacked = u'\u2003Stacked \U0001F4FD\u2003::'
    agentName = u'\u2003{0}\u2003::'.format(FILMDICT['Agent'])
    IAFD_Legend = u'::\u2003Film on IAFD {2}\u2003::\u2003{1} / {0} Actor on Cast List?\u2003::{3}{4}'
    presentOnIAFD = IAFD_ThumbsUp if 'FoundOnIAFD' in FILMDICT and FILMDICT['FoundOnIAFD'] == 'Yes' else IAFD_ThumbsDown
    stackedStatus = IAFD_Stacked if 'Stacked' in FILMDICT and FILMDICT['Stacked'] == 'Yes' else ''
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
            castURL = IAFD_BASE + cast.xpath('./a/@href')[0].strip()
            castPhoto = cast.xpath('./a/img/@src')[0].strip()
            castPhoto = '' if 'nophoto' in castPhoto or 'th_iafd_ad' in castPhoto else castPhoto

            # cast roles are sometimes not filled in
            try:
                castRole = cast.xpath('./text()[normalize-space()]')
                castRole = ' '.join(castRole).strip()
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
def getURLElement(myString, UseAdditionalResults):
    ''' check IAFD web site for better quality thumbnails irrespective of whether we have a thumbnail or not '''
    msg = ''    # this variable will be set if IAFD fails to be read
    html = ''
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
    log('%s::  > Initialise Collections:    %s', myFunc, COLCLEAR)
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
                   ' ({0}) - {1} ({2}) >> '.format(FILMDICT['Studio'], FILMDICT['Title'], FILMDICT['Year'])]:
        log('%s :: %s', myFunc, footer.center(72, '*'))
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
def matchCast(agntCastList, FILMDICT):
    ''' check IAFD web site for individual cast'''
    matchedCastDict = {}

    myYear = int(FILMDICT['Year']) if 'Year' in FILMDICT and FILMDICT['Year'] else ''

    for agntCast in agntCastList:
        compareAgntCast = re.sub(r'[\W\d_]', '', agntCast).strip().lower()
        log('UTILS :: {0:<29} {1}'.format('Unmatched Cast Name', agntCast))

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
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Cast: Full Match - Cast Name', agntCast))
                matchedName = True
                break

            # 2nd full match against Cast Alias
            if compareAgntCast == IAFDCompareAlias:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Cast: Full Match - Cast Alias', agntCast))
                matchedName = True
                break

            # 3rd partial match against Cast Name
            if compareAgntCast in IAFDCompareName:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Cast: Partial Match - Cast Name', agntCast))
                matchedName = True
                break

            # 4th partial match against Cast Alias
            if compareAgntCast in IAFDCompareAlias:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Cast: Partial Match - Cast Alias', agntCast))
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
                log('UTILS :: {0:<29} {1}'.format('Levenshtein Match', testNameType))
                log('UTILS :: {0:<29} {1}'.format('  IAFD Cast Name', testName))
                log('UTILS :: {0:<29} {1}'.format('  Agent Cast Name', agntCast))
                log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(levScore, levDistance)))
                log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                break

            # 6th Lehvenstein Match against Cast Alias
            if testAlias:
                levScore = String.LevenshteinDistance(agntCast, testAlias)
                matchedName = levScore <= levDistance
                if matchedName:
                    log('UTILS :: {0:<29} {1}'.format('Levenshtein Match', testNameType))
                    log('UTILS :: {0:<29} {1}'.format('  IAFD Cast Alias', testAlias))
                    log('UTILS :: {0:<29} {1}'.format('  Agent Cast Name', agntCast))
                    log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(levScore, levDistance)))
                    log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                    break

            # 7th Soundex Matching on Cast Name
            soundIAFD = soundex(testName)
            soundAgent = soundex(agntCast)
            matchedName = soundIAFD == soundAgent
            if matchedName:
                log('UTILS :: {0:<29} {1}'.format('SoundEx Match', testNameType))
                log('UTILS :: {0:<29} {1}'.format('  IAFD Cast Name', testName))
                log('UTILS :: {0:<29} {1}'.format('  Agent Cast Name', agntCast))
                log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(soundIAFD, soundAgent)))
                log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                break

            # 8th Soundex Matching on Cast Alias
            if testAlias:
                soundIAFD = soundex(testAlias)
                soundAgent = soundex(agntCast)
                matchedName = soundIAFD == soundAgent
                if matchedName:
                    log('UTILS :: {0:<29} {1}'.format('SoundEx Match', testNameType))
                    log('UTILS :: {0:<29} {1}'.format('  IAFD Cast Alias', testAlias))
                    log('UTILS :: {0:<29} {1}'.format('  Agent Cast Name', agntCast))
                    log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(soundIAFD, soundAgent)))
                    log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                    break

        if matchedName: # we have a match, on to the next cast
            continue

        # the cast on the website has not matched to those listed against the film in IAFD. So search for the cast's entry on IAFD
        matchedCastDict[agntCast] = {'Photo': '', 'Role': IAFD_ABSENT, 'Alias': '', 'CompareName': '', 'CompareAlias': ''} # initialise cast member's dictionary
        xPathMale = '//table[@id="tblMal"]/tbody/tr'
        xPathFemale = '//table[@id="tblFem"]/tbody/tr'
        if 'AllMale' in FILMDICT and FILMDICT['AllMale'] == 'Yes':
            xPath = xPathMale
        elif 'AllFemale' in FILMDICT and FILMDICT['AllFemale'] == 'Yes':
            xPath = xPathFemale
        else:
            xPath = '{0}|{1}'.format(xPathMale, xPathFemale)

        try:
            html = getURLElement(IAFD_SEARCH_URL.format(String.URLEncode(agntCast)), UseAdditionalResults=False)
            castList = html.xpath(xPath)
            log('UTILS :: {0:<29} {1}'.format('{0} Cast XPath'.format('Male' if 'tblMal' in xPath else 'Female'), xPath))

            castFound = len(castList)
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Cast Found'), '{0:>2}'.format(castFound, 'Skipping: Too Many Cast Names Returned' if castFound > 30 else '' )))

            log(LOG_BIGLINE)
            for cast in castList:
                # get cast details and compare to Agent cast
                try:
                    castName = cast.xpath('./td[2]/a/text()[normalize-space()]')[0]
                    compareCastName = re.sub(r'[\W\d_]', '', castName).strip().lower()
                    log('UTILS :: {0:<29} {1}'.format('Cast Name', '{0} / {1}'.format(castName, compareCastName)))
                except Exception as e:
                    log('UTILS :: Error: Could not read Cast Name: %s', e)
                    continue   # next cast with

                try:
                    castAliasList = cast.xpath('./td[3]/text()[normalize-space()]')[0].split(',')
                    castAliasList = [x.strip() for x in castAliasList if x]
                    compareCastAliasList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in castAliasList]
                    log('UTILS :: {0:<29} {1}'.format('Alias', castAliasList if castAliasList else 'No Director Alias Recorded'))
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

                log('UTILS :: {0:<29} {1}'.format('Career', '{0} - {1}'.format(startCareer if startCareer > 0 else 'N/A', endCareer if endCareer > 0 else 'N/A')))

                matchedUsing = ''

                # match iafd row with Agent Cast entry
                matchedCast = True if compareAgntCast == compareCastName else False
                matchedUsing = 'Cast Name' if matchedCast else 'Failed Cast Name Matching: {0} != {1}'.format(compareAgntCast, compareCastName)

                # match iafd row with Agent Cast Alias entry
                if not matchedCast and castAliasList:
                    matchedItem = x = [x for x in compareCastAliasList if compareAgntCast in x]
                    matchedCast = True if matchedItem else False
                    matchedUsing = 'Cast Alias' if matchedCast else 'Failed Cast Alias List Matching: {0} not in {1}'.format(compareAgntCast, compareCastAliasList)

                # Check Career - if we have a match - this can only be done if the film is not a compilation and we have a Year
                # only do this if we have more than one actor returned
                if castFound > 1 and matchedCast and FILMDICT['Compilation'] == "No" and myYear:
                    matchedCast = (startCareer <= myYear <= endCareer)
                    matchedUsing = 'Career' if matchedCast else 'Failed Career Matching: {0} <= {1} <= {2}'.format(startCareer, myYear, endCareer)

                if not matchedCast:
                    log('UTILS :: {0:<29} {1}'.format('Matching', '{0} - {1}'.format(agntCast, matchedUsing)))
                    log(LOG_SUBLINE)
                    continue # to next cast in the returned iafd search cast list

                # further matching with IAFD
                matchedCastWithIAFD = False
                for key, value in FILMDICT['Cast'].items():
                    # Check if any of the Film's cast has an alias recorded against his name on the film page
                    checkName = key
                    if value['CompareAlias']:
                        checkAlias = value['Alias']
                        checkCompareAlias = value['CompareAlias']
                        if checkCompareAlias in compareCastAliasList:
                            matchedCastWithIAFD = True
                            log('UTILS :: {0:<29} {1}'.format('Skipping: Recorded Cast Name', '{0} AKA {1} also known by this name: {2}'.format(checkName, checkAlias, castName)))
                            matchedCastDict.pop(agntCast)
                            log(LOG_SUBLINE)
                            break

                # Check Cast member's page for Other Aliases he has used in other films
                castURL = IAFD_BASE + cast.xpath('./td[2]/a/@href')[0]
                if not matchedCastWithIAFD:
                    try:
                        chtml = getURLElement(castURL, UseAdditionalResults=False)
                    except Exception as e:
                        log('UTILS :: Error: Could not read Cast Page: %s', e)
                    else:
                        castPerformerAKAList = chtml.xpath('//p[@class="bioheading" and contains(.,"Performer") and contains(.,"AKA")]//following-sibling::div[@class="biodata"]/text()')[0].strip().split(', ')
                        log('UTILS :: {0:<29} {1}'.format('Other Performer AKA Names', castPerformerAKAList))
                        if agntCast in castPerformerAKAList:
                            matchedCastWithIAFD = True
                            log('UTILS :: {0:<29} {1}'.format('Skipping: Recorded Cast Name', '{0} also known as: {1}'.format(agntCast, castPerformerAKAList)))
                            matchedCastDict.pop(agntCast)
                            break

                if matchedCastWithIAFD:
                    log(LOG_SUBLINE)
                    break

                # we have an cast who satisfies the conditions
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
                myDict['Role'] = castRole
                myDict['Alias'] = ''
                myDict['CompareName'] = compareCastName
                myDict['CompareAlias'] = compareCastAliasList
                matchedCastDict[agntCast] = myDict

                log(LOG_SUBLINE)
                break   # matched - ignore any other entries

        except Exception as e:
            log('UTILS :: Error: Cannot Process IAFD Cast Search Results: %s', e)
            log(LOG_SUBLINE)


    return matchedCastDict
# ----------------------------------------------------------------------------------------------------------------------------------
def matchDirectors(agntDirectorList, FILMDICT):
    ''' check IAFD web site for individual directors'''
    matchedDirectorDict = {}

    myYear = int(FILMDICT['Year']) if 'Year' in FILMDICT and FILMDICT['Year'] else ''

    for agntDirector in agntDirectorList:
        compareAgntDirector = re.sub(r'[\W\d_]', '', agntDirector).strip().lower()
        log('UTILS :: {0:<29} {1}'.format('Unmatched Director Name', agntDirector))

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
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Director: Full Match - Director Name', agntDirector))
                matchedName = True
                break

            # 2nd full match against director alias
            if [x for x in IAFDCompareAlias if x == compareAgntDirector]:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Director: Full Match - Director Alias', agntDirector))
                matchedName = True
                break

            # 3rd partial match against director name
            if compareAgntDirector in IAFDCompareName:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Director: Partial Match - Director Name', agntDirector))
                matchedName = True
                break

            # 4th partial match against director alias
            if compareAgntDirector in IAFDCompareAlias:
                log('UTILS :: {0:<29} {1}'.format('Matched with IAFD Director: Partial Match - Director Alias', agntDirector))
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
                log('UTILS :: {0:<29} {1}'.format('Levenshtein Match', testNameType))
                log('UTILS :: {0:<29} {1}'.format('  IAFD Director Name', testName))
                log('UTILS :: {0:<29} {1}'.format('  Agent Director Name', agntDirector))
                log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(levScore, levDistance)))
                log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
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
                    log('UTILS :: {0:<29} {1}'.format('Levenshtein Match', testNameType))
                    log('UTILS :: {0:<29} {1}'.format('  IAFD Director Alias', testAlias))
                    log('UTILS :: {0:<29} {1}'.format('  Agent Director Name', agntDirector))
                    log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(levScore, levDistance)))
                    log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                    break

            # 7th Soundex Matching on Director Name
            soundIAFD = [soundex(x) for x in testName] if type(testName) is list else soundex(testName)
            soundAgent = soundex(agntDirector)
            matchedName = True if soundAgent in soundIAFD else False
            if matchedName:
                log('UTILS :: {0:<29} {1}'.format('SoundEx Match', testNameType))
                log('UTILS :: {0:<29} {1}'.format('  IAFD Director Name', testName))
                log('UTILS :: {0:<29} {1}'.format('  Agent Director Name', agntDirector))
                log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(soundIAFD, soundAgent)))
                log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                break

            # 8th Soundex Matching on Director Alias
            if testAlias:
                soundIAFD = [soundex(x) for x in testAlias] if type(testAlias) is list else soundex(testAlias)
                soundAgent = soundex(agntDirector)
                matchedName = True if soundAgent in soundIAFD else False
                if matchedName:
                    log('UTILS :: {0:<29} {1}'.format('SoundEx Match', testNameType))
                    log('UTILS :: {0:<29} {1}'.format('  IAFD Director Alias', testAlias))
                    log('UTILS :: {0:<29} {1}'.format('  Agent Director Name', agntDirector))
                    log('UTILS :: {0:<29} {1}'.format('  Score:Distance', '{0}:{1}'.format(soundIAFD, soundAgent)))
                    log('UTILS :: {0:<29} {1}'.format('  Matched', matchedName))
                    break

        if matchedName: # we have a match, on to the next director
            continue

        # the director on the website has not matched to those listed against the film in IAFD. So search for the director's entry on IAFD
        matchedDirectorDict[agntDirector] = '' # initialise director's dictionary
        try:
            html = getURLElement(IAFD_SEARCH_URL.format(String.URLEncode(agntDirector)), UseAdditionalResults=False)
            directorList = html.xpath('//table[@id="tblDir"]/tbody/tr')

            directorsFound = len(directorList)
            log('UTILS :: {0:<29} {1}'.format('{0}:'.format('Directors Found'), directorsFound))

            log(LOG_BIGLINE)
            for director in directorList:
                # get director details and compare to Agent director
                try:
                    directorName = director.xpath('./td[2]/a/text()[normalize-space()]')[0]
                    compareDirectorName = re.sub(r'[\W\d_]', '', directorName).strip().lower()
                    log('UTILS :: {0:<29} {1}'.format('Director', '{0} / {1}'.format(directorName, compareDirectorName)))
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
                matchedDirector = True if compareAgntDirector == compareDirectorName else False
                matchedUsing = 'Director Name' if matchedDirector else 'Failed Director Name Matching: {0} != {1}'.format(compareAgntDirector, compareDirectorName)

                if not matchedDirector and directorAliasList:
                    matchedItem = x = [x for x in compareDirectorAliasList if compareAgntDirector in x]
                    matchedDirector = True if matchedItem else False
                    matchedUsing = 'Director Alias' if matchedDirector else 'Directot Alias List Matching: {0} not in {1}'.format(compareAgntDirector, compareDirectorAliasList)

                # Check Career - if we have a match - this can only be done if we have a Year
                # only do this if we have more than one director returned
                if directorsFound > 1 and matchedDirector and myYear:
                    matchedDirector = (startCareer <= myYear <= endCareer)
                    matchedUsing = 'Career' if matchedDirector else 'Failed Career Matching: {0} <= {1} <= {2}'.format(startCareer, myYear, endCareer)

                if not matchedDirector:
                    log('UTILS :: {0:<29} {1}'.format('Matching', '{0} - {1}'.format(agntDirector, matchedUsing)))
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
                        log('UTILS :: {0:<29} {1}'.format('Skipping: Recorded Director Name', '{0} AKA {1} also known by this name: {2}'.format(checkName, checkAlias, directorName)))
                        matchedDirectorDict.pop(agntDirector)
                        break

                if matchedDirectorWithIAFD:
                    log(LOG_SUBLINE)
                    break

                # we have an director who matches the conditions
                directorURL = IAFD_BASE + director.xpath('./td[2]/a/@href')[0]
                directorPhoto = director.xpath('./td[1]/a/img/@src')[0] # director name on agent website - retrieve picture
                directorPhoto = '' if 'th_iafd_ad.gif' in directorPhoto else directorPhoto.replace('thumbs/th_', '')

                log('UTILS :: {0:<29} {1}'.format('Director URL', directorURL))
                log('UTILS :: {0:<29} {1}'.format('Director Photo', directorPhoto))

                # Assign values to dictionary
                myDict = {}
                myDict['Photo'] = directorPhoto
                myDict['Alias'] = directorAliasList
                myDict['CompareName'] = compareDirectorName
                myDict['CompareAlias'] = compareDirectorAliasList
                matchedDirectorDict[agntDirector] = myDict

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
    filmVars['Agent'] = AGENT

    # file matching pattern
    filmPath = media.items[0].parts[0].file
    filmVars['FileName'] = os.path.splitext(os.path.basename(filmPath))[0]

    # film duration
    try:
        calcDuration = 0.0
        for part in media.items[0].parts:
            calcDuration += long(getattr(part, 'duration'))
        filmDuration = datetime.fromtimestamp(calcDuration // 1000) # convert miliseconds to seconds

    except:
        filmDuration = datetime.fromtimestamp(0)

    finally:
        filmVars['Duration'] = filmDuration

    filmVars['IAFDDuration'] = datetime.fromtimestamp(0) # default 1970-01-01 00:00:00

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

    filmVars['Format'] = '(Studio) - Title' if groups['fnYEAR'] is None else '(Studio) - Title (Year)'
    filmVars['Studio'] = groups['fnSTUDIO'].split(';')[0].strip()
    filmVars['CompareStudio'] = NormaliseComparisonString(filmVars['Studio'])
    filmVars['IAFDStudio'] = groups['fnSTUDIO'].split(';')[1].strip() if ';' in groups['fnSTUDIO'] else ''
    filmVars['CompareIAFDStudio'] = NormaliseComparisonString(filmVars['IAFDStudio']) if 'IAFDStudio' in filmVars and filmVars['IAFDStudio'] else ''

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

    try:
        filmVars['Year'] = int(groups['fnYEAR'])
    except:
        filmVars['Year'] = 0

    filmVars['Stacked'] = 'Yes' if groups['fnSTACK'] is not None else 'No'

    # if cast list exists - extract from filename as a list of names
    filmVars['FilenameCast'] = re.split(r',\s*', groups['fnCAST']) if groups['fnCAST'] else []

    # default to 31 Dec of Filename year if Year provided in filename and is not 1900
    filmVars['CompareDate'] = datetime(int(filmVars['Year']), 12, 31) if 'Year' in filmVars and filmVars['Year'] else datetime.fromtimestamp(0)

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
            if COLSERIES:
                collections.insert(0, matchedSeries[0].strip()) # e.g. Pissing
            series.insert(0, partTitle)                         # e.g. Pissing 1
            if index < splitCount:                              # only blank out series info in title if not last split
                splitFilmTitle[index] = ''
        else:
            if index < splitCount:                              # only add to collection if not last part of title e.g. Hardcore Fetish Series
                splitFilmTitle[index] = ''
                if COLSERIES:
                    collections.insert(0, partTitle)

    filmVars['Collection'] = collections
    filmVars['Series'] = series
    if 'Agent' in filmVars and filmVars['Agent'] != 'IAFD':
        filmVars['Title'] = filmVars['Title'] if '- ' not in filmVars['Title'] else re.sub(ur' - |- ', ': ', filmVars['Title']) # put colons back in as they can't be used in the filename
        pattern = ur'[' + re.escape(''.join(['.', '!', '%', '?'])) + ']+$'
        filmVars['ShortTitle'] = re.sub(pattern, '', ' '.join(splitFilmTitle).strip())                                          # strip punctuations at end of string
        if 'ShortTitle' in filmVars and 'CompareTitle' in filmVars and filmVars['ShortTitle'] not in filmVars['CompareTitle']:
            filmVars['CompareTitle'].append(sortAlphaChars(NormaliseComparisonString(filmVars['ShortTitle'])))
        filmVars['SearchTitle'] =  filmVars['ShortTitle']

    # if search title ends with a "1" drop it... as many first in series omit the number
    pattern = ur' 1$'
    matched = re.search(pattern, filmVars['SearchTitle'])  # match against whole string
    if matched:
        filmVars['SearchTitle'] = filmVars['SearchTitle'][:matched.start()]

    filmVars['Compilation'] = 'No'  # default to No

    # print out dictionary values / normalise unicode
    printFilmInformation(filmVars)

    return filmVars

# ----------------------------------------------------------------------------------------------------------------------------------
def matchDuration(siteDuration, FILMDICT, matchAgainstIAFD = False):
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
    log('UTILS :: {0:<29} {1}'.format('Duration Comparison Test', testDuration))

    if testDuration == 'Failed':
        raise Exception('< Duration Match Failure! >')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def matchReleaseDate(siteReleaseDate, FILMDICT):
    ''' match file year against website release date: return formatted site date if no error or default to formated file date '''

    # there can not be a difference more than 366 days between FileName Date and siteReleaseDate
    dx = abs((FILMDICT['CompareDate'] - siteReleaseDate).days)
    testReleaseDate = 'Failed' if dx > 366 else 'Passed'

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
    compareSiteStudio = NormaliseComparisonString(siteStudio)

    filmDictStudioList = []
    filmDictCompareStudioList = []
    filmDictStudioList.append(FILMDICT['Studio'])
    filmDictCompareStudioList.append(FILMDICT['CompareStudio'])

    if 'IAFDStudio' in FILMDICT and FILMDICT['IAFDStudio']:
        filmDictStudioList.append(FILMDICT['IAFDStudio'])

    if 'CompareIAFDStudio' in FILMDICT and FILMDICT['CompareIAFDStudio']:
        filmDictCompareStudioList.append(FILMDICT['IAFDCompareStudio'])

    testStudio = ''
    if compareSiteStudio == FILMDICT['CompareStudio']:
        testStudio = 'Full Match'

    if 'IAFDCompareStudio' in FILMDICT and not testStudio:
        if compareSiteStudio == FILMDICT['IAFDCompareStudio']:
            testStudio = 'Full Match (IAFD)'

    if not testStudio:
        if compareSiteStudio in FILMDICT['CompareStudio'] or FILMDICT['CompareStudio'] in compareSiteStudio:
            testStudio = 'Partial Match'

    if 'IAFDCompareStudio' in FILMDICT and not testStudio:
        if compareSiteStudio in FILMDICT['CompareIAFDStudio'] or FILMDICT['CompareIAFDStudio'] in compareSiteStudio:
            testStudio = 'Partial Match (IAFD)'

    if not testStudio:
        testStudio = 'Failed Match'

    log('UTILS :: {0:<29} {1}'.format('Site Studio', siteStudio))
    log('UTILS :: {0:<29} {1}'.format('Compare Site Studio', compareSiteStudio))
    log('UTILS :: {0:<29} {1}'.format('        Agent Studio', FILMDICT['CompareStudio']))
    log('UTILS :: {0:<29} {1}'.format('        IAFD Studio', FILMDICT['CompareIAFDStudio']))
    log('UTILS :: {0:<29} {1}'.format('Studio Comparison Test', testStudio))

    if testStudio == 'Failed Match':
        raise Exception('< Studio Match Failure! >')

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

    # some agents have the studio name in the title within brackets - lets out strip everything in brackets and rematch
    siteTitleStudioNoBrackets = ''
    matchedGroup = ''
    matched = ''
    if testTitle == 'Failed':
        pattern = re.compile('\((.*?)\)', re.IGNORECASE)
        matched = re.search(pattern, siteTitle)  # match against whole string
        if matched:
            siteTitleStudioNoBrackets = re.sub(pattern, '', siteTitle)
            amendedSiteTitle  = NormaliseComparisonString(siteTitleStudioNoBrackets)
            matchedGroup = matched.group(1)
            if matchedGroup in FILMDICT['Studio'] and amendedShortTitle in amendedSiteTitle:
                pattern = re.compile(re.escape(amendedShortTitle), re.IGNORECASE)
                amendedSiteTitle = '{0}{1}'.format(re.sub(pattern, '', amendedSiteTitle).strip(), amendedShortTitle)
                sortedSiteTitle = sortAlphaChars(amendedSiteTitle)
                testTitle = 'Passed' if sortedSiteTitle in FILMDICT['CompareTitle'] else 'Passed (IAFD)' if sortedSiteTitle in FILMDICT['IAFDCompareTitle'] else 'Failed'

    log('UTILS :: {0:<29} {1}'.format('Site Title', siteTitle))
    if matched:
        log('UTILS :: {0:<29} {1}'.format('Site Title, No Brackets', siteTitleStudioNoBrackets))
        log('UTILS :: {0:<29} {1}'.format('Bracketted Characters', matchedGroup))
    log('UTILS :: {0:<29} {1}'.format('Amended Title', amendedSiteTitle))
    log('UTILS :: {0:<29} {1}'.format('File Title', FILMDICT['Title']))
    log('UTILS :: {0:<29} {1}'.format('File Short Title', FILMDICT['ShortTitle']))
    log('UTILS :: {0:<29} {1}'.format('Compare Site Title', sortedSiteTitle))
    log('UTILS :: {0:<29} {1}'.format('       Agent Title', FILMDICT['CompareTitle']))
    log('UTILS :: {0:<29} {1}'.format('       IAFD Title', FILMDICT['IAFDCompareTitle']))
    log('UTILS :: {0:<29} {1}'.format('Title Comparison Test', testTitle))

    if testTitle == 'Failed':
        raise Exception('< Title Match Failure! >')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def NormaliseComparisonString(myString):
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
    myString = makeASCII(myString)

    # strip domain suffixes, vol., volume, Pt, Part from string, standalone '1's' then strip all non alphanumeric characters
    pattern = r'[.]([a-z]{2,3}|co[.][a-z]{2})|Vol[.]|Vols[.]|Nr[.]|\bVolume\b|\bVolumes\b|(?<!\d)1(?!\d)|Pt |\bPart\b[^A-Za-z0-9]+'
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
def setDefaultMetadata(metadata, FILMDICT):
    '''
    The following bits of metadata need to be established and used to update the movie on plex
      1.  Metadata that is set by Agent as default
          a. id.                 : Plex media id setting
          b. Studio              : From studio group of filename - no need to process this as above
          c. Title               : From title group of filename - no need to process this as is used to find it on website
          d. Tag line            : Corresponds to the url of film
          e. Originally Available: set from metadata.id (search result)
          f. Content Rating      : Always X
          g. Content Rating Age  : Always 18
          h. Collection Info     : From title group of filename
    '''
    log('UTILS :: Set Metadata from File Name:')

    # 1a.   Set id
    try:
        metadata.id = FILMDICT['id']
        log('UTILS :: {0:<29} {1}'.format('ID', metadata.id))

    except Exception as e:
        log('UTILS :: Error setting Studio: %s', e)

    # 1b.   Set Studio
    try:
        metadata.studio = FILMDICT['Studio']
        log('UTILS :: {0:<29} {1}'.format('Studio', metadata.studio))

    except Exception as e:
        log('UTILS :: Error setting Studio: %s', e)

    # 1c.   Set Title
    try:
        metadata.title = FILMDICT['Title']
        log('UTILS :: {0:<29} {1}'.format('Title', metadata.title))

    except Exception as e:
        log('UTILS :: Error setting Title: %s', e)

    # 1d.   Set Tagline
    try:
        metadata.tagline = FILMDICT['SiteURL']
        log('UTILS :: {0:<29} {1}'.format('Tagline', metadata.tagline))

    except Exception as e:
        log('UTILS :: Error setting Tag Line: %s', e)

    # 1e.   Set Originally Available from metadata.id
    #       GEVI has access to external websites load into dictionary and select the earliest date in list
    #            this works well as they will be dates within the same year as the Filename Year
    #       For other Agents just use the default Release Date stored in the CompareDate Key
    if FILMDICT['Agent'] in ['GEVI', 'AEBNiii', 'GayHotMovies', 'GayDVDEmpire']:
        originallyAvaliableDate = {}
        originallyAvaliableDate['GEVI'] = FILMDICT['CompareDate']    # first add GEVI's release date
        for key in ['AEBNiii', 'GayHotMovies', 'GayDVDEmpire']:
            if key in FILMDICT and FILMDICT[key] != {}:
                log('UTILS :: {0:<29} {1}'.format('Date From', '{0:<12} - {1}'.format(key, FILMDICT[key]['ReleaseDate'])))
                if FILMDICT[key]['ReleaseDate'] and FILMDICT[key]['ReleaseDate'] > datetime.fromtimestamp(0):
                    originallyAvaliableDate[key] = FILMDICT[key]['ReleaseDate'] # add external release dates
                    log('UTILS :: {0:<29} {1}'.format('Selected Date', '{0:<12} - {1}'.format(key, FILMDICT[key]['ReleaseDate'])))
        if originallyAvaliableDate != {}:
            oaDate = min(originallyAvaliableDate.values())

    else:
        oaDate = FILMDICT['CompareDate']

    try:
        metadata.originally_available_at = oaDate
        metadata.year = metadata.originally_available_at.year
        log('UTILS :: {0:<29} {1}'.format('Originally Available Date', metadata.originally_available_at))
        log('UTILS :: {0:<29} {1}'.format('Originally Available Year', metadata.originally_available_at.year))

    except Exception as e:
        log('UTILS :: Error setting Originally Available Date: %s', e)

    # 1f/g. Set Content Rating to Adult/18 years
    try:
        metadata.content_rating = 'X'
        metadata.content_rating_age = 18
        log('UTILS :: {0:<29} {1}'.format('Content: Rating - Age', 'X - 18'))

    except Exception as e:
        log('UTILS :: Error setting Content Rating/Age: %s', e)

    # 1h.   Set Collection
    try:
        if COLCLEAR:
            metadata.collections.clear()

        collections = sorted(FILMDICT['Collection'])
        for collection in collections:
            metadata.collections.add(collection)
        log('UTILS :: {0:<29} {1}'.format('Filename Collection', '{0:>2} - {1}'.format(len(collections), collections)))

    except Exception as e:
        log('UTILS :: Error setting Conllection: %s', e)

    return metadata

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

    #   2.     Tidy Genres: create dictionary containing the tidy genres from genres.tsv file located in plugins code directory
    log(LOG_SUBLINE)
    global TIDYDICT
    try:
        tidy_csv = os.path.join(PlexSupportPath, 'Plug-ins', 'tidy.tsv')
        csvfile = PlexLoadFile(tidy_csv)
        csvfile = csvfile.replace('\r\n', '##')
        csvrows = csvfile.split('##')
        for row in csvrows:
            if '\t' in row:
                key, value = row.split('\t')
                key = key.strip()
                if key not in TIDYDICT:
                    value = value.strip()
                    TIDYDICT[key] = value if value != 'x' else None

        tidiedSet = set(TIDYDICT.values())
        log('START :: {0:<29} {1}'.format('Original Genres', '{0:>2} - {1}'.format(len(TIDYDICT), sorted(TIDYDICT.keys()))))
        log('START :: {0:<29} {1}'.format('Tidied Genres', '{0:>2} - {1}'.format(len(tidiedSet), sorted(tidiedSet.keys()))))

    except Exception as e:
        log('START :: Error creating Tidy Genres Dictionary: %s', e)   
        log('START :: Error: Tidy Genres Source File: %s', tidy_csv)   

    #   3. Country Set: create set containing countries from country.txt located in plugins code directory
    log(LOG_SUBLINE)
    global COUNTRYSET
    try:
        country_txt = os.path.join(PlexSupportPath, 'Plug-ins', 'country.txt')
        txtfile = PlexLoadFile(country_txt)
        txtfile = txtfile.replace('\r\n', '##')
        txtrows = txtfile.split('##')
        for row in txtrows:
            COUNTRYSET.add(row.strip())

        log('START :: {0:<29} {1}'.format('Country Set', '{0:>2} - {1}'.format(len(COUNTRYSET), sorted(COUNTRYSET))))

    except Exception as e:
        log('START :: Error creating Country Set: %s', e)
        log('START :: Error: Country Source File: %s', country_txt)

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