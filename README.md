# Branch-and-Bound Graph Coloring

This repository implements a sequential branch-and-bound solver for the graph coloring problem. Given an input graph \(G\), the solver searches for the chromatic number \(\chi(G)\), the minimum number of colors needed to assign colors to vertices so that adjacent vertices receive different colors.


## Project Structure

```text
.
├── bab/
│   ├── bab_coloring.py          
│   ├── bab_utils.py            
│   └── babnode.py              
|  
├── heuristics/
|   |
│   ├── cliques/
|   |   ├── abstract_cliques.py   
|   |   ├── networkx_cliques.py   
|   |   └── sampler_cliques.py   
|   |
│   └── coloring/    
|       ├── abstract_coloring.py 
|       └── networkx_coloring.py 
|  
├── dimacs_graphs/               
|  
├── notebooks/ 
│   ├── test_bab.ipynb            
│   ├── test_clique.ipynb            
│   └── test_coloring.ipynb                   
|  
├── utils.py                    
└── requirements.txt                    
```

## Algorithm Overview
The solver represents each search node as a constraint graph whose vertices are bags of original graph vertices.

At each branch-and-bound node:
1. A lower bound is computed from a clique heuristic.
2. An upper bound is computed from a coloring heuristic.
3. If the lower bound reaches the incumbent upper bound, the node is pruned.
4. Otherwise, the solver chooses two non-adjacent bags u and v and branches:
    - same-color branch: contract u and v
    - different-color branch: add an edge between u and v

When all open branches are resolved, the best valid coloring gives the chromatic number if optimality was proven.

## Usage
```
import networkx as nx
from bab.bab_coloring import BranchAndBoundColoringSolver
from heuristics.cliques.networkx_cliques import NetworkxClique
from heuristics.coloring.networkx_coloring import NetworkxGreedyColoring

G = nx.grid_2d_graph(m=9, n=9, periodic=True)

solver = BranchAndBoundColoringSolver(
    G,
    coloring_heuristic=NetworkxGreedyColoring(),
    clique_heuristic=NetworkxClique(),
    time_limit=60,
    log_path="bab_log.json",
    verbose=False,
)

result = solver.solve()
```

## To Do
1. Logging
2. Branching strategies
3. SDP bounds
4. MPI
5. Benchmarking
6. ... 