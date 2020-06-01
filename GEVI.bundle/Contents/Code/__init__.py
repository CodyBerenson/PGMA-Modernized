# pylint: disable=line-too-long
# encoding=utf8
'''
# GEVI - (IAFD)
                                                  Version History
                                                  ---------------
    Date            Version                         Modification
    07 Apr 2020   2019.12.25.7     Changed the agent to search past the first page of results
    08 Apr 2020   2020.12.25.8     Created new function to prepare the video title to build the search query
    12 Apr 2020   2020.12.25.9     removed line in updating countries as it raised an error in the logs
                                   logical error replacing full stops in title when preparing search string
    26 Apr 2020   2020.12.25.10    corrected search string: can only be 24 characters long and be comprised of full words
                                   search and replace of special characters in search string was not working correctly
    28 Apr 2020   2020.12.25.11    Failed to scrap for some titles, found errors stopped execution, so code placed in try: exception
                                   added no spaces comparison to studio found results
                                   Added Scene breakdown scrape to summary
                                   Added Ratings scrape
    08 May 2020   2020.12.25.12    Enhanced the creation of the search string and the search url to return fewer but more exact results
                                   added portugues, spanish, german - articles for removal from search title
                                   added/merge matching string routines - filename, studio, release date
                                   removed references from summary relating to where scene can be found in compilation or other movie
    28 May 2020   2020.12.25.13    Took into account Brackets () in Title - characters replaced by Space
                                   GEVI will now compare file studio name against both site distributor and site studio names
-----------------------------------------------------------------------------------------------------------------------------------
'''

import datetime, linecache, platform, os, re, string, sys, urllib

# Version / Log Title
VERSION_NO = '2019.12.25.13'
PLUGIN_LOG_TITLE = 'GEVI'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
FILEPATTERN = Prefs['regex']

# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# URLS
BASE_URL = 'https://www.gayeroticvideoindex.com'
BASE_SEARCH_URL = BASE_URL + '/search.php?type=t&where=b&query={0}&Search=Search&page=1'

# Date Format used by website
DATEFORMAT = '%Y%m%d'

# ----------------------------------------------------------------------------------------------------------------------------------
def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'

# ----------------------------------------------------------------------------------------------------------------------------------
def ValidatePrefs():
    pass

# ----------------------------------------------------------------------------------------------------------------------------------
class GEVI(Agent.Movies):
    name = 'GEVI (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchFilename(self, filename):
        ''' return groups from filename regex match else return false '''
        pattern = re.compile(FILEPATTERN)
        matched = pattern.search(filename)
        if matched:
            groups = matched.groupdict()
            return groups['studio'], groups['title'], groups['year']
        else:
            raise Exception("File Name [{0}] not in the expected format: (Studio) - Title (Year)".format(filename))

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchStudioName(self, fileStudioName, siteStudioName):
        ''' match file studio name against website studio name: Boolean Return '''
        siteStudioName = self.NormaliseComparisonString(siteStudioName)

        # remove spaces in comparison variables and check for equality
        noSpaces_siteStudioName = siteStudioName.replace(' ', '')
        noSpaces_fileStudioName = fileStudioName.replace(' ', '')

        if siteStudioName == fileStudioName:
            self.log('SELF:: Studio: Full Word Match: Site: {0} = File: {1}'.format(siteStudioName, fileStudioName))
        elif noSpaces_siteStudioName == noSpaces_fileStudioName:
            self.log('SELF:: Studio: Full Word Match: Site: {0} = File: {1}'.format(siteStudioName, fileStudioName))
        elif siteStudioName in fileStudioName:
            self.log('SELF:: Studio: Part Word Match: Site: {0} IN File: {1}'.format(siteStudioName, fileStudioName))
        elif fileStudioName in siteStudioName:
            self.log('SELF:: Studio: Part Word Match: File: {0} IN Site: {1}'.format(fileStudioName, siteStudioName))
        else:
            raise Exception('Match Failure: Site: {0}'.format(siteStudioName))

        return True

    # -------------------------------------------------------------------------------------------------------------------------------
    def matchReleaseDate(self, fileDate, siteDate):
        ''' match file year against website release date: return formatted site date if no error or default to formated file date '''
        siteDate = siteDate + '1231' # a year has being provided - default to 31st December of that year
        siteDate = datetime.datetime.strptime(siteDate, DATEFORMAT)

        # there can not be a difference more than 366 days between FileName Date and SiteDate
        dx = abs((fileDate - siteDate).days)
        msg = 'Match{0}: File Date [{1}] - Site Date [{2}] = Dx [{3}] days'.format(' Failure' if dx > 366 else '', fileDate.strftime('%Y %m %d'), siteDate.strftime('%Y %m %d'), dx)
        if dx > 366:
            raise Exception('Release Date: {0}'.format(msg))
        else:
            self.log('SELF:: Release Date: {0}'.format(msg))

        return siteDate

    # -------------------------------------------------------------------------------------------------------------------------------
    def NormaliseComparisonString(self, myString):
        ''' Normalise string for Comparison, strip all non alphanumeric characters, Vol., Volume, Part, and 1 in series '''
        # convert to lower case and trim
        myString = myString.strip().lower()

        # remove vol/volume/part and vol.1 etc wording as filenames dont have these to maintain a uniform search across all websites and remove all non alphanumeric characters
        myString = myString.replace('&', 'and').replace(' vol.', '').replace(' volume', '').replace(' part', '').replace(',', '')

        # remove all standalone "1's"
        regex = re.compile(r'(?<!\d)1(?!\d)')
        myString = regex.sub('', myString)

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

    # -------------------------------------------------------------------------------------------------------------------------------
    def CleanSearchString(self, myString):
        ''' Prepare Video title for search query '''
        # convert to lower case and trim and strip diacritics - except ß which we replace with one s
        myString = myString.replace('ß', 's').replace("'s ", 's ')
        myString = String.StripDiacritics(myString)
        myString = myString.lower().strip()

        # these need to be replace with a space
        replaceChars = ['-', '–', '(', ')']
        regex = '[' + re.escape(''.join(replaceChars)) + ']'
        myString = re.sub(regex, ' ', myString)

        # these need to be replace with a null
        replaceChars = ['-', '–', "'", ',' '&', '!', '.', '#']
        regex = '[' + re.escape(''.join(replaceChars)) + ']'
        myString = re.sub(regex, '', myString)

        # removal of definitive/indefinitive articles in title as it messes GEVIs search algorithm - English, French and German
        # split myString at position of first separate digit e.g MY TITLE 7 - THE 7TH RETURN becomes MY TITLE 
        art_eng = ['a', 'an', 'the']
        art_fre = ['un', 'une', 'des', 'le', 'la', 'les', "l'"]
        art_prt = ['um', 'uma', 'uns', 'umas', 'o', 'a', 'os', 'as']
        art_esp = ['un', 'una', 'unos', 'unas', 'el', 'la', 'los', 'las']
        art_ger = ['ein', 'eine', 'eines', 'einen', 'einem', 'einer', 'das', 'die', 'der', 'dem', 'den', 'des']
        articles = art_eng + art_fre + art_prt + art_esp + art_ger
        for i, myWord in enumerate(myString.split()):
            if i == 0:
                myNewString = myWord if myWord not in articles else ''
                if myNewString == '':
                    self.log('SELF:: Removed Initial (in)definitive article: %s', myWord)
                continue
            try:                    # if it converts, it's a number stop
                float(myWord)      
                self.log('SELF:: Split at stand-alone digit: %s', myWord)
                break
            except ValueError:      # it's a string keep building
                myNewString = '{0} {1}'.format(myNewString, myWord)

        # reassign newly created string and remove multiple spaces
        myString = ' '.join(myNewString.split())

        # GEVI uses a maximum of 24 characters when searching, make sure that this string only contains whole words
        if len(myString) > 24:
            for i in range(24, 0, -1):
                if myString[i] == ' ':
                    break
                myString = myString[:i]

        myString = String.URLEncode(myString.strip())
        self.log('SELF:: Search String = %s', myString)
        return myString

    # -------------------------------------------------------------------------------------------------------------------------------
    def getIAFDActorImage(self, actor):
        ''' check IAFD web site for better quality actor thumbnails irrespective of whether we have a thumbnail or not '''
        photourl = ''
        actor = String.StripDiacritics(actor).lower()
        fullname = actor.replace(' ', '').replace("'", '').replace(".", '')
        full_name = actor.replace(' ', '-').replace("'", '&apos;')

        # actors are categorised on iafd as male, director, female in order of likelihood
        for gender in ['m', 'd']:
            iafd_url = 'http://www.iafd.com/person.rme/perfid={0}/gender={1}/{2}.htm'.format(fullname, gender, full_name)
            self.log('SELF:: Actor  %s - IAFD url: %s', actor, iafd_url)
            # Check URL exists and get actors thumbnail
            try:
                photourl = HTML.ElementFromURL(iafd_url).xpath('//*[@id="headshot"]/img')[0].get('src')
                photourl = photourl.replace('headshots/', 'headshots/thumbs/th_')
                photourl = 'nophoto' if 'nophoto' in photourl else photourl
                break   # if we have got here then actor has a page, stop iteration
            except:
                self.log('SELF:: NO IAFD Actor Page')

        return photourl

    # -------------------------------------------------------------------------------------------------------------------------------
    def log(self, message, *args):
        ''' log messages '''
        Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    # -------------------------------------------------------------------------------------------------------------------------------
    def search(self, results, media, lang, manual):
        ''' Search For Media Entry '''
        if not media.items[0].parts[0].file:
            return
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])

        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version      : v.%s', VERSION_NO)
        self.log('SEARCH:: Python       : %s', sys.version_info)
        self.log('SEARCH:: Platform     : %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Prefs->delay : %s', DELAY)
        self.log('SEARCH::      ->regex : %s', FILEPATTERN)
        self.log('SEARCH:: media.title  : %s', media.title)
        self.log('SEARCH:: File Name    : %s', filename)
        self.log('SEARCH:: File Folder  : %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check filename format
        try:
            group_studio, group_title, group_year = self.matchFilename(filename)
            self.log('SEARCH:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)
        except Exception as e:
            self.log('SEARCH:: Skipping %s', e)
            return

        # Compare Variables used to check against the studio name on website: remove all umlauts, accents and ligatures
        compareStudio = self.NormaliseComparisonString(group_studio)
        compareTitle = self.NormaliseComparisonString(group_title)
        compareReleaseDate = datetime.datetime(int(group_year), 12, 31) # default to 31 Dec of Filename yesr

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        searchTitle = self.CleanSearchString(group_title)
        searchQuery = BASE_SEARCH_URL.format(searchTitle)

        # Finds the entire media enclosure <Table> element then steps through the rows
        morePages = True
        while morePages:
            self.log('SEARCH:: Search Query: %s', searchQuery)
            try:
                html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
            except Exception as e:
                self.log('SEARCH:: Error: Search Query did not pull any results: %s', e)
                return

            try:
                searchQuery = html.xpath('//a[text()="Next"]/@href')[0]
                searchQuery = "{0}/{1}".format(BASE_URL, searchQuery)   # href does not have base_url in it
                self.log('SEARCH:: Next Page Search Query: %s', searchQuery)
                pageNumber = int(searchQuery.split('&where')[0].split('page=')[1]) - 1
                morePages = True if pageNumber <= 10 else False
            except:
                searchQuery = ''
                self.log('SEARCH:: No More Pages Found')
                pageNumber = 1
                morePages = False

            titleList = html.xpath('//table[contains(@class,"d")]/tr/td[@class="cd"]/parent::tr')
            self.log('SEARCH:: Result Page No: %s, Titles Found %s', pageNumber, len(titleList))

            for title in titleList:
                # Site Title
                try:
                    siteTitle = title[0].text_content().strip()
                    siteTitle = self.NormaliseComparisonString(siteTitle)
                    self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
                    if siteTitle != compareTitle:
                        continue
                except:
                    self.log('SEARCH:: Error getting Site Title')
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('.//a/@href')[0]
                    if BASE_URL not in siteURL:
                        siteURL = BASE_URL + siteURL
                    self.log('SEARCH:: Site Title url: %s', siteURL)
                except:
                    self.log('SEARCH:: Error getting Site Title Url')
                    continue

                # Access Site URL for Studio and Release Date information
                try:
                    html = HTML.ElementFromURL(siteURL, sleep=DELAY)
                except Exception as e:
                    self.log('SEARCH:: Error reading Site URL page: %s', e)
                    continue

                # Site Studio / Release Date
                try:
                    foundStudio = False
                    foundReleaseDate = False

                    # get distributor/studio
                    htmlSiteStudio = html.xpath('//a[contains(@href, "/C/")]/text()[normalize-space()]')
                    self.log('SEARCH:: %s Site URL Distributor/Studio: %s', len(htmlSiteStudio), htmlSiteStudio)
                    
                    # get the release dates - if not numeric replace with file year
                    htmlReleaseDate = html.xpath('//td[.="released" or .="produced"]/following-sibling::td[1]/text()[normalize-space()]')
                    htmlReleaseDate = [x if unicode(x, 'utf-8').isnumeric() else group_year for x in htmlReleaseDate] 
                    self.log('SEARCH:: %s Site URL Release Dates: %s', len(htmlReleaseDate), htmlReleaseDate)

                    # correlate studio and date lists - then get unique values
                    correlatedList = ["{0}:{1}".format(i, j) for i, j in zip(htmlSiteStudio, htmlReleaseDate)] 
                    correlatedList = list(set(correlatedList))
                    self.log('SEARCH:: %s Correlated List: %s', len(correlatedList), correlatedList)
                    for correlated in correlatedList:
                        siteStudio, siteReleaseDate = correlated.split(":")

                        # site studio
                        try:
                            self.log('SEARCH:: Studio: %s Compare against: %s', compareStudio, siteStudio)
                            self.matchStudioName(compareStudio, siteStudio)
                            foundStudio = True
                        except Exception as e:
                            self.log('SEARCH:: Error: %s', e)
                            continue

                        # site release date
                        try:
                            self.log('SEARCH:: Release Date: %s Compare against: %s', compareReleaseDate, siteReleaseDate)
                            siteReleaseDate = self.matchReleaseDate(compareReleaseDate, siteReleaseDate)
                            foundReleaseDate = True
                        except Exception as e:
                            self.log('SEARCH:: Error: %s', e)
                            continue

                        break # if we get here we have a match

                    if not foundStudio:
                        self.log('SEARCH:: Error No Matching Site Studio')
                        continue

                    if not foundReleaseDate:
                        self.log('SEARCH:: Error No Matching Site Release Date')
                        continue

                except Exception as e:
                    self.log('SEARCH:: Error getting Site Studio / Release Date %s', e)
                    continue

                # we should have a match on studio, title and year now
                results.Append(MetadataSearchResult(id=siteURL + '|' + siteReleaseDate.strftime(DATEFORMAT), name=group_title, score=100, lang=lang)) 
                return

    # -------------------------------------------------------------------------------------------------------------------------------
    def update(self, metadata, media, lang, force=True):
        ''' Update Media Entry '''
        folder, filename = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log('-----------------------------------------------------------------------')
        self.log('UPDATE:: Version    : v.%s', VERSION_NO)
        self.log('UPDATE:: File Name  : %s', filename)
        self.log('UPDATE:: File Folder: %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check filename format
        try:
            group_studio, group_title, group_year = self.matchFilename(filename)
            self.log('UPDATE:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)
        except Exception as e:
            self.log('UPDATE:: Skipping %s', e)
            return

        # Fetch HTML.
        html = HTML.ElementFromURL(metadata.id.split('|')[0], timeout=60, errors='ignore', sleep=DELAY)

        #  The following bits of metadata need to be established and used to update the movie on plex
        #    1.  Metadata that is set by Agent as default
        #        a. Studio               : From studio group of filename - no need to process this as above
        #        b. Title                : From title group of filename - no need to process this as is used to find it on website
        #        c. Tag line             : Corresponds to the url of movie
        #        d. Originally Available : set from metadata.id (search result)
        #        e. Content Rating       : Always X
        #    2.  Metadata retrieved from website
        #        a. Summary 
        #        b. Countries            : Alphabetic order
        #        c. Rating
        #        d. Directors            : List of Directors (alphabetic order)
        #        e. Cast                 : List of Actors and Photos (alphabetic order) - Photos sourced from IAFD
        #        f. Genre
        #        g. Posters/Background 

        # 1a.   Studio - straight of the file name
        metadata.studio = group_studio
        self.log('UPDATE:: Studio: %s' % metadata.studio)

        # 1b.   Set Title
        metadata.title = group_title
        self.log('UPDATE:: Video Title: %s' % metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = metadata.id.split('|')[0]
        metadata.originally_available_at = datetime.datetime.strptime(metadata.id.split('|')[1], DATEFORMAT)
        metadata.year = metadata.originally_available_at.year
        self.log('UPDATE:: Tagline: %s', metadata.tagline)
        self.log('UPDATE:: Default Originally Available Date: %s', metadata.originally_available_at)    

        # 1e.   Set Content Rating to Adult
        metadata.content_rating = 'X'
        self.log('UPDATE:: Content Rating: X')

        # 2a.   Summary = Promo + Scenes + Action Notes
        try:
            promo = ''
            htmlpromo = html.xpath('//td[contains(text(),"promo/")]//following-sibling::td//span[@style]/text()[following::br]')
            for item in htmlpromo:
                promo = '{0}\n{1}'.format(promo, item)
            self.log('UPDATE:: Promo Found: %s', promo)
        except Exception as e:
            promo = ''
            self.log('UPDATE:: Error getting Promo: %s', e)

        # action notes
        try:
            htmlactionnotes = html.xpath('//td[@class="sfn"]//text()')
            actionnotes = ''.join(htmlactionnotes).replace('\n', '')
            self.log('UPDATE:: Action Notes: %s', actionnotes)
        except Exception as e:
            actionnotes = ''
            self.log('UPDATE:: Error getting Action Notes: %s', e)

        # scenes
        try:
            htmlscenes = html.xpath('//td[contains(text(),"scenes /")]//following-sibling::td//div')
            scenes = '' if len(htmlscenes) == 0 else '\nScenes: {0}'.format(actionnotes)
            for item in htmlscenes:
                scenes = '{0}\n{1}'.format(scenes, item.text_content().strip())
            self.log('UPDATE:: Scenes Found: %s', scenes)
        except Exception as e:
            scenes = ''
            self.log('UPDATE:: Error getting Scenes: %s', e)

        # combine and update
        summary = promo + scenes
        if summary:
            regex = r'View this scene at.*|found in compilation.*|see also.*'
            pattern = re.compile(regex, re.IGNORECASE)
            summary = re.sub(pattern, '', summary)
        metadata.summary = summary if len(summary.strip()) > 0 else ' '

        # 2b.   Countries
        try:
            countries = []
            htmlcountries = html.xpath('//td[contains(text(),"location")]//following-sibling::td[1]/text()')
            self.log('UPDATE:: Countries List %s', htmlcountries)
            for country in htmlcountries:
                country = country.strip()
                if len(country) > 0:
                    countries.append(country)

            countries.sort()
            metadata.countries.clear()
            for country in countries:
                metadata.countries.add(country)
        except Exception as e:
            self.log('UPDATE:: Error getting Countries(ies): %s', e)

        # 2c.   Rating (out of 4 Stars) = Rating can be a maximum of 10 - float value
        try:
            rating = html.xpath('//td[contains(text(),"rating out of 4")]//following-sibling::td[1]/text()')[0].strip()
            rating = rating.count('*') * 2.5
            self.log('UPDATE:: Film Rating %s', rating)
            metadata.rating = rating
        except Exception as e:
            self.log('UPDATE:: Error getting Rating: %s', e)

        # 2d.   Directors
        try:
            directors = []
            htmldirector = html.xpath('//td[contains(text(),"director")]//following-sibling::td[1]/a/text()')
            self.log('UPDATE:: Director List %s', htmldirector)
            for directorname in htmldirector:
                director = directorname.strip()
                if len(director) > 0:
                    directors.append(director)

            directors.sort()
            metadata.directors.clear()
            for director in directors:
                Director = metadata.directors.new()
                Director.name = director
        except Exception as e:
            self.log('UPDATE:: Error getting Director(s): %s', e)

        # 2e.   Cast: get thumbnails from IAFD as they are right dimensions for plex cast list
        try:
            castdict = {}
            htmlcast = html.xpath('//td[@class="pd"]/a/text()')
            for castname in htmlcast:
                cast = castname.strip()
                if not cast:
                    continue
                if '(' in cast:
                    cast = cast.split('(')[0]
                castdict[cast] = self.getIAFDActorImage(cast)
                castdict[cast] = '' if castdict[cast] == 'nophoto' else castdict[cast]

            # sort the dictionary and add kv to metadata
            metadata.roles.clear()
            for key in sorted(castdict):
                role = metadata.roles.new()
                role.name = key
                role.photo = castdict[key]
        except Exception as e:
            self.log('UPDATE - Error getting Cast: %s', e)

        # 2f.   Genre
        try:
            genres = []
            htmlgenres = html.xpath('//td[contains(text(),"category")]//following-sibling::td[1]/text()')
            self.log('UPDATE:: %s Genres Found: %s', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                genre = genre.strip()
                if genre:
                    genres.append(genre)

            genres.sort()
            metadata.genres.clear()
            for genre in genres:
                metadata.genres.add(genre)
        except Exception as e:
            self.log('UPDATE:: Error getting Genres: %s', e)

        # 2g.   Posters/Background Art
        try:
            htmlimages = html.xpath('//td[@class="gp"]/a/@href')
            posterImages = htmlimages if len(htmlimages) == 1 else htmlimages[::2]          # assume poster images first
            backgroundImages = htmlimages if len(htmlimages) == 1 else htmlimages[1::2]     # are followed by their background images

            validPosterList = []
            for image in posterImages:
                image = (BASE_URL if BASE_URL not in image else '') + image
                self.log('UPDATE:: Movie Poster Found: %s', image)
                validPosterList.append(image)
                if image not in metadata.posters:
                    metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order = 1)
                #  clean up and only keep the poster we have added
                metadata.posters.validate_keys(validPosterList)

            validArtList = []
            for image in backgroundImages:
                image = (BASE_URL if BASE_URL not in image else '') + image
                self.log('UPDATE:: Movie Background Art Found: %s', image)
                validArtList.append(image)
                if image not in metadata.art:
                    metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order = 1)
                #  clean up and only keep the Art we have added
                metadata.art.validate_keys(validArtList)
        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Background Art: %s', e)
