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

import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.RoomDatabase

@Entity(tableName = "samples")
internal data class SampleEntity(
    @PrimaryKey internal val id: Long,
    internal val value: String,
)

@Dao
internal interface SampleDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    public suspend fun upsert(sample: SampleEntity)

    @Query("SELECT * FROM samples WHERE id = :id")
    public suspend fun findById(id: Long): SampleEntity?

    @Query("DELETE FROM samples")
    public suspend fun clear()
}

@Database(
    entities = [SampleEntity::class],
    version = 1,
    exportSchema = true,
)
internal abstract class TemplateDatabase : RoomDatabase() {
    public abstract fun sampleDao(): SampleDao
}
