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
    alias(libs.plugins.androidlab.jvm.library)
    alias(libs.plugins.androidlab.hilt)
    alias(libs.plugins.androidlab.kotlin.explicit.visibility)
    alias(libs.plugins.serialization)
}

dependencies {
    implementation(project(":feature:posts:domain"))
    implementation(libs.kotlinx.coroutines.core)
    implementation(libs.kotlinx.serialization)
    implementation(libs.square.okhttp)
    implementation(libs.square.retrofit.core)
    implementation(libs.square.retrofit.kotlin.serialization)

    testImplementation(libs.kotlinx.coroutines.test)
}
