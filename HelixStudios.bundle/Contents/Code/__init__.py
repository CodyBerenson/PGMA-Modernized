# HelixStudios
# Matches Scenes, Unsearchable Scenes, and DVDs (dvd's not the same)
#| Sk8 Boys.mp4 | 3392.mp4           | HXM087.mp4                  |

#All metadata imported, with HD stills (yippee!)

import re, os, platform, urllib
from difflib import SequenceMatcher

#Fix HTTPS errors when connecting to Facebox (neural.vigue.me) and Thumbor CDN (cdn.vigue.me)
import certifi
import requests

PLUGIN_LOG_TITLE = 'Helix Studios'	# Log Title

VERSION_NO = '2019.11.03.107'

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL = 'https://www.helixstudios.net%s'

# Example Video Details URL
# https://www.helixstudios.net/video/3437/hosing-him-down.html
BASE_VIDEO_DETAILS_URL = 'https://www.helixstudios.net/video/%s'
BASE_MODEL_DETAILS_URL = 'https://www.helixstudios.net/model/%s/index.html'

# Example Search URL:
# https://www.helixstudios.net/videos/?q=Hosing+Him+Down
BASE_SEARCH_URL = 'https://www.helixstudios.net/videos/?q=%s'

# File names to match for this agent
file_name_pattern = re.compile(Prefs['regex'])

# Example File Name:
# https://media.helixstudios.com/scenes/hx111_scene2/hx111_scene2_member_1080p.mp4
# FILENAME_PATTERN = re.compile("")
# TITLE_PATTERN = re.compile("")

def Start():
	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
        'Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
        '.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

class HelixStudios(Agent.Movies):
	name = 'Helix Studios'
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

		if "hxm" in basename:
			#DVD release, use special indexer
			movie_url_name = movie_url_name.upper()
			video_url = "/movie/" + movie_url_name + "/index.html"
			self.Log('SEARCH - DIRECT DVD MATCH: %s', video_url);
			self.rating = 5
			html = HTML.ElementFromURL("https://www.helixstudios.net" + video_url, sleep=REQUEST_DELAY)
			video_title = html.xpath('//*[@id="rightcolumn"]/div/div/h3/text()')[0]
			results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
			return

		if basename.isdigit():
			#add direct video match & skip search
			video_url = "/video/" + movie_url_name + "/index.html"
			self.Log('SEARCH - DIRECT SCENE MATCH: %s', video_url);
			self.rating = 5
			html = HTML.ElementFromURL("https://www.helixstudios.net" + video_url, sleep=REQUEST_DELAY)
			video_title = html.xpath('//div[@class="scene-title"]/span/text()')[0]
			results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
			return

		movie_url = BASE_SEARCH_URL % movie_url_name
		search_query_raw = list()
		for piece in clip_name.split(' '):
			if re.search('^[0-9A-Za-z]*$', piece.replace('!', '')) is not None:
				search_query_raw.append(piece)

		self.Log('SEARCH - Video URL: %s', movie_url)
		html = HTML.ElementFromURL(movie_url, sleep=REQUEST_DELAY)

		search_results = html.xpath('//*[@class="video-gallery"]/li')

		score=10
		# Enumerate the search results looking for an exact match. The hope is that by eliminating special character words from the title and searching the remainder that we will get the expected video in the results.
		if search_results:
			for result in search_results:
				video_title = result.find('a').find("img").get("alt")
				video_title = re.sub("[\:\?\|]", '', video_title)
				video_title = re.sub("\s{2,4}", ' ', video_title)
				video_title = video_title.rstrip(' ')

				self.Log('SEARCH - video title percentage: %s', self.similar(video_title.lower(), clip_name.lower()))

				self.Log('SEARCH - video title: %s', video_title)
				# Check the alt tag which includes the full title with special characters against the video title. If we match we nominate the result as the proper metadata. If we don't match we reply with a low score.
				#if video_title.lower() == clip_name.lower():
				if self.similar(video_title.lower(), clip_name.lower()) > 0.90:
					video_url=result.find('a').get('href')
					self.Log('SEARCH - video url: %s', video_url)
					self.rating = result.find('.//*[@class="current-rating"]').text.strip('Currently ').strip('/5 Stars')
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
			html=HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
			search_results=html.xpath('//*[@class="video-gallery"]/li')
			if search_results:
				for result in search_results:
					video_title = result.find('a').find("img").get("alt")
					video_title = re.sub("[\:\?\|]", '', video_title)
					video_title = video_title.rstrip(' ')
					self.Log('SEARCH - video title: %s', video_title)
					if video_title.lower() == clip_name.lower():
						video_url=result.find('a').get('href')
						self.Log('SEARCH - video url: %s', video_url)
						self.rating = result.find('.//*[@class="current-rating"]').text.strip('Currently ').strip('/5 Stars')
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
				html=HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
				search_results=html.xpath('//*[@class="video-gallery"]/li')
				if search_results:
					for result in search_results:
						video_title=result.find('a').find("img").get("alt")
						video_title = re.sub("[\:\?\|]", '', video_title)
						video_title = video_title.rstrip(' ')
						self.Log('SEARCH - video title: %s', video_title)
						if video_title.lower() == clip_name.lower():
							video_url=result.find('a').get('href')
							self.Log('SEARCH - video url: %s', video_url)
							self.rating = result.find('.//*[@class="current-rating"]').text.strip('Currently ').strip('/5 Stars')
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
		url = BASE_URL % metadata.id

		# Fetch HTML
		html = HTML.ElementFromURL(url, sleep=REQUEST_DELAY)

		# Set tagline to URL
		metadata.tagline = url
		valid_image_names = list()
		valid_art_names = list()
		if "HXM" in url:
			#movie logic

			#movie title
			metadata.title = html.xpath('//*[@id="rightcolumn"]/div/div/h3/text()')[0]

			#Movie poster
			mov_cover_lores = html.xpath('//div[@id="rightcolumn"]/a/img')[0].get("src")
			mov_cover_hires = mov_cover_lores.replace("320w","1920w")
			valid_image_names.append(mov_cover_hires)
			metadata.posters[mov_cover_hires]=Proxy.Media(HTTP.Request(mov_cover_hires), sort_order = 1)

			#Background art
			mov_id = str(filter(str.isdigit, url))
			art_url = "https://cdn.helixstudios.com/media/titles/hxm" + mov_id + "_trailer.jpg";
			valid_art_names.append(art_url)
			metadata.art[art_url] = Proxy.Media(HTTP.Request(art_url), sort_order=1)
			metadata.art.validate_keys(valid_art_names)

			#Description
			metadata.summary = html.xpath("//p[@class='description']/text()")[0]

			#Release date
			raw_date = html.xpath('//*[@id="rightcolumn"]/div/div/div[1]/text()')[0]
			metadata.originally_available_at = Datetime.ParseDate(raw_date).date()
			metadata.year = metadata.originally_available_at.year

			#Cast images
			metadata.roles.clear()
			rolethumbs = list();
			headshot_list = html.xpath('//ul[@id="scene-models"]/li/a/img')
			for headshot_obj in headshot_list:
				headshot_url_lo_res = headshot_obj.get("src")
				headshot_url_hi_res = headshot_url_lo_res.replace("150w","480w")

				result = requests.post('https://neural.vigue.me/facebox/check', json={"url": headshot_url_hi_res}, verify=certifi.where())
				Log(result.json()["facesCount"])
				if result.json()["facesCount"] == 1:
					box = result.json()["faces"][0]["rect"]
					cropped_headshot = "https://cdn.vigue.me/unsafe/" + str(self.noNegative(box["left"] - 100)) + "x" + str(self.noNegative(box["top"] - 100)) + ":" + str(self.noNegative((box["left"]+box["width"])+100)) + "x" + str(self.noNegative((box["top"]+box["height"])+100)) + "/" + headshot_url_hi_res
				else:
					cropped_headshot = headshot_url_hi_res

				rolethumbs.append(cropped_headshot)
			index = 0

			#Cast names
			cast_text_list = html.xpath('//ul[@id="scene-models"]/li/a/div/text()')
			for cast in cast_text_list:
				cname = cast.strip()
				if (len(cname) > 0):
					role = metadata.roles.new()
					role.name = cname
					role.photo = rolethumbs[index]
				index += 1

			metadata.posters.validate_keys(valid_image_names)
			metadata.art.validate_keys(valid_art_names)
			metadata.collections.add("Helix Studios")
			metadata.content_rating = 'X'
			metadata.studio = "Helix Studios"
			return

		video_title = html.xpath('//div[@class="scene-title"]/span/text()')[0]
		self.Log('UPDATE - video_title: "%s"', video_title)
		metadata.title = video_title

		# External 	https://cdn.helixstudios.com/img/300h/media/stills/hx109_scene52_001.jpg
		# Member 	https://cdn.helixstudios.com/img/1920w/media/stills/hx109_scene52_001.jpg
		i = 0
		video_image_list = html.xpath('//*[@id="scene-just-gallery"]/a/img')
		# self.Log('UPDATE - video_image_list: "%s"', video_image_list)
		try:
			coverPrefs = Prefs['cover']
			for image in video_image_list:
				if i <= (self.intTest(coverPrefs)-1) or coverPrefs == "all available":
					i = i + 1
					thumb_url = image.get('src')
					poster_url = thumb_url.replace('300h', '1920w')
					valid_image_names.append(poster_url)
					if poster_url not in metadata.posters:
						try:
							metadata.posters[poster_url]=Proxy.Preview(HTTP.Request(thumb_url), sort_order = i)
						except Exception as e: 
							pass
		except Exception as e:
			self.Log('UPDATE - Error getting posters: %s', e)
			pass

		#Try to get scene background art
		try:
			bg_image = html.xpath('//*[@id="container"]/div[3]/img')[0].get("src")
			valid_art_names.append(bg_image)
			metadata.art[bg_image] = Proxy.Media(HTTP.Request(bg_image), sort_order=1)
			self.Log("UPDATE- Art: %s", bg_image)
		except Exception as e:
			self.Log('UPDATE - Error getting art: %s', e)
			pass

		# Try to get description text
		try:
			raw_about_text=html.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/table/tr/td/p')
			self.Log('UPDATE - About Text - RAW %s', raw_about_text)
			about_text=' '.join(str(x.text_content().strip()) for x in raw_about_text)
			metadata.summary=about_text
		except Exception as e:
			self.Log('UPDATE - Error getting description text: %s', e)
			pass

		# Try to get release date
		try:
			release_date=html.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/table/tr[1]/td[1]/text()')[1].strip()
			self.Log('UPDATE - Release Date - New: %s', release_date)
			metadata.originally_available_at = Datetime.ParseDate(release_date).date()
			metadata.year = metadata.originally_available_at.year
		except Exception as e:
			self.Log('UPDATE - Error getting release date: %s', e)
			pass

		# Try to get and process the video cast
		metadata.roles.clear()
		rolethumbs = list();
		cast_list = html.xpath('//*[@Class="scene-info"]/table/tr[1]/td/a')
		for cast_obj in cast_list:
				model_href = BASE_URL % cast_obj.get('href')
				model_page = HTML.ElementFromURL(model_href, sleep=REQUEST_DELAY)
				model_headshot_lo_res = model_page.xpath('//div[@id="modelHeadshot"]/img')[0].get('src')
				headshot_url_hi_res = model_headshot_lo_res.replace("320w","320w")

				#Ask facebox to query image for face bounding boxes
				Log(headshot_url_hi_res);
				result = requests.post('https://neural.vigue.me/facebox/check', json={"url": headshot_url_hi_res}, verify=certifi.where())
				Log(result.json()["facesCount"])
				if result.json()["facesCount"] == 1:
					box = result.json()["faces"][0]["rect"]
					cropped_headshot = "https://cdn.vigue.me/unsafe/" + str(abs(box["left"] - 50)) + "x" + str(abs(box["top"] - 50)) + ":" + str(abs((box["left"]+box["width"])+50)) + "x" + str(abs((box["top"]+box["height"])+50)) + "/" + headshot_url_hi_res
				else:
					cropped_headshot = headshot_url_hi_res	
				#Create new image url from Thumbor CDN with facial bounding box
				self.Log("UPDATE - Cropped headshot: %s", cropped_headshot)
				rolethumbs.append(cropped_headshot)

		index = 0
		htmlcast = html.xpath('//*[@Class="scene-info"]/table/tr[1]/td/a/text()')
		for cast in htmlcast:
			cname = cast.strip()
			if (len(cname) > 0):
				role = metadata.roles.new()
				role.name = cname
				role.photo = rolethumbs[index]
			index += 1

		# Try to get and process the video genres
		try:
			metadata.genres.clear()
			genres = html.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/table/tr[4]/td/a/text()')
			self.Log('UPDATE - video_genres: "%s"', genres)
			for genre in genres:
				genre = genre.strip()
				if (len(genre) > 0):
					metadata.genres.add(genre)
		except Exception as e:
			self.Log('UPDATE - Error getting video genres: %s', e)
			pass

		metadata.posters.validate_keys(valid_image_names)
		metadata.art.validate_keys(valid_art_names)
		metadata.rating = float(self.rating)*2
		metadata.collections.add("Helix Studios")
		metadata.content_rating = 'X'
		metadata.title = video_title
		metadata.studio = "Helix Studios"
