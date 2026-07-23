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

package app.template.feature.posts.presentation.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.error
import androidx.compose.ui.semantics.semantics
import app.template.core.designsystem.component.TemplateEmptyState
import app.template.core.designsystem.component.TemplateLoadingIndicator
import app.template.core.designsystem.component.TemplateOutlinedButton
import app.template.core.designsystem.theme.TemplateSpacing
import app.template.feature.posts.presentation.R
import app.template.feature.posts.presentation.ui.PostsUiState
import app.template.feature.posts.presentation.ui.model.PostUiModel

@Composable
internal fun PostsContent(
    state: PostsUiState.Success,
    onLoadMoreClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    if (state.posts.isEmpty()) {
        Box(
            modifier = modifier.padding(TemplateSpacing.large),
            contentAlignment = Alignment.Center,
        ) {
            TemplateEmptyState(
                headlineContent = {
                    Text(stringResource(R.string.feature_posts_presentation_empty_title))
                },
                supportingContent = {
                    Text(stringResource(R.string.feature_posts_presentation_empty_message))
                },
            )
        }
        return
    }

    LazyColumn(
        modifier = modifier,
        contentPadding = PaddingValues(
            start = TemplateSpacing.large,
            end = TemplateSpacing.large,
            bottom = TemplateSpacing.large,
        ),
        verticalArrangement = Arrangement.spacedBy(TemplateSpacing.medium),
    ) {
        items(
            items = state.posts,
            key = PostUiModel::id,
        ) { post ->
            PostCard(
                post = post,
                modifier = Modifier.fillMaxWidth(),
            )
        }
        item {
            PostsFooter(
                state = state,
                onLoadMoreClick = onLoadMoreClick,
                modifier = Modifier.fillMaxWidth(),
            )
        }
    }
}

@Composable
private fun PostsFooter(
    state: PostsUiState.Success,
    onLoadMoreClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val appendErrorMessage = state.appendError?.toMessage()
    when {
        state.isLoadingMore -> {
            Box(
                modifier = modifier.padding(TemplateSpacing.medium),
                contentAlignment = Alignment.Center,
            ) {
                TemplateLoadingIndicator(
                    contentDescription = stringResource(
                        R.string.feature_posts_presentation_loading_more,
                    ),
                )
            }
        }

        appendErrorMessage != null -> {
            Column(
                modifier = modifier.semantics {
                    error(appendErrorMessage)
                },
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(TemplateSpacing.small),
            ) {
                Text(
                    text = appendErrorMessage,
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodyMedium,
                )
                TemplateOutlinedButton(onClick = onLoadMoreClick) {
                    Text(stringResource(R.string.feature_posts_presentation_retry_load_more))
                }
            }
        }

        state.canLoadMore -> {
            TemplateOutlinedButton(
                onClick = onLoadMoreClick,
                modifier = modifier,
            ) {
                Text(stringResource(R.string.feature_posts_presentation_load_more))
            }
        }
    }
}
