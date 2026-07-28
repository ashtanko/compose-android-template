package dev.shtanko.androidlab.convention

import com.android.build.api.dsl.TestExtension
import dev.shtanko.androidlab.libs
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies

class AndroidBenchmarkConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "androidlab.android.test")
            apply(plugin = "androidx.baselineprofile")

            extensions.configure<TestExtension> {
                defaultConfig {
                    minSdk = libs.findVersion("benchmarkMinSdk").get().requiredVersion.toInt()
                    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
                    testInstrumentationRunnerArguments["listener"] =
                        "androidx.benchmark.junit4.SideEffectRunListener"
                }
            }

            dependencies {
                "implementation"(libs.findLibrary("androidx-benchmark-macro").get())
                "implementation"(libs.findLibrary("androidx-test-ext").get())
                "implementation"(libs.findLibrary("androidx-test-runner").get())
                "implementation"(libs.findLibrary("androidx-uiautomator").get())
            }
        }
    }
}
