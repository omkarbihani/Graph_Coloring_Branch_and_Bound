from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Set, Hashable
import numpy as np

import networkx as nx

@dataclass(frozen=True)
class CliqueResult:
    clique: Set[Hashable]
    clique_number: int

class AbstractClique(ABC):
    """
    Abstract interface for clique heuristics.
    """

    def __call__(self, G: nx.Graph) -> CliqueResult:
        pass

    



