from __future__ import annotations

import json
from typing import Dict, Hashable, Optional, Tuple, FrozenSet, Iterable

import networkx as nx


Bag = FrozenSet[Hashable]


def make_initial_bag_graph(G: nx.Graph) -> nx.Graph:
    """
    Converts an ordinary graph into a bag graph.

    Original node v becomes frozenset({v}).
    """

    H = nx.Graph()

    node_map = {v: frozenset({v}) for v in G.nodes}

    for v in G.nodes:
        H.add_node(node_map[v])

    for u, v in G.edges:
        H.add_edge(node_map[u], node_map[v])

    return H


def expand_bag_coloring(
    bag_coloring: Dict[Bag, int],
) -> Dict[Hashable, int]:
    """
    Converts a coloring of the bag graph back to a coloring of the original graph.
    """

    original_coloring: Dict[Hashable, int] = {}

    for bag, color in bag_coloring.items():
        for original_vertex in bag:
            original_coloring[original_vertex] = color

    return original_coloring


def validate_coloring(G: nx.Graph, coloring: Dict[Hashable, int]) -> bool:
    """
    Checks whether a coloring is valid for the original graph.
    """

    if set(coloring.keys()) != set(G.nodes):
        return False

    for u, v in G.edges:
        if coloring[u] == coloring[v]:
            return False

    return True


def number_of_colors(coloring: Dict[Hashable, int]) -> int:
    return len(set(coloring.values()))


def is_complete_graph(G: nx.Graph) -> bool:
    n = G.number_of_nodes()
    return G.number_of_edges() == n * (n - 1) // 2


def get_branching_vertices(G: nx.Graph) -> Optional[Tuple[Bag, Bag]]:
    """
    Chooses two non-adjacent vertices for branching.

    Strategy:
    - compute maximal cliques;
    - score each node by the largest maximal clique it belongs to;
    - sort nodes by decreasing score;
    - return the first non-adjacent pair.

    This is still simple, but much better than a random pair.
    """

    if G.number_of_nodes() <= 1:
        return None

    cliques = list(nx.find_cliques(G))

    score = {v: 0 for v in G.nodes}

    for clique in cliques:
        clique_size = len(clique)
        for v in clique:
            score[v] = max(score[v], clique_size)

    nodes = sorted(
        G.nodes,
        key=lambda v: (score[v], G.degree[v], len(v)),
        reverse=True,
    )

    for i, u in enumerate(nodes):
        for v in nodes[i + 1 :]:
            if not G.has_edge(u, v):
                return u, v

    return None


def same_color_branch(G: nx.Graph, u: Bag, v: Bag) -> nx.Graph:
    """
    Branch where u and v receive the same color.

    Since u and v are non-adjacent in the current graph, they may be contracted.
    The new node is u union v.
    """

    if G.has_edge(u, v):
        raise ValueError("Cannot contract adjacent bags in the same-color branch.")

    H = nx.Graph()

    merged = frozenset(set(u) | set(v))

    def map_node(x: Bag) -> Bag:
        if x == u or x == v:
            return merged
        return x

    for x in G.nodes:
        H.add_node(map_node(x))

    for a, b in G.edges:
        aa = map_node(a)
        bb = map_node(b)

        if aa != bb:
            H.add_edge(aa, bb)

    return H


def different_color_branch(G: nx.Graph, u: Bag, v: Bag) -> nx.Graph:
    """
    Branch where u and v receive different colors.

    This is represented by adding an edge between them.
    """

    if G.has_edge(u, v):
        raise ValueError("Different-color branch received already adjacent bags.")

    H = G.copy()
    H.add_edge(u, v)
    return H


def serialize_bag(bag: Bag) -> list:
    """
    JSON-friendly representation of a bag.
    """

    return sorted(list(bag), key=str)


def write_jsonl_line(path: str, data: dict) -> None:
    """
    Appends one JSON object to a JSONL log file.
    """

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, default=str) + "\n")

        