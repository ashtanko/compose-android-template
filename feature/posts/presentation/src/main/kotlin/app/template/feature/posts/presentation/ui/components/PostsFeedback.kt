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

import androidx.compose.foundation.layout.Box
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.error
import androidx.compose.ui.semantics.semantics
import app.template.core.designsystem.component.TemplateButton
import app.template.core.designsystem.component.TemplateEmptyState
import app.template.core.designsystem.component.TemplateLoadingIndicator
import app.template.feature.posts.presentation.R
import app.template.feature.posts.presentation.ui.PostsErrorMessage

@Composable
internal fun LoadingContent(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier,
        contentAlignment = Alignment.Center,
    ) {
        TemplateLoadingIndicator(
            contentDescription = stringResource(R.string.feature_posts_presentation_loading),
        )
    }
}

@Composable
internal fun ErrorContent(
    message: PostsErrorMessage,
    onRetryClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val errorMessage = message.toMessage()
    Box(
        modifier = modifier,
        contentAlignment = Alignment.Center,
    ) {
        TemplateEmptyState(
            headlineContent = {
                Text(stringResource(R.string.feature_posts_presentation_error_title))
            },
            modifier = Modifier.semantics { error(errorMessage) },
            supportingContent = { Text(errorMessage) },
            actionContent = {
                TemplateButton(onClick = onRetryClick) {
                    Text(stringResource(R.string.feature_posts_presentation_retry))
                }
            },
        )
    }
}

@Composable
internal fun PostsErrorMessage.toMessage(): String = when (this) {
    PostsErrorMessage.NetworkUnavailable -> {
        stringResource(R.string.feature_posts_presentation_error_network)
    }

    PostsErrorMessage.ServiceUnavailable -> {
        stringResource(R.string.feature_posts_presentation_error_service)
    }

    PostsErrorMessage.Unexpected -> {
        stringResource(R.string.feature_posts_presentation_error_unexpected)
    }
}
