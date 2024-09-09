@file:Suppress("UnstableApiUsage")

pluginManagement {
    includeBuild("build-logic")
    repositories {
        gradlePluginPortal()
        google()
        mavenCentral()
        maven(url = "https://plugins.gradle.org/m2/")
    }
}
plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version "0.8.0"
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven(url = "https://plugins.gradle.org/m2/")
    }
}

rootProject.name = "template"
enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")
include(":app")
include(":domain")

include(":core:data")
include(":core:shared")
include(":core:database")
include(":core:model")

include(":core:network")
include(":core:testing")
include(":core:navigation")
include(":core:designsystem")
include(":core:di")
include(":core:utils")
include(":core:datastore-test")
include(":core:datastore-proto")
include(":core:datastore")
include(":core:extension")

//include(":feature:search")
//include(":feature:about")
//include(":feature:settings")
//include(":feature:photo")
//include(":feature:collection")
//include(":feature:topic")
//include(":feature:stats")
//include(":feature:home")
//include(":feature:user")
//include(":feature:login")
//include(":feature:filter")
