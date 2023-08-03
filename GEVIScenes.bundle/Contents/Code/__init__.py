#!/usr/bin/env python
# encoding=utf8
'''
# GEVIScenes - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    27 May 2023     2023.05.27.01   New Scraper for GEVI Episodes (Scenes)
    01 Jul 2023     2023.05.27.02   Updated to use new utils.py
    07 Jul 2023     2023.05.27.03   GEVI Website Design Change - implement new xpath
-----------------------------------------------------------------------------------------------------------------------------------
'''
import copy, json, os, re
from datetime import datetime

# Version / Log Title
VERSION_NO = '2023.05.27.03'
AGENT = 'GEVIScenes'
AGENT_TYPE = '⚣'   # '⚤' if straight agent

# URLS
BASE_URL = 'https://www.gayeroticvideoindex.com'
BASE_SEARCH_URL = BASE_URL + '/episode/{0}'

# Date Formats used by website
DATEFORMAT = '%Y-%m-%d'

# Website Language
SITE_LANGUAGE = 'en'

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
    HTTP.Headers['User-Agent'] = utils.getUserAgent()
    HTTP.Headers['Referer'] = 'https://gayeroticvideoindex.com/search'

# ----------------------------------------------------------------------------------------------------------------------------------
class GEVIScenes(Agent.Movies):
    ''' define Agent class '''
    name = 'GEVIScenes (IAFD)'
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultScenes']

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            utils.log(LOG_ASTLINE)
            utils.log('SEARCH:: {0:<29} {1}'.format('Error: Missing Media Item File', 'QUIT'))
            utils.log(LOG_ASTLINE)
            return

        #clear-cache directive
        if media.name == "clear-cache":
            HTTP.ClearCache()
            results.Append(MetadataSearchResult(id='clear-cache', name='Plex web cache cleared', year=media.year, lang=lang, score=0))
            utils.log(LOG_ASTLINE)
            utils.log('SEARCH:: {0:<29} {1}'.format('Warning: Clear Cache Directive Encountered', 'QUIT'))
            utils.log(LOG_ASTLINE)
            return

        AGENTDICT = copy.deepcopy(utils.setupAgentVariables(media))
        if not AGENTDICT:
            utils.log(LOG_ASTLINE)
            utils.log('SEARCH:: {0:<29} {1}'.format('Erro: Could Not Set Agent Parameters', 'QUIT'))
            utils.log(LOG_ASTLINE)
            return

        utils.logHeader('SEARCH', AGENTDICT, media, lang)

        # Check filename format
        try:
            FILMDICT = copy.deepcopy(utils.matchFilename(AGENTDICT, media))
            FILMDICT['lang'] = lang
            FILMDICT['Agent'] = AGENT
            FILMDICT['Status'] = False
        except Exception as e:
            utils.log(LOG_ASTLINE)
            utils.log('SEARCH:: Error: {0}'.format(e))
            utils.log(LOG_ASTLINE)
            return

        utils.log(LOG_BIGLINE)

        # Search Query
        if FILMDICT['GEVIScene']:
            searchQuery = BASE_SEARCH_URL.format(FILMDICT['GEVIScene'])
            utils.log('SEARCH:: Search Query: {0}'.format(searchQuery))
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=utils.delay())
                process = True
            except Exception as e:
                utils.log('SEARCH:: Error: Search Query did not pull a result: {0}'.format(e))
                process = False
                return
        else:
            return

        if process is True:
            myYear = '({0})'.format(FILMDICT['Year']) if FILMDICT['Year'] else ''
            utils.log('SEARCH:: {0:<29} {1}'.format('Processing', '{0} - {1} {2}'.format(FILMDICT['Studio'], FILMDICT['Title'], myYear)))
            utils.log(LOG_BIGLINE)

        # Site Title
        if process is True:
            try:
                siteTitle = html.xpath('//section/h1/text()')[0].strip()
                utils.matchTitle(siteTitle, FILMDICT)
            except Exception as e:
                utils.log('SEARCH:: Error getting Site Title: {0}'.format(e))
                utils.log(LOG_SUBLINE)
                process = False

        # Site Title URL
        if process is True:
            utils.log(LOG_BIGLINE)
            FILMDICT['FilmURL'] = searchQuery
            utils.log('SEARCH:: {0:<29} {1}'.format('Site Title URL', searchQuery))

        # Studio Name
        if process is True:
            utils.log(LOG_BIGLINE)
            try:
                siteStudio = html.xpath('//a[contains(@href, "company/")]/text()')[0].strip()
                utils.matchStudio(siteStudio, FILMDICT)
            except Exception as e:
                utils.log('SEARCH:: Error getting Site Studio: {0}'.format(e))
                utils.log(LOG_SUBLINE)
                process = False

        # Site Release Date
        vReleaseDate = None
        if process is True:
            utils.log(LOG_BIGLINE)
            try:
                siteReleaseDate = html.xpath('//div[span[.="Date:"]]/text()')[1].strip()
                utils.log('SEARCH:: {0:<29} {1}'.format('Site URL Release Date', siteReleaseDate))
                try:
                    releaseDate = datetime.strptime(siteReleaseDate, DATEFORMAT)
                    utils.matchReleaseDate(releaseDate, FILMDICT)
                    vReleaseDate = releaseDate
                except Exception as e:
                    if FILMDICT['Year']:
                        utils.log(LOG_SUBLINE)
                        process = False
            except:
                utils.log('SEARCH:: Error getting Site URL Release Date: Default to Filename Date')
                vReleaseDate = FILMDICT['CompareDate']

        if process is True:
            FILMDICT['vCompilation'] = ''
            FILMDICT['vDuration'] = FILMDICT['Duration']
            FILMDICT['vReleaseDate'] = vReleaseDate

            myID = json.dumps(FILMDICT, default=utils.jsonDumper)
            results.Append(MetadataSearchResult(id=myID, name=FILMDICT['Title'], score=100, lang=lang))

        # Film Scraped Sucessfully - update status and break out!
        FILMDICT['Status'] = process

        # End Search Routine
        utils.logFooter('SEARCH', FILMDICT)
        return FILMDICT['Status']

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        utils.updateMetadata(metadata, media, lang, force=True)
