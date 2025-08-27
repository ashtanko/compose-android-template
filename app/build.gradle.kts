import com.android.build.gradle.internal.cxx.configure.gradleLocalProperties
import io.gitlab.arturbosch.detekt.extensions.DetektExtension
import java.util.Properties
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.plugin.KotlinSourceSetContainer

val isGithubActions = System.getenv("GITHUB_ACTIONS")?.toBoolean() == true
val isCI = providers.environmentVariable("CI").isPresent

plugins {
    alias(libs.plugins.androidlab.android.application)
    alias(libs.plugins.androidlab.android.application.compose)
    alias(libs.plugins.androidlab.android.application.jacoco)
    alias(libs.plugins.androidlab.hilt)
    alias(libs.plugins.compose.guard)
    alias(libs.plugins.kotlin.parcelize)
    alias(libs.plugins.serialization)
    alias(libs.plugins.kover)
    alias(libs.plugins.ksp)
    alias(libs.plugins.sonarqube)
    alias(libs.plugins.screenshot)
    alias(libs.plugins.baselineprofile)
    alias(libs.plugins.roborazzi)
    jacoco
}

android {
    namespace = "dev.shtanko.template"
    compileSdk = libs.versions.compileSdk.get().toInt()

    defaultConfig {
        applicationId = "dev.shtanko.template"
        minSdk = libs.versions.minSdk.get().toInt()
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        register("release") {
            enableV1Signing = true
            enableV2Signing = true

            if (isCI) {
                storeFile = file("keystore.jks")
                storePassword = System.getenv("SIGNING_STORE_PASSWORD")
                keyAlias = System.getenv("SIGNING_KEY_ALIAS")
                keyPassword = System.getenv("SIGNING_KEY_PASSWORD")
            } else if (isGithubActions) {
                storeFile = file("keystore.jks")
                storePassword = System.getenv("SIGNING_STORE_PASSWORD")
                keyAlias = System.getenv("SIGNING_KEY_ALIAS")
                keyPassword = System.getenv("SIGNING_KEY_PASSWORD")
            } else {
                storeFile = getReleaseValue("storeFile")?.let { file(it) }
                keyAlias = getReleaseValue("keyAlias")
                keyPassword = getReleaseValue("keyPassword")
                storePassword = getReleaseValue("storePassword")
            }
        }
    }

    buildTypes {
        debug {
            val apiKey: String =
                gradleLocalProperties(rootDir, providers).getProperty("TMDB_API_KEY") ?: ""
            buildConfigField("String", "TMDB_API_KEY", "\"$apiKey\"")
        }
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
            signingConfig = signingConfigs.getByName("release")

            val apiKey: String =
                gradleLocalProperties(rootDir, providers).getProperty("TMDB_API_KEY") ?: ""
            buildConfigField("String", "TMDB_API_KEY", "\"$apiKey\"")
        }

        create("benchmark") {
            initWith(buildTypes.getByName("release"))
            matchingFallbacks += listOf("release")
            isDebuggable = false
            proguardFiles("benchmark-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility(libs.versions.jvmTarget.get())
        targetCompatibility(libs.versions.jvmTarget.get())
    }
    kotlinOptions {
        jvmTarget = libs.versions.jvmTarget.get()
    }
    buildFeatures {
        buildConfig = true
        compose = true
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
            merges += "META-INF/LICENSE.md"
            merges += "META-INF/LICENSE-notice.md"
        }
    }
    testOptions {
        // Required for Robolectric
        unitTests.isIncludeAndroidResources = true
        unitTests.isReturnDefaultValues = true

        unitTests.all {
            it.useJUnitPlatform()
            it.jvmArgs(
                "--add-opens",
                "java.base/java.util=ALL-UNNAMED",
                "--add-opens",
                "java.base/java.lang=ALL-UNNAMED",
                "--add-opens",
                "java.base/java.time=ALL-UNNAMED",
                "-Xshare:off",
            )
        }
        screenshotTests {
            imageDifferenceThreshold = 0.0001f // 0.01%
        }
    }
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.15"
    }
    experimentalProperties["android.experimental.enableScreenshotTest"] = true

    ksp {
        arg("room.schemaLocation", "$projectDir/schemas")
    }
}

fun getReleaseValue(key: String): String? {
    return getValueFromConfig(key, false, configFile = "key.properties")
}

fun getValueFromConfig(
    key: String,
    quot: Boolean,
    configFile: String = "local.properties"
): String? {
    val properties = Properties()
    properties.load(project.rootProject.file(configFile).inputStream())
    var value = if (properties.containsKey(key)) {
        properties[key].toString()
    } else {
        ""
    }
    if (quot) {
        value = "\"" + value + "\""
    }
    return value.takeIf { it.isNotEmpty() }
}

project.gradle.startParameter.excludedTaskNames.apply {
    val excludedTasks = listOf(
        "testDebugScreenshotTest",
        "testReleaseScreenshotTest",
        "testBenchmarkReleaseScreenshotTest",
        "testBenchmarkScreenshotTest",
        "testNonMinifiedReleaseScreenshotTest",
        "testBenchmarkUnitTest",
        "testReleaseUnitTest",
        "finalizeTestRoborazziRelease",
    )
    if (isCI || isGithubActions) {
        excludedTasks.forEach(::add)
    }
}

tasks {
    getByName("check") {
        // Add detekt with type resolution to check
        dependsOn("detekt")
    }

    getByName("sonar") {
        dependsOn("check")
    }

    withType<io.gitlab.arturbosch.detekt.Detekt>().configureEach {
        jvmTarget = libs.versions.jvmTarget.get()
    }

    withType<io.gitlab.arturbosch.detekt.DetektCreateBaselineTask>().configureEach {
        jvmTarget = libs.versions.jvmTarget.get()
    }

    withType<Test> {
        useJUnitPlatform()
        maxHeapSize = "2g"
        maxParallelForks = Runtime.getRuntime().availableProcessors()
        jvmArgs = jvmArgs.orEmpty() + "-XX:+UseParallelGC"
        android.sourceSets["main"].res.srcDirs("src/test/res")
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
            files("$projectBuildDirectory/jacoco/test.exec")
        )

        reports {
            listOf(xml, html).map { it.required }.forEach { it.set(true) }
            xml.outputLocation.set(file("$projectBuildDirectory/reports/jacoco/report.xml"))
        }
    }
}

composeGuardCheck {
    errorOnNewDynamicProperties = false
    errorOnNewUnstableClasses = false
    reportAllOnMissingBaseline = true
}

composeGuard {
    configureKotlinTasks = false
}

kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.fromTarget(libs.versions.jvmTarget.get()))
    }
}

//detekt {
//    config.setFrom("${project.rootDir}/config/detekt/detekt.yml")
//
//    val projectDir = projectDir
//    val kotlinExtension = project.extensions.getByType(KotlinSourceSetContainer::class.java)
//
//    source.setFrom(
//        provider {
//            kotlinExtension.sourceSets
//                .flatMap { sourceSet ->
//                    sourceSet.kotlin.srcDirs.filter {
//                        it.relativeTo(projectDir).startsWith("src")
//                    }
//                }
//        },
//    )
//}

//configure<DetektExtension> {
//    config.from("${project.rootDir}/config/detekt/detekt-compose.yml")
//}

dependencies {
    // implementation(projects.core.designsystem)

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
            implementation(hilt.navigation.compose)
            implementation(runtime.tracing)
            implementation(tracing.ktx)

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
            screenshotTestImplementation(compose.ui.tooling)
        }

        implementation(profileinstaller)

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

//        detekt.apply {
//            detektPlugins(rules)
//            detektPlugins(formatting)
//        }

        coil.apply {
            implementation(kt)
            implementation(kt.compose)
            implementation(kt.svg)
        }

        google.hilt.apply {
            implementation(android)
            ksp(compiler)
            kspTest(compiler)
            kspAndroidTest(compiler)
            testImplementation(android.testing)
        }

        implementation(profileinstaller)

        implementation(accompanist.adaptive)
        implementation(accompanist.permissions)

        implementation(libs.androidx.window)
        implementation(libs.androidx.window.core)

        implementation(room.runtime)
        implementation(room.ktx)
        implementation(room.paging)
        ksp(room.compiler)

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
        testImplementation(roborazzi)
        testImplementation(roborazzi.accessibility.check)
        testImplementation(androidx.activity.compose)

        junit5.apply {
            testImplementation(api)
            testImplementation(params)

            androidTestImplementation(api)
            androidTestImplementation(params)

            testRuntimeOnly(jupiterEngine)
            testRuntimeOnly(vintageEngine)
        }
    }
}
