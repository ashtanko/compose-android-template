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

import android.content.res.Configuration
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import app.template.feature.home.ui.HomeScreen
import app.template.feature.home.ui.model.FactorialResult
import app.template.feature.home.ui.model.HomeUiState
import com.android.tools.screenshot.PreviewTest

@PreviewTest
@Preview(
    name = "Home calculated result",
    widthDp = 400,
    heightDp = 500,
    locale = "en",
    fontScale = 1f,
    uiMode = Configuration.UI_MODE_NIGHT_NO,
    showBackground = true,
)
@Composable
public fun HomeScreenCalculatedResultPreview() {
    MaterialTheme(colorScheme = lightColorScheme()) {
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
