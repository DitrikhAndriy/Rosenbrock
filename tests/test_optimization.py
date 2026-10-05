"""Regression tests for the original failure cases and shared integration."""

import unittest
from math import hypot, cos, sin

from dsc_powell import dsc_powell
from main import rosenbrock_function, sphere
from rosenbrock import rosenbrock
from rosenbrock_modified import rosenbrock_modified
from constraints import Disk, HalfPlane, Box
from golden_section import golden_section
from ui import run_request


class OptimizationTests(unittest.TestCase):
    def methods(self):
        return (
            ("standard", rosenbrock),
            ("golden", lambda f, x, **kw: rosenbrock_modified(f, x, line_method="golden", **kw)),
            ("dsc_powell", lambda f, x, **kw: rosenbrock_modified(f, x, line_method="dsc_powell", **kw)),
        )

    def test_rosenbrock_function(self):
        for name, solver in self.methods():
            for termination in ("step", "change"):
                with self.subTest(method=name, termination=termination):
                    outcome = solver(rosenbrock_function, (-1.2, 0), termination=termination)
                    self.assertTrue(outcome.converged)
                    self.assertLess(outcome.fun, 1e-7)
                    self.assertLess(hypot(outcome.x[0] - 1, outcome.x[1] - 1), 1e-3)
                    values = [rosenbrock_function(x) for x in outcome.path]
                    self.assertTrue(all(new < old for old, new in zip(values, values[1:])))

    def test_origin_and_stationary_coordinate(self):
        for name, solver in self.methods():
            for start in ((0, 0), (0, 2)):
                with self.subTest(method=name, start=start):
                    outcome = solver(sphere, start)
                    self.assertTrue(outcome.converged)
                    self.assertLess(hypot(*outcome.x), 2e-5)

    def test_rosenbrock_from_zero(self):
        for name, solver in self.methods():
            with self.subTest(method=name):
                outcome = solver(rosenbrock_function, (0, 0))
                self.assertTrue(outcome.converged)
                self.assertLess(outcome.fun, 1e-7)

    def test_counter_and_input_ownership(self):
        for name, solver in self.methods():
            with self.subTest(method=name):
                calls = []
                start = [-1.2, 0]
                def measured(x):
                    calls.append(x)
                    return rosenbrock_function(x)
                first = solver(measured, start)
                self.assertEqual(first.nfev, len(calls))
                self.assertEqual(first.fun, rosenbrock_function(first.x))
                self.assertEqual(start, [-1.2, 0])
                calls.clear()
                second = solver(measured, start)
                self.assertEqual(first.nfev, second.nfev)
                self.assertEqual(first.path, second.path)
        steps = [0.3, 1.2]
        rosenbrock(sphere, (0, 2), steps)
        self.assertEqual(steps, [0.3, 1.2])

    def test_feasible_paths_and_objective_calls(self):
        restriction = lambda x: x[0] ** 2 + x[1] ** 2 <= 1.69
        for name, solver in self.methods():
            with self.subTest(method=name):
                def measured(x):
                    self.assertTrue(restriction(x))
                    return rosenbrock_function(x)
                outcome = solver(measured, (-1.2, 0), restriction=restriction)
                self.assertTrue(outcome.converged)
                self.assertTrue(all(restriction(x) for x in outcome.path))
                self.assertLess(outcome.fun, 0.004)

    def test_boundary_minimum_on_box(self):
        restriction = lambda x: -1 <= x[0] <= 1 and -1 <= x[1] <= 1
        f = lambda x: (x[0] - 2) ** 2 + x[1] ** 2
        for name, solver in self.methods():
            with self.subTest(method=name):
                outcome = solver(f, (0, 0), restriction=restriction)
                self.assertTrue(outcome.converged)
                self.assertLess(hypot(outcome.x[0] - 1, outcome.x[1]), 2e-5)

    def test_iteration_limit(self):
        for name, solver in self.methods():
            with self.subTest(method=name):
                outcome = solver(rosenbrock_function, (-1.2, 0), max_iterations=1)
                self.assertFalse(outcome.converged)
                self.assertEqual(outcome.iterations, 1)

    def test_validation(self):
        for name, solver in self.methods():
            for kwargs in ({"epsilon": 0}, {"max_iterations": 0}, {"termination": "unknown"}):
                with self.subTest(method=name, kwargs=kwargs), self.assertRaises(ValueError):
                    solver(sphere, (0, 0), **kwargs)
            with self.assertRaises(ValueError):
                solver(sphere, (2, 0), restriction=lambda x: x[0] <= 1)
            with self.assertRaises(ValueError):
                solver(sphere, (0, 0), restriction=lambda x: -1.0)
        with self.assertRaises(ValueError):
            rosenbrock(sphere, (0, 0), beta=0.5)
        with self.assertRaises(ValueError):
            rosenbrock_modified(sphere, (0, 0), line_method="unknown")

    def test_dsc_powell_bounded_regressions(self):
        self.assertEqual(dsc_powell(lambda t: (t - 2) ** 2, 0, .1, 1e-6, bounds=(0, 1)), 1)
        self.assertEqual(dsc_powell(lambda t: t, 0, .1, 1e-6, bounds=(0, 1)), 0)
        self.assertAlmostEqual(dsc_powell(lambda t: (t - .2) ** 2, 0, 1, .1), .2)

    def test_projected_boundary_minima(self):
        t = golden_section(lambda t: rosenbrock_function((t, -.5*t+1)), .5, 1, 1e-9)
        angle = golden_section(lambda a: rosenbrock_function((1.3*cos(a), 1.3*sin(a))), .4, 1.1, 1e-9)
        cases = ((HalfPlane(), (t, -.5*t+1)), (Disk(), (1.3*cos(angle), 1.3*sin(angle))))
        for restriction, expected in cases:
            for name, solver in self.methods():
                with self.subTest(method=name, constraint=type(restriction).__name__):
                    calls = []
                    def measured(x):
                        self.assertTrue(restriction(x))
                        calls.append(x)
                        return rosenbrock_function(x)
                    outcome = solver(measured, (-1.2, 0), restriction=restriction)
                    self.assertTrue(outcome.converged)
                    self.assertLess(hypot(outcome.x[0]-expected[0], outcome.x[1]-expected[1]), 1e-5)
                    self.assertEqual(outcome.nfev, len(calls))
                    self.assertTrue(all(restriction(x) for x in outcome.path))

    def test_projection_and_box_corner(self):
        for constraint in (Disk(), HalfPlane(), Box()):
            for x in ((100, 100), (-100, -100), (0, 0)):
                self.assertTrue(constraint(constraint.project(x)))
        for name, solver in self.methods():
            with self.subTest(method=name):
                outcome = solver(lambda x:(x[0]-2)**2+(x[1]-2)**2, (0, 0), restriction=Box())
                self.assertTrue(outcome.converged)
                self.assertLess(hypot(outcome.x[0]-1, outcome.x[1]-1), 1e-5)

    def test_ui_compare_and_validation(self):
        body = run_request({"method":"compare", "constraint":"halfplane"})
        self.assertEqual([r["method"] for r in body["results"]], ["standard", "modified"])
        for r in body["results"]:
            self.assertTrue(r["converged"])
            self.assertAlmostEqual(r["fun"], .04794622560648, places=9)
        for data in ({"method":"unknown"}, {"max_iterations":1.5}, {"epsilon":"nan"},
                     {"constraint":"disk", "radius":.5}, {"constraint":"box", "xmin":3}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                run_request(data)

    def test_shifted_circle_and_line_side(self):
        disk = Disk(1.0, (2.0, -1.0))
        above = HalfPlane(0.0, 1.0, "above")
        cases = ((disk, (2.0, -1.0), (2-2/5**.5, -1+1/5**.5)),
                 (above, (0.0, 2.0), (0.0, 1.0)),
                 (Box((1.0, -2.0), (3.0, 2.0)), (2.0, 0.0), (1.0, 0.0)))
        for constraint, start, expected in cases:
            for point in ((100, 100), (-100, -100), start):
                self.assertTrue(constraint(constraint.project(point)))
            for name, solver in self.methods():
                with self.subTest(method=name, constraint=constraint):
                    def measured(x):
                        self.assertTrue(constraint(x))
                        return sphere(x)
                    outcome = solver(measured, start, restriction=constraint)
                    self.assertTrue(outcome.converged)
                    self.assertLess(hypot(outcome.x[0]-expected[0], outcome.x[1]-expected[1]), 2e-5)
                    self.assertTrue(all(constraint(x) for x in outcome.path))

        body = run_request(dict(function="sphere", constraint="disk", radius=1,
                                center_x=2, center_y=-1, x0=2, y0=-1))
        for outcome in body["results"]:
            self.assertTrue(outcome["converged"])
            self.assertLess(abs(outcome["fun"]-(5**.5-1)**2), 1e-8)
        body = run_request(dict(function="sphere", constraint="halfplane", slope=0,
                                intercept=1, side="above", x0=0, y0=2))
        for outcome in body["results"]:
            self.assertTrue(outcome["converged"])
            self.assertAlmostEqual(outcome["fun"], 1, places=8)
        for data in ({"constraint":"disk", "center_x":"nan"},
                     {"constraint":"disk", "center_x":10},
                     {"constraint":"halfplane", "side":"unknown"}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                run_request(data)


if __name__ == "__main__":
    unittest.main()
