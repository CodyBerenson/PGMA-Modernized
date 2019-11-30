#NDS Plex Agent
#Matches ALL subsites!
#Matches with <video ID>.mp4 OR title.mp4!

import re, os, platform, urllib
from difflib import SequenceMatcher

#Fix HTTPS errors when connecting to Facebox (neural.vigue.me) and Thumbor CDN (cdn.vigue.me)
import certifi
import requests

PLUGIN_LOG_TITLE = 'NextDoorStudios'	# Log Title

VERSION_NO = '2019.11.30.166'
REQUEST_DELAY = 0
BASE_VIDEO_DETAILS_URL = 'https://www.nextdoorstudios.com/en/show/nextdoorworld/%s'
BASE_VIDEO_SEARCH_URL = 'https://www.nextdoorstudios.com/en/search/%s'

# File names to match for this agent
file_name_pattern = re.compile(Prefs['regex'])

def Start():
	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
        'Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
        '.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

class NextDoorStudios(Agent.Movies):
	name = 'NextDoorStudios'
	languages = [Locale.Language.NoLanguage, Locale.Language.English]
	primary_provider = False
	fallback_agent = ['com.plexapp.agents.gayporncollector']
	contributes_to = ['com.plexapp.agents.cockporn']

	def Log(self, message, *args):
		if Prefs['debug']:
			Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

	def noNegative(self, value):
		if(value < 0):
			return 0
		else:
			return value

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
		if basename.isdigit():
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
			return
		else:
			groups = m.groupdict()
			clip_name = groups['clip_name']
			movie_url_name = re.sub('\s+', '+', clip_name)
			movie_url = BASE_VIDEO_SEARCH_URL % movie_url_name
			search_query_raw = list()
			for piece in clip_name.split(' '):
				if re.search('^[0-9A-Za-z]*$', piece.replace('!', '')) is not None:
					search_query_raw.append(piece)

			self.Log('SEARCH - Video URL: %s', movie_url)
			html = HTML.ElementFromURL(movie_url, sleep=REQUEST_DELAY)

			search_results = html.xpath("//*[contains(concat(' ',normalize-space(@class),' '),' tlcContentPage ')]/div")
			score=10
			# Enumerate the search results looking for an exact match. The hope is that by eliminating special character words from the title and searching the remainder that we will get the expected video in the results.
			if search_results:
				for result in search_results:
					video_title = result.xpath("//div[@class='tlcDetails']/div[1]/a").text
					video_title = re.sub("[\:\?\|]", '', video_title)
					video_title = re.sub("\s{2,4}", ' ', video_title)
					video_title = video_title.rstrip(' ')

					self.Log('SEARCH - video title percentage: %s', self.similar(video_title.lower(), clip_name.lower()))

					self.Log('SEARCH - video title: %s', video_title)
					if self.similar(video_title.lower(), clip_name.lower()) > 0.90:
						video_url=result.find('a')[0].get('href')
						self.Log('SEARCH - video url: %s', video_url)
						self.Log('SEARCH - rating: %s', self.rating)
						self.Log('SEARCH - Exact Match "' + clip_name.lower() + '" == "%s"', video_title.lower())
						results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
						return
					else:
						self.Log('SEARCH - Title not found "' + clip_name.lower() + '" != "%s"', video_title.lower())
						score=score-1
						results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))
			else:
				search_query="+".join(search_query_raw[-2:])
				self.Log('SEARCH - Search Query: %s', search_query)
				html=HTML.ElementFromURL(BASE_VIDEO_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
				search_results = html.xpath("//*[contains(concat(' ',normalize-space(@class),' '),' tlcContentPage ')]/div")
				if search_results:
					for result in search_results:
						video_title = result.xpath("//div[@class='tlcDetails']/div[1]/a").text
						video_title = re.sub("[\:\?\|]", '', video_title)
						video_title = video_title.rstrip(' ')
						self.Log('SEARCH - video title: %s', video_title)
						if video_title.lower() == clip_name.lower():
							video_url=result.find('a')[0].get('href')
							self.Log('SEARCH - video url: %s', video_url)
							self.Log('SEARCH - rating: %s', self.rating)
							self.Log('SEARCH - Exact Match "' + clip_name.lower() + '" == "%s"', video_title.lower())
							results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
							return
						else:
							self.Log('SEARCH - Title not found "' + clip_name.lower() + '" != "%s"', video_title.lower())
							score=score-1
							results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))
				else:
					search_query="+".join(search_query_raw[:2])
					self.Log('SEARCH - Search Query: %s', search_query)
					html=HTML.ElementFromURL(BASE_VIDEO_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
					search_results = html.xpath("//*[contains(concat(' ',normalize-space(@class),' '),' tlcContentPage ')]/div")
					if search_results:
						for result in search_results:
							video_title = result.xpath("//div[@class='tlcDetails']/div[1]/a").text
							video_title = re.sub("[\:\?\|]", '', video_title)
							video_title = video_title.rstrip(' ')
							self.Log('SEARCH - video title: %s', video_title)
							if video_title.lower() == clip_name.lower():
								video_url=result.find('a')[1].get('href')
								self.Log('SEARCH - video url: %s', video_url)
								self.Log('SEARCH - rating: %s', self.rating)
								self.Log('SEARCH - Exact Match "' + clip_name.lower() + '" == "%s"', video_title.lower())
								results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
								return
							else:
								self.Log('SEARCH - Title not found "' + clip_name.lower() + '" != "%s"', video_title.lower())
								results.Append(MetadataSearchResult(id = '', name = media.filename, score = 1, lang = lang))
					else:
						score=1
						self.Log('SEARCH - Title not found "' + clip_name.lower() + '" != "%s"', video_title.lower())
						return

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
			descx = html.xpath("normalize-space(string(//div[@id='sceneInfo']/div[2]))")
			descx = descx.replace("Video Description: ","")
			self.Log('UPDATE - Description: %s', descx)
			metadata.summary=descx
		except Exception as e:
			self.Log('UPDATE - Error getting description text: %s', e)
			pass

		#get the measly ONE poster
		valid_art_names = list()

		actors = list()
		actor_urls = list()
		try:
			metadata.roles.clear()
			htmlcast = html.xpath("//div[@class='sceneCol sceneColActors']/a/text()")
			html_urls = html.xpath("//div[@class='sceneCol sceneColActors']/a")
			for cast in htmlcast:
				if (len(cast) > 0):
					actors.append(cast)
			for url in html_urls:
				actor_urls.append("https://www.nextdoorstudios.com" + url.get("href"))
		except Exception as e:
			self.Log('UPDATE - Error getting video cast: %s', e)
			pass

		valid_image_names = list()
		try:
			if actors != []:
				gsearch = HTML.ElementFromURL("https://bananaguide.com/searchModels/" + actors[0], sleep=REQUEST_DELAY)
				first_result = gsearch.xpath("//div/div/p[2]/a")[0].get("href")
				bananaguide_gallery = HTML.ElementFromURL(first_result, sleep=REQUEST_DELAY)
				images = bananaguide_gallery.xpath('//div[@class="grid-item-wrapper-2"]/a')
				i = 0
				for image in images:
					if i > 1:
						#self.Log(image.get("href"))
						poster_url = "https://bananaguide.com" + image.get("href")

						valid_image_names.append(poster_url)
						if poster_url not in metadata.posters:
							try:
								metadata.posters[poster_url]=Proxy.Media(HTTP.Request(poster_url), sort_order = i-2)
							except Exception as e: 
								pass
					i += 1
		except Exception as e:
			Log(e)

		#get rating
		tu = html.xpath("//span[@class='value']/text()")[0]
		td = html.xpath("//span[@class='value']/text()")[1]
		self.Log("%s - %s", tu, td)
		metadata.rating = float(int(tu) / int(td));

		try:
			release_date = html.xpath("//div[@class='updatedDate']/text()")[1]
			metadata.originally_available_at = Datetime.ParseDate(release_date).date()
			metadata.year = metadata.originally_available_at.year
			self.Log('UPDATE - Release Date - New: %s', release_date)
		except Exception as e:
			self.Log("UPDATE - Error release_date: %s", e)

		gevi_scene_url = "";
		try:
			#search with first actor
			actor = actors[0];
			actor = actor.replace(" ", "+");
			gevi_search = HTML.ElementFromURL("https://www.gayeroticvideoindex.com/search.php?type=s&where=b&query=" + actor + "&Search=Search&page=1", sleep=REQUEST_DELAY)
			try:
				index = 3
				actor_links = gevi_search.xpath('//*[@class="cd"]/a');
				gevi_actor_result = ""
				for gevi_actor_link in actor_links:
					valid = 0
					actor_link = "https://www.gayeroticvideoindex.com" + actor_link.get("href");
					gevi_actor_result = HTML.ElementFromURL(actor_link, sleep=REQUEST_DELAY)
					see_at = gevi_actor_result.xpath("//td[@class='gspr']/div/a/img")
					for see_at_studio in see_at:
						studio_logo = see_at_studio.get("src");
						if studio_logo == "../../images/NextDoorVideo.png":
							#valid actor, exit loop
							Log("Found Actor!")
							Log(actor_link)
							valid = 1
							break
					if valid == 1:
						break
				actor_episodes = gevi_actor_result.xpath('//tr[@class="er"]/td[1]/a/text()')
				indexx = 1
				for episode in actor_episodes:
					if episode.lower() == video_title.lower():
						self.Log("UPDATE - Matched with GEVI!")
						gevi_scene_url = "https://www.gayeroticvideoindex.com" + gevi_actor_result.xpath('//*[@id="episodes"]/tr[' + str(indexx) + ']/td[1]/a')[0].get("href")
					indexx += 1
			except Exception as e:
				self.Log(e)
				pass
		except Exception as e:
			self.Log(e)
			pass

		try:
			metadata.genres.clear()
			genres = html.xpath('//div[@class="sceneCol sceneColCategories"]/a/text()')
			for genre in genres:
				genre = genre.strip()
				if (len(genre) > 0):
					metadata.genres.add(genre)
		except Exception as e:
			Log(e)
			pass

		#get cast extrainfo
		actors = list()
		actions = list()
		try:
			if gevi_scene_url is not "":
				gevi_episode = HTML.ElementFromURL(gevi_scene_url, sleep=REQUEST_DELAY)
				poster_url = "https://www.gayeroticvideoindex.com" + gevi_episode.xpath("//img[@class='episode']")[0].get("src")
				self.Log(poster_url)
				valid_art_names.append(poster_url)
				if poster_url not in metadata.art:
					try:
						metadata.art[poster_url] = Proxy.Media(HTTP.Request(poster_url), sort_order=1)
					except Exception as e: 
						pass
				actors_tmp = gevi_episode.xpath('//a/nobr/text()')
				for actor in actors_tmp:
					actors.append(actor)
				actor_urls_tmp = gevi_episode.xpath('//td[@class="pd"]/a')
				actions_tmp = gevi_episode.xpath('//td[2][@class="pd"]/text()')
				for action in actions_tmp:
					actions.append(action)
					self.Log("actor action found: %s", action)
				if actors != [] and actor_urls != [] and actions != []:
					metadata.roles.clear()
					index = 0
					for actor in actors:
						url = actor_urls[index]
						action = actions[index]

						actionText = ""
						if "Atb" in action:
							actionText = "Flip Top"
						elif "Abt" in action:
							actionText = "Flip Bottom"
						elif "At" in action:
							actionText = "Top"
						elif "Ab" in action:
							actionText = "Bottom"

						role = metadata.roles.new()
						role.name = actor
						role.role = actionText

						#get picture of actor
						actorPage = HTML.ElementFromURL(actor_urls[index], sleep=REQUEST_DELAY)
						headshot_url_hi_res = actorPage.xpath('//img[@class="actorPicture"]')[0].get("src")

						result = requests.post('https://neural.vigue.me/facebox/check', json={"url": headshot_url_hi_res}, verify=certifi.where())
						Log(result.json()["facesCount"])
						if result.json()["facesCount"] == 1:
							box = result.json()["faces"][0]["rect"]
							cropped_headshot = "https://cdn.vigue.me/unsafe/" + str(self.noNegative(box["left"] - 100)) + "x" + str(self.noNegative(box["top"] - 100)) + ":" + str(self.noNegative((box["left"]+box["width"])+100)) + "x" + str(self.noNegative((box["top"]+box["height"])+100)) + "/" + headshot_url_hi_res
						else:
							cropped_headshot = headshot_url_hi_res
						role.photo = cropped_headshot
						index += 1;
		except Exception as e:
			self.Log(e)

		
		metadata.posters.validate_keys(valid_image_names)
		metadata.art.validate_keys(valid_art_names)
		metadata.collections.add(html.xpath("//p[@class='labelContent']/text()")[0])
		metadata.content_rating = 'X'
		metadata.studio = "NextDoorStudios"