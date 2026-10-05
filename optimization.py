"""Shared types and helpers for two-dimensional optimization."""

from dataclasses import dataclass
from math import hypot, isfinite
from typing import Callable, Sequence

Point = tuple[float, float]
Objective = Callable[[Point], float]
Restriction = Callable[[Point], bool]


@dataclass(frozen=True)
class OptimizationResult:
    x: Point
    fun: float
    path: tuple[Point, ...]
    nfev: int
    iterations: int
    converged: bool
    message: str


class Evaluator:
    def __init__(self, f: Objective, restriction: Restriction | None):
        self.f = f
        self.restriction = restriction
        self.nfev = 0

    def feasible(self, x: Point) -> bool:
        if not all(isfinite(value) for value in x):
            return False
        if self.restriction is None:
            return True
        allowed = self.restriction(x)
        if not isinstance(allowed, bool):
            raise ValueError("restriction must return bool: True means feasible.")
        return allowed

    def __call__(self, x: Point) -> float:
        if not self.feasible(x):
            raise ValueError("Cannot evaluate an infeasible point.")
        self.nfev += 1
        value = float(self.f(x))
        if not isfinite(value):
            raise ValueError("Function value must be finite.")
        return value


def positive(value: float, name: str) -> float:
    value = float(value)
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be positive and finite.")
    return value


def prepare(
    f: Objective, x0: Sequence[float], epsilon: float, max_iterations: int,
    termination: str, restriction: Restriction | None,
) -> tuple[Evaluator, Point, float, float]:
    if len(x0) != 2:
        raise ValueError("x0 must contain two coordinates.")
    x = (float(x0[0]), float(x0[1]))
    if not all(isfinite(value) for value in x):
        raise ValueError("x0 must be finite.")
    epsilon = positive(epsilon, "epsilon")
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, int) or max_iterations <= 0:
        raise ValueError("max_iterations must be a positive integer.")
    if termination not in ("change", "step"):
        raise ValueError("termination must be 'change' or 'step'.")
    evaluator = Evaluator(f, restriction)
    if not evaluator.feasible(x):
        raise ValueError("x0 must satisfy the restriction.")
    return evaluator, x, evaluator(x), epsilon


def move(x: Point, direction: Point, step: float) -> Point:
    return x[0] + step * direction[0], x[1] + step * direction[1]


def rotate(displacement: Point, directions: tuple[Point, Point]) -> tuple[Point, Point]:
    length = hypot(*displacement)
    if length == 0:
        return directions
    first = displacement[0] / length, displacement[1] / length
    return first, (-first[1], first[0])


def small_change(x: Point, previous: Point, value: float, old_value: float, epsilon: float) -> bool:
    distance = hypot(x[0] - previous[0], x[1] - previous[1])
    return (
        distance <= epsilon * max(1.0, hypot(*x))
        and abs(value - old_value) <= epsilon * max(1.0, abs(value))
    )


def result(
    evaluator: Evaluator, x: Point, value: float, path: list[Point],
    iterations: int, converged: bool,
) -> OptimizationResult:
    message = "Stopping criterion satisfied." if converged else "Iteration limit reached."
    return OptimizationResult(x, value, tuple(path), evaluator.nfev, iterations, converged, message)
