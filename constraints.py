"""Convex constraints with Euclidean projections."""

from dataclasses import dataclass
from math import hypot, isfinite, nextafter

from optimization import Point, positive


@dataclass(frozen=True)
class Disk:
    radius: float = 1.3
    center: Point = (0.0, 0.0)

    def __post_init__(self):
        positive(self.radius, "radius")
        if len(self.center) != 2 or not all(isfinite(v) for v in self.center):
            raise ValueError("Circle center must contain two finite coordinates.")

    def __call__(self, x: Point) -> bool:
        return hypot(x[0] - self.center[0], x[1] - self.center[1]) <= self.radius

    def project(self, x: Point) -> Point:
        dx, dy = x[0] - self.center[0], x[1] - self.center[1]
        length = hypot(dx, dy)
        if not isfinite(length):
            raise ValueError("Circle projection overflow: use smaller coordinates.")
        if length <= self.radius:
            return x
        scale = nextafter(self.radius, 0.0) / length
        projected = self.center[0] + dx * scale, self.center[1] + dy * scale
        while not self(projected):
            projected = tuple(nextafter(v, c) for v, c in zip(projected, self.center))
        return projected


@dataclass(frozen=True)
class HalfPlane:
    slope: float = -0.5
    intercept: float = 1.0
    side: str = "below"

    def __post_init__(self):
        if not isfinite(self.slope) or not isfinite(self.intercept):
            raise ValueError("Half-plane parameters must be finite.")
        if self.side not in ("below", "above"):
            raise ValueError("Line side must be 'below' or 'above'.")

    def __call__(self, x: Point) -> bool:
        boundary = self.slope * x[0] + self.intercept
        return x[1] <= boundary if self.side == "below" else x[1] >= boundary

    def project(self, x: Point) -> Point:
        sign = 1 if self.side == "below" else -1
        violation = sign * (x[1] - self.slope * x[0] - self.intercept)
        if violation <= 0:
            return x
        correction = sign * violation / (1 + self.slope**2)
        first = x[0] + correction * self.slope
        boundary = self.slope * first + self.intercept
        second = (min(x[1] - correction, boundary) if self.side == "below"
                  else max(x[1] - correction, boundary))
        return first, nextafter(second, float("-inf") if self.side == "below" else float("inf"))


@dataclass(frozen=True)
class Box:
    lower: Point = (-1.0, -1.0)
    upper: Point = (1.0, 1.0)

    def __post_init__(self):
        if not all(isfinite(v) for v in (*self.lower, *self.upper)):
            raise ValueError("Box bounds must be finite.")
        if any(a >= b for a, b in zip(self.lower, self.upper)):
            raise ValueError("Box lower bounds must be below upper bounds.")

    def __call__(self, x: Point) -> bool:
        return all(a <= v <= b for v, a, b in zip(x, self.lower, self.upper))

    def project(self, x: Point) -> Point:
        return tuple(min(b, max(a, v)) for v, a, b in zip(x, self.lower, self.upper))
