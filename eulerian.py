from __future__ import annotations

from graph import Edge, Graph


def hierholzer(
    graph: Graph, edge_ids: list[int], start: int
) -> list[Edge]:
    """Build an Eulerian path using every edge of `edge_ids` exactly once.

    `edge_ids` are indices in `graph.edges` and may contain the same index
    several times (duplicated edges). The multigraph they form must be
    connected and have 0 or 2 odd vertices; if 2, `start` must be one of them.

    Parameters
    ----------
    graph : Graph
        Input graph.
    edge_ids : list[int]
        Indices of the edges to traverse (with repetitions for duplications).
    start : int
        Starting vertex.

    Returns
    -------
    list[Edge]
        Edges in travel order, oriented (from, to, weight, coord from, coord to).
    """
    # adjacency[v] = list of (neighbor, slot) where slot indexes `edge_ids`,
    # so that two copies of the same edge are two distinct slots
    adjacency: dict[int, list[tuple[int, int]]] = {}
    for slot, i in enumerate(edge_ids):
        u, v = graph.edges[i][0], graph.edges[i][1]
        adjacency.setdefault(u, []).append((v, slot))
        adjacency.setdefault(v, []).append((u, slot))

    used = [False] * len(edge_ids)
    pointer = {v: 0 for v in adjacency}  # next entry to inspect in adjacency[v]

    # iterative version (recursion would overflow on paris_map)
    stack = [(start, -1)]  # (vertex, slot used to reach it)
    circuit: list[tuple[int, int]] = []
    while stack:
        vertex, _ = stack[-1]
        neighbors = adjacency.get(vertex, [])
        while pointer[vertex] < len(neighbors) and used[neighbors[pointer[vertex]][1]]:
            pointer[vertex] += 1
        if pointer[vertex] < len(neighbors):
            neighbor, slot = neighbors[pointer[vertex]]
            used[slot] = True
            stack.append((neighbor, slot))
        else:
            circuit.append(stack.pop())
    circuit.reverse()

    if len(circuit) - 1 != len(edge_ids):
        raise ValueError("Edges are not connected or have more than 2 odd vertices")

    path = []
    for (u, _), (v, slot) in zip(circuit, circuit[1:]):
        weight = graph.edges[edge_ids[slot]][2]
        path.append((u, v, weight, graph.vertices[u], graph.vertices[v]))
    return path


def check_path(graph: Graph, path: list[Edge], edge_ids: list[int]) -> None:
    """Assert that `path` is a valid walk traversing each slot of `edge_ids` once."""
    for previous, current in zip(path, path[1:]):
        assert previous[1] == current[0], "path is not continuous"
    expected: dict[tuple[int, int, int], int] = {}
    for i in edge_ids:
        u, v, w = graph.edges[i][:3]
        key = (min(u, v), max(u, v), w)
        expected[key] = expected.get(key, 0) + 1
    for u, v, w, *_ in path:
        key = (min(u, v), max(u, v), w)
        expected[key] -= 1
    assert all(count == 0 for count in expected.values()), "edges missing or extra"
