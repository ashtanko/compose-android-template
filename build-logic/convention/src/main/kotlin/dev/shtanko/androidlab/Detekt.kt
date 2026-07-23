package dev.shtanko.androidlab

import io.gitlab.arturbosch.detekt.Detekt
import io.gitlab.arturbosch.detekt.DetektCreateBaselineTask
import org.gradle.api.Project
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.withType

internal fun Project.configureDetekt() {
    tasks.withType<Detekt>().configureEach {
        description = "Runs Detekt analysis for this module."
        parallel = true
        jvmTarget = libs.findVersion("jvmTarget").get().requiredVersion
        baseline.set(file("$rootDir/config/detekt/detekt-baseline.xml"))
        config.from(
            file("$rootDir/config/detekt/detekt.yml"),
            file("$rootDir/config/detekt/detekt-compose.yml"),
        )

        setSource(files("src"))
        include("**/*.kt", "**/*.kts")
        exclude("**/resources/**")

        reports {
            listOf(xml, html, txt, md, sarif).forEach {
                it.required.set(true)
            }
        }
    }

    tasks.withType<DetektCreateBaselineTask>().configureEach {
        jvmTarget = libs.findVersion("jvmTarget").get().requiredVersion
    }

    dependencies {
        "detektPlugins"(libs.findLibrary("detekt-formatting").get())
        "detektPlugins"(libs.findLibrary("detekt-rules").get())
    }
}
