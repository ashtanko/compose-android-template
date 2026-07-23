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
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation3.runtime.NavBackStack
import androidx.navigation3.runtime.NavKey
import androidx.navigation3.runtime.entryProvider
import androidx.navigation3.runtime.rememberNavBackStack
import androidx.navigation3.ui.NavDisplay
import app.template.feature.home.ui.HomeRoute
import app.template.feature.posts.presentation.ui.PostsRoute
import app.template.home.ContentGreen

private const val TRANSITION_DURATION_MS = 1000

@Composable
fun MainNavigation(
    modifier: Modifier = Modifier,
    backStack: NavBackStack<NavKey> = rememberNavBackStack(Screen.ScreenA),
    postsContent: @Composable (Modifier) -> Unit = { PostsRoute(modifier = it) },
) {
    NavDisplay(
        backStack = backStack,
        onBack = { backStack.removeLastOrNull() },
        modifier = modifier,
        entryProvider = mainEntryProvider(
            backStack = backStack,
            postsContent = postsContent,
        ),
        transitionSpec = { horizontalSlideTransition(isPop = false) },
        popTransitionSpec = { horizontalSlideTransition(isPop = true) },
        predictivePopTransitionSpec = { horizontalSlideTransition(isPop = true) },
    )
}

private fun mainEntryProvider(
    backStack: NavBackStack<NavKey>,
    postsContent: @Composable (Modifier) -> Unit,
) = entryProvider {
    entry<Screen.ScreenA> {
        HomeRoute(
            onExploreNavigationClick = { backStack.add(Screen.ScreenB) },
            modifier = Modifier.fillMaxSize(),
        )
    }
    entry<Screen.ScreenB> {
        postsContent(Modifier.fillMaxSize())
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
