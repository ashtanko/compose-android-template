buildscript {
    repositories {
        google()
        mavenCentral()
    }
}
// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.android.library) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
    alias(libs.plugins.compose.guard) apply false
    alias(libs.plugins.detekt) apply false
    alias(libs.plugins.sonarqube) apply false
    alias(libs.plugins.ksp) apply false
    alias(libs.plugins.kover) apply false
    alias(libs.plugins.kotlin.parcelize) apply false
    alias(libs.plugins.hilt) apply false
    alias(libs.plugins.android.test) apply false
    alias(libs.plugins.baselineprofile) apply false
    alias(libs.plugins.roborazzi) apply false
    alias(libs.plugins.google.android.libraries.mapsplatform.secrets.gradle.plugin) apply false
    alias(libs.plugins.dependencyGuard) apply false
}

// CI Task Exclusion Logic
val isCI = System.getenv("CI") == "true" || System.getenv("GITHUB_ACTIONS") == "true"

val excludedTasks = setOf(
    "testDebugScreenshotTest",
    "testReleaseScreenshotTest",
    "testBenchmarkReleaseScreenshotTest",
    "testBenchmarkScreenshotTest",
    "testNonMinifiedReleaseScreenshotTest",
    "testBenchmarkUnitTest",
    "testReleaseUnitTest",
    "finalizeTestRoborazziRelease"
)

tasks.configureEach {
    if (name in excludedTasks && isCI) {
        enabled = false
    }
}
