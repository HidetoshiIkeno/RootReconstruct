# coding: utf-8
from __future__ import division, print_function, unicode_literals
import math

import sys, os
sys.path.append(os.pardir)
from common import util
from treeroot import TreeRoot
from disjoint_set import DisjointSet

def inner_product(a, b):
    util.assert_same_size(a=a, b=b)
    n = len(a)
    dot = 0.0
    for i in xrange(n):
        dot += a[i] * b[i]
    return dot


class MinimumSpanningTree:
    def __init__(self):
        pass

    def reconstruct(self, tree_root):
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
        util.assert_same_size(xs=tree_root.xs, ys=tree_root.ys, zs=tree_root.zs)
        n = tree_root.node_count()
        es = []
        for i in xrange(n):
            for j in xrange(i + 1, n):
                l2norm = tree_root.distance(i, j)
                es.append((math.sqrt(l2norm), i, j))

        es.sort(key=lambda tup: tup[0])
        disjoint_set = DisjointSet(n)
        links = []
        for _, src, dst in es:
            if not disjoint_set.same(src, dst):
                disjoint_set.merge(src, dst)
                links.append((src, dst))
        return links


class SekiharaMethod:
    def __init__(self, param, inner_product=True):
        self.param = param
        if inner_product:
            self.cost_func = lambda cos_theta, abs_dst, max_d : param * (1.0 - cos_theta) + abs_dst / max_d
        else:
            self.cost_func = lambda cos_theta, abs_dst, max_d : math.acos(cos_theta) + param * abs_dst / max_d

    def reconstruct(self, tree_root):
        links = []

        n = tree_root.node_count()
        max_d = tree_root.max_distance()
        UF = DisjointSet(n)
        order_by_dist = tree_root.order_by_dist(reverse=True)

        center = tree_root.vectorized_center_pos()
        for t in xrange(0, n-1):
            i = order_by_dist[t][0]
            cost = float('inf')
            next_index = -1
            src = tree_root.vectorized_node_pos(i)

            for j in xrange(0, n):
                if i == j: continue
                if j != 0 and tree_root.radii[i] > 1.3 * tree_root.radii[j]: continue

                # Avoid making a cycle
                if UF.same(i, j): continue

                dst = tree_root.vectorized_node_pos(j)
                c = self._sekihara_method(src, dst, center, self.cost_func, max_d)

                if cost > c:
                    cost = c
                    next_index = j

            if next_index != -1:
                links.append((i, next_index))
                UF.merge(i, next_index)

        return links

    def _sekihara_method(self, src, dst, center, cost_func, max_d):
        vec_dst = [dst[0] - src[0], dst[1] - src[1], dst[2] - src[2]]
        abs_dst = math.sqrt(inner_product(vec_dst, vec_dst))

        vec_center = [center[0] - src[0], center[1] - src[1], center[2] - src[2]]
        abs_center = math.sqrt(inner_product(vec_center, vec_center))

        dot = inner_product(vec_dst, vec_center)

        if abs_dst == 0.0 or abs_center == 0.0:
            cos_theta = 1.0
        else:
            cos_theta = dot / (abs_dst * abs_center)
            if cos_theta > 0.0: cos_theta = min(cos_theta, 1.0)
            else:               cos_theta = max(cos_theta, -1.0)

        return cost_func(cos_theta, abs_dst, max_d)
