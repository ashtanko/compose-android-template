package dev.shtanko.androidlab

import com.joetr.compose.guard.ComposeCompilerCheckExtension
import com.joetr.compose.guard.ComposeCompilerExtension

internal fun configureComposeGuard(
    composeGuard: ComposeCompilerExtension,
    composeGuardCheck: ComposeCompilerCheckExtension,
) {
    composeGuard.configureKotlinTasks.set(false)
    composeGuardCheck.apply {
        errorOnNewDynamicProperties.set(false)
        errorOnNewUnstableClasses.set(false)
        errorOnNewUnstableParams.set(false)
        reportAllOnMissingBaseline.set(true)
    }
}
