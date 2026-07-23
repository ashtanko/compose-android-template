package dev.shtanko.androidlab
import dev.shtanko.androidlab.detekt.DetektRulesClasspathMarker
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

        if (name == "detektCompose") {
            config.setFrom(file("$rootDir/config/detekt/detekt-compose.yml"))
            setSource(files("src/main"))
        } else {
            config.setFrom(
                file("$rootDir/config/detekt/detekt.yml"),
                file("$rootDir/config/detekt/detekt-compose.yml"),
            )
            setSource(files("src"))
        }
        include("**/*.kt", "**/*.kts")
        exclude("**/resources/**")

        val taskName = name
        reports {
            listOf(xml, html, txt, md, sarif).forEach {
                it.required.set(true)
            }
            if (taskName == "detektCompose" || taskName == "detektAutoCorrect") {
                xml.outputLocation.set(layout.buildDirectory.file("reports/detekt/$taskName.xml"))
                html.outputLocation.set(layout.buildDirectory.file("reports/detekt/$taskName.html"))
                txt.outputLocation.set(layout.buildDirectory.file("reports/detekt/$taskName.txt"))
                md.outputLocation.set(layout.buildDirectory.file("reports/detekt/$taskName.md"))
                sarif.outputLocation.set(
                    layout.buildDirectory.file("reports/detekt/$taskName.sarif"),
                )
            }
        }
    }

    tasks.register("detektCompose", Detekt::class.java) {
        group = "verification"
        description = "Runs Compose-specific Detekt rules against production Kotlin sources."
    }

    tasks.register("detektAutoCorrect", Detekt::class.java) {
        group = "formatting"
        description = "Runs Detekt with auto-correction for rules that provide a safe fix."
        autoCorrect = true
    }

    tasks.withType<DetektCreateBaselineTask>().configureEach {
        jvmTarget = libs.findVersion("jvmTarget").get().requiredVersion
    }

    dependencies {
        val architectureRules = files(
            DetektRulesClasspathMarker::class.java.protectionDomain.codeSource.location,
        )
        "detektPlugins"(architectureRules)
        "detektPlugins"(libs.findLibrary("detekt-formatting").get())
        "detektPlugins"(libs.findLibrary("detekt-rules").get())
    }
}
