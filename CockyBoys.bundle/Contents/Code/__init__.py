# CockyBoys
import re, os, platform, urllib
from difflib import SequenceMatcher

#Fix HTTPS errors when connecting to Facebox (neural.vigue.me) and Thumbor CDN (cdn.vigue.me)
import certifi
import requests

PLUGIN_LOG_TITLE = 'CockyBoys'	# Log Title

VERSION_NO = '2020.01.21.01'

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL = 'https://cockyboys.com%s'
BASE_VIDEO_DETAILS_URL = 'https://cockyboys.com/scenes/%s?type=vids'
BASE_SEARCH_URL = 'https://cockyboys.com/search.php?query=%s'

# File names to match for this agent
file_name_pattern = re.compile(Prefs['regex'])

def Start():
	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
        'Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
        '.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

class CockyBoys(Agent.Movies):
	name = 'CockyBoys'
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
		movie_url_name = urllib.quote_plus(movie_url_name);
		movie_url_name = movie_url_name.replace("%2B","+");
		movie_url = BASE_SEARCH_URL % movie_url_name
		self.Log('SEARCH - Video URL: %s', movie_url)
		html = HTML.ElementFromURL(movie_url, sleep=REQUEST_DELAY)

		search_results = html.xpath('//div[@class="sceneList newReleases responsive"]/div[@class="previewThumb "]')
		score=10
		# Enumerate the search results looking for an exact match. The hope is that by eliminating special character words from the title and searching the remainder that we will get the expected video in the results.
		if search_results:
			for result in search_results:
				video_title = result.xpath(".//em/a/strong/text()")[0]
				self.Log('SEARCH - video title percentage: %s', self.similar(video_title.lower(), clip_name.lower()))
				self.Log('SEARCH - video title: %s', video_title)
				# Check the alt tag which includes the full title with special characters against the video title. If we match we nominate the result as the proper metadata. If we don't match we reply with a low score.
				#if video_title.lower() == clip_name.lower():
				if self.similar(video_title.lower(), clip_name.lower()) > 0.50:
					video_url=result.find('em').find('a').get('href')
					poster_url=result.find('video').find('img').get('src')
					self.Log('SEARCH - video url: %s', video_url)
					self.Log('SEARCH - Exact Match "' + clip_name.lower() + '" == "%s"', video_title.lower())
					results.Append(MetadataSearchResult(id = video_url + ":::" + poster_url, name = video_title, score = 100, lang = lang))
					return
				else:
					self.Log('SEARCH - Title not found "' + clip_name.lower() + '" != "%s"', video_title.lower())
					score=score-1
					results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))
		else:
			score=1
			self.Log('SEARCH - Title not found "' + clip_name.lower())
			return

	def update(self, metadata, media, lang, force=False):
		self.Log('UPDATE CALLED')

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.Log('UPDATE - File Path: %s', file_path)
		self.Log('UPDATE - Video URLs: %s', metadata.id)
		url = metadata.id.split(":::")[0]

		# Fetch HTML
		html = HTML.ElementFromURL(url, sleep=REQUEST_DELAY)

		# Set tagline to URL
		metadata.tagline = url
		valid_image_names = list()
		valid_art_names = list()

		video_title = html.xpath('//h1[@class="gothamy sectionTitle"]/text()')[0]
		self.Log('UPDATE - video_title: "%s"', video_title)
		metadata.title = video_title

		img_html = HTML.ElementFromURL(url.replace("vids","highres"), sleep=REQUEST_DELAY);
		i = 0
		video_image_list = img_html.xpath('//div[@class="photo_gallery_block"]/a/img')
		# self.Log('UPDATE - video_image_list: "%s"', video_image_list)
		try:
			coverPrefs = Prefs['cover']
			for image in video_image_list:
				if i <= (self.intTest(coverPrefs)-1) or coverPrefs == "all available":
					i = i + 1
					thumb_url = image.get('src')
					poster_url = thumb_url.replace('thumbs', '1024watermarked')
					valid_image_names.append(poster_url)
					if poster_url not in metadata.posters:
						try:
							metadata.posters[poster_url]=Proxy.Preview(HTTP.Request(thumb_url), sort_order = i)
						except: pass
		except Exception as e:
			self.Log('UPDATE - Error getting posters: %s', e)
			pass

		#Try to get scene background art
		try:
			bg_image = metadata.id.split(":::")[1]
			valid_art_names.append(bg_image)
			metadata.art[bg_image] = Proxy.Media(HTTP.Request(bg_image), sort_order=1)
			self.Log("UPDATE- Art: %s", bg_image)
		except Exception as e:
			self.Log('UPDATE - Error getting art: %s', e)
			pass

		# Try to get description text
		try:
			raw_about_text=html.xpath('//div[@class="movieDesc"]')
			self.Log('UPDATE - About Text - RAW %s', raw_about_text)
			about_text=' '.join(str(x.text_content().replace("Description","").strip()) for x in raw_about_text)
			metadata.summary=about_text
		except Exception as e:
			self.Log('UPDATE - Error getting description text: %s', e)
			pass

		# Try to get release date
		try:
			release_date=html.xpath('//div[@id="info"]/p/span[1]/text()')[0]
			self.Log('UPDATE - Release Date - New: %s', release_date)
			metadata.originally_available_at = Datetime.ParseDate(release_date).date()
			metadata.year = metadata.originally_available_at.year
		except Exception as e:
			self.Log('UPDATE - Error getting release date: %s', e)
			pass

		# Try to get and process the video cast
		try:
			metadata.roles.clear()
			rolethumbs = list();
			cast_list = html.xpath('//div[@class="movieModels"]/span/a[@class="fade"]/img')
			for cast_obj in cast_list:
					headshot_url_hi_res = cast_obj.get('src')

					#Ask facebox to query image for face bounding boxes
					Log(headshot_url_hi_res);
					result = requests.post('https://neural.vigue.me/facebox/check', json={"url": headshot_url_hi_res}, verify=certifi.where())
					box = result.json()["faces"][0]["rect"]

					#Create new image url from Thumbor CDN with facial bounding box
					cropped_headshot = "https://cdn.vigue.me/unsafe/" + str(abs(box["left"] - 50)) + "x" + str(abs(box["top"] - 50)) + ":" + str(abs((box["left"]+box["width"])+50)) + "x" + str(abs((box["top"]+box["height"])+50)) + "/" + headshot_url_hi_res
					self.Log("UPDATE - Cropped headshot: %s", cropped_headshot)
					rolethumbs.append(cropped_headshot)

			index = 0
			htmlcast = html.xpath('//div[@id="info"]/p/span[3]/a/text()')
			for cast in htmlcast:
				cname = cast.strip()
				if (len(cname) > 0):
					role = metadata.roles.new()
					role.name = cname
					role.photo = rolethumbs[index]
				index += 1
		except Exception as e:
			self.Log("UPDATE - Error setting cast: %s", e)
			pass

		# Try to get and process the video genres
		try:
			metadata.genres.clear()
			genres = html.xpath('//div[@id="info"]/p/span[2]/a/text()')
			self.Log('UPDATE - video_genres: "%s"', genres)
			for genre in genres:
				genre = genre.strip()
				if genre == "BareBack": genre = "Bareback"
				if genre == "Condomless": genre = ""
				if genre == "Flip-Fucking": genre = "Flip-Fuck"
				if genre == "Oral & Deep Throating": genre = "Oral Sex"
				if (len(genre) > 0):
					metadata.genres.add(genre)
		except Exception as e:
			self.Log('UPDATE - Error getting video genres: %s', e)
			pass

		metadata.rating = float(html.xpath('//div[@class="underPlayer"]/div/p[@class="gothamy"]/text()')[0])
		metadata.posters.validate_keys(valid_image_names)
		metadata.art.validate_keys(valid_art_names)
		metadata.collections.add("CockyBoys")
		metadata.content_rating = 'X'
		metadata.title = video_title
		metadata.studio = "CockyBoys"
