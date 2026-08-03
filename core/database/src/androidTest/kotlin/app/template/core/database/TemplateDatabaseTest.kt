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

package app.template.core.database

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
public class TemplateDatabaseTest {

    private lateinit var database: TemplateDatabase

    @Before
    public fun setUp() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder(
            context,
            TemplateDatabase::class.java,
        ).allowMainThreadQueries().build()
    }

    @After
    public fun tearDown() {
        database.close()
    }

    @Test
    public fun upsertReadAndClearUseTheAndroidSqliteEngine(): Unit = runTest {
        val sample = SampleEntity(id = 7, value = "stored on device")

        database.sampleDao().upsert(sample)
        assertThat(database.sampleDao().findById(sample.id)).isEqualTo(sample)

        database.sampleDao().clear()
        assertThat(database.sampleDao().findById(sample.id)).isNull()
    }
}
