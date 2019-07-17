# BelAmi Plex Agent
import re, os, platform, urllib, io, requests
import calendar;
import time;
from difflib import SequenceMatcher
import xml.etree.ElementTree as xmltree

PLUGIN_LOG_TITLE = 'BelAmi'	# Log Title

VERSION_NO = '2019.02.28.10'
REQUEST_DELAY = 0
BASE_VIDEO_DETAILS_URL = 'https://newtour.belamionline.com/content_video.aspx?VideoID=%s'
file_name_pattern = re.compile(Prefs['regex'])

def Start():
	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
        'Windows NT 6.3; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
        '.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

class BelAmi(Agent.Movies):
	name = 'BelAmi'
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
		self.Log('SEARCH - Prefs->cover - %s', Prefs['cover'])
		self.Log('SEARCH - Prefs->folders - %s', Prefs['folders'])
		self.Log('SEARCH - Prefs->regex - %s', Prefs['regex'])

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
		html = HTML.ElementFromURL(movie_url)

		webpage = requests.get(movie_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"}).text
		Log(webpage)
		video_title = html.xpath('//*[@id="LabelModelNames"]/text()')
		Log(video_title)
		results.Append(MetadataSearchResult(id = movie_url_name, name = video_title, score = 100, lang = lang))

	def update(self, metadata, media, lang, force=False):
		self.Log('UPDATE CALLED')

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.Log('UPDATE - File Path: %s', file_path)
		self.Log('UPDATE - Video URL: %s', metadata.id)
		url = BASE_VIDEO_DETAILS_URL % metadata.id

		# Fetch HTML
		html = HTML.ElementFromURL(url + "&v=" + str(calendar.timegm(time.gmtime())), sleep=REQUEST_DELAY)

		# Set tagline to URL
		metadata.tagline = url
		try:
			video_title = html.xpath('//span[@id="LabelModelNames"]/text()')[0]
			self.Log("UPDATE - Video title: %s", video_title)
		except Exception as e:
			self.Log("UPDATE - Error setting title: %s", html.xpath('//span[@id="LabelModelNames"]/text()'))
			pass
		#
		# Try to get description text
		try:
			raw_about_text = html.xpath('//span[@id="LabelDescription"]/text()')[0]
			metadata.summary=raw_about_text
			self.Log("UPDATE - Video summary: %s", metadata.summary)
		except Exception as e:
			self.Log('UPDATE - Error getting description text: %s', e)
			pass

		valid_art_names = list()
		valid_art_names.append("https://medusa.vigue.me/baol.png")
		metadata.art["https://medusa.vigue.me/baol.png"] = Proxy.Media(HTTP.Request("https://medusa.vigue.me/baol.png"), sort_order=1)

		# Try to get and process the video cast
		metadata.roles.clear()
		rolethumbs = list();
		actor_image_list = html.xpath("//div[@class='PanelActorImage']/div/img")
		for actor_image in actor_image_list:
			actor_img = actor_image.get('src');
			Log(actor_img)
			rolethumbs.append(actor_img);
		htmlcast = html.xpath("//div[@class='PanelActorImage']/div/span/text()")
		self.Log('UPDATE - cast: "%s"', htmlcast)
		index = 0
		for cast in htmlcast:
			cname = cast.strip()
			if (len(cname) > 0):
				role = metadata.roles.new()
				role.name = cname
				role.photo = rolethumbs[index]
			index += 1

		# Try to get and process the video genres
		metadata.genres.add("BelAmi")
		metadata.collections.add("BelAmi")
		metadata.art.validate_keys(valid_art_names)
		metadata.content_rating = 'X'
		metadata.title = video_title
		metadata.studio = "BelAmi"

