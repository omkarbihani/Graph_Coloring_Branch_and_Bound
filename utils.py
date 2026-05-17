import numpy as np
import networkx as nx


def read_graph_file_coloring_instances(filename):
    """
    Reads the edgelist of the graphs in dimacs format and returns a nx.Graph.
    """

    edges = []
    num_nodes = num_edges = 0

    with open(filename, "r") as file:
        for line in file:
            if line.startswith("c"):
                continue  # Skip comment lines
            elif line.startswith("p"):
                parts = line.strip().split()
                num_nodes = int(parts[2])
                num_edges = int(parts[3])
            elif line.startswith("e"):
                _, node1, node2 = line.strip().split()
                edges.append((int(node1), int(node2)))

    G = nx.Graph()
    G.add_nodes_from(range(1, num_nodes + 1))
    G.add_edges_from(edges)

    return G
