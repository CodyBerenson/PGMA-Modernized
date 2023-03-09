#!/usr/bin/env python
# encoding=utf8
'''
# IAFD - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    19 Aug 2022     2020.04.22.17   Multiple Improvements and major rewrites
                                    - tidy up of genres as they have different names across various websites.
                                    - tidy up of countries and locations
                                    - introduced Grouped Collections and Default to keep track of films
    05 Dec 2022     2020.04.22.18   Updated to use latest version of utils.py
    26 Feb 2023     2020.04.22.19   Restrict search string to 72 Characters

-----------------------------------------------------------------------------------------------------------------------------------
'''
import copy, json, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2020.04.22.18'
AGENT = 'IAFD'
AGENT_TYPE = '⚣'   # '⚤' if straight agent and ⚢ if lesbian

# URLS
WATERMARK = 'https://cdn0.iconfinder.com/data/icons/mobile-device/512/lowcase-letter-d-latin-alphabet-keyboard-2-32.png'

# Website Language
SITE_LANGUAGE = 'en'

# Preferences
MATCHSITEDURATION = ''

# dictionaries & Set for holding film variables, genres and countries
FILMDICT = {}

# utils.log section separators
LOG_BIGLINE = '-' * 140
LOG_SUBLINE = '      ' + '-' * 100
LOG_ASTLINE = '*' * 140
# ----------------------------------------------------------------------------------------------------------------------------------
# imports placed here to use previously declared variables
import utils

# ----------------------------------------------------------------------------------------------------------------------------------
def Start():
    ''' initialise process '''
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'
    HTTP.Headers['Referer'] =  'https://www.iafd.com'

    utils.setupStartVariables()
    ValidatePrefs()

# ----------------------------------------------------------------------------------------------------------------------------------
def ValidatePrefs():
    ''' Validate Changed Preferences '''
    pass

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
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            utils.log('SEARCH:: {0:<29} {1}'.format('Error: Missing Media Item File', 'QUIT'))
            return

        #clear-cache directive
        if media.name == "clear-cache":  
            HTTP.ClearCache()
            results.Append(MetadataSearchResult(id='clear-cache', name='Plex web cache cleared', year=media.year, lang=lang, score=0))
            utils.log('SEARCH:: {0:<29} {1}'.format('Warning: Clear Cache Directive Encountered', 'QUIT'))
            return

        utils.logHeader('SEARCH', media, lang)

        # Check filename format
        try:
            FILMDICT = utils.matchFilename(media)
            FILMDICT['lang'] = lang
            FILMDICT['Agent'] = AGENT
        except Exception as e:
            utils.log('SEARCH:: Error: %s', e)
            return

        utils.log(LOG_BIGLINE)
        utils.log('SEARCH:: Check for Film on IAFD:')
        utils.getFilmOnIAFD(FILMDICT)
        utils.log(LOG_BIGLINE)

        if FILMDICT['FoundOnIAFD'] == 'Yes':
            FILMDICT['id'] = media.id
            myID = json.dumps(FILMDICT, default=utils.jsonDumper)
            results.Append(MetadataSearchResult(id=myID, name=FILMDICT['Title'], score=100, lang=lang))

            # Film Scraped Sucessfully - update status and break out!
            FILMDICT['Status'] = True

        # End Search Routine
        utils.logFooter('SEARCH', FILMDICT)
        return FILMDICT['Status']

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        utils.logHeader('UPDATE', media, lang)

        utils.log('UPDATE:: Convert Date Time & Set Objects:')
        FILMDICT = json.loads(metadata.id, object_hook=utils.jsonLoader)
        utils.log(LOG_BIGLINE)

        utils.printFilmInformation(FILMDICT)

        FILMDICT['Status'] = True

        # update the metadata
        utils.log(LOG_BIGLINE)
        if FILMDICT['Status'] is True:
            utils.log(LOG_BIGLINE)
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

            2.  Metadata retrieved from website
                a. Originally Availiable Date
                b. Ratings
                c. Genres                           : List of Genres (alphabetic order)
                d. Countries
                e. Cast                             : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
                f. Directors                        : List of Directors (alphabetic order)
                g. Collections                      : retrieved from FILMDICT, Genres, Countries, Cast Directors
                h. Posters
                i. Art (Background)
                j. Reviews
                k. Chapters
                l. Summary
            '''
            utils.setMetadata(metadata, media, FILMDICT)

        # Failure: initialise original availiable date, so that one can find titles sorted by release date which are not scraped
        if FILMDICT['Status'] is False:
            metadata.originally_available_at = None
            metadata.year = 0

        utils.logFooter('UPDATE', FILMDICT)
        return FILMDICT['Status']