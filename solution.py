from __future__ import annotations

from eulerian import check_path, hierholzer
from graph import Edge, Graph
from matching import (
    candidate_distances,
    drop_worst_pairs,
    greedy_matching,
    improve_matching,
    matching_lower_bound,
)
from shortest_paths import (
    build_adjacency,
    connected_components,
    dijkstra,
    odd_vertices,
    path_edges,
)


def solve(graph: Graph) -> tuple[list[list[Edge]], float]:
    """Compute one path per connected component covering all its edges.

    Steps: pair odd vertices (greedy), duplicate the edges of the shortest path
    of each pair, then build an Eulerian path per component (Hierholzer).

    Parameters
    ----------
    graph : Graph
        Input graph.

    Returns
    -------
    tuple[list[list[Edge]], float]
        One path per connected component having edges, and a lower bound on
        the optimal total cost.
    """
    adjacency = build_adjacency(graph)
    component = connected_components(adjacency)
    odd = odd_vertices(adjacency)
    distances = candidate_distances(adjacency, odd)
    pairs = greedy_matching(adjacency, odd, distances)
    pairs = drop_worst_pairs(pairs, component)
    paired = {v for a, b, _ in pairs for v in (a, b)}
    pairs = improve_matching(pairs, [v for v in odd if v not in paired], distances)

    # every edge once, plus one copy per edge on the shortest path of each pair
    edge_ids = list(range(len(graph.edges)))
    for a, b, _ in pairs:
        _, parent = dijkstra(adjacency, a, {b}, max_targets=1)
        edge_ids.extend(path_edges(parent, a, b))

    ids_by_component: dict[int, list[int]] = {}
    for i in edge_ids:
        ids_by_component.setdefault(component[graph.edges[i][0]], []).append(i)

    paths = []
    for ids in ids_by_component.values():
        degree: dict[int, int] = {}
        for i in ids:
            for v in graph.edges[i][:2]:
                degree[v] = degree.get(v, 0) + 1
        odd = [v for v, d in degree.items() if d % 2 == 1]
        start = odd[0] if odd else graph.edges[ids[0]][0]
        path = hierholzer(graph, ids, start)
        check_path(graph, path, ids)
        paths.append(path)

    lower_bound = sum(edge[2] for edge in graph.edges) + matching_lower_bound(distances, component)
    return paths, lower_bound
