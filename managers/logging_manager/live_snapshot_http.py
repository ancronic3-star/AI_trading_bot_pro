"""
Read-only HTTP bridge for live_snapshot.json.

Run from project root:
    python -m managers.logging_manager.live_snapshot_http --host 127.0.0.1 --port 8765 --snapshot live_snapshot.json --token YOURTOKEN
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_PATH = "live_snapshot.json"
DEFAULT_TRACKED_PATH = "tracked_account_snapshot.json"
DEFAULT_DECISION_REPLAY_PATH = "decision_replay_snapshot.json"
DEFAULT_WM3_SUPPORT_PATH = "wm3_support_snapshot.json"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _guess_content_type(path: str) -> str:
    if path.endswith(".json"):
        return "application/json; charset=utf-8"
    return "text/plain; charset=utf-8"


class LiveSnapshotHandler(BaseHTTPRequestHandler):
    server_version = "LiveSnapshotHTTP/1.0"

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_common_headers("text/plain; charset=utf-8", 0)
        self.end_headers()

    def do_GET(self) -> None:
        self._handle(method="GET")

    def do_HEAD(self) -> None:
        self._handle(method="HEAD")

    def log_message(self, fmt: str, *args) -> None:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write(f"[{ts}] [live_snapshot_http] " + (fmt % args) + "\n")
        sys.stdout.flush()

    def _handle(self, method: str) -> None:
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"

        if route == "/healthz":
            body = json.dumps({"ok": True, "ts": int(time.time())}).encode("utf-8")
            self.send_response(200)
            self._send_common_headers("application/json; charset=utf-8", len(body))
            self.end_headers()
            if method == "GET":
                self.wfile.write(body)
            return

        route_map = {
            "/": self.server.snapshot_path,  # type: ignore[attr-defined]
            "/live_snapshot.json": self.server.snapshot_path,  # type: ignore[attr-defined]
            "/snapshot": self.server.snapshot_path,  # type: ignore[attr-defined]
            "/tracked_account_snapshot.json": self.server.tracked_snapshot_path,  # type: ignore[attr-defined]
            "/tracked_account": self.server.tracked_snapshot_path,  # type: ignore[attr-defined]
            "/decision_replay_snapshot.json": self.server.decision_replay_path,  # type: ignore[attr-defined]
            "/decision_replay": self.server.decision_replay_path,  # type: ignore[attr-defined]
            "/wm3_support_snapshot.json": self.server.wm3_support_path,  # type: ignore[attr-defined]
            "/wm3_support": self.server.wm3_support_path,  # type: ignore[attr-defined]
        }
        target_path = route_map.get(route)
        if target_path is None:
            self._respond_json({"error": "not_found", "path": route}, 404, method)
            return

        if not self._authorized():
            self._respond_json({"error": "unauthorized"}, 401, method, extra_headers={
                "WWW-Authenticate": 'Bearer realm="live-snapshot"'
            })
            return

        snapshot_path: Path = target_path
        if not snapshot_path.exists():
            self._respond_json(
                {"error": "snapshot_missing", "path": str(snapshot_path)},
                503,
                method,
            )
            return

        try:
            body_text = _read_text(snapshot_path)
            body_bytes = body_text.encode("utf-8")
        except Exception as e:
            self._respond_json(
                {"error": "snapshot_read_failed", "detail": f"{type(e).__name__}: {e}"},
                500,
                method,
            )
            return

        self.send_response(200)
        self._send_common_headers(_guess_content_type(snapshot_path.name), len(body_bytes))
        self.end_headers()
        if method == "GET":
            self.wfile.write(body_bytes)

    def _authorized(self) -> bool:
        token: Optional[str] = self.server.token  # type: ignore[attr-defined]
        if not token:
            return True
        auth = self.headers.get("Authorization", "")
        x_token = self.headers.get("X-Live-Snapshot-Token", "")
        if auth.startswith("Bearer "):
            presented = auth[len("Bearer "):].strip()
            return presented == token
        return x_token.strip() == token

    def _send_common_headers(self, content_type: str, content_length: int, extra_headers: Optional[dict] = None) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, X-Live-Snapshot-Token, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)

    def _respond_json(self, obj: dict, status: int, method: str, extra_headers: Optional[dict] = None) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_common_headers("application/json; charset=utf-8", len(body), extra_headers=extra_headers)
        self.end_headers()
        if method == "GET":
            self.wfile.write(body)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Read-only HTTP bridge for live_snapshot.json")
    p.add_argument("--host", default=os.environ.get("LIVE_SNAPSHOT_HOST", DEFAULT_HOST))
    p.add_argument("--port", type=int, default=int(os.environ.get("LIVE_SNAPSHOT_PORT", DEFAULT_PORT)))
    p.add_argument("--snapshot", default=os.environ.get("LIVE_SNAPSHOT_PATH", DEFAULT_PATH))
    p.add_argument("--token", default=os.environ.get("LIVE_SNAPSHOT_TOKEN", ""))
    return p


def main() -> int:
    args = build_parser().parse_args()
    snapshot_path = Path(args.snapshot).resolve()
    token = (args.token or "").strip()
    tracked_snapshot_path = (snapshot_path.parent / DEFAULT_TRACKED_PATH).resolve()
    decision_replay_path = (snapshot_path.parent / DEFAULT_DECISION_REPLAY_PATH).resolve()
    wm3_support_path = (snapshot_path.parent / DEFAULT_WM3_SUPPORT_PATH).resolve()

    httpd = ThreadingHTTPServer((args.host, args.port), LiveSnapshotHandler)
    httpd.snapshot_path = snapshot_path  # type: ignore[attr-defined]
    httpd.tracked_snapshot_path = tracked_snapshot_path  # type: ignore[attr-defined]
    httpd.decision_replay_path = decision_replay_path  # type: ignore[attr-defined]
    httpd.wm3_support_path = wm3_support_path  # type: ignore[attr-defined]
    httpd.token = token  # type: ignore[attr-defined]

    print(f"LIVE SNAPSHOT HTTP -> http://{args.host}:{args.port}/live_snapshot.json")
    print(f"TRACKED ACCOUNT HTTP -> http://{args.host}:{args.port}/tracked_account_snapshot.json")
    print(f"DECISION REPLAY HTTP -> http://{args.host}:{args.port}/decision_replay_snapshot.json")
    print(f"WM3 SUPPORT HTTP -> http://{args.host}:{args.port}/wm3_support_snapshot.json")
    print(f"SNAPSHOT PATH -> {snapshot_path}")
    print(f"TRACKED ACCOUNT PATH -> {tracked_snapshot_path}")
    print(f"DECISION REPLAY PATH -> {decision_replay_path}")
    print(f"WM3 SUPPORT PATH -> {wm3_support_path}")
    if token:
        print("AUTH -> bearer/x-token enabled")
    else:
        print("AUTH -> disabled")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
