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

package app.template

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.navigation3.runtime.rememberNavBackStack
import androidx.test.espresso.Espresso
import app.template.home.navigation.MainNavigation
import app.template.home.navigation.Screen
import org.junit.Rule
import org.junit.Test

class MainNavigationTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun testNavigationFlow_FromAToC() {
        // Start the app
        composeTestRule.setContent {
            MainNavigation()
        }

        // 1. Verify we start on Screen A
        composeTestRule.onNodeWithText("This is Screen A").assertIsDisplayed()

        // 2. Navigate to Screen B
        composeTestRule.onNodeWithText("Go to Screen B").performClick()

        // Wait for transition and verify Screen B
        composeTestRule.onNodeWithText("This is Screen B").assertIsDisplayed()
        composeTestRule.onNodeWithText("This is Screen A").assertDoesNotExist()

        // 3. Navigate to Screen C
        composeTestRule.onNodeWithText("Go to Screen C").performClick()

        // Verify Screen C
        composeTestRule.onNodeWithText("This is Screen C").assertIsDisplayed()
    }

    @Test
    fun testBackNavigation_RemovesEntries() {
        composeTestRule.setContent {
            MainNavigation()
        }

        // Navigate to Screen B
        composeTestRule.onNodeWithText("Go to Screen B").performClick()
        composeTestRule.onNodeWithText("This is Screen B").assertIsDisplayed()

        // Trigger system back (Navigation3 handles this via the onBack lambda)
        Espresso.pressBack()

        // Verify we are back on Screen A
        composeTestRule.onNodeWithText("This is Screen A").assertIsDisplayed()
        composeTestRule.onNodeWithText("This is Screen B").assertDoesNotExist()
    }

    @Test
    fun testStartAtScreenB() {
        composeTestRule.setContent {
            // Testability: we can start at any screen by providing a custom backstack
            val backStack = rememberNavBackStack(Screen.ScreenB)
            MainNavigation(backStack = backStack)
        }

        // Verify we start on Screen B
        composeTestRule.onNodeWithText("This is Screen B").assertIsDisplayed()
        composeTestRule.onNodeWithText("Go to Screen C").assertIsDisplayed()
    }
}
