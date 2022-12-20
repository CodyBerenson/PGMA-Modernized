#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable=W0702, W0703, C0103, C0410
# encoding=utf8
'''
# GayAdult
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    22 Apr 2020   2020.02.07.01    Creation: Agent For mixed content Films and Scenes
    03 Jun 2020   2020.02.07.02    pylint standards implementation
    25 Jun 2020   2020.02.07.03    Improvement to Summary Translation: Translate into Plex Library Language
    12 Jul 2020   2020.02.07.04    added PornTeam scrapper - changed plist and readme files

---------------------------------------------------------------------------------------------------------------
'''
import platform, sys

AGENT = 'GayAdult'
VERSION_NO = '2020.02.07.04'

# ----------------------------------------------------------------------------------------------------------------------------------
def Start():
    ''' initialise process '''
    pass

# ----------------------------------------------------------------------------------------------------------------------------------
class GayAdult(Agent.Movies):
    ''' define Agent class '''
    name = 'Gay Adult'
    primary_provider = True
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
    def log(self, message, *args):
        ''' log messages '''
        Log(AGENT + ' - ' + message, *args)

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
