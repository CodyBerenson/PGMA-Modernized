'''
General Functions found in all agents
                                                  Version History
                                                  ---------------
    Date            Modification
    27 Mar 2021   Added curly single quotes to string normalisation in addition to `, all quotes single quotes are now replaced by straight quotes
    03 May 2021   Issue #96 - Series Titles matching...
                  Added duration matching between filename duration and iafd duration
    08 May 2021   Merged GenFunctions.py with Utils.py created by codeanator to deal with cloudscraper protection issues in IAFD
'''
# ----------------------------------------------------------------------------------------------------------------------------------
import cloudscraper, fake_useragent, os, platform, re, subprocess, unicodedata
from datetime import datetime
from googletrans import Translator
from unidecode import unidecode
from urlparse import urlparse

scraper = None

# ----------------------------------------------------------------------------------------------------------------------------------
def getFilmInfo(filmPath) :
    ''' Checks video information from file name '''
    FilmInfo = None
    try:
        command = ['ffprobe', '-v', 'fatal', '-show_entries', 'stream=width,height,r_frame_rate,duration', '-of', 'default=noprint_wrappers=1:nokey=1', filmPath, '-sexagesimal']
        ffmpeg = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE )
        out, err = ffmpeg.communicate()
        if err:
            log('UTILS :: FFProbe Issues: %s', err)

        out = out.split('\n')
        filmLength = [float(x.strip()) for x in out[3].split(':')]
        duration = int(filmLength[0] * 60 + filmLength[1])

        FilmInfo = {'width': int(out[0]),
                    'height': int(out[1]),
                    'fps': float(out[2].split('/')[0])/float(out[2].split('/')[1]),
                    'duration': duration}
    except Exception as e:
        # should error if ffmpeg is not installed
        log('UTILS :: FFProbe Error: %s', e)

    return FilmInfo

# -------------------------------------------------------------------------------------------------------------------------------
def getFilmImages(imageType, imageURL, whRatio):
    ''' Only for Scene Agents: get Film images - posters/background art and crop if necessary '''
    pic = imageURL
    picContent = ''
    picInfo = Image.open(BytesIO(HTTP.Request(pic).content))
    width, height = picInfo.size
    dispWidth = '{:,d}'.format(width)       # thousands separator
    dispHeight = '{:,d}'.format(height)     # thousands separator

    log('UTILS :: {0} Found: Width ({1}) x Height ({2}); URL: {3}'.format(imageType, dispWidth, dispHeight, imageURL))

    maxHeight = float(width * whRatio)      # Maximum allowable height

    cropHeight = float(maxHeight if maxHeight <= height else height)
    cropWidth = float(cropHeight / whRatio)

    DxHeight = 0.0 if cropHeight == height else (abs(cropHeight - height) / height) * 100.0
    DxWidth = 0.0 if cropWidth == width else (abs(cropWidth - width) / width) * 100.0

    cropRequired = True if DxWidth >= 10 or DxHeight >=10 else False
    cropWidth = int(cropWidth)
    cropHeight = int(cropHeight)
    desiredWidth = '{0:,d}'.format(cropWidth)     # thousands separator
    desiredHeight = '{0:,d}'.format(cropHeight)   # thousands separator
    DxWidth = '{0:.2f}'.format(DxWidth)    # percent format
    DxHeight = '{0:.2f}'.format(DxHeight)  # percent format
    log('UTILS :: Crop {0} {1}: Actual (w{2} x h{3}), Desired (w{4} x h{5}), % Dx = w[{6}%] x h[{7}%]'.format("Required:" if cropRequired else "Not Required:", imageType, dispWidth, dispHeight, desiredWidth, desiredHeight, DxWidth, DxHeight))
    if cropRequired:
        try:
            log('UTILS :: Using Thumbor to crop image to: {0} x {1}'.format(desiredWidth, desiredHeight))
            pic = THUMBOR.format(cropWidth, cropHeight, imageURL)
            picContent = HTTP.Request(pic).content
        except Exception as e:
            log('UTILS :: Error Thumbor Failed to Crop Image to: {0} x {1}: {2} - {3}'.format(desiredWidth, desiredHeight, pic, e))
            try:
                if os.name == 'nt':
                    log('UTILS :: Using Script to crop image to: {0} x {1}'.format(desiredWidth, desiredHeight))
                    envVar = os.environ
                    TempFolder = envVar['TEMP']
                    LocalAppDataFolder = envVar['LOCALAPPDATA']
                    pic = os.path.join(TempFolder, imageURL.split("/")[-1])
                    cmd = CROPPER.format(LocalAppDataFolder, imageURL, pic, cropWidth, cropHeight)
                    subprocess.call(cmd)
                    picContent = load_file(pic)
            except Exception as e:
                log('UTILS :: Error Script Failed to Crop Image to: {0} x {1}'.format(desiredWidth, desiredHeight))
    else:
        picContent = HTTP.Request(pic).content

    return pic, picContent

# -------------------------------------------------------------------------------------------------------------------------------
def getHTTPRequest(url, **kwargs):
    headers = kwargs.pop('headers', {})
    cookies = kwargs.pop('cookies', {})
    timeout = kwargs.pop('timeout', 20)
    proxies = {}

    global scraper

    if 'User-Agent' not in headers:
        headers['User-Agent'] = (fake_useragent.UserAgent(fallback=HTTP.Headers['User-agent'])).random

    # clean up url....
    ClearURL = url
    if url.startswith('http'):
        url = urlparse(url)
        path = url.path
        path = path.replace('//', '/')

        ClearURL = '%s://%s%s' % (url.scheme, url.netloc, path)
        if url.query:
            ClearURL += '?%s' % url.query

    url = ClearURL

    HTTPRequest = None
    try:
        log('UTILS :: CloudScraper Request         \t%s', url)
        if scraper is None:
            scraper = cloudscraper.CloudScraper()
            scraper.headers.update(headers)
            scraper.cookies.update(cookies)
        HTTPRequest = scraper.request('GET', url, timeout=timeout, proxies=proxies)
        log('UTILS :: CloudScraper Response        \tOK? <%s> - Status <%s>', HTTPRequest.ok, HTTPRequest.status_code)

    except Exception as e:
        msg = ('CloudScraper Failed: %s', e)
        raise Exception(msg)

    if HTTPRequest:
        HTTPRequest.encoding = 'UTF-8'

    return HTTPRequest

# ----------------------------------------------------------------------------------------------------------------------------------
def logHeaders(header, media, lang):
    ''' list header of search and update functions '''
    log(LOG_BIGLINE)
    log('%s:: Version                      : v.%s', header, VERSION_NO)
    log('%s:: Python                       : %s %s', header, platform.python_version(), platform.python_build())
    log('%s:: Platform                     : %s - %s %s', header, platform.machine(), platform.system(), platform.release())
    log('%s:: Preferences:', header)
    log('%s::  > Cast Legend Before Summary: %s', header, PREFIXLEGEND)
    log('%s::  > Collection Gathering', header)
    log('%s::      > Cast                  : %s', header, COLCAST)
    log('%s::      > Director(s)           : %s', header, COLDIRECTOR)
    log('%s::      > Studio                : %s', header, COLSTUDIO)
    log('%s::      > Film Title            : %s', header, COLTITLE)
    log('%s::      > Genres                : %s', header, COLGENRE)
    log('%s::  > Match Site Duration       : %s', header, MATCHSITEDURATION)
    log('%s::  > Duration Difference       : %s Minutes', header, DURATIONDX)
    log('%s::  > Language Detection        : %s', header, DETECT)
    log('%s::  > Library:Site Language     : (%s:%s)', header, lang, SITE_LANGUAGE)
    log('%s::  > Network Request Delay     : %s Seconds', header, DELAY)
    
    log('%s:: Media Title                  : %s', header, media.title)
    log('%s:: File Path                    : %s', header, media.items[0].parts[0].file)
    log(LOG_BIGLINE)

# ----------------------------------------------------------------------------------------------------------------------------------
def matchFilename(filmPath):
    ''' Check filename on disk corresponds to regex preference format '''
    filmVars = {}

    # file matching pattern
    filename = os.path.basename(filmPath)
    REGEX = '^\((?P<Studio0>.+)\) - (?P<Title0>.+) \((?P<Year0>\d{4})\)|^\((?P<Studio1>.+)\) - (?P<Title1>.+)'
    pattern = re.compile(REGEX)
    matched = pattern.search(filename)
    if not matched:
        raise Exception('<File Name [{0}] not in the expected format: (Studio) - Title (Year)>'.format(filename))

    groups = matched.groupdict()
    filmVars['Format'] = '(Studio) - Title' if groups['Year0'] is None else '(Studio) - Title (Year)'
    studio = groups['Studio1'] if groups['Year0'] is None else groups['Studio0']
    filmVars['Studio'] = studio.split(';')[0].strip() if ';' in studio else studio
    filmVars['IAFDStudio'] = studio.split(';')[1].strip() if ';' in studio else ''
    filmVars['CompareStudio'] = NormaliseComparisonString(filmVars['Studio'])
    filmVars['CompareIAFDStudio'] = NormaliseComparisonString(filmVars['IAFDStudio']) if filmVars['IAFDStudio'] else ''

    filmVars['Title'] =  groups['Title1'] if groups['Year0'] is None else groups['Title0']
    filmVars['ShortTitle'] = filmVars['Title']
    filmVars['CompareTitle'] = [SortAlphaChars(NormaliseComparisonString(filmVars['ShortTitle']))]
    # if film starts with a determinate, strip the detrminate and add the title to the comparison list
    pattern = ur'^(The |An |A )'
    matched = re.search(pattern, filmVars['ShortTitle'], re.IGNORECASE)  # match against whole string
    if matched:
        filmVars['CompareTitle'].append(SortAlphaChars(NormaliseComparisonString(re.sub(pattern, '', filmVars['ShortTitle'], flags=re.IGNORECASE))))
    filmVars['SearchTitle'] = filmVars['Title']

    filmVars['IAFDTitle'] =  makeASCII(filmVars['Title'])
    filmVars['IAFDCompareTitle'] = filmVars['CompareTitle']
    filmVars['IAFDSearchTitle'] = filmVars['IAFDTitle']

    filmVars['Year'] = groups['Year0'] if groups['Year0'] is not None else ''
    # default to 31 Dec of Filename year if Year provided in filename and is not 1900
    filmVars['CompareDate'] = datetime(int(filmVars['Year']), 12, 31).strftime(DATEFORMAT) if filmVars['Year'] else ''

    # film duration +/- 10%
    filmInfo = getFilmInfo(filmPath)
    filmVars['Duration'] = str(filmInfo['duration']) if filmInfo != None else ''

    filmVars['Compilation'] = 'No'
    filmVars['FoundOnIAFD'] = 'No'

    # For this title: (Raging Stallion Studios) - Hardcore Fetish Series - Pissing 1 - Piss Off (2009)
    #    Collections: [Hardcore Fetish Series, Pissing]
    #         Series: [Pissing 1]
    #    Short Title: Piss Off
    collections = []
    if COLSTUDIO:
        collections.append(filmVars['Studio'])                # All films have their Studio Name as a collection
    series = []
    splitFilmTitle = filmVars['Title'].split(' - ')
    splitFilmTitle = [x.strip() for x in splitFilmTitle]
    splitCount = len(splitFilmTitle) - 1
    for index, partTitle in enumerate(splitFilmTitle):
        pattern = r'(?<![-.])\b[0-9]+\b(?!\.[0-9])$'           # series matching = whole separate number at end of string
        matchedSeries = re.subn(pattern, '', partTitle)
        if matchedSeries[1]:
            if COLTITLE:
                collections.insert(0, matchedSeries[0].strip()) # e.g. Pissing
            series.insert(0, partTitle)                         # e.g. Pissing 1
            if index < splitCount:                              # only blank out series info in title if not last split
                splitFilmTitle[index] = ''
        else:
            if index < splitCount:                              # only add to collection if not last part of title e.g. Hardcore Fetish Series
                splitFilmTitle[index] = ''
                if COLTITLE:
                    collections.insert(0, partTitle)

    filmVars['Collection'] = collections
    filmVars['Series'] = series
    filmVars['Title'] = filmVars['Title'] if '- ' not in filmVars['Title'] else re.sub(ur' - |- ', ': ', filmVars['Title'])                 # put colons back in as they can't be used in the filename
    filmVars['ShortTitle'] = re.sub(ur'\W+$', '', ' '.join(splitFilmTitle).strip()) # strip punctions at end of string
    if filmVars['ShortTitle'] not in filmVars['CompareTitle']:
        filmVars['CompareTitle'].append(SortAlphaChars(NormaliseComparisonString(filmVars['ShortTitle'])))
    filmVars['SearchTitle'] = filmVars['ShortTitle']
    
    # prepare IAFD Title and Search String
    filmVars['IAFDTitle'] = makeASCII(filmVars['ShortTitle']).replace(' - ', ': ')       # iafd needs colons in place to search correctly, removed all unicode
    filmVars['IAFDTitle'] = filmVars['IAFDTitle'].replace(' &', ' and')                  # iafd does not use &
    filmVars['IAFDTitle'] = filmVars['IAFDTitle'].replace('!', '')                       # remove !

    # split and take up to first occurence of character
    splitChars = ['-', '[', '(', ur'\u2013', ur'\u2014']
    pattern = ur'[{0}]'.format(''.join(splitChars))
    matched = re.search(pattern, filmVars['IAFDTitle'])  # match against whole string
    if matched:
        filmVars['IAFDTitle'] = filmVars['IAFDTitle'][:matched.start()]

    # strip standalone '1's'
    pattern = ur'(?<!\d)1(?!\d)'
    filmVars['IAFDTitle'] = re.sub(pattern, '', filmVars['IAFDTitle'])

    # strip definite and indefinite english articles
    pattern = ur'^(The|An|A) '
    matched = re.search(pattern, filmVars['IAFDTitle'], re.IGNORECASE)  # match against whole string
    if matched:
        filmVars['IAFDTitle'] = filmVars['IAFDTitle'][matched.end():]
        tempCompare = SortAlphaChars(NormaliseComparisonString(filmVars['IAFDTitle']))
        if tempCompare not in filmVars['IAFDCompareTitle']:
            filmVars['IAFDCompareTitle'].append(tempCompare)

    # sort out double encoding: & html code %26 for example is encoded as %2526; on MAC OS '*' sometimes appear in the encoded string, also remove '!'
    filmVars['IAFDSearchTitle'] = String.StripDiacritics(filmVars['IAFDTitle']).strip()
    filmVars['IAFDSearchTitle'] = String.URLEncode(filmVars['IAFDSearchTitle'])
    filmVars['IAFDSearchTitle'] = filmVars['IAFDSearchTitle'].replace('%25', '%').replace('*', '')

    # print out dictionary values / normalise unicode
    log('UTILS :: Film Dictionary Variables:')
    for key in sorted(filmVars.keys()):
        filmVars[key] = list(dict.fromkeys(filmVars[key])) if type(filmVars[key]) is list else filmVars[key]
        log('UTILS :: {0: <29}: {1}'.format(key, filmVars[key]))

    return filmVars

# ----------------------------------------------------------------------------------------------------------------------------------
def matchDuration(siteDuration, FILMDICT, matchDuration=True):
    ''' match file duration against iafd duration: Only works if ffmpeg is installed and duration recorded: Boolean Return '''
    siteDuration = siteDuration.strip()
    if siteDuration and matchDuration == True and FILMDICT['Duration']:
        if ':' in siteDuration:
            # convert hours and minutes to minutes if time is in format hh:mm:ss
            siteDuration = siteDuration.split(':')[:2]
            siteDuration = int(float(siteDuration[0]) * 60 + float(siteDuration[1]))
        else:
            # assume time is in minutes: first convert to float incase there is a decimal point
            siteDuration = int(float(siteDuration))

        fileDuration = int(FILMDICT['Duration'])
        matchDuration = (abs(fileDuration - siteDuration) <= DURATIONDX)

        log('UTILS :: Site Duration                 %s Minutes \tAcceptable Deviation ±%s Minutes', siteDuration, DURATIONDX)
        log('UTILS :: Duration Comparison           [%s]\tSite: "%s" Minutes\tFile: "%s" Minutes', 'Passed' if matchDuration else 'Failed', siteDuration, fileDuration)

        if not matchDuration:
            msg = '<Film Duration not within acceptable deviation of ±%s minutes!>'.format(DURATIONDX)
            raise Exception(msg)
    else:
        log('UTILS :: Site Duration                 %s', 'Skipped - Duration Not Established')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def matchReleaseDate(siteReleaseDate, FILMDICT):
    ''' match file year against website release date: return formatted site date if no error or default to formated file date '''
    # if a year has being provided - default to 31st December of that year
    siteReleaseDate = datetime.strptime(siteReleaseDate + '1231', '%Y%m%d') if len(siteReleaseDate) == 4 else datetime.strptime(siteReleaseDate, DATEFORMAT)

    # there can not be a difference more than 366 days between FileName Date and siteReleaseDate
    if FILMDICT['CompareDate']:
        fileReleaseDate = datetime.strptime(FILMDICT['CompareDate'], DATEFORMAT)
        dx = abs((fileReleaseDate - siteReleaseDate).days)

        log('UTILS :: Release Date                  %s', siteReleaseDate)
        log('UTILS :: Release Date Comparison       [%s]\t %s days\tSite: "%s"\tFile: "%s"', 'Failed' if dx > 366 else 'Pass', dx, siteReleaseDate.strftime('%Y %m %d'), fileReleaseDate.strftime('%Y %m %d'))

        if dx > 366:
            raise Exception('<Release Date Match Failure!>')

    # reset comparison date to above scrapping result
    FILMDICT['CompareDate'] = siteReleaseDate.strftime(DATEFORMAT)
    FILMDICT['Year'] = siteReleaseDate.year

    return siteReleaseDate

# ----------------------------------------------------------------------------------------------------------------------------------
def matchStudio(siteStudio, FILMDICT, useAgent=True):
    ''' match file studio name against website studio/iafd name: Boolean Return '''
    compareSiteStudio = NormaliseComparisonString(siteStudio)
    dtStudio = FILMDICT['Studio'] if useAgent else FILMDICT['IAFDStudio']
    dtCompareStudio = FILMDICT['CompareStudio'] if useAgent else FILMDICT['CompareIAFDStudio']

    testStudio = 'Full Match' if compareSiteStudio == dtCompareStudio else 'Partial Match' if compareSiteStudio in dtCompareStudio or dtCompareStudio in compareSiteStudio else 'Failed Match'

    log('UTILS :: Site Studio                   %s', siteStudio)
    log('UTILS :: Studio Comparison             [%s]\tSite: "%s"\tFile: "%s"', testStudio, siteStudio, dtStudio)

    if testStudio == 'Failed Match':
        raise Exception('<Studio Match Failure!>')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def matchTitle(siteTitle, FILMDICT):
    ''' match file title against website/iafd title: Boolean Return '''
    compareSiteTitle = SortAlphaChars(NormaliseComparisonString(siteTitle))
    testSite = 'Passed' if compareSiteTitle in FILMDICT['CompareTitle'] else 'Passed (IAFD)' if compareSiteTitle in FILMDICT['IAFDCompareTitle'] else 'Failed'

    log('UTILS :: Site Title                    %s', siteTitle)
    log('UTILS :: Title Comparison              [%s]\tSite: "%s"\tFile: Full/Short Title - "%s" / "%s"', testSite, siteTitle, FILMDICT['Title'], FILMDICT['ShortTitle'])

    if testSite == 'Failed':
        raise Exception('<Title Match Failure!>')

    return True

# ----------------------------------------------------------------------------------------------------------------------------------
def NormaliseComparisonString(myString):
    ''' Normalise string for, strip uneeded characters for comparison of web site values to file name regex group values '''
    # Check if string has roman numerals as in a series; note the letter I will be converted
    myString = '{0} '.format(myString)  # append space at end of string to match last characters 
    pattern = '\s(?=[MDCLXVI])M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3})$'
    matches = re.findall(pattern, myString, re.IGNORECASE)  # match against string
    if matches:
        RomanValues = {'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000}
        for count, match in enumerate(matches):
            myRoman = ''.join(match).upper()
            log('UTILS :: Found Roman Numeral: {0}.. {1} len[{2}]'.format(count, myRoman, len(myRoman)))
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

    # replace ampersand with 'and'
    myString = myString.replace('&', 'and')

    # replace ": " with " - "
    myString = myString.replace(': ', ' - ')

    # change string to ASCII
    myString = makeASCII(myString)

    # strip domain suffixes, vol., volume from string, standalone '1's'
    pattern = ur'[.]([a-z]{2,3}|co[.][a-z]{2})|Vol[.]|Vols[.]|\bVolume\b|\bVolumes\b|(?<!\d)1(?!\d)|\bPart\b|[^A-Za-z0-9]+'
    myString = re.sub(pattern, '', myString, flags=re.IGNORECASE)

    return myString

# ----------------------------------------------------------------------------------------------------------------------------------
def makeASCII(myString):
    # standardise single quotes
    singleQuotes = ['`', '‘', '’']
    pattern = ur'[{0}]'.format(''.join(singleQuotes))
    myString = re.sub(pattern, "'", myString)

    # standardise double quotes
    doubleQuotes = ['“', '”']
    pattern = ur'[{0}]'.format(''.join(doubleQuotes))
    myString = re.sub(pattern, '"', myString)

    # convert letters to their ascii equivalents
    try:
        nfkd_form = unicodedata.normalize('NFKD', myString)
        myString = nfkd_form.encode('ASCII', 'ignore')
    except:
        pass
    
    return myString
# ----------------------------------------------------------------------------------------------------------------------------------
def SortAlphaChars(myString):
    numbers = re.sub('[^0-9]','', myString)
    letters = re.sub('[0-9]','', myString)
    myString = '{0}{1}'.format(numbers, ''.join(sorted(letters)))

    return myString
# ----------------------------------------------------------------------------------------------------------------------------------
def TranslateString(myString, language):
    ''' Translate string into Library language '''
    myString = myString.strip()
    if language == 'xn' or language == 'xx':    # no language or language unknown
        log('UTILS :: Library Language: [%s], Run Translation: [False]', 'No Language' if language == 'xn' else 'Unknown')
    elif myString:
        translator = Translator(service_urls=['translate.google.com',    'translate.google.ca',    'translate.google.co.uk',
                                              'translate.google.com.au', 'translate.google.co.za', 'translate.google.br.com',
                                              'translate.google.pt',     'translate.google.es',    'translate.google.com.mx',
                                              'translate.google.it',     'translate.google.nl',    'translate.google.be',
                                              'translate.google.de',     'translate.google.ch',    'translate.google.at',
                                              'translate.google.ru',     'translate.google.pl',    'translate.google.bg',
                                              'translate.google.com.eg', 'translate.google.co.il', 'translate.google.co.jp',
                                              'translate.google.co.kr',  'translate.google.fr',    'translate.google.dk'])
        runTranslation = (language != SITE_LANGUAGE)
        log('UTILS :: [Library:Site] Language: [%s:%s], Run Translation: [%s]', language, SITE_LANGUAGE, runTranslation)
        if DETECT:
            detectString = re.findall(ur'.*?[.!?]', myString)[:4]   # take first 4 sentences of string to detect language
            detectString = ''.join(detectString)
            log('UTILS :: Detect Site Language [%s] using this text: %s', DETECT, detectString)
            try:
                detected = translator.detect(detectString)
                runTranslation = (language != detected.lang)
                log('UTILS :: Detected Language: [%s] Run Translation: [%s]', detected.lang, runTranslation)
            except Exception as e:
                log('UTILS :: Error Detecting Text Language: %s', e)

        try:
            myString = translator.translate(myString, dest=language).text if runTranslation else myString
            log('UTILS :: Translated [%s] Summary Found: %s', runTranslation, myString)
        except Exception as e:
            log('UTILS :: Error Translating Text: %s', e)

    return myString if myString else ' '     # return single space to initialise metadata summary field