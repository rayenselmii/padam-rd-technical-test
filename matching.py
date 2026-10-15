from __future__ import annotations

from shortest_paths import Adjacency, dijkstra

Pair = tuple[int, int, int]  # (odd vertex a, odd vertex b, distance)
# distances[a][b] = shortest path distance, only for the candidate pairs computed
Distances = dict[int, dict[int, int]]


def candidate_distances(adjacency: Adjacency, odd: list[int], neighbors: int = 10) -> Distances:
    """Distances from each odd vertex to its `neighbors` closest odd vertices (symmetric)."""
    targets = set(odd)
    distances: Distances = {a: {} for a in odd}
    for a in odd:
        found, _ = dijkstra(adjacency, a, targets, max_targets=neighbors)
        for b, d in found.items():
            distances[a][b] = d
            distances[b][a] = d
    return distances


def greedy_matching(adjacency: Adjacency, odd: list[int], distances: Distances) -> list[Pair]:
    """Pair odd vertices greedily, closest pairs first.

    Candidate pairs are the ones in `distances`. Vertices left alone at the end
    are paired with the closest still-free odd vertex (added to `distances`).

    Parameters
    ----------
    adjacency : Adjacency
        Graph adjacency lists.
    odd : list[int]
        Odd-degree vertices.
    distances : Distances
        Candidate pairs distances, completed in place for leftover pairs.

    Returns
    -------
    list[Pair]
        Chosen pairs (a, b, shortest path distance).
    """
    candidates = sorted(
        (d, a, b) for a in odd for b, d in distances[a].items() if a < b
    )

    free = set(odd)
    pairs: list[Pair] = []
    for d, a, b in candidates:
        if a in free and b in free:
            pairs.append((a, b, d))
            free -= {a, b}

    # leftovers: their close candidates were all taken, search among free ones only
    for a in sorted(free):
        if a not in free:
            continue
        found, _ = dijkstra(adjacency, a, free, max_targets=1)
        if not found:
            continue  # TODO: alone in its component, cannot happen (even count per component)
        b, d = next(iter(found.items()))
        distances[a][b] = d
        distances[b][a] = d
        pairs.append((a, b, d))
        free -= {a, b}
    return pairs


def matching_lower_bound(distances: Distances, component: list[int]) -> float:
    """Lower bound on the cost of any valid set of duplications.

    Each paired odd vertex v is the end of a duplicated path of length at least
    nearest(v) (distance to its closest odd vertex), and each path has 2 ends:
    cost >= sum(nearest(v)) / 2. Up to 2 odd vertices per component stay
    unpaired, so the 2 largest nearest(v) of each component are left out.
    """
    nearest_by_component: dict[int, list[int]] = {}
    for a, neighbors in distances.items():
        nearest_by_component.setdefault(component[a], []).append(min(neighbors.values()))
    total = 0
    for nearest in nearest_by_component.values():
        total += sum(sorted(nearest)[:-2])
    return total / 2


def improve_matching(pairs: list[Pair], endpoints: list[int], distances: Distances) -> list[Pair]:
    """Local search on the matching, until no move improves it.

    For a pair (a, b) and a close odd vertex c of a:
    - if c is paired with d: replace (a, b), (c, d) by (a, c), (b, d);
    - if c is a path endpoint: replace (a, b) by (a, c), b becomes the endpoint.
    Only distances already in `distances` are used (no new Dijkstra).

    Parameters
    ----------
    pairs : list[Pair]
        Current matching.
    endpoints : list[int]
        Odd vertices left unpaired (path endpoints).
    distances : Distances
        Candidate pairs distances.

    Returns
    -------
    list[Pair]
        Improved matching.
    """
    partner: dict[int, int | None] = {v: None for v in endpoints}
    for a, b, _ in pairs:
        partner[a], partner[b] = b, a

    improved = True
    while improved:
        improved = False
        for a in partner:
            b = partner[a]
            if b is None:
                continue
            d_ab = distances[a][b]
            for c, d_ac in distances[a].items():
                if d_ac >= d_ab or c == b:
                    continue
                d = partner[c]
                if d is None:  # c is an endpoint: a goes with c, b becomes endpoint
                    partner[a], partner[c], partner[b] = c, a, None
                    improved = True
                    break
                d_bd = distances[b].get(d)
                if d_bd is not None and d_ac + d_bd < d_ab + distances[c][d]:
                    partner[a], partner[c], partner[b], partner[d] = c, a, d, b
                    improved = True
                    break

    return [(a, b, distances[a][b]) for a, b in partner.items() if b is not None and a < b]


def drop_worst_pairs(pairs: list[Pair], component: list[int]) -> list[Pair]:
    """Remove the most expensive pair of each connected component.

    The path does not need to be closed: the 2 vertices of the removed pair
    stay odd and become the endpoints of the component's path.
    """
    worst: dict[int, Pair] = {}
    for pair in pairs:
        c = component[pair[0]]
        if c not in worst or pair[2] > worst[c][2]:
            worst[c] = pair
    dropped = set(worst.values())
    return [pair for pair in pairs if pair not in dropped]
