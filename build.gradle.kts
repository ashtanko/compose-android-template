// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.android.library) apply false
    alias(libs.plugins.android.test) apply false
    alias(libs.plugins.kotlin.jvm) apply false
    alias(libs.plugins.kotlin.compose) apply false
    alias(libs.plugins.compose.guard) apply false
    alias(libs.plugins.detekt) apply false
    alias(libs.plugins.ksp) apply false
    alias(libs.plugins.room) apply false
    alias(libs.plugins.hilt) apply false
    alias(libs.plugins.android.junit5) apply false
    alias(libs.plugins.screenshot) apply false
    alias(libs.plugins.baselineprofile) apply false
    alias(libs.plugins.dependencyGuard) apply false
    alias(libs.plugins.spotless) apply false
    alias(libs.plugins.sonarqube) apply false
    alias(libs.plugins.kotlin.parcelize) apply false
    alias(libs.plugins.serialization) apply false
    alias(libs.plugins.google.android.libraries.mapsplatform.secrets.gradle.plugin) apply false
}

tasks.register("spotlessCheck") {
    group = "verification"
    description = "Checks formatting in the included build logic."
    dependsOn(gradle.includedBuild("build-logic").task(":convention:spotlessCheck"))
}

tasks.register("spotlessApply") {
    group = "formatting"
    description = "Applies formatting in the included build logic."
    dependsOn(gradle.includedBuild("build-logic").task(":convention:spotlessApply"))
}

tasks.register("detekt") {
    group = "verification"
    description = "Runs Detekt in the included build logic."
    dependsOn(gradle.includedBuild("build-logic").task(":convention:detekt"))
}

tasks.register("detektCompose") {
    group = "verification"
    description = "Runs Compose-specific Detekt rules in every module."
}

tasks.register("detektAutoCorrect") {
    group = "formatting"
    description = "Runs Detekt auto-correction in every module."
}

val integrationTest = tasks.register("integrationTest") {
    group = "verification"
    description = "Runs integration tests in every Kotlin/JVM module."
}

val coverageReport = tasks.register("coverageReport") {
    group = "reporting"
    description = "Generates JVM and Android reports from available unit and device coverage."
}

val coverageVerification = tasks.register("coverageVerification") {
    group = "verification"
    description = "Enforces JVM business-logic coverage thresholds."
}

val ciManagedDeviceTest = tasks.register("ciManagedDeviceTest") {
    group = "verification"
    description = "Runs every debug instrumentation and end-to-end test on the CI device group."
}

val allManagedDeviceTest = tasks.register("allManagedDeviceTest") {
    group = "verification"
    description = "Runs every debug instrumentation and end-to-end test on all managed devices."
}

subprojects {
    pluginManager.withPlugin("org.jetbrains.kotlin.jvm") {
        integrationTest.configure {
            dependsOn(tasks.named("integrationTest"))
        }
        coverageReport.configure {
            dependsOn(tasks.named("jacocoTestReport"))
        }
        coverageVerification.configure {
            dependsOn(tasks.named("jacocoTestCoverageVerification"))
        }
    }

    listOf(
        "androidlab.android.application.jacoco",
        "androidlab.android.library.jacoco",
    ).forEach { pluginId ->
        pluginManager.withPlugin(pluginId) {
            coverageReport.configure {
                dependsOn(tasks.named("createDebugCombinedCoverageReport"))
            }
        }
    }

    listOf(
        "com.android.application",
        "com.android.library",
        "com.android.test",
    ).forEach { pluginId ->
        pluginManager.withPlugin(pluginId) {
            ciManagedDeviceTest.configure {
                dependsOn(tasks.matching { it.name == "ciGroupDebugAndroidTest" })
            }
            allManagedDeviceTest.configure {
                dependsOn(tasks.matching { it.name == "allDevicesDebugAndroidTest" })
            }
        }
    }
}

// Bootstraps a new project from this template by delegating to
// scripts/rename-template.sh. Same flags, exposed as Gradle properties:
//
//   ./gradlew renameProject \
//     -Ppackage=com.example.myapp \
//     -Pname="My Awesome App" \
//     [-PpluginAlias=myapp] \
//     [-Pauthor="Jane Doe"] \
//     [-PdryRun=true] \
//     [-Pverbose=true] \
//     [-Pforce=true]
tasks.register<Exec>("renameProject") {
    group = "template"
    description = "Rename packages, applicationId, plugin aliases, folders, and (optionally) author headers."

    val newPackage  = providers.gradleProperty("package")
    val newName     = providers.gradleProperty("name")
    val pluginAlias = providers.gradleProperty("pluginAlias")
    val author      = providers.gradleProperty("author")
    val dryRun      = providers.gradleProperty("dryRun").map { it.toBoolean() }.orElse(false)
    val verbose     = providers.gradleProperty("verbose").map { it.toBoolean() }.orElse(false)
    val force       = providers.gradleProperty("force").map { it.toBoolean() }.orElse(false)
    val script      = layout.projectDirectory.file("scripts/rename-template.sh").asFile

    doFirst {
        check(newPackage.isPresent) { "missing -Ppackage=<com.example.app>" }
        check(newName.isPresent)    { "missing -Pname=<\"My App\">" }
        val cmd = mutableListOf("bash", script.absolutePath,
            "--package", newPackage.get(),
            "--name",    newName.get())
        pluginAlias.orNull?.let { cmd += listOf("--plugin-alias", it) }
        author.orNull?.let      { cmd += listOf("--author", it) }
        if (dryRun.get()) cmd += "--dry-run"
        if (verbose.get()) cmd += "--verbose"
        if (force.get())  cmd += "--force"
        commandLine(cmd)
    }
    // Placeholder commandLine; replaced in doFirst above. Gradle requires it
    // be non-empty at configuration time.
    commandLine("bash", "-c", "true")
}
