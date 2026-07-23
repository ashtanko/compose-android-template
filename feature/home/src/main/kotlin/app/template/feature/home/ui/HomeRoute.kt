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

package app.template.feature.home.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.createSavedStateHandle
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
public fun HomeRoute(
    onExploreNavigationClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    HomeRoute(
        onExploreNavigationClick = onExploreNavigationClick,
        viewModel = viewModel {
            HomeViewModel(createSavedStateHandle())
        },
        modifier = modifier,
    )
}

@Composable
internal fun HomeRoute(
    onExploreNavigationClick: () -> Unit,
    viewModel: HomeViewModel,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    HomeScreen(
        state = state,
        onInputChanged = viewModel::onInputChanged,
        onCalculateClick = viewModel::onCalculateClick,
        onExploreNavigationClick = onExploreNavigationClick,
        modifier = modifier,
    )
}
