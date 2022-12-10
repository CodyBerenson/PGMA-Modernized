#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Small library to translate text using Google translate.

Examples:
    Use GoogleTranslator to translate a word::

        >>> from google_translate import GoogleTranslator

        >>> translator = GoogleTranslator()
        >>> translator.translate("hello world", "fr")

    Use GoogleTranslator & ProxySelector to translate multiple words using
    different proxies for each request::

        >>> from google_translate import GoogleTranslator, ProxySelector

        >>> pselector = ProxySelector(proxy_file="proxy_file")
        >>> translator = GoogleTranslator(proxy_selector=pselector)
        >>> translator.translate(["hello", "world"], "fr")

    Use GoogleTranslator with logging support::

        >>> import logging
        >>> logging.basicConfig(level=logging.DEBUG)
        >>> from google_translate import GoogleTranslator

        >>> translator = GoogleTranslator()
        >>> translator.translate("monday", "french")

"""

from __future__ import unicode_literals

__license__ = "Unlicense"

import logging

# Avoid no handler messages
logging.getLogger(__name__).addHandler(logging.NullHandler())


from .translator import GoogleTranslator
from .selectors import ProxySelector, UserAgentSelector
from .options import parse_options
from .version import __version__

__all__ = [
    b"GoogleTranslator",
    b"ProxySelector",
    b"UserAgentSelector",
    b"parse_options",
    b"__version__"
]
