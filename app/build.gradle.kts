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
import com.android.build.gradle.internal.cxx.configure.gradleLocalProperties
import java.util.Properties

val isCiBuild = providers.environmentVariable("CI").map(String::toBoolean).getOrElse(false)

private val storePasswordKey = "storePassword"
private val keyPasswordKey = "keyPassword"
private val keyAliasKey = "keyAlias"
private val storeFileKey = "storeFile"
private val releaseSigningPropertyKeys = listOf(
    storePasswordKey,
    keyPasswordKey,
    keyAliasKey,
    storeFileKey,
)

val releaseSigningPropertiesFile = rootProject.file("key.properties")
val releaseSigningProperties = Properties().apply {
    if (releaseSigningPropertiesFile.isFile) {
        releaseSigningPropertiesFile.inputStream().use(::load)
    }
}
val releaseSigningStoreFile = releaseSigningProperties
    .getProperty(storeFileKey)
    ?.let(rootProject::file)
val hasValidLocalReleaseSigningConfig =
    releaseSigningPropertyKeys.all(releaseSigningProperties::containsKey) &&
        releaseSigningStoreFile?.isFile == true

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

        // Client-side configuration only: BuildConfig values are recoverable from APKs.
        val apiKey = gradleLocalProperties(rootDir, providers).getProperty("TMDB_API_KEY") ?: ""
        buildConfigField("String", "TMDB_API_KEY", "\"$apiKey\"")
    }

    signingConfigs {
        register("release") {
            enableV1Signing = true
            enableV2Signing = true

            if (isCiBuild) {
                storeFile = file("keystore.jks")
                storePassword = providers.environmentVariable("SIGNING_STORE_PASSWORD").orNull
                keyAlias = providers.environmentVariable("SIGNING_KEY_ALIAS").orNull
                keyPassword = providers.environmentVariable("SIGNING_KEY_PASSWORD").orNull
            } else if (hasValidLocalReleaseSigningConfig) {
                storeFile = releaseSigningStoreFile
                keyAlias = releaseSigningProperties.getProperty(keyAliasKey)
                keyPassword = releaseSigningProperties.getProperty(keyPasswordKey)
                storePassword = releaseSigningProperties.getProperty(storePasswordKey)
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
            isDebuggable = false
            proguardFiles("benchmark-rules.pro")
        }
    }

    buildFeatures {
        buildConfig = true
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

    libs.apply {
        androidx.apply {
            implementation(core.ktx)
            implementation(lifecycle.runtime.ktx)
            implementation(activity.compose)
            implementation(platform(compose.bom))
            implementation(ui)
            implementation(ui.graphics)
            implementation(ui.tooling.preview)
            implementation(material3)
            implementation(runtime.tracing)
            implementation(tracing.ktx)
            implementation(navigation3.runtime)
            implementation(navigation3.ui)
            implementation(material3.navigation3)

            compose.apply {
                implementation(material3.adaptive)
                implementation(material3.adaptive.layout)
                implementation(material3.adaptive.navigation)
                implementation(material3.adaptive.navigationSuite)
                implementation(materialWindow)
                implementation(icons.extended)
            }

            androidTestImplementation(junit)
            androidTestImplementation(platform(compose.bom))
            androidTestImplementation(ui.test.junit4)
            testImplementation(ui.test.junit4)

            debugImplementation(ui.tooling)
            debugImplementation(ui.test.manifest)

            ui.apply {
                implementation(text.google.fonts)
                debugImplementation(test.manifest)
                androidTestImplementation(test.junit4)
                androidTestImplementation(test)
            }

            androidTestImplementation(arch.core.test)
        }

        baselineProfile(project(":benchmarks"))

        implementation(paging.runtime)
        implementation(paging.compose)

        implementation(generativeai)

        kotlinx.apply {
            implementation(collections.immutable)
            implementation(coroutines.android)
            implementation(coroutines.core)
            implementation(serialization)

            testImplementation(coroutines.test)
            testImplementation(coroutines.debug)
        }

        coil.apply {
            implementation(kt)
            implementation(kt.compose)
            implementation(kt.svg)
        }

        hilt.apply {
            kspTest(compiler)
            kspAndroidTest(compiler)
            testImplementation(android.testing)
        }

        implementation(accompanist.adaptive)
        implementation(accompanist.permissions)

        implementation(libs.androidx.window)
        implementation(libs.androidx.window.core)

        implementation(room.paging)

        implementation(jacoco.core)

        implementation(square.okhttp)
        implementation(square.okhttp.logging)
        implementation(square.okhttp.mockwebserver)
        implementation(square.retrofit.core)
        implementation(skydoves.sandwich.retrofit)
        implementation(square.retrofit.kotlin.serialization)

        testImplementation(square.turbine)
        testImplementation(mockito)
        testImplementation(mockito.kotlin2)
        testImplementation(mockk.kotlin)
        androidTestImplementation(mockk.android)

        testImplementation(robolectric.robolectric)
        testImplementation(androidx.activity.compose)

        androidTestImplementation(libs.androidx.junit)
        androidTestImplementation(libs.androidx.espresso.core)
        androidTestImplementation(platform(libs.androidx.compose.bom))
        androidTestImplementation(libs.androidx.ui.test.junit4)
        debugImplementation(libs.androidx.ui.tooling)
        debugImplementation(libs.androidx.ui.test.manifest)
    }
}

dependencyGuard {
    configuration("releaseRuntimeClasspath")
}
