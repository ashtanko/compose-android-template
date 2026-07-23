package dev.shtanko.androidlab.convention

import com.android.build.api.dsl.TestExtension
import dev.shtanko.androidlab.configureDetekt
import dev.shtanko.androidlab.configureKotlinAndroid
import dev.shtanko.androidlab.libs
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure

class AndroidTestConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.android.test")
                apply("androidlab.android.lint")
                apply("androidlab.spotless")
                apply("io.gitlab.arturbosch.detekt")
            }

            configureDetekt()

            extensions.configure<TestExtension> {
                configureKotlinAndroid(this)
                defaultConfig.targetSdk =
                    libs.findVersion("targetSdk").get().requiredVersion.toInt()
            }
        }
    }
}
