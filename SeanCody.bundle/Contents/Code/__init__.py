# SeanCody
import re, os, platform, simplejson as json

PLUGIN_LOG_TITLE = 'Sean Cody'    # Log Title

VERSION_NO = '2017.07.26.0'

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL = 'https://www.seancody.com%s'

# Example Tour URL
# http://www.seancody.com/tour/movie/9291/brodie-cole-bareback/trailer/
BASE_TOUR_MOVIE_URL = 'http://www.seancody.com/tour/movie/%s/%s/trailer'

# File names to match for this agent
movie_pattern = re.compile(Prefs['regex'])

def Start():
	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
		'Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
		'.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

class SeanCody(Agent.Movies):
	name = 'Sean Cody'
	languages = [Locale.Language.NoLanguage, Locale.Language.English]
	primary_provider = False
	fallback_agent = ['com.plexapp.agents.gayporncollector']
	contributes_to = ['com.plexapp.agents.cockporn']

	def Log(self, message, *args):
		if Prefs['debug']:
			Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

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

		m = movie_pattern.search(basename)
		if not m:
			self.Log('SEARCH - Skipping %s because the file name is not in the expected format.', basename)
			return

		self.Log('SEARCH - File Name: %s' % basename)
		self.Log('SEARCH - Split File Name: %s' % basename.split(' '))

		groups = m.groupdict()
		movie_url_name = re.sub('[^a-z0-9\-]', '', re.sub(' +', '-', groups['clip_name']))
		movie_url = BASE_TOUR_MOVIE_URL + groups['clip_number'] + movie_url_name

		self.Log('SEARCH - Video URL: %s' % movie_url)
		try:
			html = HTML.ElementFromURL(movie_url, sleep=REQUEST_DELAY)
		except:
			self.Log("SEARCH - Title not found: %s" % movie_url)
			return

		movie_name = html.xpath('//*[@id="player-wrapper"]/div/h1/text()')[0]
		self.Log('SEARCH - title: %s' % movie_name)
		results.Append(MetadataSearchResult(id=movie_url, name=movie_name, score=100, lang=lang))
		return

	def fetch_summary(self, html, metadata):
		raw_about_text = html.xpath('//*[@id="description"]/p')
		self.Log('UPDATE - About Text - RAW %s', raw_about_text)
		about_text = ' '.join(str(x.text_content().strip()) for x in raw_about_text)
		metadata.summary = about_text

	def fetch_release_date(self, html, metadata):
		release_date = html.xpath('//*[@id="player-wrapper"]/div/span/time/text()')[0].strip()
		self.Log('UPDATE - Release Date - New: %s' % release_date)
		metadata.originally_available_at = Datetime.ParseDate(release_date).date()
		metadata.year = metadata.originally_available_at.year

	def fetch_roles(self, html, metadata):
		metadata.roles.clear()
		htmlcast = html.xpath('//*[@id="scroll"]/div[2]/ul[2]/li/a/span/text()')
		self.Log('UPDATE - cast: "%s"' % htmlcast)
		for cast in htmlcast:
			cname = cast.strip()
			if (len(cname) > 0):
				role = metadata.roles.new()
				role.name = cname

	def fetch_genre(self, html, metadata):
		metadata.genres.clear()
		genres = html.xpath('//*[@id="scroll"]/div[2]/ul[1]/li/a/text()')
		self.Log('UPDATE - video_genres: "%s"' % genres)
		for genre in genres:
			genre = genre.strip()
			if (len(genre) > 0):
				metadata.genres.add(genre)

	def fetch_gallery(self, html, metadata):
		i = 0

		# convert the gallery source variable to parseable JSON and then
		# grab the useful bits out of it
		gallery_info = json.loads(html.xpath('/html/body/div[1]/div/div/section[2]/div/script/text()')[0].
			replace('\n', '').
			replace('var gallerySource = ', '').
			replace('};', '}'))

		try:
			coverPrefs = int(Prefs['cover'])
		except ValueError:
			# an absurdly high number means "download all the things"
			coverPrefs = 10000

		thumb_path = gallery_info['thumb']['path']
		thumb_hash = gallery_info['thumb']['hash']
		poster_path = gallery_info['fullsize']['path']
		poster_hash = gallery_info['fullsize']['hash']
		gallery_length = int(gallery_info['length'])
		valid_image_names = []

		for i in xrange(1, gallery_length + 1):
			if i > coverPrefs:
				break

			thumb_url = "%s%02d.jpg%s" % (thumb_path, i, thumb_hash)
			poster_url = "%s%02d.jpg%s" % (poster_path, i, poster_hash)

			valid_image_names.append(poster_url)
			if poster_url not in metadata.posters:
				try:
					i += 1
					metadata.posters[poster_url] = Proxy.Preview(HTTP.Request(thumb_url), sort_order=i)
				except:
					pass

		return valid_image_names

	def update(self, metadata, media, lang, force=False):
		self.Log('UPDATE CALLED')

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.Log('UPDATE - File Path: %s', file_path)
		self.Log('UPDATE - Video URL: %s', metadata.id)

		# Fetch HTML
		html = HTML.ElementFromURL(metadata.id, sleep=REQUEST_DELAY)

		# Set tagline to URL
		metadata.tagline = metadata.id

		# The Title
		video_title = html.xpath('//*[@id="player-wrapper"]/div/h1/text()')[0]

		# Try to get description text
		try:
			self.fetch_summary(html, metadata)
		except:
			pass

		# Try to get release date
		try:
			self.fetch_release_date(html, metadata)
		except:
			pass

		# Try to get and process the video cast
		try:
			self.fetch_roles(html, metadata)
		except:
			pass

		# Try to get and process the video genres
		try:
			self.fetch_genres(html, metadata)
		except:
			pass

		valid_image_names = self.fetch_gallery(html, metadata)
		metadata.posters.validate_keys(valid_image_names)

		metadata.content_rating = 'X'
		metadata.title = video_title
		metadata.studio = "Sean Cody"
