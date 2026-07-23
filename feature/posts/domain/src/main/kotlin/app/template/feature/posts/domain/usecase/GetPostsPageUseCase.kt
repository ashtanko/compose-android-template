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

import app.template.feature.posts.domain.model.PostsPage
import app.template.feature.posts.domain.repository.PostsRepository
import app.template.feature.posts.domain.result.DomainResult
import app.template.feature.posts.domain.result.PostsFailure

private const val DEFAULT_POSTS_PAGE_SIZE = 20

public class GetPostsPageUseCase(
    private val repository: PostsRepository,
    private val pageSize: Int = DEFAULT_POSTS_PAGE_SIZE,
) {
    init {
        require(pageSize > 0) { "Page size must be greater than zero." }
    }

    public suspend operator fun invoke(page: Int): DomainResult<PostsPage> =
        if (page < 1) {
            DomainResult.Error(PostsFailure.InvalidRequest)
        } else {
            repository.getPosts(page = page, pageSize = pageSize)
        }
}
