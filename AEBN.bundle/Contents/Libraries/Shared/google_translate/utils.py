#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Contains different utility functions - objects.

Attributes:
    MODULE_LOGGER (logging.Logger): Module level logger.

    PUNCTUATIONS (string): String that contains punctuations used in the
        split_text function.

"""

from __future__ import unicode_literals

import os
import json
import locale
import urllib2
import logging

from gzip import GzipFile
from cStringIO import StringIO

MODULE_LOGGER = logging.getLogger(__name__)


def decode_string(string, encoding=None):
    """Decode string back to unicode.

    Decodes the given string back to unicode. The process ignores
    all the characters that the encoding does not support.

    Args:
        string (string): String to decode.

        encoding (string): Encoding to use during the decode process. If no
            encoding is given then it uses the default system encoding.

    """
    if isinstance(string, unicode):
        return string

    if encoding is None:
        encoding = locale.getpreferredencoding()

    return string.decode(encoding, "ignore")


def load_from_file(filename, ignore_char='#'):
    """Load content from file.

    Returns a list that contains all the lines of the file with the newline
    character removed. It also ignores all the lines starting with the
    ignore_char. If an error occurs it returns an empty list.

    Args:
        filename (string): Absolute path to the file.

        ignore_char (char): Line ignore character (default: #).

    """
    MODULE_LOGGER.debug("Trying to load content from file: %r", filename)

    content = []

    if not isinstance(filename, basestring) or not os.path.exists(filename):
        MODULE_LOGGER.warning("Could not locate file: %r", filename)
        return content

    with open(filename, 'r') as input_file:
        for line in input_file:
            line = line.rstrip()

            if line[0] == ignore_char:
                MODULE_LOGGER.debug("Ignoring line: %r", line)
                continue

            content.append(decode_string(line))

    return content


def ungzip_stream(stream):
    """Returns the ungzipped stream."""
    try:
        gzipped_stream = GzipFile(fileobj=StringIO(stream))
        return gzipped_stream.read()
    except IOError:
        return stream


def make_request(url, headers=None, proxy=None, timeout=10.0, simulate=False):
    """Make a GET request to the given url.

    Args:
        url (string): URL string.

        headers (list): List that contains ('header', 'value') pairs.

        proxy (string): Proxy string in the 'ip:port' format.

        timeout (float): Socket timeout in seconds (default: 10.0).

        simulate (boolean): When True no real requests will be sent (default: False).

    Returns:
        File like object on success else None. Note that when
        it runs in simulate mode it always returns None.

    Raises:
        urllib2.HTTPError, urllib2.URLError, IOError

    """
    reply = None

    MODULE_LOGGER.debug("Headers: %r", headers)
    MODULE_LOGGER.debug("Proxy: %r", proxy)
    MODULE_LOGGER.debug("Socket timeout: (%s)", timeout)

    if simulate:
        MODULE_LOGGER.info("Running in simulate mode no request will be sent")
        return None

    if proxy is None:
        url_opener = urllib2.build_opener()
    else:
        url_opener = urllib2.build_opener(urllib2.ProxyHandler({"http": proxy, "https": proxy}))

    if headers is not None:
        url_opener.addheaders = headers

    try:
        MODULE_LOGGER.info("Sending request")
        reply = url_opener.open(url, timeout=timeout)
    except (urllib2.HTTPError, urllib2.URLError, IOError) as error:
        raise error
    finally:
        url_opener.close()

    return reply


def parse_reply(reply, encoding="UTF-8"):
    """Parse the HTTP reply.

    Args:
        reply (file object): Reply to parse.

        encoding (string): Encoding to use (default: UTF-8).

    Returns:
        String that contains the HTTP reply body.

    Raises:
        AttributeError

    """
    try:
        reply_stream = ungzip_stream(reply.read())
        reply.close()
    except AttributeError as error:
        raise error

    return decode_string(reply_stream, encoding)


def get_absolute_path(filename):
    """Returns the absolute path to the given file."""
    return os.path.dirname(os.path.abspath(filename))


def display_unicode_item(item):
    """Returns the unicode representation of the item."""
    return repr(item).decode("unicode_escape").replace("u'", "'").replace('\n', '\\n')


def write_dict(filename, dictionary):
    """Write python dictionary to file.

    Writes the given dictionary to the file in json format. It also creates
    all the directories as needed. Returns True on success else False.

    Args:
        filename (string): Absolute path to the destination file.

        dictionary (dict): Python dictionary to write.

    Raises:
        AssertionError

    """
    assert isinstance(dictionary, dict)
    assert isinstance(filename, basestring)

    file_path = os.path.dirname(filename)

    if file_path and not os.path.isdir(file_path):
        try:
            os.makedirs(file_path)
        except OSError:
            return False

    try:
        with open(filename, 'w') as json_file:
            # Store the dictionary.items() in order to keep the key types
            json.dump(dictionary.items(), json_file)
    except IOError:
        return False

    return True


def get_dict(filename):
    """Load python dictionary from file.

    It tries to load the json dictionary stored in the given file.
    Returns python dictionary on success else None.

    Args:
        filename (string): Absolute path to the file.

    Raises:
        AssertionError

    """
    assert isinstance(filename, basestring)

    if os.path.exists(filename):
        try:
            with open(filename, 'r') as json_file:
                return dict(json.load(json_file))
        except (IOError, ValueError):
            pass

    return None


def quote_unicode(text, encoding="utf-8"):
    """urllib2.quote wrapper to handle unicode items."""
    if isinstance(text, unicode):
        text = text.encode(encoding)

    return urllib2.quote(text).decode(encoding)


def unquote_unicode(text, encoding="utf-8"):
    """urllib2.unquote wrapper to handle unicode items."""
    if isinstance(text, unicode):
        text = text.encode(encoding)

    return urllib2.unquote(text).decode(encoding)


PUNCTUATIONS = ".!?:,;)]} \n"


def split_text(text, max_chunk, punctuations=PUNCTUATIONS):
    """Generator to split text into chunks.

    Tries to split the given text into sentences (using the given punctuations)
    where each sentence length does not exceed the max_chunk size.

    Args:
        text (unicode): Text to split.

        max_chunk (int): The maximum size of each chunk. Must be a positive
            integer.

        punctuations (unicode - list<unicode>): Punctuations to use during the split process.
            (default: utils.PUNCTUATIONS)

    Yields:
        Splitted text.

    Raises:
        Exception, AssertionError

    """
    assert isinstance(text, unicode)
    assert max_chunk > 0

    start = 0

    while start < len(text):
        end = start + max_chunk

        if len(text[start: end]) >= max_chunk:
            for punctuation in punctuations:
                pindex = text.rfind(punctuation, start, end)

                if pindex != -1:
                    break
            else:
                raise Exception("Could not split text")

            end = pindex + len(punctuation)

        yield text[start: end]

        start = end
