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

package app.template.feature.posts.data.remote

import app.template.feature.posts.data.model.PostsDataPage
import app.template.feature.posts.data.model.PostsPageRequest
import app.template.feature.posts.data.remote.api.PostsApi
import javax.inject.Inject

internal interface PostsRemoteDataSource {
    public suspend fun getPosts(request: PostsPageRequest): PostsDataPage
}

internal class RetrofitPostsRemoteDataSource @Inject constructor(
    private val api: PostsApi,
) : PostsRemoteDataSource {

    public override suspend fun getPosts(request: PostsPageRequest): PostsDataPage {
        val response = api.getPosts(
            page = request.page,
            pageSize = request.pageSize,
        )
        if (!response.isSuccessful) {
            throw PostsHttpException(response.code())
        }

        val posts = response.body() ?: throw PostsPayloadException()
        val totalCount = response.headers()[TOTAL_COUNT_HEADER]?.toIntOrNull()
        val hasNextPage = totalCount?.let { request.page * request.pageSize < it }
            ?: (posts.size == request.pageSize)

        return PostsDataPage(
            posts = posts,
            nextPage = if (hasNextPage) request.page + 1 else null,
        )
    }

    private companion object {
        private const val TOTAL_COUNT_HEADER = "X-Total-Count"
    }
}

internal class PostsHttpException(
    private val statusCode: Int,
) : Exception("Posts request failed with HTTP $statusCode.")

internal class PostsPayloadException : Exception("Posts response body was empty.")
