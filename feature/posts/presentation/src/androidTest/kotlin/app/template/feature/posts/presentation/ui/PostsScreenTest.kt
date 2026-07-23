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

package app.template.feature.posts.presentation.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import app.template.feature.posts.presentation.ui.model.PostUiModel
import com.google.common.truth.Truth.assertThat
import kotlinx.collections.immutable.persistentListOf
import org.junit.Rule
import org.junit.Test

public class PostsScreenTest {

    @get:Rule
    public val composeTestRule = createComposeRule()

    @Test
    public fun loadingStateIsDisplayed() {
        setContent(state = PostsUiState.Loading)

        composeTestRule.onNodeWithText("Posts").assertIsDisplayed()
        composeTestRule.onNodeWithContentDescription("Loading posts").assertIsDisplayed()
    }

    @Test
    public fun errorStateDisplaysMessageAndForwardsRetry() {
        var retryClicks = 0
        setContent(
            state = PostsUiState.Error(PostsErrorMessage.NetworkUnavailable),
            onRetryClick = { retryClicks += 1 },
        )

        composeTestRule.onNodeWithText("Check your connection and try again.").assertIsDisplayed()
        composeTestRule.onNodeWithText("Retry").performClick()

        assertThat(retryClicks).isEqualTo(1)
    }

    @Test
    public fun successStateDisplaysPostsAndForwardsLoadMore() {
        var loadMoreClicks = 0
        setContent(
            state = PostsUiState.Success(
                posts = persistentListOf(
                    PostUiModel(
                        id = 1,
                        title = "A post title",
                        body = "A post body",
                    ),
                ),
                canLoadMore = true,
            ),
            onLoadMoreClick = { loadMoreClicks += 1 },
        )

        composeTestRule.onNodeWithText("A post title").assertIsDisplayed()
        composeTestRule.onNodeWithText("A post body").assertIsDisplayed()
        composeTestRule.onNodeWithText("Load more").performClick()

        assertThat(loadMoreClicks).isEqualTo(1)
    }

    private fun setContent(
        state: PostsUiState,
        onRetryClick: () -> Unit = {},
        onLoadMoreClick: () -> Unit = {},
    ) {
        composeTestRule.setContent {
            MaterialTheme {
                PostsScreen(
                    state = state,
                    onRetryClick = onRetryClick,
                    onLoadMoreClick = onLoadMoreClick,
                )
            }
        }
    }
}
