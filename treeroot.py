# coding: utf-8
from __future__ import division, print_function, unicode_literals

from common import util, dat2vtk, swc2vtk
import math
import codecs

class DisconnectedException(Exception):
    pass


class TreeRoot:
    def __init__(self, **keywords):
        util.assert_same_size(xs=keywords['xs'], ys=keywords['ys'], zs=keywords['zs'])

        self.xs             = keywords["xs"]
        self.ys             = keywords["ys"]
        self.zs             = keywords["zs"]
        self.links          = keywords["links"]
        self.radii          = keywords["radii"]
        self.labels         = keywords["labels"]
        self.label_to_index = keywords["label_to_index"]

        self._n             = len(self.xs)

    def node_count(self):
        return self._n

    def vectorized_node_pos(self, idx):
        return [self.xs[idx], self.ys[idx], self.zs[idx]]

    def vectorized_center_pos(self):
        return self.vectorized_node_pos(0)

    def distance(self, i, j):
        return math.sqrt((self.xs[i] - self.xs[j])**2 + (self.ys[i] - self.ys[j])**2 + (self.zs[i] - self.zs[j])**2)

    def max_distance(self):
        max_d = 0.0
        for i in xrange(self._n):
            for j in xrange(i+1, self._n):
                l2norm = self.distance(i, j)
                dis = math.sqrt(l2norm)
                if dis > max_d: max_d = dis
        return max_d

    def order_by_dist(self, reverse=False):
        order = [[i, (self.xs[i]-self.xs[0])**2 + (self.ys[i]-self.ys[0])**2 + (self.zs[i]-self.zs[0])**2] for i in xrange(1, self.node_count())]
        order.sort(key=lambda x:x[1], reverse=reverse)
        return order

    def edge_volume(self, node_a, node_b):
        r1, r2 = self.radii[node_a], self.radii[node_b]
        h = self.distance(node_a, node_b)
        return math.pi * (r1*r1 + r1*r2 + r2*r2) * h / 3.0

    def edge_volume_sum(self):
        volume_sum = 0.0
        for l in self.links:
            if l[0] != 0 and l[1] != 0:
                volume_sum += self.edge_volume(l[0], l[1])
        return volume_sum

    def to_adjacency_list(self, reverse=False):
        adj_list = [[] for _ in xrange(n)]
        for l in self.links:
            frm, to = l[0], l[1]
            if reverse:
                frm, to = to, frm
            if to not in adj_list[frm] and not frm == to:
                adj_list.append(to)
        return adj_list

    @classmethod
    def load_dat(cls, fname, coef_radius=0.5):
        tree_data = dat2vtk.Parser.load(fname)
        links, xs, ys, zs, radii_in, labels, label_to_index = dat2vtk.convert_to_simple_format_graph(tree_data)
        radii = map(lambda r: r * coef_radius, radii_in)
        return cls(
            links=links,
            xs=xs,
            ys=ys,
            zs=zs,
            radii=radii,
            labels=labels,
            label_to_index=label_to_index
        )

    def export_vtk(self, fname):
        with codecs.open(fname, mode='w', encoding='utf_8') as f:
            for line in swc2vtk.generate_vtk(0, self.links, self.xs, self.ys, self.zs, self.radii):
                print(line, file=f)

    def export_dat(self, fname):
        with codecs.open(fname, mode='w', encoding='utf_8') as f:
            for label in self.labels:
                idx_from = self.label_to_index[label]
                idx_to   = [x[1] for x in self.links if x[0] == idx_from][0]
                row_data = [self.xs[idx_from], self.ys[idx_from], self.zs[idx_from], self.radii[idx_from], label, self.labels[idx_to]]
                print(" ".join(map(str, row_data)), file=f)


def compute_accuracy(tree1, tree2):
    edge_count_all = len(tree1.links)
    edge_volume_all = tree2.edge_volume_sum()

    edge_count_correct = 0
    edge_volume_correct = 0.0

    for l1 in tree1.links:
        for l2 in tree2.links:
            if min(l1) == min(l2) and max(l1) == max(l2):
                edge_count_correct += 1
                if l1[0] != 0 and l1[1] != 0:
                    edge_volume_correct += tree1.edge_volume(l1[0], l1[1])
                break
    return {
        "edge_count":  edge_count_correct / edge_count_all,
        "edge_volume": edge_volume_correct / edge_volume_all,
    }
