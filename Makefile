GRADLE := ./gradlew
GRADLE_ARGS ?=

.DEFAULT_GOAL := help

.PHONY: \
	help \
	docs-check \
	template-check \
	build \
	install \
	test \
	check \
	verify \
	lint \
	detekt \
	detekt-compose \
	detekt-fix \
	format-check \
	format \
	device-test \
	benchmark \
	screenshot-test \
	screenshot-record \
	roborazzi-test \
	roborazzi-record \
	coverage \
	dependency-guard \
	dependency-guard-baseline \
	baseline-profile \
	tasks \
	gradle-version

help:
	@echo "Usage: make <target> [GRADLE_ARGS=\"...\"]"
	@echo
	@echo "Build and verification:"
	@echo "  docs-check                  Validate documentation links and project facts"
	@echo "  template-check              Validate rename dry run and module generation"
	@echo "  build                       Assemble debug artifacts"
	@echo "  install                     Install the app's debug build"
	@echo "  test                        Run unit tests"
	@echo "  check                       Run routine static checks"
	@echo "  verify                      Assemble debug, test, and run routine checks"
	@echo "  lint                        Run Android lint"
	@echo "  detekt                      Run Detekt in every module"
	@echo "  detekt-compose              Run Compose-specific Detekt rules"
	@echo "  detekt-fix                  Apply safe Detekt auto-corrections"
	@echo "  format-check                Check formatting"
	@echo "  format                      Apply formatting changes"
	@echo
	@echo "Device and visual tests:"
	@echo "  device-test                 Run debug instrumentation tests"
	@echo "  benchmark                   Run benchmarkRelease macrobenchmarks"
	@echo "  screenshot-test             Verify Compose screenshot baselines"
	@echo "  screenshot-record           Update Compose screenshot baselines"
	@echo "  roborazzi-test              Verify Roborazzi baselines"
	@echo "  roborazzi-record            Update Roborazzi baselines"
	@echo
	@echo "Reports and maintenance:"
	@echo "  coverage                    Generate the app Kover HTML report"
	@echo "  dependency-guard            Check dependency baselines"
	@echo "  dependency-guard-baseline   Update the app dependency baseline"
	@echo "  baseline-profile            Generate the app baseline profile"
	@echo "  tasks                       List available Gradle tasks"
	@echo "  gradle-version              Print Gradle, Kotlin, and JVM versions"

docs-check:
	bash scripts/check-docs.sh

template-check:
	bash scripts/check-template-tools.sh

build:
	$(GRADLE) assembleDebug $(GRADLE_ARGS)

install:
	$(GRADLE) :app:installDebug $(GRADLE_ARGS)

test:
	$(GRADLE) test $(GRADLE_ARGS)

check:
	$(GRADLE) lint detekt spotlessCheck dependencyGuard $(GRADLE_ARGS)

verify: docs-check template-check
	$(GRADLE) :build-logic:convention:check assembleDebug test lint detekt spotlessCheck dependencyGuard validateDebugScreenshotTest verifyRoborazziDebug $(GRADLE_ARGS)

lint:
	$(GRADLE) lint $(GRADLE_ARGS)

detekt:
	$(GRADLE) detekt $(GRADLE_ARGS)

detekt-compose:
	$(GRADLE) detektCompose $(GRADLE_ARGS)

detekt-fix:
	$(GRADLE) detektAutoCorrect $(GRADLE_ARGS)

format-check:
	$(GRADLE) spotlessCheck $(GRADLE_ARGS)

format:
	$(GRADLE) spotlessApply $(GRADLE_ARGS)

device-test:
	$(GRADLE) connectedDebugAndroidTest $(GRADLE_ARGS)

benchmark:
	$(GRADLE) :benchmarks:connectedBenchmarkReleaseAndroidTest $(GRADLE_ARGS)

screenshot-test:
	$(GRADLE) validateDebugScreenshotTest $(GRADLE_ARGS)

screenshot-record:
	$(GRADLE) updateDebugScreenshotTest $(GRADLE_ARGS)

roborazzi-test:
	$(GRADLE) verifyRoborazziDebug $(GRADLE_ARGS)

roborazzi-record:
	$(GRADLE) recordRoborazziDebug $(GRADLE_ARGS)

coverage:
	$(GRADLE) :app:koverHtmlReport $(GRADLE_ARGS)

dependency-guard:
	$(GRADLE) dependencyGuard $(GRADLE_ARGS)

dependency-guard-baseline:
	$(GRADLE) :app:dependencyGuardBaseline $(GRADLE_ARGS)

baseline-profile:
	$(GRADLE) :app:generateBaselineProfile $(GRADLE_ARGS)

tasks:
	$(GRADLE) tasks $(GRADLE_ARGS)

gradle-version:
	$(GRADLE) --version
