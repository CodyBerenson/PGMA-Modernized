# Gay Porn Collector
import cookielib, cgi, re, os, platform, json, urllib

PLUGIN_LOG_TITLE='Gay Porn Collector'	# Log Title

VERSION_NO = '2017.07.26.0'

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL='http://www.gayporncollector.com'
BASE_VIDEO_DETAILS_URL = BASE_URL + '%s'

# Example Search URL
# http://www.gayporncollector.com/wp-json/milkshake/v2/pornmovies/?movie_title=%23helix:%20Twink%20Confessions%202
BASE_SEARCH_URL_MOVIES = 'http://www.gayporncollector.com/wp-json/milkshake/v2/pornmovies/?movie_title='

# http://www.gayporncollector.com/wp-json/milkshake/v2/pornscenes/?scene_title=Wet%20&%20Wild%20With%20Blake%20Mitchell
BASE_SEARCH_URL_SCENES = 'http://www.gayporncollector.com/wp-json/milkshake/v2/pornscenes/'

# http://www.gayporncollector.com/wp-json/milkshake/v2/pornscenes/3620
BASE_SEARCH_URL_STARS = 'http://www.gayporncollector.com/wp-json/milkshake/v2/pornstars/'

# File names to match for this agent
file_name_pattern = re.compile(Prefs['regex'])

#replace # with %27 and ' with %23
def Start():
	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
        'Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
        '.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

class GayPornCollector(Agent.Movies):
	name = 'Gay Porn Collector'
	languages = [Locale.Language.NoLanguage, Locale.Language.English]
	fallback_agent = False
	primary_provider = False
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

		scene_url_name = groups['clip_name']
		scene_url = BASE_SEARCH_URL_SCENES + '?scene_title=' +  urllib.quote(scene_url_name)

		self.Log('SEARCH - Scene URL: %s', scene_url)

		file_studio = final_dir #used in if statment for studio name
		self.Log('SEARCH - final_dir: %s', final_dir)
		self.Log('SEARCH - This is a scene: True')
		file_name = basename.lower() #Sets string to lower.
		file_name = re.sub('\(([^\)]+)\)', '', file_name) #Removes anything inside of () and the () themselves.
		file_name = file_name.lstrip(' ') #Removes white spaces on the left end.
		file_name = file_name.lstrip('- ') #Removes white spaces on the left end.
		file_name = file_name.rstrip(' ') #Removes white spaces on the right end.

		response = urllib.urlopen(scene_url)
		search_results = json.loads(response.read())
		score=10

		if 'message' in search_results:
			self.Log('SEARCH - Skipping %s because the results are empty.', basename)
			return

		self.Log('SEARCH - results size exact match: %s', len(search_results))
		for result in search_results:
			try:
				studio = result['related_porn_studio'][0]['porn_studio_name']
				self.Log('SEARCH - studio: %s', studio)
			except:
				studio = 'empty'
				self.Log('SEARCH - studios: Empty')
			pass
			video_title = result['title']
			video_title = video_title.lstrip(' ') #Removes white spaces on the left end.
			video_title = video_title.rstrip(' ') #Removes white spaces on the right end.
			video_title = video_title.replace(':', '')
			if studio.lower() == file_studio.lower() and video_title.lower() == file_name.lower():
				self.Log('SEARCH - video title: %s', video_title)
				self.Log('SEARCH - video url: %s', result['link'])
				self.Log('SEARCH - Exact Match "' + file_name.lower() + '" == "%s"', video_title.lower())
				self.Log('SEARCH - Studio Match "' + studio.lower() + '" == "%s"', file_studio.lower())
				results.Append(MetadataSearchResult(id = str(result['ID']), name = video_title, score = 100, lang = lang))
				return

	def update(self, metadata, media, lang, force=False):
		self.Log('UPDATE CALLED')
		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.Log('UPDATE - File Path: %s', file_path)
		self.Log('UPDATE - Video URL: %s', metadata.id)
		url = BASE_SEARCH_URL_SCENES + metadata.id
		# Fetch HTML.
		response = urllib.urlopen(url)
		results = json.loads(response.read())

		# Set tagline to URL.
		metadata.tagline = results['link']
		# Set video title.
		video_title = results['title']
		self.Log('UPDATE - video_title: "%s"', video_title)

		metadata.title = video_title

		metadata.content_rating = 'X'

		# Try to get and process the director posters.
		valid_image_poster_names = list()
		try:
			self.Log('UPDATE - video_image_list: "%s"', results['poster'])
			poster_url = results['poster']['guid']
			valid_image_poster_names.append(poster_url)
			if poster_url not in metadata.posters:
				metadata.posters[poster_url]=Proxy.Preview(HTTP.Request(poster_url))
		except Exception as e:
			self.Log('UPDATE - Error getting posters: %s', e)
			pass

		# Try to get and process the background art.
		valid_image_background_names = list()
		try:
			i = 0
			video_image_list = results['gallery']
			self.Log('UPDATE - video_image_list: "%s"', video_image_list)
			coverPrefs = Prefs['cover']
			for image in video_image_list:
				if i <= (self.intTest(coverPrefs)-1) or coverPrefs == "all available":
					i = i + 1
					art_url = image['guid']
					valid_image_background_names.append(art_url)
					if art_url not in metadata.art:
						try:
							metadata.art[art_url]=Proxy.Preview(HTTP.Request(art_url), sort_order = i)
						except: pass
		except Exception as e:
			self.Log('UPDATE - Error getting posters: %s', e)
			pass

		# Try to get description text.
		try:
			about_text=results['scene_description']
			self.Log('UPDATE - About Text %s', about_text)
			metadata.summary=about_text
		except Exception as e:
			self.Log('UPDATE - Error getting description text: %s', e)
			pass

		# Try to get and process the release date.
		try:
			rd=results['release_date']
			self.Log('UPDATE - Release Date: %s', rd)
			metadata.originally_available_at = Datetime.ParseDate(rd).date()
			metadata.year = metadata.originally_available_at.year
		except Exception as e:
			self.Log('UPDATE - Error getting release date: %s', e)
			pass

		# Try to get and process the video genres.
		try:
			metadata.genres.clear()
			genres = results['porn_scene_genres']
			self.Log('UPDATE - video_genres count from scene: "%s"', len(genres))
			self.Log('UPDATE - video_genres from scene: "%s"', genres)
			for genre in genres:
				metadata.genres.add(genre['name'])
		except Exception as e:
			self.Log('UPDATE - Error getting video genres: %s', e)
			pass

		# Crew.
		# Try to get and process the director.
		try:
			metadata.directors.clear()
			director = metadata.directors.new()
			director.name = results['scene_director']
			self.Log('UPDATE - director: "%s"', director)
		except Exception as e:
			self.Log('UPDATE - Error getting director: %s', e)
			pass

		# Try to get and process the video cast.
		try:
			metadata.roles.clear()
			casts = results['related_porn_stars']
			self.Log('UPDATE - cast scene count: "%s"', len(casts))
			if len(casts) > 0:
				roleCount = {}
				for cast in casts:
					cname = cast['porn_star_name']
					self.Log('UPDATE - cast: "%s"', cname)
					role = metadata.roles.new()
					role.name = cname
					try:
						c_id = cast['porn_star_id']
						self.Log('UPDATE - cast id: "%s"', c_id)
						url = BASE_SEARCH_URL_STARS + c_id
						# Fetch HTML.
						response = urllib.urlopen(url)
						star = json.loads(response.read())
						role.photo = star['poster']['guid']
						roleCount[star['role']] = 1 + roleCount.get(star['role'],0)
						if roleCount[star['role']] != 1:
							role.role = star['role'] + " " + str(roleCount[star['role']])
						else:
							role.role = star['role']
					except Exception as e:
						self.Log('UPDATE - Error getting cast: %s', e)
						pass

		except Exception as e:
			self.Log('UPDATE - Error getting cast: %s', e)
			pass

		# Try to get and process the studio name.
		try:
			studio = results['related_porn_studio'][0]['porn_studio_name']
			self.Log('UPDATE - studio: "%s"', studio)
			metadata.studio=studio
		except Exception as e:
			self.Log('UPDATE - Error getting studio name: %s', e)
			pass

		# Try to get and process the country.
		try:
			metadata.countries.clear()
			country_name = results['related_porn_studio'][0]['porn_studio_country']
			metadata.countries.add(country_name)
			self.Log('UPDATE - country: "%s"', country_name)
		except Exception as e:
			self.Log('UPDATE - Error getting country name: %s', e)
			pass
		# Try to get and process the country.
		try:
			metadata.collections.clear()
			movie_names = results['related_porn_movie']
			if movie_names is not None:
				self.Log('UPDATE - collections count: "%s"', len(movie_names))
				if len(movie_names) > 0:
					for movie in movie_names:
						movie_name = movie['porn_movie_title']
						self.Log('UPDATE - collection: "%s"', movie_name)
						collection = metadata.collections.add(movie_name)
		except Exception as e:
			self.Log('UPDATE - Error getting collections name: %s', e)
			pass
		metadata.art.validate_keys(valid_image_background_names)
		metadata.posters.validate_keys(valid_image_poster_names)
