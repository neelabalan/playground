- Computational Efficiency
    - Working with a spanning graph, which has fewer edges, can lead to improved computational efficiency for graph algorithms and analysis. Many algorithms have time complexity that depends on the number of edges.
- Optimization and Simplification
    - Spanning graphs, especially minimum spanning trees, can simplify the structure of the original graph while preserving important connectivity properties. This can be useful for optimization problems, network design, and other applications.

```
❯ python bench.py --nodes 1000
2024-04-14 11:07:47,421 - INFO - Original Graph:
2024-04-14 11:07:47,715 - INFO - Number of components: 1
2024-04-14 11:07:47,715 - INFO - Diameter: 23
2024-04-14 11:07:47,715 - INFO - Average clustering coefficient: 0.0
2024-04-14 11:07:47,715 - INFO - Computation time: 0.29365 seconds
2024-04-14 11:07:47,719 - INFO - Spanning Tree:
2024-04-14 11:07:47,949 - INFO - Number of components: 1
2024-04-14 11:07:47,949 - INFO - Diameter: 23
2024-04-14 11:07:47,949 - INFO - Average clustering coefficient: 0.0
2024-04-14 11:07:47,949 - INFO - Computation time: 0.22944 seconds
2024-04-14 11:07:47,949 - INFO - Original graph computation time: 0.29365 seconds
2024-04-14 11:07:47,949 - INFO - Spanning tree computation time: 0.22944 seconds
2024-04-14 11:07:47,949 - INFO - The spanning tree is easier to compute.
```