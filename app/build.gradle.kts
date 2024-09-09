import  dev.shtanko.template.ShotBuildType

plugins {
  alias(libs.plugins.template.android.application)
  alias(libs.plugins.template.android.application.compose)
  alias(libs.plugins.template.android.application.jacoco)
  alias(libs.plugins.template.hilt)
  alias(libs.plugins.roborazzi)
}

android {
  namespace = "dev.shtanko.template"
  compileSdk = 35
  compileSdkPreview = "VanillaIceCream"

  defaultConfig {
    applicationId = "dev.shtanko.template"
    minSdk = 26
    targetSdk = 35
    versionCode = 1
    versionName = "0.0.1" // X.Y.Z; X = Major, Y = minor, Z = Patch level

    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

    vectorDrawables {
      useSupportLibrary = true
    }
  }

  buildTypes {
    debug {
      applicationIdSuffix = ShotBuildType.DEBUG.applicationIdSuffix
    }
    release {
      isMinifyEnabled = true
      applicationIdSuffix = ShotBuildType.RELEASE.applicationIdSuffix
      proguardFiles(
        getDefaultProguardFile("proguard-android-optimize.txt"),
        "proguard-rules.pro"
      )
    }
  }

  compileOptions {
    sourceCompatibility = JavaVersion.VERSION_1_8
    targetCompatibility = JavaVersion.VERSION_1_8
  }

  testOptions {
    unitTests {
      isIncludeAndroidResources = true
    }
  }

  kotlinOptions {
    jvmTarget = "1.8"
  }

  buildFeatures {
    compose = true
  }

  packaging.resources {
    // The Rome library JARs embed some internal utils libraries in nested JARs.
    // We don't need them so we exclude them in the final package.
    excludes += "/*.jar"

    // Multiple dependency bring these files in. Exclude them to enable
    // our test APK to build (has no effect on our AARs)
    excludes += "/META-INF/AL2.0"
    excludes += "/META-INF/LGPL2.1"
  }
}

dependencies {
  implementation(libs.androidx.palette)

  implementation(libs.androidx.activity.compose)
  implementation(libs.androidx.compose.material3.adaptive)
  implementation(libs.androidx.compose.material3.adaptive.layout)
  implementation(libs.androidx.compose.material3.adaptive.navigation)
  implementation(libs.androidx.compose.material3.windowSizeClass)
  implementation(libs.androidx.compose.runtime.tracing)
  implementation(libs.androidx.core.ktx)
  implementation(libs.androidx.hilt.navigation.compose)
  implementation(libs.androidx.tracing.ktx)
  implementation(libs.coil.kt)
  implementation(libs.androidx.material3.android)

  implementation(libs.paging.compose)

  val composeBom = platform(libs.androidx.compose.bom)
  implementation(composeBom)
  androidTestImplementation(composeBom)

  // Dependency injection
  implementation(libs.androidx.hilt.navigation.compose)
  implementation(libs.hilt.android)
  ksp(libs.hilt.compiler)

  implementation(libs.androidx.hilt.navigation.compose)
  implementation(libs.androidx.ui)
  implementation(libs.androidx.ui.graphics)
  implementation(libs.androidx.ui.tooling.preview)
  implementation(libs.androidx.compose.runtime.tracing)

  ksp(libs.hilt.compiler)

  testImplementation(libs.junit)
  testImplementation(libs.hilt.android.testing)

  androidTestImplementation(libs.androidx.junit)
  androidTestImplementation(libs.androidx.ui.test.junit4)
  androidTestImplementation(libs.hilt.android.testing)
  debugImplementation(libs.androidx.ui.tooling)
  debugImplementation(libs.androidx.ui.test.manifest)
}
java {
  toolchain {
    languageVersion = JavaLanguageVersion.of(17)
  }
}
