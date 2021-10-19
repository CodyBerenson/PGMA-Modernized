#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Module that contains the translators.

Translators:
    GoogleTranslator

Attributes:
    _JSON_REPLACE_PATTERN (regexp): Regular expression to replace
        contiguous commas.

"""

from __future__ import unicode_literals

import re
import sys
import copy
import json
import random
import os.path
import urllib2
import logging

from time import sleep

try:
    from twodict import TwoWayOrderedDict
except ImportError as error:
    print error
    sys.exit(1)

from .tk_generator import get_tk
from .cache import Cache
from .utils import (
    display_unicode_item,
    get_absolute_path,
    load_from_file,
    quote_unicode,
    make_request,
    parse_reply
)

_JSON_REPLACE_PATTERN = re.compile(r",(?=,)|\[,+")


class GoogleTranslator(object):

    """Uses the Google translate API to provide different functionalities.

    GoogleTranslator currently provides four different functionalities.

        * word translation
        * source language detection
        * romanization
        * typo detection

    Examples:
        Use GoogleTranslator to translate multiple words::

            >>> from google_translate import GoogleTranslator

            >>> translator = GoogleTranslator()
            >>> translator.translate(["dog", "cat"], "french")

        Use GoogleTranslator to get additional translations in json format::

            >>> from google_translate import GoogleTranslator

            >>> translator = GoogleTranslator()
            >>> translator.translate("dog", "greek", additional=True, output="json")

        Use GoogleTranslator to detect the source language of multiple words::

            >>> from google_translate import GoogleTranslator

            >>> translator = GoogleTranslator()
            >>> translator.detect(["hello", "bonjour"])

        Use GoogleTranslator to check multiple words for typos::

            >>> from google_translate import GoogleTranslator

            >>> translator = GoogleTranslator()
            >>> translator.word_exists(["hello", "computor"], "english")

    Attributes:
        LANGUAGES_DB (string): Absolute path to the languages file.

        WAIT_MIN (float): Minimum time to wait when 'random_wait' is enabled.

        WAIT_MAX (float): Maximum time to wait when 'random_wait' is enabled.

        MAX_INPUT_SIZE (int): Maximum length of the word to process. Currently
            only GET requests are supported which limits the maximum word size.

        MAX_CACHE_SIZE (int): The number of items that the cache can store.

        CACHE_VALID_PERIOD (float): Time period in seconds for which the cache
            items are valid.

        DEFAULT_USERAGENT (string): Default user-agent to use when there is no
            'User-Agent' header in the _user_specific_headers and a ua_selector
            is not defined.

        DOMAIN_NAME (string): Domain name of Google translate. Note that
            different top level domains return different data.

        REQUEST_URL (string): Google translate API url template.

    Args:
        proxy_selector (ProxySelector): Object used to pick a proxy.

        ua_selector (UserAgentSelector): Object used to pick a user-agent.

        simulate (boolean): When True no real requests will be sent.

        https (boolean): Enable-disable HTTPS.

        timeout (float): Socket timeout in seconds.

        retries (int): Maximum attempts number before giving up.

        wait_time (float): Time in seconds to wait between requests.

        random_wait (boolean): When True GoogleTranslator will wait a random
            amount of seconds instead of using the wait_time.

        encoding (string): Encoding to use during data encode-decode.

    """

    LANGUAGES_DB = os.path.join(get_absolute_path(__file__), "data", "languages")

    WAIT_MIN = 1.0
    WAIT_MAX = 20.0
    MAX_INPUT_SIZE = 1980

    MAX_CACHE_SIZE = 500
    CACHE_VALID_PERIOD = 604800.0  # one week

    DEFAULT_USERAGENT = "Mozilla/5.0"

    DOMAIN_NAME = "translate.google.ru"

    REQUEST_URL = "{prot}://{host}/translate_a/single?{params}"

    def __init__(self, proxy_selector=None, ua_selector=None, simulate=False, https=True,
                 timeout=10.0, retries=5, wait_time=1.0, random_wait=False, encoding="UTF-8"):
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        # Parse args
        self._https = https
        self._timeout = timeout
        self._retries = retries
        self._encoding = encoding
        self._simulate = simulate
        self._wait_time = wait_time
        self._random_wait = random_wait
        self._ua_selector = ua_selector
        self._proxy_selector = proxy_selector

        self.cache = Cache(self.MAX_CACHE_SIZE, self.CACHE_VALID_PERIOD)

        # Set up default headers
        if https:
            referer = "https://{0}/".format(self.DOMAIN_NAME)
        else:
            referer = "http://{0}/".format(self.DOMAIN_NAME)

        self._default_headers = {
            "Accept": "*/*",
            "Referer": referer,
            "Connection": "close",
            "Host": self.DOMAIN_NAME,
            "Accept-Language": "en-US,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "User-Agent": self.DEFAULT_USERAGENT
        }

        self._user_specific_headers = {}

        # Load languages from file
        self._lang_dict = TwoWayOrderedDict(auto="auto")

        for line in load_from_file(self.LANGUAGES_DB):
            lang, code = line.split(':')
            self._lang_dict[lang.lower()] = code

    def add_header(self, header):
        """Add HTTP header to user specific headers.

        Args:
            header (tuple): Tuple that contains two values the header
                name and the header value (e.g. ('Host', 'test.com')).

        Note:
            User specific headers overwrite the default headers.

        Raises:
            ValueError

        """
        if (not isinstance(header, tuple) or
                len(header) != 2 or
                not isinstance(header[0], basestring) or
                not isinstance(header[1], basestring)):
            raise ValueError(header)

        self._user_specific_headers[header[0]] = header[1]

    def word_exists(self, word, lang="en", output="text"):
        """Check if the given word(s) exist in language.

        Args:
            word (string - list<string>): Word(s) to check.

            lang (string): Language to check. See _validate_language method for
                valid language formats (default: en).

            output (string): Output return type. See _convert_output method
                for a list of valid output types (default: text).

        Returns:
            True if the word exists else False.

        Raises:
            ValueError

        """
        lang = self._validate_language(lang, allow_auto=False)

        return self._do_work(self._word_exists, word, lang, output)

    def romanize(self, word, src_lang="auto", output="text"):
        """Get the romanization of the given word(s).

        Args:
            word (string - list<string>): Word(s) to process.

            src_lang (string): Source language of the given word(s). See
                _validate_language method for valid language formats (default: auto).

            output (string): Output return type. See _convert_output method
                for a list of valid output types (default: text).

        Returns:
            String with the romanized word.

        Raises:
            ValueError

        """
        src_lang = self._validate_language(src_lang)

        return self._do_work(self._romanize, word, src_lang, output)

    def detect(self, word, output="text"):
        """Detect the source language of the given word(s).

        Args:
            word (string - list<string>): Word(s) to process.

            output (string): Output return type. See _convert_output method
                for a list of valid output types (default: text).

        Returns:
            String with the source language name-code.

        Raises:
            ValueError

        """
        return self._do_work(self._detect, word, output)

    def translate(self, word, dst_lang, src_lang="auto", additional=False, output="text"):
        """Translate the given word(s) from src_lang to dst_lang.

        Args:
            word (string - list<string): Word(s) to translate.

            dst_lang (string): Language to translate the given word(s). See
                _validate_language method for valid language formats.

            src_lang (string): Source language of the given word(s) (default: auto).

            additional (boolean): When True translate will return additional translations.

            output (string): Output return type. See _convert_output method
                for a list of valid output types (default: text).

        Returns:
            If additional is True.
                Dictionary with the additional translations.

            If additional is False.
                String with the translated word.

        Raises:
            ValueError

        """
        if not isinstance(additional, bool):
            raise ValueError(additional)

        src_lang = self._validate_language(src_lang)
        dst_lang = self._validate_language(dst_lang, allow_auto=False)

        return self._do_work(self._translate, word, dst_lang, src_lang, additional, output)

    def get_info_dict(self, word, dst_lang, src_lang="auto", output="text"):
        """Returns the information dictionary for the given word.

        For a list with available dictionary keys, see _extract_data method.

        Args:
            word (string - list<string>): Word(s) to process.

            dst_lang (string): Destination language to use. See _validate_language
                method for valid language formats.

            src_lang (string): Source language to use (default: auto).

            output (string): Output return type. See _convert_output method for
                a list of valid output types (default: text).

        Raises:
            ValueError

        """
        src_lang = self._validate_language(src_lang)
        dst_lang = self._validate_language(dst_lang, allow_auto=False)

        return self._do_work(self._get_info, word, dst_lang, src_lang, output)

    def _do_work(self, func, *args):
        """Run the given function.

        Run the given function with args and return the results back to the
        caller after converting them to the appropriate format (used to avoid
        code duplicates). Func is the function to run (_translate, _detect,
        _word_exists, _romanize) and args are the arguments of each function.
        Note that args[0] is the word(s) and args[-1] is the output type.

        """
        if isinstance(args[0], list):
            results_list = []

            for word in args[0]:
                self._validate_word(word)
                results_list.append(func(word, *args[1:-1]))

                if word != args[0][-1]:
                    self._wait()

            return self._convert_output(args[0], results_list, args[-1])

        self._validate_word(args[0])
        return self._convert_output(args[0], func(*args[:-1]), args[-1])

    def _convert_output(self, word, output, output_type):
        """Convert the output to the appropriate format.

        Args:
            word (string - list<string>): Word(s) given by the user.

            output (*): Return value from the _do_work 'func' arg.

            output_type (string): Type to return. Valid types are 'text',
                'dict', 'json'.

        """
        if output_type not in ["text", "dict", "json"]:
            raise ValueError(output_type)

        if output_type == "text":
            return output

        if isinstance(word, list):
            temp_dict = dict(zip(word, output))
        else:
            temp_dict = {word: output}

        if output_type == "dict":
            return temp_dict

        return json.dumps(temp_dict, indent=4, ensure_ascii=False)

    def _validate_word(self, word):
        """Validate the given word and raise ValueError if not all conditions are met."""
        if not isinstance(word, basestring):
            self.logger.critical("Invalid word: %r", word)
            raise ValueError(word)

        quoted_text_length = len(quote_unicode(word, self._encoding))

        self.logger.debug("Max input size: (%s)", self.MAX_INPUT_SIZE)
        self.logger.debug("Unquoted text size: (%s)", len(word))
        self.logger.debug("Quoted text size: (%s)", quoted_text_length)

        if quoted_text_length >= self.MAX_INPUT_SIZE:
            self.logger.critical("Input size over limit: %r", word)
            raise ValueError("Input size exceeds the maximum value")

    def _validate_language(self, language, allow_auto=True):
        """Validate the given language.

        If the given language is not in the LANGUAGES_DB a ValueError will be
        raised. If the given language is in the long format (e.g. "english") it
        will return the corresponding language code.

        Args:
            language (string): Language to check. The language can be either in
                the "en" format or "english" format (case insensitive).

            allow_auto (boolean): When False no 'auto' language will be allowed.

        Returns:
            The language code of the given language.

        Raises:
            ValueError

        """
        if not isinstance(language, basestring):
            self.logger.critical("Invalid language: %r", language)
            raise ValueError(language)

        if '-' in language:
            # Cases like ZH-CN -> zh-CN
            language = language[:2].lower() + language[2:].upper()
        else:
            language = language.lower()

        if language == "auto" and not allow_auto:
            self.logger.critical("'auto' language is not allowed")
            raise ValueError(language)

        if not language in self._lang_dict:
            self.logger.critical("Could not locate language: %r", language)
            raise ValueError(language)

        if language in self._lang_dict.keys():
            language = self._lang_dict[language]

        return language

    def _word_exists(self, word, src_lang):
        """Checks if the given word is a valid word in src_lang."""
        self.logger.info("Searching for word: %r", word)

        # Get a destination language different than source
        dst_lang = src_lang
        for lang_code in self._lang_dict.values():
            if lang_code != "auto" and lang_code != src_lang:
                dst_lang = lang_code
                break

        self.logger.debug("src_lang: %r dst_lang: %r", src_lang, dst_lang)
        data = self._get_info(word, dst_lang, src_lang)

        if data is not None:
            if data["original_text"] == data["translation"]:
                return False

            return not data["has_typo"]

        return None

    def _romanize(self, word, src_lang):
        """Romanize the given word."""
        self.logger.info("Romanizing word: %r", word)

        self.logger.debug("src_lang: %r", src_lang)
        data = self._get_info(word, "en", src_lang)

        if data is not None:
            if not data["has_typo"]:
                return data["romanization"]

        return None

    def _detect(self, word):
        """Detect source language of the given word."""
        self.logger.info("Detecting language for word: %r", word)

        data = self._get_info(word, "en", "auto")

        if data is not None:
            try:
                return self._lang_dict[data["src_lang"]]
            except KeyError:
                return data["src_lang"]

        return None

    def _translate(self, word, dst_lang, src_lang, additional):
        """Translate the given word from src_lang to dst_lang."""
        self.logger.info("Translating word: %r", word)

        self.logger.debug("src_lang: %r dst_lang: %r", src_lang, dst_lang)

        if dst_lang == src_lang:
            return word

        data = self._get_info(word, dst_lang, src_lang)

        if data is not None:
            if not data["has_typo"]:
                if additional:
                    return data["extra"]

                return data["translation"]

        return None

    def _get_info(self, word, dst_lang, src_lang):
        """Get the info dictionary for the given word.

        Returns:
            Info dictionary, see _extract_data method for a list with valid keys.

            None if an error occurs.

        """
        cache_key = word + dst_lang + src_lang
        info_dict = self.cache.get(cache_key)

        if info_dict is not None:
            return copy.deepcopy(info_dict)

        reply = self._try_make_request(self._build_request(word, dst_lang, src_lang))

        if reply is not None:
            self.logger.info("Parsing reply")

            data = parse_reply(reply, self._encoding)
            self.logger.debug("Raw data: %s\n", data)

            json_data = self._string_to_json(data)
            self.logger.debug("JSON data: %s\n", display_unicode_item(json_data))

            info_dict = self._extract_data(json_data)
            self.logger.debug("Extracted data: %s\n", display_unicode_item(info_dict))

            self.cache.add(cache_key, info_dict)
            return copy.deepcopy(info_dict)

        return None

    def _build_request(self, word, dst_lang, src_lang):
        """Build and return the request URL based on the given inputs."""
        self.logger.info("Building the request")

        params = [
            ["client", "t"],
            ["sl", src_lang],
            ["tl", dst_lang],
            ["dt", "t"],            # translation
            #["dt", "at"],          # alternative translations
            ["dt", "bd"],           # alternative translations (detailed?)
            #["dt", "ex"],          # examples
            #["dt", "ld"],          # language detection
            #["dt", "md"],          # definitions
            #["dt", "rw"],          # related words
            ["dt", "rm"],           # romanization
            #["dt", "ss"],          # synonyms
            ["dt", "qca"],          # correction (html)
            ["ie", self._encoding],
            ["oe", self._encoding],
            ["tk", get_tk(word)],
            ["q", quote_unicode(word, self._encoding)]
        ]

        if self._https:
            protocol = "https"
        else:
            protocol = "http"

        params_str = ""
        for param in params:
            params_str += "{key}={value}&".format(key=param[0], value=param[1])

        # Strip the last '&'
        params_str = params_str[:-1]

        request_url = self.REQUEST_URL.format(prot=protocol, host=self.DOMAIN_NAME, params=params_str)

        self.logger.debug("Request url: %r", request_url)
        self.logger.debug("URL size: (%s)", len(request_url))

        return request_url

    def _try_make_request(self, request_url):
        """Try to make the request and return the reply or None."""
        current_attempt = 1

        while current_attempt <= self._retries:
            self.logger.info("Attempt no. %s out of %s", current_attempt, self._retries)

            proxy = self._get_proxy()

            try:
                return make_request(request_url, self._get_headers(), proxy, self._timeout, self._simulate)
            except (urllib2.HTTPError, urllib2.URLError, IOError) as error:
                self.logger.error("Error %s", error)

                if proxy is not None and self._proxy_selector is not None:
                    self._proxy_selector.remove_proxy(proxy)

            if current_attempt < self._retries:
                self._wait()

            current_attempt += 1

        self.logger.warning("Maximum attempts reached")

        return None

    def _wait(self):
        """Wait for a period of time."""
        wait_time = self._wait_time

        if self._random_wait:
            wait_time = random.uniform(self.WAIT_MIN, self.WAIT_MAX)

        self.logger.debug("Sleep time (seconds): (%.1f)", wait_time)
        sleep(wait_time)

    def _get_proxy(self):
        """Return proxy using the proxy selector."""
        if self._proxy_selector is not None:
            return self._proxy_selector.get_proxy()

        return None

    def _get_headers(self):
        """Return the http headers."""
        headers = dict(self._default_headers)

        if not self._ua_selector is None:
            user_agent = self._ua_selector.get_useragent()

            if user_agent is not None:
                headers["User-Agent"] = user_agent

        # User specific headers overwrite the default ones and the ua selector
        for header in self._user_specific_headers:
            headers[header] = self._user_specific_headers[header]

        return headers.items()

    def _extract_data(self, json_list):
        """Extracts and filters the data from the json_list.

        Returns:
            Python dictionary.

        """
        EXTRA_KEYS = {1: "nouns", 2: "verbs", 3: "adjectives", 4: "adverbs", 5: "prepositions"}

        data_dict = {
            "original_text": "",
            "romanization": "",
            "translation": "",
            "has_typo": False,
            "src_lang": "",
            "extra": {},
            "match": 1.0
        }

        if not isinstance(json_list, list):
            return data_dict

        # Extract the basic ones
        try:
            data_dict["romanization"] = json_list[0][-1][3]
        except IndexError:
            pass

        try:
            data_dict["src_lang"] = json_list[2]
        except IndexError:
            pass

        try:
            data_dict["match"] = json_list[6]
        except IndexError:
            pass

        try:
            # When that thing is set it contains the word spelled right?!
            data_dict["has_typo"] = True if json_list[7] else False
        except IndexError:
            pass

        # Extract translation & original text
        try:
            translation = []
            original_text = []

            translation_list = json_list[0]

            # Exclude the romanization entry
            if len(translation_list) > 1:
                translation_list = json_list[0][:-1]

            for item in translation_list:
                if isinstance(item[4], int):
                    translation.append(item[0])
                    original_text.append(item[1])

            data_dict["translation"] = ''.join(translation)
            data_dict["original_text"] = ''.join(original_text)
        except IndexError:
            pass

        # Extract extra translations
        try:
            if json_list[1] is not None:
                for item in json_list[1]:
                    item_type = item[-1]

                    if item_type in EXTRA_KEYS:
                        dest_key = EXTRA_KEYS[item_type]
                    else:
                        continue

                    temp_dict = {}
                    for extra_trans in item[2]:
                        temp_dict[extra_trans[0]] = extra_trans[1]

                    data_dict["extra"][dest_key] = temp_dict
        except IndexError:
            pass

        # Apply filters
        if not data_dict["romanization"] or data_dict["src_lang"] == "en":
            data_dict["romanization"] = data_dict["original_text"]

        return data_dict

    def _string_to_json(self, data_string):
        """Parse Google translate reply string to json list."""
        if not isinstance(data_string, basestring):
            return None

        def replace_func(mobj):
            """Replace the multiple commas in the json reply."""
            if '[' in mobj.group(0):
                return '[' + '"",' * mobj.group(0).count(',')
            return ',""'

        valid_data = _JSON_REPLACE_PATTERN.sub(replace_func, data_string)

        try:
            json_data = json.loads(valid_data)
        except ValueError as error:
            self.logger.error("Error <%s>", error)
            return None

        return json_data
