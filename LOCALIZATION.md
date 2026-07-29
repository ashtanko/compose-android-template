# Localization

## Strategy

- English (United States) is the complete fallback locale in unqualified `values/` directories.
  `app/src/main/res/resources.properties` declares that policy to the Android Gradle Plugin.
- Each Android module owns its source strings and translations. Feature text stays with the feature;
  application-wide text stays in `app`.
- European Portuguese uses the `pt-PT` BCP 47 locale and Android's `values-pt-rPT` resource
  qualifier.
- The application generates its locale configuration from app and library resources at build time,
  so supported languages appear in Android's per-app language settings without a hand-maintained
  locale list.
- Product names or technical tokens that must not be translated use
  `translatable="false"`. All other production UI text must use resources.
- Debug builds enable Android's `en-XA` expansion pseudolocale and `ar-XB` RTL pseudolocale.

Android's official guidance underpins these choices:

- [Localize your app](https://developer.android.com/guide/topics/resources/localization)
- [Per-app language preferences](https://developer.android.com/guide/topics/resources/app-languages)
- [Test with pseudolocales](https://developer.android.com/guide/topics/resources/pseudolocales)
- [String and plural resources](https://developer.android.com/guide/topics/resources/string-resource)
- [Translations Editor](https://developer.android.com/studio/write/translations-editor)

## Translation workflow

1. Add complete default text to the owning module's `src/main/res/values/strings.xml`. Use a
   descriptive, module-prefixed key. Add a translator comment when the UI context is not obvious.
2. Keep a whole sentence in one resource. Do not concatenate fragments. Use positional formatter
   arguments such as `%1$s` and `%2$d`, and use `<plurals>` only for grammatically plural text.
3. Add the locale file under the same module. For Portuguese (Portugal), use
   `src/main/res/values-pt-rPT/strings.xml`.
4. Run the fast, dependency-free gate:

   ```bash
   make localization-check
   ```

   The check discovers localized modules and rejects common hardcoded Compose literals in production
   files, malformed XML, missing or stale resources, empty values, incompatible
   string-array/plural shapes, and changed formatter argument indexes or types. Preview-only files
   remain free to use developer-facing sample text. Its unit tests run first.
5. Produce a translator or reviewer catalog when needed:

   ```bash
   make localization-report LOCALE=pt-PT FORMAT=table
   python3 scripts/localization.py report \
       --locale pt-PT \
       --format csv \
       --output /tmp/pt-PT-translations.csv
   ```

   `FORMAT` supports `table`, `csv`, and `json`. The structured formats include module, key, source
   text, translation, status, and source paths, which makes them suitable for review or import into
   a translation-management system.
6. Have a native speaker review wording in context. Automated checks prove resource integrity, not
   linguistic quality.

When adding another locale, create at least one matching locale directory, translate every
localizable default resource across all owning modules, and run `make localization-check`. The
generated locale configuration picks it up automatically.

## Validation matrix

| Layer | What it catches | Command or action |
| --- | --- | --- |
| Repository resource gate | Missing, stale, empty, or format-incompatible translations | `make localization-check` |
| Android resource tooling | Invalid qualifiers, resource linking, lint localization issues | `./gradlew assembleDebug lint` |
| Expansion pseudolocale | Hardcoded text, truncation, fixed-width layouts, concatenated fragments | Run debug with `English (XA)` |
| RTL pseudolocale | Absolute left/right assumptions and bidi/layout issues | Run debug with `AR (XB)` |
| Target locale | Wording, line wrapping, accessibility labels, locale fallback | Select Português (Portugal) in the app's Android language settings |
| Compose preview | Fast review at representative dimensions and font scales | Use `@Preview(locale = "pt-rPT", fontScale = 1.3f)` |
| Screenshot/device test | Clipping and visual regressions in important UI states | Add locale/font-scale preview screenshot cases, then review intentional goldens |
| Human review | Meaning, tone, terminology, and cultural fit | Native-speaker review on a device |

For release confidence, exercise compact and expanded windows, a large font scale, light and dark
themes, an unsupported locale to verify English fallback, `pt-PT`, `en-XA`, and `ar-XB`. Check
TalkBack output for translated content descriptions and controls as part of the target-locale pass.
