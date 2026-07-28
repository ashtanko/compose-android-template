/*
 * Designed and developed by 2026 ashtanko (Oleksii Shtanko)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
import java.util.Properties

private val storePasswordKey = "storePassword"
private val keyPasswordKey = "keyPassword"
private val keyAliasKey = "keyAlias"
private val storeFileKey = "storeFile"
private val releaseSigningKeys = listOf(
    storePasswordKey,
    keyPasswordKey,
    keyAliasKey,
    storeFileKey,
)
private val releaseSigningEnvironmentVariables = mapOf(
    storePasswordKey to "SIGNING_STORE_PASSWORD",
    keyPasswordKey to "SIGNING_KEY_PASSWORD",
    keyAliasKey to "SIGNING_KEY_ALIAS",
    storeFileKey to "SIGNING_KEYSTORE_PATH",
)

data class ReleaseSigningCredentials(
    val storeFile: File,
    val storePassword: String,
    val keyAlias: String,
    val keyPassword: String,
)

val releaseSigningPropertiesFile = rootProject.file("key.properties")
val releaseSigningProperties = Properties().apply {
    if (releaseSigningPropertiesFile.isFile) {
        releaseSigningPropertiesFile.inputStream().use(::load)
    }
}
val releaseSigningEnvironmentValues = releaseSigningEnvironmentVariables.mapValues { (_, name) ->
    providers.environmentVariable(name).orNull
}
val hasAnyReleaseSigningEnvironmentValue =
    releaseSigningEnvironmentValues.values.any { !it.isNullOrBlank() }
val hasCompleteReleaseSigningEnvironment =
    releaseSigningEnvironmentValues.values.all { !it.isNullOrBlank() }
val hasCompleteLocalReleaseSigningProperties =
    releaseSigningKeys.all { !releaseSigningProperties.getProperty(it).isNullOrBlank() }

val releaseSigningCredentials = when {
    hasCompleteReleaseSigningEnvironment -> ReleaseSigningCredentials(
        storeFile = rootProject.file(releaseSigningEnvironmentValues.getValue(storeFileKey)!!),
        storePassword = releaseSigningEnvironmentValues.getValue(storePasswordKey)!!,
        keyAlias = releaseSigningEnvironmentValues.getValue(keyAliasKey)!!,
        keyPassword = releaseSigningEnvironmentValues.getValue(keyPasswordKey)!!,
    )

    !hasAnyReleaseSigningEnvironmentValue && hasCompleteLocalReleaseSigningProperties ->
        ReleaseSigningCredentials(
            storeFile = rootProject.file(releaseSigningProperties.getProperty(storeFileKey)),
            storePassword = releaseSigningProperties.getProperty(storePasswordKey),
            keyAlias = releaseSigningProperties.getProperty(keyAliasKey),
            keyPassword = releaseSigningProperties.getProperty(keyPasswordKey),
        )

    else -> null
}

val releaseSigningConfigurationError = when {
    hasAnyReleaseSigningEnvironmentValue && !hasCompleteReleaseSigningEnvironment -> {
        val missingVariables = releaseSigningEnvironmentVariables
            .filterKeys { releaseSigningEnvironmentValues[it].isNullOrBlank() }
            .values
            .joinToString()
        "Release signing environment is incomplete. Missing: $missingVariables."
    }

    releaseSigningPropertiesFile.isFile && !hasCompleteLocalReleaseSigningProperties -> {
        val missingProperties = releaseSigningKeys
            .filter { releaseSigningProperties.getProperty(it).isNullOrBlank() }
            .joinToString()
        "Release signing file ${releaseSigningPropertiesFile.path} is incomplete. " +
            "Missing: $missingProperties."
    }

    releaseSigningCredentials == null ->
        "Release signing is not configured. Copy key.properties.example to key.properties " +
            "for local builds, or configure the production secrets described in RELEASING.md."

    !releaseSigningCredentials.storeFile.isFile ->
        "Release keystore does not exist: ${releaseSigningCredentials.storeFile.path}"

    else -> null
}

plugins {
    alias(libs.plugins.androidlab.android.application.compose)
    alias(libs.plugins.androidlab.android.application.baselineprofile)
    alias(libs.plugins.androidlab.android.application.jacoco)
    alias(libs.plugins.androidlab.android.compose.screenshot)
    alias(libs.plugins.androidlab.android.junit5)
    alias(libs.plugins.androidlab.android.roborazzi)
    alias(libs.plugins.androidlab.android.room)
    alias(libs.plugins.androidlab.hilt)
    alias(libs.plugins.kotlin.parcelize)
    alias(libs.plugins.serialization)
    alias(libs.plugins.kover)
    alias(libs.plugins.sonarqube)
    jacoco
}

android {
    namespace = "dev.shtanko.template"

    defaultConfig {
        applicationId = "dev.shtanko.template"
        versionCode = 1
        versionName = "1.0"
    }

    signingConfigs {
        register("release") {
            releaseSigningCredentials?.let { credentials ->
                storeFile = credentials.storeFile
                storePassword = credentials.storePassword
                keyAlias = credentials.keyAlias
                keyPassword = credentials.keyPassword
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
            signingConfig = signingConfigs.getByName("release")
        }

        create("benchmark") {
            initWith(buildTypes.getByName("release"))
            matchingFallbacks += listOf("release")
            signingConfig = signingConfigs.getByName("debug")
            isDebuggable = false
            proguardFiles("benchmark-rules.pro")
        }
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
            merges += "META-INF/LICENSE.md"
            merges += "META-INF/LICENSE-notice.md"
        }
    }
}

tasks {
    val validateReleaseSigningConfiguration = register("validateReleaseSigningConfiguration") {
        group = "verification"
        description = "Validate credentials required to sign a release artifact"

        doLast {
            releaseSigningConfigurationError?.let { throw GradleException(it) }
        }
    }

    matching { it.name == "validateSigningRelease" }.configureEach {
        dependsOn(validateReleaseSigningConfiguration)
    }

    getByName("check") {
        dependsOn("detekt")
    }

    getByName("sonar") {
        dependsOn("check")
    }

    withType<Test> {
        useJUnitPlatform()
        maxHeapSize = "2g"
        maxParallelForks = Runtime.getRuntime().availableProcessors()
        jvmArgs = jvmArgs.orEmpty() + "-XX:+UseParallelGC"
        jvmArgs(
            "--add-opens",
            "java.base/java.util=ALL-UNNAMED",
            "--add-opens",
            "java.base/java.lang=ALL-UNNAMED",
            "--add-opens",
            "java.base/java.time=ALL-UNNAMED",
            "-Xshare:off",
        )
    }

    register<JacocoReport>("testCoverage") {
        dependsOn("test")
        group = "Reporting"
        description = "Generate Jacoco coverage reports"

        val excludedFiles = mutableSetOf("**/*Test*.*")
        val projectBuildDirectory = project.layout.buildDirectory.get().asFile.absoluteFile
        val sourceDirs = fileTree(
            "$projectBuildDirectory/classes/kotlin/",
        ) {
            exclude(excludedFiles)
        }
        val coverageDirs = listOf(
            "src/main/java",
            "src/main/kotlin",
        )
        classDirectories.setFrom(files(sourceDirs))
        additionalClassDirs.setFrom(files(coverageDirs))
        executionData.setFrom(
            files("$projectBuildDirectory/jacoco/test.exec"),
        )

        reports {
            listOf(xml, html).map { it.required }.forEach { it.set(true) }
            xml.outputLocation.set(file("$projectBuildDirectory/reports/jacoco/report.xml"))
        }
    }
}

dependencies {
    implementation(project(":core:designsystem"))
    implementation(project(":feature:home"))
    implementation(project(":feature:posts:data"))
    implementation(project(":feature:posts:presentation"))

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    implementation(libs.androidx.runtime.tracing)
    implementation(libs.androidx.tracing.ktx)
    implementation(libs.androidx.navigation3.runtime)
    implementation(libs.androidx.navigation3.ui)
    implementation(libs.androidx.material3.navigation3)

    implementation(libs.androidx.compose.material3.adaptive)
    implementation(libs.androidx.compose.material3.adaptive.layout)
    implementation(libs.androidx.compose.material3.adaptive.navigation)
    implementation(libs.androidx.compose.material3.adaptive.navigationSuite)
    implementation(libs.androidx.compose.materialWindow)
    implementation(libs.androidx.compose.icons.extended)

    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.ui.test.junit4)
    testImplementation(libs.androidx.ui.test.junit4)

    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)

    implementation(libs.androidx.ui.text.google.fonts)

    androidTestImplementation(libs.arch.core.test)

    baselineProfile(project(":benchmarks"))

    implementation(libs.paging.runtime)
    implementation(libs.paging.compose)

    implementation(libs.generativeai)

    implementation(libs.kotlinx.collections.immutable)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.kotlinx.coroutines.core)
    implementation(libs.kotlinx.serialization)

    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.kotlinx.coroutines.debug)

    implementation(libs.coil.kt)
    implementation(libs.coil.kt.compose)
    implementation(libs.coil.kt.svg)

    kspTest(libs.hilt.compiler)
    kspAndroidTest(libs.hilt.compiler)
    testImplementation(libs.hilt.android.testing)

    implementation(libs.accompanist.adaptive)
    implementation(libs.accompanist.permissions)

    implementation(libs.androidx.window)
    implementation(libs.androidx.window.core)

    implementation(libs.room.paging)

    implementation(libs.jacoco.core)

    implementation(libs.square.okhttp)
    implementation(libs.square.okhttp.logging)
    implementation(libs.square.okhttp.mockwebserver)
    implementation(libs.square.retrofit.core)
    implementation(libs.skydoves.sandwich.retrofit)
    implementation(libs.square.retrofit.kotlin.serialization)

    testImplementation(libs.square.turbine)
    testImplementation(libs.mockito)
    testImplementation(libs.mockito.kotlin2)
    testImplementation(libs.mockk.kotlin)
    androidTestImplementation(libs.mockk.android)

    testImplementation(libs.robolectric.robolectric)
    testImplementation(libs.androidx.activity.compose)

    androidTestImplementation(libs.androidx.espresso.core)
}

dependencyGuard {
    configuration("releaseRuntimeClasspath")
}
