plugins {
    alias(libs.plugins.androidlab.jvm.library)
}

dependencies {
    libs.apply {
        junit5.apply {
            testImplementation(api)
            testImplementation(params)

            testRuntimeOnly(jupiterEngine)
            testRuntimeOnly(vintageEngine)
        }

        testImplementation(assertj.core)
    }
}
