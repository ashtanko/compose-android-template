package dev.shtanko.androidlab.convention

import com.android.build.api.dsl.LibraryExtension
import dev.shtanko.androidlab.configureDetekt
import dev.shtanko.androidlab.configureKotlinAndroid
import dev.shtanko.androidlab.libs
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.invoke

class AndroidLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "com.android.library")
            apply(plugin = "androidlab.android.lint")
            apply(plugin = "androidlab.spotless")
            apply(plugin = "io.gitlab.arturbosch.detekt")

            configureDetekt()

            extensions.configure<LibraryExtension> {
                configureKotlinAndroid(this)
                testOptions.targetSdk =
                    libs.findVersion("targetSdk").get().requiredVersion.toInt()
                defaultConfig.testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
                testOptions.animationsDisabled = true
                // The resource prefix is derived from the module name,
                // so resources inside ":core:module1" must be prefixed with "core_module1_"
                resourcePrefix =
                    path.split("""\W""".toRegex()).drop(1).distinct().joinToString(separator = "_")
                        .lowercase() + "_"

                testOptions {
                    // Required for Robolectric
                    unitTests.isIncludeAndroidResources = true
                    unitTests.isReturnDefaultValues = true

                    unitTests.all {
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
            dependencies {
                "implementation"(libs.findLibrary("androidx.tracing.ktx").get())
            }
        }
    }
}
