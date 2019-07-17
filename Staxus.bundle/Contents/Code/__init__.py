# Staxus
import re, os, platform, urllib, cgi
from difflib import SequenceMatcher
#Fix HTTPS errors when connecting to Facebox (neural.vigue.me) and Thumbor CDN (cdn.vigue.me)
import certifi
import requests

PLUGIN_LOG_TITLE='Staxus'	# Log Title

VERSION_NO = '2017.07.11.3'

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL='http://staxus.com%s'

# Example Video Details URL
# http://staxus.com/trial/gallery.php?id=4044
BASE_VIDEO_DETAILS_URL='http://staxus.com/trial/%s'

# Example Search URL:
# http://staxus.com/trial/search.php?query=Staxus+Classic%3A+BB+Skate+Rave+-+Scene+1+-+Remastered+in+HD
BASE_SEARCH_URL='http://staxus.com/trial/search.php?st=advanced&qall=%s'

# File names to match for this agent
file_name_pattern = re.compile(Prefs['regex'])

def Start():
	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
        'Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
        '.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

class Staxus(Agent.Movies):
	name = 'Staxus'
	languages = [Locale.Language.NoLanguage, Locale.Language.English]
	primary_provider = False
	fallback_agent = ['com.plexapp.agents.gayporncollector']
	contributes_to = ['com.plexapp.agents.cockporn']

	def Log(self, message, *args):
		if Prefs['debug']:
			Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

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

		enclosing_directory, file_name = os.path.split(os.path.splitext(path_and_file)[0])
		enclosing_directory, enclosing_folder = os.path.split(enclosing_directory)

		self.Log('SEARCH - Enclosing Folder: %s', enclosing_folder)

		if Prefs['folders'] != "*":
			folder_list = re.split(',\s*', Prefs['folders'].lower())
			if enclosing_folder not in folder_list:
				self.Log('SEARCH - Skipping %s because the folder %s is not in the acceptable folders list: %s', basename, final_dir, ','.join(folder_list))
				return

		self.Log('SEARCH - File Name: %s', file_name)
		self.Log('SEARCH - Split File Name: %s', file_name.split(' '))

		remove_words = file_name.lower() #Sets string to lower.
		remove_words = remove_words.replace('staxus', '') #Removes word.
		remove_words = re.sub('\(([^\)]+)\)', '', remove_words) #Removes anything inside of () and the () themselves.
		remove_words = remove_words.lstrip(' ') #Removes white spaces on the left end.
		remove_words = remove_words.rstrip(' ') #Removes white spaces on the right end.
		search_query_raw = list()

		if remove_words.isdigit():
                        #add direct video match & skip search
			video_url = "gallery.php?id=" + remove_words
			self.Log('SEARCH - DIRECT SCENE MATCH: %s', video_url);
			self.rating = 5
			html = HTML.ElementFromURL("https://staxus.com/trial/" + video_url, sleep=REQUEST_DELAY)
			video_title = html.xpath('//div[@class="video-descr__title"]/div[@class="row-flex"]/div[@class="col-md-7 col-xs-12"]/h2/text()')[0]
			results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
			return

		# Process the split filename to remove words with special characters. This is to attempt to find a match with the limited search function(doesn't process any non-alphanumeric characters correctly)
		for piece in remove_words.split(' '):
			search_query_raw.append(cgi.escape(piece))
		search_query="%2C+".join(search_query_raw)
		self.Log('SEARCH - Search Query: %s', search_query)
		html=HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
		search_results=html.xpath('//*[@class="item"]')
		score=10
		self.Log('SEARCH - results size: %s', len(search_results))
		# Enumerate the search results looking for an exact match. The hope is that by eliminating special character words from the title and searching the remainder that we will get the expected video in the results.
		for result in search_results:
			#result=result.find('')
			video_title=result.findall("div/a/img")[0].get("alt")
			video_title = video_title.lstrip(' ') #Removes white spaces on the left end.
			video_title = video_title.rstrip(' ') #Removes white spaces on the right end.
			self.Log('SEARCH - video title: %s', video_title)
			# Check the alt tag which includes the full title with special characters against the video title. If we match we nominate the result as the proper metadata. If we don't match we reply with a low score.
			if self.similar(video_title.lower().replace(':',''),file_name.lower()) > 0.7:
				video_url=result.findall("div/a")[0].get('href')
				self.Log('SEARCH - video url: %s', video_url)
				image_url=result.findall("div/a/img")[0].get("src")
				self.Log('SEARCH - image url: %s', image_url)
				self.Log('SEARCH - Exact Match "' + file_name.lower() + '" == "%s"' % video_title.lower())
				results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
			else:
				self.Log('SEARCH - Title not found "' + file_name.lower() + '" != "%s"' % video_title.lower())
				score=score-1
				results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))

	def update(self, metadata, media, lang, force=False):
		self.Log('UPDATE CALLED')

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.Log('UPDATE - File Path: %s', file_path)
		self.Log('UPDATE - Video URL: %s', metadata.id)
		url = BASE_VIDEO_DETAILS_URL % metadata.id

		# Fetch HTML
		html = HTML.ElementFromURL(url, sleep=REQUEST_DELAY)

		# Set tagline to URL
		metadata.tagline = url

		video_title = html.xpath('//div[@class="video-descr__title"]/div[@class="row-flex"]/div[@class="col-md-7 col-xs-12"]/h2/text()')[0]
		video_title = video_title.replace(", Sc.",": Scene ")
		self.Log('UPDATE - video_title: "%s"' % video_title)

		valid_image_names = list()
		i = 0
		video_image_list = html.xpath('//div[@class="video-descr__gallery"]/div/div/a')
		try:
			coverPrefs = Prefs['cover']
			for image in video_image_list:
				if i != coverPrefs or coverPrefs == "all available":
					css = image.get('style')
					thumb_url = css.split("'")[1]
					thumb_url = thumb_url.replace("//","https://")
					#self.Log('UPDATE - thumb_url: "%s"' % thumb_url)
					poster_url = thumb_url.replace('300h', '1920w')
					#self.Log('UPDATE - poster_url: "%s"' % poster_url)
					valid_image_names.append(poster_url)
					if poster_url not in metadata.posters:
						try:
							i += 1
							metadata.posters[poster_url]=Proxy.Preview(HTTP.Request(thumb_url), sort_order = i)
						except: pass
		except Exception as e:
			self.Log('UPDATE - Error getting posters: %s', e)
			pass

		valid_art_names = list()
		try:
			bg_image = html.xpath('//div[@class="player-wrapper aspect-ratio"]')
			bg_image = bg_image[0].get("style")
			bg_image = bg_image.split("'")[1];
			bg_image = bg_image.replace("//","https://")
			valid_art_names.append(bg_image)
			self.Log('UPDATE - Art: %s', bg_image)
			metadata.art[bg_image] = Proxy.Media(HTTP.Request(bg_image), sort_order=1)
			metadata.art.validate_keys(valid_art_names)
		except Exception as e:
			self.Log('UPDATE - Error getting art: %s', e)
			pass

		# Try to get description text.
		try:
			about_text=html.xpath('//div[@class="video-descr__content"]/p/text()')[0]
			self.Log('UPDATE - About Text - %s', about_text)
			metadata.summary=about_text
		except Exception as e:
			self.Log('UPDATE - Error getting description text: %s', e)
			pass

		# Try to get release date.
		try:
			rd=html.xpath('//div[@class="video-details-wrap"]/div[1]/text()')[1]
			rd = rd.split('/')
			rd = [rd[i] for i in [1,0,2]]
			rd[1] = rd[1] + ', '
			rd[0] = rd[0] + " "
			rd=''.join(rd)
			self.Log('UPDATE - Release Date: %s', rd)
			metadata.originally_available_at = Datetime.ParseDate(rd).date()
			metadata.year = metadata.originally_available_at.year
		except Exception as e:
			self.Log('UPDATE - Error getting release date: %s', e)
			pass

		# Try to get and process the video cast.
		try:
			metadata.roles.clear()
			rolethumbs = list();
			cast_img_list = html.xpath('//div[@class="video-descr__model-item"]/div')
			for image in cast_img_list:
				css = image.get('style')
				thumb_url = css.split("'")[1]
				thumb_url = thumb_url.replace("//","https://")

				#Ask facebox to query image for face bounding boxes
				result = requests.post('https://neural.vigue.me/facebox/check', json={"url": thumb_url}, verify=certifi.where())
				box = result.json()["faces"][0]["rect"]

				#Create new image url from Thumbor CDN with facial bounding box
				cropped_headshot = "https://cdn.vigue.me/unsafe/" + str(abs(box["left"] - 50)) + "x" + str(abs(box["top"] - 50)) + ":" + str(abs((box["left"]+box["width"])+50)) + "x" + str(abs((box["top"]+box["height"])+50)) + "/" + thumb_url
				self.Log("UPDATE - Cast image: %s" ,cropped_headshot)
				rolethumbs.append(cropped_headshot)

			metadata.roles.clear()
			htmlcast = html.xpath('//div[@class="video-descr__model-item"]/p/a/text()')
			self.Log('UPDATE - cast: "%s"' % htmlcast)
			index = 0
			for cast in htmlcast:
				cname = cast.strip()
				if (len(cname) > 0):
					role = metadata.roles.new()
					role.name = cname
					role.photo = rolethumbs[index]
				index += 1
		except Exception as e:
			self.Log('UPDATE - Error getting video cast: %s', e)
			pass

		# Try to get and process the video genres.
		try:
			metadata.genres.clear()
			genres = html.xpath("//div[@class='video-descr__section']/p/a/text()")
			self.Log('UPDATE - video_genres: "%s"' % genres)
			for genre in genres:
				genre = genre.strip()
				if (len(genre) > 0):
					genre = genre.replace("arse","ass")
					genre = genre.replace(" (18+)","")
					metadata.genres.add(genre)
		except Exception as e:
			self.Log('UPDATE - Error getting video genres: %s', e)
			pass

		# Try to get and process the ratings.
		try:
			rating = html.xpath('//span[@class="video-grade-average"]/strong/text()')[0].strip()
			self.Log('UPDATE - video_rating: "%s"', rating)
			metadata.rating = float(rating)*2
		except Exception as e:
			self.Log('UPDATE - Error getting rating: %s', e)
			pass

		metadata.posters.validate_keys(valid_image_names)
		metadata.collections.add("Staxus")
		metadata.content_rating = 'X'
		metadata.title = video_title
		metadata.studio = "Staxus"
