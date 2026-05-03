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
const presetSelect = document.querySelector("#preset");
const presetNote = document.querySelector("#preset-note");
const toolInputs = document.querySelectorAll('input[name="tool"]');
const scaleInputs = document.querySelectorAll('input[name="scale"]');
const sizingInputs = document.querySelectorAll('input[name="sizing"]');
const sizePanels = document.querySelectorAll("[data-size-panel]");
const toolPanels = document.querySelectorAll("[data-tool-panel]");
const infoTips = document.querySelectorAll(".info-tip");
const infoPanels = document.querySelectorAll(".info-panel");
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
const processingDetail = document.querySelector("#processing-detail");
const progressFill = document.querySelector("#progress-fill");
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
const targetWidthInput = document.querySelector("#target-width");
const targetHeightInput = document.querySelector("#target-height");
const previewBgButtons = document.querySelectorAll("[data-preview-bg]");
const previewStages = document.querySelectorAll(".preview-stage");
const historyList = document.querySelector("#history-list");
const batchResults = document.querySelector("#batch-results");
const refreshHistory = document.querySelector("#refresh-history");
const diagnosticsPanel = document.querySelector("#diagnostics-panel");
const refreshDiagnostics = document.querySelector("#refresh-diagnostics");

let selectedFile = null;
let selectedFiles = [];
let beforeUrl = null;
let afterUrl = null;
let busyTimer = null;
let maxUploadMb = 64;
let maxImageDimension = 16384;
let maxUpscaleFactor = 8;
let selectedImageSize = null;
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

const presets = {
  smart: {
    note: "Smart Auto keeps model detection enabled and chooses safer defaults.",
    tool: null,
    mode: "auto",
    model: "auto",
    cut: "balanced",
    scale: "4",
    sizing: "scale",
    denoise: "0.55",
    alphaMatting: true,
    postProcess: true,
    preserveInterior: true,
    respectAlpha: true,
    format: "png",
  },
  logo: {
    note: "Best for logos, decals, text graphics, and shirt art with hard edges.",
    tool: "remove-background-upscale",
    mode: "conservative",
    model: "logo",
    cut: "preserve",
    scale: "4",
    sizing: "scale",
    denoise: "0.3",
    alphaMatting: false,
    postProcess: true,
    preserveInterior: true,
    respectAlpha: true,
    format: "png",
  },
  photo: {
    note: "Best for natural photos where detail enhancement matters.",
    tool: "upscale",
    mode: "photo",
    model: "accurate",
    cut: "balanced",
    scale: "4",
    sizing: "scale",
    denoise: "0.45",
    alphaMatting: true,
    postProcess: true,
    preserveInterior: true,
    respectAlpha: true,
    format: "png",
  },
  artwork: {
    note: "Best for drawings, illustrations, flat colors, and line art.",
    tool: "upscale",
    mode: "anime",
    model: "anime",
    cut: "balanced",
    scale: "4",
    sizing: "scale",
    denoise: "0.35",
    alphaMatting: false,
    postProcess: true,
    preserveInterior: true,
    respectAlpha: true,
    format: "png",
  },
  product: {
    note: "Best for product images that need a transparent cutout and cleaner output.",
    tool: "remove-background-upscale",
    mode: "photo",
    model: "accurate",
    cut: "balanced",
    scale: "4",
    sizing: "scale",
    denoise: "0.5",
    alphaMatting: true,
    postProcess: true,
    preserveInterior: true,
    respectAlpha: true,
    format: "png",
  },
  print: {
    note: "Best when preparing a larger clean image for print or mockups.",
    tool: "upscale",
    mode: "auto",
    model: "auto",
    cut: "balanced",
    scale: "8",
    sizing: "scale",
    denoise: "0.55",
    alphaMatting: true,
    postProcess: true,
    preserveInterior: true,
    respectAlpha: true,
    format: "png",
  },
  "transparent-sticker": {
    note: "Best for transparent PNG stickers and graphic assets that already have an alpha channel.",
    tool: "remove-background-upscale",
    mode: "conservative",
    model: "logo",
    cut: "preserve",
    scale: "4",
    sizing: "scale",
    denoise: "0.25",
    alphaMatting: false,
    postProcess: false,
    preserveInterior: true,
    respectAlpha: true,
    format: "png",
  },
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

function closeInfoTips(exceptTip = null) {
  infoTips.forEach((tip) => {
    if (tip !== exceptTip) {
      tip.dataset.open = "false";
      tip.setAttribute("aria-expanded", "false");
      const panel = document.getElementById(tip.getAttribute("aria-controls"));
      if (panel) panel.hidden = true;
    }
  });
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
  setProgress(8, "Preparing job...");
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
  setProgress(0, "Large files may take a little longer.");
}

function setProgress(percent, detail = "") {
  progressFill.style.width = `${Math.max(0, Math.min(100, percent))}%`;
  if (detail) processingDetail.textContent = detail;
}

function revoke(url) {
  if (url) URL.revokeObjectURL(url);
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) return "";
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function fileExtension(file) {
  const fromName = file.name.split(".").pop();
  if (fromName && fromName.length <= 5) return fromName.toUpperCase();
  return file.type.replace("image/", "").toUpperCase();
}

function resolutionLimitLabel() {
  return `${maxImageDimension.toLocaleString()} x ${maxImageDimension.toLocaleString()}`;
}

function selectedScale() {
  return Number(document.querySelector('input[name="scale"]:checked')?.value || 1);
}

function selectedSizingMode() {
  return document.querySelector('input[name="sizing"]:checked')?.value || "scale";
}

function setRadioValue(name, value) {
  const input = document.querySelector(`input[name="${name}"][value="${value}"]`);
  if (input) input.checked = true;
}

function setCheckbox(id, checked) {
  const input = document.querySelector(`#${id}`);
  if (input) input.checked = Boolean(checked);
}

function applyPreset(key, fromUser = false) {
  const preset = presets[key] || presets.smart;
  if (preset.tool) setRadioValue("tool", preset.tool);
  setRadioValue("scale", preset.scale);
  setRadioValue("sizing", preset.sizing);
  setRadioValue("cut_mode", preset.cut);
  document.querySelector("#mode").value = preset.mode;
  bgModel.value = preset.model;
  denoise.value = preset.denoise;
  outputFormat.value = preset.format;
  setCheckbox("alpha-matting", preset.alphaMatting);
  setCheckbox("post-process-mask", preset.postProcess);
  setCheckbox("preserve-interior", preset.preserveInterior);
  setCheckbox("respect-alpha", preset.respectAlpha);
  updateDenoiseValue();
  applyCutPreset(false);
  syncToolUi();
  syncSizingUi(key === "print");
  presetNote.textContent = preset.note;
  if (selectedFile && fromUser) {
    clearResultOnly();
    validateResolutionForCurrentSettings("Preset updated. Start when ready.");
  }
}

function applySmartPresetForFile(file, size) {
  const name = file.name.toLowerCase();
  const isLarge = Math.max(size.width, size.height) >= 1800;
  const looksLikeGraphic =
    name.includes("logo") ||
    name.includes("sticker") ||
    name.includes("shirt") ||
    name.includes("graphic");
  const looksLikeProduct = name.includes("product") || name.includes("mockup") || name.includes("item");

  if (looksLikeProduct) {
    applyPreset("product");
    return;
  }
  if (looksLikeGraphic) {
    setRadioValue("tool", "remove-background-upscale");
    document.querySelector("#mode").value = "auto";
    bgModel.value = "auto";
    setRadioValue("cut_mode", "balanced");
    setRadioValue("scale", isLarge ? "2" : "4");
    setRadioValue("sizing", "scale");
    denoise.value = "0.45";
    setCheckbox("alpha-matting", false);
    setCheckbox("post-process-mask", true);
    setCheckbox("preserve-interior", true);
    setCheckbox("respect-alpha", true);
    updateDenoiseValue();
    applyCutPreset(false);
    syncToolUi();
    syncSizingUi(false);
    presetNote.textContent = "Smart Auto detected a graphic-style image and kept safer cutout/upscale defaults.";
    return;
  }
  setRadioValue("tool", "upscale");
  document.querySelector("#mode").value = "auto";
  setRadioValue("scale", isLarge ? "2" : "4");
  setRadioValue("sizing", "scale");
  denoise.value = "0.55";
  updateDenoiseValue();
  syncToolUi();
  syncSizingUi(false);
  presetNote.textContent = "Smart Auto detected a photo-style image and left upscale type on Auto.";
}

function numericInputValue(input) {
  const value = Number(input.value);
  return Number.isFinite(value) && value > 0 ? Math.round(value) : null;
}

function targetOutputSize(size = selectedImageSize) {
  if (!size) return null;
  let width = numericInputValue(targetWidthInput);
  let height = numericInputValue(targetHeightInput);
  if (!width && !height) return null;
  if (!width) width = Math.round(size.width * (height / size.height));
  if (!height) height = Math.round(size.height * (width / size.width));
  return { width: Math.max(1, width), height: Math.max(1, height) };
}

function fillTargetDefaults(force = false) {
  if (!selectedImageSize || selectedSizingMode() !== "target") return;
  if (!force && (targetWidthInput.value || targetHeightInput.value)) return;

  const scale = selectedScale();
  let width = Math.round(selectedImageSize.width * scale);
  let height = Math.round(selectedImageSize.height * scale);
  const capRatio = Math.min(1, maxImageDimension / Math.max(width, height));
  if (capRatio < 1) {
    width = Math.round(width * capRatio);
    height = Math.round(height * capRatio);
  }
  targetWidthInput.value = width;
  targetHeightInput.value = height;
}

function validateResolutionForCurrentSettings(validDetail = null) {
  if (!selectedImageSize) return true;

  const { width, height } = selectedImageSize;
  if (width > maxImageDimension || height > maxImageDimension) {
    runButton.disabled = true;
    setStatus("Error", "error", `Image is ${width} x ${height}. Maximum input resolution is ${resolutionLimitLabel()}.`);
    return false;
  }

  if (usesUpscale()) {
    let outputWidth;
    let outputHeight;

    if (selectedSizingMode() === "target") {
      const target = targetOutputSize();
      if (!target) {
        runButton.disabled = true;
        setStatus("Error", "error", "Enter a target width, target height, or both.");
        return false;
      }
      outputWidth = target.width;
      outputHeight = target.height;
    } else {
      const scale = selectedScale();
      outputWidth = Math.round(width * scale);
      outputHeight = Math.round(height * scale);
    }

    if (outputWidth > maxImageDimension || outputHeight > maxImageDimension) {
      runButton.disabled = true;
      setStatus(
        "Error",
        "error",
        `Requested output would be ${outputWidth} x ${outputHeight}. Maximum output is ${resolutionLimitLabel()}. Choose a smaller output size.`,
      );
      return false;
    }

    const upscaleFactor = Math.max(outputWidth / width, outputHeight / height);
    if (upscaleFactor > maxUpscaleFactor) {
      runButton.disabled = true;
      setStatus(
        "Error",
        "error",
        `Requested output is ${upscaleFactor.toFixed(2)}x the source. Maximum upscale factor is ${maxUpscaleFactor}x.`,
      );
      return false;
    }
  }

  runButton.disabled = false;
  if (validDetail) setStatus("Ready", "ready", validDetail);
  return true;
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
    maxImageDimension = health.max_image_dimension || maxImageDimension;
    maxUpscaleFactor = health.max_upscale_factor || maxUpscaleFactor;
    document.querySelector("#drop-note").textContent =
      `PNG, JPG, or WEBP supported. Max ${resolutionLimitLabel()} per side.`;
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

async function setFiles(files) {
  const list = Array.from(files || []).filter((file) => file.type.startsWith("image/"));
  if (!list.length) {
    setStatus("Error", "error", "Unsupported file type. Try PNG, JPG, or WEBP.");
    return;
  }
  selectedFiles = list;
  batchResults.classList.add("hidden");
  batchResults.replaceChildren();
  await setFile(list[0]);
  if (list.length > 1) {
    fileLabel.textContent = `${list.length} images selected`;
    fileMeta.textContent = `First preview: ${list[0].name}`;
    setStatus("Ready", "ready", `${list.length} images loaded. Batch processing will run one image at a time.`);
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
  if (!selectedFiles.length) selectedFiles = [file];
  selectedImageSize = null;
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

  try {
    const size = await imageSize(beforeUrl);
    selectedImageSize = size;
    if (presetSelect.value === "smart") {
      applySmartPresetForFile(file, size);
    }
    fillTargetDefaults(false);
    beforeMeta.textContent = `${size.width} x ${size.height} | ${fileExtension(file)} | ${formatBytes(file.size)}`;
    fileMeta.textContent = `${size.width} x ${size.height} | ${formatBytes(file.size)}`;
  } catch {
    beforeMeta.textContent = `${fileExtension(file)} | ${formatBytes(file.size)}`;
  }

  afterMeta.textContent = "No result yet";
  setStep(1);
  validateResolutionForCurrentSettings("Image loaded. Choose your settings and start.");
}

function selectedTool() {
  return document.querySelector('input[name="tool"]:checked').value;
}

function usesUpscale() {
  return selectedTool() === "upscale" || selectedTool() === "remove-background-upscale";
}

function usesBackgroundRemoval() {
  return selectedTool() === "remove-background" || selectedTool() === "remove-background-upscale";
}

function selectedCutMode() {
  return document.querySelector('input[name="cut_mode"]:checked')?.value || "balanced";
}

function actionText() {
  if (selectedTool() === "remove-background") return "Remove Background";
  if (selectedTool() === "remove-background-upscale") return "Remove BG + Upscale";
  return "Upscale Image";
}

function syncRunLabel() {
  runLabel.textContent = actionText();
}

function syncSizingUi(forceDefaults = false) {
  const mode = selectedSizingMode();
  sizePanels.forEach((panel) => {
    panel.classList.toggle("hidden", panel.dataset.sizePanel !== mode);
  });
  if (mode === "target") fillTargetDefaults(forceDefaults);
  if (selectedFile) {
    clearResultOnly();
    validateResolutionForCurrentSettings("Sizing updated. Start when ready.");
  }
}

function syncToolUi() {
  const tool = selectedTool();
  toolPanels.forEach((panel) => {
    const shouldShow =
      panel.dataset.toolPanel === tool ||
      (tool === "remove-background-upscale" &&
        (panel.dataset.toolPanel === "upscale" || panel.dataset.toolPanel === "remove-background"));
    panel.classList.toggle("hidden", !shouldShow);
  });

  outputFormat.replaceChildren();
  const allowedFormats = usesBackgroundRemoval() ? ["png", "webp"] : ["png", "jpeg", "webp"];
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
  if (tool === "remove-background") {
    resultTitle.textContent = "Transparent Result";
  } else if (tool === "remove-background-upscale") {
    resultTitle.textContent = "Transparent Enhanced Result";
  } else {
    resultTitle.textContent = "Enhanced Result";
  }
  if (!afterUrl) {
    afterMeta.textContent = "No result yet";
  } else {
    clearResultOnly();
  }
  if (selectedFile) {
    validateResolutionForCurrentSettings("Settings updated. Start when ready.");
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
  selectedFiles = [];
  selectedImageSize = null;
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
  batchResults.classList.add("hidden");
  batchResults.replaceChildren();
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

function applyCutPreset(notify = true) {
  edgeRefine.value = edgeDefaults[selectedCutMode()] || edgeDefaults.balanced;
  bgTolerance.value = toleranceDefaults[selectedCutMode()] || toleranceDefaults.balanced;
  updateEdgeRefineValue();
  updateBgToleranceValue();
  if (selectedFile && notify) {
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

function setPreviewBackground(value = "checker") {
  previewBgButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.previewBg === value);
  });
  previewStages.forEach((stage) => {
    stage.classList.remove("bg-white", "bg-gray", "bg-dark");
    if (value !== "checker") stage.classList.add(`bg-${value}`);
  });
}

function renderBatchResults(results) {
  batchResults.replaceChildren();
  if (!results.length) {
    batchResults.classList.add("hidden");
    return;
  }
  batchResults.classList.remove("hidden");
  results.forEach((result) => {
    const row = document.createElement("div");
    row.className = `batch-row ${result.ok ? "" : "error"}`.trim();
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = result.name;
    const meta = document.createElement("span");
    meta.textContent = result.ok ? result.summary : result.error;
    copy.append(title, meta);
    row.append(copy);
    if (result.ok) {
      const link = document.createElement("a");
      link.href = result.downloadUrl;
      link.download = result.filename;
      link.textContent = "Download";
      row.append(link);
    }
    batchResults.append(row);
  });
}

function renderHistory(jobs) {
  historyList.replaceChildren();
  if (!jobs.length) {
    const empty = document.createElement("p");
    empty.className = "muted-copy";
    empty.textContent = "No saved jobs yet. Process an image and the output will appear here.";
    historyList.append(empty);
    return;
  }
  jobs.forEach((job) => {
    const row = document.createElement("div");
    row.className = "job-row";
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = job.filename || job.source_filename || "Processed image";
    const meta = document.createElement("span");
    const output = job.output || {};
    meta.textContent =
      `${job.tool || "job"} | ${output.width || "?"} x ${output.height || "?"} ${String(output.format || "").toUpperCase()} | ${formatBytes(output.size_bytes || 0)} | ${formatDate(job.created_at)}`;
    copy.append(title, meta);
    const link = document.createElement("a");
    link.href = job.download_url;
    link.download = job.filename || "result.png";
    link.textContent = "Download";
    row.append(copy, link);
    historyList.append(row);
  });
}

async function loadHistory() {
  try {
    const response = await fetch("/api/jobs?limit=10", { cache: "no-store" });
    if (!response.ok) throw new Error("history failed");
    const body = await response.json();
    renderHistory(body.jobs || []);
  } catch {
    historyList.innerHTML = '<p class="muted-copy">Could not load saved jobs.</p>';
  }
}

function renderDiagnostics(data) {
  const runtime = data.runtime || {};
  const storage = data.storage || {};
  const limits = data.limits || {};
  const rows = [
    ["Hardware", runtime.cuda_available ? `NVIDIA GPU: ${runtime.cuda_device || "CUDA"}` : "CPU runtime"],
    ["Available devices", Array.isArray(runtime.available_devices) ? runtime.available_devices.join(", ") : "cpu"],
    ["ONNX providers", Array.isArray(runtime.onnx_providers) ? runtime.onnx_providers.join(", ") : "Unknown"],
    ["Saved outputs", `${storage.saved_jobs || 0} jobs | ${formatBytes(storage.saved_bytes || 0)}`],
    ["Limits", `${limits.max_upload_mb || maxUploadMb} MB upload | ${limits.max_image_dimension || maxImageDimension}px max side | ${limits.max_upscale_factor || maxUpscaleFactor}x max upscale`],
  ];
  diagnosticsPanel.replaceChildren();
  rows.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "diagnostic-row";
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = label;
    const meta = document.createElement("span");
    meta.textContent = value;
    copy.append(title, meta);
    row.append(copy);
    diagnosticsPanel.append(row);
  });
  (data.recommendations || []).forEach((text) => {
    const row = document.createElement("div");
    row.className = "diagnostic-row";
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = "Recommendation";
    const meta = document.createElement("span");
    meta.textContent = text;
    copy.append(title, meta);
    row.append(copy);
    diagnosticsPanel.append(row);
  });
}

async function loadDiagnostics() {
  try {
    const response = await fetch("/api/diagnostics", { cache: "no-store" });
    if (!response.ok) throw new Error("diagnostics failed");
    renderDiagnostics(await response.json());
  } catch {
    diagnosticsPanel.innerHTML = '<p class="muted-copy">Could not load diagnostics.</p>';
  }
}

fileInput.addEventListener("change", () => setFiles(fileInput.files));

presetSelect.addEventListener("change", () => applyPreset(presetSelect.value, true));

toolInputs.forEach((input) => input.addEventListener("change", syncToolUi));

scaleInputs.forEach((input) => {
  input.addEventListener("change", () => {
    if (selectedFile) {
      clearResultOnly();
      validateResolutionForCurrentSettings("Output size updated. Start when ready.");
    }
  });
});

sizingInputs.forEach((input) => {
  input.addEventListener("change", () => syncSizingUi(true));
});

[targetWidthInput, targetHeightInput].forEach((input) => {
  input.addEventListener("input", () => {
    if (selectedFile) {
      clearResultOnly();
      validateResolutionForCurrentSettings("Target resolution updated. Start when ready.");
    }
  });
});

infoTips.forEach((tip) => {
  tip.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const shouldOpen = tip.dataset.open !== "true";
    const panel = document.getElementById(tip.getAttribute("aria-controls"));
    closeInfoTips(tip);
    tip.dataset.open = shouldOpen ? "true" : "false";
    tip.setAttribute("aria-expanded", shouldOpen ? "true" : "false");
    if (panel) panel.hidden = !shouldOpen;
  });
});

infoPanels.forEach((panel) => {
  panel.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
  });
});

document.addEventListener("click", () => closeInfoTips());
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeInfoTips();
  }
});

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
refreshHistory.addEventListener("click", loadHistory);
refreshDiagnostics.addEventListener("click", loadDiagnostics);

previewBgButtons.forEach((button) => {
  button.addEventListener("click", () => setPreviewBackground(button.dataset.previewBg));
});

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
  setFiles(event.dataTransfer.files);
});

function endpointForTool(tool) {
  if (tool === "remove-background") return "/api/remove-background";
  if (tool === "remove-background-upscale") return "/api/remove-background-upscale";
  return "/api/upscale";
}

function buildPayload(file, size = selectedImageSize) {
  const tool = selectedTool();
  const payload = new FormData(form);
  payload.set("image", file);
  payload.delete("tool");
  payload.delete("sizing");
  if (tool === "remove-background-upscale") {
    payload.set("upscale_device", upscaleDevice.value);
    payload.set("background_device", backgroundDevice.value);
  } else {
    payload.delete("upscale_device");
    payload.delete("background_device");
  }
  payload.delete("target_width");
  payload.delete("target_height");
  if (usesUpscale() && selectedSizingMode() === "target") {
    const target = targetOutputSize(size);
    if (target) {
      if (targetWidthInput.value) payload.set("target_width", target.width);
      if (targetHeightInput.value) payload.set("target_height", target.height);
      if (!targetWidthInput.value && !targetHeightInput.value) {
        payload.set("target_width", target.width);
        payload.set("target_height", target.height);
      }
    }
  }
  if (tool !== "remove-background-upscale") {
    payload.set("device", tool === "remove-background" ? backgroundDevice.value : upscaleDevice.value);
  } else {
    payload.delete("device");
  }
  payload.set("face_enhance", document.querySelector("#face").checked ? "true" : "false");
  payload.set("cut_mode", selectedCutMode());
  payload.set("alpha_matting", document.querySelector("#alpha-matting").checked ? "true" : "false");
  payload.set("edge_refine", edgeRefine.value);
  payload.set("background_tolerance", bgTolerance.value);
  payload.set("post_process_mask", document.querySelector("#post-process-mask").checked ? "true" : "false");
  payload.set("preserve_interior", document.querySelector("#preserve-interior").checked ? "true" : "false");
  payload.set("respect_existing_alpha", document.querySelector("#respect-alpha").checked ? "true" : "false");
  return payload;
}

function filenameFromResponse(response, fallback) {
  const disposition = response.headers.get("Content-Disposition") || "";
  const filenameMatch = disposition.match(/filename="([^"]+)"/);
  return filenameMatch ? filenameMatch[1] : fallback;
}

function showResult(blob, response, fallbackName) {
  revoke(afterUrl);
  afterUrl = URL.createObjectURL(blob);
  afterImg.src = afterUrl;
  afterEmpty.classList.add("hidden");

  const width = response.headers.get("X-Output-Width");
  const height = response.headers.get("X-Output-Height");
  const engine =
    response.headers.get("X-Pipeline-Engine") ||
    response.headers.get("X-Upscaler-Engine") ||
    response.headers.get("X-Background-Engine") ||
    "";
  const extension = outputFormat.value.toUpperCase();
  afterMeta.textContent = `${width} x ${height} | ${extension} | ${formatBytes(blob.size)}`;
  resultSummary.textContent = `${width} x ${height} ${extension}`;

  if (engine) {
    engineChip.textContent = engine;
    engineChip.className = `mini-badge ${engine.includes("CUDA") ? "good" : ""}`.trim();
    engineChip.classList.remove("hidden");
  }

  const downloadUrl = response.headers.get("X-Download-URL") || afterUrl;
  const filename = filenameFromResponse(response, fallbackName || "result.png");
  resultDownload.href = downloadUrl;
  resultDownload.download = filename;
  resultDownload.textContent = `Download ${extension}`;
  resultActions.classList.remove("hidden");
  return {
    width,
    height,
    extension,
    engine,
    downloadUrl,
    filename,
    summary: `${width} x ${height} ${extension} | ${formatBytes(blob.size)}`,
  };
}

async function imageSizeForFile(file) {
  const url = URL.createObjectURL(file);
  try {
    return await imageSize(url);
  } finally {
    URL.revokeObjectURL(url);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selectedFile) return;
  if (!validateResolutionForCurrentSettings(null)) return;

  const filesToProcess = selectedFiles.length ? selectedFiles : [selectedFile];
  runButton.disabled = true;
  resultActions.classList.add("hidden");
  afterEmpty.classList.add("hidden");
  compareStage.classList.add("hidden");
  engineChip.classList.add("hidden");
  compareActive = false;
  compareToggle.textContent = "Compare";
  setStep(2);

  const tool = selectedTool();
  let actionLabel = "Enhancing image";
  if (tool === "remove-background") actionLabel = "Removing background";
  if (tool === "remove-background-upscale") actionLabel = "Removing background and upscaling";
  setBusyStatus(filesToProcess.length > 1 ? `Batch ${actionLabel.toLowerCase()}` : actionLabel);

  try {
    const endpoint = endpointForTool(tool);
    const results = [];

    for (let index = 0; index < filesToProcess.length; index += 1) {
      const file = filesToProcess[index];
      const size = index === 0 && selectedImageSize ? selectedImageSize : await imageSizeForFile(file);
      setProgress(
        Math.round((index / filesToProcess.length) * 100),
        `Processing ${index + 1} of ${filesToProcess.length}: ${file.name}`,
      );
      const response = await fetch(endpoint, {
        method: "POST",
        body: buildPayload(file, size),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        results.push({
          ok: false,
          name: file.name,
          error: body.error || `Request failed with ${response.status}`,
        });
        continue;
      }

      const blob = await response.blob();
      const shown = showResult(blob, response, `${file.name}-result.${outputFormat.value}`);
      const item = {
        ok: true,
        name: file.name,
        ...shown,
      };
      results.push(item);
      setProgress(
        Math.round(((index + 1) / filesToProcess.length) * 100),
        `Finished ${index + 1} of ${filesToProcess.length}`,
      );
    }

    renderBatchResults(filesToProcess.length > 1 ? results : []);
    await loadHistory();
    await loadDiagnostics();

    const failures = results.filter((result) => !result.ok);
    if (!results.some((result) => result.ok)) {
      throw new Error(failures[0]?.error || "No images were processed.");
    }

    if (failures.length) {
      setStatus(
        "Complete",
        "complete",
        `${results.length - failures.length} finished, ${failures.length} failed. Check saved jobs for downloads.`,
      );
    } else if (filesToProcess.length > 1) {
      setStatus("Complete", "complete", `Batch complete. ${results.length} images are ready to download.`);
    } else {
      setStatus("Complete", "complete", "Done. Your image is ready to download.");
    }
  } catch (error) {
    afterEmpty.classList.remove("hidden");
    setStep(selectedFile ? 1 : 0);
    setStatus("Error", "error", error.message || "Something went wrong while processing the image.");
  } finally {
    clearBusyStatus();
    if (selectedFile && validateResolutionForCurrentSettings(null)) {
      runButton.disabled = false;
    }
    syncRunLabel();
  }
});

updateDenoiseValue();
updateEdgeRefineValue();
updateBgToleranceValue();
setComparePosition(compareSlider.value);
setPreviewBackground("checker");
syncSizingUi();
syncToolUi();
loadRuntime();
loadHistory();
loadDiagnostics();
