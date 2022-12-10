#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

"""This module creates the TK GET parameter for Google translate.

This is just a code port to python. All credits should go to the original
creators of the code @tehmaestro and @helen5106.

For more info see: https://github.com/Stichoza/google-translate-php/issues/32

Usage:
    Call this python script from the command line.

        $ python tk_generator.py <word>

    Use this module from another python script.

        >>> import tk_generator
        >>> tk_generator.get_tk('dog')

Attributes:
    _ENCODING (string): Default encoding to be used during the string
        encode-decode process.

"""

__all__ = ["get_tk"]

import sys
from datetime import datetime


_ENCODING = "UTF-8"


# Helper functions
def _mb_strlen(string):
    """Get the length of the encoded string."""
    return len(string.decode(_ENCODING))


def _mb_substr(string, start, length):
    """Get substring from the encoded string."""
    return string.decode(_ENCODING)[start: start + length]

##################################################


def _shr32(x, bits):
    if bits <= 0:
        return x

    if bits >= 32:
        return 0

    x_bin = bin(x)[2:]
    x_bin_length = len(x_bin)

    if x_bin_length > 32:
        x_bin = x_bin[x_bin_length - 32: x_bin_length]

    if x_bin_length < 32:
        x_bin = x_bin.zfill(32)

    return int(x_bin[:32 - bits].zfill(32), 2)


def _char_code_at(string, index):
    return ord(_mb_substr(string, index, 1))


#OLD Function
def _generateB():
    start = datetime(1970, 1, 1)
    now = datetime.now()

    diff = now - start

    return int(diff.total_seconds() / 3600)


def _TKK():
    """Replacement for _generateB function."""
    return [406604, 1836941114]


def _RL(a, b):
    for c in range(0, len(b) - 2, 3):
        d = b[c + 2]

        if d >= 'a':
            d = _char_code_at(d, 0) - 87
        else:
            d = int(d)

        if b[c + 1] == '+':
            d = _shr32(a, d)
        else:
            d = a << d

        if b[c] == '+':
            a = a + d & (pow(2, 32) - 1)
        else:
            a = a ^ d

    return a


def _TL(a):
    #b = _generateB()
    tkk = _TKK()
    b = tkk[0]

    d = []

    for f in range(0, _mb_strlen(a)):
        g = _char_code_at(a, f)

        if g < 128:
            d.append(g)
        else:
            if g < 2048:
                d.append(g >> 6 | 192)
            else:
                if ((g & 0xfc00) == 0xd800 and
                        f + 1 < _mb_strlen(a) and
                        (_char_code_at(a, f + 1) & 0xfc00) == 0xdc00):

                    f += 1
                    g = 0x10000 + ((g & 0x3ff) << 10) + (_char_code_at(a, f) & 0x3ff)

                    d.append(g >> 18 | 240)
                    d.append(g >> 12 & 63 | 128)
                else:
                    d.append(g >> 12 | 224)
                    d.append(g >> 6 & 63 | 128)

            d.append(g & 63 | 128)

    a = b

    for e in range(0, len(d)):
        a += d[e]
        a = _RL(a, "+-a^+6")

    a = _RL(a, "+-3^+b+-f")

    a = a ^ tkk[1]

    if a < 0:
        a = (a & (pow(2, 31) - 1)) + pow(2, 31)

    a %= pow(10, 6)

    return "%d.%d" % (a, a ^ b)


def get_tk(word):
    """Returns the tk parameter for the given word."""
    if isinstance(word, unicode):
        word = word.encode(_ENCODING)

    return _TL(word)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: %s <word>" % sys.argv[0]
        sys.exit(1)

    print "%s=%s" % (sys.argv[1], get_tk(sys.argv[1]))
