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
const edgeTrim = document.querySelector("#edge-trim");
const edgeTrimValue = document.querySelector("#edge-trim-value");
const fringeCleanup = document.querySelector("#fringe-cleanup");
const fringeCleanupValue = document.querySelector("#fringe-cleanup-value");
const bgModel = document.querySelector("#bg-model");
const bgTolerance = document.querySelector("#bg-tolerance");
const bgToleranceValue = document.querySelector("#bg-tolerance-value");
const innerCleanup = document.querySelector("#inner-cleanup");
const innerCleanupValue = document.querySelector("#inner-cleanup-value");
const backgroundDevice = document.querySelector("#background-device");
const resultActions = document.querySelector("#result-actions");
const resultDownload = document.querySelector("#result-download");
const resultSummary = document.querySelector("#result-summary");
const compareToggle = document.querySelector("#compare-toggle");
const processAnother = document.querySelector("#process-another");
const compareStage = document.querySelector("#compare-stage");
const compareControls = document.querySelector("#compare-controls");
const compareContent = document.querySelector("#compare-content");
const compareBefore = document.querySelector("#compare-before");
const compareAfter = document.querySelector("#compare-after");
const compareDifference = document.querySelector("#compare-difference");
const compareSlider = document.querySelector("#compare-slider");
const compareTagBefore = document.querySelector(".compare-tag-before");
const compareTagAfter = document.querySelector(".compare-tag-after");
const compareModeSelect = document.querySelector("#compare-mode-select");
const compareZoomSelect = document.querySelector("#compare-zoom-select");
const targetWidthInput = document.querySelector("#target-width");
const targetHeightInput = document.querySelector("#target-height");
const targetPresetSelect = document.querySelector("#target-preset");
const previewBgButtons = document.querySelectorAll("[data-preview-bg]");
const previewStages = document.querySelectorAll(".preview-stage");
const historyList = document.querySelector("#history-list");
const batchResults = document.querySelector("#batch-results");
const refreshHistory = document.querySelector("#refresh-history");
const clearHistory = document.querySelector("#clear-history");
const toggleHistoryPreview = document.querySelector("#toggle-history-preview");
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
let maxBatchFiles = 100;
let maxBatchTotalMb = 512;
let selectedImageSize = null;
let compareActive = false;
let compareMode = "slider";
let compareZoom = "fit";
let compareNaturalSize = null;
let differenceKey = "";
let differenceToken = 0;
let historyPreviewEnabled = true;
let currentBatchId = null;

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

const trimDefaults = {
  preserve: "1",
  balanced: "2",
  strong: "3",
};

const fringeDefaults = {
  preserve: "30",
  balanced: "45",
  strong: "70",
};

const innerCleanupDefaults = {
  preserve: "0",
  balanced: "25",
  strong: "50",
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
    edgeTrim: "1",
    fringeCleanup: "45",
    innerCleanup: "25",
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
    edgeTrim: "2",
    fringeCleanup: "70",
    innerCleanup: "45",
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
    edgeTrim: "0",
    fringeCleanup: "0",
    innerCleanup: "0",
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
    edgeTrim: "1",
    fringeCleanup: "35",
    innerCleanup: "20",
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
    edgeTrim: "1",
    fringeCleanup: "40",
    innerCleanup: "25",
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
    edgeTrim: "0",
    fringeCleanup: "0",
    innerCleanup: "0",
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
    edgeTrim: "2",
    fringeCleanup: "70",
    innerCleanup: "45",
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
  if (url && url.startsWith("blob:")) URL.revokeObjectURL(url);
}

function absoluteUrl(url) {
  if (!url) return "";
  return new URL(url, window.location.origin).href;
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
  applyCutPreset(false);
  document.querySelector("#mode").value = preset.mode;
  bgModel.value = preset.model;
  denoise.value = preset.denoise;
  edgeTrim.value = preset.edgeTrim;
  fringeCleanup.value = preset.fringeCleanup;
  innerCleanup.value = preset.innerCleanup;
  outputFormat.value = preset.format;
  setCheckbox("alpha-matting", preset.alphaMatting);
  setCheckbox("post-process-mask", preset.postProcess);
  setCheckbox("preserve-interior", preset.preserveInterior);
  setCheckbox("respect-alpha", preset.respectAlpha);
  updateDenoiseValue();
  updateEdgeTrimValue();
  updateFringeCleanupValue();
  updateInnerCleanupValue();
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
    applyCutPreset(false);
    setRadioValue("scale", isLarge ? "2" : "4");
    setRadioValue("sizing", "scale");
    denoise.value = "0.45";
    edgeTrim.value = "2";
    fringeCleanup.value = "65";
    innerCleanup.value = "45";
    setCheckbox("alpha-matting", false);
    setCheckbox("post-process-mask", true);
    setCheckbox("preserve-interior", true);
    setCheckbox("respect-alpha", true);
    updateDenoiseValue();
    updateEdgeTrimValue();
    updateFringeCleanupValue();
    updateInnerCleanupValue();
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
  edgeTrim.value = "0";
  fringeCleanup.value = "0";
  innerCleanup.value = "0";
  updateDenoiseValue();
  updateEdgeTrimValue();
  updateFringeCleanupValue();
  updateInnerCleanupValue();
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

function loadPreviewImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
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
    maxBatchFiles = health.max_batch_files || maxBatchFiles;
    maxBatchTotalMb = health.max_batch_total_mb || maxBatchTotalMb;
    document.querySelector("#drop-note").textContent =
      `PNG, JPG, or WEBP supported. Max ${resolutionLimitLabel()} per side. Batches up to ${maxBatchFiles} files or ${maxBatchTotalMb} MB.`;
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
  if (list.length > maxBatchFiles) {
    setStatus("Error", "error", `Batch limit is ${maxBatchFiles} images.`);
    return;
  }
  const batchBytes = list.reduce((total, file) => total + file.size, 0);
  if (batchBytes > maxBatchTotalMb * 1024 * 1024) {
    setStatus("Error", "error", `Batch upload exceeds ${maxBatchTotalMb} MB total.`);
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
  closeCompare();

  beforeImg.src = beforeUrl;
  beforeEmpty.classList.add("hidden");
  afterImg.removeAttribute("src");
  afterEmpty.classList.remove("hidden");
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
  if (selectedTool() === "remove-background") return "Remove Back Ground";
  if (selectedTool() === "remove-background-upscale") return "Remove Back Ground + Upscale";
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
  if (mode !== "target" && targetPresetSelect) targetPresetSelect.value = "";
  if (selectedFile) {
    clearResultOnly();
    validateResolutionForCurrentSettings("Sizing updated. Start when ready.");
  }
}

function applyTargetPreset(value) {
  if (!value) return;
  const [w, h] = String(value).split("x").map((n) => Number.parseInt(n, 10));
  if (!Number.isFinite(w) || !Number.isFinite(h)) return;
  setRadioValue("sizing", "target");
  syncSizingUi(false);
  targetWidthInput.value = String(w);
  targetHeightInput.value = String(h);
  if (selectedFile) {
    clearResultOnly();
    validateResolutionForCurrentSettings(`Target preset selected: ${w} x ${h}`);
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
  resultTitle.textContent = "Compare & Result";
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
  afterImg.removeAttribute("src");
  closeCompare();
  afterEmpty.classList.remove("hidden");
  afterMeta.textContent = "No result yet";
  engineChip.classList.add("hidden");
  resultActions.classList.add("hidden");
}

function clearWorkspace() {
  selectedFile = null;
  selectedFiles = [];
  selectedImageSize = null;
  revoke(beforeUrl);
  revoke(afterUrl);
  beforeUrl = null;
  afterUrl = null;
  fileInput.value = "";
  beforeImg.removeAttribute("src");
  afterImg.removeAttribute("src");
  closeCompare();
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
  setStep(0);
  setStatus("Ready", "ready", "Ready for an image.");
}

function updateDenoiseValue() {
  denoiseValue.textContent = Number(denoise.value).toFixed(2);
}

function updateEdgeRefineValue() {
  edgeRefineValue.textContent = edgeRefine.value;
}

function updateEdgeTrimValue() {
  edgeTrimValue.textContent = edgeTrim.value;
}

function updateFringeCleanupValue() {
  fringeCleanupValue.textContent = fringeCleanup.value;
}

function updateBgToleranceValue() {
  bgToleranceValue.textContent = bgTolerance.value;
}

function updateInnerCleanupValue() {
  innerCleanupValue.textContent = innerCleanup.value;
}

function applyCutPreset(notify = true) {
  edgeRefine.value = edgeDefaults[selectedCutMode()] || edgeDefaults.balanced;
  bgTolerance.value = toleranceDefaults[selectedCutMode()] || toleranceDefaults.balanced;
  edgeTrim.value = trimDefaults[selectedCutMode()] || trimDefaults.balanced;
  fringeCleanup.value = fringeDefaults[selectedCutMode()] || fringeDefaults.balanced;
  innerCleanup.value = innerCleanupDefaults[selectedCutMode()] || innerCleanupDefaults.balanced;
  updateEdgeRefineValue();
  updateBgToleranceValue();
  updateEdgeTrimValue();
  updateFringeCleanupValue();
  updateInnerCleanupValue();
  if (selectedFile && notify) {
    clearResultOnly();
    setStatus("Ready", "ready", "Cut strength updated. Start when ready.");
  }
}

function setComparePosition(value) {
  compareStage.style.setProperty("--compare", `${value}%`);
}

function resetCompareDefaults() {
  compareMode = "slider";
  compareZoom = "fit";
  compareSlider.value = "50";
  setComparePosition(50);
  applyCompareMode("slider");
  applyCompareZoom("fit");
}

function closeCompare() {
  compareActive = false;
  compareStage.classList.add("hidden");
  compareControls.classList.add("hidden");
  compareToggle.textContent = "Show Compare";
  updateCompareAvailability();
}

function updateCompareAvailability() {
  const canCompare = Boolean(beforeUrl && afterUrl);
  compareToggle.disabled = !canCompare;
  compareToggle.setAttribute("aria-disabled", canCompare ? "false" : "true");
  compareToggle.title = canCompare ? "Show slider comparison" : "Comparison needs both the original image and a result.";
}

async function refreshCompareSizing() {
  if (!afterUrl) return;
  try {
    const size = await imageSize(afterUrl);
    compareNaturalSize = size;
    applyCompareZoom(compareZoom);
  } catch {
    compareNaturalSize = null;
  }
}

function applyCompareZoom(value = compareZoom) {
  compareZoom = value;
  compareStage.dataset.zoom = value;
  compareZoomSelect.value = value;

  if (!compareNaturalSize || value === "fit") {
    compareContent.style.removeProperty("width");
    compareContent.style.removeProperty("height");
    return;
  }

  const multiplier = value === "200" ? 2 : 1;
  const paneMultiplier = compareMode === "side-by-side" ? 2 : 1;
  compareContent.style.width = `${Math.max(1, Math.round(compareNaturalSize.width * multiplier * paneMultiplier))}px`;
  compareContent.style.height = `${Math.max(1, Math.round(compareNaturalSize.height * multiplier))}px`;
}

async function renderDifferencePreview() {
  if (!beforeUrl || !afterUrl) return;
  const key = `${beforeUrl}|${afterUrl}`;
  if (differenceKey === key && compareDifference.width > 0) return;
  const token = differenceToken + 1;
  differenceToken = token;
  try {
    const [beforeImage, afterImage] = await Promise.all([
      loadPreviewImage(beforeUrl),
      loadPreviewImage(afterUrl),
    ]);
    if (token !== differenceToken) return;

    const maxPreviewSide = 1600;
    const ratio = Math.min(
      1,
      maxPreviewSide / Math.max(afterImage.naturalWidth || 1, afterImage.naturalHeight || 1),
    );
    const width = Math.max(1, Math.round((afterImage.naturalWidth || beforeImage.naturalWidth || 1) * ratio));
    const height = Math.max(1, Math.round((afterImage.naturalHeight || beforeImage.naturalHeight || 1) * ratio));
    compareDifference.width = width;
    compareDifference.height = height;

    const ctx = compareDifference.getContext("2d", { willReadFrequently: true });
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);
    ctx.drawImage(beforeImage, 0, 0, width, height);
    const beforeData = ctx.getImageData(0, 0, width, height);

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);
    ctx.drawImage(afterImage, 0, 0, width, height);
    const afterData = ctx.getImageData(0, 0, width, height);
    const pixels = afterData.data;
    const beforePixels = beforeData.data;
    for (let index = 0; index < pixels.length; index += 4) {
      const red = Math.abs(pixels[index] - beforePixels[index]);
      const green = Math.abs(pixels[index + 1] - beforePixels[index + 1]);
      const blue = Math.abs(pixels[index + 2] - beforePixels[index + 2]);
      const alpha = Math.abs(pixels[index + 3] - beforePixels[index + 3]);
      pixels[index] = Math.min(255, red * 3 + alpha);
      pixels[index + 1] = Math.min(255, green * 3 + alpha);
      pixels[index + 2] = Math.min(255, blue * 3 + alpha);
      pixels[index + 3] = 255;
    }
    ctx.putImageData(afterData, 0, 0);
    differenceKey = key;
  } catch {
    compareDifference.width = 1;
    compareDifference.height = 1;
  }
}

function applyCompareMode(value = compareMode) {
  compareMode = beforeUrl ? value : value === "before" || value === "difference" ? "after" : value;
  compareStage.dataset.mode = compareMode;
  compareModeSelect.value = compareMode;
  Array.from(compareModeSelect.options).forEach((option) => {
    option.disabled = !beforeUrl && (option.value === "before" || option.value === "difference");
  });
  compareTagBefore.textContent = compareMode === "difference" ? "Difference" : "Original";
  compareTagAfter.textContent = "Result";
  applyCompareZoom(compareZoom);
  if (compareActive && compareMode === "difference") {
    renderDifferencePreview();
  }
}

function openCompare({ mode = compareMode } = {}) {
  updateCompareAvailability();
  if (!beforeUrl || !afterUrl) return;
  compareActive = true;
  compareBefore.src = beforeUrl;
  compareAfter.src = afterUrl;
  setComparePosition(compareSlider.value);
  applyCompareMode(mode);
  applyCompareZoom(compareZoom);
  refreshCompareSizing();
  compareStage.classList.remove("hidden");
  compareControls.classList.remove("hidden");
  compareToggle.textContent = "Hide Compare";
  compareToggle.title = "Hide comparison view";
}

function toggleCompare() {
  if (compareActive) {
    closeCompare();
  } else {
    openCompare({ mode: compareMode });
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

function openStoredPreview({ sourceUrl, resultUrl, downloadUrl, filename, summary, compare = false }) {
  const resolvedResult = absoluteUrl(resultUrl || downloadUrl);
  const resolvedSource = absoluteUrl(sourceUrl);
  if (!resolvedResult) return;

  revoke(beforeUrl);
  revoke(afterUrl);
  beforeUrl = resolvedSource || null;
  afterUrl = resolvedResult;

  if (beforeUrl) {
    beforeImg.src = beforeUrl;
    beforeEmpty.classList.add("hidden");
    beforeMeta.textContent = "Original preview";
  } else {
    beforeImg.removeAttribute("src");
    beforeEmpty.classList.remove("hidden");
    beforeMeta.textContent = "No source preview";
  }

  afterImg.src = afterUrl;
  afterEmpty.classList.add("hidden");
  afterMeta.textContent = summary || filename || "Saved result";
  resultSummary.textContent = summary || filename || "Saved result";
  resultDownload.href = afterUrl;
  resultDownload.download = filename || "result.png";
  resultDownload.textContent = "Download Image";
  resultActions.classList.remove("hidden");
  engineChip.classList.add("hidden");
  differenceKey = "";
  resetCompareDefaults();
  if (beforeUrl) {
    openCompare({ mode: "slider" });
  } else {
    closeCompare();
  }
  setStep(2);
  setStatus("Ready", "ready", `Previewing ${filename || "saved result"}.`);
}

function batchToResults(batch) {
  return (batch.items || []).map((item) => {
    const done = item.status === "done";
    return {
      ok: done,
      pending: !done && item.status !== "error",
      status: item.status || "queued",
      name: item.filename,
      summary: done ? item.result_filename || "Done" : `Status: ${item.status || "queued"}`,
      error: item.error || "Failed",
      downloadUrl: item.result_download_url || "",
      sourceUrl: item.source_url || "",
      filename: item.result_filename || item.filename,
    };
  });
}

function makePreviewThumbs(sourceUrl, resultUrl, label) {
  const thumbs = document.createElement("button");
  thumbs.className = "preview-thumbs";
  if (!sourceUrl) thumbs.classList.add("single");
  thumbs.type = "button";
  thumbs.title = "Preview before and after";
  thumbs.addEventListener("click", () => openStoredPreview({
    sourceUrl,
    resultUrl,
    filename: label,
    summary: label,
    compare: Boolean(sourceUrl),
  }));

  if (sourceUrl) {
    const before = document.createElement("img");
    before.src = sourceUrl;
    before.alt = "Original thumbnail";
    thumbs.append(before);
  }

  const after = document.createElement("img");
  after.src = resultUrl;
  after.alt = "Result thumbnail";
  thumbs.append(after);
  return thumbs;
}

function renderBatchResults(results, batch = null) {
  batchResults.replaceChildren();
  if (!results.length) {
    batchResults.classList.add("hidden");
    return;
  }
  batchResults.classList.remove("hidden");
  if (batch || currentBatchId) {
    const batchId = batch?.id || currentBatchId;
    const actions = document.createElement("div");
    actions.className = "batch-actions";
    if (batch) {
      const summary = document.createElement("span");
      summary.className = "batch-summary";
      summary.textContent = `Batch ${batch.id.slice(0, 8)} | ${batch.completed || 0}/${batch.total || results.length} complete | ${batch.status || "queued"}`;
      actions.append(summary);
    }
    if (batch?.zip_url && (batch.completed || 0) > 0) {
      const zipLink = document.createElement("a");
      zipLink.href = batch.zip_url;
      zipLink.className = "secondary-button";
      zipLink.textContent = "Download Batch ZIP";
      actions.append(zipLink);
    }
    const retryFailed = document.createElement("button");
    retryFailed.className = "small-button";
    retryFailed.type = "button";
    retryFailed.textContent = "Retry Failed";
    retryFailed.addEventListener("click", () => retryBatch(batchId, true).catch((error) => setStatus("Error", "error", error.message || "Retry failed.")));
    const rerunAll = document.createElement("button");
    rerunAll.className = "small-button";
    rerunAll.type = "button";
    rerunAll.textContent = "Run Again";
    rerunAll.addEventListener("click", () => retryBatch(batchId, false).catch((error) => setStatus("Error", "error", error.message || "Rerun failed.")));
    actions.append(retryFailed, rerunAll);
    batchResults.append(actions);
  }
  results.forEach((result) => {
    const row = document.createElement("div");
    row.className = `batch-row ${result.ok ? "" : result.pending ? "pending" : "error"}`.trim();
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = result.name;
    const meta = document.createElement("span");
    meta.textContent = result.ok || result.pending ? result.summary : result.error;
    copy.append(title, meta);
    if (historyPreviewEnabled && result.ok && result.downloadUrl) {
      copy.append(makePreviewThumbs(result.sourceUrl, result.downloadUrl, result.filename || result.name));
    }
    row.append(copy);
    if (result.ok) {
      const actions = document.createElement("div");
      actions.className = "job-actions";
      if (historyPreviewEnabled) {
        const preview = document.createElement("button");
        preview.className = "small-button";
        preview.type = "button";
        preview.textContent = "Preview";
        preview.setAttribute("aria-label", `Preview ${result.filename || result.name || "batch result"}`);
        preview.addEventListener("click", () => openStoredPreview({
          sourceUrl: result.sourceUrl,
          resultUrl: result.downloadUrl,
          filename: result.filename,
          summary: result.summary,
        }));
        actions.append(preview);
        if (result.sourceUrl) {
          const compare = document.createElement("button");
          compare.className = "small-button";
          compare.type = "button";
          compare.textContent = "Compare";
          compare.setAttribute("aria-label", `Compare ${result.filename || result.name || "batch result"}`);
          compare.addEventListener("click", () => openStoredPreview({
            sourceUrl: result.sourceUrl,
            resultUrl: result.downloadUrl,
            filename: result.filename,
            summary: result.summary,
            compare: true,
          }));
          actions.append(compare);
        }
      }
      const link = document.createElement("a");
      link.href = result.downloadUrl;
      link.download = result.filename;
      link.textContent = "Download";
      actions.append(link);
      row.append(actions);
    }
    batchResults.append(row);
  });
}

async function retryBatch(batchId, failedOnly = true) {
  const response = await fetch(`/api/batches/${encodeURIComponent(batchId)}/retry?failed_only=${failedOnly ? "true" : "false"}`, {
    method: "POST",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "Could not queue retry batch.");
  }
  const batch = (await response.json()).batch;
  currentBatchId = batch.id;
  setStatus("Processing", "busy", failedOnly ? "Retrying failed items in background." : "Re-running batch in background.");
  const completed = await pollBatch(batch.id);
  const batchItems = completed.items || [];
  renderBatchResults(batchToResults({ ...completed, items: batchItems }), completed);
  await loadHistory();
  await loadDiagnostics();
}

function renderHistory(jobs, batches = []) {
  historyList.replaceChildren();
  if (!jobs.length && !batches.length) {
    const empty = document.createElement("p");
    empty.className = "muted-copy";
    empty.textContent = "No saved jobs or batches yet. Process images and the outputs will appear here.";
    historyList.append(empty);
    return;
  }

  if (batches.length) {
    const batchHeading = document.createElement("h3");
    batchHeading.className = "history-section-title";
    batchHeading.textContent = "Batch Jobs";
    historyList.append(batchHeading);
    batches.forEach((batch) => {
      const card = document.createElement("div");
      card.className = "batch-card";
      const header = document.createElement("div");
      header.className = "batch-card-header";
      const copy = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = `Batch ${String(batch.id || "").slice(0, 8)}`;
      const meta = document.createElement("span");
      meta.textContent =
        `${batch.tool || "batch"} | ${batch.completed || 0}/${batch.total || 0} complete | ${batch.status || "queued"} | ${formatDate(batch.created_at)}`;
      copy.append(title, meta);
      const actions = document.createElement("div");
      actions.className = "job-actions";
      if (batch.zip_url && (batch.completed || 0) > 0) {
        const zipLink = document.createElement("a");
        zipLink.href = batch.zip_url;
        zipLink.textContent = "ZIP";
        actions.append(zipLink);
      }
      const openButton = document.createElement("button");
      openButton.className = "small-button";
      openButton.type = "button";
      openButton.textContent = "Open";
      openButton.addEventListener("click", () => {
        currentBatchId = batch.id;
        renderBatchResults(batchToResults(batch), batch);
        setStatus("Ready", "ready", `Loaded batch ${String(batch.id || "").slice(0, 8)}.`);
      });
      actions.append(openButton);
      header.append(copy, actions);
      card.append(header);

      if (historyPreviewEnabled) {
        const itemGrid = document.createElement("div");
        itemGrid.className = "batch-preview-grid";
        (batch.items || []).forEach((item) => {
          const itemRow = document.createElement("div");
          itemRow.className = `batch-mini ${item.status === "done" ? "" : "pending"}`.trim();
          if (item.status === "done" && item.result_download_url) {
            itemRow.append(makePreviewThumbs(item.source_url, item.result_download_url, item.result_filename || item.filename));
          }
          const label = document.createElement("span");
          label.textContent = item.result_filename || item.filename;
          itemRow.append(label);
          itemGrid.append(itemRow);
        });
        card.append(itemGrid);
      }
      historyList.append(card);
    });
  }

  if (jobs.length) {
    const jobHeading = document.createElement("h3");
    jobHeading.className = "history-section-title";
    jobHeading.textContent = "Image Jobs";
    historyList.append(jobHeading);
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
    if (historyPreviewEnabled && job.download_url) {
      copy.append(makePreviewThumbs(job.source_download_url, job.download_url, job.filename || job.source_filename || "Processed image"));
    }
    const link = document.createElement("a");
    link.href = job.download_url;
    link.download = job.filename || "result.png";
    link.textContent = "Download";
    const actions = document.createElement("div");
    actions.className = "job-actions";
    if (historyPreviewEnabled) {
      const previewButton = document.createElement("button");
      previewButton.className = "small-button";
      previewButton.type = "button";
      previewButton.textContent = "Preview";
      previewButton.setAttribute("aria-label", `Preview ${job.filename || job.source_filename || "processed image"}`);
      previewButton.addEventListener("click", () => openStoredPreview({
        sourceUrl: job.source_download_url,
        resultUrl: job.download_url,
        filename: job.filename || "result.png",
        summary: meta.textContent,
      }));
      actions.append(previewButton);
      if (job.source_download_url) {
        const compareButton = document.createElement("button");
        compareButton.className = "small-button";
        compareButton.type = "button";
        compareButton.textContent = "Compare";
        compareButton.setAttribute("aria-label", `Compare ${job.filename || job.source_filename || "processed image"}`);
        compareButton.addEventListener("click", () => openStoredPreview({
          sourceUrl: job.source_download_url,
          resultUrl: job.download_url,
          filename: job.filename || "result.png",
          summary: meta.textContent,
          compare: true,
        }));
        actions.append(compareButton);
      }
    }
    const deleteButton = document.createElement("button");
    deleteButton.className = "small-button danger-button";
    deleteButton.type = "button";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", () => deleteSavedJob(job));
    actions.append(link, deleteButton);
    row.append(copy, actions);
    historyList.append(row);
  });
}

async function loadHistory() {
  try {
    const [jobsResponse, batchesResponse] = await Promise.all([
      fetch("/api/jobs?limit=20", { cache: "no-store" }),
      fetch("/api/batches?limit=10", { cache: "no-store" }),
    ]);
    if (!jobsResponse.ok || !batchesResponse.ok) throw new Error("history failed");
    const jobsBody = await jobsResponse.json();
    const batchesBody = await batchesResponse.json();
    renderHistory(jobsBody.jobs || [], batchesBody.batches || []);
  } catch {
    historyList.innerHTML = '<p class="muted-copy">Could not load saved jobs.</p>';
  }
}

async function pollBatch(batchId) {
  while (true) {
    const response = await fetch(`/api/batches/${encodeURIComponent(batchId)}`, { cache: "no-store" });
    if (!response.ok) throw new Error("Batch status failed");
    const batch = await response.json();
    const done = batch.completed || 0;
    const failed = batch.failed || 0;
    const total = batch.total || 0;
    setProgress(total ? Math.round(((done + failed) / total) * 100) : 0, `Batch progress: ${done + failed}/${total}`);
    if (batch.status === "completed") return batch;
    await new Promise((resolve) => setTimeout(resolve, 1200));
  }
}

async function deleteSavedJob(job) {
  const name = job.filename || job.source_filename || "this saved job";
  const confirmed = window.confirm(
    `Delete "${name}" from Saved Jobs? This removes the saved output file and its history entry.`,
  );
  if (!confirmed) return;

  try {
    const response = await fetch(`/api/jobs/${encodeURIComponent(job.id)}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.error || `Delete failed with ${response.status}`);
    }
    setStatus("Ready", "ready", "Saved job deleted.");
    await loadHistory();
    await loadDiagnostics();
  } catch (error) {
    setStatus("Error", "error", error.message || "Could not delete the saved job.");
  }
}

async function clearSavedJobs() {
  const confirmed = window.confirm(
    "Clear all recent saved jobs? This removes every saved output file and history entry from Docker storage.",
  );
  if (!confirmed) return;

  try {
    const response = await fetch("/api/jobs", {
      method: "DELETE",
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.error || `Clear failed with ${response.status}`);
    }
    setStatus("Ready", "ready", "Recent saved jobs cleared.");
    await loadHistory();
    await loadDiagnostics();
  } catch (error) {
    setStatus("Error", "error", error.message || "Could not clear saved jobs.");
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
    ["Saved outputs", `${storage.saved_jobs || 0} jobs | ${formatBytes(storage.saved_bytes || 0)} output | ${formatBytes(storage.saved_source_bytes || 0)} source`],
    ["Limits", `${limits.max_upload_mb || maxUploadMb} MB upload | ${limits.max_batch_files || maxBatchFiles} files / ${limits.max_batch_total_mb || maxBatchTotalMb} MB batch | ${limits.max_image_dimension || maxImageDimension}px max side | ${limits.max_upscale_factor || maxUpscaleFactor}x max upscale`],
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
    if (targetPresetSelect) targetPresetSelect.value = "";
    if (selectedFile) {
      clearResultOnly();
      validateResolutionForCurrentSettings("Target resolution updated. Start when ready.");
    }
  });
});
if (targetPresetSelect) {
  targetPresetSelect.addEventListener("change", () => applyTargetPreset(targetPresetSelect.value));
}

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
edgeTrim.addEventListener("input", updateEdgeTrimValue);
fringeCleanup.addEventListener("input", updateFringeCleanupValue);
bgTolerance.addEventListener("input", updateBgToleranceValue);
innerCleanup.addEventListener("input", updateInnerCleanupValue);
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
compareModeSelect.addEventListener("change", () => {
  applyCompareMode(compareModeSelect.value);
  if (!compareActive) openCompare({ mode: compareModeSelect.value });
});
compareZoomSelect.addEventListener("change", () => {
  applyCompareZoom(compareZoomSelect.value);
  if (!compareActive) openCompare({ mode: compareMode });
});
refreshHistory.addEventListener("click", loadHistory);
clearHistory.addEventListener("click", clearSavedJobs);
toggleHistoryPreview.addEventListener("click", () => {
  historyPreviewEnabled = !historyPreviewEnabled;
  toggleHistoryPreview.textContent = `Preview: ${historyPreviewEnabled ? "On" : "Off"}`;
  loadHistory();
});
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
  payload.set("tool", tool);
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
  payload.set("edge_trim", edgeTrim.value);
  payload.set("fringe_cleanup", fringeCleanup.value);
  payload.set("background_tolerance", bgTolerance.value);
  payload.set("inner_cleanup", innerCleanup.value);
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
  differenceKey = "";
  updateCompareAvailability();

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
  const sourceUrl = response.headers.get("X-Source-URL") || beforeUrl;
  const filename = filenameFromResponse(response, fallbackName || "result.png");
  resultDownload.href = downloadUrl;
  resultDownload.download = filename;
  resultDownload.textContent = `Download ${extension}`;
  resultActions.classList.remove("hidden");
  resetCompareDefaults();
  if (beforeUrl) openCompare({ mode: "slider" });
  return {
    width,
    height,
    extension,
    engine,
    downloadUrl,
    sourceUrl,
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
  engineChip.classList.add("hidden");
  closeCompare();
  setStep(2);

  const tool = selectedTool();
  let actionLabel = "Enhancing image";
  if (tool === "remove-background") actionLabel = "Removing back ground";
  if (tool === "remove-background-upscale") actionLabel = "Removing back ground and upscaling";
  setBusyStatus(filesToProcess.length > 1 ? `Batch ${actionLabel.toLowerCase()}` : actionLabel);

  try {
    const endpoint = endpointForTool(tool);
    const results = [];

    if (filesToProcess.length > 1) {
      const payload = buildPayload(filesToProcess[0], selectedImageSize);
      payload.delete("image");
      filesToProcess.forEach((file) => payload.append("images", file, file.name));
      const batchResponse = await fetch("/api/batches", { method: "POST", body: payload });
      if (!batchResponse.ok) {
        const body = await batchResponse.json().catch(() => ({}));
        throw new Error(body.detail || `Batch failed with ${batchResponse.status}`);
      }
      const batch = (await batchResponse.json()).batch;
      currentBatchId = batch.id;
      renderBatchResults(batchToResults(batch), batch);
      setStatus("Processing", "busy", "Batch queued on server. You can close this browser and return later.");
      const completed = await pollBatch(batch.id);
      const batchItems = completed.items || [];
      const ok = batchItems.filter((item) => item.status === "done");
      const failed = batchItems.filter((item) => item.status === "error");
      renderBatchResults(batchToResults(completed), completed);
      if (ok[0]?.result_download_url) {
        openStoredPreview({
          sourceUrl: ok[0].source_url,
          resultUrl: ok[0].result_download_url,
          filename: ok[0].result_filename || ok[0].filename,
          summary: ok[0].result_filename || "Batch result",
        });
      }
      await loadHistory();
      await loadDiagnostics();
      setStatus("Complete", "complete", `Batch complete. ${ok.length} finished, ${failed.length} failed.`);
      return;
    }

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
updateEdgeTrimValue();
updateFringeCleanupValue();
updateBgToleranceValue();
updateInnerCleanupValue();
setComparePosition(compareSlider.value);
applyCompareMode("slider");
applyCompareZoom("fit");
updateCompareAvailability();
setPreviewBackground("checker");
syncSizingUi();
syncToolUi();
loadRuntime();
loadHistory();
loadDiagnostics();
