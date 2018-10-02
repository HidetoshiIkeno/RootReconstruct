# coding: utf-8
from __future__ import division, print_function, unicode_literals

import unittest
from disjoint_set import DisjointSet

class TestDisjointSet(unittest.TestCase):
    def test_no_merge(self):
        s = DisjointSet(3)
        self.assertEqual(s._parent, [-1, -1, -1])
        self.assertEqual(s._root(0), 0)
        self.assertEqual(s._root(1), 1)
        self.assertEqual(s._root(2), 2)
        self.assertEqual(s.size(0), 1)
        self.assertEqual(s.size(1), 1)
        self.assertEqual(s.size(2), 1)
        self.assertTrue(s.same(0, 0))
        self.assertTrue(s.same(1, 1))
        self.assertTrue(s.same(2, 2))
        self.assertFalse(s.same(0, 1))
        self.assertFalse(s.same(0, 2))
        self.assertFalse(s.same(1, 0))
        self.assertFalse(s.same(1, 2))
        self.assertFalse(s.same(2, 0))
        self.assertFalse(s.same(2, 1))

    def test_merge(self):
        s = DisjointSet(3)
        s.merge(0, 2)
        self.assertEqual(s.size(0), 2)
        self.assertEqual(s.size(2), 2)
        self.assertEqual(s.size(1), 1)
        self.assertTrue(s.same(0, 2))
        self.assertTrue(s.same(2, 0))
        self.assertFalse(s.same(0, 1))
        self.assertFalse(s.same(1, 0))
        self.assertFalse(s.same(1, 2))
        self.assertFalse(s.same(2, 1))

if __name__ == '__main__':
    unittest.main()
