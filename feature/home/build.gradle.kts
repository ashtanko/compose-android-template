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
    alias(libs.plugins.androidlab.android.feature)
    alias(libs.plugins.androidlab.android.library.jacoco)
    alias(libs.plugins.androidlab.android.junit5)
}

android {
    namespace = "app.template.feature.home"
}

dependencies {
    implementation(project(":library-kotlin"))

    libs.apply {
        androidx.apply {
            androidTestImplementation(test.ext)

            ui.apply {
                androidTestImplementation(test.junit4)
                debugImplementation(test.manifest)
            }
        }

        androidTestImplementation(truth)
    }
}
