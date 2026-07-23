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

package app.template.feature.home.ui

import androidx.lifecycle.SavedStateHandle
import app.template.feature.home.ui.model.FactorialResult
import app.template.feature.home.ui.model.HomeInputError
import app.template.feature.home.ui.model.HomeUiState
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

internal class HomeViewModelTest {

    @Test
    internal fun `calculate valid input updates result`() {
        val viewModel = HomeViewModel(SavedStateHandle())

        viewModel.onInputChanged("5")
        viewModel.onCalculateClick()

        assertThat(viewModel.state.value).isEqualTo(
            HomeUiState(
                input = "5",
                result = FactorialResult(input = 5, value = 120),
            ),
        )
    }

    @Test
    internal fun `calculate blank input reports required error`() {
        val viewModel = HomeViewModel(SavedStateHandle())

        viewModel.onCalculateClick()

        assertThat(viewModel.state.value.inputError).isEqualTo(HomeInputError.Required)
    }

    @Test
    internal fun `calculate non numeric input reports invalid number error`() {
        val viewModel = HomeViewModel(SavedStateHandle())

        viewModel.onInputChanged("not a number")
        viewModel.onCalculateClick()

        assertThat(viewModel.state.value.inputError).isEqualTo(HomeInputError.InvalidNumber)
    }

    @Test
    internal fun `calculate input above safe long range reports range error`() {
        val viewModel = HomeViewModel(SavedStateHandle())

        viewModel.onInputChanged("21")
        viewModel.onCalculateClick()

        assertThat(viewModel.state.value.inputError).isEqualTo(HomeInputError.OutOfRange)
    }

    @Test
    internal fun `editing input clears prior result and persists the input`() {
        val savedStateHandle = SavedStateHandle()
        val viewModel = HomeViewModel(savedStateHandle)
        viewModel.onInputChanged("5")
        viewModel.onCalculateClick()

        viewModel.onInputChanged("6")

        assertThat(viewModel.state.value).isEqualTo(HomeUiState(input = "6"))
        assertThat(HomeViewModel(savedStateHandle).state.value.input).isEqualTo("6")
    }
}
