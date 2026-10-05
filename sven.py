"""Sven's bracketing method."""

from math import isfinite
from typing import Callable


def sven_method(
    f: Callable[[float], float],
    x_curr: float,
    delta: float,
    *,
    max_iterations: int = 1000,
) -> tuple[float, float]:
    """Bracket a minimum by doubling the step.

    delta must be nonzero; its sign is ignored.
    Requires unimodal f with a finite minimizer and finite values.
    Unimodality is not checked.
    """
    x_curr, step = float(x_curr), abs(float(delta))
    if not isfinite(x_curr) or not isfinite(step) or step == 0:
        raise ValueError('x_curr and nonzero delta must be finite.')
    if (
        isinstance(max_iterations, bool)
        or not isinstance(max_iterations, int)
        or max_iterations <= 0
    ):
        raise ValueError('max_iterations must be a positive integer.')

    def evaluate(point: float) -> float:
        value = float(f(point))
        if not isfinite(value):
            raise ValueError('Function value must be finite.')
        return value

    def interval(first: float, last: float) -> tuple[float, float]:
        a, b = sorted((first, last))
        if not isfinite(b - a):
            raise RuntimeError('Overflow while expanding the Sven interval.')
        return a, b

    left, right = x_curr - step, x_curr + step
    if not isfinite(left) or not isfinite(right):
        raise RuntimeError('Overflow while expanding the Sven interval.')
    if not left < x_curr < right:
        raise RuntimeError('Step is too small to change the float coordinate.')

    f_left, f_curr, f_right = evaluate(left), evaluate(x_curr), evaluate(right)
    if f_left == f_curr == f_right:
        raise ValueError('Three values are equal: change the step or starting point.')
    if f_left < f_curr and f_right < f_curr:
        raise ValueError('Both neighbors are lower: change the starting point or interval.')
    if f_curr <= f_left and f_curr <= f_right:
        return interval(left, right)

    previous = x_curr
    if f_right < f_curr:
        x_curr, f_curr = right, f_right
    else:
        step = -step
        x_curr, f_curr = left, f_left

    for _ in range(max_iterations):
        step *= 2
        next_point = x_curr + step
        if not isfinite(step) or not isfinite(next_point):
            raise RuntimeError('Overflow while expanding the Sven interval.')
        if next_point == x_curr:
            raise RuntimeError('Step is too small to change the float coordinate.')
        f_next = evaluate(next_point)

        if f_next > f_curr:
            midpoint = x_curr + (next_point - x_curr) / 2
            f_mid = evaluate(midpoint)
            if f_mid > f_curr:
                return interval(previous, midpoint)
            if f_mid < f_curr:
                return interval(x_curr, next_point)
            return interval(previous, next_point)
        if f_next == f_curr:
            return interval(previous, next_point)

        previous, x_curr, f_curr = x_curr, next_point, f_next

    raise RuntimeError('Sven: no bracket found within the iteration limit.')
