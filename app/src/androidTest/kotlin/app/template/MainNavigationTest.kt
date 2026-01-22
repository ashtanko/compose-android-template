package app.template

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.espresso.Espresso
import app.template.home.MainNavigation
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
}
