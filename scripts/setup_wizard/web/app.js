"use strict";

const state = {
  step: 0,
  bootstrap: null,
  capabilities: new Set(),
  preset: "standard",
  plan: null,
  projectSettings: {},
  revision: 0,
  identityLinks: {
    applicationId: true,
    displayName: true,
  },
  token: new URLSearchParams(window.location.search).get("token") || "",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

document.addEventListener("DOMContentLoaded", initialize);

async function initialize() {
  renderStepNavigation();
  bindNavigation();
  bindForms();
  setBooting(true);
  try {
    state.bootstrap = await request("/api/bootstrap", { method: "GET" });
    $("#output-path").value = state.bootstrap.suggestedOutput;
    state.capabilities = new Set(state.bootstrap.presets.standard);
    initializeIdentity();
    initializeProjectSettings();
    renderProjectSettings();
    renderConfigurationSurfaces();
    if (state.bootstrap.downloadOnly) {
      $$(".local-output").forEach((element) => { element.hidden = true; });
      $(".output-panel").classList.add("download-only");
      setRadio("output-mode", "archive");
    }
    syncOutputMode();
    syncStarterConstraints();
    renderCapabilities();
    updateSummary();
    updateReview();
    setBooting(false, true);
    updateNavigation();
  } catch (error) {
    setBooting(false, false);
    showError(error.message);
  }
}

function renderStepNavigation() {
  const list = $("#step-list");
  const panels = $$(".step");
  list.replaceChildren(...panels.map((panel, index) => {
    panel.dataset.panel = String(index);
    panel.querySelector("h1")?.setAttribute("tabindex", "-1");
    const item = document.createElement("li");
    const button = document.createElement("button");
    const number = document.createElement("span");
    button.type = "button";
    button.dataset.step = String(index);
    button.disabled = true;
    number.textContent = String(index + 1);
    button.append(number, document.createTextNode(panel.dataset.stepTitle));
    item.append(button);
    return item;
  }));
}

function bindNavigation() {
  $("#next-button").addEventListener("click", () => showStep(state.step + 1));
  $("#back-button").addEventListener("click", () => showStep(state.step - 1));
  $$('[data-next]').forEach((button) => button.addEventListener("click", () => showStep(state.step + 1)));
  $$("#step-list button").forEach((button) => {
    button.addEventListener("click", () => showStep(Number(button.dataset.step)));
  });
}

function bindForms() {
  $("#project-name").addEventListener("input", () => {
    if (state.identityLinks.displayName) $("#display-name").value = $("#project-name").value;
    configurationChanged();
  });
  $("#package-name").addEventListener("input", () => {
    if (state.identityLinks.applicationId) $("#application-id").value = $("#package-name").value;
    configurationChanged();
  });
  $("#application-id").addEventListener("input", () => {
    state.identityLinks.applicationId = false;
    configurationChanged();
  });
  $("#display-name").addEventListener("input", () => {
    state.identityLinks.displayName = false;
    configurationChanged();
  });
  ["#plugin-alias", "#author", "#output-path"].forEach((selector) => {
    $(selector).addEventListener("input", configurationChanged);
  });
  $$("input[name=starter]").forEach((input) => input.addEventListener("change", () => {
    syncSelectedCards(".choice-card", "input[name=starter]");
    syncStarterConstraints();
    configurationChanged();
  }));
  $("#ai-free").addEventListener("change", () => {
    applyAiFreeConstraint();
    renderCapabilities();
    configurationChanged();
  });
  $$("input[name=output-mode]").forEach((input) => input.addEventListener("change", () => {
    syncSelectedCards(".radio-row", "input[name=output-mode]");
    syncOutputMode();
    configurationChanged();
  }));
  $("#format-output").addEventListener("change", configurationChanged);
  $("#verification").addEventListener("change", configurationChanged);
  $("#capability-search").addEventListener("input", renderCapabilities);
  $$("#preset-list button").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.classList.contains("selected")));
    button.addEventListener("click", () => selectPreset(button.dataset.preset));
  });
  $("#preview-plan").addEventListener("click", previewPlan);
  $("#apply-plan").addEventListener("click", applyPlan);
  $("#export-config").addEventListener("click", exportConfig);
  $("#import-config").addEventListener("change", importConfig);
}

function setBooting(booting, ready = false) {
  $(".shell").setAttribute("aria-busy", String(booting));
  const actionSelectors = [
    "#import-config",
    "#export-config",
    "[data-next]",
    "#next-button",
    "#preview-plan",
    "#preset-list button",
  ];
  $$(actionSelectors.join(",")).forEach((control) => { control.disabled = booting || !ready; });
  $$("#step-list button").forEach((button) => { button.disabled = booting || !ready; });
  $(".import-action").setAttribute("aria-disabled", String(booting || !ready));
}

function initializeIdentity() {
  $("#application-id").value = $("#package-name").value;
  $("#display-name").value = $("#project-name").value;
  state.identityLinks.applicationId = true;
  state.identityLinks.displayName = true;
}

function initializeProjectSettings() {
  state.projectSettings = {};
  state.bootstrap.projectSettingDefinitions
    .filter((definition) => definition.section === "projectSettings")
    .forEach((definition) => {
      state.projectSettings[definition.id] = state.bootstrap.projectDefaults[definition.id] ?? "";
    });
}

function renderProjectSettings() {
  const container = $("#project-setting-list");
  const groups = new Map();
  state.bootstrap.projectSettingDefinitions
    .filter((definition) => definition.section === "projectSettings")
    .forEach((definition) => {
      if (!groups.has(definition.category)) groups.set(definition.category, []);
      groups.get(definition.category).push(definition);
    });
  container.replaceChildren(...[...groups].map(([category, definitions]) => {
    const group = document.createElement("section");
    group.className = "setting-group";
    const heading = document.createElement("h2");
    heading.textContent = category;
    group.append(heading);
    const fields = document.createElement("div");
    fields.className = "form-grid";
    definitions.forEach((definition) => fields.append(createProjectSettingField(definition)));
    group.append(fields);
    return group;
  }));
  syncStarterConstraints();
}

function createProjectSettingField(definition) {
  const label = document.createElement("label");
  label.className = "field setting-field";
  label.dataset.setting = definition.id;
  const title = document.createElement("span");
  title.textContent = definition.title;
  const input = document.createElement("input");
  input.id = `project-setting-${definition.id}`;
  input.type = definition.inputType;
  input.value = state.projectSettings[definition.id] ?? "";
  input.readOnly = !definition.editable;
  input.setAttribute("aria-describedby", `${input.id}-help`);
  if (definition.minimum !== null) input.min = String(definition.minimum);
  if (definition.maximum !== null) input.max = String(definition.maximum);
  if (definition.inputType === "number") input.step = "1";
  const help = document.createElement("small");
  help.id = `${input.id}-help`;
  help.textContent = `${definition.description} Source: ${definition.source}.${definition.editable ? "" : " This value is read-only."}`;
  input.addEventListener("input", () => {
    state.projectSettings[definition.id] = input.value;
    configurationChanged();
  });
  label.append(title, input, help);
  return label;
}

function renderConfigurationSurfaces() {
  const container = $("#configuration-surfaces");
  container.replaceChildren(...state.bootstrap.configurationSurfaces.map((surface) => {
    const card = document.createElement("article");
    card.className = "surface-card";
    card.tabIndex = 0;
    const disposition = document.createElement("span");
    disposition.className = `disposition disposition-${surface.disposition}`;
    disposition.textContent = surface.disposition;
    const title = document.createElement("h3");
    title.textContent = surface.title;
    const description = document.createElement("p");
    description.textContent = surface.description;
    const sources = document.createElement("small");
    sources.textContent = surface.sources.join(" · ");
    card.append(disposition, title, description, sources);
    return card;
  }));
}

function showStep(nextStep) {
  if (!state.bootstrap) return;
  const panels = $$(".step");
  const clamped = Math.max(0, Math.min(panels.length - 1, nextStep));
  const generateStep = panels.findIndex((panel) => panel.id === "generate");
  if (clamped === generateStep && !state.plan) {
    showError("Preview a valid plan before continuing to Generate.");
    return;
  }
  if (clamped > state.step && !validateCurrentStep()) return;
  state.step = clamped;
  panels.forEach((panel, index) => panel.classList.toggle("active", index === state.step));
  updateNavigation();
  if (panels[state.step]?.id === "project-settings") renderProjectSettings();
  if (state.step >= panels.findIndex((panel) => panel.dataset.stepTitle === "Review")) updateReview();
  window.scrollTo({ top: 0, behavior: "smooth" });
  panels[state.step]?.querySelector("h1")?.focus();
}

function updateNavigation() {
  const panels = $$(".step");
  const generateStep = panels.findIndex((panel) => panel.id === "generate");
  $$("#step-list li").forEach((item, index) => {
    const button = item.querySelector("button");
    item.classList.toggle("active", index === state.step);
    item.classList.toggle("complete", index < state.step);
    if (index === state.step) button.setAttribute("aria-current", "step");
    else button.removeAttribute("aria-current");
  });
  $("#back-button").disabled = state.step === 0;
  $("#next-button").hidden = state.step === panels.length - 1;
  $("#next-button").disabled = state.step === generateStep - 1 && !state.plan;
  $("#step-indicator").textContent = `${state.step + 1} of ${panels.length}`;
}

function validateCurrentStep() {
  const active = $$(".step")[state.step];
  if (active?.dataset.stepTitle === "Identity") return validateIdentity();
  if (active?.dataset.stepTitle === "Starter") return validateDestination();
  if (active?.id === "project-settings") return validateProjectSettings();
  return true;
}

function validateIdentity() {
  const fields = [$("#project-name"), $("#package-name"), $("#application-id"), $("#display-name")];
  const invalid = fields.find((field) => !field.value.trim() || !field.checkValidity());
  if (invalid) invalid.reportValidity();
  return !invalid;
}

function validateDestination() {
  const output = $("#output-path");
  if (selectedValue("output-mode") === "copy" && !output.value.trim()) {
    output.reportValidity();
    return false;
  }
  return true;
}

function validateProjectSettings() {
  const invalid = $$("#project-setting-list input:not(:disabled)").find((input) => !input.checkValidity());
  if (invalid) invalid.reportValidity();
  return !invalid;
}

function renderCapabilities() {
  if (!state.bootstrap) return;
  const query = $("#capability-search").value.trim().toLowerCase();
  const groups = new Map();
  state.bootstrap.capabilities
    .filter((capability) => `${capability.title} ${capability.description} ${capability.category}`.toLowerCase().includes(query))
    .forEach((capability) => {
      if (!groups.has(capability.category)) groups.set(capability.category, []);
      groups.get(capability.category).push(capability);
    });
  const container = $("#capability-list");
  container.replaceChildren();
  groups.forEach((capabilities, category) => {
    const group = document.createElement("section");
    group.className = "capability-group";
    const heading = document.createElement("h2");
    heading.textContent = category;
    group.append(heading);
    capabilities.forEach((capability) => {
      const disabled = $("#ai-free").checked && capability.id === "generative_ai";
      const label = document.createElement("label");
      label.className = [
        "capability-card",
        state.capabilities.has(capability.id) ? "selected" : "",
        disabled ? "disabled" : "",
      ].filter(Boolean).join(" ");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.checked = state.capabilities.has(capability.id);
      input.disabled = disabled;
      input.addEventListener("change", () => toggleCapability(capability.id, input.checked));
      const copy = document.createElement("span");
      const title = document.createElement("strong");
      title.textContent = capability.title;
      const description = document.createElement("small");
      description.textContent = disabled ? "Excluded by the AI-free project option." : capability.description;
      copy.append(title, description);
      label.append(input, copy);
      group.append(label);
    });
    container.append(group);
  });
}

function selectPreset(preset) {
  if (preset !== "custom") state.capabilities = new Set(state.bootstrap.presets[preset]);
  applyAiFreeConstraint();
  state.preset = preset;
  $$("#preset-list button").forEach((button) => {
    const selected = button.dataset.preset === preset;
    button.classList.toggle("selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  renderCapabilities();
  configurationChanged();
}

function toggleCapability(id, enabled) {
  if ($("#ai-free").checked && id === "generative_ai") return;
  if (enabled) state.capabilities.add(id);
  else state.capabilities.delete(id);
  state.preset = "custom";
  $$("#preset-list button").forEach((button) => {
    const selected = button.dataset.preset === "custom";
    button.classList.toggle("selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  renderCapabilities();
  configurationChanged();
}

function configurationChanged() {
  if (!state.bootstrap) return;
  applyAiFreeConstraint();
  state.revision += 1;
  state.plan = null;
  $("#apply-plan").disabled = true;
  $("#plan-digest").hidden = true;
  $("#generate-state").classList.remove("running", "success");
  $("#generate-title").textContent = "Ready when you are.";
  updateGenerateAction();
  updateSummary();
  updateReview();
  updateNavigation();
  clearError();
}

function currentConfig() {
  const outputMode = selectedValue("output-mode");
  const archiveMode = outputMode === "archive";
  const removeExamples = selectedValue("starter") === "remove";
  const { postsBackendUrl, ...projectSettings } = collectProjectSettings();
  return {
    schemaVersion: 3,
    identity: {
      packageName: $("#package-name").value.trim(),
      projectName: $("#project-name").value.trim(),
      applicationId: $("#application-id").value.trim(),
      displayName: $("#display-name").value.trim(),
      pluginAlias: $("#plugin-alias").value.trim() || null,
      author: $("#author").value.trim() || null,
    },
    output: {
      mode: outputMode,
      path: outputMode === "copy" ? $("#output-path").value.trim() : null,
    },
    starter: {
      removeExamples,
      aiFree: $("#ai-free").checked,
    },
    projectSettings: {
      ...projectSettings,
      ...(removeExamples ? {} : { postsBackendUrl: postsBackendUrl || null }),
    },
    capabilities: [...state.capabilities].sort(),
    validation: {
      format: archiveMode ? false : $("#format-output").checked,
      level: archiveMode ? "none" : $("#verification").value,
    },
  };
}

function collectProjectSettings() {
  const values = {};
  state.bootstrap.projectSettingDefinitions
    .filter((definition) => definition.section === "projectSettings")
    .forEach((definition) => {
      const input = $(`#project-setting-${definition.id}`);
      const rawValue = input?.value ?? state.projectSettings[definition.id] ?? "";
      values[definition.id] = definition.inputType === "number" && rawValue !== ""
        ? Number(rawValue)
        : (rawValue || null);
    });
  return values;
}

function applyAiFreeConstraint() {
  if ($("#ai-free").checked) state.capabilities.delete("generative_ai");
}

function syncStarterConstraints() {
  const removeExamples = selectedValue("starter") === "remove";
  const field = $('[data-setting="postsBackendUrl"]');
  const input = $("#project-setting-postsBackendUrl");
  if (field) field.hidden = removeExamples;
  if (input) input.disabled = removeExamples;
}

function syncOutputMode() {
  const outputMode = selectedValue("output-mode");
  const archiveMode = outputMode === "archive";
  $("#output-path-field").hidden = outputMode !== "copy";
  $("#output-path").required = outputMode === "copy";
  $("#force-row").hidden = outputMode !== "inPlace";
  $("#format-output").disabled = archiveMode;
  $("#verification").disabled = archiveMode;
  if (archiveMode) {
    $("#format-output").checked = false;
    $("#verification").value = "none";
  }
  updateGenerateAction();
}

function updateGenerateAction() {
  const archiveMode = selectedValue("output-mode") === "archive";
  $("#apply-plan").textContent = archiveMode ? "Build & download ZIP" : "Generate project";
  $("#generate-copy").textContent = archiveMode
    ? "Preview the plan, then download your configured Android project."
    : "Preview the plan, then create your configured Android project.";
}

function updateSummary() {
  $("#summary-name").textContent = $("#project-name").value.trim() || "Untitled project";
  $("#summary-package").textContent = $("#package-name").value.trim() || "Package not set";
  $("#summary-count").textContent = state.capabilities.size;
}

function updateReview() {
  if (!state.bootstrap) return;
  const config = currentConfig();
  const outputDescription = {
    archive: "Browser ZIP download",
    copy: escapeHtml(config.output.path || "—"),
    inPlace: "Current repository",
  }[config.output.mode];
  $("#identity-review").innerHTML = `
    <dt>Name</dt><dd>${escapeHtml(config.identity.projectName || "—")}</dd>
    <dt>Package</dt><dd><code>${escapeHtml(config.identity.packageName || "—")}</code></dd>
    <dt>Application ID</dt><dd><code>${escapeHtml(config.identity.applicationId || "—")}</code></dd>
    <dt>Display name</dt><dd>${escapeHtml(config.identity.displayName || "—")}</dd>
    <dt>Starter</dt><dd>${config.starter.removeExamples ? "Minimal branded screen" : "Example modules retained"}</dd>
    <dt>AI tooling</dt><dd>${config.starter.aiFree ? "Excluded" : "Included"}</dd>
    <dt>Output</dt><dd>${outputDescription}</dd>
  `;
  const review = $("#capability-review");
  review.replaceChildren();
  const plannedCapabilities = new Map((state.plan?.capabilities || []).map((item) => [item.id, item]));
  const capabilityIds = state.plan ? [...plannedCapabilities.keys()] : [...state.capabilities];
  if (!capabilityIds.length) appendChip(review, "Compose foundations");
  capabilityIds.sort().forEach((id) => {
    const definition = state.bootstrap.capabilities.find((capability) => capability.id === id);
    const planned = plannedCapabilities.get(id);
    const requested = state.capabilities.has(id);
    const label = `${definition?.title || planned?.title || id}${planned?.reason ? ` · ${planned.reason}` : ""}${requested ? "" : " · added by plan"}`;
    appendChip(review, label);
  });
  const settingsReview = $("#settings-review");
  settingsReview.replaceChildren();
  state.bootstrap.projectSettingDefinitions
    .filter((definition) => definition.section === "projectSettings" && Object.hasOwn(config.projectSettings, definition.id))
    .forEach((definition) => {
      const term = document.createElement("dt");
      const detail = document.createElement("dd");
      term.textContent = definition.title;
      detail.textContent = String(config.projectSettings[definition.id] ?? "—");
      settingsReview.append(term, detail);
    });
}

function appendChip(container, text) {
  const chip = document.createElement("span");
  chip.className = "chip";
  chip.textContent = text;
  container.append(chip);
}

async function previewPlan() {
  if (!validateAll()) return;
  clearError();
  const revision = state.revision;
  const config = currentConfig();
  setBusy($("#preview-plan"), true, "Planning…");
  setPageBusy(true);
  try {
    const plan = await request("/api/plan", {
      method: "POST",
      body: JSON.stringify({ config }),
    });
    if (revision !== state.revision) return;
    state.plan = plan;
    updateReview();
    const operations = $("#operation-review");
    operations.replaceChildren(...plan.operations.map((operation) => {
      const item = document.createElement("li");
      item.textContent = operation;
      return item;
    }));
    const target = plan.targetRoot || plan.archiveName;
    $("#plan-digest").textContent = `Plan ${plan.digest.slice(0, 16)} · ${target}`;
    $("#plan-digest").hidden = false;
    $("#apply-plan").disabled = false;
    $("#generate-copy").textContent = selectedValue("output-mode") === "archive"
      ? `${plan.operations.length} operations are validated and ready to package.`
      : `${plan.operations.length} operations are validated and ready to apply.`;
    showStep($$(".step").findIndex((panel) => panel.id === "generate"));
  } catch (error) {
    if (revision === state.revision) showError(error.message);
  } finally {
    setBusy($("#preview-plan"), false, "Preview plan");
    setPageBusy(false);
  }
}

async function applyPlan() {
  if (!state.plan) {
    showError("Preview the plan before generating the project.");
    return;
  }
  clearError();
  const button = $("#apply-plan");
  const panel = $("#generate-state");
  const archiveMode = selectedValue("output-mode") === "archive";
  const approvedPlan = state.plan;
  const approvedConfig = currentConfig();
  const force = $("#force-in-place").checked;
  panel.classList.add("running");
  setBusy(button, true, archiveMode ? "Building archive…" : "Generating…");
  setPageBusy(true);
  try {
    if (archiveMode) {
      const archive = await requestArchive({ config: approvedConfig, digest: approvedPlan.digest });
      downloadBlob(archive, approvedPlan.archiveName);
      panel.classList.remove("running");
      panel.classList.add("success");
      $("#generate-title").textContent = "Your download is ready.";
      $("#generate-copy").textContent = `${approvedPlan.archiveName} was prepared and downloaded.`;
      $("#plan-digest").textContent = approvedPlan.archiveName;
      button.disabled = false;
      button.textContent = "Download ZIP again";
      return;
    }
    const result = await request("/api/apply", {
      method: "POST",
      body: JSON.stringify({
        config: approvedConfig,
        digest: approvedPlan.digest,
        force,
      }),
    });
    panel.classList.remove("running");
    panel.classList.add("success");
    $("#generate-title").textContent = "Your project is ready.";
    $("#generate-copy").textContent = `${result.message} Location: ${result.targetRoot}`;
    button.textContent = "Completed";
    $("#plan-digest").textContent = result.targetRoot;
  } catch (error) {
    panel.classList.remove("running");
    button.disabled = false;
    setBusy(button, false, archiveMode ? "Build & download ZIP" : "Generate project");
    showError(error.message);
  } finally {
    setPageBusy(false);
  }
}

function validateAll() {
  if (!validateIdentity()) {
    showStep($$(".step").findIndex((panel) => panel.dataset.stepTitle === "Identity"));
    return false;
  }
  if (!validateDestination()) {
    showStep($$(".step").findIndex((panel) => panel.dataset.stepTitle === "Starter"));
    return false;
  }
  if (!validateProjectSettings()) {
    showStep($$(".step").findIndex((panel) => panel.id === "project-settings"));
    return false;
  }
  return true;
}

function exportConfig() {
  const blob = new Blob([`${JSON.stringify(currentConfig(), null, 2)}\n`], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "project-setup.json";
  link.click();
  URL.revokeObjectURL(link.href);
}

async function importConfig(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    clearError();
    const config = JSON.parse(await file.text());
    applyImportedConfig(config);
    await previewPlan();
  } catch (error) {
    showError(`Could not import configuration: ${error.message}`);
  } finally {
    event.target.value = "";
  }
}

function applyImportedConfig(config) {
  if (!state.bootstrap.supportedSchemaVersions.includes(config.schemaVersion) || !config.identity || !config.output) {
    throw new Error("unsupported or incomplete configuration");
  }
  const legacy = config.schemaVersion < 3;
  $("#project-name").value = config.identity.projectName || "";
  $("#package-name").value = config.identity.packageName || "";
  const hasApplicationId = !legacy && typeof config.identity.applicationId === "string" && config.identity.applicationId.trim();
  const hasDisplayName = !legacy && typeof config.identity.displayName === "string" && config.identity.displayName.trim();
  state.identityLinks.applicationId = !hasApplicationId;
  state.identityLinks.displayName = !hasDisplayName;
  $("#application-id").value = hasApplicationId ? config.identity.applicationId : $("#package-name").value;
  $("#display-name").value = hasDisplayName ? config.identity.displayName : $("#project-name").value;
  $("#plugin-alias").value = config.identity.pluginAlias || "";
  $("#author").value = config.identity.author || "";
  setRadio("starter", config.starter?.removeExamples === false ? "keep" : "remove");
  $("#ai-free").checked = Boolean(config.starter?.aiFree);
  const importedOutputMode = ["archive", "copy", "inPlace"].includes(config.output.mode) ? config.output.mode : "copy";
  setRadio("output-mode", state.bootstrap.downloadOnly ? "archive" : importedOutputMode);
  $("#output-path").value = config.output.path || state.bootstrap.suggestedOutput;
  state.capabilities = new Set(config.capabilities || []);
  applyAiFreeConstraint();
  state.preset = "custom";
  state.bootstrap.projectSettingDefinitions
    .filter((definition) => definition.section === "projectSettings")
    .forEach((definition) => {
      state.projectSettings[definition.id] = config.projectSettings?.[definition.id]
        ?? state.bootstrap.projectDefaults[definition.id]
        ?? "";
    });
  renderProjectSettings();
  const archiveMode = selectedValue("output-mode") === "archive";
  $("#format-output").checked = archiveMode ? false : Boolean(config.validation?.format);
  $("#verification").value = archiveMode ? "none" : (config.validation?.level || "none");
  syncSelectedCards(".choice-card", "input[name=starter]");
  syncSelectedCards(".radio-row", "input[name=output-mode]");
  syncOutputMode();
  syncStarterConstraints();
  selectPreset("custom");
}

async function request(path, options) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "X-Setup-Token": state.token,
      ...(options.method === "POST" ? { "Content-Type": "application/json" } : {}),
    },
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
  return payload;
}

async function requestArchive(payload) {
  const response = await fetch("/api/archive", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Setup-Token": state.token,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    let error;
    try {
      error = (await response.json()).error;
    } catch {
      error = null;
    }
    throw new Error(error || `Archive request failed (${response.status})`);
  }
  return response.blob();
}

function downloadBlob(blob, filename) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(link.href), 0);
}

function selectedValue(name) {
  return $(`input[name=${name}]:checked`).value;
}

function setRadio(name, value) {
  const input = $(`input[name=${name}][value="${value}"]`);
  if (input) input.checked = true;
}

function syncSelectedCards(cardSelector, inputSelector) {
  $$(cardSelector).forEach((card) => card.classList.toggle("selected", card.querySelector(inputSelector).checked));
}

function setBusy(button, busy, label) {
  button.disabled = busy;
  button.setAttribute("aria-busy", String(busy));
  button.textContent = label;
}

function setPageBusy(busy) {
  $(".content").setAttribute("aria-busy", String(busy));
}

function showError(message) {
  const notice = $("#notice");
  notice.textContent = message;
  notice.hidden = false;
}

function clearError() {
  const notice = $("#notice");
  notice.textContent = "";
  notice.hidden = true;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[character]));
}
