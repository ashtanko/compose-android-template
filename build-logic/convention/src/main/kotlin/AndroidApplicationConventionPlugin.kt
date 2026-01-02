import com.android.build.gradle.internal.dsl.BaseAppModuleExtension
import dev.shtanko.androidlab.configureDetekt
import dev.shtanko.androidlab.configureKotlinAndroid
import io.gitlab.arturbosch.detekt.extensions.DetektExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.getByType

class AndroidApplicationConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply(plugin = "com.android.application")
                apply(plugin = "org.jetbrains.kotlin.android")
                apply(plugin = "io.gitlab.arturbosch.detekt")
                apply(plugin = "com.dropbox.dependency-guard")
            }

            configureDetekt(extensions.getByType<DetektExtension>())

            extensions.configure<BaseAppModuleExtension> {
                configureKotlinAndroid(this)
                defaultConfig.targetSdk = 35
            }
        }
    }
}
