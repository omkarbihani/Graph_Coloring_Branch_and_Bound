from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Hashable, Optional, FrozenSet

import networkx as nx


Bag = FrozenSet[Hashable]


@dataclass(order=False)
class ColoringBaBNode:
    """
    Node in the Branch-and-Bound tree for graph coloring.

    The graph stored in this node is a quotient/constraint graph.

    Each node of `graph` is a frozenset of original vertices.
    If a graph node is frozenset({1, 4, 9}), then original vertices
    1, 4, and 9 are constrained to have the same color.
    """

    node_id: int
    level: int
    graph: nx.Graph
    parent_id: Optional[int] = None
    branch_type: Optional[str] = None
    branch_vertices: Optional[tuple[Bag, Bag]] = None

    lb: int = 0
    ub: int = 0
    coloring: Dict[Bag, int] = field(default_factory=dict)
    clique: set[Bag] = field(default_factory=set)
    status: str = "open"

    def __lt__(self, other: ColoringBaBNode) -> bool:
        """
        Priority queue ordering.

        Prefer nodes with larger lower bound first.
        If tied, prefer deeper nodes.
        """
        if self.lb != other.lb:
            return self.lb > other.lb

        return self.level > other.level

    def is_complete_graph(self) -> bool:
        n = self.graph.number_of_nodes()
        return self.graph.number_of_edges() == n * (n - 1) // 2

    def summary(self) -> dict:
        return {
            "node_id": self.node_id,
            "parent_id": self.parent_id,
            "level": self.level,
            "lb": self.lb,
            "ub": self.ub,
            "status": self.status,
            "branch_type": self.branch_type,
            "branch_vertices": self.branch_vertices,
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
        }

    def __repr__(self) -> str:
        return (
            f"ColoringBaBNode("
            f"id={self.node_id}, "
            f"parent={self.parent_id}, "
            f"level={self.level}, "
            f"lb={self.lb}, "
            f"ub={self.ub}, "
            f"status={self.status}, "
            f"|V|={self.graph.number_of_nodes()}, "
            f"|E|={self.graph.number_of_edges()}"
            f")"
        )
    
    