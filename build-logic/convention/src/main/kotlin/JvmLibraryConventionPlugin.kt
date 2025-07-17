import dev.shtanko.androidlab.configureDetekt
import dev.shtanko.androidlab.configureKotlinJvm
import dev.shtanko.androidlab.libs
import io.gitlab.arturbosch.detekt.extensions.DetektExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.getByType

class JvmLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("org.jetbrains.kotlin.jvm")
                apply("androidlab.android.lint")

                apply(
                    libs.findLibrary("detekt-gradle").get().get().group.toString()
                )
            }
            configureKotlinJvm()
            configureDetekt(extensions.getByType<DetektExtension>())
        }
    }
}
