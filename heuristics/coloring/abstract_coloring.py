from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Hashable

import networkx as nx

@dataclass(frozen=True)
class ColoringResult:
    coloring: Dict[Hashable, int]
    number_of_colors: int

class AbstractColoring(ABC):
    """
    Abstract interface for graph coloring heuristics.
    """

    def __call__(self, G: nx.Graph) -> ColoringResult:
        pass

