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

package app.template.feature.home

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import app.template.library.FactorialCalculator
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

internal const val MAX_FACTORIAL_INPUT = 20

class HomeViewModel internal constructor(
    private val savedStateHandle: SavedStateHandle,
) : ViewModel() {

    private val mutableState = MutableStateFlow(
        HomeUiState(input = savedStateHandle[INPUT_KEY] ?: ""),
    )
    val state: StateFlow<HomeUiState> = mutableState.asStateFlow()

    fun onInputChanged(input: String) {
        savedStateHandle[INPUT_KEY] = input
        mutableState.update { current ->
            current.copy(
                input = input,
                result = null,
                inputError = null,
            )
        }
    }

    fun onCalculateClick() {
        val input = state.value.input
        val parsedInput = input.toIntOrNull()
        val inputError = when {
            input.isBlank() -> HomeInputError.Required
            parsedInput == null -> HomeInputError.InvalidNumber
            parsedInput !in 0..MAX_FACTORIAL_INPUT -> HomeInputError.OutOfRange
            else -> null
        }

        if (inputError != null) {
            mutableState.update { current ->
                current.copy(
                    result = null,
                    inputError = inputError,
                )
            }
            return
        }

        checkNotNull(parsedInput)
        val result = FactorialResult(
            input = parsedInput,
            value = FactorialCalculator.computeFactorial(parsedInput),
        )
        mutableState.update { current ->
            current.copy(
                result = result,
                inputError = null,
            )
        }
    }

    private companion object {
        const val INPUT_KEY = "factorial_input"
    }
}
