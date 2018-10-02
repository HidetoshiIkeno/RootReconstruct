# coding: utf-8
from __future__ import division, print_function, unicode_literals

import argparse
import codecs
import sys

from pov import *
from paraview.simple import *

def load(fname):
    spheres, cones = read_pov(fname)
    print('#spheres')
    omit_print(spheres)
    print('')
    print('#cones')
    omit_print(cones)

    for s in spheres:
        Sphere(Center=s[:3], Radius=s[3]/20)
        Show()
    Render()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output')
    args = parser.parse_args()

    load(args.input)

if __name__ == '__main__':
    sys.stdin = codecs.getreader('utf_8')(sys.stdin)
    sys.stdout = codecs.getwriter('utf_8')(sys.stdout)
    sys.stderr = codecs.getwriter('utf_8')(sys.stderr)
    main()
