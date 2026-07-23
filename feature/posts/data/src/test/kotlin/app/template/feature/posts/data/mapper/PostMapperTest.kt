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

import app.template.feature.posts.data.remote.dto.PostDto
import app.template.feature.posts.domain.model.Post
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

internal class PostMapperTest {

    @Test
    internal fun `DTO maps only feature-owned fields to domain model`() {
        val dto = PostDto(
            userId = 99,
            id = 7,
            title = "A transport title",
            body = "A transport body",
        )

        assertThat(dto.toDomain()).isEqualTo(
            Post(
                id = 7,
                title = "A transport title",
                body = "A transport body",
            ),
        )
    }
}
