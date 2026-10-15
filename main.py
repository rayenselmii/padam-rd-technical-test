import time

from input import parse_cmd_line, parse_file
from graph import Graph
from solution import solve

MILP_TIME_LIMIT = 60  # seconds


def main():
    in_file, plot_graph, run_milp = parse_cmd_line()
    vertices, edges = parse_file(in_file)
    print(f"#E={len(edges)}, #V={len(vertices)}")
    graph = Graph(vertices, edges)

    # one path per connected component (the graph may not be connected)
    start = time.perf_counter()
    paths, lower_bound = solve(graph)
    duration = time.perf_counter() - start
    value = sum(edge[2] for path in paths for edge in path)

    print(f"Number of paths found : {len(paths)}")
    print(f"Length of paths found : {[len(path) + 1 for path in paths]}")
    print(f"Value of paths found  : {value} ({duration:.2f}s)")
    print(f"Lower bound           : {lower_bound:g} (gap <= {100 * (value - lower_bound) / lower_bound:.1f}%)")

    if run_milp:
        from milp_solution import solve_duplications  # optional: needs PuLP

        start = time.perf_counter()
        duplications = solve_duplications(graph, time_limit=MILP_TIME_LIMIT)
        duration = time.perf_counter() - start
        if duplications is None:
            print(f"MILP optimum          : not found within {MILP_TIME_LIMIT}s")
        else:
            optimum = sum(edge[2] * (1 + k) for edge, k in zip(edges, duplications))
            print(f"MILP optimum          : {optimum} ({duration:.2f}s, gap = {100 * (value - optimum) / optimum:.1f}%)")

    if plot_graph:
        graph.plot()
        graph.display_paths(paths=paths)


if __name__ == "__main__":
    main()
