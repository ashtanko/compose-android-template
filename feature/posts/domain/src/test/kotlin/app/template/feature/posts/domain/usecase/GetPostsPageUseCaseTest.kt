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

package app.template.feature.posts.domain.usecase

import app.template.feature.posts.domain.model.Post
import app.template.feature.posts.domain.model.PostsPage
import app.template.feature.posts.domain.repository.PostsRepository
import app.template.feature.posts.domain.result.DomainResult
import app.template.feature.posts.domain.result.PostsFailure
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

internal class GetPostsPageUseCaseTest {

    private val expectedPage = PostsPage(
        posts = listOf(Post(id = 1, title = "Title", body = "Body")),
        nextPage = 2,
    )

    @Test
    internal fun `valid page delegates to repository with configured page size`() =
        kotlinx.coroutines.test.runTest {
            val repository = FakePostsRepository(DomainResult.Success(expectedPage))
            val useCase = GetPostsPageUseCase(repository = repository, pageSize = 10)

            val result = useCase(page = 3)

            assertThat(result).isEqualTo(DomainResult.Success(expectedPage))
            assertThat(repository.requestedPage).isEqualTo(3)
            assertThat(repository.requestedPageSize).isEqualTo(10)
        }

    @Test
    internal fun `invalid page returns domain failure without calling repository`() =
        kotlinx.coroutines.test.runTest {
            val repository = FakePostsRepository(DomainResult.Success(expectedPage))
            val useCase = GetPostsPageUseCase(repository)

            val result = useCase(page = 0)

            assertThat(result).isEqualTo(DomainResult.Error(PostsFailure.InvalidRequest))
            assertThat(repository.requestedPage).isNull()
        }

    private class FakePostsRepository(
        private val result: DomainResult<PostsPage>,
    ) : PostsRepository {
        internal var requestedPage: Int? = null
            private set
        internal var requestedPageSize: Int? = null
            private set

        public override suspend fun getPosts(
            page: Int,
            pageSize: Int,
        ): DomainResult<PostsPage> {
            requestedPage = page
            requestedPageSize = pageSize
            return result
        }
    }
}
