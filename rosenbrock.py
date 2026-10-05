"""Two-dimensional Rosenbrock search with adaptive steps."""

from math import hypot, isfinite
from typing import Sequence

from boundary_refinement import finish

from optimization import Objective, OptimizationResult, Restriction, move, prepare, result, rotate, small_change


def rosenbrock(
    f: Objective,
    x0: Sequence[float],
    steps: Sequence[float] = (0.3, 1.2),
    epsilon: float = 1e-5,
    alpha: float = 3.0,
    beta: float = -0.5,
    *,
    restriction: Restriction | None = None,
    termination: str = "step",
    max_iterations: int = 10000,
) -> OptimizationResult:
    """Expand successful steps; reverse and shrink unsuccessful ones.

    Rotate after an unsuccessful sweep that follows stage progress.
    restriction(x) must return True for feasible points.
    iterations counts sweeps; path contains accepted points.
    """
    evaluator, x, value, epsilon = prepare(f, x0, epsilon, max_iterations, termination, restriction)
    if len(steps) != 2:
        raise ValueError("steps must contain two nonzero values.")
    steps = [float(step) for step in steps]
    if not all(isfinite(step) and step != 0 for step in steps):
        raise ValueError("steps must be nonzero and finite.")
    alpha, beta = float(alpha), float(beta)
    if not isfinite(alpha) or alpha <= 1:
        raise ValueError("alpha must be finite and greater than 1.")
    if not isfinite(beta) or not -1 < beta < 0:
        raise ValueError("beta must satisfy -1 < beta < 0.")

    directions = ((1.0, 0.0), (0.0, 1.0))
    stage_start, stage_value = x, value
    path = [x]
    for iteration in range(1, max_iterations + 1):
        successes = 0
        for index, direction in enumerate(directions):
            trial = move(x, direction, steps[index])
            trial_value = evaluator(trial) if trial != x and evaluator.feasible(trial) else None
            if trial_value is not None and trial_value < value:
                x, value = trial, trial_value
                path.append(x)
                steps[index] *= alpha
                successes += 1
            else:
                steps[index] *= beta

        if not successes:
            step_size = hypot(*steps)
            if termination == "step":
                converged = step_size <= epsilon
            else:
                converged = (
                    step_size <= epsilon * max(1.0, hypot(*x))
                    and small_change(x, stage_start, value, stage_value, epsilon)
                )
            if converged:
                return finish(evaluator, x, value, path, iteration, epsilon, max_iterations)
            displacement = x[0] - stage_start[0], x[1] - stage_start[1]
            directions = rotate(displacement, directions)
            stage_start, stage_value = x, value

    return result(evaluator, x, value, path, max_iterations, False)
