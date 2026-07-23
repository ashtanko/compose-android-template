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

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.tooling.preview.Preview
import app.template.core.designsystem.component.TemplateBackground
import app.template.core.designsystem.theme.TemplateSpacing
import app.template.feature.posts.presentation.R
import app.template.feature.posts.presentation.ui.components.ErrorContent
import app.template.feature.posts.presentation.ui.components.LoadingContent
import app.template.feature.posts.presentation.ui.components.PostsContent
import app.template.feature.posts.presentation.ui.model.PostUiModel
import kotlinx.collections.immutable.persistentListOf

@Composable
internal fun PostsScreen(
    state: PostsUiState,
    onRetryClick: () -> Unit,
    onLoadMoreClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    TemplateBackground(modifier = modifier) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .safeDrawingPadding(),
        ) {
            Text(
                text = stringResource(R.string.feature_posts_presentation_title),
                modifier = Modifier
                    .padding(
                        horizontal = TemplateSpacing.large,
                        vertical = TemplateSpacing.medium,
                    )
                    .semantics { heading() },
                style = MaterialTheme.typography.headlineMedium,
            )

            when (state) {
                PostsUiState.Loading -> LoadingContent(
                    modifier = Modifier.fillMaxSize(),
                )

                is PostsUiState.Error -> ErrorContent(
                    message = state.message,
                    onRetryClick = onRetryClick,
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(TemplateSpacing.large),
                )

                is PostsUiState.Success -> PostsContent(
                    state = state,
                    onLoadMoreClick = onLoadMoreClick,
                    modifier = Modifier.fillMaxSize(),
                )
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun PostsSuccessPreview() {
    MaterialTheme {
        PostsScreen(
            state = PostsUiState.Success(
                posts = persistentListOf(
                    PostUiModel(
                        id = 1,
                        title = "A clean boundary",
                        body = "DTOs stay in data while UI renders a dedicated model.",
                    ),
                ),
                canLoadMore = true,
            ),
            onRetryClick = {},
            onLoadMoreClick = {},
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun PostsErrorPreview() {
    MaterialTheme {
        PostsScreen(
            state = PostsUiState.Error(PostsErrorMessage.NetworkUnavailable),
            onRetryClick = {},
            onLoadMoreClick = {},
        )
    }
}
