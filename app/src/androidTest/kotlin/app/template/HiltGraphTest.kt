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

package app.template

import app.template.feature.posts.domain.repository.PostsRepository
import com.google.common.truth.Truth.assertThat
import dagger.hilt.android.testing.HiltAndroidRule
import dagger.hilt.android.testing.HiltAndroidTest
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import javax.inject.Inject

@HiltAndroidTest
public class HiltGraphTest {

    @get:Rule
    public val hiltRule = HiltAndroidRule(this)

    @Inject
    internal lateinit var postsRepository: PostsRepository

    @Before
    public fun injectGraph() {
        hiltRule.inject()
    }

    @Test
    public fun applicationGraphResolvesFeatureRepository() {
        assertThat(postsRepository).isNotNull()
    }
}
