from __future__ import annotations

import pulp

from graph import Graph


def connected_components(graph: Graph) -> list[int]:
    """Label each vertex with the id of its connected component.

    Parameters
    ----------
    graph : Graph
        Input graph.

    Returns
    -------
    list[int]
        component id of each vertex.
    """
    adjacency = [[] for _ in graph.vertices]
    for u, v, *_ in graph.edges:
        adjacency[u].append(v)
        adjacency[v].append(u)

    component = [-1] * len(graph.vertices)
    current = 0
    for start in range(len(graph.vertices)):
        if component[start] != -1:
            continue
        component[start] = current
        stack = [start]
        while stack:
            vertex = stack.pop()
            for neighbor in adjacency[vertex]:
                if component[neighbor] == -1:
                    component[neighbor] = current
                    stack.append(neighbor)
        current += 1
    return component


def solve_duplications(graph: Graph, time_limit: int | None = None) -> list[int] | None:
    """Find a minimum-weight set of edges to duplicate so that each connected
    component has at most 2 odd-degree vertices (i.e. admits an Eulerian path).

    Model (one binary x_e per edge, at most one duplication is enough):
        min  sum_e w_e x_e
        s.t. deg(v) + sum_{e ∋ v} x_e - s_v = 2 z_v   for all v   (parity)
             sum_{v in C} s_v <= 2                    for all C   (path endpoints)
             x_e, s_v binary, z_v integer >= 0

    Parameters
    ----------
    graph : Graph
        Input graph.
    time_limit : int | None
        Optional CBC time limit in seconds.

    Returns
    -------
    list[int] | None
        number of duplications (0 or 1) for each edge, in the order of `graph.edges`,
        or None if no optimal solution was found within the time limit.
    """
    n = len(graph.vertices)
    degree = [0] * n
    incident = [[] for _ in range(n)]
    for i, (u, v, *_) in enumerate(graph.edges):
        degree[u] += 1
        degree[v] += 1
        incident[u].append(i)
        incident[v].append(i)

    model = pulp.LpProblem(sense=pulp.LpMinimize)
    x = [pulp.LpVariable(f"x_{i}", cat="Binary") for i in range(len(graph.edges))]
    s = [pulp.LpVariable(f"s_{v}", cat="Binary") for v in range(n)]
    z = [pulp.LpVariable(f"z_{v}", lowBound=0, cat="Integer") for v in range(n)]

    model += pulp.lpSum(edge[2] * x[i] for i, edge in enumerate(graph.edges))

    for v in range(n):
        if not incident[v]:
            continue  # isolated vertex: nothing to cover
        model += (
            degree[v] + pulp.lpSum(x[i] for i in incident[v]) - s[v] == 2 * z[v],
            f"parity_{v}",
        )

    component = connected_components(graph)
    for c in set(component):
        model += (
            pulp.lpSum(s[v] for v in range(n) if component[v] == c) <= 2,
            f"endpoints_{c}",
        )

    model.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit))
    if pulp.LpStatus[model.status] != "Optimal":
        return None  # TODO: return the best feasible solution found, if any

    return [round(var.value() or 0) for var in x]
