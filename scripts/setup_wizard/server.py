"""Loopback-only HTTP server for the dependency-free browser wizard."""

from __future__ import annotations

import json
import secrets
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .engine import SetupError, SetupPlan, apply_plan, build_plan
from .model import CAPABILITIES, PRESETS, SetupConfig


MAX_REQUEST_BYTES = 128 * 1024
STATIC_ROOT = Path(__file__).resolve().parent / "web"


class WizardSession:
    def __init__(self, source_root: Path, token: str):
        self.source_root = source_root
        self.token = token
        self.plans: dict[str, SetupPlan] = {}
        self.lock = threading.Lock()

    def remember(self, plan: SetupPlan) -> None:
        with self.lock:
            self.plans = {plan.digest: plan}

    def approved_plan(self, digest: str) -> SetupPlan | None:
        with self.lock:
            return self.plans.get(digest)


def run_server(source_root: Path) -> None:
    token = secrets.token_urlsafe(32)
    session = WizardSession(source_root.resolve(), token)
    handler = _handler_for(session)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    host, port = server.server_address
    url = f"http://{host}:{port}/?token={token}"
    print(f"Project Setup Wizard: {url}")
    print("The server is bound to this computer only. Press Ctrl+C to stop it.")
    try:
        webbrowser.open(url, new=1)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping setup wizard.")
    finally:
        server.server_close()


def _handler_for(session: WizardSession) -> type[BaseHTTPRequestHandler]:
    class WizardHandler(BaseHTTPRequestHandler):
        server_version = "ProjectSetupWizard/1"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/bootstrap":
                if not self._authorized():
                    return
                self._send_json(_bootstrap_payload(session))
                return
            static_files = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/index.html": ("index.html", "text/html; charset=utf-8"),
                "/styles.css": ("styles.css", "text/css; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            }
            static = static_files.get(parsed.path)
            if static is None:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            filename, content_type = static
            try:
                body = (STATIC_ROOT / filename).read_bytes()
            except OSError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self._send(body, content_type)

        def do_POST(self) -> None:
            if not self._authorized() or not self._same_origin():
                return
            try:
                payload = self._read_json()
                if self.path == "/api/plan":
                    config = SetupConfig.from_dict(_payload_object(payload, "config"))
                    plan = build_plan(config, source_root=session.source_root)
                    session.remember(plan)
                    self._send_json(plan.to_dict())
                    return
                if self.path == "/api/apply":
                    config = SetupConfig.from_dict(_payload_object(payload, "config"))
                    digest = _payload_string(payload, "digest")
                    remembered = session.approved_plan(digest)
                    if remembered is None:
                        raise SetupError("preview this configuration before applying it")
                    current = build_plan(config, source_root=session.source_root)
                    if current.digest != remembered.digest:
                        raise SetupError("configuration changed; preview the plan again")
                    force = payload.get("force", False)
                    if not isinstance(force, bool):
                        raise ValueError("force must be true or false")
                    target = apply_plan(
                        remembered,
                        expected_digest=digest,
                        force=force,
                    )
                    self._send_json(
                        {
                            "ok": True,
                            "targetRoot": str(target),
                            "message": "Project setup completed successfully.",
                        },
                    )
                    return
                self.send_error(HTTPStatus.NOT_FOUND)
            except (SetupError, ValueError, OSError, json.JSONDecodeError) as error:
                self._send_json(
                    {"error": str(error)},
                    status=HTTPStatus.BAD_REQUEST,
                )

        def _authorized(self) -> bool:
            expected_host = f"{self.server.server_address[0]}:{self.server.server_address[1]}"
            host = self.headers.get("Host", "")
            if host != expected_host:
                self._send_json(
                    {"error": "invalid host"},
                    status=HTTPStatus.FORBIDDEN,
                )
                return False
            supplied = self.headers.get("X-Setup-Token", "")
            if not secrets.compare_digest(supplied, session.token):
                self._send_json(
                    {"error": "invalid setup session"},
                    status=HTTPStatus.FORBIDDEN,
                )
                return False
            return True

        def _same_origin(self) -> bool:
            origin = self.headers.get("Origin")
            expected = (
                f"http://{self.server.server_address[0]}:"
                f"{self.server.server_address[1]}"
            )
            if origin not in {None, expected}:
                self._send_json(
                    {"error": "invalid origin"},
                    status=HTTPStatus.FORBIDDEN,
                )
                return False
            return True

        def _read_json(self) -> dict[str, Any]:
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("application/json"):
                raise ValueError("Content-Type must be application/json")
            raw_length = self.headers.get("Content-Length")
            if raw_length is None:
                raise ValueError("Content-Length is required")
            try:
                length = int(raw_length)
            except ValueError as error:
                raise ValueError("invalid Content-Length") from error
            if length < 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("request is too large")
            body = self.rfile.read(length)
            value = json.loads(body.decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError("request body must be a JSON object")
            return value

        def _send_json(
            self,
            value: dict[str, Any],
            *,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            body = json.dumps(value).encode("utf-8")
            self._send(body, "application/json; charset=utf-8", status=status)

        def _send(
            self,
            body: bytes,
            content_type: str,
            *,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; "
                "object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format_value: str, *args: object) -> None:
            return

    return WizardHandler


def _bootstrap_payload(session: WizardSession) -> dict[str, Any]:
    identity_path = session.source_root / "scripts" / "template-identity.json"
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    suggested = session.source_root.parent / "my-android-app"
    return {
        "sourceRoot": str(session.source_root),
        "suggestedOutput": str(suggested),
        "identity": identity,
        "presets": {
            key: sorted(value)
            for key, value in PRESETS.items()
        },
        "capabilities": [
            {
                "id": capability.id,
                "title": capability.title,
                "description": capability.description,
                "category": capability.category,
                "requires": list(capability.requires),
            }
            for capability in CAPABILITIES
        ],
    }


def _payload_object(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise ValueError(f"{key} must be an object")
    return result


def _payload_string(value: dict[str, Any], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise ValueError(f"{key} must be a non-empty string")
    return result
