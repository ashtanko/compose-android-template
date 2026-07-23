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

package app.template.feature.posts.data.mapper

import app.template.feature.posts.data.model.PostsDataPage
import app.template.feature.posts.data.remote.dto.PostDto
import app.template.feature.posts.domain.model.Post
import app.template.feature.posts.domain.model.PostsPage

internal fun PostDto.toDomain(): Post = Post(
    id = id,
    title = title,
    body = body,
)

internal fun PostsDataPage.toDomain(): PostsPage = PostsPage(
    posts = posts.map(PostDto::toDomain),
    nextPage = nextPage,
)
