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

package app.template.feature.home.ui.model

internal data class HomeUiState(
    internal val input: String = "",
    internal val result: FactorialResult? = null,
    internal val inputError: HomeInputError? = null,
)

internal data class FactorialResult(
    internal val input: Int,
    internal val value: Long,
)

internal enum class HomeInputError {
    Required,
    InvalidNumber,
    OutOfRange,
}
