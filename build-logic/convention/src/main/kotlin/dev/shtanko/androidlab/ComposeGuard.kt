package dev.shtanko.androidlab

import com.joetr.compose.guard.ComposeCompilerCheckExtension
import org.gradle.api.Project

internal fun Project.configureComposeGuard(extension: ComposeCompilerCheckExtension) =
    extension.apply {
        errorOnNewUnstableParams.set(false)
    }
