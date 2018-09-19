# coding: utf-8
from __future__ import division, print_function, unicode_literals

import argparse
import codecs
import math
from collections import deque
import common
import dat2vtk
import swc2vtk
from disjoint_set import DisjointSet
import os.path
import sys
import calc_volume

def construct_minimum_spanning_tree(xs, ys, zs):
    """
    Parameters
    ----------
    xs : [float]
    ys : [float]
    zs : [float]

    Returns
    -------
    links : [(int, int)]
    biggest_root : int
    """
    common.assert_same_size(xs=xs, ys=ys, zs=zs)
    n = len(xs)
    es = []
    for i in xrange(n):
        for j in xrange(i + 1, n):
            l2norm = (xs[i] - xs[j])**2 + (ys[i] - ys[j])**2 + (zs[i] - zs[j])**2
            es.append((math.sqrt(l2norm), i, j))

    es.sort(key=lambda tup: tup[0])
    disjoint_set = DisjointSet(n)
    links = []
    for _, src, dst in es:
        if not disjoint_set.same(src, dst):
            disjoint_set.merge(src, dst)
            links.append((src, dst))

    biggest_root = -1

    for i in xrange(n):
        if biggest_root == -1 or disjoint_set.size(biggest_root) < disjoint_set.size(i):
            biggest_root = i

    return links, biggest_root


def inner_product(a, b):
    common.assert_same_size(a=a, b=b)
    n = len(a)
    dot = 0.0
    for i in xrange(n):
        dot += a[i] * b[i]
    return dot


def sekihara_method(src, dst, center, alpha):
    vec_dst = [dst[0] - src[0], dst[1] - src[1], dst[2] - src[2]]
    abs_dst = math.sqrt(inner_product(vec_dst, vec_dst))

    vec_center = [center[0] - src[0], center[1] - src[1], center[2] - src[2]]
    abs_center = math.sqrt(inner_product(vec_center, vec_center))

    dot = inner_product(vec_dst, vec_center)
    
    if abs_dst == 0.0 or abs_center == 0.0:
        cos_theta = 1.0
    else:
        cos_theta = dot / (abs_dst * abs_center)
    
    return alpha*(1.0 - cos_theta) + abs_dst
    

def construct_one_vs_one_cost(xs, ys, zs, radii, alpha, **keywords):
    common.assert_same_size(xs=xs, ys=ys, zs=zs)
    links = []
    
    n = len(xs)
    UF = DisjointSet(n)

    """
    # ２点間の距離の最大を求める
    max_d = 0.0
    for i in xrange(n):
        for j in xrange(i+1, n):
            dis = math.sqrt((xs[i]-xs[j])**2 + (ys[i]-ys[j])**2 + (zs[i]-zs[j])**2)
            if dis > max_d: max_d = dis
    """

    # 中心に遠い点から順番に処理する
    order_by_dist = []
    for i in xrange(1, n):
        order_by_dist.append([i, (xs[i]-xs[0])**2 + (ys[i]-ys[0])**2 + (zs[i] - zs[0])**2])
    order_by_dist.sort(key=lambda x:x[1], reverse=True)

    center = [xs[0], ys[0], zs[0]]
    for t in xrange(len(order_by_dist)):
        i = order_by_dist[t][0]

        cost = float('inf')
        next_index = -1

        src = [xs[i], ys[i], zs[i]]
         
        for j in xrange(0, len(xs)):
            if i == j: continue
            if j != 0 and radii[i] > 1.3 * radii[j]: continue
            
            # 閉路をつくらないようにする
            if UF.same(i, j): continue

            dst = [xs[j], ys[j], zs[j]]
            c = sekihara_method(src, dst, center, alpha)

            if cost > c:
                cost = c
                next_index = j
        links.append((i, next_index))
        
        if next_index != -1:
            UF.merge(i, next_index)
       
    return links, 0


def mst_sekihara_method(xs, ys, zs, radii, alpha, **keywords):
    n = len(xs)
    links = []
    edge = []

    radi_max = 0
    for i in xrange(n):
        radi_max = max(radi_max, radii[i])
    
    for i in xrange(n):
        for j in xrange(n):
            if i == j: continue
            if radii[i] > 1.3 * radii[j]: continue

            src = [xs[i], ys[i], zs[i]]
            dst = [xs[j], ys[j], zs[j]]
            center = [xs[0], ys[0], zs[0]]

            edge.append([i, j, (2 - radii[i] / radi_max) ** 2  * sekihara_method(src, dst, center, 0, alpha)])
    
    edge.sort(key=lambda x:x[2])

    UF = DisjointSet(n)

    for e in edge:
        u, v = e[0], e[1]
        if UF.same(u, v): continue
        links.append([u, v])
        UF.merge(u, v)

    return links, 0


def topological_dfs(G, parent, res):
    Q = deque()
    Q.append([parent, -1])
    vis = [parent]
    
    while len(Q):
        v = Q.popleft()
        if v[0] != parent:
            res[parent].append(v[0])
        
        for u in G[v[0]]:
            if u != v[1] and u not in vis:
                Q.append([u, v[0]])
                vis.append(u)


class DisconnectedException(Exception):
    pass


def relation_mat(n, links, xs, ys):
    G = [[] for _ in xrange(n)]
    G_reverse = [[] for _ in xrange(n)]
    for l in links:
        if l[1] not in G[l[0]] and not l[0] == l[1]:
            G[l[0]].append(l[1])
        if l[0] not in G_reverse[l[1]] and not l[0] == l[1]:
            G_reverse[l[1]].append(l[0])
    
    topological_related = [[] for _ in xrange(n)]
    for i in xrange(n):
        topological_dfs(G,  i, topological_related)
    
    # 分岐次数を求めるための幅優先探索
    depth = {}
    Q = deque()
    Q.append([0, 0])
    vis = []
    while len(Q):
        s = Q.popleft()
        depth[s[0]] = s[1]
        for t in G_reverse[s[0]]:
            if t not in vis:
                if len(G_reverse[s[0]]) >= 2 or s[0] == 0:
                    Q.append([t, s[1]+1])
                else:
                    Q.append([t, s[1]])
                vis.append(t)
    
    if len(depth) < n:
        raise DisconnectedException
    
    order_by_dist = []
    for i in xrange(1, n):
        order_by_dist.append([i, (xs[i]-xs[0])**2 + (ys[i]-ys[0])**2])
    order_by_dist.sort(key=lambda x:x[1], reverse=True)
    
    l_max = max(depth.values())
    # print("l_max = %d" % l_max)
     
    R = [[0]*(n-1) for _ in xrange(n-1)]
    for i in xrange(n-1):
        ki = order_by_dist[i][0]
        for j in xrange(i+1, n-1):
            kj = order_by_dist[j][0]
    
            if kj in topological_related[ki] and ki in depth.keys():
                R[i][j] = l_max - depth[ki] + 1
            else:
                R[i][j] = 0 
    
    return R, True 



def evaluate_mat(n, links, correct_links, xs, ys):
    R, ok = relation_mat(n, links, xs, ys)
    R_correct, ok  = relation_mat(n, correct_links, xs, ys)

    sum_error = 0
    sum_correct = 0
    for i in xrange(len(R)):
        for j in xrange(i, len(R[i])):
            sum_error += abs(R[i][j] - R_correct[i][j])
            sum_correct += R_correct[i][j]
    return (1 - sum_error/sum_correct)*100


def evaluate_edge(xs, ys, zs, rs, links, correct_links):
    cnt = 0
    ok = 0
    
    cnt_v = calc_volume.calc_edge_volume(xs, ys, zs, rs, correct_links)
    ok_v = 0.0

    for cl in correct_links:
        cnt += 1
        for l in links:
            if (cl[0] == l[0] and cl[1] == l[1]) or (cl[1] == l[0] and cl[0] == l[1]):
                ok += 1

                if (cl[0] != 0 and cl[1] != 0):
                    vec = [xs[l[1]] - xs[l[0]], ys[l[1]] - ys[l[0]], zs[l[1]] - zs[l[0]]]
                    height = math.sqrt(inner_product(vec, vec))
                    ok_v += calc_volume.tube(rs[l[0]]*0.5, rs[l[1]]*0.5, height)
                    break

    return (ok/cnt * 100), (ok_v/cnt_v * 100)


def generate_dat(input_file, links, labels, label_to_index):
    if input_file[-3:] == "dat": delim = " "
    elif input_file[-3:] == "csv": delim = ","
    
    with codecs.open(input_file, mode='r', encoding='utf-8') as f:
        for line in f:
            dat = line[:-1].split(delim)
            
            i = label_to_index[int(dat[4])]

            to = i
            for lnk in links:
                if lnk[0] == i:
                    to = lnk[1]

            # yield "{0}{6}{1}{6}{2}{6}{3}{6}{4}{6}{5}".format(dat[0], dat[1], dat[2], dat[3], labels[i], labels[to], separator)
            yield delim.join([str(dat[0]), str(dat[1]), str(dat[2]), str(dat[3]), str(labels[i]), str(labels[to])])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dat', type=str)
    parser.add_argument('output_vtk', type=str)
    parser.add_argument('--coef-radius', dest='coef_radius', type=float, default=0.05)
    parser.add_argument('--method', type=str, choices=['sekihara', 'mst', 'mst_sekihara'], default='sekihara', help='再構築に用いる手法')
    parser.add_argument('--output', type=str, choices=['dat', 'vtk'], default='vtk', help='出力ファイルの形式')
    parser.add_argument('--alpha', type=float, default=1.1)
    args = parser.parse_args()

    try:
        tree_data = dat2vtk.Parser.load(args.input_dat)
    except IOError as e:
        print("[エラー] 入力ファイルが存在しません")
        sys.exit(1)
    except dat2vtk.FileFormatError as e:
        print("[エラー] 入力はdat形式かcsv形式のファイルを指定してください")
        sys.exit(1)
    except dat2vtk.FileSyntaxError as e:
        print("[エラー] 入力ファイルが正しく記述されていません")
        sys.exit(1)
    
    correct_links, xs, ys, zs, radii_in, labels, label_to_index = dat2vtk.convert_to_simple_format_graph(tree_data)
    radii = map(lambda r: r * args.coef_radius, radii_in)

    if args.method == 'mst':
        links, biggest_root = construct_minimum_spanning_tree(xs, ys, zs)
    elif args.method == 'sekihara':
        links, biggest_root = construct_one_vs_one_cost(xs, ys, zs, radii, args.alpha)
    elif args.method == 'mst_sekihara':
        links, biggest_root = mst_sekihara_method(xs, ys, zs, radii, args.alpha)

    # 再構築結果をファイルに出力する
    with codecs.open(args.output_vtk, mode='w', encoding='utf_8') as f:
        if args.output == 'dat':
            for line in generate_dat(args.input_dat, links, labels, label_to_index):
                print(line, file=f) 
        elif args.output == 'vtk':
            for line in swc2vtk.generate_vtk(biggest_root, links, xs, ys, zs, radii):
                print(line, file=f) 

    # 再構築結果の評価値を表示する
    e_cnt, e_vol = evaluate_edge(xs, ys, zs, radii, links, correct_links)
    print("一致率 (辺)       : %.3f %%" % e_cnt)
    print("一致率 (体積)     : %.3f %%" % e_vol)

    try:
        print("一致率 (分岐次数) : %.3f %%" % evaluate_mat(len(xs), links, correct_links, xs, ys))
    except DisconnectedException as e:
        print("[エラー] 非連結なため, 分岐次数を計算できません")


if __name__ == "__main__":
    common.set_terminal_encoding()
    main()
