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

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import app.template.feature.home.ui.model.FactorialResult
import app.template.feature.home.ui.model.HomeInputError
import app.template.feature.home.ui.model.HomeUiState
import com.google.common.truth.Truth.assertThat
import org.junit.Rule
import org.junit.Test

public class HomeScreenTest {

    @get:Rule
    public val composeTestRule = createComposeRule()

    @Test
    public fun inputAndActionsForwardUserIntent() {
        var input = ""
        var calculateClicks = 0
        var navigationClicks = 0
        composeTestRule.setContent {
            MaterialTheme {
                HomeScreen(
                    state = HomeUiState(),
                    onInputChanged = { input = it },
                    onCalculateClick = { calculateClicks += 1 },
                    onExploreNavigationClick = { navigationClicks += 1 },
                )
            }
        }

        composeTestRule.onNodeWithText("Factorial input").performTextInput("5")
        composeTestRule.onNodeWithText("Calculate factorial").performClick()
        composeTestRule.onNodeWithText("Explore navigation").performClick()

        assertThat(input).isEqualTo("5")
        assertThat(calculateClicks).isEqualTo(1)
        assertThat(navigationClicks).isEqualTo(1)
    }

    @Test
    public fun resultAndValidationErrorAreDisplayed() {
        composeTestRule.setContent {
            MaterialTheme {
                HomeScreen(
                    state = HomeUiState(
                        input = "21",
                        result = FactorialResult(input = 5, value = 120),
                        inputError = HomeInputError.OutOfRange,
                    ),
                    onInputChanged = {},
                    onCalculateClick = {},
                    onExploreNavigationClick = {},
                )
            }
        }

        composeTestRule.onNodeWithText("5! = 120").assertIsDisplayed()
        composeTestRule.onNodeWithText("Enter a number from 0 to 20.").assertIsDisplayed()
    }
}
