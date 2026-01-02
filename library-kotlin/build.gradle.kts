plugins {
    alias(libs.plugins.androidlab.jvm.library)
}

dependencies {

}

tasks {
    withType<Test> {
        useJUnitPlatform()
    }
}
