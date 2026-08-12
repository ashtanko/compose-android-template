package dev.shtanko.androidlab

import com.android.build.api.artifact.ScopedArtifact
import com.android.build.api.dsl.CommonExtension
import com.android.build.api.variant.AndroidComponentsExtension
import com.android.build.api.variant.ScopedArtifacts
import com.android.build.api.variant.SourceDirectories
import org.gradle.api.Project
import org.gradle.api.file.Directory
import org.gradle.api.file.RegularFile
import org.gradle.api.provider.ListProperty
import org.gradle.api.provider.Provider
import org.gradle.api.tasks.testing.Test
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.register
import org.gradle.kotlin.dsl.withType
import org.gradle.testing.jacoco.plugins.JacocoPluginExtension
import org.gradle.testing.jacoco.plugins.JacocoTaskExtension
import org.gradle.testing.jacoco.tasks.JacocoReport

private val coverageExclusions = listOf(
    // Android
    "**/R.class",
    "**/R\$*.class",
    "**/BuildConfig.*",
    "**/Manifest*.*",
    "**/*_Hilt*.class",
    "**/Hilt_*.class",
)

/**
 * Creates a new task that generates a combined coverage report with data from local and
 * instrumented tests.
 *
 * `create{variant}CombinedCoverageReport`
 *
 * Note that coverage data must exist before running the task. This allows us to run device
 * tests on CI using a different Github Action or an external device farm.
 */
internal fun Project.configureJacoco(
    commonExtension: CommonExtension,
    androidComponentsExtension: AndroidComponentsExtension<*, *, *>,
) {
    enableDebugCoverage(commonExtension)
    configureJacocoToolVersion()

    androidComponentsExtension.onVariants(
        androidComponentsExtension.selector().withBuildType("debug"),
    ) { variant ->
        val myObjFactory = project.objects
        val allJars: ListProperty<RegularFile> = myObjFactory.listProperty(RegularFile::class.java)
        val allDirectories: ListProperty<Directory> =
            myObjFactory.listProperty(Directory::class.java)
        val reportTask =
            tasks.register(
                "create${variant.name.replaceFirstChar(Char::uppercaseChar)}CombinedCoverageReport",
                JacocoReport::class,
            ) {
                dependsOn("test${variant.name.replaceFirstChar(Char::uppercaseChar)}UnitTest")
                classDirectories.setFrom(
                    allJars,
                    allDirectories.map { dirs ->
                        dirs.map { dir ->
                            myObjFactory.fileTree().setDir(dir).exclude(coverageExclusions)
                        }
                    },
                )
                reports {
                    xml.required.set(true)
                    html.required.set(true)
                }

                fun SourceDirectories.Flat?.toFilePaths(): Provider<List<String>> = this
                    ?.all
                    ?.map { directories -> directories.map { it.asFile.path } }
                    ?: provider { emptyList() }
                sourceDirectories.setFrom(
                    files(
                        variant.sources.java.toFilePaths(),
                        variant.sources.kotlin.toFilePaths(),
                    ),
                )

                executionData.setFrom(coverageExecutionData(variant.name))
            }

        variant.artifacts.forScope(ScopedArtifacts.Scope.PROJECT)
            .use(reportTask)
            .toGet(
                ScopedArtifact.CLASSES,
                { _ -> allJars },
                { _ -> allDirectories },
            )
    }

    configureUnitTestCoverage()
}

private fun Project.coverageExecutionData(variantName: String) = files(
    fileTree(
        layout.buildDirectory.dir("outputs/unit_test_code_coverage/${variantName}UnitTest"),
    ).matching { include("**/*.exec") },
    fileTree(
        layout.buildDirectory.dir("outputs/code_coverage/${variantName}AndroidTest"),
    ).matching { include("**/*.ec") },
    fileTree(
        layout.buildDirectory.dir("outputs/managed_device_code_coverage/$variantName"),
    ).matching { include("**/*.ec") },
)

private fun Project.configureJacocoToolVersion() {
    configure<JacocoPluginExtension> {
        toolVersion = libs.findVersion("jacoco").get().toString()
    }
}

private fun enableDebugCoverage(commonExtension: CommonExtension) {
    // Enabling coverage on release build types would also make them debuggable.
    commonExtension.buildTypes.named("debug") {
        enableAndroidTestCoverage = true
        enableUnitTestCoverage = true
    }
}

private fun Project.configureUnitTestCoverage() {
    tasks.withType<Test>().configureEach {
        configure<JacocoTaskExtension> {
            // Required for JaCoCo + Robolectric
            // https://github.com/robolectric/robolectric/issues/2230
            isIncludeNoLocationClasses = true

            // Required for JDK 11 with the above
            // https://github.com/gradle/gradle/issues/5184#issuecomment-391982009
            excludes = listOf("jdk.internal.*")
        }
    }
}
