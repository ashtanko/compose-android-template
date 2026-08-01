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

package app.template.feature.posts.data.local

import app.template.feature.posts.data.model.PostsDataPage
import app.template.feature.posts.data.model.PostsPageRequest
import app.template.feature.posts.data.remote.dto.PostDto
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

internal class InMemoryPostsLocalDataSourceTest {

    @Test
    internal fun `saved pages are isolated by request and replace the same request`() = runTest {
        val source = InMemoryPostsLocalDataSource()
        val firstRequest = PostsPageRequest(page = 1, pageSize = 20)
        val secondRequest = PostsPageRequest(page = 2, pageSize = 20)
        val firstPage = page(id = 1)
        val replacement = page(id = 2)

        assertThat(source.getPosts(firstRequest)).isNull()

        source.savePosts(firstRequest, firstPage)
        source.savePosts(secondRequest, page(id = 3))
        source.savePosts(firstRequest, replacement)

        assertThat(source.getPosts(firstRequest)).isEqualTo(replacement)
        assertThat(source.getPosts(secondRequest)?.posts?.single()?.id).isEqualTo(3)
    }

    private fun page(id: Int): PostsDataPage = PostsDataPage(
        posts = listOf(
            PostDto(
                userId = 1,
                id = id,
                title = "Title $id",
                body = "Body $id",
            ),
        ),
        nextPage = null,
    )
}
