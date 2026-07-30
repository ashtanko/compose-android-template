"use strict";

const state = {
  step: 0,
  bootstrap: null,
  capabilities: new Set(),
  preset: "standard",
  plan: null,
  token: new URLSearchParams(window.location.search).get("token") || "",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

document.addEventListener("DOMContentLoaded", initialize);

async function initialize() {
  bindNavigation();
  bindForms();
  try {
    state.bootstrap = await request("/api/bootstrap", { method: "GET" });
    $("#output-path").value = state.bootstrap.suggestedOutput;
    state.capabilities = new Set(state.bootstrap.presets.standard);
    renderCapabilities();
    updateSummary();
    updateReview();
  } catch (error) {
    showError(error.message);
  }
}

function bindNavigation() {
  $("#next-button").addEventListener("click", () => showStep(state.step + 1));
  $("#back-button").addEventListener("click", () => showStep(state.step - 1));
  $$("[data-next]").forEach((button) => button.addEventListener("click", () => showStep(state.step + 1)));
  $$("#step-list button").forEach((button) => {
    button.addEventListener("click", () => showStep(Number(button.dataset.step)));
  });
}

function bindForms() {
  ["#project-name", "#package-name", "#plugin-alias", "#author", "#output-path"].forEach((selector) => {
    $(selector).addEventListener("input", configurationChanged);
  });
  $$("input[name=starter]").forEach((input) => input.addEventListener("change", () => {
    syncSelectedCards(".choice-card", "input[name=starter]");
    configurationChanged();
  }));
  $$("input[name=output-mode]").forEach((input) => input.addEventListener("change", () => {
    syncSelectedCards(".radio-row", "input[name=output-mode]");
    const copyMode = selectedValue("output-mode") === "copy";
    $("#output-path-field").hidden = !copyMode;
    $("#force-row").hidden = copyMode;
    configurationChanged();
  }));
  $("#format-output").addEventListener("change", configurationChanged);
  $("#verification").addEventListener("change", configurationChanged);
  $("#capability-search").addEventListener("input", renderCapabilities);
  $$("#preset-list button").forEach((button) => {
    button.addEventListener("click", () => selectPreset(button.dataset.preset));
  });
  $("#preview-plan").addEventListener("click", previewPlan);
  $("#apply-plan").addEventListener("click", applyPlan);
  $("#export-config").addEventListener("click", exportConfig);
  $("#import-config").addEventListener("change", importConfig);
}

function showStep(nextStep) {
  const clamped = Math.max(0, Math.min(5, nextStep));
  if (clamped > state.step && !validateCurrentStep()) return;
  state.step = clamped;
  $$(".step").forEach((panel) => panel.classList.toggle("active", Number(panel.dataset.panel) === state.step));
  $$("#step-list li").forEach((item, index) => {
    item.classList.toggle("active", index === state.step);
    item.classList.toggle("complete", index < state.step);
  });
  $("#back-button").disabled = state.step === 0;
  $("#next-button").hidden = state.step === 5;
  $("#step-indicator").textContent = `${state.step + 1} of 6`;
  if (state.step >= 4) updateReview();
  window.scrollTo({ top: 0, behavior: "smooth" });
  $(".step.active h1")?.focus?.();
}

function validateCurrentStep() {
  if (state.step === 1) {
    const name = $("#project-name");
    const packageName = $("#package-name");
    if (!name.value.trim()) {
      name.reportValidity();
      return false;
    }
    if (!packageName.checkValidity()) {
      packageName.reportValidity();
      return false;
    }
  }
  if (state.step === 2 && selectedValue("output-mode") === "copy" && !$("#output-path").value.trim()) {
    $("#output-path").reportValidity();
    return false;
  }
  return true;
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
      const label = document.createElement("label");
      label.className = `capability-card${state.capabilities.has(capability.id) ? " selected" : ""}`;
      const input = document.createElement("input");
      input.type = "checkbox";
      input.checked = state.capabilities.has(capability.id);
      input.addEventListener("change", () => toggleCapability(capability.id, input.checked));
      const copy = document.createElement("span");
      const title = document.createElement("strong");
      title.textContent = capability.title;
      const description = document.createElement("small");
      description.textContent = capability.description;
      copy.append(title, description);
      label.append(input, copy);
      group.append(label);
    });
    container.append(group);
  });
}

function selectPreset(preset) {
  if (preset !== "custom") {
    state.capabilities = new Set(state.bootstrap.presets[preset]);
  }
  state.preset = preset;
  $$("#preset-list button").forEach((button) => button.classList.toggle("selected", button.dataset.preset === preset));
  renderCapabilities();
  configurationChanged();
}

function toggleCapability(id, enabled) {
  if (enabled) state.capabilities.add(id);
  else state.capabilities.delete(id);
  state.preset = "custom";
  $$("#preset-list button").forEach((button) => button.classList.toggle("selected", button.dataset.preset === "custom"));
  renderCapabilities();
  configurationChanged();
}

function configurationChanged() {
  state.plan = null;
  $("#apply-plan").disabled = true;
  $("#plan-digest").hidden = true;
  updateSummary();
  updateReview();
}

function currentConfig() {
  const copyMode = selectedValue("output-mode") === "copy";
  return {
    schemaVersion: 1,
    identity: {
      packageName: $("#package-name").value.trim(),
      projectName: $("#project-name").value.trim(),
      pluginAlias: $("#plugin-alias").value.trim() || null,
      author: $("#author").value.trim() || null,
    },
    output: {
      mode: copyMode ? "copy" : "inPlace",
      path: copyMode ? $("#output-path").value.trim() : null,
    },
    starter: {
      removeExamples: selectedValue("starter") === "remove",
    },
    capabilities: [...state.capabilities].sort(),
    validation: {
      format: $("#format-output").checked,
      level: $("#verification").value,
    },
  };
}

function updateSummary() {
  $("#summary-name").textContent = $("#project-name").value.trim() || "Untitled project";
  $("#summary-package").textContent = $("#package-name").value.trim() || "Package not set";
  $("#summary-count").textContent = state.capabilities.size;
}

function updateReview() {
  const config = currentConfig();
  $("#identity-review").innerHTML = `
    <dt>Name</dt><dd>${escapeHtml(config.identity.projectName || "—")}</dd>
    <dt>Package</dt><dd><code>${escapeHtml(config.identity.packageName || "—")}</code></dd>
    <dt>Starter</dt><dd>${config.starter.removeExamples ? "Minimal branded screen" : "Example modules retained"}</dd>
    <dt>Output</dt><dd>${config.output.mode === "copy" ? escapeHtml(config.output.path || "—") : "Current repository"}</dd>
  `;
  const review = $("#capability-review");
  review.replaceChildren();
  const selected = state.bootstrap?.capabilities.filter((capability) => state.capabilities.has(capability.id)) || [];
  if (!selected.length) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = "Compose foundations";
    review.append(chip);
  }
  selected.forEach((capability) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    const planned = state.plan?.capabilities.find((item) => item.id === capability.id);
    chip.textContent = planned?.reason
      ? `${capability.title} · ${planned.reason}`
      : capability.title;
    review.append(chip);
  });
}

async function previewPlan() {
  if (!validateAll()) return;
  setBusy($("#preview-plan"), true, "Planning…");
  try {
    const plan = await request("/api/plan", {
      method: "POST",
      body: JSON.stringify({ config: currentConfig() }),
    });
    state.plan = plan;
    state.capabilities = new Set(plan.config.capabilities);
    renderCapabilities();
    updateSummary();
    updateReview();
    const operations = $("#operation-review");
    operations.replaceChildren(...plan.operations.map((operation) => {
      const item = document.createElement("li");
      item.textContent = operation;
      return item;
    }));
    $("#plan-digest").textContent = `Plan ${plan.digest.slice(0, 16)} · ${plan.targetRoot}`;
    $("#plan-digest").hidden = false;
    $("#apply-plan").disabled = false;
    $("#generate-copy").textContent = `${plan.operations.length} operations are validated and ready to apply.`;
    showStep(5);
  } catch (error) {
    showError(error.message);
  } finally {
    setBusy($("#preview-plan"), false, "Preview plan");
  }
}

async function applyPlan() {
  if (!state.plan) {
    showError("Preview the plan before generating the project.");
    return;
  }
  const button = $("#apply-plan");
  const panel = $("#generate-state");
  panel.classList.add("running");
  button.disabled = true;
  setBusy(button, true, "Generating…");
  try {
    const result = await request("/api/apply", {
      method: "POST",
      body: JSON.stringify({
        config: currentConfig(),
        digest: state.plan.digest,
        force: $("#force-in-place").checked,
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
    setBusy(button, false, "Generate project");
    showError(error.message);
  }
}

function validateAll() {
  const name = $("#project-name");
  const packageName = $("#package-name");
  const output = $("#output-path");
  if (!name.value.trim() || !packageName.checkValidity()) {
    showStep(1);
    (name.value.trim() ? packageName : name).reportValidity();
    return false;
  }
  if (selectedValue("output-mode") === "copy" && !output.value.trim()) {
    showStep(2);
    output.reportValidity();
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
  if (config.schemaVersion !== 1 || !config.identity || !config.output) {
    throw new Error("unsupported or incomplete configuration");
  }
  $("#project-name").value = config.identity.projectName || "";
  $("#package-name").value = config.identity.packageName || "";
  $("#plugin-alias").value = config.identity.pluginAlias || "";
  $("#author").value = config.identity.author || "";
  setRadio("starter", config.starter?.removeExamples === false ? "keep" : "remove");
  setRadio("output-mode", config.output.mode === "inPlace" ? "inPlace" : "copy");
  $("#output-path").value = config.output.path || state.bootstrap.suggestedOutput;
  $("#output-path-field").hidden = config.output.mode === "inPlace";
  $("#force-row").hidden = config.output.mode !== "inPlace";
  state.capabilities = new Set(config.capabilities || []);
  state.preset = "custom";
  $("#format-output").checked = Boolean(config.validation?.format);
  $("#verification").value = config.validation?.level || "none";
  syncSelectedCards(".choice-card", "input[name=starter]");
  syncSelectedCards(".radio-row", "input[name=output-mode]");
  selectPreset("custom");
  configurationChanged();
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
  button.textContent = label;
}

function showError(message) {
  const notice = $("#notice");
  notice.textContent = message;
  notice.hidden = false;
  window.setTimeout(() => { notice.hidden = true; }, 7000);
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
