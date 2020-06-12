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

---------------------------------------------------------------------------------------------------------------
'''
import platform, sys

PLUGIN_LOG_TITLE = 'GayAdultFilms'
VERSION_NO = '2020.02.07.02'

# ----------------------------------------------------------------------------------------------------------------------------------
def Start():
    ''' initialise process '''
    pass

# ----------------------------------------------------------------------------------------------------------------------------------
class GayAdultFilms(Agent.Movies):
    ''' define Agent class '''
    name = 'Gay Adult Films'
    languages = [Locale.Language.NoLanguage, Locale.Language.English]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia']

    # -------------------------------------------------------------------------------------------------------------------------------
    def log(self, message, *args):
        ''' log messages '''
        Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version         : v.%s', VERSION_NO)
        self.log('SEARCH:: Python          : %s', sys.version_info)
        self.log('SEARCH:: Platform        : %s %s', platform.system(), platform.release())
        self.log('SEARCH:: results         : %s', results)
        self.log('SEARCH:: media.title     : %s', media.title)
        self.log('-----------------------------------------------------------------------')

        results.Append(MetadataSearchResult(id=media.id, name=media.name, score=86, lang=lang))
        self.log('SEARCH - %s', results)

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang):
        ''' Update Media Entry '''
        self.log('-----------------------------------------------------------------------')
        self.log('UPDATE CALLED')
        self.log('UPDATE:: Version    : v.%s', VERSION_NO)
        self.log('-----------------------------------------------------------------------')
