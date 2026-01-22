/*
 * Designed and developed by 2022 ashtanko (Oleksii Shtanko)
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

package app.template.home

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.animation.ContentTransform
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.ExperimentalSharedTransitionApi
import androidx.compose.animation.core.tween
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.slideOutVertically
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.tooling.preview.datasource.LoremIpsum
import androidx.compose.ui.unit.dp
import androidx.core.view.WindowCompat
import androidx.navigation3.runtime.NavBackStack
import androidx.navigation3.runtime.NavKey
import androidx.navigation3.runtime.entryProvider
import androidx.navigation3.runtime.rememberNavBackStack
import androidx.navigation3.ui.NavDisplay
import app.template.home.navigation.Screen
import app.template.ui.setEdgeToEdgeConfig
import app.template.ui.theme.PastelGreen
import app.template.ui.theme.PastelMauve
import app.template.ui.theme.PastelOrange
import app.template.ui.theme.TemplateTheme

private const val TRANSITION_DURATION_MS = 1000

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        setEdgeToEdgeConfig()
        super.onCreate(savedInstanceState)

        // This app draws behind the system bars, so we want to handle fitting system windows
        WindowCompat.setDecorFitsSystemWindows(window, false)

        setContent {
            MainNavigation()
        }
    }
}

@Composable
fun MainNavigation() {
    val backStack = rememberNavBackStack(Screen.ScreenA)

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

@Composable
private fun ContentOrange(
    title: String,
    modifier: Modifier = Modifier,
    onNext: (() -> Unit)? = null,
    content: (@Composable () -> Unit)? = null,
) = ContentBase(
    title = title,
    modifier = modifier.background(PastelOrange),
    onNext = onNext,
    content = content,
)

@Composable
private fun ContentGreen(
    title: String,
    modifier: Modifier = Modifier,
    onNext: (() -> Unit)? = null,
    content: (@Composable () -> Unit)? = null,
) = ContentBase(
    title = title,
    modifier = modifier.background(PastelGreen),
    onNext = onNext,
    content = content,
)

@Composable
private fun ContentMauve(
    title: String,
    modifier: Modifier = Modifier,
    onNext: (() -> Unit)? = null,
    content: (@Composable () -> Unit)? = null,
) = ContentBase(
    title = title,
    modifier = modifier.background(PastelMauve),
    onNext = onNext,
    content = content,
)

@OptIn(ExperimentalSharedTransitionApi::class)
@Composable
private fun ContentBase(
    title: String,
    modifier: Modifier = Modifier,
    onNext: (() -> Unit)? = null,
    content: (@Composable () -> Unit)? = null,
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = modifier
            .fillMaxSize()
            .safeDrawingPadding()
            .clip(RoundedCornerShape(48.dp)),
    ) {
        Title(title)
        if (content != null) content()
        if (onNext != null) {
            Button(
                modifier = Modifier.align(Alignment.CenterHorizontally),
                onClick = onNext,
            ) {
                Text("Next")
            }
        }
    }
}

@Composable
private fun ColumnScope.Title(title: String) {
    Text(
        modifier = Modifier
            .padding(24.dp)
            .align(Alignment.CenterHorizontally),
        fontWeight = FontWeight.Bold,
        text = title,
    )
}

@Composable
@Preview
private fun ContentAPreview() {
    TemplateTheme {
        ContentOrange(
            title = LoremIpsum(3).values.first(),
        )
    }
}
