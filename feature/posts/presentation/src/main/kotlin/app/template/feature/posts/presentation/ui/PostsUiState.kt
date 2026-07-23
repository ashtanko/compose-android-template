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

import app.template.feature.posts.presentation.ui.model.PostUiModel
import kotlinx.collections.immutable.ImmutableList

internal sealed interface PostsUiState {
    public data object Loading : PostsUiState

    public data class Success(
        public val posts: ImmutableList<PostUiModel>,
        public val canLoadMore: Boolean,
        public val isLoadingMore: Boolean = false,
        public val appendError: PostsErrorMessage? = null,
    ) : PostsUiState

    public data class Error(
        public val message: PostsErrorMessage,
    ) : PostsUiState
}

internal enum class PostsErrorMessage {
    NetworkUnavailable,
    ServiceUnavailable,
    Unexpected,
}
