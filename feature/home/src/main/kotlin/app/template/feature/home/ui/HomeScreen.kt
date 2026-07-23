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

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import app.template.core.designsystem.component.TemplateBackground
import app.template.core.designsystem.theme.TemplateSpacing
import app.template.feature.home.ui.components.HomeContent
import app.template.feature.home.ui.model.FactorialResult
import app.template.feature.home.ui.model.HomeUiState

@Composable
internal fun HomeScreen(
    state: HomeUiState,
    onInputChanged: (String) -> Unit,
    onCalculateClick: () -> Unit,
    onExploreNavigationClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    TemplateBackground(modifier = modifier) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .safeDrawingPadding()
                .padding(TemplateSpacing.large),
            contentAlignment = Alignment.Center,
        ) {
            HomeContent(
                state = state,
                onInputChanged = onInputChanged,
                onCalculateClick = onCalculateClick,
                onExploreNavigationClick = onExploreNavigationClick,
                modifier = Modifier
                    .fillMaxWidth()
                    .widthIn(max = MAX_CONTENT_WIDTH)
                    .verticalScroll(rememberScrollState()),
            )
        }
    }
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
