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

package app.template.ui.theme

import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

val TemplateTypography = androidx.compose.material3.Typography(
    displayLarge = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 57.sp,
        fontWeight = FontWeight.W400,
        lineHeight = 64.sp,
        letterSpacing = (-0.25).sp,
    ),
    displayMedium = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 45.sp,
        fontWeight = FontWeight.W400,
        lineHeight = 52.sp,
    ),
    displaySmall = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 36.sp,
        fontWeight = FontWeight.W400,
        lineHeight = 44.sp,
    ),
    headlineLarge = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 32.sp,
        fontWeight = FontWeight.W500,
        lineHeight = 40.sp,
    ),
    headlineMedium = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 28.sp,
        fontWeight = FontWeight.W500,
        lineHeight = 36.sp,
    ),
    headlineSmall = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 24.sp,
        fontWeight = FontWeight.W500,
        lineHeight = 32.sp,
    ),
    titleLarge = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 22.sp,
        fontWeight = FontWeight.W400,
        lineHeight = 28.sp,
    ),
    titleMedium = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 16.sp,
        fontWeight = FontWeight.W500,
        lineHeight = 24.sp,
        letterSpacing = 0.15.sp,
    ),
    titleSmall = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 14.sp,
        fontWeight = FontWeight.W500,
        lineHeight = 20.sp,
        letterSpacing = 0.1.sp,
    ),
    labelLarge = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 14.sp,
        fontWeight = FontWeight.W500,
        lineHeight = 20.sp,
        letterSpacing = 0.1.sp,
    ),
    labelMedium = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 12.sp,
        fontWeight = FontWeight.W500,
        lineHeight = 16.sp,
        letterSpacing = 0.5.sp,
    ),
    labelSmall = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 11.sp,
        fontWeight = FontWeight.W500,
        lineHeight = 16.sp,
        letterSpacing = 0.5.sp,
    ),
    bodyLarge = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 16.sp,
        fontWeight = FontWeight.W500,
        lineHeight = 24.sp,
        letterSpacing = 0.5.sp,
    ),
    bodyMedium = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 14.sp,
        fontWeight = FontWeight.W500,
        lineHeight = 20.sp,
        letterSpacing = 0.25.sp,
    ),
    bodySmall = TextStyle(
        fontFamily = LexendDecaFontFamily,
        fontSize = 12.sp,
        fontWeight = FontWeight.W500,
        lineHeight = 16.sp,
        letterSpacing = 0.4.sp,
    ),
)
