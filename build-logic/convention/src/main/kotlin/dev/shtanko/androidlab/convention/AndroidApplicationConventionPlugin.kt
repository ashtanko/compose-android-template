package dev.shtanko.androidlab.convention

import com.android.build.api.dsl.ApplicationExtension
import dev.shtanko.androidlab.configureDetekt
import dev.shtanko.androidlab.configureGradleManagedDevices
import dev.shtanko.androidlab.configureKotlinAndroid
import dev.shtanko.androidlab.libs
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure

class AndroidApplicationConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply(plugin = "com.android.application")
                apply(plugin = "androidlab.android.lint")
                apply(plugin = "androidlab.spotless")
                apply(plugin = "io.gitlab.arturbosch.detekt")
                apply(plugin = "com.dropbox.dependency-guard")
            }

            configureDetekt()

            extensions.configure<ApplicationExtension> {
                configureKotlinAndroid(this)
                configureGradleManagedDevices(this)
                defaultConfig {
                    targetSdk = libs.findVersion("targetSdk").get().requiredVersion.toInt()
                    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
                }
                testOptions {
                    animationsDisabled = true
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
        }
    }
}
