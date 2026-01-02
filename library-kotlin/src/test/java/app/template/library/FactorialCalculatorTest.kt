/*
 * Designed and developed by 2022 ashtanko (Oleksii Shtanko)
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

package app.template.library

import app.template.library.FactorialCalculator.computeFactorial
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

/**
 * Example local unit test, which will execute on the development machine (host).
 *
 * See [testing documentation](http://d.android.com/tools/testing).
 */
class FactorialCalculatorTest {

    @Test
    fun `compute factorial with negative, should throw raise exception`() {
        assertThrows(Exception::class.java) {
            computeFactorial(-1)
        }
    }

    @Test
    fun `compute factorial for zero, should equal 1`() {
        assertThat(computeFactorial(0)).isEqualTo(1)
    }

    @Test
    fun `compute factorial for five, should equal 120`() {
        assertThat(computeFactorial(5)).isEqualTo(120)
    }
}
