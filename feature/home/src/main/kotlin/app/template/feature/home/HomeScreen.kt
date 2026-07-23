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

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.error
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import app.template.core.designsystem.component.TemplateBackground
import app.template.core.designsystem.component.TemplateButton
import app.template.core.designsystem.component.TemplateOutlinedButton
import app.template.core.designsystem.theme.TemplateSpacing

@Composable
fun HomeScreen(
    state: HomeUiState,
    onInputChanged: (String) -> Unit,
    onCalculateClick: () -> Unit,
    onExploreNavigationClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val keyboardController = LocalSoftwareKeyboardController.current
    val inputError = state.inputError.toMessage()

    TemplateBackground(modifier = modifier) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .safeDrawingPadding()
                .padding(TemplateSpacing.large),
            contentAlignment = Alignment.Center,
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .widthIn(max = MAX_CONTENT_WIDTH)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(TemplateSpacing.medium),
            ) {
                Text(
                    text = stringResource(R.string.feature_home_title),
                    modifier = Modifier.semantics { heading() },
                    style = MaterialTheme.typography.headlineMedium,
                )
                Text(
                    text = stringResource(R.string.feature_home_subtitle),
                    style = MaterialTheme.typography.bodyLarge,
                )
                OutlinedTextField(
                    value = state.input,
                    onValueChange = onInputChanged,
                    modifier = Modifier
                        .fillMaxWidth()
                        .then(
                            if (inputError != null) {
                                Modifier.semantics { error(inputError) }
                            } else {
                                Modifier
                            },
                        ),
                    label = { Text(stringResource(R.string.feature_home_input_label)) },
                    supportingText = {
                        Text(
                            inputError ?: stringResource(
                                R.string.feature_home_input_supporting_text,
                                MAX_FACTORIAL_INPUT,
                            ),
                        )
                    },
                    isError = inputError != null,
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Number,
                        imeAction = ImeAction.Done,
                    ),
                    keyboardActions = KeyboardActions(
                        onDone = {
                            onCalculateClick()
                            keyboardController?.hide()
                        },
                    ),
                )
                TemplateButton(
                    onClick = onCalculateClick,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(stringResource(R.string.feature_home_calculate))
                }
                state.result?.let { result ->
                    Text(
                        text = stringResource(
                            R.string.feature_home_result,
                            result.input,
                            result.value,
                        ),
                        style = MaterialTheme.typography.titleLarge,
                    )
                }
                TemplateOutlinedButton(
                    onClick = onExploreNavigationClick,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(stringResource(R.string.feature_home_explore_navigation))
                }
            }
        }
    }
}

@Composable
private fun HomeInputError?.toMessage(): String? = when (this) {
    HomeInputError.Required -> stringResource(R.string.feature_home_error_required)
    HomeInputError.InvalidNumber -> stringResource(R.string.feature_home_error_invalid_number)
    HomeInputError.OutOfRange -> stringResource(
        R.string.feature_home_error_out_of_range,
        MAX_FACTORIAL_INPUT,
    )
    null -> null
}

@Preview(showBackground = true)
@Composable
private fun HomeScreenPreview() {
    MaterialTheme {
        HomeScreen(
            state = HomeUiState(
                input = "5",
                result = FactorialResult(input = 5, value = 120),
            ),
            onInputChanged = {},
            onCalculateClick = {},
            onExploreNavigationClick = {},
        )
    }
}

private val MAX_CONTENT_WIDTH = 560.dp
