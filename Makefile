.PHONY: check run
check:
		./gradlew lint spotlessApply spotlessCheck spotlessKotlin detekt ktlintCheck lint --profile --daemon

run:
		./gradlew build

lint:
		./gradlew lint

.DEFAULT_GOAL := check
