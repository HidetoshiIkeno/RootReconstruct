# coding: utf-8
from __future__ import division, print_function, unicode_literals

import argparse
import codecs
import logging
from collections import deque, namedtuple

import swc2vtk
import common
import dat2vtk

import sys


def cast_and_join(delim, l):
    l = map(str, l)
    return delim.join(l)


def generate_swc(dat_name, label_to_index, node_filter, center_height, center_radius):
    fformat = dat_name[-3:]
    if fformat == "dat": delim = " "
    elif fformat == "csv": delim = ","

    for line in open(dat_name, 'r'):
        s = line.rstrip().split(delim)

        if len(node_filter) != 0 and label_to_index[int(s[4])] not in node_filter: continue

        if s[4] == "0" and s[5] == "0":
            # the root point
            yield cast_and_join(" ", [0, 0, s[0], s[1], float(s[2])-center_height, center_radius, -1])
            yield cast_and_join(" ", [1, 0, s[0], s[1], s[2], center_radius, 0])
        else:
            yield cast_and_join(" ", [int(s[4])+1, 0, s[0], s[1], s[2], float(s[3]) * 0.5, int(s[5])+1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dat', type=str)
    parser.add_argument('output_swc', type=str)
    parser.add_argument('--start', type=int, default=-1);
    parser.add_argument('--center_radius', type=float, default=0)
    parser.add_argument('--center_height', type=float, default=0)
    args = parser.parse_args() 

    try:
        tree_data = dat2vtk.Parser.load(args.input_dat)
    except IOError as e:
        print("[Error] No such file : {}".format(args.input_dat))
        sys.exit(1)
    except dat2vtk.FileFormatError as e:
        print("[Error] Unexpected file format.")
        sys.exit(1)
    except dat2vtk.FileSyntaxError as e:
        print("[Error] Syntax error.")
        sys.exit(1)

    links, xs, ys, zs, rs, labels, label_to_index = dat2vtk.convert_to_simple_format_graph(tree_data)
    n = len(xs)

    # Make a set of nodes that can reach to the selected node
    dist = []
    if args.start != -1:
        tree = [[] for i in xrange(0, n)]
        for l in links:
            tree[l[0]].append(l[1])
            tree[l[1]].append(l[0])

        found = False
        Q = deque()
        vis = [False for i in xrange(n)]
        Q.append([0, -1, False])
        vis[0] = True

        while len(Q):
            s = Q.popleft()

            # print("{} {} {}".format(s[0], s[1], s[2]))
            if s[0] == label_to_index[args.start] or s[2]:
                dist.append(s[0])
                
            for u in tree[s[0]]:
                if u == s[1] or vis[u]: continue
                Q.append([u, s[0], (s[2] or s[0] == label_to_index[args.start])])
                vis[u] = True

    # Output as swc file format
    iterator = generate_swc(args.input_dat, label_to_index, dist, args.center_height, args.center_radius) 
    with codecs.open(args.output_swc, 'w', 'utf_8') as f_out:
        for line in iterator:
            print(line, file=f_out)
    

if __name__ == "__main__":
    common.set_terminal_encoding()
    main()
