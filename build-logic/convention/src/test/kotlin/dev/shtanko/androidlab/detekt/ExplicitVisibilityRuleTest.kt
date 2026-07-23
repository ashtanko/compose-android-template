package dev.shtanko.androidlab.detekt

import io.gitlab.arturbosch.detekt.test.TestConfig
import io.gitlab.arturbosch.detekt.test.lint
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

internal class ExplicitVisibilityRuleTest {

    @Test
    internal fun `reports implicit visibility for eligible declarations`() {
        val code = """
            class Example(val value: Int) {
                val label = "example"

                fun execute() = Unit
            }

            val topLevelValue = 1

            fun topLevelFunction() = Unit
        """.trimIndent()

        val findings = rule().lint(code)

        assertEquals(6, findings.size)
    }

    @Test
    internal fun `accepts all supported explicit visibility modifiers`() {
        val code = """
            internal open class Example(public val value: Int) {
                private val label = "example"

                protected fun protectedFunction() = Unit
                internal fun internalFunction() = Unit
                public fun publicFunction() = Unit
            }
        """.trimIndent()

        assertTrue(rule().lint(code).isEmpty())
    }

    @Test
    internal fun `ignores local declarations and non-property constructor parameters`() {
        val code = """
            internal class Example internal constructor(value: Int) {
                private fun execute() {
                    val localValue = value

                    fun localFunction() = localValue

                    class LocalClass(val property: Int)
                }
            }

            internal enum class Direction {
                NORTH,
            }
        """.trimIndent()

        assertTrue(rule().lint(code).isEmpty())
    }

    private fun rule(): ExplicitVisibility = ExplicitVisibility(
        TestConfig("active" to true),
    )
}
