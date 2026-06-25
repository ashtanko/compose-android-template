plugins {
    alias(libs.plugins.androidlab.android.library)
    alias(libs.plugins.androidlab.hilt)
    alias(libs.plugins.hilt)
    alias(libs.plugins.serialization)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.android.junit5)
    alias(libs.plugins.androidlab.android.library.jacoco)
}

android {
    namespace = "app.template.core.navigation"
}

dependencies {
    api(libs.androidx.navigation3.runtime)
    implementation(libs.androidx.savedstate.compose)
    implementation(libs.androidx.lifecycle.viewmodel.navigation3)

    testImplementation(libs.truth)

    libs.apply {
        junit5.apply {
            testImplementation(api)
            testImplementation(params)

            testRuntimeOnly(jupiterEngine)
            testRuntimeOnly(vintageEngine)
        }
    }

    androidTestImplementation(libs.junit5.api)
    androidTestImplementation(libs.android.junit5.test.core)
    androidTestRuntimeOnly(libs.android.junit5.test.runner)
    androidTestImplementation(libs.androidx.test.ext)
    androidTestImplementation(libs.androidx.compose.ui.testManifest)
    androidTestImplementation(libs.androidx.lifecycle.viewModel.testing)
    androidTestImplementation(libs.truth)
}
