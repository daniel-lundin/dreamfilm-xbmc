#
# Unpacker for Dean Edward's p.a.c.k.e.r, a part of javascript beautifier
# by Einar Lielmanis <einar@jsbeautifier.org>
#
#     written by Stefano Sanfilippo <a.little.coder@gmail.com>
#
# usage:
#
# if detect(some_string):
#     unpacked = unpack(some_string)
#

"""Unpacker for Dean Edward's p.a.c.k.e.r"""

import re
import string
class UnpackingError(Exception):
    """Badly packed source or general error. Argument is a
    meaningful description."""
    pass


PRIORITY = 1

def detect(source):
    """Detects whether `source` is P.A.C.K.E.R. coded."""
    return source.replace(' ', '').startswith('eval(function(p,a,c,k,e,')

def unpack(source):
    """Unpacks P.A.C.K.E.R. packed js code."""
    payload, symtab, radix, count = _filterargs(source)

    if count != len(symtab):
        raise UnpackingError('Malformed p.a.c.k.e.r. symtab.')

    try:
        unbase = Unbaser(radix)
    except TypeError, e:
        raise UnpackingError('Unknown p.a.c.k.e.r. encoding.')

    def lookup(match):
        """Look up symbols in the synthetic symtab."""
        word  = match.group(0)
        return symtab[unbase(word)] or word

    source = re.sub(r'\b\w+\b', lookup, payload)
    return _replacestrings(source)

def _filterargs(source):
    """Juice from a source file the four args needed by decoder."""
    juicers = [ (r"}\('(.*)', *(\d+), *(\d+), *'(.*)'\.split\('\|'\), *(\d+), *(.*)\)\)"),
                (r"}\('(.*)', *(\d+), *(\d+), *'(.*)'\.split\('\|'\)"),
              ]
    for juicer in juicers:
        args = re.search(juicer, source, re.DOTALL)
        if args:
            a = args.groups()
            try:
                return a[0], a[3].split('|'), int(a[1]), int(a[2])
            except ValueError:
                raise UnpackingError('Corrupted p.a.c.k.e.r. data.')

    # could not find a satisfying regex
    raise UnpackingError('Could not make sense of p.a.c.k.e.r data (unexpected code structure)')



def _replacestrings(source):
    """Strip string lookup table (list) and replace values in source."""
    match = re.search(r'var *(_\w+)\=\["(.*?)"\];', source, re.DOTALL)

    if match:
        varname, strings = match.groups()
        startpoint = len(match.group(0))
        lookup = strings.split('","')
        variable = '%s[%%d]' % varname
        for index, value in enumerate(lookup):
            source = source.replace(variable % index, '"%s"' % value)
        return source[startpoint:]
    return source


class Unbaser(object):
    """Functor for a given base. Will efficiently convert
    strings to natural numbers."""
    ALPHABET  = {
        22 : '0123456789abcdefghijkl',
        23 : '0123456789abcdefghijklm',
        24 : '0123456789abcdefghijklmn',
        25 : '0123456789abcdefghijklmno',
        26 : '0123456789abcdefghijklmnop',
        27 : '0123456789abcdefghijklmnopq',
        28 : '0123456789abcdefghijklmnopqr',
        29 : '0123456789abcdefghijklmnopqrs',
        30 : '0123456789abcdefghijklmnopqrst',
        31 : '0123456789abcdefghijklmnopqrstu',
        32 : '0123456789abcdefghijklmnopqrstuv',
        33 : '0123456789abcdefghijklmnopqrstuvw',
        34 : '0123456789abcdefghijklmnopqrstuvwx',
        35 : '0123456789abcdefghijklmnopqrstuvwxy',
        36 : '0123456789abcdefghijklmnopqrstuvwxyz',
        37 : '0123456789abcdefghijklmnopqrstuvwxyzA',
        38 : '0123456789abcdefghijklmnopqrstuvwxyzAB',
        39 : '0123456789abcdefghijklmnopqrstuvwxyzABC',
        40 : '0123456789abcdefghijklmnopqrstuvwxyzABCD',
        41 : '0123456789abcdefghijklmnopqrstuvwxyzABCDE',
        42 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEF',
        43 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFG',
        44 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGH',
        45 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHI',
        46 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJ',
        47 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJK',
        48 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKL',
        49 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLM',
        50 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN',
        51 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNO',
        52 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP',
        53 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQ',
        54 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR',
        55 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRS',
        56 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRST',
        57 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTU',
        58 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUV',
        59 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVW',
        60 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX',
        61 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXY',
        62 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
        95 : (' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ'
              '[\]^_`abcdefghijklmnopqrstuvwxyz{|}~')
    }

    def __init__(self, base):
        self.base = base

        # If base can be handled by int() builtin, let it do it for us
        if 2 <= base <= 36:
            self.unbase = lambda string: int(string, base)
        else:
            # Build conversion dictionary cache
            try:
                self.dictionary = dict((cipher, index) for
                    index, cipher in enumerate(self.ALPHABET[base]))
            except KeyError, e:
                raise TypeError('Unsupported base encoding.')

            self.unbase = self._dictunbaser

    def __call__(self, string):
        return self.unbase(string)

    def _dictunbaser(self, string):
        """Decodes a  value to an integer."""
        ret = 0
        for index, cipher in enumerate(string[::-1]):
            ret += (self.base ** index) * self.dictionary[cipher]
        return ret
