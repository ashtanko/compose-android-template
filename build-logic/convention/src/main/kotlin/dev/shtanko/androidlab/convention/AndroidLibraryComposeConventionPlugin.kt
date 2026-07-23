package dev.shtanko.androidlab.convention

import com.android.build.api.dsl.LibraryExtension
import com.joetr.compose.guard.ComposeCompilerCheckExtension
import com.joetr.compose.guard.ComposeCompilerExtension
import dev.shtanko.androidlab.configureAndroidCompose
import dev.shtanko.androidlab.configureComposeGuard
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.getByType

class AndroidLibraryComposeConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "androidlab.android.library")
            apply(plugin = "org.jetbrains.kotlin.plugin.compose")
            apply(plugin = "com.joetr.compose.guard")

            val extension = extensions.getByType<LibraryExtension>()
            configureAndroidCompose(extension)
            configureComposeGuard(
                extensions.getByType<ComposeCompilerExtension>(),
                extensions.getByType<ComposeCompilerCheckExtension>(),
            )
        }
    }
}
