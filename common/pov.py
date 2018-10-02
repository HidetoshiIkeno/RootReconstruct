# coding: utf-8
from __future__ import division, print_function, unicode_literals

import codecs


def read_pov(fname):
    spheres = []
    cones = []
    with codecs.open(fname, 'r', 'utf_8') as f:
        for line in f:
            if line.startswith('object{parts('):
                # Remove 'object{parts(' and ')}'
                s = line.strip()[len('object{parts('):-2]
                a = map(float, s.split(','))
                if len(a) == 4:
                    spheres.append(a)
                elif len(a) == 11:
                    cones.append(a)
                else:
                    raise RuntimeError('unknown format: ' + line)

    return spheres, cones


def omit_print(seq):
    '''
    Print the list only 10 elements
    '''
    if len(seq) > 10:
        for s in seq[:5]:
            print(repr(s))
        print('...')
        for s in seq[-5:]:
            print(repr(s))
    else:
        for s in seq:
            print(repr(s))
