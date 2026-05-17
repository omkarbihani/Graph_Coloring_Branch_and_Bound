from .abstract_cliques import AbstractClique, CliqueResult
from typing import Set, Hashable, Tuple, Optional
import numpy as np
from dwave.samplers import SimulatedAnnealingSampler, SteepestDescentSampler
import networkx as nx

class SAClique(AbstractClique):
    """
    Uses QUBO formalism to calcute the clique.

    This is a heuristic, so it gives a valid lower bound for the chromatic number,
    but not necessarily the exact clique number.
    """

    def __init__(
            self, 
            num_reads = 1000,
            use_steepest_descent: bool = True,
            expand: bool = True
        ):
        self.num_reads = num_reads
        self.use_steepest_descent = use_steepest_descent
        self.expand = expand
        self.sampleset = None

    @staticmethod
    def _is_clique(G, nodes):
        """
        Check whether the given node set is a clique in G.
        """
        nodes = list(nodes)
        k = len(nodes)
        if k <= 1:
            return True

        sub = G.subgraph(nodes)
        return sub.number_of_edges() == k * (k - 1) // 2
    
    @staticmethod
    def _repair_to_clique(G, candidate_nodes):
        """
        Convert an arbitrary set of nodes into a valid clique by removing
        nodes that create conflicts.

        Strategy:
        - Work on the induced subgraph.
        - While it is not a clique, remove a node with the largest number of
        non-neighbors inside the candidate set.
        - Ties are broken by lower degree in the original graph.
        """
        clique = set(candidate_nodes)

        while len(clique) > 1:
            badness = {}

            for u in clique:
                conflicts = 0
                for v in clique:
                    if u != v and not G.has_edge(u, v):
                        conflicts += 1
                badness[u] = conflicts

            max_conflicts = max(badness.values())

            if max_conflicts == 0:
                break

            worst_nodes = [u for u, c in badness.items() if c == max_conflicts]

            # Tie-break: remove the node with smallest original graph degree.
            remove_node = min(worst_nodes, key=lambda u: G.degree[u])
            clique.remove(remove_node)

        return clique

    @staticmethod
    def _greedily_expand_clique(G, clique):
        """
        Try to enlarge a valid clique by adding nodes adjacent to all nodes
        already in the clique.

        Nodes are considered in descending degree order.
        """
        clique = set(clique)

        candidates = set(G.nodes) - clique

        candidates = sorted(
            candidates,
            key=lambda u: G.degree[u],
            reverse=True
        )

        for u in candidates:
            if all(G.has_edge(u, v) for v in clique):
                clique.add(u)

        return clique


    def sample_clique_qubo(
        self,
        G: nx.Graph,
    )-> Tuple[Set[Hashable], Optional[object]]:
        """
        Heuristic maximum clique finder using QUBO sampling plus deterministic repair.

        Returns
        -------
        best_clique : set
            A valid clique in G.
        sampleset :
            The final sampleset returned by the sampler.
        """
        nodes = sorted(G.nodes)
        n = len(nodes)

        if n == 0:
            return set(), None

        if n == 1:
            return {nodes[0]}, None

        # Complement graph: non-edges in G become edges in complement(G).
        G_comp = nx.complement(G)

        adj_comp = nx.to_numpy_array(
            G_comp,
            nodelist=nodes,
            dtype=float
        )

        # Energy:
        #   sum_{non-edge pairs} x_i x_j - 0.5 * sum_i x_i
        #
        # The first term penalizes selecting non-adjacent vertices.
        # The second term rewards selecting more vertices.
        #
        # This QUBO may still produce invalid cliques, so we repair every sample.

        Q = 0.5 * (adj_comp - np.eye(n))

        sampler = SimulatedAnnealingSampler()
        sampleset = sampler.sample_qubo(Q, num_reads=self.num_reads)

        if self.use_steepest_descent:
            sampleset = SteepestDescentSampler().sample_qubo(Q, initial_states=sampleset)

        best_clique = set()

        for sample, energy in sampleset.data(fields=["sample", "energy"]):
            candidate = {
                nodes[i]
                for i in range(n)
                if sample[i] == 1
            }

            repaired = self._repair_to_clique(G, candidate)

            if self.expand:
                repaired = self._greedily_expand_clique(G, repaired)

            if len(repaired) > len(best_clique):
                best_clique = repaired

        assert self._is_clique(G, best_clique), "Postprocessing failed: result is not a clique."

        return best_clique, sampleset
    

    def __call__(self, G) -> CliqueResult:
        clique, self.sampleset = self.sample_clique_qubo(G)
        return CliqueResult(
            clique=clique,
            clique_number=len(clique)
        )
    
