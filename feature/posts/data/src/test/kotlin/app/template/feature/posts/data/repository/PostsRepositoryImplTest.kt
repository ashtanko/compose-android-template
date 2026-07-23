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

package app.template.feature.posts.data.repository

import app.template.feature.posts.data.local.PostsLocalDataSource
import app.template.feature.posts.data.model.PostsDataPage
import app.template.feature.posts.data.model.PostsPageRequest
import app.template.feature.posts.data.remote.PostsHttpException
import app.template.feature.posts.data.remote.PostsRemoteDataSource
import app.template.feature.posts.data.remote.dto.PostDto
import app.template.feature.posts.domain.model.Post
import app.template.feature.posts.domain.model.PostsPage
import app.template.feature.posts.domain.result.DomainResult
import app.template.feature.posts.domain.result.PostsFailure
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException
import java.util.concurrent.CancellationException

internal class PostsRepositoryImplTest {

    private val request = PostsPageRequest(page = 1, pageSize = 20)
    private val dataPage = PostsDataPage(
        posts = listOf(
            PostDto(
                userId = 2,
                id = 11,
                title = "Title",
                body = "Body",
            ),
        ),
        nextPage = 2,
    )
    private val domainPage = PostsPage(
        posts = listOf(Post(id = 11, title = "Title", body = "Body")),
        nextPage = 2,
    )

    @Test
    internal fun `successful remote response is cached and mapped`() = runTest {
        val localDataSource = FakePostsLocalDataSource()
        val repository = PostsRepositoryImpl(
            remoteDataSource = FakePostsRemoteDataSource { dataPage },
            localDataSource = localDataSource,
        )

        val result = repository.getPosts(page = request.page, pageSize = request.pageSize)

        assertThat(result).isEqualTo(DomainResult.Success(domainPage))
        assertThat(localDataSource.pages[request]).isEqualTo(dataPage)
    }

    @Test
    internal fun `network failure returns cached page when one exists`() = runTest {
        val localDataSource = FakePostsLocalDataSource(
            pages = mutableMapOf(request to dataPage),
        )
        val repository = PostsRepositoryImpl(
            remoteDataSource = FakePostsRemoteDataSource { throw IOException("Offline") },
            localDataSource = localDataSource,
        )

        val result = repository.getPosts(page = request.page, pageSize = request.pageSize)

        assertThat(result).isEqualTo(DomainResult.Success(domainPage))
    }

    @Test
    internal fun `network failure without cache returns domain failure`() = runTest {
        val repository = PostsRepositoryImpl(
            remoteDataSource = FakePostsRemoteDataSource { throw IOException("Offline") },
            localDataSource = FakePostsLocalDataSource(),
        )

        val result = repository.getPosts(page = request.page, pageSize = request.pageSize)

        assertThat(result).isEqualTo(DomainResult.Error(PostsFailure.NetworkUnavailable))
    }

    @Test
    internal fun `HTTP failure without cache returns service failure`() = runTest {
        val repository = PostsRepositoryImpl(
            remoteDataSource = FakePostsRemoteDataSource { throw PostsHttpException(503) },
            localDataSource = FakePostsLocalDataSource(),
        )

        val result = repository.getPosts(page = request.page, pageSize = request.pageSize)

        assertThat(result).isEqualTo(DomainResult.Error(PostsFailure.ServiceUnavailable))
    }

    @Test
    internal fun `cancellation is rethrown`() = runTest {
        val cancellation = CancellationException("Cancelled")
        val repository = PostsRepositoryImpl(
            remoteDataSource = FakePostsRemoteDataSource { throw cancellation },
            localDataSource = FakePostsLocalDataSource(),
        )

        val thrown = try {
            repository.getPosts(page = request.page, pageSize = request.pageSize)
            null
        } catch (exception: CancellationException) {
            exception
        }

        assertThat(thrown).isSameAs(cancellation)
    }

    private class FakePostsRemoteDataSource(
        private val getPosts: suspend () -> PostsDataPage,
    ) : PostsRemoteDataSource {
        public override suspend fun getPosts(request: PostsPageRequest): PostsDataPage = getPosts()
    }

    private class FakePostsLocalDataSource(
        internal val pages: MutableMap<PostsPageRequest, PostsDataPage> = mutableMapOf(),
    ) : PostsLocalDataSource {
        public override suspend fun getPosts(request: PostsPageRequest): PostsDataPage? =
            pages[request]

        public override suspend fun savePosts(
            request: PostsPageRequest,
            page: PostsDataPage,
        ) {
            pages[request] = page
        }
    }
}
