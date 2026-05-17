from .abstract_coloring import AbstractColoring, ColoringResult

import networkx as nx


class NetworkxGreedyColoring(AbstractColoring):
    """
    Greedy NetworkX coloring heuristic.

    This gives a valid upper bound on the chromatic number.
    """

    def __init__(self, strategy: str = "largest_first"):
        self.strategy = strategy

    def __call__(self, G) -> ColoringResult:
        coloring = nx.algorithms.coloring.greedy_color(
            G,
            strategy=self.strategy
        ) 

        return ColoringResult(
            coloring=coloring,
            number_of_colors=len(set(coloring.values())),
        )