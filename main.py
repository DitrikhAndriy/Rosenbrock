"""Command-line runner for both Rosenbrock methods."""

import argparse

from optimization import positive
from constraints import Disk
from rosenbrock import rosenbrock
from rosenbrock_modified import rosenbrock_modified


def rosenbrock_function(x: tuple[float, float]) -> float:
    return (1 - x[0]) ** 2 + 100 * (x[1] - x[0] ** 2) ** 2


def sphere(x: tuple[float, float]) -> float:
    return x[0] ** 2 + x[1] ** 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Two-dimensional Rosenbrock optimization")
    parser.add_argument("--method", choices=("standard", "modified"), default="standard")
    parser.add_argument("--line-method", choices=("golden", "dsc_powell"), default="golden")
    parser.add_argument("--function", choices=("rosenbrock", "sphere"), default="rosenbrock")
    parser.add_argument("--start", type=float, nargs=2, default=(-1.2, 0.0), metavar=("X", "Y"))
    parser.add_argument("--epsilon", type=float, default=1e-5)
    parser.add_argument("--termination", choices=("step", "change"), default="step")
    parser.add_argument("--max-iterations", type=int, default=10000)
    parser.add_argument("--steps", type=float, nargs=2, default=(0.3, 1.2), metavar=("S1", "S2"))
    parser.add_argument("--alpha", type=float, default=3.0)
    parser.add_argument("--beta", type=float, default=-0.5)
    parser.add_argument("--delta", type=float, default=0.1)
    parser.add_argument("--line-epsilon", type=float)
    parser.add_argument("--line-max-iterations", type=int, default=1000)
    parser.add_argument("--radius", type=float, help="Restrict points to the inside of a circle")
    parser.add_argument("--center", type=float, nargs=2, default=(0.0, 0.0), metavar=("X", "Y"), help="Circle center (used with --radius)")
    args = parser.parse_args()

    try:
        restriction = None
        if args.radius is not None:
            radius = positive(args.radius, "radius")
            restriction = Disk(radius, tuple(args.center))
        f = rosenbrock_function if args.function == "rosenbrock" else sphere
        options = dict(
            epsilon=args.epsilon, restriction=restriction,
            termination=args.termination, max_iterations=args.max_iterations,
        )
        if args.method == "standard":
            outcome = rosenbrock(f, args.start, args.steps, alpha=args.alpha, beta=args.beta, **options)
        else:
            outcome = rosenbrock_modified(
                f, args.start, line_method=args.line_method, delta=args.delta,
                line_epsilon=args.line_epsilon, line_max_iterations=args.line_max_iterations, **options,
            )
    except (ValueError, RuntimeError) as error:
        parser.error(str(error))

    print(f"Method: {args.method}")
    if args.method == "modified":
        print(f"Line search: {args.line_method}")
    print(f"Point: ({outcome.x[0]:.10g}, {outcome.x[1]:.10g})")
    print(f"Function value: {outcome.fun:.10g}")
    print(f"Iterations: {outcome.iterations}")
    print(f"Function evaluations: {outcome.nfev}")
    print(f"Converged: {outcome.converged}")
    print(outcome.message)
    return 0 if outcome.converged else 1


if __name__ == "__main__":
    raise SystemExit(main())
