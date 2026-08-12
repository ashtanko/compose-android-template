"""Regression tests for the shared project setup wizard."""

from __future__ import annotations

import http.client
import io
import json
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest import mock


SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from setup_wizard.engine import (
    SOURCE_MANIFEST_PATH,
    SetupError,
    _RepositorySnapshot,
    _configure_ai_free_project,
    _tracked_files,
    build_plan,
    create_archive,
)
from setup_wizard.model import (
    EXAMPLE_REQUIREMENTS,
    PRESETS,
    IdentityConfig,
    OutputConfig,
    ProjectSettingsConfig,
    SetupConfig,
    StarterConfig,
    ValidationConfig,
    resolve_capabilities,
)
from setup_wizard.server import (
    MAX_CONCURRENT_PUBLIC_WORK,
    WizardSession,
    _bootstrap_payload,
    _handler_for,
    _plan_payload,
    _validate_public_config,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def sample_config(
    output_path: Path,
    *,
    application_id: str | None = None,
    display_name: str | None = None,
    capabilities: frozenset[str] = frozenset(),
    remove_examples: bool = True,
    ai_free: bool = False,
    output_mode: str = "copy",
    project_settings: ProjectSettingsConfig | None = None,
) -> SetupConfig:
    return SetupConfig(
        identity=IdentityConfig(
            package_name="com.example.wizard",
            project_name="Wizard App",
            application_id=application_id,
            display_name=display_name,
        ),
        output=OutputConfig(
            mode=output_mode,
            path=str(output_path) if output_mode == "copy" else None,
        ),
        starter=StarterConfig(
            remove_examples=remove_examples,
            ai_free=ai_free,
        ),
        capabilities=capabilities,
        project_settings=project_settings or ProjectSettingsConfig(),
        validation=ValidationConfig(),
    )


class SetupConfigTest(unittest.TestCase):
    def test_json_round_trip_preserves_extended_identity(self) -> None:
        config = sample_config(
            Path("/tmp/identity-round-trip"),
            application_id="com.example.product",
            display_name="Product Display Name",
        )

        restored = SetupConfig.from_dict(json.loads(config.to_json()))

        self.assertEqual(config.identity, restored.identity)

    def test_json_round_trip_preserves_project_settings(self) -> None:
        settings = ProjectSettingsConfig(
            version_code=42,
            version_name="4.2.0",
            compile_sdk=36,
            min_sdk=23,
            target_sdk=35,
            benchmark_min_sdk=28,
            jvm_target=17,
            posts_backend_url="https://api.example.com/v1/",
        )
        config = sample_config(
            Path("/tmp/project-settings-round-trip"),
            remove_examples=False,
            project_settings=settings,
        )

        restored = SetupConfig.from_dict(json.loads(config.to_json()))

        self.assertEqual(settings, restored.project_settings)

    def test_json_round_trip_preserves_versioned_configuration(self) -> None:
        config = sample_config(
            Path("/tmp/wizard-output"),
            capabilities=PRESETS["standard"],
        )

        restored = SetupConfig.from_dict(json.loads(config.to_json()))

        self.assertEqual(config, restored)

    def test_version_one_configuration_migrates_to_current_schema(self) -> None:
        value = sample_config(Path("/tmp/version-one")).to_dict()
        value["schemaVersion"] = 1
        value["starter"].pop("aiFree")
        value.pop("projectSettings")
        value["identity"].pop("applicationId")
        value["identity"].pop("displayName")

        restored = SetupConfig.from_dict(value)

        self.assertEqual(3, restored.schema_version)
        self.assertFalse(restored.starter.ai_free)
        self.assertEqual("com.example.wizard", restored.identity.application_id)
        self.assertEqual("Wizard App", restored.identity.display_name)
        self.assertEqual(ProjectSettingsConfig(), restored.project_settings)

    def test_version_two_configuration_migrates_with_unset_project_settings(self) -> None:
        value = sample_config(Path("/tmp/version-two")).to_dict()
        value["schemaVersion"] = 2
        value.pop("projectSettings")
        value["identity"].pop("applicationId")
        value["identity"].pop("displayName")

        restored = SetupConfig.from_dict(value)

        self.assertEqual(3, restored.schema_version)
        self.assertEqual("com.example.wizard", restored.identity.application_id)
        self.assertEqual("Wizard App", restored.identity.display_name)
        self.assertEqual(ProjectSettingsConfig(), restored.project_settings)

    def test_sdk_minimum_above_target_is_rejected(self) -> None:
        value = sample_config(Path("/tmp/invalid-sdk-order")).to_dict()
        value["projectSettings"] = {
            "compileSdk": 36,
            "minSdk": 35,
            "targetSdk": 34,
        }

        with self.assertRaisesRegex(ValueError, "minSdk.*targetSdk"):
            SetupConfig.from_dict(value)

    def test_target_sdk_above_compile_sdk_is_rejected(self) -> None:
        value = sample_config(Path("/tmp/invalid-compile-sdk")).to_dict()
        value["projectSettings"] = {
            "compileSdk": 35,
            "minSdk": 24,
            "targetSdk": 36,
        }

        with self.assertRaisesRegex(ValueError, "targetSdk.*compileSdk"):
            SetupConfig.from_dict(value)

    def test_benchmark_sdk_below_app_minimum_is_rejected(self) -> None:
        value = sample_config(Path("/tmp/invalid-benchmark-sdk")).to_dict()
        value["projectSettings"] = {
            "minSdk": 24,
            "benchmarkMinSdk": 23,
        }

        with self.assertRaisesRegex(ValueError, "benchmarkMinSdk"):
            SetupConfig.from_dict(value)

    def test_non_positive_version_code_is_rejected(self) -> None:
        value = sample_config(Path("/tmp/invalid-version-code")).to_dict()
        value["projectSettings"] = {"versionCode": 0}

        with self.assertRaisesRegex(ValueError, "versionCode"):
            SetupConfig.from_dict(value)

    def test_multiline_version_name_is_rejected(self) -> None:
        value = sample_config(Path("/tmp/invalid-version-name")).to_dict()
        value["projectSettings"] = {"versionName": "1.0\nmalformed"}

        with self.assertRaisesRegex(ValueError, "versionName.*single line"):
            SetupConfig.from_dict(value)

    def test_invalid_application_id_is_rejected(self) -> None:
        value = sample_config(Path("/tmp/invalid-application-id")).to_dict()
        value["identity"]["applicationId"] = "invalid-application-id"

        with self.assertRaisesRegex(ValueError, "applicationId"):
            SetupConfig.from_dict(value)

    def test_multiline_posts_backend_url_is_rejected(self) -> None:
        value = sample_config(
            Path("/tmp/invalid-backend-url"),
            remove_examples=False,
        ).to_dict()
        value["projectSettings"] = {
            "postsBackendUrl": "https://api.example.com/\nINJECTED=true",
        }

        with self.assertRaisesRegex(ValueError, "postsBackendUrl.*single line"):
            SetupConfig.from_dict(value)

    def test_non_https_posts_backend_url_is_rejected(self) -> None:
        value = sample_config(
            Path("/tmp/http-backend-url"),
            remove_examples=False,
        ).to_dict()
        value["projectSettings"] = {
            "postsBackendUrl": "http://api.example.com/",
        }

        with self.assertRaisesRegex(ValueError, "postsBackendUrl.*HTTPS"):
            SetupConfig.from_dict(value)

    def test_posts_backend_url_without_trailing_slash_is_rejected(self) -> None:
        value = sample_config(
            Path("/tmp/backend-url-without-slash"),
            remove_examples=False,
        ).to_dict()
        value["projectSettings"] = {
            "postsBackendUrl": "https://api.example.com/v1",
        }

        with self.assertRaisesRegex(ValueError, "postsBackendUrl.*slash"):
            SetupConfig.from_dict(value)

    def test_posts_backend_url_is_rejected_when_examples_are_removed(self) -> None:
        value = sample_config(Path("/tmp/backend-without-posts")).to_dict()
        value["projectSettings"] = {
            "postsBackendUrl": "https://api.example.com/",
        }

        with self.assertRaisesRegex(ValueError, "example modules.*retained"):
            SetupConfig.from_dict(value)

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

    def test_ai_free_configuration_excludes_generative_ai_capability(self) -> None:
        config = sample_config(
            Path("/tmp/ai-free"),
            capabilities=frozenset({"generative_ai"}),
            ai_free=True,
        )

        plan = build_plan(config, source_root=REPOSITORY_ROOT)

        self.assertNotIn("generative_ai", plan.config.capabilities)
        self.assertIn(
            "Remove coding-agent guidance and generative-AI integration",
            plan.operations,
        )

    def test_package_keyword_is_rejected(self) -> None:
        config = sample_config(Path("/tmp/output"))
        value = config.to_dict()
        value["identity"]["packageName"] = "com.example.when"

        with self.assertRaisesRegex(ValueError, "reserved keyword"):
            SetupConfig.from_dict(value)


class SetupPlanTest(unittest.TestCase):
    def test_plan_resolves_project_setting_defaults_from_repository(self) -> None:
        config = sample_config(
            Path("/tmp/default-project-settings"),
            remove_examples=False,
        )

        plan = build_plan(config, source_root=REPOSITORY_ROOT)

        self.assertEqual(
            ProjectSettingsConfig(
                version_code=1,
                version_name="1.0",
                compile_sdk=37,
                min_sdk=24,
                target_sdk=37,
                benchmark_min_sdk=28,
                jvm_target=21,
                posts_backend_url="https://jsonplaceholder.typicode.com/",
            ),
            plan.config.project_settings,
        )

    def test_plan_resolves_identity_defaults_from_package_and_project_name(self) -> None:
        config = sample_config(Path("/tmp/default-identity"))

        plan = build_plan(config, source_root=REPOSITORY_ROOT)

        self.assertEqual("com.example.wizard", plan.config.identity.application_id)
        self.assertEqual("Wizard App", plan.config.identity.display_name)

    def test_plan_rejects_jvm_target_that_differs_from_repository(self) -> None:
        config = sample_config(
            Path("/tmp/different-jvm-target"),
            project_settings=ProjectSettingsConfig(jvm_target=17),
        )

        with self.assertRaisesRegex(SetupError, "jvmTarget.*fixed"):
            build_plan(config, source_root=REPOSITORY_ROOT)

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

    def test_non_git_inventory_uses_manifest_and_excludes_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = root / SOURCE_MANIFEST_PATH
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                "README.md\n"
                "release/app-debug.jks\n"
                f"{SOURCE_MANIFEST_PATH.as_posix()}\n",
                encoding="utf-8",
            )
            (root / "README.md").write_text("safe", encoding="utf-8")
            debug_key = root / "release" / "app-debug.jks"
            debug_key.parent.mkdir()
            debug_key.write_bytes(b"template debug key")
            (root / "production-signing.jks").write_bytes(b"secret")
            (root / "service-account-production.json").write_text(
                '{"private_key": "secret"}',
                encoding="utf-8",
            )
            (root / ".env.production").write_text(
                "TOKEN=secret",
                encoding="utf-8",
            )

            inventory = _tracked_files(root)

            self.assertEqual(
                {
                    Path("README.md"),
                    Path("release/app-debug.jks"),
                    SOURCE_MANIFEST_PATH,
                },
                set(inventory),
            )

    def test_non_git_inventory_fails_closed_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "production-signing.jks").write_bytes(b"secret")

            with self.assertRaisesRegex(SetupError, "source manifest"):
                _tracked_files(root)

    def test_git_inventory_excludes_ide_state(self) -> None:
        self.assertNotIn(
            Path(".idea/kotlinc.xml"),
            _tracked_files(REPOSITORY_ROOT),
        )

    def test_ai_free_setup_reports_guidance_deletion_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".agents").mkdir()

            with mock.patch(
                "setup_wizard.engine.shutil.rmtree",
                side_effect=OSError("permission denied"),
            ):
                with self.assertRaisesRegex(SetupError, "remove AI guidance"):
                    _configure_ai_free_project(root)

    def test_archive_is_deterministic_executable_and_ai_free(self) -> None:
        config = sample_config(
            Path("/tmp/unused"),
            capabilities=frozenset({"generative_ai"}),
            ai_free=True,
            output_mode="archive",
        )
        plan = build_plan(config, source_root=REPOSITORY_ROOT)

        first, filename = create_archive(plan, expected_digest=plan.digest)
        second, second_filename = create_archive(plan, expected_digest=plan.digest)

        self.assertEqual("wizard-app.zip", filename)
        self.assertEqual(filename, second_filename)
        self.assertEqual(first, second)
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            names = archive.namelist()
            root = "wizard-app/"
            manifest = {
                Path(line)
                for line in archive.read(
                    f"{root}{SOURCE_MANIFEST_PATH.as_posix()}",
                ).decode("utf-8").splitlines()
                if line
            }
            archived_files = {
                Path(name.removeprefix(root))
                for name in names
            }
            self.assertEqual(archived_files, manifest)
            self.assertIn(f"{root}gradlew", names)
            self.assertIn(
                f"{root}app/src/main/kotlin/com/example/wizard/home/StarterScreen.kt",
                names,
            )
            self.assertFalse(
                any(
                    name.startswith(
                        (
                            f"{root}.agents/",
                            f"{root}.claude/",
                        ),
                    )
                    or name.endswith("/AGENTS.md")
                    or name in {
                        f"{root}AGENTS.md",
                        f"{root}CLAUDE.md",
                        f"{root}skills-lock.json",
                    }
                    for name in names
                ),
            )
            app_build = archive.read(
                f"{root}app/build.gradle.kts",
            ).decode("utf-8")
            catalog = archive.read(
                f"{root}gradle/libs.versions.toml",
            ).decode("utf-8")
            readme = archive.read(f"{root}README.md").decode("utf-8")
            architecture = archive.read(
                f"{root}ARCHITECTURE.md",
            ).decode("utf-8")
            docs_check = archive.read(
                f"{root}scripts/check-docs.sh",
            ).decode("utf-8")
            self.assertNotIn("generativeai", app_build)
            self.assertNotIn("generativeai", catalog)
            self.assertNotIn(".agents", readme)
            self.assertNotIn("AGENTS.md", readme)
            self.assertNotIn(".agents", architecture)
            self.assertNotIn(".agents", docs_check)
            self.assertNotIn("AGENTS.md", docs_check)
            self.assertNotIn("CLAUDE.md", docs_check)
            gradlew_mode = archive.getinfo(f"{root}gradlew").external_attr >> 16
            self.assertNotEqual(0, gradlew_mode & 0o111)


class ProjectSettingsArchiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config = sample_config(
            Path("/tmp/unused"),
            application_id="com.example.runtime",
            display_name="Runtime Display Name",
            capabilities=frozenset({"baseline_profiles"}),
            remove_examples=False,
            output_mode="archive",
            project_settings=ProjectSettingsConfig(
                version_code=42,
                version_name="4.2.0",
                compile_sdk=36,
                min_sdk=23,
                target_sdk=35,
                benchmark_min_sdk=28,
                jvm_target=21,
                posts_backend_url="https://api.example.com/v2/",
            ),
        )
        plan = build_plan(config, source_root=REPOSITORY_ROOT)
        archive_bytes, _ = create_archive(plan, expected_digest=plan.digest)
        cls.archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
        cls.root = "wizard-app/"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.archive.close()

    def test_archive_applies_application_id(self) -> None:
        app_build = self.archive.read(
            f"{self.root}app/build.gradle.kts",
        ).decode("utf-8")

        self.assertIn('applicationId = "com.example.runtime"', app_build)

    def test_archive_applies_version_settings(self) -> None:
        app_build = self.archive.read(
            f"{self.root}app/build.gradle.kts",
        ).decode("utf-8")

        self.assertIn("versionCode = 42", app_build)
        self.assertIn('versionName = "4.2.0"', app_build)

    def test_archive_applies_sdk_settings(self) -> None:
        catalog = self.archive.read(
            f"{self.root}gradle/libs.versions.toml",
        ).decode("utf-8")

        self.assertIn('compileSdk = "36"', catalog)
        self.assertIn('minSdk = "23"', catalog)
        self.assertIn('benchmarkMinSdk = "28"', catalog)
        self.assertIn('targetSdk = "35"', catalog)

    def test_archive_applies_display_name_resource(self) -> None:
        strings = self.archive.read(
            f"{self.root}app/src/main/res/values/strings.xml",
        ).decode("utf-8")

        self.assertIn(
            '<string name="app_name" translatable="false">'
            "Runtime Display Name</string>",
            strings,
        )

    def test_archive_applies_application_id_to_benchmark_target(self) -> None:
        benchmark_config = self.archive.read(
            f"{self.root}benchmarks/src/main/java/com/example/wizard/benchmarks/"
            "BenchmarkConfig.kt",
        ).decode("utf-8")

        self.assertIn(
            'TARGET_PACKAGE_NAME = "com.example.runtime"',
            benchmark_config,
        )

    def test_archive_applies_posts_backend_url_when_examples_are_retained(self) -> None:
        network_module = self.archive.read(
            f"{self.root}feature/posts/data/src/main/kotlin/com/example/wizard/"
            "feature/posts/data/di/PostsNetworkModule.kt",
        ).decode("utf-8")

        self.assertIn(
            'POSTS_BASE_URL = "https://api.example.com/v2/"',
            network_module,
        )

    def test_archive_does_not_apply_posts_backend_url_to_secrets_defaults(self) -> None:
        secrets = self.archive.read(
            f"{self.root}secrets.defaults.properties",
        ).decode("utf-8")

        self.assertNotIn("api.example.com/v2", secrets)

    def test_archive_records_application_and_display_identity(self) -> None:
        identity = json.loads(
            self.archive.read(
                f"{self.root}scripts/template-identity.json",
            ),
        )

        self.assertEqual("com.example.runtime", identity["applicationPackage"])
        self.assertEqual("Runtime Display Name", identity["displayName"])


class BootstrapContractTest(unittest.TestCase):
    def test_bootstrap_describes_project_settings_and_configuration_surfaces(self) -> None:
        session = WizardSession(REPOSITORY_ROOT, "test-token")

        payload = _bootstrap_payload(session)

        self.assertEqual(
            {
                "applicationId": "dev.shtanko.template",
                "displayName": "Compose Android Template",
                "versionCode": 1,
                "versionName": "1.0",
                "compileSdk": 37,
                "minSdk": 24,
                "targetSdk": 37,
                "benchmarkMinSdk": 28,
                "jvmTarget": 21,
                "postsBackendUrl": "https://jsonplaceholder.typicode.com/",
            },
            payload["projectDefaults"],
        )
        definition_ids = {
            definition["id"]
            for definition in payload["projectSettingDefinitions"]
        }
        self.assertEqual(set(payload["projectDefaults"]), definition_ids)
        self.assertTrue(payload["configurationSurfaces"])

    def test_public_payloads_do_not_disclose_server_paths(self) -> None:
        session = WizardSession(REPOSITORY_ROOT, None, public=True)
        config = sample_config(
            Path("/tmp/unused"),
            output_mode="archive",
        )
        plan = build_plan(config, source_root=REPOSITORY_ROOT)

        bootstrap = _bootstrap_payload(session)
        plan_payload = _plan_payload(session, plan)

        self.assertIsNone(bootstrap["sourceRoot"])
        self.assertIsNone(bootstrap["suggestedOutput"])
        self.assertIsNone(plan_payload["sourceRoot"])
        self.assertIsNone(plan_payload["targetRoot"])

    def test_public_mode_accepts_archive_output_only(self) -> None:
        session = WizardSession(REPOSITORY_ROOT, None, public=True)

        with self.assertRaisesRegex(ValueError, "archive output only"):
            _validate_public_config(
                session,
                sample_config(Path("/tmp/server-path")),
            )

    def test_public_work_limit_is_non_blocking(self) -> None:
        session = WizardSession(REPOSITORY_ROOT, None, public=True)
        acquired = 0
        try:
            for _ in range(MAX_CONCURRENT_PUBLIC_WORK):
                self.assertTrue(session.work_slots.acquire(blocking=False))
                acquired += 1
            self.assertFalse(session.work_slots.acquire(blocking=False))
        finally:
            for _ in range(acquired):
                session.work_slots.release()


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

    def test_archive_returns_the_freshly_previewed_project_zip(self) -> None:
        config = sample_config(
            Path("/tmp/unused"),
            ai_free=True,
            output_mode="archive",
        ).to_dict()
        host = f"127.0.0.1:{self.server.server_address[1]}"
        plan_body = json.dumps({"config": config})
        headers = {
            "Content-Type": "application/json",
            "Origin": f"http://{host}",
            "X-Setup-Token": self.token,
        }
        self.connection.request(
            "POST",
            "/api/plan",
            body=plan_body,
            headers=headers,
        )
        plan_response = self.connection.getresponse()
        plan = json.loads(plan_response.read())
        self.assertEqual(200, plan_response.status)

        archive_body = json.dumps(
            {
                "config": config,
                "digest": plan["digest"],
            },
        )
        self.connection.request(
            "POST",
            "/api/archive",
            body=archive_body,
            headers=headers,
        )
        response = self.connection.getresponse()
        body = response.read()

        self.assertEqual(200, response.status)
        self.assertEqual("application/zip", response.getheader("Content-Type"))
        self.assertIn(
            'filename="wizard-app.zip"',
            response.getheader("Content-Disposition"),
        )
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            self.assertIn("wizard-app/settings.gradle.kts", archive.namelist())


class PublicWizardServerTest(unittest.TestCase):
    def setUp(self) -> None:
        from http.server import ThreadingHTTPServer

        self.session = WizardSession(REPOSITORY_ROOT, None, public=True)
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

    def test_bootstrap_is_tokenless_and_download_only(self) -> None:
        self.connection.request("GET", "/api/bootstrap")

        response = self.connection.getresponse()
        payload = json.loads(response.read())

        self.assertEqual(200, response.status)
        self.assertTrue(payload["downloadOnly"])
        self.assertIsNone(payload["sourceRoot"])
        self.assertIsNone(payload["suggestedOutput"])

    def test_apply_is_disabled_in_public_mode(self) -> None:
        host = f"127.0.0.1:{self.server.server_address[1]}"
        body = json.dumps({})
        self.connection.request(
            "POST",
            "/api/apply",
            body=body,
            headers={
                "Content-Type": "application/json",
                "Origin": f"http://{host}",
            },
        )

        response = self.connection.getresponse()
        payload = json.loads(response.read())

        self.assertEqual(403, response.status)
        self.assertIn("disabled", payload["error"])

    def test_plan_rejects_non_archive_output_in_public_mode(self) -> None:
        host = f"127.0.0.1:{self.server.server_address[1]}"
        body = json.dumps(
            {"config": sample_config(Path("/tmp/server-path")).to_dict()},
        )
        self.connection.request(
            "POST",
            "/api/plan",
            body=body,
            headers={
                "Content-Type": "application/json",
                "Origin": f"http://{host}",
            },
        )

        response = self.connection.getresponse()
        payload = json.loads(response.read())

        self.assertEqual(400, response.status)
        self.assertIn("archive output only", payload["error"])

    def test_plan_rejects_work_above_public_limit(self) -> None:
        acquired = 0
        try:
            for _ in range(MAX_CONCURRENT_PUBLIC_WORK):
                self.assertTrue(self.session.work_slots.acquire(blocking=False))
                acquired += 1
            host = f"127.0.0.1:{self.server.server_address[1]}"
            body = json.dumps(
                {
                    "config": sample_config(
                        Path("/tmp/unused"),
                        output_mode="archive",
                    ).to_dict(),
                },
            )
            self.connection.request(
                "POST",
                "/api/plan",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Origin": f"http://{host}",
                },
            )

            response = self.connection.getresponse()
            payload = json.loads(response.read())
        finally:
            for _ in range(acquired):
                self.session.work_slots.release()

        self.assertEqual(429, response.status)
        self.assertIn("busy", payload["error"])

    def test_cross_origin_posts_are_rejected(self) -> None:
        body = json.dumps({})
        self.connection.request(
            "POST",
            "/api/plan",
            body=body,
            headers={
                "Content-Type": "application/json",
                "Origin": "https://attacker.example",
            },
        )

        response = self.connection.getresponse()
        payload = json.loads(response.read())

        self.assertEqual(403, response.status)
        self.assertEqual("invalid origin", payload["error"])


class WizardUiContractTest(unittest.TestCase):
    def test_ui_exposes_schema_three_project_settings_step(self) -> None:
        web_root = SCRIPTS_ROOT / "setup_wizard" / "web"
        html = (web_root / "index.html").read_text(encoding="utf-8")
        script = (web_root / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="project-settings"', html)
        self.assertIn("Project settings", html)
        self.assertIn("schemaVersion: 3", script)
        self.assertIn("applicationId:", script)
        self.assertIn("displayName:", script)
        self.assertIn("projectSettings:", script)
        self.assertIn("postsBackendUrl:", script)

    def test_ui_is_local_accessible_and_reduced_motion_aware(self) -> None:
        web_root = SCRIPTS_ROOT / "setup_wizard" / "web"
        html = (web_root / "index.html").read_text(encoding="utf-8")
        css = (web_root / "styles.css").read_text(encoding="utf-8")
        script = (web_root / "app.js").read_text(encoding="utf-8")

        self.assertIn('aria-label="Wizard progress"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('id="ai-free"', html)
        self.assertIn('value="archive"', html)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("[hidden] { display: none !important; }", css)
        self.assertEqual(2, css.count("--surface-sidebar:"))
        self.assertEqual(2, css.count("--surface-translucent:"))
        self.assertIn("background: var(--surface-sidebar);", css)
        self.assertEqual(
            2,
            css.count("background: var(--surface-translucent);"),
        )
        complete_icon_rule = css.split(
            ".step-list li.complete span::after",
            maxsplit=1,
        )[1].split("}", maxsplit=1)[0]
        self.assertIn('content: "";', complete_icon_rule)
        self.assertIn("position: absolute;", complete_icon_rule)
        self.assertIn("transform: rotate(45deg);", complete_icon_rule)
        self.assertNotIn("✓", complete_icon_rule)
        self.assertNotIn("https://", html)
        self.assertIn("X-Setup-Token", script)
        self.assertIn('schemaVersion: 3', script)
        self.assertIn('fetch("/api/archive"', script)


if __name__ == "__main__":
    unittest.main()
