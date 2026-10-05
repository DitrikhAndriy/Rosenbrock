"""Projected refinement for constraints exposing project(x)."""

from math import hypot

from optimization import Evaluator, Point, OptimizationResult, result


def finish(
    evaluator: Evaluator, x: Point, value: float, path: list[Point],
    iteration: int, epsilon: float, max_iterations: int,
) -> OptimizationResult:
    project = getattr(evaluator.restriction, "project", None)
    if project is None:
        return result(evaluator, x, value, path, iteration, True)

    step = 1.0
    for extra in range(max_iterations - iteration):
        h = max(1.0, hypot(*x)) * max(1e-8, epsilon / 100)
        aa = ab = bb = ax = ay = 0.0
        for dx, dy in ((h, 0), (-h, 0), (0, h), (0, -h)):
            sample = project((x[0] + dx, x[1] + dy))
            ux, uy = (sample[0] - x[0]) / h, (sample[1] - x[1]) / h
            if ux == uy == 0:
                continue
            change = (evaluator(sample) - value) / h
            aa += ux * ux
            ab += ux * uy
            bb += uy * uy
            ax += ux * change
            ay += uy * change
        determinant = aa * bb - ab * ab
        trace = aa + bb
        if trace == 0:
            return result(evaluator, x, value, path, iteration + extra, True)
        if determinant > 1e-12 * trace**2:
            gradient = (bb * ax - ab * ay) / determinant, (aa * ay - ab * ax) / determinant
        else:
            gradient = ax / trace, ay / trace

        projected = project((x[0] - gradient[0], x[1] - gradient[1]))
        if hypot(projected[0] - x[0], projected[1] - x[1]) <= epsilon * max(1.0, hypot(*x)):
            return result(evaluator, x, value, path, iteration + extra, True)

        accepted = False
        for _ in range(60):
            trial = project((x[0] - step * gradient[0], x[1] - step * gradient[1]))
            if trial == x:
                break
            descent = gradient[0] * (trial[0] - x[0]) + gradient[1] * (trial[1] - x[1])
            trial_value = evaluator(trial)
            if descent < 0 and trial_value < value and trial_value <= value + 1e-4 * descent:
                x, value = trial, trial_value
                path.append(x)
                step = min(1.0, step * 2)
                accepted = True
                break
            step /= 2
        if not accepted:
            outcome = result(evaluator, x, value, path, iteration + extra + 1, False)
            return OptimizationResult(
                outcome.x, outcome.fun, outcome.path, outcome.nfev,
                outcome.iterations, False, "Projected refinement stalled at numerical precision.",
            )

    return result(evaluator, x, value, path, max_iterations, False)
