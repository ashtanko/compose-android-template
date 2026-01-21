package app.template.library.android

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.CsvSource

class MathValidatorTest {

    @ParameterizedTest(name = "{0} + {1} should equal {2}")
    @CsvSource(
        "1, 1, 2",
        "5, 5, 10",
        "10, -2, 8",
    )
    fun `test addition variations`(first: Int, second: Int, expected: Int) {
        assertEquals(expected, first + second)
    }
}
