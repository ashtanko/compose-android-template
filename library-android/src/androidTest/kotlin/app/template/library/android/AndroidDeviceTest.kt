package app.template.library.android

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Test

class AndroidDeviceTest {

    @Test
    fun verifyContext() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        assertNotNull(context)
    }
}
