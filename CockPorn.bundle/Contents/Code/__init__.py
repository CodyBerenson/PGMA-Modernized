# Gay Scenes
import platform

# Description: Updated for the changes to the new site.
PLUGIN_LOG_TITLE='Cock Porn'	# Log Title

VERSION_NO = '2017.07.26.1'

def Start():
	pass

class CockPornAgent(Agent.Movies):
	name = 'Gay Adult'
	languages = [Locale.Language.NoLanguage, Locale.Language.English]
	primary_provider = True
	accepts_from=['com.plexapp.agents.localmedia']

	def Log(self, message, *args):
		if Prefs['debug']:
			Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

	def search(self, results, media, lang):
		self.Log('-----------------------------------------------------------------------')
		self.Log('SEARCH CALLED v.%s', VERSION_NO)
		self.Log('SEARCH - Platform: %s %s', platform.system(), platform.release())
		self.Log('SEARCH - media.filename - %s', media.filename.split('%2F')[-1])
		self.Log('SEARCH - results - %s', results)
		self.Log('SEARCH - media.title - %s', media.title)
		results.Append(MetadataSearchResult(id=media.id, name=media.name, score = 86, lang = lang))
		self.Log('SEARCH - %s', results)


	def update(self, metadata, media, lang):
		self.Log('UPDATE CALLED')
