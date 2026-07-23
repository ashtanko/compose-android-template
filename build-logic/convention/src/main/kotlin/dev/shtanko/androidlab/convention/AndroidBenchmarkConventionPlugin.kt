package dev.shtanko.androidlab.convention

import dev.shtanko.androidlab.libs
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.dependencies

class AndroidBenchmarkConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "androidlab.android.test")
            apply(plugin = "androidx.baselineprofile")

            dependencies {
                "implementation"(libs.findLibrary("androidx-benchmark-macro").get())
                "implementation"(libs.findLibrary("androidx-test-core").get())
                "implementation"(libs.findLibrary("androidx-espresso-core").get())
                "implementation"(libs.findLibrary("androidx-test-ext").get())
                "implementation"(libs.findLibrary("androidx-test-rules").get())
                "implementation"(libs.findLibrary("androidx-test-runner").get())
                "implementation"(libs.findLibrary("androidx-uiautomator").get())
                "implementation"(libs.findLibrary("androidx-junit").get())
            }
        }
    }
}
