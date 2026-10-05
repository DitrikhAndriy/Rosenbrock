"""Two-dimensional Rosenbrock search with directional minimization."""

from math import hypot
from typing import Sequence

from boundary_refinement import finish

from line_search import line_search
from optimization import Objective, OptimizationResult, Restriction, positive, prepare, result, rotate, small_change


def rosenbrock_modified(
    f: Objective,
    x0: Sequence[float],
    epsilon: float = 1e-5,
    *,
    line_method: str = "golden",
    delta: float = 0.1,
    line_epsilon: float | None = None,
    restriction: Restriction | None = None,
    termination: str = "step",
    max_iterations: int = 10000,
    line_max_iterations: int = 1000,
) -> OptimizationResult:
    """Minimize along each direction, then rotate toward total progress.

    restriction(x) must return True; the feasible set must be convex.
    delta is an absolute step, independent of the distance to the origin.
    iterations counts sweeps; path contains accepted points.
    """
    evaluator, x, value, epsilon = prepare(f, x0, epsilon, max_iterations, termination, restriction)
    if line_method not in ("golden", "dsc_powell"):
        raise ValueError("line_method must be 'golden' or 'dsc_powell'.")
    delta = positive(delta, "delta")
    line_epsilon = positive(epsilon / 10 if line_epsilon is None else line_epsilon, "line_epsilon")
    if line_epsilon > epsilon:
        raise ValueError("line_epsilon must not exceed epsilon.")
    if isinstance(line_max_iterations, bool) or not isinstance(line_max_iterations, int) or line_max_iterations <= 0:
        raise ValueError("line_max_iterations must be a positive integer.")

    directions = ((1.0, 0.0), (0.0, 1.0))
    path = [x]
    for iteration in range(1, max_iterations + 1):
        previous, previous_value = x, value
        for direction in directions:
            new_x, new_value = line_search(
                evaluator, x, value, direction, line_method, delta,
                line_epsilon, line_max_iterations,
            )
            if new_x != x:
                path.append(new_x)
            x, value = new_x, new_value

        displacement = x[0] - previous[0], x[1] - previous[1]
        if termination == "step":
            converged = hypot(*displacement) <= epsilon
        else:
            converged = small_change(x, previous, value, previous_value, epsilon)
        if converged:
            return finish(evaluator, x, value, path, iteration, epsilon, max_iterations)
        directions = rotate(displacement, directions)

    return result(evaluator, x, value, path, max_iterations, False)
