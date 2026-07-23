/*
 * Designed and developed by 2026 ashtanko (Oleksii Shtanko)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
plugins {
    alias(libs.plugins.androidlab.android.library.compose)
    alias(libs.plugins.androidlab.android.library.jacoco)
    alias(libs.plugins.androidlab.android.junit5)
    alias(libs.plugins.androidlab.android.roborazzi)
}

android {
    namespace = "app.template.library.android"

    defaultConfig {
        consumerProguardFiles("consumer-rules.pro")
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
            }
        }

        testImplementation(assertj.core)
    }
}
