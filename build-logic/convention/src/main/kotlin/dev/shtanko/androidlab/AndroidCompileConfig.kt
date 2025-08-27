package dev.shtanko.androidlab

import com.android.build.api.dsl.LibraryExtension
import org.gradle.api.JavaVersion

fun LibraryExtension.configureAndroidCompileOptions() {
    compileSdk = 36
    defaultConfig.minSdk = 21

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }
}
