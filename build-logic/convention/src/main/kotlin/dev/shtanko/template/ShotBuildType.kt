package dev.shtanko.template

/**
 * This is shared between :app and :benchmarks module to provide configurations type safety.
 */
enum class ShotBuildType(val applicationIdSuffix: String? = null) {
  DEBUG(".debug"),
  RELEASE,
}
