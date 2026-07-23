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

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import app.template.feature.posts.domain.model.PostsPage
import app.template.feature.posts.domain.result.DomainResult
import app.template.feature.posts.domain.result.PostsFailure
import app.template.feature.posts.domain.usecase.GetPostsPageUseCase
import app.template.feature.posts.presentation.ui.model.toUiModel
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.collections.immutable.toImmutableList
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
internal class PostsViewModel @Inject internal constructor(
    private val getPostsPage: GetPostsPageUseCase,
) : ViewModel() {

    private val mutableState = MutableStateFlow<PostsUiState>(PostsUiState.Loading)
    internal val state: StateFlow<PostsUiState> = mutableState.asStateFlow()

    private var hasStarted = false
    private var nextPage: Int? = FIRST_PAGE
    private var loadJob: Job? = null

    internal fun onStart() {
        if (hasStarted) return

        hasStarted = true
        loadPage(page = FIRST_PAGE, replaceContent = true)
    }

    internal fun onRetryClick() {
        nextPage = FIRST_PAGE
        loadPage(page = FIRST_PAGE, replaceContent = true)
    }

    internal fun onLoadMoreClick() {
        val page = nextPage ?: return
        val currentState = state.value as? PostsUiState.Success ?: return
        if (currentState.isLoadingMore) return

        loadPage(page = page, replaceContent = false)
    }

    private fun loadPage(
        page: Int,
        replaceContent: Boolean,
    ) {
        if (loadJob?.isActive == true) return

        mutableState.update { currentState ->
            if (replaceContent) {
                PostsUiState.Loading
            } else {
                (currentState as? PostsUiState.Success)?.copy(
                    isLoadingMore = true,
                    appendError = null,
                ) ?: currentState
            }
        }

        loadJob = viewModelScope.launch {
            when (val result = getPostsPage(page)) {
                is DomainResult.Success -> showPage(
                    page = result.data,
                    replaceContent = replaceContent,
                )

                is DomainResult.Error -> showError(
                    failure = result.failure,
                    replaceContent = replaceContent,
                )
            }
        }
    }

    private fun showPage(
        page: PostsPage,
        replaceContent: Boolean,
    ) {
        val loadedPosts = page.posts.map { it.toUiModel() }
        nextPage = page.nextPage
        mutableState.update { currentState ->
            val posts = if (replaceContent) {
                loadedPosts
            } else {
                val existingPosts = (currentState as? PostsUiState.Success)?.posts.orEmpty()
                existingPosts + loadedPosts
            }
            PostsUiState.Success(
                posts = posts.toImmutableList(),
                canLoadMore = page.nextPage != null,
            )
        }
    }

    private fun showError(
        failure: PostsFailure,
        replaceContent: Boolean,
    ) {
        val message = failure.toUiMessage()
        mutableState.update { currentState ->
            if (replaceContent) {
                PostsUiState.Error(message)
            } else {
                (currentState as? PostsUiState.Success)?.copy(
                    isLoadingMore = false,
                    appendError = message,
                ) ?: PostsUiState.Error(message)
            }
        }
    }

    private companion object {
        private const val FIRST_PAGE = 1
    }
}

private fun PostsFailure.toUiMessage(): PostsErrorMessage = when (this) {
    PostsFailure.NetworkUnavailable -> PostsErrorMessage.NetworkUnavailable
    PostsFailure.ServiceUnavailable -> PostsErrorMessage.ServiceUnavailable
    PostsFailure.InvalidRequest,
    PostsFailure.Unexpected,
    -> PostsErrorMessage.Unexpected
}
