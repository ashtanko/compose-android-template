import dev.shtanko.androidlab.configureDetekt
import dev.shtanko.androidlab.configureKotlinJvm
import dev.shtanko.androidlab.libs
import io.gitlab.arturbosch.detekt.extensions.DetektExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.getByType

class JvmLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply(plugin = "org.jetbrains.kotlin.jvm")
                apply(plugin = "androidlab.android.lint")

                apply(
                    libs.findLibrary("detekt-gradle").get().get().group
                )
            }
            configureKotlinJvm()
            configureDetekt(extensions.getByType<DetektExtension>())
            dependencies {
                "testImplementation"(libs.findLibrary("junit5-api").get())
                "testImplementation"(libs.findLibrary("junit5-params").get())
                "testImplementation"(libs.findLibrary("assertj-core").get())
                "testRuntimeOnly"(libs.findLibrary("junit5-jupiterEngine").get())
                "testRuntimeOnly"(libs.findLibrary("junit5-vintageEngine").get())
                "testImplementation"(libs.findLibrary("kotlin.test").get())
            }
        }
    }
}
