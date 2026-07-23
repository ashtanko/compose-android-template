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

package app.template.feature.posts.domain.result

public sealed interface DomainResult<out T> {
    public data class Success<T>(
        public val data: T,
    ) : DomainResult<T>

    public data class Error(
        public val failure: PostsFailure,
    ) : DomainResult<Nothing>
}

public sealed interface PostsFailure {
    public data object InvalidRequest : PostsFailure

    public data object NetworkUnavailable : PostsFailure

    public data object ServiceUnavailable : PostsFailure

    public data object Unexpected : PostsFailure
}
