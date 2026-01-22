package app.template.home.navigation

import androidx.navigation3.runtime.NavKey
import kotlinx.serialization.Serializable

sealed interface Screen {
    @Serializable
    public data object ScreenA : NavKey

    @Serializable
    public data object ScreenB : NavKey

    @Serializable
    public data object ScreenC : NavKey
}
