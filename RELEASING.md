# Release signing

The recommended setup is to use [Play App Signing](https://developer.android.com/studio/publish/app-signing#app-signing-google-play)
and keep only the separate **upload key** on developer machines and GitHub Actions. Google Play
protects the app-signing key, while a lost or compromised upload key can be reset without changing
the identity of the installed app.

If the app is already published, use the upload key currently registered in Play Console. Do not
replace it with a newly generated key unless the Play Console upload-key reset process is complete.

Do not commit a production keystore, passwords, `key.properties`, or a Base64-encoded key. Keep an
independent encrypted backup of the upload keystore and its credentials.

## Local release

### Generate a new upload key

For a new app, run the interactive generator:

```bash
make generate-release-key
```

It creates `release/upload-keystore.p12` and `key.properties` by default, refuses to overwrite
either file, applies owner-only permissions, and prompts for one strong password used for both the
keystore and key. Choose an external keystore path when prompted if you do not want the key stored
under the ignored repository tree.

The equivalent command with explicit certificate identity is:

```bash
scripts/generate-release-key.sh \
  --keystore /absolute/path/to/upload-keystore.p12 \
  --alias upload \
  --dname "CN=Your Name, OU=Mobile, O=Your Organization, C=PT"
```

The generated PKCS#12 keystore contains a 4096-bit RSA upload certificate valid for 10,000 days,
which exceeds Android's recommended minimum of 25 years. The script uses JDK `keytool`, so select
the repository's required JDK before running it.

If the app is already published, do not generate a replacement unless Play Console expects a new
upload certificate as part of its upload-key reset process.

### Configure an existing key

1. Copy the tracked example:

   ```bash
   cp key.properties.example key.properties
   chmod 600 key.properties
   ```

2. Fill in all four values:

   ```properties
   storeFile=/absolute/path/to/upload-keystore.p12
   storePassword=your-keystore-password
   keyAlias=your-upload-key-alias
   keyPassword=your-key-password
   ```

   An absolute keystore path outside the repository is preferred. `key.properties`, `*.jks`,
   `*.keystore`, `*.p12`, and `*.pfx` are ignored as a second line of defense, but ignored files can
   still be exposed by backups, logs, or accidental force-adds.

3. Build the signed Android App Bundle:

   ```bash
   make release
   ```

The bundle is written under `app/build/outputs/bundle/release/`. A release task fails with a clear
error if the file is missing, any value is blank, or the keystore path does not exist. Debug builds
do not require release credentials.

Before each Play upload, increment and commit `versionCode` and update `versionName` when
appropriate.

## GitHub Actions release

The manual [`Release`](.github/workflows/release.yml) workflow:

1. accepts runs only from the repository's default branch;
2. runs the same host verification as pull requests before requesting signing access;
3. waits on the protected `production` environment;
4. reconstructs the upload keystore in the ephemeral runner's temporary directory;
5. builds a signed AAB with Gradle configuration caching disabled for the signing invocation;
6. uploads the AAB and R8 `mapping.txt` as a short-lived workflow artifact; and
7. removes the temporary keystore even when the build fails.

It intentionally does not publish to Google Play. Download and inspect the workflow artifact, then
upload the AAB through Play Console. This keeps the first version of the release pipeline small and
avoids adding a Play service-account credential. Automated Play upload can be added later as a
separate deployment step in the same protected environment.

### 1. Create and protect the environment

In the repository, open **Settings → Environments → New environment** and create `production`.
Restrict deployment branches to the default branch. When the repository plan supports it, add a
required reviewer and prevent self-review. Environment secrets are unavailable to the release job
until its protection rules pass.

If environment secrets are unavailable for a private repository on the current GitHub plan, add
the same four names under **Settings → Secrets and variables → Actions → Repository secrets**. The
workflow does not change, but approval no longer gates access to those repository-level secrets;
the protected environment is the preferred setup.

### 2. Add four environment secrets

Open **Settings → Environments → production → Environment secrets** and add:

| Secret | Value |
| --- | --- |
| `SIGNING_KEYSTORE_BASE64` | Base64 text of the upload keystore file |
| `SIGNING_STORE_PASSWORD` | Keystore password |
| `SIGNING_KEY_ALIAS` | Upload-key alias |
| `SIGNING_KEY_PASSWORD` | Upload-key password |

Base64 is only a binary-to-text encoding; GitHub's encrypted secret storage provides the
protection. GitHub secrets have a size limit, so confirm the encoded file is below the current
[GitHub secret limit](https://docs.github.com/en/actions/reference/security/secrets#limits-for-secrets).

With [GitHub CLI](https://cli.github.com/) authenticated for this repository, the keystore secret
can be uploaded without writing an encoded copy into the project:

macOS:

```bash
base64 -i /absolute/path/to/upload-keystore.p12 \
  | gh secret set --env production SIGNING_KEYSTORE_BASE64
```

Linux:

```bash
base64 -w 0 /absolute/path/to/upload-keystore.p12 \
  | gh secret set --env production SIGNING_KEYSTORE_BASE64
```

Add the three text secrets interactively so they do not enter shell history:

```bash
gh secret set --env production SIGNING_STORE_PASSWORD
gh secret set --env production SIGNING_KEY_ALIAS
gh secret set --env production SIGNING_KEY_PASSWORD
```

Confirm only the secret names:

```bash
gh secret list --env production
```

### 3. Build a release

Commit the intended version and wait for normal CI to pass. Then open **Actions → Release → Run
workflow**, select the default branch, and approve the `production` environment when prompted.
Download the `release-<commit SHA>` artifact after the workflow finishes.

## CI signing contract

Gradle accepts either the complete local `key.properties` file or this complete environment
variable set:

```text
SIGNING_KEYSTORE_PATH
SIGNING_STORE_PASSWORD
SIGNING_KEY_ALIAS
SIGNING_KEY_PASSWORD
```

The workflow creates `SIGNING_KEYSTORE_PATH`; it is not a GitHub secret. Sources are never mixed:
if any signing environment variable is set, all four must be present. This prevents a partially
configured runner from silently falling back to a developer file.

For key rotation or compromise, follow the Play Console upload-key reset process, replace all four
`production` secrets together, and retain the old workflow run and Play release records for audit.
