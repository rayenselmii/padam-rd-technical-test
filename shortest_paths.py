from __future__ import annotations

import heapq

from graph import Graph

# adjacency[v] = list of (neighbor, weight, edge id)
Adjacency = list[list[tuple[int, int, int]]]


def build_adjacency(graph: Graph) -> Adjacency:
    """Adjacency lists of the graph, keeping edge ids (parallel edges stay distinct)."""
    adjacency: Adjacency = [[] for _ in graph.vertices]
    for i, (u, v, weight, *_) in enumerate(graph.edges):
        adjacency[u].append((v, weight, i))
        adjacency[v].append((u, weight, i))
    return adjacency


def connected_components(adjacency: Adjacency) -> list[int]:
    """Component id of each vertex."""
    component = [-1] * len(adjacency)
    current = 0
    for start in range(len(adjacency)):
        if component[start] != -1:
            continue
        component[start] = current
        stack = [start]
        while stack:
            vertex = stack.pop()
            for neighbor, *_ in adjacency[vertex]:
                if component[neighbor] == -1:
                    component[neighbor] = current
                    stack.append(neighbor)
        current += 1
    return component


def odd_vertices(adjacency: Adjacency) -> list[int]:
    """Vertices with an odd degree."""
    return [v for v, neighbors in enumerate(adjacency) if len(neighbors) % 2 == 1]


def dijkstra(
    adjacency: Adjacency,
    source: int,
    targets: set[int],
    max_targets: int | None = None,
) -> tuple[dict[int, int], dict[int, tuple[int, int]]]:
    """Shortest paths from `source`, stopped early once `max_targets` targets are reached.

    Parameters
    ----------
    adjacency : Adjacency
        Graph adjacency lists.
    source : int
        Starting vertex.
    targets : set[int]
        Vertices we want to reach (the source itself is ignored).
    max_targets : int | None
        Stop after settling this many targets; None explores the whole component.

    Returns
    -------
    tuple[dict[int, int], dict[int, tuple[int, int]]]
        distance of each reached target, and parent (previous vertex, edge id)
        of each settled vertex to rebuild paths.
    """
    distance = {source: 0}
    parent: dict[int, tuple[int, int]] = {}
    settled = set()
    found: dict[int, int] = {}
    heap = [(0, source)]
    while heap:
        d, vertex = heapq.heappop(heap)
        if vertex in settled:
            continue
        settled.add(vertex)
        if vertex in targets and vertex != source:
            found[vertex] = d
            if max_targets is not None and len(found) >= max_targets:
                break
        for neighbor, weight, edge_id in adjacency[vertex]:
            new_distance = d + weight
            if new_distance < distance.get(neighbor, float("inf")):
                distance[neighbor] = new_distance
                parent[neighbor] = (vertex, edge_id)
                heapq.heappush(heap, (new_distance, neighbor))
    return found, parent


def path_edges(parent: dict[int, tuple[int, int]], source: int, target: int) -> list[int]:
    """Edge ids of the shortest path from `source` to `target`, read back from `parent`."""
    edges = []
    vertex = target
    while vertex != source:
        vertex, edge_id = parent[vertex]
        edges.append(edge_id)
    return edges
