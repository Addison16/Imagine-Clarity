const fileInput = document.querySelector("#file");
const fileLabel = document.querySelector("#file-label");
const fileMeta = document.querySelector("#file-meta");
const dropzone = document.querySelector("#dropzone");
const form = document.querySelector("#controls");
const runButton = document.querySelector("#run");
const runLabel = document.querySelector("#run-label");
const statusEl = document.querySelector("#status");
const statusDetail = document.querySelector("#status-detail");
const runtimeChip = document.querySelector("#runtime-chip");
const toolInputs = document.querySelectorAll('input[name="tool"]');
const toolPanels = document.querySelectorAll("[data-tool-panel]");
const steps = document.querySelectorAll(".step");
const beforeImg = document.querySelector("#before");
const afterImg = document.querySelector("#after");
const beforeMeta = document.querySelector("#before-meta");
const afterMeta = document.querySelector("#after-meta");
const beforeEmpty = document.querySelector("#before-empty");
const afterEmpty = document.querySelector("#after-empty");
const inputChip = document.querySelector("#input-chip");
const engineChip = document.querySelector("#engine-chip");
const processing = document.querySelector("#processing");
const processingLabel = document.querySelector("#processing-label");
const outputFormat = document.querySelector("#output-format");
const resultTitle = document.querySelector("#result-title");
const denoise = document.querySelector("#denoise");
const denoiseValue = document.querySelector("#denoise-value");
const upscaleDevice = document.querySelector("#upscale-device");
const cutModeInputs = document.querySelectorAll('input[name="cut_mode"]');
const edgeRefine = document.querySelector("#edge-refine");
const edgeRefineValue = document.querySelector("#edge-refine-value");
const bgModel = document.querySelector("#bg-model");
const bgTolerance = document.querySelector("#bg-tolerance");
const bgToleranceValue = document.querySelector("#bg-tolerance-value");
const backgroundDevice = document.querySelector("#background-device");
const resultActions = document.querySelector("#result-actions");
const resultDownload = document.querySelector("#result-download");
const resultSummary = document.querySelector("#result-summary");
const compareToggle = document.querySelector("#compare-toggle");
const processAnother = document.querySelector("#process-another");
const compareStage = document.querySelector("#compare-stage");
const compareBefore = document.querySelector("#compare-before");
const compareAfter = document.querySelector("#compare-after");
const compareSlider = document.querySelector("#compare-slider");

let selectedFile = null;
let beforeUrl = null;
let afterUrl = null;
let busyTimer = null;
let maxUploadMb = 64;
let compareActive = false;

const formatOptions = Array.from(outputFormat.options).map((option) => ({
  value: option.value,
  text: option.textContent,
}));

const edgeDefaults = {
  preserve: "4",
  balanced: "8",
  strong: "14",
};

const toleranceDefaults = {
  preserve: "24",
  balanced: "34",
  strong: "48",
};

function setStatus(message, state = "ready", detail = "") {
  statusEl.textContent = message;
  statusEl.className = `status-badge ${state}`.trim();
  if (detail) statusDetail.textContent = detail;
}

function setRuntime(message, state = "neutral") {
  runtimeChip.textContent = message;
  runtimeChip.className = `runtime-badge ${state}`.trim();
}

function setStep(index) {
  steps.forEach((step, stepIndex) => {
    step.classList.toggle("active", stepIndex <= index);
  });
}

function setBusyStatus(label) {
  const startedAt = Date.now();
  clearBusyStatus();
  processing.classList.remove("hidden");
  const render = () => {
    const elapsed = Math.floor((Date.now() - startedAt) / 1000);
    const minutes = String(Math.floor(elapsed / 60)).padStart(2, "0");
    const seconds = String(elapsed % 60).padStart(2, "0");
    const message = `${label} ${minutes}:${seconds}`;
    setStatus("Processing...", "busy", "Processing image. Large files may take a little longer.");
    processingLabel.textContent = message;
  };
  render();
  busyTimer = window.setInterval(render, 1000);
}

function clearBusyStatus() {
  if (busyTimer) {
    window.clearInterval(busyTimer);
    busyTimer = null;
  }
  processing.classList.add("hidden");
}

function revoke(url) {
  if (url) URL.revokeObjectURL(url);
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) return "";
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function fileExtension(file) {
  const fromName = file.name.split(".").pop();
  if (fromName && fromName.length <= 5) return fromName.toUpperCase();
  return file.type.replace("image/", "").toUpperCase();
}

function imageSize(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight });
    img.onerror = reject;
    img.src = url;
  });
}

async function loadRuntime() {
  try {
    const response = await fetch("/health", { cache: "no-store" });
    if (!response.ok) throw new Error("health failed");
    const health = await response.json();
    maxUploadMb = health.max_upload_mb || maxUploadMb;
    const runtime = health.runtime || {};
    if (runtime.cuda_available) {
      setRuntime(`GPU: ${runtime.cuda_device || "CUDA"}`, "good");
    } else {
      setRuntime("CPU runtime", "warn");
      document.querySelectorAll(".device-select option[value='cuda']").forEach((option) => {
        option.disabled = true;
      });
      if (upscaleDevice.value === "cuda") upscaleDevice.value = "auto";
      if (backgroundDevice.value === "cuda") backgroundDevice.value = "auto";
    }
  } catch {
    setRuntime("Runtime unknown", "warn");
  }
}

async function setFile(file) {
  if (!file) return;

  if (!file.type.startsWith("image/")) {
    setStatus("Error", "error", "Unsupported file type. Try PNG, JPG, or WEBP.");
    return;
  }

  if (file.size > maxUploadMb * 1024 * 1024) {
    setStatus("Error", "error", `Upload exceeds ${maxUploadMb} MB.`);
    return;
  }

  selectedFile = file;
  revoke(beforeUrl);
  revoke(afterUrl);
  beforeUrl = URL.createObjectURL(file);
  afterUrl = null;
  compareActive = false;

  beforeImg.src = beforeUrl;
  beforeEmpty.classList.add("hidden");
  afterImg.removeAttribute("src");
  afterEmpty.classList.remove("hidden");
  compareStage.classList.add("hidden");
  resultActions.classList.add("hidden");
  engineChip.classList.add("hidden");

  fileLabel.textContent = file.name;
  fileMeta.textContent = "Ready to process";
  inputChip.textContent = fileExtension(file);
  inputChip.classList.remove("hidden");
  runButton.disabled = false;

  try {
    const size = await imageSize(beforeUrl);
    beforeMeta.textContent = `${size.width} x ${size.height} | ${fileExtension(file)} | ${formatBytes(file.size)}`;
    fileMeta.textContent = `${size.width} x ${size.height} | ${formatBytes(file.size)}`;
  } catch {
    beforeMeta.textContent = `${fileExtension(file)} | ${formatBytes(file.size)}`;
  }

  afterMeta.textContent = "No result yet";
  setStep(1);
  setStatus("Ready", "ready", "Image loaded. Choose your settings and start.");
}

function selectedTool() {
  return document.querySelector('input[name="tool"]:checked').value;
}

function selectedCutMode() {
  return document.querySelector('input[name="cut_mode"]:checked')?.value || "balanced";
}

function actionText() {
  return selectedTool() === "remove-background" ? "Remove Background" : "Upscale Image";
}

function syncRunLabel() {
  runLabel.textContent = actionText();
}

function syncToolUi() {
  const tool = selectedTool();
  toolPanels.forEach((panel) => {
    panel.classList.toggle("hidden", panel.dataset.toolPanel !== tool);
  });

  outputFormat.replaceChildren();
  const allowedFormats = tool === "remove-background" ? ["png", "webp"] : ["png", "jpeg", "webp"];
  formatOptions
    .filter((option) => allowedFormats.includes(option.value))
    .forEach((option) => {
      const el = document.createElement("option");
      el.value = option.value;
      el.textContent = option.text;
      outputFormat.appendChild(el);
    });
  outputFormat.value = "png";

  syncRunLabel();
  resultTitle.textContent = tool === "remove-background" ? "Transparent Result" : "Enhanced Result";
  if (!afterUrl) {
    afterMeta.textContent = "No result yet";
  } else {
    clearResultOnly();
  }
  if (selectedFile) {
    setStatus("Ready", "ready", "Settings updated. Start when ready.");
  }
}

function clearResultOnly() {
  revoke(afterUrl);
  afterUrl = null;
  compareActive = false;
  afterImg.removeAttribute("src");
  compareStage.classList.add("hidden");
  afterEmpty.classList.remove("hidden");
  afterMeta.textContent = "No result yet";
  engineChip.classList.add("hidden");
  resultActions.classList.add("hidden");
  compareToggle.textContent = "Compare";
}

function clearWorkspace() {
  selectedFile = null;
  revoke(beforeUrl);
  revoke(afterUrl);
  beforeUrl = null;
  afterUrl = null;
  compareActive = false;
  fileInput.value = "";
  beforeImg.removeAttribute("src");
  afterImg.removeAttribute("src");
  compareStage.classList.add("hidden");
  beforeEmpty.classList.remove("hidden");
  afterEmpty.classList.remove("hidden");
  beforeMeta.textContent = "No image selected";
  afterMeta.textContent = "No result yet";
  fileLabel.textContent = "Drop your image here";
  fileMeta.textContent = "or click to browse";
  inputChip.classList.add("hidden");
  engineChip.classList.add("hidden");
  resultActions.classList.add("hidden");
  runButton.disabled = true;
  compareToggle.textContent = "Compare";
  setStep(0);
  setStatus("Ready", "ready", "Ready for an image.");
}

function updateDenoiseValue() {
  denoiseValue.textContent = Number(denoise.value).toFixed(2);
}

function updateEdgeRefineValue() {
  edgeRefineValue.textContent = edgeRefine.value;
}

function updateBgToleranceValue() {
  bgToleranceValue.textContent = bgTolerance.value;
}

function applyCutPreset() {
  edgeRefine.value = edgeDefaults[selectedCutMode()] || edgeDefaults.balanced;
  bgTolerance.value = toleranceDefaults[selectedCutMode()] || toleranceDefaults.balanced;
  updateEdgeRefineValue();
  updateBgToleranceValue();
  if (selectedFile) {
    clearResultOnly();
    setStatus("Ready", "ready", "Cut strength updated. Start when ready.");
  }
}

function setComparePosition(value) {
  compareStage.style.setProperty("--compare", `${value}%`);
}

function toggleCompare() {
  if (!beforeUrl || !afterUrl) return;
  compareActive = !compareActive;
  if (compareActive) {
    compareBefore.src = beforeUrl;
    compareAfter.src = afterUrl;
    setComparePosition(compareSlider.value);
    compareStage.classList.remove("hidden");
    compareToggle.textContent = "Exit Compare";
  } else {
    compareStage.classList.add("hidden");
    compareToggle.textContent = "Compare";
  }
}

fileInput.addEventListener("change", () => setFile(fileInput.files[0]));

toolInputs.forEach((input) => input.addEventListener("change", syncToolUi));

denoise.addEventListener("input", updateDenoiseValue);
edgeRefine.addEventListener("input", updateEdgeRefineValue);
bgTolerance.addEventListener("input", updateBgToleranceValue);
bgModel.addEventListener("change", () => {
  if (selectedFile) {
    clearResultOnly();
    setStatus("Ready", "ready", "Subject type updated. Start when ready.");
  }
});
[upscaleDevice, backgroundDevice].forEach((select) => {
  select.addEventListener("change", () => {
    if (selectedFile) {
      clearResultOnly();
      setStatus("Ready", "ready", "Processing source updated. Start when ready.");
    }
  });
});
cutModeInputs.forEach((input) => input.addEventListener("change", applyCutPreset));
processAnother.addEventListener("click", clearWorkspace);
compareToggle.addEventListener("click", toggleCompare);
compareSlider.addEventListener("input", () => setComparePosition(compareSlider.value));

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("dragging");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragging");
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("dragging");
  setFile(event.dataTransfer.files[0]);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selectedFile) return;

  runButton.disabled = true;
  resultActions.classList.add("hidden");
  afterEmpty.classList.add("hidden");
  compareStage.classList.add("hidden");
  engineChip.classList.add("hidden");
  compareActive = false;
  compareToggle.textContent = "Compare";
  setStep(2);

  const tool = selectedTool();
  const actionLabel = tool === "remove-background" ? "Removing background" : "Enhancing image";
  setBusyStatus(actionLabel);

  const payload = new FormData(form);
  payload.set("image", selectedFile);
  payload.delete("tool");
  payload.delete("upscale_device");
  payload.delete("background_device");
  payload.set("device", tool === "remove-background" ? backgroundDevice.value : upscaleDevice.value);
  payload.set("face_enhance", document.querySelector("#face").checked ? "true" : "false");
  payload.set("cut_mode", selectedCutMode());
  payload.set("alpha_matting", document.querySelector("#alpha-matting").checked ? "true" : "false");
  payload.set("edge_refine", edgeRefine.value);
  payload.set("background_tolerance", bgTolerance.value);
  payload.set("post_process_mask", document.querySelector("#post-process-mask").checked ? "true" : "false");
  payload.set("preserve_interior", document.querySelector("#preserve-interior").checked ? "true" : "false");
  payload.set("respect_existing_alpha", document.querySelector("#respect-alpha").checked ? "true" : "false");

  try {
    const endpoint = tool === "remove-background" ? "/api/remove-background" : "/api/upscale";
    const response = await fetch(endpoint, {
      method: "POST",
      body: payload,
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.error || `Request failed with ${response.status}`);
    }

    const blob = await response.blob();
    revoke(afterUrl);
    afterUrl = URL.createObjectURL(blob);
    afterImg.src = afterUrl;
    afterEmpty.classList.add("hidden");

    const width = response.headers.get("X-Output-Width");
    const height = response.headers.get("X-Output-Height");
    const engine =
      response.headers.get("X-Upscaler-Engine") || response.headers.get("X-Background-Engine") || "";
    const extension = outputFormat.value.toUpperCase();
    afterMeta.textContent = `${width} x ${height} | ${extension} | ${formatBytes(blob.size)}`;
    resultSummary.textContent = `${width} x ${height} ${extension}`;

    if (engine) {
      engineChip.textContent = engine;
      engineChip.className = `mini-badge ${engine.includes("CUDA") ? "good" : ""}`.trim();
      engineChip.classList.remove("hidden");
    }

    const disposition = response.headers.get("Content-Disposition") || "";
    const filenameMatch = disposition.match(/filename="([^"]+)"/);
    resultDownload.href = afterUrl;
    resultDownload.download = filenameMatch ? filenameMatch[1] : "result.png";
    resultDownload.textContent = `Download ${extension}`;
    resultActions.classList.remove("hidden");
    setStatus("Complete", "complete", "Done. Your image is ready to download.");
  } catch (error) {
    afterEmpty.classList.remove("hidden");
    setStep(selectedFile ? 1 : 0);
    setStatus("Error", "error", error.message || "Something went wrong while processing the image.");
  } finally {
    clearBusyStatus();
    runButton.disabled = false;
    syncRunLabel();
  }
});

updateDenoiseValue();
updateEdgeRefineValue();
updateBgToleranceValue();
setComparePosition(compareSlider.value);
syncToolUi();
loadRuntime();
