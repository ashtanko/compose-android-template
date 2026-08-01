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

import app.template.feature.posts.data.model.PostsPageRequest
import app.template.feature.posts.data.remote.api.PostsApi
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import retrofit2.Retrofit
import java.net.HttpURLConnection.HTTP_OK
import java.net.HttpURLConnection.HTTP_UNAVAILABLE

internal class RetrofitPostsRemoteDataSourceIntegrationTest {

    private lateinit var server: MockWebServer
    private lateinit var dataSource: RetrofitPostsRemoteDataSource

    @BeforeEach
    internal fun setUp() {
        server = MockWebServer()
        server.start()
        val json = Json { ignoreUnknownKeys = true }
        val api = Retrofit.Builder()
            .baseUrl(server.url("/"))
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(PostsApi::class.java)
        dataSource = RetrofitPostsRemoteDataSource(api)
    }

    @AfterEach
    internal fun tearDown() {
        server.shutdown()
    }

    @Test
    internal fun `transport parses payload headers and pagination`() = runTest {
        server.enqueue(
            MockResponse()
                .setResponseCode(HTTP_OK)
                .setHeader("Content-Type", "application/json")
                .setHeader("X-Total-Count", "3")
                .setBody(
                    """
                    [
                      {"userId": 9, "id": 1, "title": "First", "body": "Body"},
                      {"userId": 9, "id": 2, "title": "Second", "body": "Body"}
                    ]
                    """.trimIndent(),
                ),
        )

        val result = dataSource.getPosts(PostsPageRequest(page = 1, pageSize = 2))

        assertThat(result.posts.map { it.id }).containsExactly(1, 2)
        assertThat(result.nextPage).isEqualTo(2)
        val request = server.takeRequest()
        assertThat(request.path).isEqualTo("/posts?_page=1&_limit=2")
    }

    @Test
    internal fun `transport exposes non-success HTTP status to repository policy`() {
        server.enqueue(MockResponse().setResponseCode(HTTP_UNAVAILABLE))

        assertThatThrownBy {
            kotlinx.coroutines.test.runTest {
                dataSource.getPosts(PostsPageRequest(page = 1, pageSize = 20))
            }
        }.isInstanceOf(PostsHttpException::class.java)
    }
}
