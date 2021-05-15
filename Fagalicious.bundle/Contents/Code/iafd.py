'''
Functions used to process results from IAFD
                                                  Version History
                                                  ---------------
    Date         Dev          Modification
    06 Apr 2021  JPH71        Return unprocessed cast and director lists if IAFD returns a 403 Error, rather than an exception which prevented 
                              cast and director scrapping results been recorded.
    16 Apr 2021  Codeanator   Use of utils.py to bypass cloudflare restrictions on iafd
    04 May 2021  JPH71        enhanced xpath cast matching as actors with wrong case names were not been matched e.g Scott DeMarco is listed as Scott Demarco
                              introduced duration matching
    08 May 2021  JPH71        remove unicode in actors names so as to use in xpath matching
'''
# -------------------------------------------------------------------------------------------------------------------------------
from unidecode import unidecode
import utils

# IAFD Related variables
IAFD_BASE = 'https://www.iafd.com'
IAFD_SEARCH_URL = IAFD_BASE + '/results.asp?searchtype=comprehensive&searchstring={0}'

# -------------------------------------------------------------------------------------------------------------------------------
def ProcessIAFD(agntCastList, FILMDICT):
    ''' Process and match cast list against IAFD '''
    # return variable
    actorDict = {}

    # clean up the Cast List 
    agntCastList = [x.split('(')[0].strip() if '(' in x else x.strip() for x in agntCastList]
    agntCastList = [utils.makeASCII(x) for x in agntCastList if x.strip()]
    if not agntCastList:
        raise Exception('<No Cast List!>')

    FoundFilm, html, NoIAFD = FindIAFD_Film(FILMDICT)
    log(LOG_SUBLINE)

    # get cast information
    originalCastList = agntCastList[:]       # copy list
    if FoundFilm:
        log('IAFD  :: Process in Film Mode:        \t{0} Actors: {1}'.format(len(agntCastList), agntCastList))
        unmatchedList, actorDict = getIAFD_FilmCast(html, agntCastList, actorDict, FILMDICT)
        log(LOG_SUBLINE)
        if agntCastList:
            log('IAFD  :: Process Unmatched Actors in Cast Mode: {0} Actors: {1}'.format(len(unmatchedList), unmatchedList))
            unmatchedList, actorDict2 = getIAFD_Actor(unmatchedList, actorDict, FILMDICT)
            actorDict.update(actorDict2)
    else:
        if not NoIAFD:      # IAFD available - process in cast mode
            log('IAFD  :: Process in Cast Mode:        \t{0} Actors: {1}'.format(len(agntCastList), agntCastList))
            unmatchedList, actorDict = getIAFD_Actor(agntCastList, actorDict, FILMDICT)

    if actorDict:
        # leave unmatched actors - normalise both agent cast list and match List
        log('IAFD  :: Agent Cast List:             \t%s', originalCastList)
        log('IAFD  :: Matched Actors List:         \t%s', sorted(actorDict.keys()))
        log('IAFD  :: Unmatched Actors:            \t%s', unmatchedList)
        if unmatchedList:
            log(LOG_SUBLINE)
            log('IAFD  :: Attempt Levenstein Matching, 1 distance per word')

            actorList = actorDict.keys()
            compareunmatchedList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in unmatchedList]
            compareActorList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in actorList]

            log('IAFD  :: Normalised Unmatched Cast:   \t%s', compareunmatchedList)
            log('IAFD  :: Normalised Actor List:       \t%s', compareActorList)
            for uIndex, compareUnmatched in enumerate(compareunmatchedList):
                # Lehvenstein Match Distance - one change per word in cast name
                levDistance = len(unmatchedList[uIndex].split()) + 1
                for aIndex, compareActor in enumerate(compareActorList):
                    if not compareActor:
                        continue
                    levScore = String.LevenshteinDistance(compareUnmatched, compareActor)
                    status = 'Passed' if levScore <= levDistance else 'Failed'
                    log('IAFD  :: Actor: {0: <20}\t{1} Levenshtein Match - Distance:Score [{2}:{3}] against: {4}'.format(unmatchedList[uIndex], status, levDistance, levScore, actorList[aIndex]))
                    if levScore <= levDistance:
                        unmatchedList[uIndex] = ''
                        compareunmatchedList[uIndex] = ''
                        actorList[aIndex] = ''
                        compareActorList[aIndex] = ''
                        break   # stop processing rest of matched names and get next cast name

            log(LOG_SUBLINE)
            unmatchedList = [x for x in unmatchedList if x]
            log('IAFD  :: IAFD Actors: Matched:        \t%s', actorDict.keys())
            log('IAFD  ::              Unmatched:      \t%s', unmatchedList)

            # Add unmatched actors to actor dictionary with an absent status
            for cast in unmatchedList:
                actorDict[cast] = {'Photo': '', 'Role': IAFD_ABSENT, 'Alias': ''}

    else:   # if there is a failure to read the website we would end up here
        # Add unmatched actors to actor dictionary with an absent status
        for cast in agntCastList:
            actorDict[cast] = {'Photo': '', 'Role': IAFD_ABSENT, 'Alias': ''}

    return actorDict

# -------------------------------------------------------------------------------------------------------------------------------
def FindIAFD_Film(FILMDICT):
    ''' check IAFD web site for better quality actor thumbnails per movie'''
    FoundFilm = False
    FILMDICT['FoundOnIAFD'] = "No"
    html = None

    # search for Film Title on IAFD
    try:
        html, NoIAFD = getIAFD_URLElement(IAFD_SEARCH_URL.format(FILMDICT['IAFDSearchTitle']), UseAdditionalResults=True)
        if NoIAFD:
            raise Exception(NoIAFD)

        # get films listed within 1 year of what is on agent - as IAFD may have a different year recorded
        if FILMDICT['Year']:
            FILMDICT['Year'] = int(FILMDICT['Year'])
            filmList = html.xpath('//table[@id="titleresult"]/tbody/tr/td[2][.>="{0}" and .<="{1}"]/ancestor::tr'.format(FILMDICT['Year'] - 1, FILMDICT['Year'] + 1))
        else:
            filmList = html.xpath('//table[@id="titleresult"]/tbody/tr')

        log('IAFD  :: [%s] IAFD Films in List', len(filmList))
        log(LOG_BIGLINE)

        for film in filmList:
            # Site Title and Site AKA
            try:
                iafdTitle = film.xpath('./td[1]/a/text()')[0].strip()
                utils.matchTitle(iafdTitle, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                try:
                    iafdAKA = film.xpath('./td[4]/text()')[0].strip()
                    utils.matchTitle(iafdAKA, FILMDICT)
                    log(LOG_BIGLINE)
                except Exception as e:
                    log('IAFD  :: Error getting Site Title: %s', e)
                    log(LOG_SUBLINE)
                    continue

            # Film URL
            try:
                iafdfilmURL = film.xpath('./td[1]/a/@href')[0].replace('+/', '/').replace('-.', '.')
                iafdfilmURL = '{0}{1}'.format(IAFD_BASE, iafdfilmURL) if iafdfilmURL[0] == '/' else '{0}/{1}'.format(IAFD_BASE, iafdfilmURL)
                log('IAFD  :: Site Title url                %s', iafdfilmURL)
                html, NoIAFD = getIAFD_URLElement(iafdfilmURL, UseAdditionalResults=False)
                if NoIAFD:
                    raise Exception(NoIAFD)

                log(LOG_BIGLINE)
            except Exception as e:
                log('IAFD  :: Error: IAFD URL Studio: %s', e)
                log(LOG_SUBLINE)
                continue

            # Film Duration
            try:
                iafdDuration = html.xpath('//p[@class="bioheading" and text()="Minutes"]//following-sibling::p[1]/text()')[0].strip()
                utils.matchDuration(iafdDuration, FILMDICT)
                log(LOG_BIGLINE)
            except Exception as e:
                log('IAFD  :: Error: IAFD Duration: %s', e)
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
                    utils.matchStudio(studio, FILMDICT, False if FILMDICT['IAFDStudio'] else True) # if an IAFD Studio was recorded on the filename - set last param to false
                    studioMatch = True
                    break           # break out of loop if it matches
                except Exception as e:
                    log('IAFD  :: Error: %s', e)
                    continue

            if not studioMatch:
                log('IAFD  :: Error getting Site Studio')
                continue

            # if we get here we have found a film match break out of loop
            FoundFilm = True
            FILMDICT['FoundOnIAFD'] = "Yes"
            break
    except Exception as e:
        log('IAFD  :: Error: IAFD Film Search Failure, %s', e)

    return FoundFilm, html, NoIAFD

# -------------------------------------------------------------------------------------------------------------------------------
def getIAFD_URLElement(myString, UseAdditionalResults):
    ''' check IAFD web site for better quality actor thumbnails irrespective of whether we have a thumbnail or not '''
    # this variable will be set if IAFD fails to be read
    NoIAFD = ''
    html = ''
    for i in range(2):
        try:
            HTTPRequest = utils.getHTTPRequest(myString, timeout=20)
            html = HTML.ElementFromString(HTTPRequest.text)
            if UseAdditionalResults:
                try:
                    searchQuery = html.xpath('//a[text()="See More Results..."]/@href')[0].strip().replace(' ', '+')
                    if searchQuery:
                        searchQuery = IAFD_BASE + searchQuery if IAFD_BASE not in searchQuery else searchQuery
                        log('IAFD  :: Loading Additional Search Results: %s', searchQuery)
                        HTTPRequest = utils.getHTTPRequest(searchQuery, timeout=20)
                        html = HTML.ElementFromString(HTTPRequest.text)
                except:
                    log('IAFD  :: No Additional Search Results')
            break
        except Exception as e:
            NoIAFD = '<{0}>'.format(e)
            log('IAFD  :: Error: Failed to read IAFD URL: {0} - Processing Abandoned'.format(NoIAFD))
            continue

    return html, NoIAFD

# -------------------------------------------------------------------------------------------------------------------------------
def getIAFD_FilmCast(html, agntCastList, actorDict, FILMDICT):
    ''' check IAFD web site for better quality actor thumbnails per movie'''
    try:
        actorList = html.xpath('//h3[.="Performers"]/ancestor::div[@class="panel panel-default"]//div[@class[contains(.,"castbox")]]/p')
        log('IAFD  :: %s Actors on IAFD', len(actorList))
        for actor in actorList:
            actorName = actor.xpath('./a/text()[normalize-space()]')[0].strip()
            actorURL = IAFD_BASE + actor.xpath('./a/@href')[0].strip()
            actorPhoto = actor.xpath('./a/img/@src')[0].strip()
            actorPhoto = '' if 'nophoto' in actorPhoto or 'th_iafd_ad' in actorPhoto else actorPhoto
            actorRole = actor.xpath('./text()[normalize-space()]')
            actorRole = ' '.join(actorRole).strip()

            try:
                actorAlias = actor.xpath('./i/text()')[0].split(':')[1].replace(')', '').strip()
            except:
                actorAlias = ''

            actorRole = actorRole if actorRole else 'AKA: {0}'.format(actorAlias) if actorAlias else IAFD_FOUND

            # log actor details
            log('IAFD  :: Actor:                       \t%s', actorName)
            log('IAFD  :: Actor Alias:                 \t%s', actorAlias)
            log('IAFD  :: Actor URL:                   \t%s', actorURL)
            log('IAFD  :: Actor Photo:                 \t%s', actorPhoto)
            log('IAFD  :: Actor Role:                  \t%s', actorRole)

            # Assign values to dictionary
            myDict = {}
            myDict['Photo'] = actorPhoto
            myDict['Role'] = actorRole
            myDict['Alias'] = actorAlias
            actorDict[actorName] = myDict
            log(LOG_SUBLINE)

    except Exception as e:
        log('IAFD  :: Error: Processing IAFD Film Cast: %s', e)

    # match actors found on IAFD to the list sent by the agent website, and remove matched actors
    compareAgntCastList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in agntCastList] # strip non alpha chars for comparison
    log('IAFD  :: Actors: in Agent List:       \t%s', agntCastList)
    for key in sorted(actorDict.keys()):
        actorName = key
        compareActorName = re.sub(r'[\W\d_]', '', actorName).strip().lower()
        actorAlias = actorDict[key]['Alias']
        compareActorAlias = re.sub(r'[\W\d_]', '', actorAlias).strip().lower()

        # 1st full match against actor name
        try:
            nameIndex = compareAgntCastList.index(compareActorName)
            del agntCastList[nameIndex]
            del compareAgntCastList[nameIndex]
            log('IAFD  :: Remove from Agent List:      \tFull Match - Actor Name: %s', actorName)
            continue
        except:
            pass

        # 2nd partial match against actor name
        try:
            nameIndex = [i for i, l in enumerate(compareAgntCastList) if compareActorName in l or l in compareActorName][0]
            del agntCastList[nameIndex]
            del compareAgntCastList[nameIndex]
            log('IAFD  :: Remove from Agent List:      \tPartial Match - Actor Name: %s', actorName)
            continue
        except:
            pass

        if actorAlias:
            # 3rd full match against actor alias
            try:
                nameIndex = compareAgntCastList.index(compareActorAlias)
                del agntCastList[nameIndex]
                del compareAgntCastList[nameIndex]
                log('IAFD  :: Remove from Agent List:      \tFull Match - Actor Alias: %s', actorAlias)
                continue
            except:
                pass

            # 4th partial match against actor alias
            try:
                nameIndex = [i for i, l in enumerate(compareAgntCastList) if compareActorAlias in l or l in compareActorAlias][0]
                del agntCastList[nameIndex]
                del compareAgntCastList[nameIndex]
                log('IAFD  :: Remove from Agent List:      \tPartial Match - Actor Name: %s', actorAlias)
                continue
            except:
                pass

        # reasons to fail match is if actor is on IAFD and not on Agent Website, or cannot find alias
        log('IAFD  :: Actor may only be on IAFD:   \tActor Name: %s', actorName)

    return agntCastList, actorDict

# -------------------------------------------------------------------------------------------------------------------------------
def getIAFD_Actor(agntCastList, actorDict, FILMDICT):
    ''' check IAFD web site for individual actors'''

    allCastList = agntCastList[:]       # copy list
    compareAgntCastList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in agntCastList]

    if FILMDICT['Year']:
        FILMDICT['Year'] = int(FILMDICT['Year'])

    useFullCareer = True if FILMDICT['Year'] else False  

    for cast in allCastList:
        cast = unidecode(cast)
        log('Decoded Cast Name %s', cast)
        compareCast = re.sub(r'[\W\d_]', '', cast).strip().lower()
        castLower = cast.lower()
        try:
            html, NoIAFD = getIAFD_URLElement(IAFD_SEARCH_URL.format(String.URLEncode(cast)), UseAdditionalResults=False)
            if NoIAFD:
                break

            # IAFD presents actor searches in career start order, this needs to be changed as actors whose main name does not match the search name 
            # will appear first in the list because he has an alias that matches the search name. we need to reorder so that those whose main name matches
            # the search name are listed first
            # xpath to get matching Actor Main Name and Alias: start with male actors, then include female actresses (bi films)
            for i in range(2):
                if i == 0 and useFullCareer:
                    filter = 'Year'
                    useFullCareer = True
                    xPathMatchMainMale = '//table[@id="tblMal"]/tbody/tr[td[2]/a[(contains(@href, "/perfid={0}") or (.) = "{1}" or translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="{2}")] and {3}>=td[4] and {3}<=td[5]]//ancestor::tr'.format(compareCast, cast, castLower, FILMDICT['Year'])
                    xPathMatchAliasMale = '//table[@id="tblMal"]/tbody/tr[contains(td[3], "{0}") and {1}>=td[4] and {1}<=td[5]]//ancestor::tr'.format(cast, FILMDICT['Year'])
                    xPathMatchMainFemale = '//table[@id="tblFem"]/tbody/tr[td[2]/a[(contains(@href, "/perfid={0}") or (.) = "{1}" or translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="{2}")] and {3}>=td[4] and {3}<=td[5]]//ancestor::tr'.format(compareCast, cast, castLower, FILMDICT['Year'])
                    xPathMatchAliasFemale = '//table[@id="tblFem"]/tbody/tr[contains(td[3], "{0}") and {1}>=td[4] and {1}<=td[5]]//ancestor::tr'.format(cast, FILMDICT['Year'])
                else:
                    # some agents mislabel compilations, thus actors won't be found by the Film Year
                    filter = 'Name'
                    useFullCareer = False
                    xPathMatchMainMale = '//table[@id="tblMal"]/tbody/tr[td[2]/a[(contains(@href, "/perfid={0}") or (.) = "{1}" or translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="{2}")]]//ancestor::tr'.format(compareCast, cast, castLower)
                    xPathMatchAliasMale = '//table[@id="tblMal"]/tbody/tr[contains(td[3], "{0}")]//ancestor::tr'.format(cast) 
                    xPathMatchMainFemale = '//table[@id="tblFem"]/tbody/tr[td[2]/a[(contains(@href, "/perfid={0}") or (.) = "{1}" or translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="{2}")]]//ancestor::tr'.format(compareCast, cast, castLower)
                    xPathMatchAliasFemale = '//table[@id="tblFem"]/tbody/tr[contains(td[3], "{0}")]//ancestor::tr'.format(cast) 

                combinedList = []
                for xPath in [xPathMatchMainMale, xPathMatchAliasMale, xPathMatchMainFemale, xPathMatchAliasFemale]:
                    try:
                        mainList = html.xpath(xPath)
                    except:
                        log('IAFD  :: Error: Bad Main Name xPath: %s', xPath)
                        mainList = []

                    combinedList.extend(mainList)

                actorList = [j for x, j in enumerate(combinedList) if j not in combinedList[:x]]
                actorsFound = len(actorList)
                log('IAFD  :: %s Filter: %s\t[%s] Actors Found named %s on Agent Website %s', filter, 'Career Match   ' if useFullCareer else 'No Career Match', actorsFound, cast, '<Skipping: too many found>' if actorsFound > 13 else '')
                if (i == 0 and actorsFound > 0) or actorsFound > 13:
                    break

            if actorsFound == 0 or actorsFound > 13:    #skip actor
                log(LOG_SUBLINE)
                continue

            for actor in actorList:
                try:
                    actorName = actor.xpath('./td[2]/a/text()[normalize-space()]')[0]          # get actor details and compare to Agent cast
                    compareActorName = re.sub(r'[\W\d_]', '', actorName).strip().lower()
                    log('IAFD  :: Actor:                       \t%s / %s', actorName, compareActorName)
                    actorAlias = ''
                    compareActorAlias = ''
                    if compareActorName != compareCast:
                        log('IAFD  :: Actor: Failed Name Match:    \tAgent [%s] - IAFD [%s]', cast, actorName)
                        try:
                            actorAliasList = actor.xpath('./td[3]/text()')[0].split(',')
                            actorAliasList = [x.strip() for x in actorAliasList if x]
                            log('IAFD  :: Actor Aliases:               \t%s', actorAliasList)
                            compareActorAliasList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in actorAliasList]
                            matchedItem = [i for (i, x) in enumerate(compareActorAliasList) if x == compareCast]
                            actorAlias = actorAliasList[matchedItem[0]] if matchedItem else ''
                            compareActorAlias = compareActorAliasList[matchedItem[0]] if matchedItem else ''
                            if not actorAlias:
                                log('IAFD  :: Actor Name not in Aliases List')
                                log(LOG_SUBLINE)
                                continue    # next actor
                        except:
                            log('IAFD  :: Error: Could not read Actor Alias')
                            log(LOG_SUBLINE)
                            continue    # next actor

                    startCareer = int(actor.xpath('./td[4]/text()[normalize-space()]')[0]) - 1 # set start of career to 1 year before for pre-releases
                    endCareer = int(actor.xpath('./td[5]/text()[normalize-space()]')[0]) + 1   # set end of career to 1 year after to cater for late releases

                    # only perform career checks if title is not a compilation and we have not fileterd the search results by the Film Year
                    if FILMDICT['Compilation'] == "No" and useFullCareer:
                        careerRange = (startCareer <= FILMDICT['Year'] <= endCareer)
                        if careerRange == False:
                            log('IAFD  :: Actor: Failed Career Range Match, Start: [%s] Film Year: [%s] End: [%s]', startCareer, FILMDICT['Year'], endCareer)
                            continue    # next actor

                    # we have an actor who satisfies the conditions
                    actorURL = IAFD_BASE + actor.xpath('./td[2]/a/@href')[0]
                    actorPhoto = actor.xpath('./td[1]/a/img/@src')[0] # actor name on agent website - retrieve picture
                    actorPhoto = '' if 'nophoto' in actorPhoto or 'th_iafd_ad' in actorPhoto else actorPhoto.replace('thumbs/th_', '')
                    actorRole = 'AKA: {0}'.format(actorAlias) if actorAlias else IAFD_FOUND

                    log('IAFD  :: Actor Alias:                 \t%s / %s', actorAlias, compareActorAlias if compareActorAlias != None else '')
                    log('IAFD  :: Start Career:                \t%s', startCareer)
                    log('IAFD  :: End Career:                  \t%s', endCareer)
                    log('IAFD  :: Actor URL:                   \t%s', actorURL)
                    log('IAFD  :: Actor Photo:                 \t%s', actorPhoto)
                    log('IAFD  :: Actor Role:                  \t%s', actorRole)

                    # if we get here we have found an actor match, remove actor from the agntCastList, full and partial matches
                    # Assign values to dictionary
                    myDict = {}
                    myDict['Photo'] = actorPhoto
                    myDict['Role'] = actorRole
                    myDict['Alias'] = actorAlias
                    actorDict[actorName] = myDict

                    log('IAFD  :: Actors: in Agent List:       \t%s', agntCastList)

                    # 1st full match against actor name
                    matchedName = False
                    try:
                        nameIndex = compareAgntCastList.index(compareActorName)
                        del agntCastList[nameIndex]
                        del compareAgntCastList[nameIndex]
                        matchedName = True
                        log('IAFD  :: Remove from Agent List:      \tFull Match - Actor Name: %s', actorName)
                    except:
                        # 2nd partial match against actor name
                        try:
                            nameIndex = [i for i, l in enumerate(compareAgntCastList) if compareActorName in l or l in compareActorName][0]
                            del agntCastList[nameIndex]
                            del compareAgntCastList[nameIndex]
                            matchedName = True
                            log('IAFD  :: Remove from Agent List:      \tPartial Match - Actor Name: %s', actorName)
                        except:
                            if actorAlias:
                                # 3rd full match against actor alias
                                try:
                                    nameIndex = compareAgntCastList.index(compareActorAlias)
                                    del agntCastList[nameIndex]
                                    del compareAgntCastList[nameIndex]
                                    matchedName = True
                                    log('IAFD  :: Remove from Agent List:      \tFull Match - Actor Alias: %s', actorAlias)
                                except:
                                    # 4th partial match against actor alias
                                    try:
                                        nameIndex = [i for i, l in enumerate(compareAgntCastList) if compareActorAlias in l or l in compareActorAlias][0]
                                        del agntCastList[nameIndex]
                                        del compareAgntCastList[nameIndex]
                                        matchedName = True
                                        log('IAFD  :: Remove from Agent List:      \tPartial Match - Actor Name: %s', actorAlias)
                                    except:
                                        pass
                    # reasons to fail match: 1. is if actor is on IAFD and not on Agent Website
                    #                        2. actor on website but not on IAFD
                    if not matchedName:
                        log('IAFD  :: Failed to match Actor:       \tActor Name: %s', actorName)

                    log(LOG_SUBLINE)
                    break   # break out to next actor in agent cast list (allCastList)

                except Exception as e:
                    log('IAFD  :: Error: Cannot Process IAFD Actor: %s', e)
                    log(LOG_SUBLINE)
                    continue   # next actor with same name (actorList)

        except Exception as e:
            log('IAFD  :: Error: Cannot Process IAFD Actor Search Results: %s', e)
            log(LOG_SUBLINE)
            continue    # next actor in agent cast list  (allCastList)

    return agntCastList, actorDict

# -------------------------------------------------------------------------------------------------------------------------------
def getIAFD_Director(agntDirectorList, FILMDICT):
    ''' check IAFD web site for individual actors'''
    agntDirectorList = [utils.makeASCII(x).strip() for x in agntDirectorList if x.strip()]
    if not agntDirectorList:
        raise Exception('<No Director List!>')

    directorDict = {k: None for k in agntDirectorList}
    allDirectorList = agntDirectorList[:]       # copy list
    compareAgntDirectorList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in agntDirectorList]

    for agntDirector in allDirectorList:
        compareDirector = re.sub(r'[\W\d_]', '', agntDirector).strip().lower()
        try:
            html, NoIAFD = getIAFD_URLElement(IAFD_SEARCH_URL.format(String.URLEncode(agntDirector)), UseAdditionalResults=False)
            if NoIAFD:
                break

            # IAFD presents director searches in career start order, this needs to be changed as directors whose main name does not match the search name 
            # will appear first in the list because he has an alias that matches the search name. we need to reorder so that those whose main name matches
            # the search name are listed first
            # xpath to get matching director Main Name and Alias
            xPathMatchMain = '//table[@id="tblDir"]/tbody/tr[td[2]="{0}"]//ancestor::tr'.format(agntDirector)
            xPathMatchAlias = '//table[@id="tblDir"]/tbody/tr[contains(td[3], "{0}")]//ancestor::tr'.format(agntDirector)
            try:
                mainList = html.xpath(xPathMatchMain)
            except:
                log('IAFD  :: Error: Bad Main Name xPath')
                mainList = []
            try:
                aliasList = html.xpath(xPathMatchAlias)
            except:
                log('IAFD  :: Error: Bad Alias xPath')
                aliasList = []

            combinedList = mainList + aliasList
            directorList = [i for x, i in enumerate(combinedList) if i not in combinedList[:x]]
            directorsFound = len(directorList)
            log('IAFD  :: [%s] Director Found named %s on Agent Website %s', directorsFound, agntDirector, '[Skipping: too many found]' if directorsFound > 5 else '')
            if directorsFound > 5:
                continue

            for director in directorList:
                try:
                    directorName = director.xpath('./td[2]/a/text()[normalize-space()]')[0]          # get director details and compare to Agent director
                    compareDirectorName = re.sub(r'[\W\d_]', '', directorName).strip().lower()
                    log('IAFD  :: Director:                    \t%s', directorName)
                    directorAlias = ''
                    if compareDirectorName != compareDirector:
                        log('IAFD  :: Director: Failed Name Match: Agent [%s] - IAFD [%s]', director, directorName)
                        try:
                            directorAliasList = director.xpath('./td[3]/text()')[0].split(',')
                            directorAliasList = [x.strip() for x in directorAliasList if x]
                            log('IAFD  :: Director Aliases:            \t%s', directorAliasList)
                            comparedirectorAliasList = [re.sub(r'[\W\d_]', '', x).strip().lower() for x in directorAliasList]
                            matchedItem = [i for (i, x) in enumerate(comparedirectorAliasList) if x == compareDirector]
                            directorAlias = directorAliasList[matchedItem[0]] if matchedItem else ''
                            compareDirectorAlias = re.sub(r'[\W\d_]', '', directorAlias).strip().lower() if matchedItem else ''
                            if not directorAlias:
                                log('IAFD  :: Director Name not in Aliases List')
                                log(LOG_SUBLINE)
                                continue    # next director
                        except:
                            log('IAFD  :: Error: Could not read Director Alias')
                            log(LOG_SUBLINE)
                            continue    # next director

                    startCareer = int(director.xpath('./td[4]/text()[normalize-space()]')[0]) # set start of career
                    endCareer = int(director.xpath('./td[5]/text()[normalize-space()]')[0])   # set end of career

                    # we have an director who satisfies the conditions
                    directorURL = IAFD_BASE + director.xpath('./td[2]/a/@href')[0]
                    directorPhoto = director.xpath('./td[1]/a/img/@src')[0] # director name on agent website - retrieve picture
                    directorPhoto = '' if 'th_iafd_ad.gif' in directorPhoto else directorPhoto.replace('thumbs/th_', '')

                    log('IAFD  :: Alias:                       \t%s', directorAlias)
                    log('IAFD  :: Start Career:                \t%s', startCareer)
                    log('IAFD  :: End Career:                  \t%s', endCareer)
                    log('IAFD  :: Director URL:                \t%s', directorURL)
                    log('IAFD  :: Director Photo:              \t%s', directorPhoto)

                    # Assign values to dictionary
                    directorDict[directorName] = directorPhoto

                    # full matching director name
                    try:
                        directorNameIndex = compareAgntDirectorList.index(compareDirectorName)
                        del agntDirectorList[directorNameIndex]
                        del compareAgntDirectorList[directorNameIndex]
                        log('IAFD  :: Remove from unmatched list:  \tFull Match - Director Name: %s', directorName)
                    except:
                        # full matching actor alias
                        try:
                            directorAliasIndex = compareAgntDirectorList.index(compareDirectorAlias)
                            del agntDirectorList[directorAliasIndex]
                            del compareAgntDirectorList[directorAliasIndex]
                            log('IAFD  :: Remove from unmatched list:  \tFull Match - Director Alias: %s', directorAlias)
                        except:
                            pass
                    log('IAFD  :: Directors left unmatched:    \t%s', agntDirectorList)

                    log(LOG_SUBLINE)
                    break   # break out to next director in agent director list (allDirectorList)

                except Exception as e:
                    log('IAFD  :: Error: Cannot Process IAFD director: %s', e)
                    log(LOG_SUBLINE)
                    continue   # next director with same name (directorList)

        except Exception as e:
            log('IAFD  :: Error: Cannot Process IAFD director Search Results: %s', e)
            log(LOG_SUBLINE)
            continue    # next director in agent director list  (allDirectorList)

    return directorDict