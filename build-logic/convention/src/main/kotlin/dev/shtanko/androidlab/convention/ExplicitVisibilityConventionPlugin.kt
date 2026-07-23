package dev.shtanko.androidlab.convention

import io.gitlab.arturbosch.detekt.Detekt
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.withType

public class ExplicitVisibilityConventionPlugin : Plugin<Project> {
    public override fun apply(target: Project) {
        with(target) {
            pluginManager.withPlugin("io.gitlab.arturbosch.detekt") {
                tasks.withType<Detekt>().configureEach {
                    if (name != "detektCompose") {
                        config.from(
                            rootProject.file(
                                "config/detekt/detekt-explicit-visibility.yml",
                            ),
                        )
                    }
                }
            }
        }
    }
}
