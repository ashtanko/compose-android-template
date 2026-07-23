package dev.shtanko.androidlab.convention

import com.android.build.api.dsl.ApplicationExtension
import com.joetr.compose.guard.ComposeCompilerCheckExtension
import com.joetr.compose.guard.ComposeCompilerExtension
import dev.shtanko.androidlab.configureAndroidCompose
import dev.shtanko.androidlab.configureComposeGuard
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.getByType

class AndroidApplicationComposeConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "androidlab.android.application")
            apply(plugin = "org.jetbrains.kotlin.plugin.compose")
            apply(plugin = "com.joetr.compose.guard")

            val extension = extensions.getByType<ApplicationExtension>()
            configureAndroidCompose(extension)
            configureComposeGuard(
                extensions.getByType<ComposeCompilerExtension>(),
                extensions.getByType<ComposeCompilerCheckExtension>(),
            )
        }
    }
}
