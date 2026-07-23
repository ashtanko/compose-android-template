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

package app.template.core.designsystem.component

import android.content.res.Configuration
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import app.template.core.designsystem.theme.TemplateSpacing

@Preview(
    name = "Light theme",
    showBackground = true,
    widthDp = PREVIEW_WIDTH,
)
@Preview(
    name = "Dark theme",
    showBackground = true,
    uiMode = Configuration.UI_MODE_NIGHT_YES,
    widthDp = PREVIEW_WIDTH,
)
private annotation class DesignSystemPreviews

@DesignSystemPreviews
@Composable
private fun TemplateBackgroundPreview() {
    DesignSystemPreviewTheme {
        TemplateBackground(modifier = Modifier.fillMaxWidth()) {
            Text(
                text = "Background content",
                modifier = Modifier.padding(TemplateSpacing.large),
            )
        }
    }
}

@DesignSystemPreviews
@Composable
private fun TemplateButtonPreview() {
    DesignSystemPreviewTheme {
        Column(
            modifier = Modifier.padding(TemplateSpacing.medium),
            verticalArrangement = Arrangement.spacedBy(TemplateSpacing.small),
        ) {
            TemplateButton(onClick = {}) {
                Text("Primary action")
            }
            TemplateButton(
                onClick = {},
                enabled = false,
            ) {
                Text("Disabled action")
            }
        }
    }
}

@DesignSystemPreviews
@Composable
private fun TemplateOutlinedButtonPreview() {
    DesignSystemPreviewTheme {
        Column(
            modifier = Modifier.padding(TemplateSpacing.medium),
            verticalArrangement = Arrangement.spacedBy(TemplateSpacing.small),
        ) {
            TemplateOutlinedButton(onClick = {}) {
                Text("Secondary action")
            }
            TemplateOutlinedButton(
                onClick = {},
                enabled = false,
            ) {
                Text("Disabled action")
            }
        }
    }
}

@DesignSystemPreviews
@Composable
private fun TemplateEmptyStatePreview() {
    DesignSystemPreviewTheme {
        TemplateEmptyState(
            headlineContent = { Text("Nothing here yet") },
            modifier = Modifier
                .fillMaxWidth()
                .padding(TemplateSpacing.large),
            iconContent = { Text("○") },
            supportingContent = { Text("New content will appear here when it is available.") },
            actionContent = {
                TemplateButton(onClick = {}) {
                    Text("Refresh")
                }
            },
        )
    }
}

@DesignSystemPreviews
@Composable
private fun TemplateEmptyStateMinimalPreview() {
    DesignSystemPreviewTheme {
        TemplateEmptyState(
            headlineContent = { Text("No notifications") },
            modifier = Modifier
                .fillMaxWidth()
                .padding(TemplateSpacing.large),
        )
    }
}

@DesignSystemPreviews
@Composable
private fun TemplateLoadingIndicatorPreview() {
    DesignSystemPreviewTheme {
        TemplateLoadingIndicator(
            contentDescription = "Loading preview",
            modifier = Modifier.padding(TemplateSpacing.large),
        )
    }
}

@Composable
private fun DesignSystemPreviewTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) darkColorScheme() else lightColorScheme(),
        content = content,
    )
}

private const val PREVIEW_WIDTH = 360
