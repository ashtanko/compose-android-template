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

package app.template.tests.e2e

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasSetTextAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import androidx.test.ext.junit.runners.AndroidJUnit4
import app.template.home.MainActivity
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
public class HomeJourneyTest {

    @get:Rule
    public val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    public fun userCalculatesFactorialAndInputSurvivesRecreation() {
        composeRule.onNodeWithText("Factorial input").performTextInput("5")
        composeRule.onNodeWithText("Calculate factorial").performClick()
        composeRule.onNodeWithText("5! = 120").assertIsDisplayed()

        composeRule.activityRule.scenario.recreate()

        composeRule.onNode(hasSetTextAction() and hasText("5")).assertIsDisplayed()
    }
}
