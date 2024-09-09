version = LibraryKotlinCoordinates.LIBRARY_VERSION

plugins {
    id("java-library")
    kotlin("jvm")
    id("maven-publish")
    id("com.android.lint")
    //publish
    jacoco
}

tasks {
    jacocoTestReport {
        reports {
            html.required.set(true)
            xml.required.set(true)
            xml.outputLocation.set(file("$buildDir/reports/jacoco/report.xml"))
        }
        executionData(file("build/jacoco/test.exec"))
    }

    withType<Test>().configureEach {
        jvmArgs = listOf(
            "-Dkotlintest.tags.exclude=Integration,EndToEnd,Performance"
        )
        testLogging {
            events("passed", "skipped", "failed")
        }
        testLogging.showStandardStreams = true
        useJUnitPlatform()
    }
}

dependencies {
    api(libs.kotlin.stdlib)
    api(libs.kotlin.coroutines.core)

    testImplementation(libs.junit)
    testImplementation(libs.junit5)

    // // (Required) Writing and executing Unit Tests on the JUnit Platform
    //  testImplementation("org.junit.jupiter:junit-jupiter-api:5.8.2")
    //  testRuntimeOnly("org.junit.jupiter:junit-jupiter-engine:5.8.2")
    //
    //  // (Optional) If you need "Parameterized Tests"
    //  testImplementation("org.junit.jupiter:junit-jupiter-params:5.8.2")
}

java {
    sourceCompatibility = JavaVersion.VERSION_11
    targetCompatibility = JavaVersion.VERSION_11
}
