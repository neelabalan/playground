# code generated with Claude Haiku
import argparse
import logging
import time

import networkx as nx
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


def create_random_tree(n_nodes):
    """Create a random tree with the given number of nodes."""
    G = nx.Graph()
    G.add_nodes_from(range(n_nodes))

    # Add edges to create a tree
    for i in range(1, n_nodes):
        G.add_edge(i, np.random.randint(0, i))

    return G


def compute_metrics(G):
    """Compute some metrics on the graph."""
    n_components = nx.number_connected_components(G)
    diameter = nx.diameter(G)
    avg_clustering = nx.average_clustering(G)

    return n_components, diameter, avg_clustering


def benchmark_original_vs_spanning(n_nodes):
    """Benchmark the original graph and its spanning tree."""
    G = create_random_tree(n_nodes)

    log.info('Original Graph:')
    start_time = time.time()
    n_components, diameter, avg_clustering = compute_metrics(G)
    original_time = time.time() - start_time
    log.info(f'Number of components: {n_components}')
    log.info(f'Diameter: {diameter}')
    log.info(f'Average clustering coefficient: {avg_clustering}')
    log.info(f'Computation time: {original_time:.5f} seconds')

    spanning_tree = nx.minimum_spanning_tree(G)

    log.info('Spanning Tree:')
    start_time = time.time()
    n_components, diameter, avg_clustering = compute_metrics(spanning_tree)
    spanning_time = time.time() - start_time
    log.info(f'Number of components: {n_components}')
    log.info(f'Diameter: {diameter}')
    log.info(f'Average clustering coefficient: {avg_clustering}')
    log.info(f'Computation time: {spanning_time:.5f} seconds')

    log.info(f'Original graph computation time: {original_time:.5f} seconds')
    log.info(f'Spanning tree computation time: {spanning_time:.5f} seconds')
    if original_time > spanning_time:
        log.info('The spanning tree is easier to compute.')
    else:
        log.info('The original graph is easier to compute.')


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Benchmark graph computations.')
    parser.add_argument('-n', '--nodes', type=int, required=True, help='Number of nodes in the graph')
    return parser.parse_args()


def main():
    args = parse_args()
    benchmark_original_vs_spanning(args.nodes)


if __name__ == '__main__':
    main()
