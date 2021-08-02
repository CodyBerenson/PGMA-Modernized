#!/usr/bin/env python
# encoding=utf8
'''
# IAFD - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    22 Apr 2020   2020.04.22.01    Creation
    15 May 2020   2020.04.22.02    Corrected search string to account for titles that have a Colon in them
                                   added/merge matching string routines - filename, studio, release date
                                   included cast with non-sexual roles
    19 May 2020   2020.04.22.03    Corrected search to look past the results page and get the movie title page to find
                                   studio/release date as the results page only listed the distributor/production year
                                   updated date match function
    01 Jun 2020   2020.04.22.04    Implemented translation of summary
                                   put back scrape from local media assets
    27 Jun 2020   2020.04.22.05    Improvement to Summary Translation: Translate into Plex Library Language
                                   stripping of intenet domain suffixes from studio names when matching
                                   handling of unicode characters in film titles and comparision string normalisation
    12 Sep 2020   2020.04.22.06    Titles with hyphens failing as these were converted to ":"
                                   corrected by splitting and using string upto that position as search...
    20 Sep 2020   2020.04.22.07    Titles with '[', '(' were corrected by splitting and using string upto that position as search...
    07 Oct 2020   2020.04.22.08    IAFD - change to https
    07 Mar 2021   2020.04.22.10    Moved IAFD and general functions to other py files
                                   Enhancements to IAFD search routine, including Levenshtein Matching on Cast names
                                   Added iafd legend to summary
    28 Mar 2021   2020.04.22.11    Added code to create actor collections
    27 Jul 2021   2020.04.22.12    Merged all libraries into utils.py
                                   improvements to film matching within iafd and scraping data at match
                                   Fix Issue: IAFD Unable to match three titles #105

---------------------------------------------------------------------------------------------------------------
'''
import json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2020.04.22.12'
PLUGIN_LOG_TITLE = 'IAFD'

# log section separators
LOG_BIGLINE = '--------------------------------------------------------------------------------'
LOG_SUBLINE = '      --------------------------------------------------------------------------'

# Preferences
DELAY = int(Prefs['delay'])                         # Delay used when requesting HTML, may be good to have to prevent being banned from the site
MATCHSITEDURATION = Prefs['matchsiteduration']      # Match against Site Duration value
DURATIONDX = 60 # int(Prefs['durationdx'])               # Acceptable difference between actual duration of video file and that on agent website
DETECT = Prefs['detect']                            # detect the language the summary appears in on the web page
PREFIXLEGEND = Prefs['prefixlegend']                # place cast legend at start of summary or end
COLCLEAR = Prefs['clearcollections']                # clear previously set collections
COLSTUDIO = Prefs['studiocollection']               # add studio name to collection
COLTITLE = Prefs['titlecollection']                 # add title [parts] to collection
COLGENRE = Prefs['genrecollection']                 # add genres to collection
COLDIRECTOR = Prefs['directorcollection']           # add director to collection
COLCAST = Prefs['castcollection']                   # add cast to collection
COLCOUNTRY = Prefs['countrycollection']             # add country to collection

# dictionary holding film variables
FILMDICT = {}

# Date Formats used by website
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
def log(message, *args):
    ''' log messages '''
    if re.search('ERROR', message, re.IGNORECASE):
        Log.Error(PLUGIN_LOG_TITLE + ' - ' + message, *args)
    else:
        Log.Info(PLUGIN_LOG_TITLE + '  - ' + message, *args)

# ----------------------------------------------------------------------------------------------------------------------------------
# imports placed here to use previously declared variables
import utils

# ----------------------------------------------------------------------------------------------------------------------------------
class IAFD(Agent.Movies):
    ''' define Agent class '''
    name = 'Internet Adult Film Database'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms', 'com.plexapp.agents.GayAdultScenes']
    accepts_from = ['com.plexapp.agents.localmedia']

    #-------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Title for search query '''
        log('AGNT  :: Original Search Query        : {0}'.format(myString))

        myString = myString.strip().lower()

        # split and take up to first occurence of character
        splitChars = ['-', '[', '(', ur'\u2013', ur'\u2014']
        pattern = u'[{0}]'.format(''.join(splitChars))
        matched = re.search(pattern, myString)  # match against whole string
        if matched:
            numPos = matched.start()
            log('SELF:: Search Query:: Splitting at position [{0}]. Found one of these {1}'.format(numPos, pattern))
            myString = myString[:numPos]
            log('SELF:: Amended Search Query [{0}]'.format(myString))
        else:
            log('SELF:: Search Query:: Split not attempted. String has none of these {0}'.format(pattern))

        myString = String.StripDiacritics(myString)
        myString = String.URLEncode(myString)

        # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string 
        myString = myString.replace('%25', '%').replace('*', '')

        log('AGNT  :: Returned Search Query        : {0}'.format(myString))

        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return

        utils.logHeaders('SEARCH', media, lang)

        # Check filename format
        try:
            FILMDICT = utils.matchFilename(media.items[0].parts[0].file)
        except Exception as e:
            log('SEARCH:: Error: %s', e)
            return

        log(LOG_BIGLINE)

        if FILMDICT['FoundOnIAFD'] == 'Yes':
            results.Append(MetadataSearchResult(id=json.dumps(FILMDICT), name=FILMDICT['Title'], score=100, lang=lang))
            log(LOG_BIGLINE)

        log('SEARCH:: Finished Search Routine')
        return

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        utils.logHeaders('UPDATE', media, lang)

        # Fetch FILMDICT
        FILMDICT = json.loads(metadata.id)
        log('UPDATE:: Film Dictionary Variables:')
        for key in sorted(FILMDICT.keys()):
            log('UPDATE:: {0: <29}: {1}'.format(key, FILMDICT[key]))
        log(LOG_BIGLINE)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as above
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Tag line             : Corresponds to the url of movie
        #        d. Originally Available : set from metadata.id (search result)
        #        e. Content Rating       : Always X
        #        f. Content Rating Age   : Always 18
        #        g. Collection Info      : From title group of filename 

        # 1a.   Set Studio
        metadata.studio = FILMDICT['Studio']
        log('UPDATE:: Studio: %s' , metadata.studio)

        # 1b.   Set Title
        metadata.title = FILMDICT['Title']
        log('UPDATE:: Title: %s' , metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = FILMDICT['SiteURL']
        metadata.originally_available_at = datetime.strptime(FILMDICT['CompareDate'], DATEFORMAT)
        metadata.year = metadata.originally_available_at.year
        log('UPDATE:: Tagline: %s', metadata.tagline)
        log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)

        # 1e/f. Set Content Rating to Adult/18 years
        metadata.content_rating = 'X'
        metadata.content_rating_age = 18
        log('UPDATE:: Content Rating - Content Rating Age: X - 18')

        # 1g. Collection
        if COLCLEAR:
            metadata.collections.clear()

        collections = FILMDICT['Collection']
        for collection in collections:
            metadata.collections.add(collection)
        log('UPDATE:: Collection Set From filename: %s', collections)

        #    2.  Metadata retrieved from website
        #        a. Directors
        #        b. Cast                 : List of Actors and Photos (alphabetic order)
        #        c. Summary              : Synopsis, Scene Breakdown and Comments

        # 2a.   Directors
        log(LOG_BIGLINE)
        if FILMDICT['Directors']:
            directorDict = FILMDICT['Directors']
            log('UPDATE:: Director List %s', directorDict.keys())
            metadata.directors.clear()
            for key in sorted(directorDict):
                newDirector = metadata.directors.new()
                newDirector.name = key
                newDirector.photo = directorDict[key]
                # add director to collection
                if COLDIRECTOR:
                    metadata.collections.add(key)
        else:
            log('UPDATE:: Error No Directors Recorded')


        # 2b.   Cast
        log(LOG_BIGLINE)
        if FILMDICT['Cast']:
            castDict = FILMDICT['Cast']
            log('UPDATE:: Cast List %s', castDict.keys())

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted(castDict):
                cast = metadata.roles.new()
                cast.name = key
                cast.photo = castDict[key]['Photo']
                cast.role = castDict[key]['Role']
                # add cast name to collection
                if COLCAST:
                    metadata.collections.add(key)
        else:
            log('UPDATE:: Error No Cast Recorded')

        # 2c.   Reviews - Put all Scene Information here
        log(LOG_BIGLINE)
        if FILMDICT['Scenes']:
            htmlscenes = FILMDICT['Scenes'].split('##')
            log('UPDATE:: Possible Number of Scenes [%s]', len(htmlscenes))

            metadata.reviews.clear()
            sceneCount = 0 # avoid enumerating the number of scenes as some films have empty scenes
            for count, scene in enumerate(htmlscenes, start=1):
                log('UPDATE:: Scene No %s', count)
                if '. ' in scene:
                    title, writing = scene.split('. ', 1)
                else:
                    title = scene
                    writing = ''

                # if no title and no scene write up
                if not title and not writing:
                    continue
                sceneCount += 1

                newReview = metadata.reviews.new()
                newReview.author = 'IAFD'
                newReview.link  = FILMDICT['SiteURL']
                if len(title) > 40:
                    for i in range(40, -1, -1):
                        if title[i] == ' ':
                            title = title[0:i]
                            break
                newReview.source = '{0}. {1}...'.format(sceneCount, title if title else FILMDICT['Title'])
                if len(writing) > 275:
                    for i in range(275, -1, -1):
                        if writing[i] in ['.', '!', '?']:
                            writing = writing[0:i + 1]
                            break
                newReview.text = utils.TranslateString(writing, lang)
                log(LOG_SUBLINE)
        else:
            log('UPDATE:: Error No Scenes Recorded')

        # 2d.   Summary (IAFD Legend + synopsis + Comments)
        log(LOG_BIGLINE)
        # synopsis
        if FILMDICT['Synopsis']:
            synopsis = FILMDICT['Synopsis']
            log('UPDATE:: Synopsis Found: %s', synopsis)
        else:
            synopsis = ''
            log('UPDATE:: Error No Synopsis Recorded')

        # comments
        log(LOG_SUBLINE)
        if FILMDICT['Comments']:
            comments = FILMDICT['Comments'].replace('##', '\n')
            log('UPDATE:: Comments Found: %s', comments)
        else:
            comments = ''
            log('UPDATE:: Error No Comments Recorded')

        # combine and update
        log(LOG_SUBLINE)
        summary = ('{0}\n{1}').format(synopsis.strip(), comments.strip())
        summary = utils.TranslateString(summary, lang)
        summary = ('{0}\n{1}' if PREFIXLEGEND else '{1}\n{0}').format(FILMDICT['CastLegend'], summary)
        summary = summary.replace('\n\n', '\n')
        metadata.summary = summary

        log(LOG_BIGLINE)
        log('UPDATE:: Finished Update Routine')
        log(LOG_BIGLINE)