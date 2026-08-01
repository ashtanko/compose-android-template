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

package app.template.feature.posts.presentation

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import app.template.core.testing.screenshot.ScreenSizePreviews
import app.template.core.testing.screenshot.ScreenVariantPreviews
import app.template.feature.posts.presentation.ui.PostsErrorMessage
import app.template.feature.posts.presentation.ui.PostsScreen
import app.template.feature.posts.presentation.ui.PostsUiState
import app.template.feature.posts.presentation.ui.model.PostUiModel
import com.android.tools.screenshot.PreviewTest
import kotlinx.collections.immutable.persistentListOf

@PreviewTest
@ScreenSizePreviews
@Composable
public fun PostsScreenSizePreview() {
    PostsScreenContent()
}

@PreviewTest
@ScreenVariantPreviews
@Composable
public fun PostsScreenVariantPreview() {
    PostsScreenContent()
}

@PreviewTest
@Preview(name = "loading", widthDp = 400, heightDp = 500, showBackground = true)
@Composable
public fun PostsScreenLoadingPreview() {
    PostsScreenContent(state = PostsUiState.Loading)
}

@PreviewTest
@Preview(name = "error", widthDp = 400, heightDp = 500, showBackground = true)
@Composable
public fun PostsScreenErrorPreview() {
    PostsScreenContent(
        state = PostsUiState.Error(PostsErrorMessage.NetworkUnavailable),
    )
}

@PreviewTest
@Preview(name = "empty", widthDp = 400, heightDp = 500, showBackground = true)
@Composable
public fun PostsScreenEmptyPreview() {
    PostsScreenContent(
        state = PostsUiState.Success(
            posts = persistentListOf(),
            canLoadMore = false,
        ),
    )
}

@Composable
private fun PostsScreenContent(
    state: PostsUiState = PostsUiState.Success(
        posts = persistentListOf(
            PostUiModel(
                id = 1,
                title = "A deterministic post",
                body = "Screenshot tests render fixed local content.",
            ),
            PostUiModel(
                id = 2,
                title = "A second post",
                body = "The same state is checked at every supported window class.",
            ),
        ),
        canLoadMore = true,
    ),
) {
    val colorScheme = if (isSystemInDarkTheme()) darkColorScheme() else lightColorScheme()
    MaterialTheme(colorScheme = colorScheme) {
        PostsScreen(
            state = state,
            onRetryClick = {},
            onLoadMoreClick = {},
        )
    }
}
