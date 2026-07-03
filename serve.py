"""
serve.py — serves the dashboard locally with an apply-confirmation endpoint.

Usage:
    python serve.py      # opens http://localhost:8765/
"""

import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import dashboard
import store

PORT = 8765


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/dashboard.html"):
            self.send_error(404)
            return
        dashboard.main()  # regenerate so every visit shows current data
        body = dashboard.DASHBOARD_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        job_id = self.path.rsplit("/", 1)[-1]
        if self.path.startswith("/applied/") and store.mark_applied(job_id):
            self.send_response(204)
        else:
            self.send_response(404)
        self.end_headers()

    def log_message(self, *args):  # quiet console
        pass


if __name__ == "__main__":
    url = f"http://localhost:{PORT}/"
    print(f"Dashboard at {url}  (Ctrl+C to stop)")
    webbrowser.open(url)
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
