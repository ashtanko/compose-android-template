plugins {
    alias(libs.plugins.androidlab.android.test)
}

android {
    namespace = "dev.shtanko.template.benchmarks"
    targetProjectPath = ":app"
    experimentalProperties["android.experimental.self-instrumenting"] = true
}

dependencies {
    implementation(libs.androidx.junit)
    implementation(libs.androidx.uiautomator)
    implementation(libs.benchmark.macro.junit4)
}
