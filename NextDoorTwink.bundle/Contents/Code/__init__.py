#NDT Plex Agent
import re, os, platform, urllib
from difflib import SequenceMatcher

#Fix HTTPS errors when connecting to Facebox (neural.vigue.me) and Thumbor CDN (cdn.vigue.me)
import certifi
import requests


PLUGIN_LOG_TITLE = 'NextDoorTwink'	# Log Title

VERSION_NO = '2019.07.22.1'

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL = 'https://www.freshmen.net%s'

# Example Video Details URL
# https://www.helixstudios.net/video/3437/hosing-him-down.html
BASE_VIDEO_DETAILS_URL = 'https://www.nextdoortwink.com/en/PRETTY-URL/film/%s'

# File names to match for this agent
file_name_pattern = re.compile(Prefs['regex'])

def Start():
	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
        'Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
        '.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

class NextDoorTwink(Agent.Movies):
	name = 'NextDoorTwink'
	languages = [Locale.Language.NoLanguage, Locale.Language.English]
	primary_provider = False
	fallback_agent = ['com.plexapp.agents.gayporncollector']
	contributes_to = ['com.plexapp.agents.cockporn']

	def Log(self, message, *args):
		if Prefs['debug']:
			Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

	def intTest(self, s):
		try:
			int(s)
			return int(s)
		except ValueError:
			return False

	def similar(self, a, b):
		return SequenceMatcher(None, a, b).ratio()

	def search(self, results, media, lang, manual):
		self.Log('-----------------------------------------------------------------------')
		self.Log('SEARCH CALLED v.%s', VERSION_NO)
		self.Log('SEARCH - Platform: %s %s', platform.system(), platform.release())
		self.Log('SEARCH - media.title - %s', media.title)
		self.Log('SEARCH - media.items[0].parts[0].file - %s', media.items[0].parts[0].file)
		self.Log('SEARCH - media.primary_metadata.title - %s', media.primary_metadata.title)
		self.Log('SEARCH - media.items - %s', media.items)
		self.Log('SEARCH - media.filename - %s', media.filename)
		self.Log('SEARCH - lang - %s', lang)
		self.Log('SEARCH - manual - %s', manual)

		if not media.items[0].parts[0].file:
			return

		path_and_file = media.items[0].parts[0].file.lower()
		self.Log('SEARCH - File Path: %s', path_and_file)

		(file_dir, basename) = os.path.split(os.path.splitext(path_and_file)[0])
		final_dir = os.path.split(file_dir)[1]

		self.Log('SEARCH - Enclosing Folder: %s', final_dir)

		if Prefs['folders'] != "*":
			folder_list = re.split(',\s*', Prefs['folders'].lower())
			if final_dir not in folder_list:
				self.Log('SEARCH - Skipping %s because the folder %s is not in the acceptable folders list: %s', basename, final_dir, ','.join(folder_list))
				return

		m = file_name_pattern.search(basename)
		if not m:
			self.Log('SEARCH - Skipping %s because the file name is not in the expected format.', basename)
			return

		self.Log('SEARCH - File Name: %s', basename)

		groups = m.groupdict()
		clip_name = groups['clip_name']
		movie_url_name = re.sub('\s+', '+', clip_name)
		movie_url = BASE_VIDEO_DETAILS_URL % movie_url_name
		search_query_raw = list()
		for piece in clip_name.split(' '):
			if re.search('^[0-9A-Za-z]*$', piece.replace('!', '')) is not None:
				search_query_raw.append(piece)

		self.Log('SEARCH - Video URL: %s', movie_url)
		html = HTML.ElementFromURL(movie_url, sleep=REQUEST_DELAY)
		video_title = html.xpath("//h1[@class='title']/text()")[0]
		results.Append(MetadataSearchResult(id = movie_url, name = video_title, score = 100, lang = lang))

	def update(self, metadata, media, lang, force=False):
		self.Log('UPDATE CALLED')

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.Log('UPDATE - File Path: %s', file_path)
		self.Log('UPDATE - Video URL: %s', metadata.id)
		url = metadata.id

		# Fetch HTML
		html = HTML.ElementFromURL(url, sleep=REQUEST_DELAY)

		# Set tagline to URL
		metadata.tagline = url
		video_title = ""
		try:
			metadata.title = html.xpath("//h1[@class='title']/text()")[0]
			video_title = html.xpath("//h1[@class='title']/text()")[0]
			self.Log('UPDATE - video_title: "%s"', metadata.title)
		except Exception as e:
			self.log("UPDATE - error getting title: %s", e)

		# Try to get description text
		try:
			raw_about_text = html.xpath("//p[@class='sceneDesc showMore']/text()")[0]
			self.Log('UPDATE - Description: %s', raw_about_text)
			metadata.summary=raw_about_text
		except Exception as e:
			self.Log('UPDATE - Error getting description text: %s', e)
			pass

		actors = list()
		try:
			metadata.roles.clear()
			htmlcast = html.xpath("//div[@class='sceneCol sceneColActors']/span[not(@class)]/text()")
			for cast in htmlcast:
				if (len(cast) > 0):
					role = metadata.roles.new()
					role.name = cast
					actors.append(cast)
		except Exception as e:
			self.Log('UPDATE - Error getting video cast: %s', e)
			pass

		gevi_scene_url = "";
		try:
			#try first actor
			actor = actors[0];
			actor = actor.replace(" ", "+");
			gevi_search = HTML.ElementFromURL("https://www.gayeroticvideoindex.com/search.php?type=s&where=b&query=" + actor + "&Search=Search&page=1", sleep=REQUEST_DELAY)

			try:
				index = 3
				actor_link = gevi_search.xpath('//*[@class="cd"]/a')[0];
				actor_link = "https://www.gayeroticvideoindex.com" + actor_link.get("href");
				self.Log(actor_link);
				gevi_actor_result = HTML.ElementFromURL(actor_link, sleep=REQUEST_DELAY)
				actor_episodes = gevi_actor_result.xpath('//tr[@class="er"]/td[1]/a/text()')
				self.Log(",".join(actor_episodes))
				indexx = 1
				for episode in actor_episodes:
					if episode == video_title:
						self.Log("UPDATE - Matched with GEVI!")
						release_date = gevi_actor_result.xpath('//*[@id="episodes"]/tr[' + str(indexx) + ']/td[2]/text()')[0]
						gevi_scene_url = "https://www.gayeroticvideoindex.com" + gevi_actor_result.xpath('//*[@id="episodes"]/tr[' + str(indexx) + ']/td[1]/a')[0].get("href")
						self.Log('UPDATE - Release Date - New: %s', release_date)
						metadata.originally_available_at = Datetime.ParseDate(release_date).date()
						metadata.year = metadata.originally_available_at.year
					indexx += 1
			except Exception as e:
				self.Log("Exception getting release date: %s", e)
				pass
		except Exception as e:
			#fuck this
			self.Log("Exception getting release date: %s", e)
			pass

		#get cast extrainfo
		actor_urls = list()
		actors = list()
		actions = list()
		try:
			if gevi_scene_url is not "":
				gevi_episode = HTML.ElementFromURL(gevi_scene_url, sleep=REQUEST_DELAY)
				actors = gevi_episode.xpath('//table[@class="d"]/tbody/tr/td[1]/a/nobr/text()')
				actor_urls = gevi_episode.xpath('//table[@class="d"]/tbody/tr/td[1]/a/@href')
				self.Log("UPDATE - (GEVI) Actors: %s", ",".join(actors))
				self.Log("UPDATE - (GEVI) Actor URLs: %s", ",".join(actor_urls))
				actions = gevi_episode.xpath('//table[@class="d"]/tbody/tr[position()>1]/td[2]/text()')
				self.Log("UPDATE - (GEVI) Actions: %s", ",".join(actions))
		except Exception as e:
			self.Log("UPDATE - (GEVI) Error getting cast extras: %s", e)

		

		metadata.collections.add("NextDoorTwink")
		#metadata.posters.validate_keys(valid_image_names)
		metadata.content_rating = 'X'
		metadata.studio = "NextDoorStudios"

