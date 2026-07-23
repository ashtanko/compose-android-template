package dev.shtanko.androidlab

import com.android.build.api.dsl.CommonExtension
import com.android.build.api.dsl.ManagedVirtualDevice
import org.gradle.kotlin.dsl.get
import org.gradle.kotlin.dsl.invoke

/**
 * Configure project for Gradle managed devices
 */
internal fun configureGradleManagedDevices(
    commonExtension: CommonExtension,
) {
    val pixel4 = DeviceConfig("Pixel 4", API_LEVEL_30, "aosp-atd")
    val pixel6 = DeviceConfig("Pixel 6", API_LEVEL_31, "aosp")
    val pixelC = DeviceConfig("Pixel C", API_LEVEL_30, "aosp-atd")

    val allDevices = listOf(pixel4, pixel6, pixelC)
    val ciDevices = listOf(pixel4, pixelC)

    commonExtension.testOptions.apply {
        @Suppress("UnstableApiUsage")
        managedDevices {
            allDevices {
                allDevices.forEach { deviceConfig ->
                    maybeCreate(deviceConfig.taskName, ManagedVirtualDevice::class.java).apply {
                        device = deviceConfig.device
                        apiLevel = deviceConfig.apiLevel
                        systemImageSource = deviceConfig.systemImageSource
                    }
                }
            }
            groups {
                maybeCreate("ci").apply {
                    ciDevices.forEach { deviceConfig ->
                        targetDevices.add(localDevices[deviceConfig.taskName])
                    }
                }
            }
        }
    }
}

private const val API_LEVEL_30 = 30
private const val API_LEVEL_31 = 31

private data class DeviceConfig(
    val device: String,
    val apiLevel: Int,
    val systemImageSource: String,
) {
    val taskName = buildString {
        append(device.lowercase().replace(" ", ""))
        append("api")
        append(apiLevel.toString())
        append(systemImageSource.replace("-", ""))
    }
}
