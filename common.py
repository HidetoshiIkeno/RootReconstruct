# coding: utf-8
from __future__ import division, print_function, unicode_literals

import codecs
import sys

def set_terminal_encoding(encoding='utf_8'):
    """
    端末とPython間のエンコーディングを設定する。

    stdout，stderrは問題ないのだが，stdinの動作が直感と反する環境もあるので注意。
    (例:MacではControl-Zを入力しないと入力が確定されない)
    """
    sys.stdin = codecs.getreader(encoding)(sys.stdin)
    sys.stdout = codecs.getwriter(encoding)(sys.stdout)
    sys.stderr = codecs.getwriter(encoding)(sys.stderr)

def assert_same_size(**keywords):
    """
    渡されたリストのサイズが同じであるかどうかチェックする
    """
    keys = keywords.keys()
    n = len(keys)
    for i in xrange(n):
        for j in xrange(i + 1, n):
            assert len(keywords[keys[i]]) == len(keywords[keys[j]]), 'len({}) should eq len({})'.format(keys[i], keys[j])
