# General Functions found in all agents
# -------------------------------------------------------------------------------------------------------------------------------
def matchFilename(self, filename):
    ''' Check filename on disk corresponds to regex preference format '''
    pattern = re.compile(REGEX)
    matched = pattern.search(filename)
    if not matched:
        raise Exception("File Name [{0}] not in the expected format: (Studio) - Title (Year)".format(filename))

    groups = matched.groupdict()
    filmVars = {}
    filmVars['Studio'] = groups['studio'].split(';')[0].strip() if ";" in groups['studio'] else groups['studio']
    filmVars['IAFDStudio'] = groups['studio'].split(';')[1].strip() if ";" in groups['studio'] else ''
    filmVars['CompareStudio'] = self.NormaliseComparisonString(filmVars['Studio'])
    filmVars['CompareIAFDStudio'] = self.NormaliseComparisonString(filmVars['IAFDStudio']) if filmVars['IAFDStudio'] else ''

    filmVars['Title'] =  groups['title']
    filmVars['ShortTitle'] = filmVars['Title']
    filmVars['CompareTitle'] = [''.join(sorted(self.NormaliseComparisonString(filmVars['Title'])))]
    filmVars['SearchTitle'] = filmVars['Title']

    filmVars['IAFDTitle'] =  filmVars['Title']
    filmVars['IAFDShortTitle'] = filmVars['ShortTitle']
    filmVars['IAFDCompareTitle'] = filmVars['CompareTitle']
    filmVars['IAFDSearchTitle'] = filmVars['IAFDTitle']

    filmVars['Year'] = groups['year']
    filmVars['CompareDate'] = datetime.datetime(int(filmVars['Year']), 12, 31).strftime(DATEFORMAT) # default to 31 Dec of Filename year

    filmVars['Compilation'] = "No"
    filmVars['FoundOnIAFD'] = "No"

    # For this title: (Raging Stallion Studios) - Hardcore Fetish Series - Pissing 1 - Piss Off (2009)
    #    Collections: [Hardcore Fetish Series, Pissing]
    #         Series: [Pissing 1]
    #    Short Title: Piss Off
    collections = []
    collections.append(filmVars['Studio'])       # All films have their Studio Name as a collection
    series = []
    splitFilmTitle = filmVars['Title'].split(' - ')
    splitFilmTitle = [x.strip() for x in splitFilmTitle]
    splitCount = len(splitFilmTitle) - 1
    for index, partTitle in enumerate(splitFilmTitle):
        pattern = r'(?<![-.])\b[0-9]+\b(?!\.[0-9])$'        # series matching = whole separate number at end of string
        matchedSeries = re.subn(pattern, '', partTitle)
        if matchedSeries[1]:
            seriesFound = True
            collections.insert(0, matchedSeries[0].strip()) # e.g. Pissing
            series.insert(0, partTitle)                     # e.g. Pissing 1
            if index < splitCount:                          # only blank out series info in title if not last split
                splitFilmTitle[index] = ''
        else:
            if index < splitCount:                          # only add to collection if not last part of title e.g. Hardcore Fetish Series
                collections.insert(0, partTitle)
                splitFilmTitle[index] = ''

    filmVars['Collection'] = collections
    filmVars['Series'] = series
    filmVars['ShortTitle'] = ' '.join(splitFilmTitle).strip()
    if filmVars['ShortTitle'] not in filmVars['CompareTitle']:
        filmVars['CompareTitle'].append(''.join(sorted(self.NormaliseComparisonString(filmVars['ShortTitle']))))
    filmVars['SearchTitle'] = filmVars['ShortTitle']

    # prepare IAFD Title and Search String
    filmVars['IAFDTitle'] = unidecode(filmVars['ShortTitle']).replace(' - ', ': ')       # iafd needs colons in place to search correctly, removed all unicode
    filmVars['IAFDTitle'] = filmVars['IAFDTitle'].replace(' &', ' and')                  # iafd does not use &
    filmVars['IAFDTitle'] = filmVars['IAFDTitle'].replace('!', '')                       # remove !

    # split and take up to first occurence of character
    splitChars = ['-', '[', '(', ur'\u2013', ur'\u2014']
    pattern = ur'[{0}]'.format(''.join(splitChars))
    matched = re.search(pattern, filmVars['IAFDTitle'])  # match against whole string
    if matched:
        filmVars['IAFDTitle'] = filmVars['IAFDTitle'][:matched.start()]

    # strip standalone "1's"
    pattern = ur'(?<!\d)1(?!\d)'
    filmVars['IAFDTitle'] = re.sub(pattern, '', filmVars['IAFDTitle'])

    # strip definite and indefinite english articles
    articles = ['the ', 'a ', 'an ']
    pattern = ur'^({0})'.format('|'.join(articles))
    matched = re.search(pattern, filmVars['IAFDTitle'], re.IGNORECASE)  # match against whole string
    if matched:
        self.log('GENF  :: test *******')
        filmVars['IAFDTitle'] = filmVars['IAFDTitle'][matched.end():]
        tempCompare = ''.join(sorted(self.NormaliseComparisonString(filmVars['IAFDTitle'])))
        if tempCompare not in filmVars['IAFDCompareTitle']:
            filmVars['IAFDCompareTitle'].append(tempCompare)

    # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string, also remove '!'
    filmVars['IAFDSearchTitle'] = String.StripDiacritics(filmVars['IAFDTitle']).strip()
    filmVars['IAFDSearchTitle'] = String.URLEncode(filmVars['IAFDSearchTitle'])
    filmVars['IAFDSearchTitle'] = filmVars['IAFDSearchTitle'].replace('%25', '%').replace('*', '')

    # print out dictionary values / normalise unicode
    for key in sorted(filmVars.keys()):
        filmVars[key] = [self.NormaliseUnicode(x) for x in filmVars[key]] if type(filmVars[key]) is list else self.NormaliseUnicode(filmVars[key])
        self.log('GENF  :: {0: <22}: {1}'.format(key, filmVars[key]))

    return filmVars

# -------------------------------------------------------------------------------------------------------------------------------
def matchTitle(self, siteTitle, FILMDICT):
    ''' match file title against website/iafd title: Boolean Return '''
    compareSiteTitle = ''.join(sorted(self.NormaliseComparisonString(siteTitle)))

    testSite = 'Passed' if compareSiteTitle in FILMDICT['CompareTitle'] else 'Passed' if compareSiteTitle in FILMDICT['IAFDCompareTitle'] else 'Failed'

    self.log('GENF  :: Site Title                    "%s"', siteTitle)
    self.log('GENF  :: Title Comparison              [%s]\tSite: "%s"\tFile: ["%s", "%s"]', testSite, siteTitle, FILMDICT['Title'], FILMDICT['ShortTitle'])

    if testSite == 'Failed':
        raise Exception('Title Match Failure!')

    return True

# -------------------------------------------------------------------------------------------------------------------------------
def matchStudio(self, siteStudio, FILMDICT, useAgent=True):
    ''' match file studio name against website studio/iafd name: Boolean Return '''
    compareSiteStudio = self.NormaliseComparisonString(siteStudio)
    dtStudio = FILMDICT['Studio'] if useAgent else FILMDICT['IAFDStudio']
    dtCompareStudio = FILMDICT['CompareStudio'] if useAgent else FILMDICT['CompareIAFDStudio']

    testStudio = 'Full Match' if compareSiteStudio == dtCompareStudio else 'Partial Match' if compareSiteStudio in dtCompareStudio or dtCompareStudio in compareSiteStudio else 'Failed Match'

    self.log('GENF  :: Site Studio                   "%s"', siteStudio)
    self.log('GENF  :: Studio Comparison             [%s]\tSite: "%s"\tFile: "%s"', testStudio, siteStudio, dtStudio)

    if testStudio == 'Failed Match':
        raise Exception('Studio Match Failure!')

    return True

# -------------------------------------------------------------------------------------------------------------------------------
def matchReleaseDate(self, siteReleaseDate, FILMDICT):
    ''' match file year against website release date: return formatted site date if no error or default to formated file date '''
    fileReleaseDate = datetime.datetime.strptime(FILMDICT['CompareDate'], DATEFORMAT)
    if len(siteReleaseDate) == 4:      # a year has being provided - default to 31st December of that year
        siteReleaseDate = siteReleaseDate + '1231'
    siteReleaseDate = datetime.datetime.strptime(siteReleaseDate, DATEFORMAT)

    # there can not be a difference more than 366 days between FileName Date and siteReleaseDate
    dx = abs((fileReleaseDate - siteReleaseDate).days)

    self.log('GENF  :: Release Date                  "%s"', siteReleaseDate)
    self.log('GENF  :: Release Date Comparison       [%s]\t %s days\tSite: "%s"\tFile: "%s"', 'Failed' if dx > 366 else 'Pass', dx, siteReleaseDate.strftime('%Y %m %d'), fileReleaseDate.strftime('%Y %m %d'))

    if dx > 366:
        raise Exception('Release Date Match Failure!')

    # reset comparison date to above scrapping result
    FILMDICT['CompareDate'] = siteReleaseDate.strftime(DATEFORMAT)
    return siteReleaseDate

# -------------------------------------------------------------------------------------------------------------------------------
def NormaliseUnicode(self, myString):
    myString = unicode(myString)
    myString = unidecode(myString)
    return myString

# -------------------------------------------------------------------------------------------------------------------------------
def NormaliseComparisonString(self, myString):
    ''' Normalise string for, strip uneeded characters for comparison of web site values to file name regex group values '''
    # Check if string has roman numerals as in a series; note the letter I will be converted
    myString = '{0} '.format(myString)  # append space at end of string to match last characters 
    pattern = '\s(?=[MDCLXVI])M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3})$'
    matches = re.findall(pattern, myString, re.IGNORECASE)  # match against string
    if matches:
        RomanValues = {'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000}
        for count, match in enumerate(matches):
            myRoman = ''.join(match).upper()
            self.log('GENF  :: Found Roman Numeral: {0}.. {1} len[{2}]'.format(count, myRoman, len(myRoman)))
            myArabic = RomanValues[myRoman[-1]]
            for i in range(len(myRoman) - 1, 0, -1):
                if RomanValues[myRoman[i]] > RomanValues[myRoman[i - 1]]:
                    myArabic = myArabic - RomanValues[myRoman[i - 1]]
                else:
                    myArabic = myArabic + RomanValues[myRoman[i - 1]]
            romanString = ' {0}'.format(myRoman)
            arabicString = ' {0}'.format(myArabic)
            myString = myString.replace(romanString, arabicString)

    # convert to lower case and trim
    myString = myString.strip().lower()

    # normalise unicode characters
    myString = self.NormaliseUnicode(myString)

    # replace ampersand with 'and'
    myString = myString.replace('&', 'and')

    # standardise quotes replace "`" with straight quotes
    myString = myString.replace("`", "'")

    # strip domain suffixes, vol., volume from string, standalone "1's"
    pattern = ur'[.](org|com|net|co[.][a-z]{2})|Vol[.]|\bPart\b|\bVolume\b|(?<!\d)1(?!\d)|[^A-Za-z0-9]+'
    myString = re.sub(pattern, '', myString, flags=re.IGNORECASE)

    return myString

# -------------------------------------------------------------------------------------------------------------------------------
def TranslateString(self, myString, language):
    ''' Translate string into Library language '''
    myString = myString.strip()
    if language == 'xn' or language == 'xx':    # no language or language unknown
        self.log('GENF  :: Library Language: [%s], Run Translation: [False]', 'No Language' if language == 'xn' else 'Unknown')
    elif myString:
        translator = Translator(service_urls=['translate.google.com', 'translate.google.ca', 'translate.google.co.uk',
                                                'translate.google.com.au', 'translate.google.co.za', 'translate.google.br.com',
                                                'translate.google.pt', 'translate.google.es', 'translate.google.com.mx',
                                                'translate.google.it', 'translate.google.nl', 'translate.google.be',
                                                'translate.google.de', 'translate.google.ch', 'translate.google.at',
                                                'translate.google.ru', 'translate.google.pl', 'translate.google.bg',
                                                'translate.google.com.eg', 'translate.google.co.il', 'translate.google.co.jp',
                                                'translate.google.co.kr', 'translate.google.fr', 'translate.google.dk'])
        runTranslation = (language != SITE_LANGUAGE)
        self.log('GENF  :: [Library:Site] Language: [%s:%s], Run Translation: [%s]', language, SITE_LANGUAGE, runTranslation)
        if DETECT:
            detectString = re.findall(ur'.*?[.!?]', myString)[:4]   # take first 4 sentences of string to detect language
            detectString = ''.join(detectString)
            self.log('GENF  :: Detect Site Language [%s] using this text: %s', DETECT, detectString)
            try:
                detected = translator.detect(detectString)
                runTranslation = (language != detected.lang)
                self.log('GENF  :: Detected Language: [%s] Run Translation: [%s]', detected.lang, runTranslation)
            except Exception as e:
                self.log('GENF  :: Error Detecting Text Language: %s', e)

        try:
            myString = translator.translate(myString, dest=language).text if runTranslation else myString
            self.log('GENF  :: Translated [%s] Summary Found: %s', runTranslation, myString)
        except Exception as e:
            self.log('GENF  :: Error Translating Text: %s', e)

    return myString if myString else ' '     # return single space to initialise metadata summary field

# -------------------------------------------------------------------------------------------------------------------------------
def log(self, message, *args):
    ''' log messages '''
    if re.search('ERROR', message, re.IGNORECASE):
        Log.Error(PLUGIN_LOG_TITLE + ' - ' + message, *args)
    else:
        Log.Info(PLUGIN_LOG_TITLE + '  - ' + message, *args)

# -------------------------------------------------------------------------------------------------------------------------------