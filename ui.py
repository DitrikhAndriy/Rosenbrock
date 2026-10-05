"""Local browser interface. Run with python ui.py."""

import argparse
import json
import math
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from constraints import Box, Disk, HalfPlane
from main import rosenbrock_function, sphere
from rosenbrock import rosenbrock
from rosenbrock_modified import rosenbrock_modified

STATIC = Path(__file__).resolve().parent / "static"


def run_request(data: dict) -> dict:
    def number(name, default):
        value = float(data.get(name, default))
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")
        return value

    def integer(name, default):
        value = number(name, default)
        if not value.is_integer() or not 1 <= value <= 50000:
            raise ValueError(f"{name} must be an integer between 1 and 50000.")
        return int(value)

    method = data.get("method", "compare")
    if method not in ("standard", "modified", "compare"):
        raise ValueError("Unknown method.")
    function = data.get("function", "rosenbrock")
    if function not in ("rosenbrock", "sphere"):
        raise ValueError("Unknown function.")
    constraint = data.get("constraint", "none")
    restriction = None
    if constraint == "disk":
        restriction = Disk(number("radius", 1.3), (number("center_x", 0), number("center_y", 0)))
    elif constraint == "halfplane":
        restriction = HalfPlane(number("slope", -0.5), number("intercept", 1), data.get("side", "below"))
    elif constraint == "box":
        restriction = Box(
            (number("xmin", -2), number("ymin", -2)),
            (number("xmax", 2), number("ymax", 2)),
        )
    elif constraint != "none":
        raise ValueError("Unknown constraint.")
    f = rosenbrock_function if function == "rosenbrock" else sphere
    start = number("x0", -1.2), number("y0", 0)
    options = dict(
        epsilon=number("epsilon", 1e-5),
        termination=data.get("termination", "step"),
        max_iterations=integer("max_iterations", 10000),
        restriction=restriction,
    )
    outcomes = []
    for selected in (("standard", "modified") if method == "compare" else (method,)):
        if selected == "standard":
            outcome = rosenbrock(
                f, start, (number("step1", .3), number("step2", 1.2)),
                alpha=number("alpha", 3), beta=number("beta", -.5), **options,
            )
        else:
            outcome = rosenbrock_modified(
                f, start, line_method=data.get("line_method", "dsc_powell"),
                delta=number("delta", .1),
                line_epsilon=number("line_epsilon", options["epsilon"] / 10),
                line_max_iterations=integer("line_max_iterations", 1000), **options,
            )
        outcomes.append(dict(
            method=selected, x=outcome.x, fun=outcome.fun, path=outcome.path,
            nfev=outcome.nfev, iterations=outcome.iterations,
            converged=outcome.converged, message=outcome.message,
        ))
    return {"results": outcomes}


class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        files = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
                 "/style.css": ("style.css", "text/css")}
        if self.path not in files:
            self.send(404, b"Not found", "text/plain")
            return
        name, content_type = files[self.path]
        self.send(200, (STATIC / name).read_bytes(), content_type + "; charset=utf-8")

    def do_POST(self):
        if self.path != "/api/run":
            self.send(404, b"Not found", "text/plain")
            return
        origin = self.headers.get("Origin")
        port = self.server.server_port
        if origin and origin not in (f"http://127.0.0.1:{port}", f"http://localhost:{port}"):
            self.send(403, b"Origin not allowed", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536:
                raise ValueError("Invalid request size.")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object.")
            body = run_request(data)
            status = 200
        except (ValueError, TypeError, RuntimeError, OverflowError) as error:
            body, status = {"error": str(error)}, 422
        self.send(status, json.dumps(body, allow_nan=False).encode(), "application/json")

    def log_message(self, *_):
        pass


def main():
    parser = argparse.ArgumentParser(description="Rosenbrock browser interface")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"Rosenbrock: {url}\nPress Ctrl+C to stop.", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
