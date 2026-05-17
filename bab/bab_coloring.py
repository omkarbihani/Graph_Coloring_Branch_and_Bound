from __future__ import annotations

import heapq
import time
from typing import Dict, Hashable, Optional

import networkx as nx

from .babnode import ColoringBaBNode, Bag
from .bab_utils import (
    make_initial_bag_graph,
    expand_bag_coloring,
    validate_coloring,
    number_of_colors,
    get_branching_vertices,
    same_color_branch,
    different_color_branch,
    write_jsonl_line,
    serialize_bag,
)

import sys
sys.path.append("..")
from heuristics.cliques.networkx_cliques import AbstractClique
from heuristics.coloring.networkx_coloring import AbstractColoring


class BranchAndBoundColoringSolver:
    """
    Sequential Branch-and-Bound solver for the chromatic number.

    Branching rule:
    - pick two non-adjacent bags u, v;
    - branch 1: u and v have the same color, represented by contraction;
    - branch 2: u and v have different colors, represented by adding edge uv.

    Bounds:
    - lower bound: heuristic clique size;
    - upper bound: greedy coloring.
    """

    def __init__(
        self,
        G: nx.Graph,
        coloring_heuristic: AbstractColoring,
        clique_heuristic: AbstractClique,
        time_limit: Optional[float] = None,
        log_path: Optional[str] = None,
        verbose: bool = False,
    ):
        self.original_graph = G.copy()
        self.root_graph = make_initial_bag_graph(G)

        self.coloring_heuristic = coloring_heuristic
        self.clique_heuristic = clique_heuristic

        self.time_limit = time_limit
        self.log_path = log_path
        self.verbose = verbose

        self.start_time: float = 0.0
        self.next_node_id: int = 0

        self.best_ub: int = G.number_of_nodes()
        self.best_coloring: Dict[Hashable, int] = {
            v: i for i, v in enumerate(G.nodes)
        }

        self.best_lb: int = 0
        self.nodes_processed: int = 0
        self.nodes_pruned: int = 0
        self.nodes_created: int = 0

    def solve(self) -> dict:
        """
        Runs the Branch-and-Bound algorithm.

        Returns a dictionary containing:
        - chromatic_number_upper_bound
        - chromatic_number_lower_bound
        - proven_optimal
        - coloring
        - runtime
        - node statistics
        """

        self.start_time = time.time()

        root = self._create_node(
            graph=self.root_graph,
            level=0,
            parent_id=None,
            branch_type="root",
            branch_vertices=None,
        )

        self.best_ub = root.ub
        self.best_coloring = expand_bag_coloring(root.coloring)
        self.best_lb = root.lb

        queue: list[ColoringBaBNode] = []
        heapq.heappush(queue, root)

        while queue:
            if self._time_limit_reached():
                break

            node = heapq.heappop(queue)
            self.nodes_processed += 1

            # self.best_lb = max(self.best_lb, node.lb)
            self.best_lb = min(self.best_lb, node.lb)

            if self.verbose:
                print(node)

            if node.lb >= self.best_ub:
                node.status = "pruned_by_bound"
                self.nodes_pruned += 1
                self._log_node(node)
                continue

            if node.lb == node.ub:
                node.status = "solved_by_bounds"

                if node.ub < self.best_ub:
                    self._update_incumbent(node)

                self._log_node(node)
                continue

            pair = get_branching_vertices(node.graph)

            if pair is None:
                # No non-edge remains, so the current graph is complete.
                node.status = "complete_graph"

                if node.graph.number_of_nodes() < self.best_ub:
                    complete_coloring = {
                        bag: color for color, bag in enumerate(node.graph.nodes)
                    }
                    node.coloring = complete_coloring
                    node.ub = node.graph.number_of_nodes()
                    self._update_incumbent(node)

                self._log_node(node)
                continue

            u, v = pair

            # Good practical ordering:
            # try same-color branch first, because it reduces the graph size.
            same_graph = same_color_branch(node.graph, u, v)
            same_node = self._create_node(
                graph=same_graph,
                level=node.level + 1,
                parent_id=node.node_id,
                branch_type="same",
                branch_vertices=(u, v),
            )

            diff_graph = different_color_branch(node.graph, u, v)
            diff_node = self._create_node(
                graph=diff_graph,
                level=node.level + 1,
                parent_id=node.node_id,
                branch_type="different",
                branch_vertices=(u, v),
            )

            for child in (same_node, diff_node):
                if child.ub < self.best_ub:
                    self._update_incumbent(child)

                if child.lb < self.best_ub:
                    heapq.heappush(queue, child)
                else:
                    child.status = "pruned_on_creation"
                    self.nodes_pruned += 1

                self._log_node(child)

        runtime = time.time() - self.start_time

        # proven_optimal = len(queue) == 0 and self.best_lb >= self.best_ub
        proven_optimal = len(queue) == 0 or self.best_lb >= self.best_ub

        is_valid = validate_coloring(self.original_graph, self.best_coloring)

        return {
            "chromatic_number": self.best_ub if proven_optimal else None,
            "best_upper_bound": self.best_ub,
            "best_lower_bound": min(self.best_lb, self.best_ub),
            "proven_optimal": proven_optimal,
            "coloring": self.best_coloring,
            "number_of_colors_in_coloring": number_of_colors(self.best_coloring),
            "valid_coloring": is_valid,
            "runtime_seconds": runtime,
            "nodes_processed": self.nodes_processed,
            "nodes_created": self.nodes_created,
            "nodes_pruned": self.nodes_pruned,
            "time_limit_reached": self._time_limit_reached(),
        }

    def _create_node(
        self,
        graph: nx.Graph,
        level: int,
        parent_id: Optional[int],
        branch_type: Optional[str],
        branch_vertices: Optional[tuple[Bag, Bag]],
    ) -> ColoringBaBNode:
        node_id = self.next_node_id
        self.next_node_id += 1
        self.nodes_created += 1

        clique_result = self.clique_heuristic(graph)
        clique = clique_result.clique
        lb = clique_result.clique_number

        coloring_result = self.coloring_heuristic(
            graph
        )
        coloring = coloring_result.coloring
        ub = coloring_result.number_of_colors

        node = ColoringBaBNode(
            node_id=node_id,
            level=level,
            graph=graph,
            parent_id=parent_id,
            branch_type=branch_type,
            branch_vertices=branch_vertices,
            lb=lb,
            ub=ub,
            coloring=coloring,
            clique=clique,
            status="open",
        )

        return node

    def _update_incumbent(self, node: ColoringBaBNode) -> None:
        original_coloring = expand_bag_coloring(node.coloring)

        if not validate_coloring(self.original_graph, original_coloring):
            raise RuntimeError(
                "Internal error: incumbent coloring is invalid for the original graph."
            )

        colors = number_of_colors(original_coloring)

        if colors < self.best_ub:
            self.best_ub = colors
            self.best_coloring = original_coloring

    def _time_limit_reached(self) -> bool:
        if self.time_limit is None:
            return False

        return time.time() - self.start_time >= self.time_limit

    def _log_node(self, node: ColoringBaBNode) -> None:
        if self.log_path is None:
            return

        branch_vertices = None
        if node.branch_vertices is not None:
            u, v = node.branch_vertices
            branch_vertices = {
                "u": serialize_bag(u),
                "v": serialize_bag(v),
            }

        data = {
            "node_id": node.node_id,
            "parent_id": node.parent_id,
            "level": node.level,
            "status": node.status,
            "branch_type": node.branch_type,
            "branch_vertices": branch_vertices,
            "lb": node.lb,
            "ub": node.ub,
            "num_graph_nodes": node.graph.number_of_nodes(),
            "num_graph_edges": node.graph.number_of_edges(),
            "clique": [serialize_bag(bag) for bag in node.clique],
            "coloring": {
                str(serialize_bag(bag)): color
                for bag, color in node.coloring.items()
            },
            "elapsed_seconds": time.time() - self.start_time,
            "current_best_ub": self.best_ub,
        }

        write_jsonl_line(self.log_path, data)


        