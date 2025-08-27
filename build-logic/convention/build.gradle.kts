plugins {
    `kotlin-dsl`
}

group = "dev.shtanko.androidlab.buildlogic"

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

dependencies {
    compileOnly(libs.android.gradlePlugin)
    compileOnly(libs.android.tools.common)
    compileOnly(libs.compose.gradlePlugin)
    compileOnly(libs.kotlin.gradlePlugin)
    compileOnly(libs.ksp.gradlePlugin)
    compileOnly(libs.room.gradlePlugin)
    compileOnly(libs.detekt.gradle)
    compileOnly(libs.spotless.gradlePlugin)
    compileOnly(libs.compose.guardPlugin)
}

gradlePlugin {
    plugins {
        register("androidApplicationCompose") {
            id = "androidlab.android.application.compose"
            implementationClass = "AndroidApplicationComposeConventionPlugin"
        }
        register("androidApplication") {
            id = "androidlab.android.application"
            implementationClass = "AndroidApplicationConventionPlugin"
        }
        register("androidLibraryCompose") {
            id = "androidlab.android.library.compose"
            implementationClass = "AndroidLibraryComposeConventionPlugin"
        }
        register("androidLibrary") {
            id = "androidlab.android.library"
            implementationClass = "AndroidLibraryConventionPlugin"
        }
        register("androidFeature") {
            id = "androidlab.android.feature"
            implementationClass = "AndroidFeatureConventionPlugin"
        }
        register("hilt") {
            id = "androidlab.hilt"
            implementationClass = "HiltConventionPlugin"
        }
        register("androidHilt") {
            id = "androidlab.hilt.android"
            implementationClass = "AndroidHiltConventionPlugin"
        }
        register("spotless") {
            id = "androidlab.spotless"
            implementationClass = "SpotlessConventionPlugin"
        }
        register("androidLint") {
            id = "androidlab.android.lint"
            implementationClass = "AndroidLintConventionPlugin"
        }
        register("androidApplicationJacoco") {
            id = "androidlab.android.application.jacoco"
            implementationClass = "AndroidApplicationJacocoConventionPlugin"
        }
        register("androidLibraryJacoco") {
            id = "androidlab.android.library.jacoco"
            implementationClass = "AndroidLibraryJacocoConventionPlugin"
        }
        register("jvmLibrary") {
            id = "androidlab.jvm.library"
            implementationClass = "JvmLibraryConventionPlugin"
        }
        register("room") {
            id = "androidlab.android.room"
            implementationClass = "AndroidRoomConventionPlugin"
        }
    }
}
