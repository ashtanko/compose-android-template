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
import app.template.feature.posts.data.mapper.toDomain
import app.template.feature.posts.data.model.PostsPageRequest
import app.template.feature.posts.data.remote.PostsHttpException
import app.template.feature.posts.data.remote.PostsPayloadException
import app.template.feature.posts.data.remote.PostsRemoteDataSource
import app.template.feature.posts.domain.model.PostsPage
import app.template.feature.posts.domain.repository.PostsRepository
import app.template.feature.posts.domain.result.DomainResult
import app.template.feature.posts.domain.result.PostsFailure
import kotlinx.serialization.SerializationException
import java.io.IOException
import java.util.concurrent.CancellationException
import javax.inject.Inject

internal class PostsRepositoryImpl @Inject constructor(
    private val remoteDataSource: PostsRemoteDataSource,
    private val localDataSource: PostsLocalDataSource,
) : PostsRepository {

    public override suspend fun getPosts(
        page: Int,
        pageSize: Int,
    ): DomainResult<PostsPage> {
        val request = PostsPageRequest(page = page, pageSize = pageSize)
        return try {
            val remotePage = remoteDataSource.getPosts(request)
            localDataSource.savePosts(request = request, page = remotePage)
            DomainResult.Success(remotePage.toDomain())
        } catch (exception: CancellationException) {
            throw exception
        } catch (_: IOException) {
            cachedPageOrError(request, PostsFailure.NetworkUnavailable)
        } catch (_: PostsHttpException) {
            cachedPageOrError(request, PostsFailure.ServiceUnavailable)
        } catch (_: SerializationException) {
            cachedPageOrError(request, PostsFailure.Unexpected)
        } catch (_: PostsPayloadException) {
            cachedPageOrError(request, PostsFailure.Unexpected)
        } catch (_: Exception) {
            cachedPageOrError(request, PostsFailure.Unexpected)
        }
    }

    private suspend fun cachedPageOrError(
        request: PostsPageRequest,
        failure: PostsFailure,
    ): DomainResult<PostsPage> {
        val cachedPage = localDataSource.getPosts(request)
        return if (cachedPage == null) {
            DomainResult.Error(failure)
        } else {
            DomainResult.Success(cachedPage.toDomain())
        }
    }
}
