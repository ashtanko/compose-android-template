import io.gitlab.arturbosch.detekt.Detekt
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    `kotlin-dsl`
    alias(libs.plugins.detekt)
    alias(libs.plugins.spotless)
}

group = "dev.shtanko.androidlab.buildlogic"

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

kotlin {
    compilerOptions {
        jvmTarget = JvmTarget.JVM_21
    }
}

spotless {
    kotlin {
        target("src/**/*.kt")
        ktlint(libs.versions.ktlintCli.get()).editorConfigOverride(
            mapOf("android" to "true"),
        )
        endWithNewline()
    }
    kotlinGradle {
        target("*.gradle.kts")
        ktlint(libs.versions.ktlintCli.get()).editorConfigOverride(
            mapOf("android" to "true"),
        )
        endWithNewline()
    }
}

detekt {
    buildUponDefaultConfig = true
    baseline = rootProject.file("../config/detekt/detekt-baseline.xml")
    config.setFrom(
        rootProject.file("../config/detekt/detekt.yml"),
        rootProject.file("../config/detekt/detekt-compose.yml"),
    )
    source.setFrom(files("src"))
}

tasks.withType<Detekt>().configureEach {
    jvmTarget = libs.versions.jvmTarget.get()
    reports {
        listOf(xml, html, txt, md, sarif).forEach {
            it.required.set(true)
        }
    }
}

dependencies {
    compileOnly(libs.android.gradlePlugin)
    compileOnly(libs.compose.gradlePlugin)
    compileOnly(libs.kotlin.gradlePlugin)
    compileOnly(libs.ksp.gradlePlugin)
    compileOnly(libs.room.gradlePlugin)
    compileOnly(libs.detekt.gradle)
    compileOnly(libs.spotless.gradlePlugin)
    compileOnly(libs.compose.guardPlugin)
    compileOnly(libs.dependencyGuard.gradlePlugin)
    compileOnly(libs.hilt.gradlePlugin)
    compileOnly(libs.android.junit5.gradlePlugin)
    compileOnly(libs.screenshot.gradlePlugin)
    compileOnly(libs.baselineprofile.gradlePlugin)
    compileOnly(libs.roborazzi.gradlePlugin)

    detektPlugins(libs.detekt.formatting)
    detektPlugins(libs.detekt.rules)
}

gradlePlugin {
    plugins {
        register("androidApplicationCompose") {
            id = "androidlab.android.application.compose"
            implementationClass =
                "dev.shtanko.androidlab.convention.AndroidApplicationComposeConventionPlugin"
        }
        register("androidApplication") {
            id = "androidlab.android.application"
            implementationClass =
                "dev.shtanko.androidlab.convention.AndroidApplicationConventionPlugin"
        }
        register("androidLibraryCompose") {
            id = "androidlab.android.library.compose"
            implementationClass =
                "dev.shtanko.androidlab.convention.AndroidLibraryComposeConventionPlugin"
        }
        register("androidLibrary") {
            id = "androidlab.android.library"
            implementationClass =
                "dev.shtanko.androidlab.convention.AndroidLibraryConventionPlugin"
        }
        register("androidFeature") {
            id = "androidlab.android.feature"
            implementationClass =
                "dev.shtanko.androidlab.convention.AndroidFeatureConventionPlugin"
        }
        register("hilt") {
            id = "androidlab.hilt"
            implementationClass = "dev.shtanko.androidlab.convention.HiltConventionPlugin"
        }
        register("spotless") {
            id = "androidlab.spotless"
            implementationClass = "dev.shtanko.androidlab.convention.SpotlessConventionPlugin"
        }
        register("androidLint") {
            id = "androidlab.android.lint"
            implementationClass = "dev.shtanko.androidlab.convention.AndroidLintConventionPlugin"
        }
        register("androidApplicationJacoco") {
            id = "androidlab.android.application.jacoco"
            implementationClass =
                "dev.shtanko.androidlab.convention.AndroidApplicationJacocoConventionPlugin"
        }
        register("androidApplicationBaselineProfile") {
            id = "androidlab.android.application.baselineprofile"
            implementationClass =
                "dev.shtanko.androidlab.convention.AndroidApplicationBaselineProfileConventionPlugin"
        }
        register("androidBenchmark") {
            id = "androidlab.android.benchmark"
            implementationClass = "dev.shtanko.androidlab.convention.AndroidBenchmarkConventionPlugin"
        }
        register("androidComposeScreenshot") {
            id = "androidlab.android.compose.screenshot"
            implementationClass =
                "dev.shtanko.androidlab.convention.AndroidComposeScreenshotConventionPlugin"
        }
        register("androidJUnit5") {
            id = "androidlab.android.junit5"
            implementationClass = "dev.shtanko.androidlab.convention.AndroidJUnit5ConventionPlugin"
        }
        register("androidRoborazzi") {
            id = "androidlab.android.roborazzi"
            implementationClass =
                "dev.shtanko.androidlab.convention.AndroidRoborazziConventionPlugin"
        }
        register("androidTest") {
            id = "androidlab.android.test"
            implementationClass = "dev.shtanko.androidlab.convention.AndroidTestConventionPlugin"
        }
        register("androidLibraryJacoco") {
            id = "androidlab.android.library.jacoco"
            implementationClass =
                "dev.shtanko.androidlab.convention.AndroidLibraryJacocoConventionPlugin"
        }
        register("jvmLibrary") {
            id = "androidlab.jvm.library"
            implementationClass = "dev.shtanko.androidlab.convention.JvmLibraryConventionPlugin"
        }
        register("room") {
            id = "androidlab.android.room"
            implementationClass = "dev.shtanko.androidlab.convention.AndroidRoomConventionPlugin"
        }
    }
}
