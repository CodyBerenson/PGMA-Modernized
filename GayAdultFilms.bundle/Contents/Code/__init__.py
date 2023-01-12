#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# GayAdultFilms
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    22 Apr 2020   2020.02.07.01    Creation: Agent For Films
    03 Jun 2020   2020.02.07.02    pylint standards implementation
    25 Jun 2020   2020.02.07.03    Improvement to Summary Translation: Translate into Plex Library Language
    12 Jul 2020   2020.02.07.04    added PornTeam scrapper - changed plist and readme files
    02 Jul 2022   2020.02.07.05    added genre/country tidy up and NFO creator

---------------------------------------------------------------------------------------------------------------
'''
import os, platform, re

AGENT = 'GayAdultFilms'
VERSION_NO = '2020.02.07.05'

# log section separators
LOG_BIGLINE = '---------------------------------------------------------------------------------'
LOG_SUBLINE = '      ---------------------------------------------------------------------------'
LOG_ASTLINE = '*********************************************************************************'

SITE_LANGUAGE = ''

# ----------------------------------------------------------------------------------------------------------------------------------
def Start():
    ''' initialise process '''
    pass

# ----------------------------------------------------------------------------------------------------------------------------------
def ValidatePrefs():
    ''' Validate Changed Preferences '''
    pass

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
class GayAdultFilms(Agent.Movies):
    ''' define Agent class '''
    name = 'Gay Adult Films'
    primary_provider = True
    media_types = ['Movie']
    accepts_from = ['com.plexapp.agents.localmedia']
    languages = [Locale.Language.Arabic, Locale.Language.Catalan, Locale.Language.Chinese, Locale.Language.Czech, Locale.Language.Danish,
                 Locale.Language.Dutch, Locale.Language.English, Locale.Language.Estonian, Locale.Language.Finnish, Locale.Language.French,
                 Locale.Language.German, Locale.Language.Greek, Locale.Language.Hebrew, Locale.Language.Hindi, Locale.Language.Hungarian,
                 Locale.Language.Indonesian, Locale.Language.Italian, Locale.Language.Japanese, Locale.Language.Korean, Locale.Language.Latvian,
                 Locale.Language.Norwegian, Locale.Language.Persian, Locale.Language.Polish, Locale.Language.Portuguese, Locale.Language.Romanian,
                 Locale.Language.Russian, Locale.Language.Slovak, Locale.Language.Spanish, Locale.Language.Swahili, Locale.Language.Swedish,
                 Locale.Language.Thai, Locale.Language.Turkish, Locale.Language.Ukrainian, Locale.Language.Vietnamese,
                 Locale.Language.NoLanguage, Locale.Language.Unknown]

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return
        log(LOG_BIGLINE)
        header = 'SEARCH'
        log('%s:: Version:                      v.%s', header, VERSION_NO)
        log('%s:: Python:                       %s %s', header, platform.python_version(), platform.python_build())
        log('%s:: Platform:                     %s - %s %s', header, platform.machine(), platform.system(), platform.release())
        log('%s:: Preferences:', header)
        log('%s:: Media Title:                  %s', header, media.title)
        log('%s:: File Path:                    %s', header, media.items[0].parts[0].file)
        log(LOG_BIGLINE)

        results.Append(MetadataSearchResult(id=media.id, name=media.name, score=85, lang=lang))
        return

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang):
        ''' Update Media Entry '''
        log(LOG_BIGLINE)
        header = 'UPDATE'
        log('%s:: Version:                      v.%s', header, VERSION_NO)
        log('%s:: Python:                       %s %s', header, platform.python_version(), platform.python_build())
        log('%s:: Platform:                     %s - %s %s', header, platform.machine(), platform.system(), platform.release())
        log('%s:: Preferences:', header)
        log('%s:: Media Title:                  %s', header, media.title)
        log('%s:: File Path:                    %s', header, media.items[0].parts[0].file)
        log(LOG_BIGLINE)

        ''' - LEFT FOR SAFEKEEP - MAY USE TO GENERATE NFOS
        # Check filename format
        try:
            FILMDICT = utils.matchFilename(media)
            FILMDICT['lang'] = lang
        except Exception as e:
            utils.log('UPDATE:: Error: %s', e)
            return

        utils.log(LOG_BIGLINE)

        PLEXTOKEN RETRIEVED FROM - %LOCALAPPDATA%\Plex\Plex Media Server\Preferences.xml - path built by PlexSupportPath.replace('Plex', 'Plex\Plex')

        # Access XML Film Source: Manually done by clicking on the humburger dots, then get info and view XML Source
        metadataURL = 'http://127.0.0.1:32400/library/metadata/{0}?X-Plex-Token={1}'.format(metadata.id, PLEXTOKEN)
        xml = XML.ElementFromURL(metadataURL, sleep=5)
        strxml = XML.StringFromElement(xml)
        utils.log('UPDATE:: HTML Page Contents:\r\n%s', xml)

        setGenres = set()
        setCountries = set()
        setCast = set()
        setDirector = set()
        setCollections = set()
        setUntidy = set()  # used to store untidiable genres

        #   1.  Get Genres 
        utils.log(LOG_BIGLINE)
        utils.log('UPDATE:: 1.\tGarner Genres')
        self.showSetData(setUntidy, 'Untidy')
        try:
            htmlgenres = html.xpath('//genre/@tag')
            htmlgenres.sort(key = lambda x: x.lower())
            utils.log('UPDATE:: {0:<29} {1}'.format('Genres', '{0:>2} - {1}'.format(len(htmlgenres), htmlgenres)))
            for idx, item in enumerate(htmlgenres, start=1):
                newItem = TIDYDICT[item] if item in TIDYDICT else ''
                utils.log('UPDATE:: {0:<29} {1}'.format('Genre: Old / New', '{0:>2} - {1} / {2}'.format(idx, item, newItem)))
                if newItem is None:        # Don't process
                    continue

                if newItem == '':         # item not in tidy list
                    setUntidy.add(item)

                setGenres.add(newItem if newItem else item)

            utils.log(LOG_SUBLINE)
            self.showSetData(setGenres, 'New Genres')

        except Exception as e:
            utils.log('UPDATE:: Error Getting Genres: %s', e)

        #   2.  Get Countries
        utils.log(LOG_BIGLINE)
        utils.log('UPDATE:: 2.\tGarner Countries')
        self.showSetData(setUntidy, 'Untidy')
        try:
            htmlcountries = html.xpath('//country/@tag')
            htmlcountries.sort(key = lambda x: x.lower())
            utils.log('UPDATE:: {0:<29} {1}'.format('Countries', '{0:>2} - {1}'.format(len(htmlcountries), htmlcountries)))
            for idx, item in enumerate(htmlcountries, start=1):
                newItem = TIDYDICT[item] if item in TIDYDICT else ''
                utils.log('UPDATE:: {0:<29} {1}'.format('Country: Old / New', '{0:>2} - {1} / {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem == '':
                    setUntidy.add(item)

                setCountries.add(newItem if newItem else item)

            utils.log(LOG_SUBLINE)
            self.showSetData(setCountries, 'New Countries')

        except Exception as e:
            utils.log('UPDATE:: Error Getting Countries: %s', e)

        #   3.  Get Cast
        utils.log(LOG_BIGLINE)
        utils.log('UPDATE:: 3.\tGarner Cast')
        self.showSetData(setUntidy, 'Untidy')
        try:
            htmlcast = html.xpath('//role/@tag')
            htmlcast.sort(key = lambda x: x.lower())
            utils.log('UPDATE:: {0:<29} {1}'.format('Cast', '{0:>2} - {1}'.format(len(htmlcast), htmlcast)))
            setCast = set(htmlcast)
            setUntidy.update(setCast)

        except Exception as e:
            utils.log('UPDATE:: Error Getting Cast: %s', e)

        #   4.  Get Directors
        utils.log(LOG_BIGLINE)
        utils.log('UPDATE:: 4.\tGarner Directors')
        self.showSetData(setUntidy, 'Untidy')
        try:
            htmldirectors = html.xpath('//director/@tag')
            htmldirectors.sort(key = lambda x: x.lower())
            utils.log('UPDATE:: {0:<29} {1}'.format('Directors', '{0:>2} - {1}'.format(len(htmldirectors), htmldirectors)))
            setDirector = set(htmldirectors)
            setUntidy.update(setDirector)

        except Exception as e:
            utils.log('UPDATE:: Error Getting Directors: %s', e)

        #   5.  Get Collections
        #       Collections could be manually set, from cast, from filename etc - all that can't be determined will be put in untidy set 
        utils.log(LOG_BIGLINE)
        utils.log('UPDATE:: 5.\tGarner Collections')
        self.showSetData(setUntidy, 'Untidy')
        try:
            htmlcollections = html.xpath('//collection/@tag')
            htmlcollections.sort(key = lambda x: x.lower())
            utils.log('UPDATE:: {0:<29} {1}'.format('Collections', '{0:>2} - {1}'.format(len(htmlcollections), htmlcollections)))
            for idx, item in enumerate(htmlcollections, start=1):
                if item == 'Stacked':    # will be reset later
                    continue

                newItem = TIDYDICT[item] if item in TIDYDICT else ''
                utils.log('UPDATE:: {0:<29} {1}'.format('Collection: Old / New', '{0:>2} - {1} / {2}'.format(idx, item, newItem)))

                if newItem is None:        # Don't process
                    continue

                if newItem == '':         # collection not found in Tidy Dictionary
                    setUntidy.add(item)

                # this could be a manually added collection
                setCollections.add(newItem if newItem else item)

            utils.log(LOG_SUBLINE)
            self.showSetData(setCollections, 'New Collections')

        except Exception as e:
            utils.log('UPDATE:: Error Getting Collections: %s', e)

        #   6.  Set Tidied Genres
        utils.log(LOG_BIGLINE)
        utils.log('UPDATE:: 6.\tSet Genres')
        self.showSetData(setUntidy, 'Untidy')
        metadata.genres.clear()
        try:
            listGenres = list(setGenres)
            listGenres.sort(key = lambda x: x.lower())
            for idx, item in enumerate(listGenres, start=1):
                metadata.genres.add(item)
                setUntidy.discard(item)
                utils.log('UPDATE:: {0:<29} {1}'.format('Genre', '{0:>2} - {1}'.format(idx, item)))

        except Exception as e:
            utils.log('UPDATE:: Error Setting Genres: %s', e)

        #   7.  Set Tidied Countries
        utils.log(LOG_BIGLINE)
        utils.log('UPDATE:: 7.\tSet Countries')
        self.showSetData(setUntidy, 'Untidy')
        metadata.countries.clear()
        try:
            listCountries = list(setCountries)
            listCountries.sort(key = lambda x: x.lower())
            for idx, item in enumerate(listCountries, start=1):
                metadata.countries.add(item)
                setUntidy.discard(item)
                utils.log('UPDATE:: {0:<29} {1}'.format('Country', '{0:>2} - {1}'.format(idx, item)))

        except Exception as e:
            utils.log('UPDATE:: Error Setting Countries: %s', e)

        #   8.  Set Tidied Collections - also include untidy ones
        utils.log(LOG_BIGLINE)
        utils.log('UPDATE:: 8.\tSet Collections')
        self.showSetData(setUntidy, 'Untidy')
        metadata.collections.clear()
        try:
            # if film is stacked, add this to the collection
            if FILMDICT['Stacked'] == 'Yes':
                setCollections.add('Stacked')

            # Check Preferences and set Collections accordingly
            if COLCAST:
                setCollections.update(setCast)
                listCollections = list(setCollections)
                listCollections.sort(key = lambda x: x.lower())
                utils.log('UPDATE:: {0:<29} {1}'.format('Added Cast to Collection', '{0:>2} - {1}'.format(len(listCollections), listCollections)))

            if COLCOUNTRY:
                setCollections.update(setCountries)
                listCollections = list(setCollections)
                listCollections.sort(key = lambda x: x.lower())
                utils.log('UPDATE:: {0:<29} {1}'.format('Added Countries to Collection', '{0:>2} - {1}'.format(len(listCollections), listCollections)))

            if COLDIRECTOR:
                setCollections.update(setDirector)
                listCollections = list(setCollections)
                listCollections.sort(key = lambda x: x.lower())
                utils.log('UPDATE:: {0:<29} {1}'.format('Added Directors to Collection', '{0:>2} - {1}'.format(len(listCollections), listCollections)))

            if COLGENRE:
                setCollections.update(setGenres)
                listCollections = list(setCollections)
                listCollections.sort(key = lambda x: x.lower())
                utils.log('UPDATE:: {0:<29} {1}'.format('Added Genres to Collection', '{0:>2} - {1}'.format(len(listCollections), listCollections)))

            if COLSERIES and FILMDICT['Series']:
                for series in FILMDICT['Series']:
                    setCollections.add(series)
                listCollections = list(setCollections)
                listCollections.sort(key = lambda x: x.lower())
                utils.log('UPDATE:: {0:<29} {1}'.format('Added Series to Collection', '{0:>2} - {1}'.format(len(listCollections), listCollections)))

            if COLSTUDIO:
                setCollections.add(FILMDICT['Studio'])
                listCollections = list(setCollections)
                listCollections.sort(key = lambda x: x.lower())
                utils.log('UPDATE:: {0:<29} {1}'.format('Added Studio to Collection', '{0:>2} - {1}'.format(len(listCollections), listCollections)))

            # sort collection and add to metadata
            listCollections = list(setCollections)
            listCollections.sort(key = lambda x: x.lower())
            for idx, item in enumerate(listCollections, start=1):
                metadata.collections.add(item)
                setUntidy.discard(item)
                utils.log('UPDATE:: {0:<29} {1}'.format('Collection', '{0:>2} - {1}'.format(idx, item)))

        except Exception as e:
            utils.log('UPDATE:: Error Setting Collections: %s', e)

        #   9.  Set untidy data - use writers field
        utils.log(LOG_BIGLINE)
        utils.log('UPDATE:: 9.\tSet Untidied (Writers)')
        self.showSetData(setUntidy, 'Untidy')
        try:
            metadata.writers.clear()
            listUntidy = list(setUntidy)
            listUntidy.sort(key = lambda x: x.lower())
            for idx, item in enumerate(listUntidy, start=1):
                metadata.writers.add(item)
                utils.log('UPDATE:: {0:<29} {1}'.format('Untidy', '{0:>2} - {1}'.format(idx, item)))

        except Exception as e:
            utils.log('UPDATE:: Error Setting Untidy: %s', e)
        '''
        log(LOG_BIGLINE)
        log('UPDATE:: Finished Update Routine')
        log(LOG_BIGLINE)