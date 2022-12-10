#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Contains the google_translate command line options."""

from __future__ import unicode_literals

import locale
import argparse

from .version import __version__
from .utils import display_unicode_item


def parse_options():
    """Parse sys.argv args."""
    usage_text = "%(prog)s [mode] [options] word(s)"
    desc = "Command line utility for google_translate module."

    unicode_type = lambda arg: arg.decode(locale.getpreferredencoding())

    custom_formatter = lambda prog: argparse.RawTextHelpFormatter(prog, max_help_position=40)

    mode_choices = ["translate", "detect", "romanize", "exist", "t", "d", "r", "e"]


    parser = argparse.ArgumentParser(usage=usage_text, description=desc, formatter_class=custom_formatter)

    parser.add_argument("words", nargs='+', type=unicode_type, help="word(s) to process")
    parser.add_argument("--version", action="version", version="%(prog)s {version}".format(version=__version__))

    basic_args = parser.add_argument_group("basic arguments")

    basic_args.add_argument("-d", "--dst-lang", default="en", type=unicode_type, help="specify destination language (default: %(default)s)", metavar="")
    basic_args.add_argument("-s", "--src-lang", default="auto", type=unicode_type, help="specify source language (default: %(default)s)", metavar="")
    basic_args.add_argument("-m", "--mode", default="translate", type=unicode_type, help="specify mode [(t)ranslate, (d)etect, (r)omanize, (e)xist] (default: %(default)s)", metavar="")

    output_args = parser.add_argument_group("output arguments")

    output_args.add_argument("-v", "--verbose", action="count", default=0, help="set verbosity level (-v:INFO, -vv:DEBUG)")
    output_args.add_argument("--no-warnings", action="store_true", help="suppress warning messages")
    output_args.add_argument("-o", "--output", default="text", type=unicode_type, choices=["text", "json", "dict"], help="specify output type [%(choices)s] (default: %(default)s)", metavar="")
    output_args.add_argument("-a", "--additional", action="store_true", help="show additional translations (requires: 'translate' mode)")

    connection_args = parser.add_argument_group("connection arguments")

    connection_args.add_argument("--simulate", action="store_true", help="dont send request")
    connection_args.add_argument("--http", action="store_false", help="use HTTP instead of HTTPS")
    connection_args.add_argument("-r", "--retries", default=5, type=int, choices=range(1, 101), help="specify number of tries before giving up (default: %(default)s)", metavar="[1-100]")
    connection_args.add_argument("-w", "--wait-time", default=1.0, type=float, help="time in seconds to wait between requests (default: %(default)s)", metavar="(0-100)")
    connection_args.add_argument("--rand-wait", action="store_true", help="wait random time between requests")
    connection_args.add_argument("--timeout", default=10.0, type=float, help="specify socket timeout in seconds (default: %(default)s)", metavar="(0-100)")

    proxy_args = parser.add_argument_group("proxy arguments")

    proxy_args.add_argument("--proxy", type=unicode_type, help="specify proxy to use", metavar="ADDRESS:PORT")
    proxy_args.add_argument("--proxy-file", type=unicode_type, help="specify file to load proxies from")
    proxy_args.add_argument("--no-fallback", action="store_true", help="prevent sending request without a proxy")
    proxy_args.add_argument("--random-proxy", action="store_true", help="select proxy randomly")

    useragent_args = parser.add_argument_group("user-agent arguments")

    useragent_args.add_argument("--user-agent", type=unicode_type, help="specify user-agent to use")
    useragent_args.add_argument("--user-agent-file", type=unicode_type, help="specify file to load user-agents from")
    useragent_args.add_argument("--user-agent-http", action="store_true", help="load user agents from the InTeRnEt")
    useragent_args.add_argument("--single-ua", action="store_true", help="keep the same user-agent between requests")

    other_args = parser.add_argument_group("other arguments")

    other_args.add_argument("--encoding", default="UTF-8", type=unicode_type, help="specify encoding to use (default: %(default)s)")
    other_args.add_argument("--header", action="append", help="specify additional HTTP headers", metavar="NAME:VALUE")
    other_args.add_argument("--disable-cache", action="store_true", help="disable cache load-store")

    args = parser.parse_args()

    # Apply extra rules
    if args.additional and args.mode != "translate":
        parser.error("'additional' flag works only with 'translate' mode")

    if args.wait_time <= 0 or args.wait_time >= 100:
        parser.error("'wait-time' out of range")

    if args.timeout <= 0 or args.timeout >= 100:
        parser.error("'timeout' out of range")

    if args.mode not in mode_choices:
        parser.error("invalid mode '%s', please choose from %s" % (args.mode, display_unicode_item(mode_choices)))

    return args


if __name__ == '__main__':
    print parse_options()
