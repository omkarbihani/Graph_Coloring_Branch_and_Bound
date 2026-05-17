from .abstract_cliques import AbstractClique, CliqueResult

import networkx as nx


class NetworkxClique(AbstractClique):
    """
    Uses NetworkX approximation.max_clique.

    This is a heuristic, so it gives a valid lower bound for the chromatic number,
    but not necessarily the exact clique number.
    """

    def __call__(self, G):

        clique = set(nx.approximation.max_clique(G))
        return CliqueResult(
            clique=clique,
            clique_number=len(clique)
        )


