version = LibraryKotlinCoordinates.LIBRARY_VERSION

plugins {
    id("java-library")
    kotlin("jvm")
}

dependencies {
    implementation(libs.kotlin.stdlib)

    testImplementation(libs.junit5)
    testImplementation(libs.assertj)
}

java {
    sourceCompatibility = JavaVersion.VERSION_11
    targetCompatibility = JavaVersion.VERSION_11
}
