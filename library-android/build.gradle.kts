/*
 * Designed and developed by 2026 ashtanko (Oleksii Shtanko)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
plugins {
    alias(libs.plugins.androidlab.android.library)
    alias(libs.plugins.androidlab.android.library.compose)
    alias(libs.plugins.androidlab.android.library.jacoco)
    alias(libs.plugins.android.junit5)
    alias(libs.plugins.roborazzi)
}

val isGithubActions = System.getenv("GITHUB_ACTIONS")?.toBoolean() == true
val isCI = providers.environmentVariable("CI").isPresent

android {
    namespace = "app.template.library.android"

    compileSdk = libs.versions.compileSdk.get().toInt()

    defaultConfig {
        minSdk = libs.versions.minSdk.get().toInt()

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        consumerProguardFiles("consumer-rules.pro")
        testInstrumentationRunnerArguments["runnerBuilder"] =
            "de.mannodermaus.junit5.AndroidJUnit5Builder"
    }

    testOptions {
        // Required for Robolectric
        unitTests.isIncludeAndroidResources = true
        unitTests.isReturnDefaultValues = true

        unitTests.all {
            it.useJUnitPlatform()
            it.jvmArgs(
                "--add-opens",
                "java.base/java.util=ALL-UNNAMED",
                "--add-opens",
                "java.base/java.lang=ALL-UNNAMED",
                "--add-opens",
                "java.base/java.time=ALL-UNNAMED",
                "-Xshare:off",
            )
        }
    }
}

tasks {
    withType<Test> {
        useJUnitPlatform()
    }
}

project.gradle.startParameter.excludedTaskNames.apply {
    val excludedTasks = listOf(
        "testDebugScreenshotTest",
        "testReleaseScreenshotTest",
        "testBenchmarkReleaseScreenshotTest",
        "testBenchmarkScreenshotTest",
        "testNonMinifiedReleaseScreenshotTest",
        "testBenchmarkUnitTest",
        "testReleaseUnitTest",
        "finalizeTestRoborazziRelease",
    )
    if (isCI || isGithubActions) {
        excludedTasks.forEach(::add)
    }
}

dependencies {
    libs.apply {
        androidx.apply {
            compose.apply {
                api(foundation)
                api(foundation.layout)
                api(icons.extended)
                api(material3.adaptive)
                api(material3.adaptive.layout)
                api(material3.adaptive.navigation)
                api(material3.adaptive.navigationSuite)
                api(materialWindow)
            }
            ui.apply {
                api(text.google.fonts)
                debugApi(test.manifest)
            }
        }

        junit5.apply {
            testImplementation(api)
            testImplementation(params)

            testRuntimeOnly(jupiterEngine)
            testRuntimeOnly(vintageEngine)
        }

        androidTestImplementation(libs.junit5.api)
        androidTestImplementation(libs.android.junit5.test.core)
        androidTestRuntimeOnly(libs.android.junit5.test.runner)

        testImplementation(assertj.core)
    }
}
