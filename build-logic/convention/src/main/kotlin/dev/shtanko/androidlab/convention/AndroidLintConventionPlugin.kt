package dev.shtanko.androidlab.convention

import com.android.build.api.dsl.ApplicationExtension
import com.android.build.api.dsl.LibraryExtension
import com.android.build.api.dsl.Lint
import com.android.build.api.dsl.TestExtension
import dev.shtanko.androidlab.configureLint
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure

class AndroidLintConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            pluginManager.withPlugin("com.android.application") {
                configure<ApplicationExtension> {
                    configureLint(lint, checkDependencies = true)
                }
            }
            pluginManager.withPlugin("com.android.library") {
                configure<LibraryExtension> {
                    configureLint(lint, checkDependencies = false)
                }
            }
            pluginManager.withPlugin("com.android.test") {
                configure<TestExtension> {
                    configureLint(lint, checkDependencies = false)
                }
            }
            pluginManager.withPlugin("org.jetbrains.kotlin.jvm") {
                apply(plugin = "com.android.lint")
                configure<Lint> {
                    configureLint(this, checkDependencies = false)
                }
            }
        }
    }
}
