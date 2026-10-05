"""DSC-Powell search with safeguarded parabolic interpolation."""

from math import isfinite
from typing import Callable

from sven import sven_method
from golden_section import golden_section


def _parabolic_minimum(
    a: float, x: float, b: float, fa: float, fx: float, fb: float
) -> float | None:
    """Return the quadratic vertex, or None for a degenerate fit."""
    left_value, right_value = fa - fx, fb - fx
    scale = max(left_value, right_value)
    if not isfinite(scale) or scale <= 0:
        return None

    width = b - a
    left, right = (x - a) / width, (b - x) / width
    left_value, right_value = left_value / scale, right_value / scale
    denominator = right * left_value + left * right_value
    if denominator <= 0:
        return None

    offset = (right**2 * left_value - left**2 * right_value) / denominator
    candidate = x + width * (offset / 2)
    return candidate if isfinite(candidate) else None


def dsc_powell(
    f: Callable[[float], float],
    x0: float,
    delta: float,
    epsilon: float,
    *,
    max_iterations: int = 1000,
    bounds: tuple[float, float] | None = None,
) -> float:
    """Bracket with Sven, then refine using quadratic interpolation.

    Requires unimodal f with finite values and a finite minimizer.
    epsilon bounds both coordinate and value changes for a parabolic step.
    A bracket of width <= epsilon also stops the search.
    These stopping criteria do not guarantee the distance to a minimizer.
    max_iterations applies separately to bracketing and refinement.
    bounds skips Sven; boundary minima use bounded golden-section search.
    """
    epsilon = float(epsilon)
    if not isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be positive and finite.")

    values: dict[float, float] = {}

    def evaluate(point: float) -> float:
        if point not in values:
            value = float(f(point))
            if not isfinite(value):
                raise ValueError("Function value must be finite.")
            values[point] = value
        return values[point]

    if bounds is None:
        a, b = sven_method(evaluate, x0, delta, max_iterations=max_iterations)
    else:
        if len(bounds) != 2:
            raise ValueError("bounds must contain two coordinates.")
        a, b = float(bounds[0]), float(bounds[1])
        if not isfinite(a) or not isfinite(b) or a > b or not isfinite(b - a):
            raise ValueError("bounds must be finite and ordered.")
        if isinstance(max_iterations, bool) or not isinstance(max_iterations, int) or max_iterations <= 0:
            raise ValueError("max_iterations must be a positive integer.")
        if a == b:
            evaluate(a)
            return a
    x = a + (b - a) / 2
    if not a < x < b:
        raise RuntimeError("Requested precision is unattainable with float.")
    fa, fx, fb = evaluate(a), evaluate(x), evaluate(b)
    if fx > min(fa, fb):
        if bounds is not None:
            candidate = golden_section(evaluate, a, b, epsilon, max_iterations=max_iterations)
            return min((a, candidate, b), key=evaluate)
        # Sven's sampled interior point preserves the minimum bracket.
        x = min((point for point in values if a < point < b), key=values.__getitem__)
        fx = values[x]

    previous_parabolic_improvement = False
    previous_step = b - a
    for _ in range(max_iterations):
        if b - a <= epsilon:
            return x

        candidate = _parabolic_minimum(a, x, b, fa, fx, fb)
        if candidate == x and previous_parabolic_improvement:
            return x
        parabolic = (
            candidate is not None
            and a < candidate < b
            and candidate != x
            and abs(candidate - x) <= previous_step / 2
        )
        if not parabolic:
            # Bisect the longer side when the parabola cannot advance.
            if x - a >= b - x:
                candidate = a + (x - a) / 2
            else:
                candidate = x + (b - x) / 2
        if not a < candidate < b or candidate == x:
            raise RuntimeError("Requested precision is unattainable with float.")

        fc = evaluate(candidate)
        if parabolic and abs(candidate - x) <= epsilon and abs(fc - fx) <= epsilon:
            return candidate if fc < fx else x

        previous_parabolic_improvement = parabolic and fc < fx
        previous_step = abs(candidate - x)

        if candidate < x:
            if fc <= fx:
                b, fb = x, fx
                x, fx = candidate, fc
            else:
                a, fa = candidate, fc
        else:
            if fc <= fx:
                a, fa = x, fx
                x, fx = candidate, fc
            else:
                b, fb = candidate, fc

    if b - a <= epsilon:
        return x
    raise RuntimeError("DSC-Powell iteration limit reached.")
