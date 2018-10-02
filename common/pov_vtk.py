# coding: utf-8
from __future__ import division, print_function, unicode_literals

import argparse
import codecs
import sys
import os

import pov
import common

def list_unique(list_):
    s = set(tuple(item) for item in list_)
    return list(s)


def convert_to_tree(nodes, edges):
    """
    Generate a set of trees from nodes and edges
    """

    point2index = {}
    index2point = {}
    nodes = list_unique(nodes)
    for node in nodes:
        pos = tuple(node[:3])
        radius = node[3]
        size = len(index2point)
        point2index[pos] = size
        index2point[size] = (pos, radius)

    # Create a graph by adjacency list
    # Use set to remove faster
    graph = [set() for i in xrange(len(nodes))]
    for edge in edges:
        src = point2index[tuple(edge[:3])]
        dst = point2index[tuple(edge[4:7])]
        # Keeping simple graph
        if src == dst:
            continue
        if dst not in graph[src]:
            graph[src].add(dst)
        if src not in graph[dst]:
            graph[dst].add(src)

    rest = set(i for i in xrange(len(nodes)))
    j2 = []
    while len(rest) > 0:
        j = []
        que = []
        merged = set()
        index = 1
        r = rest.pop()
        pos, radius = index2point[r]
        j.append({
            'index': index,
            'type': 3,
            'position': pos,
            'radius': radius,
            'parent': -1})
        merged.add(r)
        que.append((r, index)) # index of index2point and SWC
        index += 1

        while len(que) > 0:
            cur, parent_index = que.pop(0)
            if cur in rest:
                rest.remove(cur)

            for next_ in graph[cur]:
                pos, radius = index2point[next_]
                j.append({
                    'index': index,
                    'type': 3,
                    'position': pos,
                    'radius': radius / 20, # 20 is a magic number defined in pov file format
                    'parent': parent_index})

                if next_ not in merged:
                    merged.add(next_)
                    que.append((next_, index))
                    graph[next_].remove(cur)

                index += 1

        j2.append(j)
    return j2


def convert_to_swc(j):
    '''convert__to_swc(dictionary) -> iterator
    '''
    for row in j:
        yield '{} {} {:.7} {:.7} {:.7} {:.7} {}'.format(
                row['index'],
                row['type'],
                row['position'][0],
                row['position'][1],
                row['position'][2],
                row['radius'],
                row['parent'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_pov')
    parser.add_argument('output_vtk')
    args = parser.parse_args()
    spheres, cones = pov.read_pov(args.input_pov)

    j2 = convert_to_tree(spheres, cones)

    if not os.path.isdir(args.output_dir):
        os.mkdir(args.output_dir)

    zfill_width = len(str(len(j2) - 1))
    for i in xrange(len(j2)):
        fname = os.path.join(
                args.output_dir,
                # padding with zeros
                '{:0>{width}}.swc'.format(i, width=zfill_width))
        with codecs.open(fname, 'w', 'utf_8') as f:
            for line in convert_to_swc(j2[i]):
                print(line, file=f)

if __name__ == '__main__':
    common.set_terminal_encoding()
    main()
