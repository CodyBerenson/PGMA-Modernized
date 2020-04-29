# GEVI - (IAFD)
'''
                                    Version History
                                    ---------------
    Date            Version             Modification
    7 Apr 2020      2019.12.25.7        Changed the agent to search past the first page of results
    8 Apr 2020      2020.12.25.8        Created new function to prepare the video title to build the search query
    12 Apr 2020     2020.12.25.9        removed line in updating countries as it raised an error in the logs
                                        logical error replacing full stops in title when preparing search string
    26 Apr 2020     2020.12.25.10       corrected search string: can only be 24 characters long and be comprised of full words
                                        search and replace of special characters in search string was not working correctly
    28 Apr 2020     2020.12.25.11       Failed to scrap for some titles, found errors stopped execution, so code placed in try: exception
                                        added no spaces comparison to studio found results
                                        Added Scene breakdown scrape to summary
                                        Added Ratings scrape

---------------------------------------------------------------------------------------------------------------
'''

import datetime, linecache, platform, os, re, string, sys, urllib, lxml

# Version / Log Title 
VERSION_NO = '2019.12.25.11'
PLUGIN_LOG_TITLE = 'GEVI'

# Pattern: (Studio) - Title (Year).ext: ^\((?P<studio>.+)\) - (?P<title>.+) \((?P<year>\d{4})\)
# if title on website has a hyphen in its title that does not correspond to a colon replace it with an em dash in the corresponding position
FILEPATTERN = Prefs['regex']
 
# Delay used when requesting HTML, may be good to have to prevent being banned from the site
DELAY = int(Prefs['delay'])

# URLS
BASE_URL = 'https://www.gayeroticvideoindex.com'
BASE_SEARCH_URL = BASE_URL + '/search.php?type=t&where=m&query={0}&Search=Search&page={1}'

def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'

def ValidatePrefs():
    pass

class GEVI(Agent.Movies):
    name = 'GEVI (IAFD)'
    languages = [Locale.Language.English]
    primary_provider = False
    preference = True
    media_types = ['Movie']
    contributes_to = ['com.plexapp.agents.GayAdult', 'com.plexapp.agents.GayAdultFilms']

    def matchedFilename(self, file):
        # match file name to regex
        pattern = re.compile(FILEPATTERN)
        return pattern.search(file)

    def getFilenameGroups(self, file):
        # return groups from filename regex match
        pattern = re.compile(FILEPATTERN)
        matched = pattern.search(file)
        if matched:
            groups = matched.groupdict()
            return groups['studio'], groups['title'], groups['year']

    # Normalise string for Comparison, strip all non alphanumeric characters, Vol., Volume, Part, and 1 in series
    def NormaliseComparisonString(self, myString):
        # convert to lower case and trim
        myString = myString.strip().lower()

        # convert sort order version to normal version i.e "Best of Zak Spears, The -> the Best of Zak Spears"
        if myString.count(', the'):
            myString = 'the ' + myString.replace(', the', '', 1)
        if myString.count(', An'):
            myString = 'an ' + myString.replace(', an', '', 1)
        if myString.count(', a'):
            myString = 'a ' + myString.replace(', a', '', 1)

        # remove vol/volume/part and vol.1 etc wording as filenames dont have these to maintain a uniform search across all websites and remove all non alphanumeric characters
        myString = myString.replace('&', 'and').replace(' 1', '').replace(' vol.', '').replace(' volume', '').replace(' part','')

        # strip diacritics
        myString = String.StripDiacritics(myString)

        # remove all non alphanumeric chars
        regex = re.compile(r'\W+')
        return regex.sub('', myString)

    # Prepare Video title for search query
    def PrepareSearchQueryString(self, myString):
        # convert to lower case and trim and strip diacritics - except ß which we replace with one s
        myString = myString.replace('ß', 's')
        myString = String.StripDiacritics(myString)
        myString = myString.lower().strip()

        # split myString at first digit as GEVI will not find titles with digits in them
        for firstDigit, character in enumerate(myString):
            if character.isdigit():
                uptofirstDigit = firstDigit - 1
                myString = myString[0:uptofirstDigit]
                break

        # removal of definitive/indefinitive articles in title as it messes GEVIs search algorithm
        # English, French and German
        intialWords = ['a', 'an', 'un', 'une', 'ein', 'eine', 'the', 'le', 'la', 'les', 'das', 'die', 'der']
        firstWord = myString.split()[0]
        if firstWord in intialWords:
            self.log('SELF:: Remove Initial in/definitive article: %s', firstWord)
            spliceAt = len(firstWord) + 1
            myString = myString[spliceAt:]
        
        # these need to be replace with a space
        replaceChars = ['-', '–', "'", ',' '&', '!', '.']
        rx = '[' + re.escape(''.join(replaceChars)) + ']'
        myString = re.sub(rx, ' ', myString)

        # double spaces to be replaced by single spaces, repeat it twice in case there are triple/quadruple spaces
        myString = myString.replace('  ', ' ').replace('  ', ' ')

        # GEVI uses a maximum of 24 characters when searching, make sure that this string only contains whole words
        if len(myString) > 24:
            for i in range(24, 0, -1):
                if myString[i] == ' ':
                    break
                myString = myString[:i]                

        self.log('SELF:: Search String = %s', myString)
        return myString

    # check IAFD web site for better quality actor thumbnails irrespective of whether we have a thumbnail or not
    def getIAFDActorImage(self, actor):
        photourl = ''
        actor = actor.lower()
        fullname = actor.replace(' ','').replace("'", '').replace(".", '')
        full_name = actor.replace(' ','-').replace("'", '&apos;')

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

    def log(self, message, *args):
        Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    def search(self, results, media, lang, manual):
        self.log('-----------------------------------------------------------------------')
        self.log('SEARCH:: Version - v.%s', VERSION_NO)
        self.log('SEARCH:: Platform - %s %s', platform.system(), platform.release())
        self.log('SEARCH:: Prefs->delay - %s', DELAY)
        self.log('SEARCH::      ->regex - %s', FILEPATTERN)
        self.log('SEARCH:: media.title - %s', media.title)
        self.log('SEARCH:: media.items[0].parts[0].file - %s', media.items[0].parts[0].file)
        self.log('SEARCH:: media.items - %s', media.items)
        self.log('SEARCH:: media.filename - %s', media.filename)
        self.log('SEARCH:: lang - %s', lang)
        self.log('SEARCH:: manual - %s', manual)
        self.log('-----------------------------------------------------------------------')

        if not media.items[0].parts[0].file:
            return

        folder, file = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log('SEARCH:: File Name: %s', file)
        self.log('SEARCH:: Enclosing Folder: %s', folder)

        # Check filename format
        if not self.matchedFilename(file):
            self.log('SEARCH:: Skipping %s because the file name is not in the expected format: (Studio) - Title (Year)', file)
            return

        group_studio, group_title, group_year = self.getFilenameGroups(file)
        self.log('SEARCH:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)

        # compare Studio - used to check against the studio name on website
        compareStudio = self.NormaliseComparisonString(group_studio)

        #  Release date default to December 31st of Filename value compare against release date on Website
        compareReleaseDate = datetime.datetime(int(group_year), 12, 31)

        # saveTitle corresponds to the real title of the movie.
        saveTitle = group_title
        self.log('SEARCH:: Original Group Title: %s', saveTitle)

        # compareTitle will be used to search against the titles on the website, remove all umlauts, accents and ligatures
        compareTitle = self.NormaliseComparisonString(saveTitle)

        # Search Query - for use to search the internet, remove all non alphabetic characters as GEVI site returns no results if apostrophes or commas exist etc..
        searchTitle = self.PrepareSearchQueryString(saveTitle)

        # Finds the entire media enclosure <Table> element then steps through the rows
        pageNumber = 0
        morePages = True
        while morePages:
            pageNumber += 1
            self.log('SEARCH:: Result Page No: %s', pageNumber)

            searchQuery = BASE_SEARCH_URL.format(String.URLEncode(searchTitle), pageNumber)
            self.log('SEARCH:: Search Query: %s', searchQuery)
            html = HTML.ElementFromURL(searchQuery, timeout=20, sleep=DELAY)
            titleList = html.xpath('//table[contains(@class,"d")]/tr')
            self.log('SEARCH:: Titles List: %s Found', len(titleList))

            try:
                testmorePages = html.xpath('.//a[text()="Next"]/text()')[0]
                morePages = True
            except:
                morePages = False

            for title in titleList:
                # Site Title
                try:
                    siteTitle = title[0].text_content().strip()
                    if siteTitle == '':
                        break

                    siteTitle = self.NormaliseComparisonString(siteTitle)
                    self.log('SEARCH:: Title Match: [%s] Compare Title - Site Title "%s - %s"', (compareTitle == siteTitle), compareTitle, siteTitle)
                    if siteTitle != compareTitle:
                        continue
                except:
                    self.log('SEARCH:: Error getting Site Title')
                    continue

                # Site Title URL
                try:
                    siteURL = title.xpath('./td/a/@href')[0]
                    if BASE_URL not in siteURL:
                        siteURL = BASE_URL + siteURL
                    self.log('SEARCH:: Site Title url: %s', siteURL)
                except:
                    self.log('SEARCH:: Error getting Site Title Url')

                # Search Website for date - date is in format yyyy - so default to December 31st
                try:
                    siteReleaseDate = title[1].text_content().strip()
                    self.log('SEARCH:: Search Release Date: %s', siteReleaseDate)
                    siteReleaseDate = datetime.datetime(int(siteReleaseDate), 12, 31)
                except:
                    siteReleaseDate = compareReleaseDate
                    self.log('SEARCH:: Error getting Search Release Date')

                # need to check that the studio name of this title matches to the filename's studio
                try:
                    siteStudio = title[2].text_content().strip()
                    self.log('SEARCH:: Search Studio: %s', siteStudio)
                    siteStudio = self.NormaliseComparisonString(siteStudio)
                    if siteStudio == compareStudio:
                        self.log('SEARCH:: Studio: Full Word Match: Filename: %s = Website: %s', compareStudio, siteStudio)
                    elif siteStudio in compareStudio:
                        self.log('SEARCH:: Studio: Part Word Match: Website: %s IN Filename: %s', siteStudio, compareStudio)
                    elif compareStudio in siteStudio:
                        self.log('SEARCH:: Studio: Part Word Match: Filename: %s IN Website: %s', compareStudio, siteStudio)
                    else:
                        # remove spaces in comparison variables and check for equality
                        noSpaceSiteStudio = siteStudio.replace(' ', '')
                        noSpaceCompareStudio = compareStudio.replace(' ', '')
                        if noSpaceSiteStudio != noSpaceCompareStudio:
                            self.log('SEARCH:: Studio: Full Match Fail: Read Result Page: %s', siteURL)
                            # GEVI sometimes lists the distributor rather than the studio on the search results, 
                            # therefore if we get a match on the title look further
                            html = HTML.ElementFromURL(siteURL, sleep=DELAY)
                            siteStudio = html.xpath('//td[contains(text(),"studio")]//following-sibling::td[1]/a/text()')[0].strip()
                            siteStudio = self.NormaliseComparisonString(siteStudio)
                            if siteStudio == compareStudio:
                                self.log('SEARCH:: Studio: Full Word Match: Filename: %s = Website: %s', compareStudio, siteStudio)
                            elif siteStudio in compareStudio:
                                self.log('SEARCH:: Studio: Part Word Match: Website: %s IN Filename: %s', siteStudio, compareStudio)
                            elif compareStudio in siteStudio:
                                self.log('SEARCH:: Studio: Part Word Match: Filename: %s IN Website: %s', compareStudio, siteStudio)
                            else:
                                # strip spaces out of new studio name and compare
                                noSpaceSiteStudio = siteStudio.replace(' ', '')
                                if noSpaceSiteStudio != noSpaceCompareStudio:
                                    self.log('SEARCH:: Studio: Full Match Fail: Filename: %s != Website: %s', compareStudio, siteStudio)
                                    continue

                        # get the release date in the movie page as it may be different from the tabulated result
                        try:
                            sitePreviousReleaseDate = siteReleaseDate
                            siteReleaseDate = html.xpath('//td[contains(text(),"produced")]//following-sibling::td[1]/text()')[0].strip()
                            self.log('SEARCH:: Release Date: %s', siteReleaseDate)
                            siteReleaseDate = datetime.datetime(int(siteReleaseDate), 12, 31)
                        except:
                            # if none found at this level - use search result date
                            siteReleaseDate = sitePreviousReleaseDate
                            self.log('SEARCH:: Error getting Site Release Date')
                except:
                    self.log('SEARCH:: Error getting Site Studio')
                    continue

                # there can not be a difference more than 366 days
                timedelta = siteReleaseDate - compareReleaseDate
                self.log('SEARCH:: Compare Release Date - %s Site Date - %s : Dx [%s] days"', compareReleaseDate, siteReleaseDate, timedelta.days)
                if abs(timedelta.days) > 366:
                    self.log('SEARCH:: Difference of more than a year between file date and %s date from Website')
                    continue

                # we should have a match on studio, title and year now
                results.Append(MetadataSearchResult(id = siteURL + '|' + siteReleaseDate.strftime('%d/%m/%Y'), name = saveTitle, score = 100, lang = lang)) 
                return

    def update(self, metadata, media, lang, force=True):
        folder, file = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
        self.log('-----------------------------------------------------------------------')
        self.log('UPDATE:: CALLED v.%s', VERSION_NO)
        self.log('UPDATE:: File Name: %s', file)
        self.log('UPDATE:: Enclosing Folder: %s', folder)
        self.log('-----------------------------------------------------------------------')

        # Check filename format
        if not self.matchedFilename(file):
            self.log('UPDATE:: Skipping %s because the file name is not in the expected format: (Studio) - Title (Year)', file)
            return

        group_studio, group_title, group_year = self.getFilenameGroups(file)
        self.log('UPDATE:: Processing: Studio: %s   Title: %s   Year: %s', group_studio, group_title, group_year)

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
        self.log('UPDATE:: Studio: "%s"' % metadata.studio)

        # 1b.   Set Title
        metadata.title = group_title
        self.log('UPDATE:: Video Title: "%s"' % metadata.title)

        # 1c/d. Set Tagline/Originally Available from metadata.id
        metadata.tagline = metadata.id.split('|')[0]
        metadata.originally_available_at = datetime.datetime.strptime(metadata.id.split('|')[1], '%d/%m/%Y')
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
            scenes = '\nScenes: {0}'.format(actionnotes)
            htmlscenes = html.xpath('//td[contains(text(),"scenes /")]//following-sibling::td//div')
            for item in htmlscenes:
                scenes = '{0}\n{1}'.format(scenes, item.text_content().strip())
            self.log('UPDATE:: Scenes Found: %s', scenes)
        except Exception as e:
            scenes = ''
            self.log('UPDATE:: Error getting Scenes: %s', e)

        # combine and update
        summary = promo + scenes
        if summary:
            regex = r'View this scene at.*'
            pattern = re.compile(regex, re.IGNORECASE)
            summary = re.sub(pattern, '', summary)
            metadata.summary = summary

        # 2b.   Countries
        try:
            countriesdict = {}
            htmlcountries = html.xpath('//td[contains(text(),"location")]//following-sibling::td[1]/text()')
            self.log('UPDATE:: Countries List %s', htmlcountries)
            for countriesname in htmlcountries:
                countries = countriesname.strip()
                if (len(countries) > 0):
                    countriesdict[countries] = None

            # sort the dictionary and add key to metadata
            metadata.countries.clear()
            for key in sorted (countriesdict): 
                metadata.countries.add(key)
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
            directordict = {}
            htmldirector = html.xpath('//td[contains(text(),"director")]//following-sibling::td[1]/a/text()')
            self.log('UPDATE:: Director List %s', htmldirector)
            for directorname in htmldirector:
                director = directorname.strip()
                if (len(director) > 0):
                    directordict[director] = None

            # sort the dictionary and add kv to metadata
            metadata.directors.clear()
            for key in sorted (directordict): 
                director = metadata.directors.new()
                director.name = key
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
            for key in sorted (castdict): 
                role = metadata.roles.new()
                role.name = key
                role.photo = castdict[key]
        except Exception as e:
            self.log('UPDATE - Error getting Cast: %s', e)

        # 2f.   Genre
        try:
            metadata.genres.clear()
            htmlgenres = html.xpath('//td[contains(text(),"category")]//following-sibling::td[1]/text()')
            self.log('UPDATE:: %s Genres Found: "%s"', len(htmlgenres), htmlgenres)
            for genre in htmlgenres:
                genre = genre.strip()
                if (len(genre) > 0):
                    metadata.genres.add(genre)
        except Exception as e:
            self.log('UPDATE:: Error getting Genres: %s', e)

        # 2g.   Posters/Background Art
        try:
            htmlimage = html.xpath('//td[@class="gp"]/a/@href')
            image = htmlimage[0]
            if BASE_URL not in image:
                image = BASE_URL + image
            self.log('UPDATE:: Movie Poster Found: "%s"', image)
            validPosterList = [image]
            if image not in metadata.posters:
                metadata.posters[image] = Proxy.Media(HTTP.Request(image).content, sort_order = 1)
            #  clean up and only keep the poster we have added
            metadata.posters.validate_keys(validPosterList)

            # if there is no background art - use poster as background art too
            if len(htmlimage) == 2:
                image = htmlimage[1]
            else:
                image = htmlimage[0]

            if BASE_URL not in image:
                image = BASE_URL + image
            self.log('UPDATE:: Movie Background Art Found: "%s"', image)
            validArtList = [image]
            if image not in metadata.art:
                metadata.art[image] = Proxy.Media(HTTP.Request(image).content, sort_order = 1)
            #  clean up and only keep the Art we have added
            metadata.art.validate_keys(validArtList)
        except Exception as e:
            self.log('UPDATE:: Error getting Poster/Background Art: %s', e)