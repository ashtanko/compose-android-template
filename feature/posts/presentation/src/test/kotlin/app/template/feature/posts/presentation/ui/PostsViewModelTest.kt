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

import app.template.feature.posts.domain.model.Post
import app.template.feature.posts.domain.model.PostsPage
import app.template.feature.posts.domain.repository.PostsRepository
import app.template.feature.posts.domain.result.DomainResult
import app.template.feature.posts.domain.result.PostsFailure
import app.template.feature.posts.domain.usecase.GetPostsPageUseCase
import app.template.feature.posts.presentation.ui.model.toUiModel
import kotlinx.collections.immutable.persistentListOf
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

@OptIn(ExperimentalCoroutinesApi::class)
internal class PostsViewModelTest {

    private val dispatcher = StandardTestDispatcher()

    @BeforeEach
    internal fun setUp() {
        Dispatchers.setMain(dispatcher)
    }

    @AfterEach
    internal fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    internal fun `start loads first page and exposes success`() = runTest(dispatcher) {
        val repository = FakePostsRepository(
            DomainResult.Success(firstPage),
        )
        val viewModel = PostsViewModel(GetPostsPageUseCase(repository))

        viewModel.onStart()
        assertThat(viewModel.state.value).isEqualTo(PostsUiState.Loading)
        runCurrent()

        assertThat(viewModel.state.value).isEqualTo(
            PostsUiState.Success(
                posts = persistentListOf(firstPost.toUiModel()),
                canLoadMore = true,
            ),
        )
        assertThat(repository.requestedPages).containsExactly(1)
    }

    @Test
    internal fun `start is idempotent`() = runTest(dispatcher) {
        val repository = FakePostsRepository(DomainResult.Success(firstPage))
        val viewModel = PostsViewModel(GetPostsPageUseCase(repository))

        viewModel.onStart()
        viewModel.onStart()
        runCurrent()

        assertThat(repository.requestedPages).containsExactly(1)
    }

    @Test
    internal fun `retry replaces error with loaded content`() = runTest(dispatcher) {
        val repository = FakePostsRepository(
            DomainResult.Error(PostsFailure.NetworkUnavailable),
            DomainResult.Success(firstPage),
        )
        val viewModel = PostsViewModel(GetPostsPageUseCase(repository))
        viewModel.onStart()
        runCurrent()

        assertThat(viewModel.state.value).isEqualTo(
            PostsUiState.Error(PostsErrorMessage.NetworkUnavailable),
        )

        viewModel.onRetryClick()
        assertThat(viewModel.state.value).isEqualTo(PostsUiState.Loading)
        runCurrent()

        assertThat(viewModel.state.value).isInstanceOf(PostsUiState.Success::class.java)
        assertThat(repository.requestedPages).containsExactly(1, 1)
    }

    @Test
    internal fun `load more appends posts and updates pagination state`() = runTest(dispatcher) {
        val secondPost = Post(id = 2, title = "Second", body = "Second body")
        val repository = FakePostsRepository(
            DomainResult.Success(firstPage),
            DomainResult.Success(
                PostsPage(
                    posts = listOf(secondPost),
                    nextPage = null,
                ),
            ),
        )
        val viewModel = PostsViewModel(GetPostsPageUseCase(repository))
        viewModel.onStart()
        runCurrent()

        viewModel.onLoadMoreClick()
        assertThat(viewModel.state.value).isEqualTo(
            PostsUiState.Success(
                posts = persistentListOf(firstPost.toUiModel()),
                canLoadMore = true,
                isLoadingMore = true,
            ),
        )
        runCurrent()

        assertThat(viewModel.state.value).isEqualTo(
            PostsUiState.Success(
                posts = persistentListOf(firstPost.toUiModel(), secondPost.toUiModel()),
                canLoadMore = false,
            ),
        )
        assertThat(repository.requestedPages).containsExactly(1, 2)
    }

    @Test
    internal fun `load more failure keeps existing content and exposes append error`() =
        runTest(dispatcher) {
            val repository = FakePostsRepository(
                DomainResult.Success(firstPage),
                DomainResult.Error(PostsFailure.ServiceUnavailable),
            )
            val viewModel = PostsViewModel(GetPostsPageUseCase(repository))
            viewModel.onStart()
            runCurrent()

            viewModel.onLoadMoreClick()
            runCurrent()

            assertThat(viewModel.state.value).isEqualTo(
                PostsUiState.Success(
                    posts = persistentListOf(firstPost.toUiModel()),
                    canLoadMore = true,
                    appendError = PostsErrorMessage.ServiceUnavailable,
                ),
            )
        }

    private class FakePostsRepository(
        vararg results: DomainResult<PostsPage>,
    ) : PostsRepository {
        private val results = ArrayDeque(results.toList())
        internal val requestedPages = mutableListOf<Int>()

        public override suspend fun getPosts(
            page: Int,
            pageSize: Int,
        ): DomainResult<PostsPage> {
            requestedPages += page
            return results.removeFirst()
        }
    }

    private companion object {
        private val firstPost = Post(id = 1, title = "First", body = "First body")
        private val firstPage = PostsPage(
            posts = listOf(firstPost),
            nextPage = 2,
        )
    }
}
