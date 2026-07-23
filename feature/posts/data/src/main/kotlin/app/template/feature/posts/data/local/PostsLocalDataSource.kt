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
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import javax.inject.Inject
import javax.inject.Singleton

internal interface PostsLocalDataSource {
    public suspend fun getPosts(request: PostsPageRequest): PostsDataPage?

    public suspend fun savePosts(
        request: PostsPageRequest,
        page: PostsDataPage,
    )
}

@Singleton
internal class InMemoryPostsLocalDataSource @Inject constructor() : PostsLocalDataSource {
    private val mutex = Mutex()
    private val pages = mutableMapOf<PostsPageRequest, PostsDataPage>()

    public override suspend fun getPosts(request: PostsPageRequest): PostsDataPage? =
        mutex.withLock { pages[request] }

    public override suspend fun savePosts(
        request: PostsPageRequest,
        page: PostsDataPage,
    ) {
        mutex.withLock {
            pages[request] = page
        }
    }
}
