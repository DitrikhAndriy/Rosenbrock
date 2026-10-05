"""Directional minimization shared by the modified method."""

from math import isfinite

from dsc_powell import dsc_powell
from golden_section import golden_section
from optimization import Evaluator, Point, move
from sven import sven_method


def line_search(
    evaluator: Evaluator, x: Point, value: float, direction: Point,
    method: str, delta: float, epsilon: float, max_iterations: int,
) -> tuple[Point, float]:
    """Minimize along a unit direction; constrained slices must be convex."""
    values = {0.0: value}

    def phi(step: float) -> float:
        if step not in values:
            values[step] = evaluator(move(x, direction, step))
        return values[step]

    if evaluator.restriction is None:
        left, center, right = phi(-delta), value, phi(delta)
        if left == center == right:
            return x, value
        start = 0.0
        if left < center and right < center:
            start = -delta if left < right else delta
        if method == "golden":
            a, b = sven_method(phi, start, delta, max_iterations=max_iterations)
            step = golden_section(phi, a, b, epsilon, max_iterations=max_iterations)
        else:
            step = dsc_powell(phi, start, delta, epsilon, max_iterations=max_iterations)
    else:
        def extent(sign: int) -> float:
            previous, previous_value, step = 0.0, value, delta
            for _ in range(max_iterations):
                trial = sign * step
                if not isfinite(trial):
                    raise RuntimeError("Directional search overflow.")
                if not evaluator.feasible(move(x, direction, trial)):
                    inside, outside = previous, trial
                    for _ in range(max_iterations):
                        midpoint = inside + (outside - inside) / 2
                        if abs(outside - inside) <= epsilon / 4 or midpoint in (inside, outside):
                            return inside
                        if evaluator.feasible(move(x, direction, midpoint)):
                            inside = midpoint
                        else:
                            outside = midpoint
                    raise RuntimeError("Feasible-boundary iteration limit reached.")
                current_value = phi(trial)
                if current_value >= previous_value:
                    return trial
                previous, previous_value = trial, current_value
                step *= 2
            raise RuntimeError("Directional bracketing iteration limit reached.")

        a, b = extent(-1), extent(1)
        if b - a <= epsilon:
            step = min((0.0, a, b), key=phi)
        elif method == "golden":
            step = golden_section(phi, a, b, epsilon, max_iterations=max_iterations)
        else:
            step = dsc_powell(phi, 0, delta, epsilon, bounds=(a, b), max_iterations=max_iterations)
        step = min((0.0, a, b, step), key=phi)

    # Retain the best evaluated point, including the unchanged starting point.
    phi(step)
    best = min(values, key=values.__getitem__)
    if values[best] < value:
        return move(x, direction, best), values[best]
    return x, value
