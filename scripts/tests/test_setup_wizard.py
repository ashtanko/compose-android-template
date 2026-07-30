"""Regression tests for the shared project setup wizard."""

from __future__ import annotations

import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path


SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from setup_wizard.engine import SetupError, _RepositorySnapshot, build_plan
from setup_wizard.model import (
    EXAMPLE_REQUIREMENTS,
    PRESETS,
    IdentityConfig,
    OutputConfig,
    SetupConfig,
    StarterConfig,
    ValidationConfig,
    resolve_capabilities,
)
from setup_wizard.server import WizardSession, _handler_for


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def sample_config(
    output_path: Path,
    *,
    capabilities: frozenset[str] = frozenset(),
    remove_examples: bool = True,
) -> SetupConfig:
    return SetupConfig(
        identity=IdentityConfig(
            package_name="com.example.wizard",
            project_name="Wizard App",
        ),
        output=OutputConfig(mode="copy", path=str(output_path)),
        starter=StarterConfig(remove_examples=remove_examples),
        capabilities=capabilities,
        validation=ValidationConfig(),
    )


class SetupConfigTest(unittest.TestCase):
    def test_json_round_trip_preserves_versioned_configuration(self) -> None:
        config = sample_config(
            Path("/tmp/wizard-output"),
            capabilities=PRESETS["standard"],
        )

        restored = SetupConfig.from_dict(json.loads(config.to_json()))

        self.assertEqual(config, restored)

    def test_networking_resolves_coroutines_and_serialization(self) -> None:
        resolved, reasons = resolve_capabilities(
            {"networking"},
            remove_examples=True,
        )

        self.assertEqual(
            frozenset({"networking", "coroutines", "serialization"}),
            resolved,
        )
        self.assertEqual("required by Networking", reasons["coroutines"])
        self.assertEqual("required by Networking", reasons["serialization"])

    def test_retained_examples_resolve_complete_required_stack(self) -> None:
        resolved, reasons = resolve_capabilities(set(), remove_examples=False)

        self.assertTrue(EXAMPLE_REQUIREMENTS.issubset(resolved))
        self.assertEqual(
            "required by the retained example modules",
            reasons["navigation"],
        )

    def test_unknown_capability_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown capabilities"):
            SetupConfig.from_dict(
                {
                    "schemaVersion": 1,
                    "identity": {
                        "packageName": "com.example.app",
                        "projectName": "App",
                    },
                    "output": {
                        "mode": "copy",
                        "path": "/tmp/output",
                    },
                    "capabilities": ["made-up"],
                },
            )

    def test_package_keyword_is_rejected(self) -> None:
        config = sample_config(Path("/tmp/output"))
        value = config.to_dict()
        value["identity"]["packageName"] = "com.example.when"

        with self.assertRaisesRegex(ValueError, "reserved keyword"):
            SetupConfig.from_dict(value)


class SetupPlanTest(unittest.TestCase):
    def test_plan_is_deterministic(self) -> None:
        config = sample_config(Path("/tmp/deterministic-wizard-output"))

        first = build_plan(config, source_root=REPOSITORY_ROOT)
        second = build_plan(config, source_root=REPOSITORY_ROOT)

        self.assertEqual(first.digest, second.digest)
        self.assertEqual(first.operations, second.operations)

    def test_copy_destination_inside_repository_is_rejected(self) -> None:
        config = sample_config(REPOSITORY_ROOT / "generated")

        with self.assertRaisesRegex(SetupError, "outside"):
            build_plan(config, source_root=REPOSITORY_ROOT)

    def test_repository_snapshot_restores_writes_deletes_and_creations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / "original.txt"
            deleted = root / "nested" / "deleted.txt"
            original.write_text("before", encoding="utf-8")
            deleted.parent.mkdir()
            deleted.write_text("restore me", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "injected"):
                with _RepositorySnapshot(root):
                    original.write_text("after", encoding="utf-8")
                    deleted.unlink()
                    (root / "created.txt").write_text("remove me", encoding="utf-8")
                    raise RuntimeError("injected failure")

            self.assertEqual("before", original.read_text(encoding="utf-8"))
            self.assertEqual("restore me", deleted.read_text(encoding="utf-8"))
            self.assertFalse((root / "created.txt").exists())


class WizardServerTest(unittest.TestCase):
    def setUp(self) -> None:
        from http.server import ThreadingHTTPServer

        self.token = "test-token"
        self.session = WizardSession(REPOSITORY_ROOT, self.token)
        try:
            self.server = ThreadingHTTPServer(
                ("127.0.0.1", 0),
                _handler_for(self.session),
            )
        except PermissionError as error:
            self.skipTest(f"loopback sockets are unavailable: {error}")
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.thread.start()
        self.connection = http.client.HTTPConnection(
            "127.0.0.1",
            self.server.server_address[1],
            timeout=5,
        )

    def tearDown(self) -> None:
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def test_bootstrap_rejects_missing_session_token(self) -> None:
        self.connection.request("GET", "/api/bootstrap")

        response = self.connection.getresponse()
        response.read()

        self.assertEqual(403, response.status)

    def test_bootstrap_returns_local_capability_registry(self) -> None:
        self.connection.request(
            "GET",
            "/api/bootstrap",
            headers={"X-Setup-Token": self.token},
        )

        response = self.connection.getresponse()
        payload = json.loads(response.read())

        self.assertEqual(200, response.status)
        self.assertEqual(str(REPOSITORY_ROOT), payload["sourceRoot"])
        self.assertIn("standard", payload["presets"])
        self.assertTrue(payload["capabilities"])

    def test_apply_rejects_configuration_without_fresh_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = sample_config(Path(temporary) / "output").to_dict()
            body = json.dumps(
                {
                    "config": config,
                    "digest": "stale",
                },
            )
            host = f"127.0.0.1:{self.server.server_address[1]}"
            self.connection.request(
                "POST",
                "/api/apply",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body.encode("utf-8"))),
                    "Origin": f"http://{host}",
                    "X-Setup-Token": self.token,
                },
            )

            response = self.connection.getresponse()
            payload = json.loads(response.read())

        self.assertEqual(400, response.status)
        self.assertIn("preview", payload["error"])


class WizardUiContractTest(unittest.TestCase):
    def test_ui_is_local_accessible_and_reduced_motion_aware(self) -> None:
        web_root = SCRIPTS_ROOT / "setup_wizard" / "web"
        html = (web_root / "index.html").read_text(encoding="utf-8")
        css = (web_root / "styles.css").read_text(encoding="utf-8")
        script = (web_root / "app.js").read_text(encoding="utf-8")

        self.assertIn('aria-label="Wizard progress"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn("prefers-reduced-motion", css)
        self.assertNotIn("https://", html)
        self.assertIn("X-Setup-Token", script)


if __name__ == "__main__":
    unittest.main()
