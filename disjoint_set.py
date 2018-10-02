# coding: utf-8

class DisjointSet(object):
    def __init__(self, size):
        self._parent = [-1]*size

    def _root(self, x):
        if self._parent[x] < 0:
            return x
        else:
            self._parent[x] = self._root(self._parent[x])
            return self._parent[x]

    def same(self, x, y):
        return self._root(x) == self._root(y)

    def size(self, x):
        return -self._parent[self._root(x)]

    def merge(self, x, y):
        x = self._root(x)
        y = self._root(y)
        if x != y:
            if self.size(x) < self.size(y):
                x, y = y, x

            self._parent[x] += self._parent[y]
            self._parent[y] = x
