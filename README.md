# Rosenbrock Optimization

**Two methods. One workspace. See how each search reaches the minimum.**

A Python project for studying two-dimensional optimization with standard and
modified Rosenbrock searches. Compare their trajectories, function calls, and
iterations in a minimal browser interface, or use the same solvers from Python
and the command line.

**Python 3.10+ · Standard library only · English interface**

[Quick start](#quick-start) · [Methods](#methods) · [Parameters](#parameters) ·
[Constraints](#constraints) · [Python API](#python-api) · [Tests](#tests)

## Quick start

Run commands from the project directory. No package installation is needed.

```sh
python ui.py
```

On Windows, you can also double-click **`start_ui.cmd`**. The launcher looks for
the bundled Codex Python runtime, then `py -3`, then `python`.

The interface opens at **http://127.0.0.1:8765/**:

1. Choose a method, an objective function, and a starting point on the left.
2. Optionally choose a feasible region and adjust **More parameters**.
3. Click **Run optimization** or **Run comparison**.

The right panel shows function contours and accepted moves. Blue is the standard
method; orange is the modified method. Open markers show the start, filled markers
show the endpoints, and shaded areas are infeasible. **Show plot** toggles the
graph without repeating the calculation.

Results report the final point, function value, function calls, and iterations.
Changed settings take effect on the next run; the interface marks older results
when parameters change. Invalid settings appear inline.

Stop the server with **Ctrl+C** in its terminal. For a different port or manual
browser opening:

```sh
python ui.py --port 8766 --no-browser
```

## Methods

| Method | How it searches | Main controls |
| --- | --- | --- |
| Standard | Tries moves along two orthogonal directions. Expands successful steps; reverses and shrinks failed steps. Rotates after an unsuccessful sweep following progress. | Initial steps, step growth, step reversal |
| Modified | Minimizes along each direction, then rotates toward the sweep displacement. | Sven bracketing step, 1D search method, 1D accuracy |

The modified method supports **golden-section search** and **DSC-Powell**.
**Sven's method** brackets a directional minimum before an unconstrained 1D search.
A zero displacement preserves the existing directions.

These are adaptations of the original project implementations. The standard
method does not require every direction to succeed before rotation. With built-in
constraints, both solvers add projected refinement after their main stopping
criterion is met; see [Constraints](#constraints).

### Objective functions

| Function | Formula | Unconstrained minimum | Purpose |
| --- | --- | --- | --- |
| Rosenbrock | `f(x, y) = (1 − x)² + 100(y − x²)²` | `(1, 1)`, value `0` | A narrow curved valley for comparing search behavior |
| Sphere | `f(x, y) = x² + y²` | `(0, 0)`, value `0` | A simple test function with a known answer |

The **Rosenbrock method** is an optimization algorithm; the **Rosenbrock function**
is one objective it can minimize. The Python API also accepts your own function.

## Parameters

| Interface label | Python / CLI name | Default | Meaning |
| --- | --- | --- | --- |
| Starting x / y | `x0` / `--start X Y` | `(-1.2, 0)` | Initial point; must be feasible |
| Accuracy (ε) | `epsilon` / `--epsilon` | `1e-5` | Positive stopping threshold |
| Stop rule | `termination` / `--termination` | `step` | Stop based on step size or coordinate and value changes |
| Initial x / y step | `steps` / `--steps S1 S2` | `(0.3, 1.2)` | Nonzero initial steps for the standard method |
| Step growth (α) | `alpha` / `--alpha` | `3` | Multiplier for successful steps; greater than `1` |
| Step reversal (β) | `beta` / `--beta` | `-0.5` | Reverses and shrinks failed steps; between `−1` and `0` |
| Bracketing step | `delta` / `--delta` | `0.1` | Positive initial spacing for Sven's search |
| 1D accuracy | `line_epsilon` / `--line-epsilon` | `ε / 10` | Directional stopping threshold; must not exceed `ε` |
| Max iterations | `max_iterations` / `--max-iterations` | `10000` | Total budget for sweeps and projected refinement steps |
| Max 1D iterations | `line_max_iterations` / `--line-max-iterations` | `1000` | Iteration budget for each 1D search phase |

**1D search method** maps to `line_method` / `--line-method`: `golden` or
`dsc_powell`. The interface defaults to DSC-Powell; the CLI and Python API default
to golden-section search. The interface initially compares both methods; the CLI
defaults to the standard method. Hidden method-specific controls are inactive.

### What does “Accuracy” mean?

`ε` sets when the search stops. A smaller value asks for smaller steps or changes
and may require more work. It **does not guarantee** that the returned point is
within `ε` of the exact minimum.

- **Step size** (`step`): the standard method checks the norm of its trial-step
  vector after a failed sweep; the modified method checks its sweep displacement.
- **Changes** (`change`): checks both coordinate and function-value changes,
  scaled by `max(1, norm(x))` and `max(1, abs(f(x)))`. The standard method also
  requires small trial steps.

Built-in constraints additionally use a projected-gradient stopping check during
refinement. `converged=True` reports that the applicable stopping checks passed;
it is not a proof of a global minimum.

## Constraints

| Interface choice | Allowed region | Python example |
| --- | --- | --- |
| None | All finite points | `restriction=None` |
| Inside circle | `(x − cx)² + (y − cy)² ≤ r²` | `Disk(radius=1.3, center=(0, 0))` |
| One side of a line | `y ≤ mx + b` or `y ≥ mx + b` | `HalfPlane(slope=-0.5, intercept=1, side="below")` |
| Box (rectangle) | `xmin ≤ x ≤ xmax`, `ymin ≤ y ≤ ymax` | `Box(lower=(-2, -2), upper=(2, 2))` |

Circle centers and radii are editable. A line defines a **half-plane**, not a
requirement to stay exactly on the line. `side="above"` selects the other side.
The slope/intercept form represents nonvertical lines. All region boundaries are
included, and the starting point must already lie in the selected region.

Objective calls and accepted moves remain feasible. Modified constrained searches
find feasible slice bounds before minimizing and require a convex feasible set.
`Disk`, `HalfPlane`, and `Box` provide Euclidean projections. Both solvers use
these for boundary refinement with a gradient estimated from feasible samples
and backtracking; its work counts toward the total iteration and evaluation budgets.

A custom `restriction(point) -> bool` is also supported: `True` means feasible.
Numeric penalties are not accepted. A plain predicate without `project(point)`
does not receive projected refinement and can stall at a boundary.

## Command line

```sh
python main.py --method standard
python main.py --method modified --line-method golden
python main.py --method modified --line-method dsc_powell
python main.py --method modified --line-method dsc_powell --radius 1.3
python main.py --function sphere --radius 1 --center 2 -1 --start 2 -1
python main.py --help
```

The CLI supports the circle constraint through `--radius` and `--center`.
Use the interface or Python API for line and box constraints and for comparison.
Exit codes: **0** for convergence, **1** for an exhausted budget or stalled
refinement, **2** for invalid arguments or a reported search error.

## Python API

```python
from constraints import Disk
from rosenbrock import rosenbrock
from rosenbrock_modified import rosenbrock_modified

def objective(point):
    x, y = point
    return (1 - x) ** 2 + 100 * (y - x * x) ** 2

standard = rosenbrock(objective, (-1.2, 0), steps=(0.3, 1.2))
modified = rosenbrock_modified(
    objective, (-1.2, 0), line_method="dsc_powell",
    restriction=Disk(radius=1.3, center=(0, 0)),
)
print(modified.x, modified.fun, modified.converged)
```

Both return an immutable `OptimizationResult`:

| Field | Meaning |
| --- | --- |
| `x` | Final coordinate tuple |
| `fun` | Objective value at `x` |
| `path` | Starting point followed by every accepted move |
| `nfev` | Actual calls to the original objective, including 1D searches and refinement |
| `iterations` | Directional sweeps plus projected refinement steps |
| `converged` | Whether the applicable stopping checks passed |
| `message` | Why the solver stopped |

Inputs are not mutated. The final value is retained without another objective
call. An exhausted outer budget returns `converged=False`; invalid parameters,
nonfinite objective values, and failed 1D searches raise errors.

### Standalone 1D searches

```python
from sven import sven_method
from golden_section import golden_section
from dsc_powell import dsc_powell

def objective_1d(t):
    return (t - 2) ** 2

a, b = sven_method(objective_1d, 0, 0.1)
x_golden = golden_section(objective_1d, a, b, 1e-5)
x_powell = dsc_powell(objective_1d, 0, 0.1, 1e-5)
```

The objective must return finite, repeatable values and be unimodal over the
searched interval. Unimodality is assumed, not checked.

- **Sven** returns ordered bounds `(a, b)`. The step must be nonzero; its sign is
  ignored. An initial peak or three equal samples raises an error when called
  directly. The modified solver handles those cases before calling Sven.
- **Golden section** stops when interval width is at most `epsilon`. If the
  interval contains a minimizer, midpoint error is at most `epsilon / 2`.
- **DSC-Powell** caches samples and safeguards parabolic interpolation with
  bisection. It stops on small coordinate and value changes, a repeated vertex
  after an improving parabolic step, or a narrow bracket. These checks do not
  guarantee distance to the minimizer. `bounds=(a, b)` skips Sven; a boundary
  minimum uses bounded golden-section search.

No solver guarantees a global minimum for a nonconvex or multimodal objective.

## Project layout

```text
main.py                    Command-line entry point and example objectives
ui.py                      Local HTTP server and request handling
start_ui.cmd               Windows launcher
static/                    Browser interface, styles, and canvas plots
rosenbrock.py              Standard method
rosenbrock_modified.py     Modified method
optimization.py            Shared evaluation, validation, and result types
line_search.py             Directional searches and feasible slice bounds
sven.py                    1D interval bracketing
golden_section.py          Golden-section minimization
dsc_powell.py              Safeguarded parabolic minimization
constraints.py             Circle, half-plane, and box projections
boundary_refinement.py     Projected refinement for constrained minima
tests/test_optimization.py Regression and integration tests
```

## Tests

```sh
python -m unittest discover -s tests -v
```

The suite checks known minima, both stopping rules, stationary coordinates,
function-call counts, input preservation, iteration limits, feasible paths,
boundary minima, shifted circles, both sides of a line, box corners, 1D search
regressions, and interface request validation.
