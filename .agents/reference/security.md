# Android security reference

## Principle

Minimize exposed surfaces, treat every external input as untrusted, and keep secrets out of the
client and repository. Security decisions belong at component, data, network, build, and CI
boundaries rather than in scattered call-site checks.

The template currently exports its launcher activity intentionally in
[`app/src/main/AndroidManifest.xml`](../../app/src/main/AndroidManifest.xml). Any additional exported
activity, service, receiver, or provider requires an explicit use case and security review.

## Components and intents

- Set `android:exported="false"` for components that do not require calls from other applications.
- Protect deliberately exported non-launcher components with an appropriate permission and validate
  the calling identity when sensitive work is exposed.
- Use explicit intents for internal navigation and service calls.
- Validate action, data, categories, extras, URI grants, and caller assumptions for incoming intents.
- Apply the same validation in both `onCreate` and `onNewIntent`.
- Never launch a nested intent from untrusted input without a strict allowlist or
  `IntentSanitizer`.
- Use `PendingIntent.FLAG_IMMUTABLE` by default. A mutable pending intent must have an explicit
  target and a documented requirement such as direct reply.
- Register internal dynamic receivers as not exported. Protect cross-application broadcasts with a
  signature permission where appropriate.
- Do not use sticky broadcasts or deprecated local-broadcast infrastructure for in-app events.

## Providers, services, and storage

- Keep application-only providers non-exported.
- Protect exported providers with read/write permissions, narrow URI grants, strict projections,
  and parameterized selections.
- Verify the calling UID and signing identity on each sensitive exported Binder operation; do not
  rely on a one-time bind check.
- Store only data the product needs, choose retention deliberately, and avoid placing tokens or PII
  in logs, analytics attributes, saved state, or unencrypted shared files.
- Use platform-backed key storage for cryptographic keys. Do not invent custom encryption schemes.
- Review `android:allowBackup`, data-extraction rules, and profiling exposure for the product before
  shipping; template defaults are not a product threat model.

## Network and web content

- Use HTTPS and do not enable cleartext traffic globally. Scope any debug exception to a debug-only
  network security configuration.
- Validate server responses as untrusted input and keep authentication/authorization decisions on
  the server.
- Do not add certificate pinning by default; if the threat model requires it, document rotation and
  recovery behavior.
- If a WebView is introduced, allowlist navigation, disable unnecessary file/content access and
  JavaScript capabilities, and never expose a JavaScript bridge to untrusted content.

## Secrets, signing, and configuration

- Never commit `local.properties`, production keystores, signing passwords, tokens, or environment
  files.
- Values placed in resources, assets, native code, or `BuildConfig` can be recovered from an APK.
  Treat every client-side value as configuration, not secure secret storage.
- Keep privileged API credentials and authorization enforcement on a trusted backend.
- Preserve the documented CI environment-variable contract for release signing.
- Use the repository's template debug keystore only for local/template purposes.

## Permissions and privacy

- Request the minimum Android permission at the moment the related user action needs it.
- Provide a usable denied state and handle permanent denial without loops or coercion.
- Prefer system pickers, photo pickers, Credential Manager, and scoped storage APIs over broad
  permissions when they satisfy the use case.
- Keep Play data-safety declarations, SDK behavior, analytics collection, and manifest permissions
  aligned. Recheck merged manifests after adding SDKs.

## Dependencies and CI

- Add dependencies through [`gradle/libs.versions.toml`](../../gradle/libs.versions.toml) and review
  their transitive surface with Dependency Guard.
- Prefer narrowly scoped CI permissions. A job that only reads and verifies code should not receive
  write permissions.
- Review third-party build actions and plugins before adoption; pin and update them through the
  repository's dependency-maintenance process.
- Do not automatically accept a new dependency baseline without reviewing why the dependency graph
  changed.

## Review checklist

- Which components or entry points became reachable from outside the app?
- What input crosses the trust boundary, and where is it validated?
- Could any logged, persisted, backed-up, or analytics data contain a credential or user data?
- Does a new permission or SDK change privacy declarations or merged-manifest behavior?
- Are pending intents immutable and internal intents explicit?
- Are network and WebView exceptions restricted to the smallest environment and host set?
- Are CI permissions and signing inputs no broader than required?

## Verification

- Inspect the merged manifest for each affected variant.
- Run Android lint for the owning module.
- Add tests for malformed extras, unauthorized callers, denied permissions, and unsafe redirect
  attempts when those surfaces change.
- Run Dependency Guard after dependency changes.
- Never weaken lint, exported flags, permission checks, or baseline policy merely to make a build
  pass.
