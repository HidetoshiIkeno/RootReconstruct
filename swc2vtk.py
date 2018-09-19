# coding: utf-8
from __future__ import division, print_function, unicode_literals

import argparse
import codecs
import sys

import common

def generate_vtk(root, links, xs, ys, zs, radii, data={}):
    '''
    Parameters
    ----------
    root : int
    links : [(int, int)]
    xs : [float]
    ys : [float]
    zs : [float]
    radii : [float]
    data : {string, [float]}

    Returns
    -------
    iter : iterator of string
    '''

    common.assert_same_size(xs=xs, ys=ys, zs=zs, radii=radii, **data)
    n = len(radii)

    # 木の辺の数はn-1であるが、現実は非情である
    # assert len(links) == n - 1, 'len(links) expect eq len(radii) - 1'

    # おまじない
    yield '# vtk DataFile Version 2.0'
    # タイトル
    yield 'SWC Data'
    # テキストで記述する (BINARYにするとバイナリで記述可能)
    yield 'ASCII'
    # LINEで記述する
    yield 'DATASET POLYDATA'

    # 点データの記述
    yield 'POINTS {} float'.format(n)
    for i in xrange(n):
        yield '{:.7} {:.7} {:.7}'.format(xs[i], ys[i], zs[i])

    # 線データの記述
    yield 'LINES {} {}'.format(len(links), 3*len(links))
    for link in links:
        yield '2 {} {}'.format(link[0], link[1])

    # データの記述
    yield 'POINT_DATA {}'.format(n)

    # 半径の記述
    yield 'SCALARS radius float'
    yield 'LOOKUP_TABLE default'
    for radius in radii:
        yield '{:.7}'.format(radius)

    # その他データの記述
    for key, values in data.iteritems():
        yield 'SCALARS {} float'.format(key)
        yield 'LOOKUP_TABLE default'
        for value in values:
            yield '{:.7}'.format(value)


def parse_swc(fname):
    """
    Parameters
    ----------
    fname : string

    Returns
    -------
    root : int
    links : [(int, int)]
    xs : [float]
    ys : [float]
    zs : [float]
    radii : [float]
    """

    # ノードIDが連続していないので、
    # 座標圧縮のようなことをして、連続に並ぶようにする
    data = []
    label_to_index = {}
    with codecs.open(fname, encoding='utf_8') as f:
        for line in f:
            id_, type_, x, y, z, r, parent = line.split()
            id_    = int(id_)
            type_  = int(type_)
            x      = float(x)
            y      = float(y)
            z      = float(z)
            r      = float(r)
            parent = int(parent)
            data.append((id_, type_, x, y, z, r, parent))
            label_to_index[id_] = len(label_to_index)

    xs = [None]*len(label_to_index)
    ys = [None]*len(label_to_index)
    zs = [None]*len(label_to_index)
    radii = [None]*len(label_to_index)
    links = []
    for d in data:
        index = label_to_index[d[0]]
        xs[index] = d[2]
        ys[index] = d[3]
        zs[index] = d[4]
        radii[index] = d[5]
        if d[6] == -1:
            root = index
        else:
            assert d[6] in label_to_index, 'Cannot find parent node {}'.format(repr(d))
            parent_index = label_to_index[d[6]]
            links.append((index, parent_index))

    return root, links, xs, ys, zs, radii


def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser()
    parser.add_argument('input_swc')
    parser.add_argument('output_vtk')
    args = parser.parse_args()

    ret = parse_swc(args.input_swc)

    with codecs.open(args.output_vtk, mode='w', encoding='utf_8') as f:
        for line in generate_vtk(*ret):
            print(line, file=f)

if __name__ == '__main__':
    common.set_terminal_encoding()
    main()
