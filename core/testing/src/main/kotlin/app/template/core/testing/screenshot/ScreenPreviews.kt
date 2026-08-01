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

package app.template.core.testing.screenshot

import android.content.res.Configuration
import androidx.compose.ui.tooling.preview.Preview

@Target(AnnotationTarget.ANNOTATION_CLASS, AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.BINARY)
@Preview(name = "compact 400x400", widthDp = 400, heightDp = 400, showBackground = true)
@Preview(name = "compact 400x500", widthDp = 400, heightDp = 500, showBackground = true)
@Preview(name = "compact 400x1000", widthDp = 400, heightDp = 1000, showBackground = true)
@Preview(name = "medium 610x400", widthDp = 610, heightDp = 400, showBackground = true)
@Preview(name = "medium 610x500", widthDp = 610, heightDp = 500, showBackground = true)
@Preview(name = "medium 610x1000", widthDp = 610, heightDp = 1000, showBackground = true)
@Preview(name = "expanded 900x400", widthDp = 900, heightDp = 400, showBackground = true)
@Preview(name = "expanded 900x500", widthDp = 900, heightDp = 500, showBackground = true)
@Preview(name = "expanded 900x1000", widthDp = 900, heightDp = 1000, showBackground = true)
public annotation class ScreenSizePreviews

@Target(AnnotationTarget.ANNOTATION_CLASS, AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.BINARY)
@Preview(
    name = "compact dark",
    widthDp = 400,
    heightDp = 500,
    uiMode = Configuration.UI_MODE_NIGHT_YES,
    showBackground = true,
)
@Preview(
    name = "compact large font",
    widthDp = 400,
    heightDp = 500,
    fontScale = 1.5f,
    showBackground = true,
)
public annotation class ScreenVariantPreviews
