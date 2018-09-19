# coding: utf-8

from __future__ import division, print_function, unicode_literals

import argparse
import codecs
import logging
import math
from collections import deque, namedtuple

import swc2vtk
import common
import sys

class FileFormatError(Exception):
    """
    入力ファイルが対応していない形式で与えられた場合に発生される例外
    ファイルの拡張子が ".dat" か ".csv" 以外の場合に発生させる
    """
    pass

class FileSyntaxError(Exception):
    pass

class Parser(object):
    @classmethod
    def parse_line(cls, line_str, delim):
        """
        Parameters
        ----------
        line_str : string

        Returns
        -------
        retval : {"x": float, "y": float, "z": float,
                  "diameter": float, "label": int, "parent_label": int}

        Examples
        --------
        >>> Parser.parse_line("132 181 66  15.15   1001    1002")
        {"x":132.0, "y":181.0, "z":66, "diameter":15.15,
         "label":1001, "parent_label":1002}
        """
        s = line_str.split(delim)
        if len(s) != 6: raise FileSyntaxError
        return {"x": float(s[0]), "y": float(s[1]), "z": float(s[2]),
                "diameter": float(s[3]), "label": int(s[4]),
                "parent_label": int(s[5])}

    @classmethod
    def load(cls, fname):
        """
        Parameters
        ----------
        fname : string

        Returns
        -------
        retval : [{"x": float, "y": float, "z": float,
                   "diameter": float, "label": int, "parent_label": int}]

        """

        fformat = fname[-3:]
        if fformat == "dat": delim = " "
        elif fformat == "csv": delim = ","
        else: raise FileFormatError

        ret = []
        with codecs.open(fname, 'r', 'utf_8') as f:
            for line in f:
                if len(line) == 0 or line[0] == "#": continue
                ret.append(cls.parse_line(line, delim))
        return ret


def generate_sphere(xs, ys, zs, radii, data={}):
    common.assert_same_size(xs=xs, ys=ys, zs=zs, radii=radii, **data)
    n = len(radii)

    # おまじない
    yield '# vtk DataFile Version 2.0'
    # タイトル
    yield 'SWC Data'
    # テキストで記述する (BINARYにするとバイナリで記述可能)
    yield 'ASCII'
    # POLYDATAで記述する
    yield 'DATASET POLYDATA'

    # 点データの記述
    yield 'POINTS {} float'.format(n)
    for i in xrange(n):
        yield '{:.7} {:.7} {:.7}'.format(xs[i], ys[i], zs[i])

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


def convert_to_simple_format_graph(tree_data):
    """
    Parser.load(fname)で読み込んだデータを扱いやすい形式に変換する

    Parameters
    ----------
    tree_data : [{"x": float, "y": float, "z": float,
                  "diameter": float, "label": int, "parent_label": int}]

    Returns
    -------
    links : [(int, int)]
    xs : [float]
    ys : [flaot]
    zs : [float]
    radii : [float]
    labels : [int]
    label_to_index : {int, int}
    """

    # datファイルに中心点を表す0番ノードが存在しなければならない
    # assert 0 in tree_data.label, '入力ファイルに中心点を表す0番ノードが存在しません.'


    # datファイルでは連番でないIDが使われているので連番に変換する
    # 0番は中心点を表す
    label_to_index = {}
    label_to_index[0] = 0
    
    zero = False
    for datum in tree_data:
        label = datum["label"]
        if label == 0: zero=True
        if label not in label_to_index:
            label_to_index[label] = len(label_to_index)

    # 0番ノードがない場合はエラーとする
    if not zero:
        print("入力ファイルに中心点を表す0番ノードが存在しません.")
        sys.exit(1)

    # 配列の確保 (Noneをコピーするのが最も高速らしい)
    # See Also : http://stackoverflow.com/questions/537086/reserve-memory-for-list-in-python
    xs = [None]*len(label_to_index)
    ys = [None]*len(label_to_index)
    zs = [None]*len(label_to_index)
    labels = [None]*len(label_to_index)
    radii = [None]*len(label_to_index)
    links = []
    
    # datの独自IDから連番に変換しつつ、格納してみる
    for datum in tree_data:
        index = label_to_index[datum["label"]]
        xs[index] = datum["x"]
        ys[index] = datum["y"]
        zs[index] = datum["z"]
        labels[index] = datum["label"]
        radii[index] = datum["diameter"]

    # なぜかdatファイルに欠けている点 (あるノードのparentとして
    # 宣言されているのに、その点自身の情報が記述されていない)
    # が存在するため、子または親が存在しないときはlinkを作らないようにする
    for datum in tree_data:
        label = datum["label"]
        parent_label = datum["parent_label"]

        # 子の情報も親の情報も存在する時
        if label in label_to_index and parent_label in label_to_index:
            index = label_to_index[label]
            parent_index = label_to_index[parent_label]
            links.append((index, parent_index))

    return links, xs, ys, zs, radii, labels, label_to_index


def compute_distance(root_nodes, links, xs, ys, zs, radii):
    """
    distanceを計算する

    Parameters
    ----------
    root_nodes : [int]
    links : [(int, int)]
    xs : [float]
    ys : [float]
    zs : [float]
    radii : [float]

    Returns
    -------
    distance : [float]
    """
    n = len(radii)
    common.assert_same_size(xs=xs, ys=ys, zs=zs, radii=radii)


    # collections.dequeが高速
    # See Also : http://docs.python.jp/2/library/collections.html#deque
    que = deque()
    distance = [None]*n
    for index in root_nodes:
        distance[index] = 0.0
        que.append(index)

    while len(que) > 0:
        index = que.popleft()
        for src, dst in links:
            if dst == index:
                src, dst = dst, src
            if src != index:
                continue
            if distance[dst] is not None:
                continue
            l2norm = (xs[src] - xs[dst])**2 + (ys[src] - ys[dst])**2 + (zs[src] - zs[dst])**2
            distance[dst] = distance[src] + math.sqrt(l2norm)
            que.append(dst)

    for i in xrange(n):
        if distance[i] is None:
            distance[i] = 0.0

    return distance


def check_link_distance(linedata, thresh):
    Point = namedtuple("Point", "x y z parent_label")
    # label -> Point
    g = {}
    for datum in linedata:
        if datum["label"] in g:
            logging.warning("label={} のデータが複数あります".format(datum["label"]))

        g[datum["label"]] = Point(datum["x"], datum["y"], datum["z"], datum["parent_label"])

    for label, p in g.iteritems():
        if p.parent_label not in g:
            # logging.warning(
            #   "label = {} の親ラベルは {} ですが, そのラベルを持つデータが見つかりません".format(label, p.parent_label))
            continue

        q = g[p.parent_label]
        d = math.sqrt((p.x - q.x)**2 + (p.y - q.y)**2 + (p.z - q.z)**2)
        if d == 0.0 and label != p.parent_label:
            logging.warning(
                "label={} と label={} の距離が 0.0 です".format(label, p.parent_label))
        if d > thresh:
            logging.warning(
                "label={} と label={} の距離が {} (> thresh={}) です".format(label, p.parent_label, d, thresh))


def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dat', type=str,
            help="入力のdatファイル名 (CSVに似た形式)")
    parser.add_argument('output_vtk', type=str,
            help="出力するvtkファイル名")
    parser.add_argument(
            '--sphere', action='store_true',
            help="チューブで繋がずにボールだけ表示する")
    parser.add_argument(
            '--coef-radius', dest='coef_radius', type=float,default=0.05,
            help="表示するボールの大きさを決める係数 (見た目の問題)")
    parser.add_argument('--thresh', type=float,
            help="点と点のリンクのユークリッド距離がthreshよりも大きいとき, 警告メッセージを表示する (指定が無いときは警告無効)")
    args = parser.parse_args()


    try:
        tree_data = Parser.load(args.input_dat)
    except IOError as e:
        print("[エラー] 入力ファイルが存在しません")
        sys.exit(1)
    except FileFormatError as e:
        print("[エラー] 入力はdat形式かcsv形式のファイルを指定してください")
        sys.exit(1)
    except FileSyntaxError as e:
        print("[エラー] 入力ファイルが正しく記述されていません")
        sys.exit(1)


    if args.thresh is not None:
        check_link_distance(tree_data, args.thresh)

    links, xs, ys, zs, radii, _, label_to_index = convert_to_simple_format_graph(tree_data)
    radii = map(lambda r: r * args.coef_radius, radii)

    root_nodes = []
    for datum in tree_data:
        label = datum['label']
        index = label_to_index[label]
        parent_label = datum['parent_label']
        if parent_label == 0:
            root_nodes.append(index)

    distance = compute_distance(root_nodes, links, xs, ys, zs, radii)

    # write vtk
    if args.sphere:
        # POINTモード
        iterator = generate_sphere(xs, ys, zs, radii)
    else:
        # LINEモード
        iterator = swc2vtk.generate_vtk(0, links, xs, ys, zs, radii, {'distance': distance})
    with codecs.open(args.output_vtk, 'w', 'utf_8') as f:
        for line in iterator:
            print(line, file=f)

if __name__ == "__main__":
    common.set_terminal_encoding()
    main()
