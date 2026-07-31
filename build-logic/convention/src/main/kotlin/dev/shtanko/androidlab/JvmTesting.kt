package dev.shtanko.androidlab

import org.gradle.api.Project
import org.gradle.api.tasks.SourceSetContainer
import org.gradle.api.tasks.testing.Test
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.getByName
import org.gradle.kotlin.dsl.getByType
import org.gradle.kotlin.dsl.named
import org.gradle.kotlin.dsl.register
import org.gradle.kotlin.dsl.withType
import org.gradle.testing.jacoco.plugins.JacocoPluginExtension
import org.gradle.testing.jacoco.plugins.JacocoTaskExtension
import org.gradle.testing.jacoco.tasks.JacocoCoverageVerification
import org.gradle.testing.jacoco.tasks.JacocoReport
import org.jetbrains.kotlin.gradle.dsl.KotlinJvmProjectExtension
import java.math.BigDecimal

private val jvmCoverageExclusions = listOf(
    "**/*Test*.*",
    "**/di/**",
    "**/hilt_aggregated_deps/**",
    "**/*_Factory*.*",
    "**/*_MembersInjector*.*",
    "**/Dagger*.*",
    "**/Hilt_*.*",
)

/**
 * Adds a separate JVM integration-test source set and enforces business-logic line coverage.
 */
@Suppress("LongMethod")
internal fun Project.configureJvmTesting() {
    pluginManager.apply("jacoco")

    extensions.configure<JacocoPluginExtension> {
        toolVersion = libs.findVersion("jacoco").get().requiredVersion
    }

    val sourceSets = extensions.getByType<SourceSetContainer>()
    val mainSourceSet = sourceSets.getByName("main")
    val integrationTestSourceSet = sourceSets.create("integrationTest")
    integrationTestSourceSet.compileClasspath += mainSourceSet.output
    integrationTestSourceSet.runtimeClasspath += mainSourceSet.output

    extensions.configure<KotlinJvmProjectExtension> {
        target.compilations.named("integrationTest") {
            associateWith(target.compilations.getByName("main"))
        }
    }

    configurations.named(integrationTestSourceSet.implementationConfigurationName) {
        extendsFrom(configurations.getByName("testImplementation"))
    }
    configurations.named(integrationTestSourceSet.runtimeOnlyConfigurationName) {
        extendsFrom(configurations.getByName("testRuntimeOnly"))
    }

    val unitTest = tasks.named<Test>("test")
    val integrationTest = tasks.register<Test>("integrationTest") {
        group = "verification"
        description = "Runs deterministic integration tests from src/integrationTest."
        testClassesDirs = integrationTestSourceSet.output.classesDirs
        classpath = integrationTestSourceSet.runtimeClasspath
        shouldRunAfter(unitTest)
        useJUnitPlatform()
    }

    tasks.withType<Test>().configureEach {
        extensions.configure<JacocoTaskExtension> {
            isIncludeNoLocationClasses = true
            excludes = listOf("jdk.internal.*")
        }
    }

    val coveredClasses = sourceSets.named("main").map { main ->
        main.output.asFileTree.matching {
            exclude(jvmCoverageExclusions)
        }
    }
    val coveredSources = sourceSets.named("main").map { it.allSource.srcDirs }
    val unitExecutionData = layout.buildDirectory.file("jacoco/test.exec")
    val integrationExecutionData = layout.buildDirectory.file("jacoco/integrationTest.exec")

    tasks.named<JacocoReport>("jacocoTestReport") {
        dependsOn(unitTest, integrationTest)
        executionData.setFrom(unitExecutionData, integrationExecutionData)
        classDirectories.setFrom(coveredClasses)
        sourceDirectories.setFrom(coveredSources)
        reports {
            html.required.set(true)
            xml.required.set(true)
        }
    }

    tasks.named<JacocoCoverageVerification>("jacocoTestCoverageVerification") {
        dependsOn(unitTest, integrationTest)
        executionData.setFrom(unitExecutionData, integrationExecutionData)
        classDirectories.setFrom(coveredClasses)
        sourceDirectories.setFrom(coveredSources)
        violationRules {
            rule {
                limit {
                    counter = "LINE"
                    value = "COVEREDRATIO"
                    minimum = BigDecimal("0.80")
                }
            }
        }
    }

    tasks.named("check") {
        dependsOn(integrationTest, "jacocoTestCoverageVerification")
    }
}
