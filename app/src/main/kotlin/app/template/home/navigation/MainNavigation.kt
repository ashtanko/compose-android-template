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

package app.template.home.navigation

import androidx.compose.animation.ContentTransform
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.slideOutVertically
import androidx.compose.animation.togetherWith
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.navigation3.runtime.NavBackStack
import androidx.navigation3.runtime.NavKey
import androidx.navigation3.runtime.entryProvider
import androidx.navigation3.runtime.rememberNavBackStack
import androidx.navigation3.ui.NavDisplay
import app.template.home.ContentGreen
import app.template.home.ContentMauve
import app.template.home.ContentOrange

private const val TRANSITION_DURATION_MS = 1000

@Composable
fun MainNavigation(
    backStack: NavBackStack<NavKey> = rememberNavBackStack(Screen.ScreenA),
) {
    NavDisplay(
        backStack = backStack,
        onBack = { backStack.removeLastOrNull() },
        entryProvider = mainEntryProvider(backStack),
        transitionSpec = { horizontalSlideTransition(isPop = false) },
        popTransitionSpec = { horizontalSlideTransition(isPop = true) },
        predictivePopTransitionSpec = { horizontalSlideTransition(isPop = true) },
    )
}

private fun mainEntryProvider(backStack: NavBackStack<NavKey>) = entryProvider {
    entry<Screen.ScreenA> {
        ContentOrange("This is Screen A") {
            Button(onClick = { backStack.add(Screen.ScreenB) }) { Text("Go to Screen B") }
        }
    }
    entry<Screen.ScreenB> {
        ContentMauve("This is Screen B") {
            Button(onClick = { backStack.add(Screen.ScreenC) }) { Text("Go to Screen C") }
        }
    }
    entry<Screen.ScreenC>(metadata = verticalSlideTransitionSpec()) {
        ContentGreen("This is Screen C")
    }
}

private fun verticalSlideTransitionSpec() =
    NavDisplay.transitionSpec {
        slideInVertically(
            initialOffsetY = { it },
            animationSpec = tween(TRANSITION_DURATION_MS),
        ) togetherWith ExitTransition.KeepUntilTransitionsFinished
    } + NavDisplay.popTransitionSpec {
        EnterTransition.None togetherWith slideOutVertically(
            targetOffsetY = { it },
            animationSpec = tween(TRANSITION_DURATION_MS),
        )
    } + NavDisplay.predictivePopTransitionSpec {
        EnterTransition.None togetherWith slideOutVertically(
            targetOffsetY = { it },
            animationSpec = tween(TRANSITION_DURATION_MS),
        )
    }

private fun horizontalSlideTransition(isPop: Boolean): ContentTransform {
    val multiplier = if (isPop) -1 else 1
    return slideInHorizontally(
        initialOffsetX = { it * multiplier },
        animationSpec = tween(TRANSITION_DURATION_MS),
    ) togetherWith slideOutHorizontally(
        targetOffsetX = { -it * multiplier },
        animationSpec = tween(TRANSITION_DURATION_MS),
    )
}
