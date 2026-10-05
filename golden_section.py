"""Golden-section search."""

from math import isfinite, sqrt
from typing import Callable


def golden_section(
    f: Callable[[float], float],
    a: float,
    b: float,
    epsilon: float,
    *,
    max_iterations: int = 1000,
) -> float:
    """Minimize unimodal f on [a, b]; return the final interval midpoint.

    epsilon is the interval width tolerance. Unimodality is not checked.
    Error <= epsilon/2 if the final interval contains a minimizer.
    """
    a, b, epsilon = float(a), float(b), float(epsilon)
    if not all(isfinite(value) for value in (a, b, epsilon)):
        raise ValueError('Bounds and epsilon must be finite.')
    if a > b:
        raise ValueError('Bounds must satisfy a <= b.')
    if epsilon <= 0:
        raise ValueError('epsilon must be positive.')
    if (
        isinstance(max_iterations, bool)
        or not isinstance(max_iterations, int)
        or max_iterations <= 0
    ):
        raise ValueError('max_iterations must be a positive integer.')
    if not isfinite(b - a):
        raise ValueError('Interval width must be finite.')

    if b - a <= epsilon:
        return a + (b - a) / 2

    def evaluate(point: float) -> float:
        value = float(f(point))
        if not isfinite(value):
            raise ValueError('Function value must be finite.')
        return value

    ratio = (sqrt(5) - 1) / 2
    x1 = a + (1 - ratio) * (b - a)
    x2 = a + ratio * (b - a)
    f1, f2 = evaluate(x1), evaluate(x2)

    for iteration in range(max_iterations):
        previous_width = b - a
        keep_left = f1 < f2
        if keep_left:
            b = x2
            x2, f2 = x1, f1
        else:
            a = x1
            x1, f1 = x2, f2

        width = b - a
        if width <= epsilon:
            return a + width / 2
        if width >= previous_width:
            raise RuntimeError('Requested precision is unattainable with float.')

        if iteration + 1 < max_iterations:
            if keep_left:
                x1 = a + (1 - ratio) * width
                f1 = evaluate(x1)
            else:
                x2 = a + ratio * width
                f2 = evaluate(x2)

    raise RuntimeError('Golden-section iteration limit reached.')
