plugins {
    alias(libs.plugins.androidlab.android.library)
    alias(libs.plugins.androidlab.android.library.compose)
    alias(libs.plugins.androidlab.android.library.jacoco)
    alias(libs.plugins.roborazzi)
}

android {
    namespace = "app.template.library.android"

    compileSdk = libs.versions.compileSdk.get().toInt()

    defaultConfig {
        minSdk = libs.versions.minSdk.get().toInt()

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        consumerProguardFiles("consumer-rules.pro")
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
    }
}

tasks {
    withType<Test> {
        useJUnitPlatform()
    }
}

dependencies {
    libs.apply {
        androidx.apply {
            compose.apply {
                api(foundation)
                api(foundation.layout)
                api(icons.extended)
                api(material3.adaptive)
                api(material3.adaptive.layout)
                api(material3.adaptive.navigation)
                api(material3.adaptive.navigationSuite)
                api(materialWindow)
            }
            ui.apply {
                api(text.google.fonts)
                debugApi(test.manifest)
                androidTestApi(test.junit4)
                androidTestApi(test)
            }
        }

        junit5.apply {
            testImplementation(api)
            testImplementation(params)

            testRuntimeOnly(jupiterEngine)
            testRuntimeOnly(vintageEngine)
        }

        testImplementation(assertj.core)
    }
}
