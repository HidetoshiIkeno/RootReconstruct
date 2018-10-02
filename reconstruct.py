# coding: utf-8
from __future__ import division, print_function, unicode_literals

import codecs
import math
from collections import deque
import copy
from reconstructor import *

import sys, os
sys.path.append(os.pardir)
from common import util, dat2vtk, swc2vtk
from treeroot import TreeRoot
import treeroot


def get_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dat', type=str)
    parser.add_argument('output', type=str)
    parser.add_argument('--coef-radius', dest='coef_radius', type=float, default=0.05)
    parser.add_argument('--method', type=str, choices=['an', 'ip', 'dist'], default='ip', help='reconstruct method')
    parser.add_argument('--output-format', dest='output_format', type=str, choices=['dat', 'vtk'], default='vtk', help='output file format')
    parser.add_argument('--param-alpha', dest='param_alpha', type=float, default=1.1)
    parser.add_argument('--param-w', dest='param_w', type=float, default=1.1)
    return parser.parse_args()


def main():
    args = get_args()

    try:
        tree_root = TreeRoot.load_dat(args.input_dat)
    except IOError as e:
        print("[Error] No such file : {}".format(args.input_dat))
        sys.exit(1)
    except dat2vtk.FileFormatError as e:
        print("[Error] Unexpected file format.")
        sys.exit(1)
    except dat2vtk.FileSyntaxError as e:
        print("[Error] Syntax error.")
        sys.exit(1)
    
    if args.method == 'dist':
        reconstructor = MinimumSpanningTree()
    elif args.method == 'an':
        reconstructor = SekiharaMethod(args.param_alpha, inner_product=False)
    elif args.method == 'ip':
        reconstructor = SekiharaMethod(args.param_w, inner_product=True)

    reconstructed_tree_root = copy.deepcopy(tree_root)
    reconstructed_tree_root.links = reconstructor.reconstruct(tree_root)

    if args.output_format == 'dat':
        reconstructed_tree_root.export_dat(args.output)
    elif args.output_format == 'vtk':
        reconstructed_tree_root.export_vtk(args.output)
    print("Output file is created.\n");

    if len(tree_root.links) > 0:
        accuracy = treeroot.compute_accuracy(
            reconstructed_tree_root,
            tree_root
        )
        print("Accuracy (Edge)           : {:.3%}".format(accuracy["edge_count"]))
        print("Accuracy (Volume)         : {:.3%}".format(accuracy["edge_volume"]))


if __name__ == "__main__":
    util.set_terminal_encoding()
    main()
