.PHONY: check run test lines md default jacoco spotless kover diktat cloc jar repo screenshot robo

# Run detekt + ktlint
check:
	./gradlew detekt --profile --daemon

ktlint:
	./gradlew ktlintCheck

# Run spotless, more info: https://github.com/diffplug/spotless
spotless:
	./gradlew spotlessApply spotlessCheck spotlessKotlin

# Copy jacoco report
jacoco:
	cp -r build/reports/jacoco/test/html jacocoReport

# Run code style check + update the README.md file in accordance with the detekt report
default:
	./gradlew build && ./gradlew test && ./gradlew lint && ./gradlew detekt && ./gradlew updateDebugScreenshotTest && ./gradlew validateDebugScreenshotTest

# Build the project
run:
	./gradlew build

# Run tests
test:
	./gradlew test

# Print Kotlin lines count
lines:
	find . -name '*.kt' | xargs wc -l

cloc:
	cloc --include-lang=kotlin src/main

kover:
	./gradlew koverHtmlReport

diktat:
	./gradlew diktatCheck

jar:
	./gradlew shadowJar && mv ./build/libs/*.jar config/

repo:
	./gradlew detektReportToMdTask

screenshot:
	./gradlew updateDebugScreenshotTest && ./gradlew validateDebugScreenshotTest

robo:
	 ./gradlew clearRoborazziDebug && ./gradlew recordRoborazziDebug && ./gradlew compareRoborazziDebug && ./gradlew verifyRoborazziDebug

.DEFAULT_GOAL := default
