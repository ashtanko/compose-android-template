package dev.shtanko.androidlab.convention

import com.android.build.api.dsl.ApplicationExtension
import com.android.build.api.dsl.LibraryExtension
import dev.shtanko.androidlab.libs
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies

class AndroidComposeScreenshotConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "com.android.compose.screenshot")

            pluginManager.withPlugin("com.android.application") {
                extensions.configure<ApplicationExtension> {
                    experimentalProperties["android.experimental.enableScreenshotTest"] = true
                }
            }
            pluginManager.withPlugin("com.android.library") {
                extensions.configure<LibraryExtension> {
                    experimentalProperties["android.experimental.enableScreenshotTest"] = true
                }
            }

            dependencies {
                "screenshotTestImplementation"(
                    libs.findLibrary("androidx-compose-ui-tooling").get(),
                )
            }
        }
    }
}
