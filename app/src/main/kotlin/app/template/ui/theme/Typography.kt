package app.template.ui.theme

import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.googlefonts.GoogleFont
import dev.shtanko.template.R

val googleFontProvider = GoogleFont.Provider(
    providerAuthority = "com.google.android.gms.fonts",
    providerPackage = "com.google.android.gms",
    certificates = R.array.com_google_android_gms_fonts_certs,
)
val LexendDecaFont = GoogleFont("Lexend Deca")

val LexendDecaFontFamily = FontFamily(
    androidx.compose.ui.text.googlefonts.Font(
        googleFont = LexendDecaFont,
        fontProvider = googleFontProvider,
    ),
)
