import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply

class AndroidFeatureApiConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "androidlab.android.library")
            apply(plugin = "org.jetbrains.kotlin.plugin.serialization")
        }
    }
}
