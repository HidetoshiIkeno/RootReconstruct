# coding: utf-8
from __future__ import division, print_function, unicode_literals

import codecs
import sys

def set_terminal_encoding(encoding='utf_8'):
    """
    Set encoding in accordance with the terminal
    """
    sys.stdin = codecs.getreader(encoding)(sys.stdin)
    sys.stdout = codecs.getwriter(encoding)(sys.stdout)
    sys.stderr = codecs.getwriter(encoding)(sys.stderr)

def assert_same_size(**keywords):
    """
    Compare the size of passed lists and assertion
    """
    keys = keywords.keys()
    n = len(keys)
    for i in xrange(n):
        for j in xrange(i + 1, n):
            assert len(keywords[keys[i]]) == len(keywords[keys[j]]), 'len({}) should eq len({})'.format(keys[i], keys[j])
