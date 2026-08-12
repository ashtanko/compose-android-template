"""Loopback-only HTTP server for the dependency-free browser wizard."""

from __future__ import annotations

import json
import os
import secrets
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .engine import (
    SetupError,
    SetupPlan,
    apply_plan,
    build_plan,
    create_archive,
    read_project_settings,
)
from .model import (
    CAPABILITIES,
    CONFIGURATION_SURFACES,
    PRESETS,
    PROJECT_SETTING_DEFINITIONS,
    SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    SetupConfig,
)


MAX_REQUEST_BYTES = 128 * 1024
MAX_CONCURRENT_PUBLIC_WORK = 2
STATIC_ROOT = Path(__file__).resolve().parent / "web"


class WizardSession:
    def __init__(
        self,
        source_root: Path,
        token: str | None,
        *,
        public: bool = False,
    ):
        self.source_root = source_root
        self.token = token
        self.public = public
        self.plans: dict[str, SetupPlan] = {}
        self.lock = threading.Lock()
        self.work_slots = threading.BoundedSemaphore(MAX_CONCURRENT_PUBLIC_WORK)

    def remember(self, plan: SetupPlan) -> None:
        with self.lock:
            self.plans = {plan.digest: plan}

    def approved_plan(self, digest: str) -> SetupPlan | None:
        with self.lock:
            return self.plans.get(digest)


def run_server(source_root: Path, *, public: bool = False) -> None:
    token = None if public else secrets.token_urlsafe(32)
    session = WizardSession(source_root.resolve(), token, public=public)
    handler = _handler_for(session)
    host = "0.0.0.0" if public else "127.0.0.1"
    port = _public_port() if public else 0
    server = ThreadingHTTPServer((host, port), handler)
    host, port = server.server_address
    url = (
        f"http://{host}:{port}/"
        if public
        else f"http://{host}:{port}/?token={token}"
    )
    print(f"Project Setup Wizard: {url}")
    if public:
        print("Public mode enables ZIP downloads and disables filesystem writes.")
    else:
        print("The server is bound to this computer only. Press Ctrl+C to stop it.")
    try:
        if not public:
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
            work_acquired = False
            try:
                payload = self._read_json()
                if session.public and self.path in {"/api/plan", "/api/archive"}:
                    work_acquired = session.work_slots.acquire(blocking=False)
                    if not work_acquired:
                        self._send_json(
                            {
                                "error": (
                                    "project generation is busy; try again shortly"
                                ),
                            },
                            status=HTTPStatus.TOO_MANY_REQUESTS,
                        )
                        return
                if self.path == "/api/plan":
                    config = SetupConfig.from_dict(_payload_object(payload, "config"))
                    _validate_public_config(session, config)
                    plan = build_plan(config, source_root=session.source_root)
                    if not session.public:
                        session.remember(plan)
                    self._send_json(_plan_payload(session, plan))
                    return
                if self.path == "/api/archive":
                    config = SetupConfig.from_dict(_payload_object(payload, "config"))
                    _validate_public_config(session, config)
                    digest = _payload_string(payload, "digest")
                    plan = build_plan(config, source_root=session.source_root)
                    if plan.digest != digest:
                        raise SetupError(
                            "configuration changed; preview the plan again",
                        )
                    body, filename = create_archive(
                        plan,
                        expected_digest=digest,
                    )
                    self._send(
                        body,
                        "application/zip",
                        headers={
                            "Content-Disposition": (
                                f'attachment; filename="{filename}"'
                            ),
                        },
                    )
                    return
                if self.path == "/api/apply":
                    if session.public:
                        self._send_json(
                            {"error": "filesystem generation is disabled"},
                            status=HTTPStatus.FORBIDDEN,
                        )
                        return
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
            finally:
                if work_acquired:
                    session.work_slots.release()

        def _authorized(self) -> bool:
            if session.public:
                return True
            expected_host = f"{self.server.server_address[0]}:{self.server.server_address[1]}"
            host = self.headers.get("Host", "")
            if host != expected_host:
                self._send_json(
                    {"error": "invalid host"},
                    status=HTTPStatus.FORBIDDEN,
                )
                return False
            supplied = self.headers.get("X-Setup-Token", "")
            if session.token is None or not secrets.compare_digest(
                supplied,
                session.token,
            ):
                self._send_json(
                    {"error": "invalid setup session"},
                    status=HTTPStatus.FORBIDDEN,
                )
                return False
            return True

        def _same_origin(self) -> bool:
            origin = self.headers.get("Origin")
            if session.public:
                parsed = urlparse(origin) if origin else None
                valid = (
                    parsed is None
                    or (
                        parsed.scheme in {"http", "https"}
                        and parsed.netloc == self.headers.get("Host", "")
                    )
                )
            else:
                expected = (
                    f"http://{self.server.server_address[0]}:"
                    f"{self.server.server_address[1]}"
                )
                valid = origin in {None, expected}
            if not valid:
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
            headers: dict[str, str] | None = None,
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
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format_value: str, *args: object) -> None:
            return

    return WizardHandler


def _bootstrap_payload(session: WizardSession) -> dict[str, Any]:
    identity_path = session.source_root / "scripts" / "template-identity.json"
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    project_defaults = {
        "applicationId": identity["applicationPackage"],
        "displayName": identity["displayName"],
        **read_project_settings(session.source_root).to_dict(),
    }
    suggested = session.source_root.parent / "my-android-app"
    return {
        "schemaVersion": SCHEMA_VERSION,
        "supportedSchemaVersions": sorted(SUPPORTED_SCHEMA_VERSIONS),
        "sourceRoot": None if session.public else str(session.source_root),
        "suggestedOutput": None if session.public else str(suggested),
        "downloadOnly": session.public,
        "identity": identity,
        "projectDefaults": project_defaults,
        "projectSettingDefinitions": [
            definition.to_dict()
            for definition in PROJECT_SETTING_DEFINITIONS
        ],
        "configurationSurfaces": [
            surface.to_dict()
            for surface in CONFIGURATION_SURFACES
        ],
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


def _plan_payload(session: WizardSession, plan: SetupPlan) -> dict[str, Any]:
    value = plan.to_dict()
    if session.public:
        value["sourceRoot"] = None
        value["targetRoot"] = None
    return value


def _validate_public_config(
    session: WizardSession,
    config: SetupConfig,
) -> None:
    if session.public and config.output.mode != "archive":
        raise ValueError("public mode accepts archive output only")


def _public_port() -> int:
    raw_port = os.environ.get("PORT", "8000")
    try:
        port = int(raw_port)
    except ValueError as error:
        raise ValueError("PORT must be an integer") from error
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535")
    return port


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
