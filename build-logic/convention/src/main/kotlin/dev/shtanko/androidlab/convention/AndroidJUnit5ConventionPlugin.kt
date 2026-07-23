package dev.shtanko.androidlab.convention

import com.android.build.api.dsl.ApplicationExtension
import com.android.build.api.dsl.LibraryExtension
import de.mannodermaus.gradle.plugins.junit5.dsl.AndroidJUnitPlatformExtension
import dev.shtanko.androidlab.libs
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.tasks.testing.Test
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.withType

class AndroidJUnit5ConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "de.mannodermaus.android-junit5")

            extensions.configure<AndroidJUnitPlatformExtension> {
                // Coverage comes from the androidlab Jacoco conventions. The JUnit 5 plugin's
                // legacy Jacoco integration is not compatible with AGP 9.
                jacocoOptions.taskGenerationEnabled.set(false)
            }

            pluginManager.withPlugin("com.android.application") {
                extensions.configure<ApplicationExtension> {
                    defaultConfig.testInstrumentationRunnerArguments["runnerBuilder"] =
                        ANDROID_JUNIT_5_RUNNER_BUILDER
                }
            }
            pluginManager.withPlugin("com.android.library") {
                extensions.configure<LibraryExtension> {
                    defaultConfig.testInstrumentationRunnerArguments["runnerBuilder"] =
                        ANDROID_JUNIT_5_RUNNER_BUILDER
                }
            }

            tasks.withType<Test>().configureEach {
                useJUnitPlatform()
            }

            dependencies {
                "testImplementation"(libs.findLibrary("junit5-api").get())
                "testImplementation"(libs.findLibrary("junit5-params").get())
                "testImplementation"(libs.findLibrary("assertj-core").get())
                "testImplementation"(libs.findLibrary("kotlin-test").get())
                "testRuntimeOnly"(libs.findLibrary("junit5-jupiterEngine").get())
                "testRuntimeOnly"(libs.findLibrary("junit5-vintageEngine").get())

                "androidTestImplementation"(libs.findLibrary("junit5-api").get())
                "androidTestImplementation"(libs.findLibrary("junit5-params").get())
                "androidTestImplementation"(libs.findLibrary("android-junit5-test-core").get())
                "androidTestRuntimeOnly"(libs.findLibrary("android-junit5-test-runner").get())
            }
        }
    }
}

private const val ANDROID_JUNIT_5_RUNNER_BUILDER =
    "de.mannodermaus.junit5.AndroidJUnit5Builder"
