import com.android.build.api.dsl.TestExtension
import dev.shtanko.androidlab.configureDetekt
import dev.shtanko.androidlab.configureKotlinAndroid
import dev.shtanko.androidlab.configureSpotlessForAndroid
import io.gitlab.arturbosch.detekt.extensions.DetektExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.getByType

class AndroidTestConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.android.test")
                apply("io.gitlab.arturbosch.detekt")
            }

            configureDetekt(extensions.getByType<DetektExtension>())

            extensions.configure<TestExtension> {
                configureKotlinAndroid(this)
                defaultConfig.targetSdk = 37
            }
            configureSpotlessForAndroid()
        }
    }
}
