#!/usr/bin/env python3
"""
Local helper server for PQViewer remote file opening.

Features:
1. Serve a local copy of PQViewer.
2. Receive files from a remote host through an SSH reverse tunnel.
3. Open each uploaded file in a separate browser tab/window.
4. Open multiple uploaded files in one PQViewer page.
5. Queue files for an already-open named PQViewer window.
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import posixpath
import secrets
import shutil
import tempfile
import urllib.parse
import uuid
import webbrowser
from pathlib import Path
from typing import Dict, List, Tuple


Entry = Tuple[str, str]


class PQVState:
    """Store runtime state for the PQViewer helper server."""

    def __init__(self, viewer_root: Path, token: str, temp_dir: Path, host_for_url: str, port: int) -> None:
        """Initialize the shared runtime state."""
        self.viewer_root = viewer_root.resolve()
        self.token = token
        self.temp_dir = temp_dir
        self.host_for_url = host_for_url
        self.port = port
        self.files: Dict[str, Path] = {}
        self.names: Dict[str, str] = {}
        self.queues: Dict[str, List[Entry]] = {}


def guess_content_type(path: Path) -> str:
    """Return a basic content type for common static files."""
    suffix = path.suffix.lower()
    return {
        ".html": "text/html; charset=utf-8",
        ".htm": "text/html; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".txt": "text/plain; charset=utf-8",
    }.get(suffix, "application/octet-stream")


def safe_static_path(viewer_root: Path, request_path: str) -> Path | None:
    """Resolve a requested static path under viewer_root, or return None if unsafe."""
    parsed_path = urllib.parse.urlparse(request_path).path
    decoded = urllib.parse.unquote(parsed_path)
    normalized = posixpath.normpath(decoded).lstrip("/")
    if normalized in ("", "."):
        normalized = "index.html"
    candidate = (viewer_root / normalized).resolve()
    try:
        candidate.relative_to(viewer_root)
    except ValueError:
        return None
    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate


def parse_bool(value: str | None, default: bool = False) -> bool:
    """Parse a query-string boolean value."""
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def open_browser(url: str, new_window: bool = False) -> None:
    """Open a URL in the user's browser."""
    webbrowser.open(url, new=1 if new_window else 0)


def make_viewer_url(state: PQVState, entries: List[Entry], window_id: str = "") -> str:
    """Build a PQViewer URL containing optional window and file/name query pairs."""
    query_parts: List[str] = []
    if window_id:
        query_parts.append("window=" + urllib.parse.quote(window_id, safe=""))
    for file_path, name in entries:
        query_parts.append("file=" + urllib.parse.quote(file_path, safe=""))
        query_parts.append("name=" + urllib.parse.quote(name, safe=""))
    query = "&".join(query_parts)
    suffix = f"?{query}" if query else ""
    return f"http://{state.host_for_url}:{state.port}/{suffix}"


def make_handler(state: PQVState):
    """Create an HTTP request handler class bound to the given state."""

    class PQVHandler(http.server.BaseHTTPRequestHandler):
        """Handle static viewer files, uploads, view requests, and append polling."""

        server_version = "PQVAgent/1.2"

        def _check_token(self) -> bool:
            """Check the X-PQV-Token request header."""
            token = self.headers.get("X-PQV-Token", "")
            if token != state.token:
                self.send_error(403, "Invalid token")
                return False
            return True

        def _read_upload(self) -> Tuple[str, str, str] | None:
            """Read one uploaded file and return file ID, file path, and safe name."""
            length_header = self.headers.get("Content-Length")
            if length_header is None:
                self.send_error(411, "Content-Length is required")
                return None

            try:
                length = int(length_header)
            except ValueError:
                self.send_error(400, "Invalid Content-Length")
                return None

            raw_name = self.headers.get("X-Filename", "remote_file")
            safe_name = Path(raw_name).name or "remote_file"
            file_id = uuid.uuid4().hex
            output_path = state.temp_dir / f"{file_id}_{safe_name}"

            # Copy the request body to disk without loading the whole file into memory.
            with output_path.open("wb") as f:
                remaining = length
                while remaining > 0:
                    chunk = self.rfile.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)

            state.files[file_id] = output_path
            state.names[file_id] = safe_name
            file_path = f"/file/{file_id}/{urllib.parse.quote(safe_name)}"
            return file_id, file_path, safe_name

        def _read_json_payload(self) -> object | None:
            """Read a JSON request payload."""
            length_header = self.headers.get("Content-Length", "0")
            try:
                length = int(length_header)
            except ValueError:
                self.send_error(400, "Invalid Content-Length")
                return None
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return None

        def _send_json(self, obj: object) -> None:
            """Send a JSON response."""
            data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_text(self, text: str) -> None:
            """Send a plain text response."""
            data = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self) -> None:
            """Handle upload and open endpoints."""
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            new_window = parse_bool(params.get("new", [None])[0], False)
            window_id = params.get("window", params.get("target", [""]))[0]

            if parsed.path == "/open":
                self._handle_open_one(new_window)
            elif parsed.path == "/upload":
                self._handle_upload_only()
            elif parsed.path == "/view":
                self._handle_view(new_window, window_id)
            elif parsed.path == "/queue":
                self._handle_queue(window_id)
            elif parsed.path == "/append":
                self._handle_append_one(window_id)
            elif parsed.path == "/viewer":
                self._handle_open_empty_viewer(new_window, window_id)
            else:
                self.send_error(404, "Not found")

        def _handle_open_one(self, new_window: bool) -> None:
            """Upload one file and immediately open one PQViewer page for it."""
            if not self._check_token():
                return
            item = self._read_upload()
            if item is None:
                return
            _, file_path, safe_name = item
            viewer_url = make_viewer_url(state, [(file_path, safe_name)])
            open_browser(viewer_url, new_window=new_window)
            self._send_text(f"Opened in PQViewer: {viewer_url}\n")

        def _handle_upload_only(self) -> None:
            """Upload one file and return its temporary file path without opening the browser."""
            if not self._check_token():
                return
            item = self._read_upload()
            if item is None:
                return
            file_id, file_path, safe_name = item
            self._send_json({"id": file_id, "file": file_path, "name": safe_name})

        def _entries_from_payload(self, payload: object) -> List[Entry]:
            """Extract file entries from a JSON payload."""
            entries: List[Entry] = []
            if not isinstance(payload, dict):
                return entries
            for item in payload.get("files", []):
                if not isinstance(item, dict):
                    continue
                file_path = str(item.get("file", ""))
                name = str(item.get("name", "remote_file"))
                if file_path:
                    entries.append((file_path, Path(name).name or "remote_file"))
            return entries

        def _handle_view(self, new_window: bool, window_id: str) -> None:
            """Open one PQViewer page containing multiple previously uploaded files."""
            if not self._check_token():
                return
            payload = self._read_json_payload()
            if payload is None:
                return
            entries = self._entries_from_payload(payload)
            if not entries:
                self.send_error(400, "No files were specified")
                return
            viewer_url = make_viewer_url(state, entries, window_id=window_id)
            open_browser(viewer_url, new_window=new_window)
            self._send_json({"url": viewer_url, "count": len(entries), "window": window_id})

        def _handle_queue(self, window_id: str) -> None:
            """Queue multiple uploaded file entries for a named existing viewer window."""
            if not self._check_token():
                return
            if not window_id:
                self.send_error(400, "window query parameter is required")
                return
            payload = self._read_json_payload()
            if payload is None:
                return
            entries = self._entries_from_payload(payload)
            if not entries:
                self.send_error(400, "No files were specified")
                return
            state.queues.setdefault(window_id, []).extend(entries)
            self._send_json({"queued": len(entries), "window": window_id})

        def _handle_append_one(self, window_id: str) -> None:
            """Upload one file and queue it for a named existing viewer window."""
            if not self._check_token():
                return
            if not window_id:
                self.send_error(400, "window query parameter is required")
                return
            item = self._read_upload()
            if item is None:
                return
            _, file_path, safe_name = item
            state.queues.setdefault(window_id, []).append((file_path, safe_name))
            self._send_json({"queued": 1, "window": window_id, "file": file_path, "name": safe_name})

        def _handle_open_empty_viewer(self, new_window: bool, window_id: str) -> None:
            """Open an empty named viewer window that will poll for appended files."""
            if not self._check_token():
                return
            if not window_id:
                self.send_error(400, "window query parameter is required")
                return
            state.queues.setdefault(window_id, [])
            viewer_url = make_viewer_url(state, [], window_id=window_id)
            open_browser(viewer_url, new_window=new_window)
            self._send_json({"url": viewer_url, "window": window_id})

        def do_GET(self) -> None:
            """Serve temporary files, poll queues, or static viewer files."""
            parsed = urllib.parse.urlparse(self.path)
            parts = parsed.path.strip("/").split("/", 2)

            if parsed.path == "/poll":
                self._handle_poll(parsed)
                return

            if len(parts) >= 2 and parts[0] == "file":
                self._serve_temp_file(parts[1])
                return

            self._serve_static_file()

        def _handle_poll(self, parsed: urllib.parse.ParseResult) -> None:
            """Return and clear queued files for a named viewer window."""
            params = urllib.parse.parse_qs(parsed.query)
            window_id = params.get("window", params.get("target", [""]))[0]
            if not window_id:
                self._send_json({"window": "", "files": []})
                return
            entries = state.queues.get(window_id, [])
            state.queues[window_id] = []
            self._send_json({
                "window": window_id,
                "files": [{"file": file_path, "url": file_path, "name": name} for file_path, name in entries],
            })

        def _serve_temp_file(self, file_id: str) -> None:
            """Serve a temporarily stored uploaded file to the browser."""
            path = state.files.get(file_id)
            if path is None or not path.exists():
                self.send_error(404, "File not found")
                return
            size = path.stat().st_size
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(size))
            self.send_header("Content-Disposition", f'inline; filename="{path.name}"')
            self.end_headers()
            with path.open("rb") as f:
                shutil.copyfileobj(f, self.wfile)

        def _serve_static_file(self) -> None:
            """Serve PQViewer static files from the local viewer root."""
            path = safe_static_path(state.viewer_root, self.path)
            if path is None or not path.exists() or not path.is_file():
                self.send_error(404, "Viewer file not found")
                return
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", guess_content_type(path))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args) -> None:
            """Print compact logs to the console."""
            print(f"[pqv-agent] {self.address_string()} - {format % args}")

    return PQVHandler


def main() -> None:
    """Run the local PQViewer helper server."""
    parser = argparse.ArgumentParser(description="Local helper server for PQViewer remote file opening.")
    parser.add_argument("--viewer-root", default=".", help="Path to the local PQViewer directory.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address.")
    parser.add_argument("--host-for-url", default="127.0.0.1", help="Host name used in browser URLs.")
    parser.add_argument("--port", type=int, default=18765, help="Local port.")
    parser.add_argument("--token", default=os.environ.get("PQV_TOKEN"), help="Shared token. If omitted, a random token is generated.")
    args = parser.parse_args()

    viewer_root = Path(args.viewer_root).resolve()
    if not viewer_root.exists():
        raise SystemExit(f"Viewer root does not exist: {viewer_root}")
    if not (viewer_root / "index.html").exists():
        raise SystemExit(f"index.html was not found in viewer root: {viewer_root}")

    token = args.token or secrets.token_urlsafe(24)
    temp_dir = Path(tempfile.mkdtemp(prefix="pqv_agent_"))

    state = PQVState(
        viewer_root=viewer_root,
        token=token,
        temp_dir=temp_dir,
        host_for_url=args.host_for_url,
        port=args.port,
    )

    print(f"[pqv-agent] Viewer root: {viewer_root}")
    print(f"[pqv-agent] Temporary directory: {temp_dir}")
    print(f"[pqv-agent] Listening on http://{args.host}:{args.port}/")
    print(f"[pqv-agent] Token: {token}")
    print("[pqv-agent] Set the same token on the remote host as PQV_TOKEN.")

    handler = make_handler(state)
    with http.server.ThreadingHTTPServer((args.host, args.port), handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
