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

package app.template.core.designsystem.component

import androidx.compose.material3.Text
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import kotlin.test.assertEquals

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
public class TemplateComponentsTest {
    @get:Rule
    public val composeTestRule = createComposeRule()

    @Test
    public fun templateButtonInvokesClickCallback() {
        var clickCount = 0
        composeTestRule.setContent {
            TemplateButton(onClick = { clickCount += 1 }) {
                Text("Continue")
            }
        }

        composeTestRule.onNodeWithText("Continue").performClick()

        composeTestRule.runOnIdle {
            assertEquals(1, clickCount)
        }
    }

    @Test
    public fun templateButtonExposesDisabledState() {
        composeTestRule.setContent {
            TemplateButton(
                onClick = {},
                enabled = false,
            ) {
                Text("Continue")
            }
        }

        composeTestRule.onNodeWithText("Continue").assertIsNotEnabled()
    }

    @Test
    public fun emptyStateDisplaysProvidedContent() {
        composeTestRule.setContent {
            TemplateEmptyState(
                headlineContent = { Text("No results") },
                supportingContent = { Text("Try a different search") },
            )
        }

        composeTestRule.onNodeWithText("No results").assertIsDisplayed()
        composeTestRule.onNodeWithText("Try a different search").assertIsDisplayed()
    }

    @Test
    public fun loadingIndicatorExposesDescription() {
        composeTestRule.setContent {
            TemplateLoadingIndicator(contentDescription = "Loading content")
        }

        composeTestRule.onNodeWithContentDescription("Loading content").assertIsDisplayed()
    }
}
