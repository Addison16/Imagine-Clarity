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
const presetCardGrid = document.querySelector("#preset-cards");
let presetCards = document.querySelectorAll("[data-preset-choice]");
const workflowCards = document.querySelectorAll("[data-workflow-choice]");
const workflowNote = document.querySelector("#workflow-note");
const presetNameInput = document.querySelector("#preset-name");
const savePresetButton = document.querySelector("#save-preset");
const deletePresetButton = document.querySelector("#delete-preset");
const experienceInputs = document.querySelectorAll('input[name="experience_mode"]');
const experienceNote = document.querySelector("#experience-note");
const recommendationCard = document.querySelector("#recommendation-card");
const recommendationTitle = document.querySelector("#recommendation-title");
const recommendationCopy = document.querySelector("#recommendation-copy");
const useRecommendation = document.querySelector("#use-recommendation");
const advancedWorkflowCard = document.querySelector("#advanced-workflow-card");
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
const beforeStage = document.querySelector("#before-stage");
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
const vectorPreset = document.querySelector("#vector-preset");
const vectorColormode = document.querySelector("#vector-colormode");
const vectorHierarchical = document.querySelector("#vector-hierarchical");
const vectorMode = document.querySelector("#vector-mode");
const vectorFilterSpeckle = document.querySelector("#vector-filter-speckle");
const vectorColorPrecision = document.querySelector("#vector-color-precision");
const vectorLayerDifference = document.querySelector("#vector-layer-difference");
const vectorPathPrecision = document.querySelector("#vector-path-precision");
const resultActions = document.querySelector("#result-actions");
const resultDownload = document.querySelector("#result-download");
const listingPackDownload = document.querySelector("#listing-pack-download");
const resultSummary = document.querySelector("#result-summary");
const resultCheck = document.querySelector("#result-check");
const resultCheckVerdict = document.querySelector("#result-check-verdict");
const resultCheckList = document.querySelector("#result-check-list");
const resultVersions = document.querySelector("#result-versions");
const resultVersionList = document.querySelector("#result-version-list");
const resultReview = document.querySelector("#result-review");
const resultReviewJob = document.querySelector("#result-review-job");
const reviewCheckButtons = document.querySelectorAll("[data-review-action]");
const quickFixButtons = document.querySelectorAll("[data-quick-fix]");
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
const targetFitSelect = document.querySelector("#target-fit");
const resizeMethodSelect = document.querySelector("#resize-method");
const sharpenAmount = document.querySelector("#sharpen-amount");
const sharpenValue = document.querySelector("#sharpen-value");
const canvasPresetSelect = document.querySelector("#canvas-preset");
const canvasWidthInput = document.querySelector("#canvas-width");
const canvasHeightInput = document.querySelector("#canvas-height");
const canvasAnchorSelect = document.querySelector("#canvas-anchor");
const dpiInput = document.querySelector("#dpi");
const printSizeNote = document.querySelector("#print-size-note");
const exportQuality = document.querySelector("#export-quality");
const exportQualityValue = document.querySelector("#export-quality-value");
const exportQualityField = document.querySelector("#export-quality-field");
const upscaleOnlyFields = document.querySelectorAll("[data-upscale-only]");
const previewBgButtons = document.querySelectorAll("[data-preview-bg]");
const previewStages = document.querySelectorAll(".preview-stage");
const historyList = document.querySelector("#history-list");
const batchResults = document.querySelector("#batch-results");
const refreshHistory = document.querySelector("#refresh-history");
const clearHistory = document.querySelector("#clear-history");
const toggleHistoryPreview = document.querySelector("#toggle-history-preview");
const historySearch = document.querySelector("#history-search");
const historyFilter = document.querySelector("#history-filter");
const historySort = document.querySelector("#history-sort");
const diagnosticsPanel = document.querySelector("#diagnostics-panel");
const refreshDiagnostics = document.querySelector("#refresh-diagnostics");
const viewTabs = document.querySelectorAll("[data-view-target]");
const appViews = document.querySelectorAll(".app-view");
const workflowAssistant = document.querySelector("#workflow-assistant");
const assistantStep = document.querySelector("#assistant-step");
const assistantTitle = document.querySelector("#assistant-title");
const assistantDetail = document.querySelector("#assistant-detail");
const assistantPrimary = document.querySelector("#assistant-primary");
const assistantSecondary = document.querySelector("#assistant-secondary");
const globalDropOverlay = document.querySelector("#global-drop-overlay");

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
let historyPreviewEnabled = false;
let currentBatchId = null;
let currentQueueJobId = null;
let currentResultJob = null;
let activeWorkflow = "shirt";
let recommendedWorkflow = "shirt";
let userPresetIds = new Set();
let historyJobsCache = [];
let historyBatchesCache = [];
let activeEventSource = null;
let resultVersionStore = [];

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

const shirtTarget = {
  preset: "4500x5400",
  width: "4500",
  height: "5400",
  fit: "pad",
};

const presets = {
  smart: {
    note: "Smart Auto targets a standard 4500 x 5400 shirt canvas and chooses safer defaults.",
    tool: null,
    mode: "auto",
    model: "auto",
    cut: "balanced",
    scale: "4",
    sizing: "target",
    targetPreset: shirtTarget.preset,
    targetWidth: shirtTarget.width,
    targetHeight: shirtTarget.height,
    targetFit: shirtTarget.fit,
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
    sizing: "target",
    targetPreset: shirtTarget.preset,
    targetWidth: shirtTarget.width,
    targetHeight: shirtTarget.height,
    targetFit: shirtTarget.fit,
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
    sizing: "target",
    targetPreset: shirtTarget.preset,
    targetWidth: shirtTarget.width,
    targetHeight: shirtTarget.height,
    targetFit: shirtTarget.fit,
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
    sizing: "target",
    targetPreset: shirtTarget.preset,
    targetWidth: shirtTarget.width,
    targetHeight: shirtTarget.height,
    targetFit: shirtTarget.fit,
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
    sizing: "target",
    targetPreset: shirtTarget.preset,
    targetWidth: shirtTarget.width,
    targetHeight: shirtTarget.height,
    targetFit: shirtTarget.fit,
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
    note: "Best when preparing a 4500 x 5400 shirt canvas for print or mockups.",
    tool: "upscale",
    mode: "auto",
    model: "auto",
    cut: "balanced",
    scale: "8",
    sizing: "target",
    targetPreset: shirtTarget.preset,
    targetWidth: shirtTarget.width,
    targetHeight: shirtTarget.height,
    targetFit: shirtTarget.fit,
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
    sizing: "target",
    targetPreset: shirtTarget.preset,
    targetWidth: shirtTarget.width,
    targetHeight: shirtTarget.height,
    targetFit: shirtTarget.fit,
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

const workflowPresets = {
  shirt: {
    presetKey: "print",
    workflowNote: "Shirt Design applies a transparent PNG workflow and pads the final art to 4500 x 5400.",
    note: "Shirt Design removes the background first, then upscales to a standard 4500 x 5400 transparent shirt canvas.",
    tool: "remove-background-upscale",
    mode: "conservative",
    model: "logo",
    cut: "balanced",
    scale: "4",
    sizing: "target",
    targetPreset: shirtTarget.preset,
    targetWidth: shirtTarget.width,
    targetHeight: shirtTarget.height,
    targetFit: shirtTarget.fit,
    resizeMethod: "preserve",
    sharpenAmount: "65",
    dpi: "300",
    exportQuality: "95",
    denoise: "0.35",
    edgeTrim: "2",
    fringeCleanup: "65",
    innerCleanup: "45",
    alphaMatting: false,
    postProcess: true,
    preserveInterior: true,
    respectAlpha: true,
    format: "png",
  },
  sticker: {
    presetKey: "logo",
    workflowNote: "Sticker / Logo protects lettering, checks halos, and keeps the result transparent.",
    note: "Sticker / Logo keeps hard edges clean and prepares a transparent 3000 x 3000 output.",
    tool: "remove-background-upscale",
    mode: "conservative",
    model: "logo",
    cut: "preserve",
    scale: "4",
    sizing: "target",
    targetPreset: "3000x3000",
    targetWidth: "3000",
    targetHeight: "3000",
    targetFit: "pad",
    resizeMethod: "preserve",
    sharpenAmount: "70",
    dpi: "300",
    exportQuality: "95",
    denoise: "0.25",
    edgeTrim: "2",
    fringeCleanup: "70",
    innerCleanup: "35",
    alphaMatting: false,
    postProcess: true,
    preserveInterior: true,
    respectAlpha: true,
    format: "png",
  },
  product: {
    presetKey: "product",
    workflowNote: "Product Photo cuts out the subject and prepares a square listing-friendly result.",
    note: "Product Photo uses a stronger subject model and exports a transparent product listing image.",
    tool: "remove-background-upscale",
    mode: "photo",
    model: "accurate",
    cut: "balanced",
    scale: "4",
    sizing: "target",
    targetPreset: "1600x1600",
    targetWidth: "1600",
    targetHeight: "1600",
    targetFit: "pad",
    resizeMethod: "lanczos",
    sharpenAmount: "55",
    dpi: "300",
    exportQuality: "92",
    denoise: "0.45",
    edgeTrim: "1",
    fringeCleanup: "40",
    innerCleanup: "25",
    alphaMatting: true,
    postProcess: true,
    preserveInterior: true,
    respectAlpha: true,
    format: "png",
  },
  web: {
    presetKey: "photo",
    workflowNote: "Web / Listing Image keeps the background and targets a smaller web-ready file.",
    note: "Web / Listing Image upscales or resizes to a 1600 x 1600 WebP for faster pages and listings.",
    tool: "upscale",
    mode: "auto",
    model: "auto",
    cut: "balanced",
    scale: "2",
    sizing: "target",
    targetPreset: "1600x1600",
    targetWidth: "1600",
    targetHeight: "1600",
    targetFit: "contain",
    resizeMethod: "lanczos",
    sharpenAmount: "55",
    dpi: "72",
    exportQuality: "90",
    denoise: "0.4",
    edgeTrim: "0",
    fringeCleanup: "0",
    innerCleanup: "0",
    alphaMatting: true,
    postProcess: true,
    preserveInterior: true,
    respectAlpha: true,
    format: "webp",
  },
  vector: {
    presetKey: "artwork",
    workflowNote: "Vector SVG traces logos, decals, and clean artwork into scalable paths.",
    note: "Vector SVG uses VTracer for accurate color path tracing. Best after cleanup/upscale when the source is rough.",
    tool: "vectorize",
    mode: "conservative",
    model: "logo",
    cut: "preserve",
    scale: "2",
    sizing: "scale",
    targetPreset: "",
    targetWidth: "",
    targetHeight: "",
    targetFit: "contain",
    resizeMethod: "preserve",
    sharpenAmount: "50",
    dpi: "300",
    exportQuality: "95",
    denoise: "0.25",
    edgeTrim: "0",
    fringeCleanup: "0",
    innerCleanup: "0",
    alphaMatting: false,
    postProcess: false,
    preserveInterior: true,
    respectAlpha: true,
    format: "svg",
    vectorPreset: "logo",
    vectorColormode: "color",
    vectorHierarchical: "stacked",
    vectorMode: "spline",
  },
  printforge: {
    presetKey: "product",
    workflowNote: "PrintForge Product Prep cuts out product art, keeps detail protected, and exports clean shop-ready PNGs.",
    note: "PrintForge Product Prep creates transparent 3000 x 3000 PNGs that work well for listings, mockups, and reusable product assets.",
    tool: "remove-background-upscale",
    mode: "conservative",
    model: "logo",
    cut: "preserve",
    scale: "4",
    sizing: "target",
    targetPreset: "3000x3000",
    targetWidth: "3000",
    targetHeight: "3000",
    targetFit: "pad",
    resizeMethod: "preserve",
    sharpenAmount: "70",
    dpi: "300",
    exportQuality: "95",
    denoise: "0.25",
    edgeTrim: "2",
    fringeCleanup: "70",
    innerCleanup: "45",
    alphaMatting: false,
    postProcess: true,
    preserveInterior: true,
    respectAlpha: true,
    format: "png",
  },
  custom: {
    presetKey: "",
    workflowNote: "Custom leaves the current settings alone and opens Pro controls for manual tuning.",
  },
};

const vectorPresetDefaults = {
  logo: { colormode: "color", hierarchical: "stacked", mode: "spline", filterSpeckle: "4", colorPrecision: "6", layerDifference: "16", pathPrecision: "3" },
  artwork: { colormode: "color", hierarchical: "stacked", mode: "spline", filterSpeckle: "6", colorPrecision: "7", layerDifference: "12", pathPrecision: "4" },
  "line-art": { colormode: "binary", hierarchical: "stacked", mode: "spline", filterSpeckle: "3", colorPrecision: "6", layerDifference: "16", pathPrecision: "3" },
  photo: { colormode: "color", hierarchical: "stacked", mode: "spline", filterSpeckle: "8", colorPrecision: "5", layerDifference: "24", pathPrecision: "3" },
};

function selectedExperienceMode() {
  return document.querySelector('input[name="experience_mode"]:checked')?.value || "beginner";
}

function setExperienceMode(mode = "beginner") {
  setRadioValue("experience_mode", mode);
  syncExperienceMode();
}

function syncExperienceMode() {
  const mode = selectedExperienceMode();
  const isPro = mode === "pro";
  document.body.classList.toggle("pro-mode", isPro);
  if (experienceNote) {
    experienceNote.textContent = isPro
      ? "Pro = manual controls for sizing, cleanup, DPI, hardware, and export tuning."
      : "Beginner = safe guided workflow with clear defaults for upload, action, size, and export.";
  }
  if (!isPro) closeInfoTips();
}

function syncPresetCards() {
  presetCards.forEach((card) => {
    const active = card.dataset.presetChoice === presetSelect.value;
    card.classList.toggle("active", active);
    card.setAttribute("aria-pressed", active ? "true" : "false");
  });
  syncUserPresetActions();
}

function syncWorkflowCards() {
  workflowCards.forEach((card) => {
    const active = card.dataset.workflowChoice === activeWorkflow;
    card.classList.toggle("active", active);
    card.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function syncUserPresetActions() {
  const selected = presetSelect?.value || "";
  deletePresetButton?.classList.toggle("hidden", !userPresetIds.has(selected));
}

function applyVectorPresetDefaults(force = true) {
  const defaults = vectorPresetDefaults[vectorPreset?.value || "logo"] || vectorPresetDefaults.logo;
  const assign = (control, value) => {
    if (control && (force || !control.value)) control.value = value;
  };
  assign(vectorColormode, defaults.colormode);
  assign(vectorHierarchical, defaults.hierarchical);
  assign(vectorMode, defaults.mode);
  assign(vectorFilterSpeckle, defaults.filterSpeckle);
  assign(vectorColorPrecision, defaults.colorPrecision);
  assign(vectorLayerDifference, defaults.layerDifference);
  assign(vectorPathPrecision, defaults.pathPrecision);
}

function applyWorkflow(key, fromUser = false) {
  const workflow = workflowPresets[key] || workflowPresets.shirt;
  activeWorkflow = key in workflowPresets ? key : "shirt";
  if (fromUser) {
    recommendedWorkflow = activeWorkflow;
    hideRecommendation();
  }
  syncWorkflowCards();
  if (workflowNote) workflowNote.textContent = workflow.workflowNote || "Custom workflow selected.";
  if (activeWorkflow === "custom") {
    setExperienceMode("pro");
    if (fromUser) setStatus("Ready", "ready", "Custom workflow selected. Tune settings manually.");
    return;
  }
  if (workflow.presetKey && presetSelect.querySelector(`option[value="${workflow.presetKey}"]`)) {
    presetSelect.value = workflow.presetKey;
  }
  applyPresetValues(workflow, activeWorkflow, fromUser);
}

function applyPresetValues(preset, key = "", fromUser = false) {
  const base = presets.smart;
  const merged = { ...base, ...preset };
  if (merged.tool) setRadioValue("tool", merged.tool);
  setRadioValue("scale", merged.scale);
  setRadioValue("sizing", merged.sizing);
  setRadioValue("cut_mode", merged.cut);
  applyCutPreset(false);
  document.querySelector("#mode").value = merged.mode;
  bgModel.value = merged.model;
  denoise.value = merged.denoise;
  edgeTrim.value = merged.edgeTrim;
  fringeCleanup.value = merged.fringeCleanup;
  innerCleanup.value = merged.innerCleanup;
  outputFormat.value = merged.format;
  if (vectorPreset) vectorPreset.value = merged.vectorPreset || "logo";
  if (merged.vectorColormode || merged.vectorHierarchical || merged.vectorMode || merged.vectorFilterSpeckle || merged.vectorColorPrecision || merged.vectorLayerDifference || merged.vectorPathPrecision) {
    if (vectorColormode) vectorColormode.value = merged.vectorColormode || "color";
    if (vectorHierarchical) vectorHierarchical.value = merged.vectorHierarchical || "stacked";
    if (vectorMode) vectorMode.value = merged.vectorMode || "spline";
    if (vectorFilterSpeckle) vectorFilterSpeckle.value = merged.vectorFilterSpeckle || "4";
    if (vectorColorPrecision) vectorColorPrecision.value = merged.vectorColorPrecision || "6";
    if (vectorLayerDifference) vectorLayerDifference.value = merged.vectorLayerDifference || "16";
    if (vectorPathPrecision) vectorPathPrecision.value = merged.vectorPathPrecision || "3";
  } else {
    applyVectorPresetDefaults(true);
  }
  if (upscaleDevice && merged.upscaleDevice) upscaleDevice.value = merged.upscaleDevice;
  if (backgroundDevice && merged.backgroundDevice) backgroundDevice.value = merged.backgroundDevice;
  resizeMethodSelect.value = merged.resizeMethod || "lanczos";
  targetPresetSelect.value = merged.targetPreset || "";
  targetWidthInput.value = merged.targetWidth || "";
  targetHeightInput.value = merged.targetHeight || "";
  targetFitSelect.value = merged.targetFit || shirtTarget.fit;
  sharpenAmount.value = merged.sharpenAmount || "70";
  dpiInput.value = merged.dpi || "300";
  exportQuality.value = merged.exportQuality || "95";
  canvasPresetSelect.value = "";
  canvasWidthInput.value = merged.canvasWidth || "";
  canvasHeightInput.value = merged.canvasHeight || "";
  canvasAnchorSelect.value = merged.canvasAnchor || "center";
  setCheckbox("alpha-matting", merged.alphaMatting);
  setCheckbox("post-process-mask", merged.postProcess);
  setCheckbox("preserve-interior", merged.preserveInterior);
  setCheckbox("respect-alpha", merged.respectAlpha);
  updateDenoiseValue();
  updateEdgeTrimValue();
  updateFringeCleanupValue();
  updateInnerCleanupValue();
  updateSharpenValue();
  updateExportQualityValue();
  updatePrintSizeNote();
  syncToolUi();
  syncSizingUi(key === "print");
  syncPresetCards();
  presetNote.textContent = merged.note || "Preset loaded.";
  if (selectedFile && fromUser) {
    clearResultOnly();
    validateResolutionForCurrentSettings("Settings updated. Start when ready.");
  }
}

function detectImageIntent(file, size) {
  const name = (file?.name || "").toLowerCase();
  const looksLikeGraphic =
    name.includes("logo") ||
    name.includes("sticker") ||
    name.includes("shirt") ||
    name.includes("graphic") ||
    name.includes("transparent");
  const looksLikeProduct = name.includes("product") || name.includes("mockup") || name.includes("item") || name.includes("listing");
  const looksLikeWeb = name.includes("web") || name.includes("banner") || name.includes("listing");
  const squareish = size?.width && size?.height && Math.abs(size.width - size.height) / Math.max(size.width, size.height) < 0.08;
  if (looksLikeProduct) return { type: "product photo", workflow: "product", tool: "remove-background-upscale", output: "Product listing 1600 x 1600", format: "PNG" };
  if (name.includes("printforge") || name.includes("shop") || name.includes("store")) return { type: "PrintForge product asset", workflow: "printforge", tool: "remove-background-upscale", output: "Shop PNG 3000 x 3000", format: "PNG" };
  if (looksLikeWeb) return { type: "web or listing image", workflow: "web", tool: "upscale", output: "Web listing 1600 x 1600", format: "WebP" };
  if (name.includes("vector") || name.includes("svg") || name.includes("trace")) return { type: "vector-ready logo or decal", workflow: "vector", tool: "vectorize", output: "Scalable SVG", format: "SVG" };
  if (looksLikeGraphic || squareish) return { type: "logo, sticker, or shirt graphic", workflow: "shirt", tool: "remove-background-upscale", output: "Shirt PNG 4500 x 5400", format: "PNG" };
  return { type: "photo or artwork", workflow: "shirt", tool: "remove-background-upscale", output: "Shirt PNG 4500 x 5400", format: "PNG" };
}

function showRecommendation(file, size) {
  if (!recommendationCard || !file) return;
  const intent = detectImageIntent(file, size);
  recommendedWorkflow = intent.workflow || "shirt";
  recommendationTitle.textContent = `Detected: ${intent.type}`;
  recommendationCopy.textContent = `Suggested: ${toolLabel(intent.tool)} | Output: ${intent.output} | Format: ${intent.format}`;
  recommendationCard.classList.remove("hidden");
}

function hideRecommendation() {
  recommendationCard?.classList.add("hidden");
}

function setStatus(message, state = "ready", detail = "") {
  statusEl.textContent = message;
  statusEl.className = `status-badge ${state}`.trim();
  if (detail) statusDetail.textContent = detail;
  syncWorkflowAssistant();
}

function setRuntime(message, state = "neutral") {
  runtimeChip.textContent = message;
  runtimeChip.className = `runtime-badge ${state}`.trim();
}

function populateDeviceSelects(runtime = {}) {
  const options = Array.isArray(runtime.processing_devices) && runtime.processing_devices.length
    ? runtime.processing_devices
    : [{ value: "auto", label: "Auto select" }, { value: "cpu", label: "CPU" }, ...(runtime.cuda_available ? [{ value: "cuda", label: runtime.cuda_device || "NVIDIA CUDA GPU" }] : [])];

  const fill = (select, supportKey) => {
    if (!select) return;
    const previous = select.value || "auto";
    select.replaceChildren();
    options.forEach((option) => {
      const el = document.createElement("option");
      el.value = option.value;
      el.textContent = option.value === "cuda" && runtime.cuda_device ? runtime.cuda_device : option.label;
      el.disabled = option[supportKey] === false;
      select.appendChild(el);
    });
    select.value = Array.from(select.options).some((option) => option.value === previous && !option.disabled) ? previous : "auto";
  };

  fill(upscaleDevice, "upscale_supported");
  fill(backgroundDevice, "background_supported");
}

function setActiveView(view) {
  appViews.forEach((panel) => {
    const active = panel.dataset.view === view;
    panel.hidden = !active;
    panel.classList.toggle("active", active);
  });
  viewTabs.forEach((tab) => {
    const active = tab.dataset.viewTarget === view;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", active ? "true" : "false");
  });
  if (view === "jobs") loadHistory();
  if (view === "diagnostics") loadDiagnostics();
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
  clearBusyStatus();
  processing.classList.remove("hidden");
  setProgress(8, "Preparing job...");
  setStatus("Processing...", "busy", "Preparing server job.");
  processingLabel.textContent = label;
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

function progressPercent(work) {
  return Number(work?.percent ?? work?.progress ?? 0);
}

function closeActiveEventSource() {
  if (activeEventSource) {
    activeEventSource.close();
    activeEventSource = null;
  }
}

function formatDuration(totalSeconds) {
  const elapsed = Math.max(0, Math.floor(Number(totalSeconds) || 0));
  const hours = Math.floor(elapsed / 3600);
  const minutes = String(Math.floor((elapsed % 3600) / 60)).padStart(2, "0");
  const seconds = String(elapsed % 60).padStart(2, "0");
  return hours ? `${hours}:${minutes}:${seconds}` : `${minutes}:${seconds}`;
}

function serverElapsedSeconds(work) {
  if (Number.isFinite(Number(work?.elapsed_seconds))) return Number(work.elapsed_seconds);
  const start = Date.parse(work?.started_at || work?.created_at || "");
  if (!Number.isFinite(start)) return 0;
  const end = Date.parse(work?.finished_at || work?.server_time || new Date().toISOString());
  if (!Number.isFinite(end)) return 0;
  return Math.max(0, Math.floor((end - start) / 1000));
}

function setServerBusyStatus(label, work, detail) {
  processing.classList.remove("hidden");
  const elapsed = serverElapsedSeconds(work);
  processingLabel.textContent = `${label} ${formatDuration(elapsed)}`;
  setStatus("Processing", "busy", detail || "Server processing is running. You can close this browser and return later.");
}

function revoke(url) {
  if (url && url.startsWith("blob:")) URL.revokeObjectURL(url);
}

function absoluteUrl(url, { allowBlob = true } = {}) {
  if (!url) return "";
  try {
    const resolved = new URL(url, window.location.origin);
    const sameOriginHttp = ["http:", "https:"].includes(resolved.protocol) && resolved.origin === window.location.origin;
    const localBlob = allowBlob && resolved.protocol === "blob:" && resolved.origin === window.location.origin;
    return sameOriginHttp || localBlob ? resolved.href : "";
  } catch {
    return "";
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function hasFileDrag(event) {
  return Array.from(event.dataTransfer?.types || []).includes("Files");
}

function bindImageDropTarget(element) {
  if (!element) return;
  let dragDepth = 0;

  element.addEventListener("dragenter", (event) => {
    if (!hasFileDrag(event)) return;
    event.preventDefault();
    event.stopPropagation();
    dragDepth += 1;
    element.classList.add("dragging");
  });

  element.addEventListener("dragover", (event) => {
    if (!hasFileDrag(event)) return;
    event.preventDefault();
    event.stopPropagation();
    if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
    element.classList.add("dragging");
  });

  element.addEventListener("dragleave", (event) => {
    if (!hasFileDrag(event)) return;
    event.preventDefault();
    event.stopPropagation();
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) element.classList.remove("dragging");
  });

  element.addEventListener("drop", (event) => {
    if (!hasFileDrag(event)) return;
    event.preventDefault();
    event.stopPropagation();
    dragDepth = 0;
    element.classList.remove("dragging");
    setFiles(event.dataTransfer.files);
  });
}

function bindGlobalImageDrop() {
  if (!globalDropOverlay) return;
  let dragDepth = 0;

  document.addEventListener("dragenter", (event) => {
    if (!hasFileDrag(event)) return;
    event.preventDefault();
    dragDepth += 1;
    globalDropOverlay.classList.add("active");
  });

  document.addEventListener("dragover", (event) => {
    if (!hasFileDrag(event)) return;
    event.preventDefault();
    if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
    globalDropOverlay.classList.add("active");
  });

  document.addEventListener("dragleave", (event) => {
    if (!hasFileDrag(event)) return;
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) globalDropOverlay.classList.remove("active");
  });

  document.addEventListener("drop", (event) => {
    if (!hasFileDrag(event)) return;
    event.preventDefault();
    dragDepth = 0;
    globalDropOverlay.classList.remove("active");
    setFiles(event.dataTransfer.files);
  });
}

function bindClipboardUpload() {
  document.addEventListener("paste", (event) => {
    const target = event.target;
    const typing = target?.closest?.("input, textarea, select, [contenteditable='true']");
    if (typing) return;
    const files = Array.from(event.clipboardData?.files || []).filter((file) => file.type.startsWith("image/"));
    if (!files.length) return;
    event.preventDefault();
    setFiles(files);
    setStatus("Ready", "ready", files.length > 1 ? `${files.length} pasted images loaded.` : "Pasted image loaded. Choose settings and start.");
  });
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

function setShirtTargetDefaults() {
  targetPresetSelect.value = shirtTarget.preset;
  targetWidthInput.value = shirtTarget.width;
  targetHeightInput.value = shirtTarget.height;
  targetFitSelect.value = shirtTarget.fit;
}

function applyPreset(key, fromUser = false) {
  const preset = presets[key] || presets.smart;
  applyPresetValues(preset, key, fromUser);
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
    setRadioValue("sizing", "target");
    setShirtTargetDefaults();
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
    presetNote.textContent = "Smart Auto detected a graphic-style image and targeted a standard shirt canvas.";
    return;
  }
  setRadioValue("tool", "upscale");
  document.querySelector("#mode").value = "auto";
  setRadioValue("scale", isLarge ? "2" : "4");
  setRadioValue("sizing", "target");
  setShirtTargetDefaults();
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
  presetNote.textContent = "Smart Auto detected a photo-style image and targeted a standard shirt canvas.";
}

function numericInputValue(input) {
  const value = Number(input.value);
  return Number.isFinite(value) && value > 0 ? Math.round(value) : null;
}

function canvasOutputSize(size) {
  if (!size) return null;
  return {
    width: numericInputValue(canvasWidthInput) || size.width,
    height: numericInputValue(canvasHeightInput) || size.height,
  };
}

function fitInsideSize(source, target) {
  const ratio = Math.min(target.width / source.width, target.height / source.height);
  return {
    width: Math.max(1, Math.round(source.width * ratio)),
    height: Math.max(1, Math.round(source.height * ratio)),
  };
}

function coverTargetSize(source, target) {
  const ratio = Math.max(target.width / source.width, target.height / source.height);
  return {
    width: Math.max(1, Math.round(source.width * ratio)),
    height: Math.max(1, Math.round(source.height * ratio)),
  };
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

function plannedOutputSize(size = selectedImageSize) {
  if (!size) return null;
  let content;
  let final;
  if (usesUpscale() && selectedSizingMode() === "target") {
    const target = targetOutputSize(size);
    if (!target) return null;
    const bothTargetDimensions = Boolean(targetWidthInput.value && targetHeightInput.value);
    const fit = bothTargetDimensions ? targetFitSelect.value : "contain";
    if (fit === "contain") {
      content = fitInsideSize(size, target);
      final = content;
    } else if (fit === "pad") {
      content = fitInsideSize(size, target);
      final = target;
    } else if (fit === "crop") {
      content = coverTargetSize(size, target);
      final = target;
    } else {
      content = target;
      final = target;
    }
  } else if (usesUpscale()) {
    const scale = selectedScale();
    content = { width: Math.round(size.width * scale), height: Math.round(size.height * scale) };
    final = content;
  } else {
    content = size;
    final = size;
  }
  return {
    content,
    final: canvasOutputSize(final),
  };
}

function fillTargetDefaults(force = false) {
  if (selectedSizingMode() !== "target") return;
  if (!force && (targetWidthInput.value || targetHeightInput.value)) return;
  setShirtTargetDefaults();
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
    const plan = plannedOutputSize();
    if (!plan) {
      runButton.disabled = true;
      setStatus("Error", "error", "Enter a target width, target height, or both.");
      return false;
    }
    const outputWidth = plan.final.width;
    const outputHeight = plan.final.height;

    if (outputWidth > maxImageDimension || outputHeight > maxImageDimension) {
      runButton.disabled = true;
      setStatus(
        "Error",
        "error",
        `Requested output would be ${outputWidth} x ${outputHeight}. Maximum output is ${resolutionLimitLabel()}. Choose a smaller output size.`,
      );
      return false;
    }

    const upscaleFactor = Math.max(plan.content.width / width, plan.content.height / height);
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
  syncWorkflowAssistant();
  return true;
}

function selectedWorkflowLabel() {
  const activeIntent = document.querySelector(`.intent-card[data-workflow-choice="${activeWorkflow}"] .intent-title`);
  const activeSidebar = document.querySelector(`.workflow-card[data-workflow-choice="${activeWorkflow}"] > span:not(.workflow-icon)`);
  return activeIntent?.textContent?.trim() || activeSidebar?.textContent?.trim() || "Current workflow";
}

function hasResultReady() {
  return resultActions && !resultActions.classList.contains("hidden");
}

function recommendationAvailable() {
  return recommendationCard && !recommendationCard.classList.contains("hidden") && recommendedWorkflow !== activeWorkflow;
}

function syncWorkflowAssistant() {
  if (!workflowAssistant) return;
  const statusState = statusEl?.className || "";
  workflowAssistant.classList.toggle("busy", statusState.includes("busy"));
  workflowAssistant.classList.toggle("complete", statusState.includes("complete"));
  workflowAssistant.classList.toggle("error", statusState.includes("error"));

  if (!selectedFile) {
    assistantStep.textContent = "Step 1 of 4";
    assistantTitle.textContent = "Add an image to begin";
    assistantDetail.textContent = "Drop anywhere, paste from clipboard, or click Upload.";
    assistantPrimary.textContent = "Upload Image";
    assistantPrimary.disabled = false;
    return;
  }

  if (statusState.includes("busy")) {
    assistantStep.textContent = "Step 3 of 4";
    assistantTitle.textContent = "Processing in Docker";
    assistantDetail.textContent = processingDetail?.textContent || "The server job is running. You can come back in History if needed.";
    assistantPrimary.textContent = "Processing...";
    assistantPrimary.disabled = true;
    return;
  }

  if (hasResultReady()) {
    assistantStep.textContent = "Step 4 of 4";
    assistantTitle.textContent = "Result ready";
    assistantDetail.textContent = resultSummary?.textContent || "Download, compare, or reprocess with a quick fix.";
    assistantPrimary.textContent = "Download Result";
    assistantPrimary.disabled = false;
    return;
  }

  if (recommendationAvailable()) {
    assistantStep.textContent = "Step 2 of 4";
    assistantTitle.textContent = "Review the recommendation";
    assistantDetail.textContent = recommendationCopy?.textContent || "Use the suggested workflow or keep your current settings.";
    assistantPrimary.textContent = "Use Recommended";
    assistantPrimary.disabled = false;
    return;
  }

  assistantStep.textContent = "Step 3 of 4";
  assistantTitle.textContent = `${selectedWorkflowLabel()} is ready`;
  assistantDetail.textContent = statusDetail?.textContent || "Start processing when the settings look right.";
  assistantPrimary.textContent = actionText();
  assistantPrimary.disabled = runButton.disabled;
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
      `PNG, JPG, WEBP, or TIFF supported. Max ${resolutionLimitLabel()} per side. Batches up to ${maxBatchFiles} files or ${maxBatchTotalMb} MB.`;
    const runtime = health.runtime || {};
    populateDeviceSelects(runtime);
    const devices = (runtime.processing_devices || []).filter((device) => device.value !== "auto").map((device) => device.label || device.value);
    if (runtime.cuda_available) {
      setRuntime(`GPU: ${runtime.cuda_device || "CUDA"}`, "good");
    } else if (devices.length > 1) {
      setRuntime(`Runtime: ${devices.join(", ")}`, "good");
    } else {
      setRuntime("CPU runtime", "warn");
    }
  } catch {
    setRuntime("Runtime unknown", "warn");
  }
}

async function setFiles(files) {
  const list = Array.from(files || []).filter((file) => file.type.startsWith("image/"));
  if (!list.length) {
    setStatus("Error", "error", "Unsupported file type. Try PNG, JPG, WEBP, or TIFF.");
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
    setStatus("Error", "error", "Unsupported file type. Try PNG, JPG, WEBP, or TIFF.");
    return;
  }

  if (file.size > maxUploadMb * 1024 * 1024) {
    setStatus("Error", "error", `Upload exceeds ${maxUploadMb} MB.`);
    return;
  }

  selectedFile = file;
  if (!selectedFiles.length) selectedFiles = [file];
  selectedImageSize = null;
  resetResultVersions();
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
  hideResultReview();
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
    updatePrintSizeNote();
    showRecommendation(file, size);
  } catch {
    beforeMeta.textContent = `${fileExtension(file)} | ${formatBytes(file.size)}`;
    showRecommendation(file, null);
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

function usesVectorize() {
  return selectedTool() === "vectorize";
}

function selectedCutMode() {
  return document.querySelector('input[name="cut_mode"]:checked')?.value || "balanced";
}

const actionLabels = {
  upscale: "Upscale Image",
  "remove-background": "Remove Background",
  "remove-background-upscale": "Remove Background + Upscale",
  vectorize: "Vectorize to SVG",
};

const actionNotes = {
  upscale: "Upscale enlarges the image and defaults to a padded 4500 x 5400 shirt canvas.",
  "remove-background": "Remove Background cuts out the subject and returns a transparent PNG or WebP.",
  "remove-background-upscale": "Remove Background + Upscale cuts out the subject first, then targets a padded 4500 x 5400 shirt canvas.",
  vectorize: "Vectorize traces clean logos, decals, and artwork into scalable SVG paths.",
};

const toolLabels = {
  upscale: "Upscale",
  "remove-background": "Remove Background",
  "remove-background-upscale": "Remove Background + Upscale",
  vectorize: "Vectorize",
};

function actionText() {
  return actionLabels[selectedTool()] || "Process Image";
}

function toolLabel(value) {
  return toolLabels[value] || value || "Job";
}

function syncActionNote() {
  const actionNote = document.querySelector("#action-note");
  if (actionNote) actionNote.textContent = actionNotes[selectedTool()] || "";
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
  updatePrintSizeNote();
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
  updatePrintSizeNote();
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

  upscaleOnlyFields.forEach((field) => field.classList.toggle("hidden", !usesUpscale()));
  const previousFormat = outputFormat.value || "png";
  outputFormat.replaceChildren();
  const allowedFormats = usesVectorize() ? ["svg"] : usesBackgroundRemoval() ? ["png", "webp"] : ["png", "jpeg", "webp", "tiff"];
  formatOptions
    .filter((option) => allowedFormats.includes(option.value))
    .forEach((option) => {
      const el = document.createElement("option");
      el.value = option.value;
      el.textContent = option.text;
      outputFormat.appendChild(el);
    });
  outputFormat.value = allowedFormats.includes(previousFormat) ? previousFormat : allowedFormats[0];
  exportQualityField.classList.toggle("hidden", !["jpeg", "webp"].includes(outputFormat.value));

  syncRunLabel();
  syncActionNote();
  resultTitle.textContent = "Compare & Result";
  if (!afterUrl) {
    afterMeta.textContent = "No result yet";
  } else {
    clearResultOnly();
  }
  if (selectedFile) {
    validateResolutionForCurrentSettings("Settings updated. Start when ready.");
  }
  updatePrintSizeNote();
}


function setListingPackDownload(url = "") {
  const resolved = absoluteUrl(url);
  if (!listingPackDownload) return;
  if (resolved) {
    listingPackDownload.href = resolved;
    listingPackDownload.download = "";
    listingPackDownload.classList.remove("hidden");
  } else {
    listingPackDownload.removeAttribute("href");
    listingPackDownload.classList.add("hidden");
  }
}

function renderQualityReport(report) {
  if (!resultCheck || !resultCheckList) return;
  resultCheckList.replaceChildren();
  if (!report || !Array.isArray(report.checks)) {
    resultCheck.classList.add("hidden");
    return;
  }
  resultCheckVerdict.textContent = report.verdict || "Review the saved output.";
  report.checks.forEach((check) => {
    const row = document.createElement("div");
    row.className = `result-check-row ${check.status || "info"}`;
    const title = document.createElement("strong");
    title.textContent = check.label || "Check";
    const copy = document.createElement("span");
    copy.textContent = check.message || "Review this item.";
    row.append(title, copy);
    resultCheckList.append(row);
  });
  resultCheck.classList.remove("hidden");
}

function quickFixLabel(value = "") {
  return {
    "remove-leftover-background": "Remove leftover background",
    "fix-white-halo": "Fix white outline / halo",
    "make-edges-smoother": "Make edges smoother",
    "preserve-tiny-details": "Preserve tiny details",
    "make-text-sharper": "Make text sharper",
    "stronger-background-cut": "Stronger background cut",
    "try-safer-mode": "Safer mode",
    "preserve-more-detail": "Preserve tiny details",
    "trim-edge-slightly": "Make edges smoother",
  }[value] || value || "Original result";
}

function resetResultVersions() {
  resultVersionStore = [];
  resultVersionList?.replaceChildren();
  resultVersions?.classList.add("hidden");
}

function addResultVersion(job) {
  if (!job?.download_url) return;
  const key = job.result_job_id || job.id || job.download_url;
  const version = {
    key,
    label: job.quick_fix ? quickFixLabel(job.quick_fix) : resultVersionStore.length ? "Reprocessed result" : "Original result",
    job,
    sourceUrl: job.source_download_url || job.source_url,
    resultUrl: job.download_url,
    filename: job.filename || "result.png",
    summary: jobSummary(job),
    listingPackUrl: job.listing_pack_url,
    qualityReport: job.quality_report,
  };
  const existing = resultVersionStore.findIndex((item) => item.key === key);
  if (existing >= 0) resultVersionStore[existing] = version;
  else resultVersionStore.push(version);
  renderResultVersions(key);
}

function renderResultVersions(activeKey = "") {
  if (!resultVersions || !resultVersionList) return;
  resultVersionList.replaceChildren();
  if (resultVersionStore.length < 2) {
    resultVersions.classList.add("hidden");
    return;
  }
  resultVersionStore.forEach((version, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `version-pill ${version.key === activeKey ? "active" : ""}`.trim();
    button.textContent = `${index + 1}. ${version.label}`;
    button.addEventListener("click", () => {
      openStoredPreview({
        sourceUrl: version.sourceUrl,
        resultUrl: version.resultUrl,
        downloadUrl: version.resultUrl,
        filename: version.filename,
        summary: version.summary,
        listingPackUrl: version.listingPackUrl,
        qualityReport: version.qualityReport,
        job: version.job,
        compare: true,
        preserveVersions: true,
      });
      renderResultVersions(version.key);
    });
    resultVersionList.append(button);
  });
  resultVersions.classList.remove("hidden");
}

function hideResultReview() {
  resultReview?.classList.add("hidden");
  currentResultJob = null;
}

function showResultReview(job) {
  currentResultJob = job || null;
  const queueJobId = job ? job.queue_job_id : currentQueueJobId;
  const displayJobId = queueJobId || job?.id;
  currentQueueJobId = queueJobId || null;
  resultReviewJob.textContent = displayJobId ? `Job ${String(displayJobId).slice(0, 8)}` : "Server job";
  const tool = job?.tool || "";
  const hasBackground = tool === "remove-background" || tool === "remove-background-upscale";
  const canReprocess = Boolean(queueJobId) && tool !== "vectorize";
  const backgroundActions = new Set(["background-left", "halo", "rough-edges"]);
  reviewCheckButtons.forEach((button) => {
    const action = button.dataset.reviewAction || "";
    const needsBackground = backgroundActions.has(action);
    const queuesJob = !["looks-good", "size"].includes(action);
    button.disabled = queuesJob && (!canReprocess || (needsBackground && !hasBackground));
    if (button.disabled) {
      button.title = needsBackground ? "This check requires a queued background-removal result." : "This result cannot be reprocessed from saved history.";
    } else if (queuesJob) {
      button.title = "Queues a new server job using the original source.";
    } else {
      button.removeAttribute("title");
    }
  });
  quickFixButtons.forEach((button) => {
    button.disabled = !hasBackground || !queueJobId;
    button.title = hasBackground && queueJobId ? "Queues a new server job with adjusted background settings." : "Quick fixes require a queued background-removal result.";
  });
  resultReview?.classList.remove("hidden");
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
  setListingPackDownload("");
  renderQualityReport(null);
  resetResultVersions();
  hideResultReview();
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
  updatePrintSizeNote();
  fileLabel.textContent = "Drop your image here";
  fileMeta.textContent = "or click to browse";
  inputChip.classList.add("hidden");
  engineChip.classList.add("hidden");
  resultActions.classList.add("hidden");
  setListingPackDownload("");
  renderQualityReport(null);
  resetResultVersions();
  hideResultReview();
  batchResults.classList.add("hidden");
  batchResults.replaceChildren();
  hideRecommendation();
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

function updateSharpenValue() {
  sharpenValue.textContent = sharpenAmount.value;
}

function updateExportQualityValue() {
  exportQualityValue.textContent = exportQuality.value;
}

function updatePrintSizeNote() {
  const plan = plannedOutputSize();
  const dpi = numericInputValue(dpiInput);
  if (!plan || !dpi) {
    printSizeNote.textContent = "Print size will appear after an image is selected.";
    return;
  }
  const widthIn = plan.final.width / dpi;
  const heightIn = plan.final.height / dpi;
  printSizeNote.textContent = `${plan.final.width} x ${plan.final.height}px at ${dpi} DPI = ${widthIn.toFixed(2)} x ${heightIn.toFixed(2)} in.`;
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
    stage.classList.remove("bg-white", "bg-gray", "bg-dark", "bg-green");
    if (value !== "checker") stage.classList.add(`bg-${value}`);
  });
}

function openStoredPreview({ sourceUrl, resultUrl, downloadUrl, filename, summary, compare = false, listingPackUrl = "", qualityReport = null, job = null, preserveVersions = false }) {
  const resolvedResult = absoluteUrl(resultUrl || downloadUrl);
  const resolvedSource = absoluteUrl(sourceUrl);
  if (!resolvedResult) return;
  setActiveView("workspace");
  hideResultReview();
  if (!preserveVersions) resetResultVersions();

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
  resultTitle.textContent = `Viewing saved result${filename ? `: ${filename}` : ""}`;
  resultSummary.textContent = summary || filename || "Saved result";
  resultDownload.href = afterUrl;
  resultDownload.download = filename || "result.png";
  resultDownload.textContent = "Download Image";
  setListingPackDownload(listingPackUrl);
  renderQualityReport(qualityReport);
  if (job) showResultReview(job);
  resultActions.classList.remove("hidden");
  engineChip.classList.add("hidden");
  differenceKey = "";
  resetCompareDefaults();
  if (beforeUrl && compare) {
    openCompare({ mode: "slider" });
  } else {
    closeCompare();
  }
  setStep(2);
  setStatus("Ready", "ready", `Previewing ${filename || "saved result"}.`);
  document.querySelector(".result-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function jobSummary(job) {
  const output = job.output || {};
  const format = String(output.format || outputFormat.value || "png").toUpperCase();
  if (output.width && output.height) {
    return `${output.width} x ${output.height} ${format}${output.size_bytes ? ` | ${formatBytes(output.size_bytes)}` : ""}`;
  }
  const progress = progressPercent(job);
  const message = job.message ? ` | ${job.message}` : "";
  return `Status: ${job.status || "queued"}${Number.isFinite(progress) ? ` | ${progress}%` : ""}${message}`;
}

function queuedJobToResult(job) {
  const done = job.status === "done" && Boolean(job.download_url);
  return {
    ok: done,
    pending: !done && job.status !== "error",
    status: job.status || "queued",
    name: job.source_filename || job.filename || `Job ${String(job.id || "").slice(0, 8)}`,
    summary: done ? job.filename || jobSummary(job) : jobSummary(job),
    error: job.error || "Failed",
    downloadUrl: job.download_url || "",
    sourceUrl: job.source_download_url || job.source_url || "",
    filename: job.filename || job.source_filename,
  };
}

function showQueuedJobResult(job) {
  if (!job?.download_url) throw new Error("Queued job finished without a result URL.");
  currentQueueJobId = job.queue_job_id || job.id || currentQueueJobId;
  const preserveVersions = Boolean(
    job.parent_queue_job_id
    && resultVersionStore.some((version) => (version.job?.queue_job_id || version.job?.id) === job.parent_queue_job_id),
  );
  openStoredPreview({
    sourceUrl: job.source_download_url || job.source_url,
    resultUrl: job.download_url,
    filename: job.filename || "result.png",
    summary: jobSummary(job),
    listingPackUrl: job.listing_pack_url,
    qualityReport: job.quality_report,
    job,
    compare: true,
    preserveVersions,
  });
  if (job.engine) {
    engineChip.textContent = job.engine;
    engineChip.className = `mini-badge ${String(job.engine).includes("CUDA") ? "good" : ""}`.trim();
    engineChip.classList.remove("hidden");
  }
  setListingPackDownload(job.listing_pack_url);
  renderQualityReport(job.quality_report);
  addResultVersion(job);
  showResultReview(job);
  return queuedJobToResult(job);
}

function batchToResults(batch) {
  return (batch.items || []).map((item) => {
    const done = item.status === "done";
    const progress = progressPercent(item);
    return {
      ok: done,
      pending: !done && item.status !== "error",
      status: item.status || "queued",
      name: item.filename,
      summary: done ? item.result_filename || "Done" : `Status: ${item.status || "queued"}${Number.isFinite(progress) ? ` | ${progress}%` : ""}${item.message ? ` | ${item.message}` : ""}`,
      error: item.error || "Failed",
      downloadUrl: item.result_download_url || "",
      sourceUrl: item.source_url || "",
      filename: item.result_filename || item.filename,
    };
  });
}

function makePreviewThumbs(sourceUrl, resultUrl, label) {
  const safeSourceUrl = absoluteUrl(sourceUrl, { allowBlob: false });
  const safeResultUrl = absoluteUrl(resultUrl, { allowBlob: false });
  const thumbs = document.createElement("button");
  thumbs.className = "preview-thumbs";
  if (!safeSourceUrl) thumbs.classList.add("single");
  thumbs.type = "button";
  thumbs.title = "Preview before and after";
  thumbs.addEventListener("click", () => openStoredPreview({
    sourceUrl: safeSourceUrl,
    resultUrl: safeResultUrl,
    filename: label,
    summary: label,
    compare: Boolean(safeSourceUrl),
  }));

  if (safeSourceUrl) {
    const before = document.createElement("img");
    before.src = safeSourceUrl;
    before.alt = "Original thumbnail";
    thumbs.append(before);
  }

  const after = document.createElement("img");
  after.src = safeResultUrl;
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
    const batchZipUrl = absoluteUrl(batch?.zip_url, { allowBlob: false });
    if (batchZipUrl && (batch.completed || 0) > 0) {
      const zipLink = document.createElement("a");
      zipLink.href = batchZipUrl;
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
    const safeResultUrl = absoluteUrl(result.downloadUrl, { allowBlob: false });
    const safeSourceUrl = absoluteUrl(result.sourceUrl, { allowBlob: false });
    const row = document.createElement("div");
    row.className = `batch-row ${result.ok ? "" : result.pending ? "pending" : "error"}`.trim();
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = result.name;
    const meta = document.createElement("span");
    meta.textContent = result.ok || result.pending ? result.summary : result.error;
    copy.append(title, meta);
    if (historyPreviewEnabled && result.ok && safeResultUrl) {
      copy.append(makePreviewThumbs(safeSourceUrl, safeResultUrl, result.filename || result.name));
    }
    row.append(copy);
    if (result.ok && safeResultUrl) {
      const actions = document.createElement("div");
      actions.className = "job-actions";
      if (historyPreviewEnabled) {
        const preview = document.createElement("button");
        preview.className = "small-button";
        preview.type = "button";
        preview.textContent = "Preview";
        preview.setAttribute("aria-label", `Preview ${result.filename || result.name || "batch result"}`);
        preview.addEventListener("click", () => openStoredPreview({
          sourceUrl: safeSourceUrl,
          resultUrl: safeResultUrl,
          filename: result.filename,
          summary: result.summary,
        }));
        actions.append(preview);
        if (safeSourceUrl) {
          const compare = document.createElement("button");
          compare.className = "small-button";
          compare.type = "button";
          compare.textContent = "Compare";
          compare.setAttribute("aria-label", `Compare ${result.filename || result.name || "batch result"}`);
          compare.addEventListener("click", () => openStoredPreview({
            sourceUrl: safeSourceUrl,
            resultUrl: safeResultUrl,
            filename: result.filename,
            summary: result.summary,
            compare: true,
          }));
          actions.append(compare);
        }
      }
      const link = document.createElement("a");
      link.href = safeResultUrl;
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

function historySearchTextForJob(job) {
  const output = job.output || {};
  return [
    job.id,
    job.display_name,
    job.note,
    job.filename,
    job.source_filename,
    job.tool,
    job.status,
    job.queue_job_id,
    output.format,
    output.width,
    output.height,
  ].filter(Boolean).join(" ").toLowerCase();
}

function historySearchTextForBatch(batch) {
  const itemNames = (batch.items || [])
    .map((item) => [item.filename, item.result_filename, item.status].filter(Boolean).join(" "))
    .join(" ");
  return [batch.id, batch.tool, batch.status, itemNames].filter(Boolean).join(" ").toLowerCase();
}

function historyTimestamp(item) {
  const value = new Date(item.created_at || 0).getTime();
  return Number.isFinite(value) ? value : 0;
}

function historySize(item) {
  if (item.output?.size_bytes) return item.output.size_bytes;
  return (item.items || []).reduce((total, batchItem) => total + (batchItem.size_bytes || 0), 0);
}

function selectedHistoryFilter() {
  return historyFilter?.value || "all";
}

function selectedHistorySearch() {
  return (historySearch?.value || "").trim().toLowerCase();
}

function selectedHistorySort() {
  return historySort?.value || "newest";
}

function filterHistoryItems(items, kind) {
  const filter = selectedHistoryFilter();
  const query = selectedHistorySearch();
  return items.filter((item) => {
    const tool = item.tool || "";
    const matchesFilter =
      filter === "all" ||
      (filter === "batch" && kind === "batch") ||
      (filter !== "batch" && tool === filter);
    if (!matchesFilter) return false;
    if (!query) return true;
    const searchable = kind === "batch" ? historySearchTextForBatch(item) : historySearchTextForJob(item);
    return searchable.includes(query);
  });
}

function sortHistoryItems(items) {
  const sort = selectedHistorySort();
  return [...items].sort((a, b) => {
    if (sort === "oldest") return historyTimestamp(a) - historyTimestamp(b);
    if (sort === "size") return historySize(b) - historySize(a);
    if (sort === "tool") return String(a.tool || "").localeCompare(String(b.tool || ""));
    return historyTimestamp(b) - historyTimestamp(a);
  });
}

function historyStatusBadge(status = "completed") {
  const badge = document.createElement("span");
  badge.className = `status-pill ${status === "failed" || status === "error" ? "error" : status === "completed" || status === "complete" || status === "done" ? "complete" : "pending"}`;
  badge.textContent = status === "done" ? "Completed" : status || "Completed";
  return badge;
}

function highlightHistorySelection(key) {
  document.querySelectorAll("[data-history-key]").forEach((row) => {
    row.classList.toggle("selected", row.dataset.historyKey === key);
  });
}

function renderHistory(jobs, batches = []) {
  historyList.replaceChildren();
  const visibleBatches = sortHistoryItems(filterHistoryItems(batches, "batch"));
  const visibleJobs = sortHistoryItems(filterHistoryItems(jobs, "job"));

  if (!jobs.length && !batches.length) {
    const empty = document.createElement("p");
    empty.className = "muted-copy";
    empty.textContent = "No history yet. Process images and the outputs will appear here.";
    historyList.append(empty);
    return;
  }

  if (!visibleJobs.length && !visibleBatches.length) {
    const empty = document.createElement("p");
    empty.className = "muted-copy";
    empty.textContent = "No history items match the current search or filter.";
    historyList.append(empty);
    return;
  }

  if (visibleBatches.length) {
    const batchHeading = document.createElement("h3");
    batchHeading.className = "history-section-title";
    batchHeading.textContent = `Batch Jobs (${visibleBatches.length})`;
    historyList.append(batchHeading);
    visibleBatches.forEach((batch) => {
      const batchKey = `batch-${batch.id}`;
      const card = document.createElement("div");
      card.className = "batch-card";
      card.dataset.historyKey = batchKey;
      const header = document.createElement("div");
      header.className = "batch-card-header";
      const copy = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = `Batch ${String(batch.id || "").slice(0, 8)}`;
      title.title = batch.id || "Batch";
      const meta = document.createElement("span");
      meta.textContent =
        `${toolLabel(batch.tool)} | ${batch.completed || 0}/${batch.total || 0} complete | ${formatDate(batch.created_at)}`;
      const statusLine = document.createElement("div");
      statusLine.className = "history-meta-line";
      statusLine.append(historyStatusBadge(batch.status || "queued"), meta);
      copy.append(title, statusLine);
      const actions = document.createElement("div");
      actions.className = "job-actions";
      const batchZipUrl = absoluteUrl(batch.zip_url, { allowBlob: false });
      if (batchZipUrl && (batch.completed || 0) > 0) {
        const zipLink = document.createElement("a");
        zipLink.href = batchZipUrl;
        zipLink.textContent = "Download ZIP";
        actions.append(zipLink);
      }
      const openButton = document.createElement("button");
      openButton.className = "small-button";
      openButton.type = "button";
      openButton.textContent = "Open";
      openButton.addEventListener("click", () => {
        currentBatchId = batch.id;
        highlightHistorySelection(batchKey);
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

  if (visibleJobs.length) {
    const jobHeading = document.createElement("h3");
    jobHeading.className = "history-section-title";
    jobHeading.textContent = `Image Jobs (${visibleJobs.length})`;
    historyList.append(jobHeading);
  }

  visibleJobs.forEach((job) => {
    const jobKey = `job-${job.id}`;
    const row = document.createElement("div");
    row.className = "job-row";
    row.dataset.historyKey = jobKey;
    const status = job.status || (job.download_url ? "done" : "queued");
    const isDone = status === "done" || status === "completed";
    const downloadUrl = absoluteUrl(job.download_url, { allowBlob: false });
    const sourceUrl = absoluteUrl(job.source_download_url, { allowBlob: false });
    const packUrl = absoluteUrl(job.listing_pack_url, { allowBlob: false });
    const canDownload = Boolean(downloadUrl);
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    const displayTitle = job.display_name || job.filename || job.source_filename || "Processed image";
    title.textContent = displayTitle;
    title.title = job.filename && job.display_name ? `${job.display_name} | File: ${job.filename}` : displayTitle;
    const meta = document.createElement("span");
    const output = job.output || {};
    meta.textContent = canDownload
      ? `${toolLabel(job.tool)} | ${output.width || "?"} x ${output.height || "?"} ${String(output.format || "").toUpperCase()} | ${formatBytes(output.size_bytes || 0)} | ${formatDate(job.created_at)}`
      : `${toolLabel(job.tool)} | ${status} | ${Number(job.progress || 0)}% | ${formatDate(job.created_at)}`;
    const statusLine = document.createElement("div");
    statusLine.className = "history-meta-line";
    statusLine.append(historyStatusBadge(status), meta);
    copy.append(title, statusLine);
    if (job.note) {
      const note = document.createElement("p");
      note.className = "history-note";
      note.textContent = job.note;
      copy.append(note);
    }
    if (historyPreviewEnabled && downloadUrl) {
      copy.append(makePreviewThumbs(sourceUrl, downloadUrl, job.filename || job.source_filename || "Processed image"));
    }
    const actions = document.createElement("div");
    actions.className = "job-actions";
    if (canDownload) {
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = job.filename || "result.png";
      link.textContent = "Download";
      const previewButton = document.createElement("button");
      previewButton.className = "small-button";
      previewButton.type = "button";
      previewButton.textContent = "Open in Viewer";
      previewButton.setAttribute("aria-label", `Preview ${job.filename || job.source_filename || "processed image"}`);
      previewButton.addEventListener("click", () => {
        highlightHistorySelection(jobKey);
        openStoredPreview({
          sourceUrl,
          resultUrl: downloadUrl,
          filename: job.filename || "result.png",
          summary: meta.textContent,
          listingPackUrl: packUrl,
          qualityReport: job.quality_report,
          job,
          compare: false,
        });
      });
      actions.append(previewButton);
      const editButton = document.createElement("button");
      editButton.className = "small-button";
      editButton.type = "button";
      editButton.textContent = "Name / Note";
      editButton.addEventListener("click", () => editJobMetadata(job));
      actions.append(editButton);
      if (packUrl) {
        const packLink = document.createElement("a");
        packLink.href = packUrl;
        packLink.download = "";
        packLink.textContent = "PrintForge Pack";
        actions.append(packLink);
      }
      if (sourceUrl) {
        const compareButton = document.createElement("button");
        compareButton.className = "small-button";
        compareButton.type = "button";
        compareButton.textContent = "Compare";
        compareButton.setAttribute("aria-label", `Compare ${job.filename || job.source_filename || "processed image"}`);
        compareButton.addEventListener("click", () => {
          highlightHistorySelection(jobKey);
          openStoredPreview({
            sourceUrl,
            resultUrl: downloadUrl,
            filename: job.filename || "result.png",
            summary: meta.textContent,
            listingPackUrl: packUrl,
            qualityReport: job.quality_report,
            job,
            compare: true,
          });
        });
        actions.append(compareButton);
      }
      actions.append(link);
    } else if (status === "error" && job.queue_job_id) {
      const retryButton = document.createElement("button");
      retryButton.className = "small-button";
      retryButton.type = "button";
      retryButton.textContent = "Retry";
      retryButton.addEventListener("click", async () => {
        try {
          const response = await fetch(`/api/jobs/${encodeURIComponent(job.queue_job_id)}/retry`, { method: "POST" });
          if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            throw new Error(body.error || body.detail || `Retry failed with ${response.status}`);
          }
          const queued = (await response.json()).job;
          setStatus("Processing", "busy", `Retry queued on server as ${String(queued.id || "").slice(0, 8)}.`);
          await loadHistory();
          resumeQueuedJob(queued);
        } catch (error) {
          setStatus("Error", "error", error.message || "Could not retry job.");
        }
      });
      actions.append(retryButton);
    } else if (!isDone) {
      const resumeButton = document.createElement("button");
      resumeButton.className = "small-button";
      resumeButton.type = "button";
      resumeButton.textContent = "Watch";
      resumeButton.addEventListener("click", () => resumeQueuedJob(job));
      actions.append(resumeButton);
    }
    const deleteButton = document.createElement("button");
    deleteButton.className = "small-button danger-button";
    deleteButton.type = "button";
    deleteButton.textContent = "Delete";
    deleteButton.disabled = status === "running";
    deleteButton.title = status === "running" ? "Running server jobs can be deleted after they finish or fail." : "Delete this history item";
    deleteButton.addEventListener("click", () => deleteSavedJob(job));
    actions.append(deleteButton);
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
    historyJobsCache = jobsBody.jobs || [];
    historyBatchesCache = batchesBody.batches || [];
    renderHistory(historyJobsCache, historyBatchesCache);
  } catch {
    historyList.innerHTML = '<p class="muted-copy">Could not load history.</p>';
  }
}

async function resumeRunningJobs() {
  try {
    const [jobsResponse, batchesResponse] = await Promise.all([
      fetch("/api/jobs?limit=20", { cache: "no-store" }),
      fetch("/api/batches?limit=10", { cache: "no-store" }),
    ]);
    const jobsBody = jobsResponse.ok ? await jobsResponse.json() : { jobs: [] };
    const batchesBody = batchesResponse.ok ? await batchesResponse.json() : { batches: [] };
    const activeJob = (jobsBody.jobs || []).find((job) => ["queued", "running"].includes(job.status));
    if (activeJob) {
      resumeQueuedJob(activeJob);
      return;
    }
    const activeBatch = (batchesBody.batches || []).find((batch) => ["queued", "running"].includes(batch.status));
    if (activeBatch) {
      resumeBatch(activeBatch);
    }
  } catch {
    // History still loads manually if the lightweight resume check fails.
  }
}

function isBatchDone(batch) {
  return ["done", "completed"].includes(batch?.status);
}

function applyBatchProgress(batch) {
  const done = batch.completed || 0;
  const failed = batch.failed || 0;
  const total = batch.total || 0;
  const progress = progressPercent(batch);
  setServerBusyStatus(
    batch.status === "queued" ? "Queued on server" : "Processing batch on server",
    batch,
    batch.message || `Batch ${String(batch.id || "").slice(0, 8)}: ${done + failed}/${total} complete. Server elapsed ${formatDuration(serverElapsedSeconds(batch))}.`,
  );
  setProgress(Number.isFinite(progress) ? progress : total ? Math.round(((done + failed) / total) * 100) : 0, batch.message || `Batch progress: ${done + failed}/${total}`);
  renderBatchResults(batchToResults(batch), batch);
}

function applyQueuedJobProgress(job) {
  const status = job.status || "queued";
  const progress = progressPercent(job);
  setServerBusyStatus(
    status === "queued" ? "Queued on server" : "Processing on server",
    job,
    job.message || `Server job ${String(job.id || "").slice(0, 8)}: ${status}. Server elapsed ${formatDuration(serverElapsedSeconds(job))}.`,
  );
  setProgress(progress, job.message || `Server job ${String(job.id || "").slice(0, 8)}: ${status}`);
  renderBatchResults([queuedJobToResult(job)]);
}

function parseEventPayload(event) {
  try {
    return JSON.parse(event.data || "{}");
  } catch {
    return {};
  }
}

function streamBatch(batchId, fallback) {
  if (!("EventSource" in window)) return fallback();
  closeActiveEventSource();
  return new Promise((resolve, reject) => {
    let settled = false;
    const source = new EventSource(`/api/events?batch_id=${encodeURIComponent(batchId)}`);
    activeEventSource = source;

    const finish = (callback, value) => {
      if (settled) return;
      settled = true;
      source.close();
      if (activeEventSource === source) activeEventSource = null;
      callback(value);
    };

    const handle = (event) => {
      const payload = parseEventPayload(event);
      const batch = payload.batch;
      if (!batch) return;
      applyBatchProgress(batch);
      if (isBatchDone(batch)) finish(resolve, batch);
      if (batch.status === "error") finish(reject, new Error(batch.error || batch.message || "Batch job failed."));
    };

    source.addEventListener("snapshot", handle);
    source.addEventListener("progress", handle);
    source.onerror = () => {
      if (settled) return;
      settled = true;
      source.close();
      if (activeEventSource === source) activeEventSource = null;
      fallback().then(resolve).catch(reject);
    };
  });
}

function streamQueuedJob(jobId, fallback) {
  if (!("EventSource" in window)) return fallback();
  closeActiveEventSource();
  return new Promise((resolve, reject) => {
    let settled = false;
    const source = new EventSource(`/api/events?job_id=${encodeURIComponent(jobId)}`);
    activeEventSource = source;

    const finish = (callback, value) => {
      if (settled) return;
      settled = true;
      source.close();
      if (activeEventSource === source) activeEventSource = null;
      callback(value);
    };

    const handle = (event) => {
      const payload = parseEventPayload(event);
      const job = payload.job;
      if (!job) return;
      applyQueuedJobProgress(job);
      if (job.status === "done") finish(resolve, job);
      if (job.status === "error") finish(reject, new Error(job.error || job.message || "Server job failed."));
    };

    source.addEventListener("snapshot", handle);
    source.addEventListener("progress", handle);
    source.onerror = () => {
      if (settled) return;
      settled = true;
      source.close();
      if (activeEventSource === source) activeEventSource = null;
      fallback().then(resolve).catch(reject);
    };
  });
}

async function pollBatchHttp(batchId) {
  while (true) {
    const response = await fetch(`/api/batches/${encodeURIComponent(batchId)}`, { cache: "no-store" });
    if (!response.ok) throw new Error("Batch status failed");
    const batch = await response.json();
    applyBatchProgress(batch);
    if (isBatchDone(batch)) return batch;
    if (batch.status === "error") throw new Error(batch.error || batch.message || "Batch job failed.");
    await delay(1200);
  }
}

async function pollBatch(batchId) {
  return streamBatch(batchId, () => pollBatchHttp(batchId));
}

async function pollQueuedJobHttp(jobId) {
  while (true) {
    const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`, { cache: "no-store" });
    if (!response.ok) throw new Error("Job status failed");
    const job = await response.json();
    const status = job.status || "queued";
    applyQueuedJobProgress(job);
    if (status === "done") return job;
    if (status === "error") throw new Error(job.error || "Server job failed.");
    await delay(1200);
  }
}

async function pollQueuedJob(jobId) {
  return streamQueuedJob(jobId, () => pollQueuedJobHttp(jobId));
}

async function resumeQueuedJob(job) {
  const jobId = job.queue_job_id || job.id;
  if (!jobId) return;
  currentQueueJobId = jobId;
  setActiveView("workspace");
  runButton.disabled = true;
  setServerBusyStatus("Processing on server", job, `Server job ${String(jobId).slice(0, 8)} is running. You can close this browser and return later.`);
  setStatus("Processing", "busy", `Server job ${String(jobId).slice(0, 8)} is running. You can close this browser and return later.`);
  try {
    const completed = await pollQueuedJob(jobId);
    showQueuedJobResult(completed);
    await loadHistory();
    await loadDiagnostics();
    setStatus("Complete", "complete", "Server job complete. Your image is ready in History.");
  } catch (error) {
    setStatus("Error", "error", error.message || "Server job failed.");
    await loadHistory();
  } finally {
    clearBusyStatus();
    runButton.disabled = false;
    syncRunLabel();
  }
}

async function resumeBatch(batch) {
  const batchId = batch.id;
  if (!batchId) return;
  currentBatchId = batchId;
  setActiveView("workspace");
  runButton.disabled = true;
  setServerBusyStatus("Processing batch on server", batch, `Batch ${String(batchId).slice(0, 8)} is running. You can close this browser and return later.`);
  renderBatchResults(batchToResults(batch), batch);
  try {
    const completed = await pollBatch(batchId);
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
  } catch (error) {
    setStatus("Error", "error", error.message || "Batch job failed.");
    await loadHistory();
  } finally {
    clearBusyStatus();
    runButton.disabled = false;
    syncRunLabel();
  }
}


async function editJobMetadata(job) {
  const currentName = job.display_name || job.filename || job.source_filename || "";
  const displayName = window.prompt("Saved asset name", currentName);
  if (displayName === null) return;
  const note = window.prompt("Optional note for Recent Assets", job.note || "");
  if (note === null) return;
  try {
    const response = await fetch(`/api/jobs/${encodeURIComponent(job.id)}/metadata`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ display_name: displayName, note }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || body.error || "Could not save name/note.");
    setStatus("Ready", "ready", "Saved asset name and note updated.");
    await loadHistory();
  } catch (error) {
    setStatus("Error", "error", error.message || "Could not save name/note.");
  }
}

async function deleteSavedJob(job) {
  const name = job.filename || job.source_filename || "this saved job";
  const confirmed = window.confirm(
    `Delete "${name}" from History? This removes the saved output file and its history entry.`,
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
    "Clear all recent history? This removes every saved output file and history entry from Docker storage.",
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
    setStatus("Ready", "ready", "Recent history cleared.");
    await loadHistory();
    await loadDiagnostics();
  } catch (error) {
    setStatus("Error", "error", error.message || "Could not clear history.");
  }
}

function renderDiagnostics(data) {
  const runtime = data.runtime || {};
  const storage = data.storage || {};
  const limits = data.limits || {};
  const queue = data.queue || {};
  const workerCount = Array.isArray(queue.workers) ? queue.workers.length : 0;
  const rows = [
    ["Hardware", runtime.cuda_available ? `NVIDIA GPU: ${runtime.cuda_device || "CUDA"}` : "CPU runtime"],
    ["Queue", queue.redis_connected ? `Redis ready | ${queue.queue_depth || 0} waiting | ${queue.started_count || 0} running | ${workerCount} worker${workerCount === 1 ? "" : "s"}` : `Redis unavailable${queue.error ? ` | ${queue.error}` : ""}`],
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

function settingsSnapshotFromUi() {
  return {
    note: `User preset: ${toolLabel(selectedTool())}`,
    tool: selectedTool(),
    mode: document.querySelector("#mode").value,
    model: bgModel.value,
    cut: selectedCutMode(),
    scale: String(selectedScale()),
    sizing: selectedSizingMode(),
    targetPreset: targetPresetSelect.value,
    targetWidth: targetWidthInput.value,
    targetHeight: targetHeightInput.value,
    targetFit: targetFitSelect.value,
    resizeMethod: resizeMethodSelect.value,
    sharpenAmount: sharpenAmount.value,
    dpi: dpiInput.value,
    exportQuality: exportQuality.value,
    canvasWidth: canvasWidthInput.value,
    canvasHeight: canvasHeightInput.value,
    canvasAnchor: canvasAnchorSelect.value,
    denoise: denoise.value,
    edgeTrim: edgeTrim.value,
    fringeCleanup: fringeCleanup.value,
    innerCleanup: innerCleanup.value,
    alphaMatting: document.querySelector("#alpha-matting").checked,
    postProcess: document.querySelector("#post-process-mask").checked,
    preserveInterior: document.querySelector("#preserve-interior").checked,
    respectAlpha: document.querySelector("#respect-alpha").checked,
    upscaleDevice: upscaleDevice?.value || "auto",
    backgroundDevice: backgroundDevice?.value || "auto",
    vectorPreset: vectorPreset?.value || "logo",
    vectorColormode: vectorColormode?.value || "color",
    vectorHierarchical: vectorHierarchical?.value || "stacked",
    vectorMode: vectorMode?.value || "spline",
    vectorFilterSpeckle: vectorFilterSpeckle?.value || "4",
    vectorColorPrecision: vectorColorPrecision?.value || "6",
    vectorLayerDifference: vectorLayerDifference?.value || "16",
    vectorPathPrecision: vectorPathPrecision?.value || "3",
    format: outputFormat.value,
  };
}

function userPresetDescription(snapshot) {
  const target = snapshot.sizing === "target" && (snapshot.targetWidth || snapshot.targetHeight)
    ? `${snapshot.targetWidth || "auto"} x ${snapshot.targetHeight || "auto"}`
    : `${snapshot.scale || "1"}x`;
  return `${toolLabel(snapshot.tool)} | ${target} | ${String(snapshot.format || "png").toUpperCase()}`;
}

function removeUserPresetUi() {
  userPresetIds.forEach((id) => {
    delete presets[id];
  });
  userPresetIds = new Set();
  presetSelect.querySelectorAll("option[data-user-preset='true']").forEach((option) => option.remove());
  presetCardGrid?.querySelectorAll(".user-preset-card").forEach((card) => card.remove());
  presetCards = document.querySelectorAll("[data-preset-choice]");
}

function normalizeServerPreset(preset) {
  const raw = preset.settings || {};
  const base = raw.preset_key && presets[raw.preset_key] ? presets[raw.preset_key] : presets.smart;
  return {
    ...base,
    ...raw,
    note: preset.description || raw.note || `Saved preset: ${preset.name}`,
  };
}

function addUserPresetUi(preset) {
  const id = String(preset.id || "");
  if (!id) return;
  userPresetIds.add(id);
  presets[id] = normalizeServerPreset(preset);

  const option = document.createElement("option");
  option.value = id;
  option.dataset.userPreset = "true";
  option.textContent = preset.name || "Saved preset";
  presetSelect.append(option);

  const card = document.createElement("button");
  card.className = "preset-card user-preset-card";
  card.type = "button";
  card.dataset.presetChoice = id;
  card.setAttribute("aria-pressed", "false");
  const title = document.createElement("span");
  title.textContent = preset.name || "Saved preset";
  const copy = document.createElement("small");
  copy.textContent = preset.description || "Saved server preset.";
  card.append(title, copy);
  presetCardGrid?.append(card);
}

async function loadPresets() {
  try {
    const response = await fetch("/api/presets", { cache: "no-store" });
    if (!response.ok) throw new Error("presets failed");
    const data = await response.json();
    removeUserPresetUi();
    (data.presets || []).filter((preset) => preset.kind === "user").forEach(addUserPresetUi);
    presetCards = document.querySelectorAll("[data-preset-choice]");
    syncPresetCards();
  } catch {
    setStatus("Ready", "ready", "Could not load saved presets. Built-in presets are still available.");
  }
}

async function saveCurrentPreset() {
  const name = (presetNameInput?.value || "").trim();
  if (!name) {
    setStatus("Error", "error", "Enter a preset name first.");
    presetNameInput?.focus();
    return;
  }
  const snapshot = settingsSnapshotFromUi();
  try {
    savePresetButton.disabled = true;
    const response = await fetch("/api/presets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        description: userPresetDescription(snapshot),
        tool: snapshot.tool,
        settings: snapshot,
      }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || body.error || "Could not save preset.");
    await loadPresets();
    presetSelect.value = body.preset.id;
    syncPresetCards();
    presetNameInput.value = "";
    setStatus("Ready", "ready", `Saved preset "${body.preset.name}".`);
  } catch (error) {
    setStatus("Error", "error", error.message || "Could not save preset.");
  } finally {
    savePresetButton.disabled = false;
  }
}

async function deleteSelectedPreset() {
  const id = presetSelect.value;
  if (!userPresetIds.has(id)) return;
  if (!window.confirm("Delete this saved preset?")) return;
  try {
    deletePresetButton.disabled = true;
    const response = await fetch(`/api/presets/${encodeURIComponent(id)}`, { method: "DELETE" });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || body.error || "Could not delete preset.");
    presetSelect.value = "smart";
    await loadPresets();
    applyPreset("smart", true);
    setStatus("Ready", "ready", "Saved preset deleted.");
  } catch (error) {
    setStatus("Error", "error", error.message || "Could not delete preset.");
  } finally {
    deletePresetButton.disabled = false;
  }
}

function handleReviewAction(action) {
  if (!afterUrl) return;
  if (action === "looks-good") {
    setStatus("Complete", "complete", "Great — use Download Image or Create PrintForge Pack when ready.");
    return;
  }
  const fixMap = {
    "background-left": "remove-leftover-background",
    halo: "fix-white-halo",
    "rough-edges": "make-edges-smoother",
    "detail-damage": "try-safer-mode",
  };
  if (fixMap[action]) {
    reprocessWithQuickFix(fixMap[action]);
    return;
  }
  if (action === "size") {
    resultActions.scrollIntoView({ behavior: "smooth", block: "nearest" });
    setStatus("Ready", "ready", resultSummary.textContent || "Check the output size and format.");
  }
}

async function reprocessWithQuickFix(quickFix) {
  const tool = currentResultJob?.tool || "";
  const backgroundFixes = new Set(["remove-leftover-background", "fix-white-halo", "make-edges-smoother", "trim-edge-slightly"]);
  const hasBackground = tool === "remove-background" || tool === "remove-background-upscale";
  if (tool === "vectorize" || (backgroundFixes.has(quickFix) && !hasBackground)) {
    setStatus("Error", "error", "That quick fix is not compatible with this result.");
    return;
  }
  const jobId = currentResultJob?.queue_job_id || currentQueueJobId;
  if (!jobId) {
    setStatus("Error", "error", "No server queued job is available to reprocess.");
    return;
  }
  const previousResultJob = currentResultJob;
  try {
    quickFixButtons.forEach((button) => {
      button.disabled = true;
    });
    runButton.disabled = true;
    hideResultReview();
    setBusyStatus("Reprocessing on server");
    setStatus("Processing", "busy", "Quick fix queued on the server. You can close this browser and return later.");
    const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/reprocess`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quick_fix: quickFix }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || body.error || "Could not queue quick fix.");
    const queuedJob = body.job;
    currentQueueJobId = queuedJob.id;
    renderBatchResults([queuedJobToResult(queuedJob)]);
    setServerBusyStatus(
      "Reprocessing on server",
      queuedJob,
      `Quick fix queued as job ${String(queuedJob.id || "").slice(0, 8)}. Docker keeps processing without the browser.`,
    );
    const completed = await pollQueuedJob(queuedJob.id);
    showQueuedJobResult(completed);
    renderBatchResults([]);
    await loadHistory();
    await loadDiagnostics();
    setStatus("Complete", "complete", "Quick fix complete. Review the updated result.");
  } catch (error) {
    setStatus("Error", "error", error.message || "Quick fix failed.");
  } finally {
    clearBusyStatus();
    if (selectedFile && validateResolutionForCurrentSettings(null)) {
      runButton.disabled = false;
    }
    syncRunLabel();
    if (currentResultJob || previousResultJob) showResultReview(currentResultJob || previousResultJob);
  }
}

fileInput.addEventListener("change", () => setFiles(fileInput.files));

presetSelect.addEventListener("change", () => {
  applyPreset(presetSelect.value, true);
  syncPresetCards();
});

presetCardGrid?.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target : null;
  const card = target?.closest("[data-preset-choice]");
  if (card instanceof HTMLElement) {
    presetSelect.value = card.dataset.presetChoice || "smart";
    applyPreset(presetSelect.value, true);
    syncPresetCards();
  }
});

workflowCards.forEach((card) => {
  card.addEventListener("click", () => {
    applyWorkflow(card.dataset.workflowChoice || "shirt", true);
    setStatus("Ready", "ready", "Workflow settings applied. Start when ready.");
    if (card.classList.contains("intent-card")) {
      const target = selectedFile ? form : dropzone;
      window.setTimeout(() => target?.scrollIntoView({ behavior: "smooth", block: "start" }), 60);
    }
  });
});

savePresetButton?.addEventListener("click", saveCurrentPreset);
deletePresetButton?.addEventListener("click", deleteSelectedPreset);

experienceInputs.forEach((input) => input.addEventListener("change", syncExperienceMode));

advancedWorkflowCard?.addEventListener("click", () => {
  setExperienceMode("pro");
  advancedWorkflowCard.classList.add("active");
  window.setTimeout(() => advancedWorkflowCard.classList.remove("active"), 700);
});

useRecommendation?.addEventListener("click", () => {
  if (!selectedFile) return;
  applyWorkflow(recommendedWorkflow || "shirt", true);
  syncPresetCards();
  syncToolUi();
  setStatus("Ready", "ready", "Recommended workflow applied. Start when ready.");
});

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
    updatePrintSizeNote();
  });
});
if (targetPresetSelect) {
  targetPresetSelect.addEventListener("change", () => applyTargetPreset(targetPresetSelect.value));
}

targetFitSelect.addEventListener("change", () => {
  if (selectedFile) {
    clearResultOnly();
    validateResolutionForCurrentSettings("Target fit updated. Start when ready.");
  }
  updatePrintSizeNote();
});

resizeMethodSelect.addEventListener("change", () => {
  if (selectedFile) {
    clearResultOnly();
    setStatus("Ready", "ready", "Resize method updated. Start when ready.");
  }
});

sharpenAmount.addEventListener("input", () => {
  updateSharpenValue();
  if (selectedFile) {
    clearResultOnly();
    setStatus("Ready", "ready", "Output sharpening updated. Start when ready.");
  }
});

function applyCanvasPreset(value) {
  if (!value) {
    canvasWidthInput.value = "";
    canvasHeightInput.value = "";
  } else {
    const [w, h] = String(value).split("x").map((n) => Number.parseInt(n, 10));
    if (Number.isFinite(w) && Number.isFinite(h)) {
      canvasWidthInput.value = String(w);
      canvasHeightInput.value = String(h);
    }
  }
  if (selectedFile) {
    clearResultOnly();
    validateResolutionForCurrentSettings("Canvas updated. Start when ready.");
  }
  updatePrintSizeNote();
}

canvasPresetSelect.addEventListener("change", () => applyCanvasPreset(canvasPresetSelect.value));

[canvasWidthInput, canvasHeightInput].forEach((input) => {
  input.addEventListener("input", () => {
    canvasPresetSelect.value = "";
    if (selectedFile) {
      clearResultOnly();
      validateResolutionForCurrentSettings("Canvas updated. Start when ready.");
    }
    updatePrintSizeNote();
  });
});

canvasAnchorSelect.addEventListener("change", () => {
  if (selectedFile) {
    clearResultOnly();
    setStatus("Ready", "ready", "Canvas anchor updated. Start when ready.");
  }
});

dpiInput.addEventListener("input", updatePrintSizeNote);

exportQuality.addEventListener("input", () => {
  updateExportQualityValue();
  if (selectedFile && ["jpeg", "webp"].includes(outputFormat.value)) {
    clearResultOnly();
    setStatus("Ready", "ready", "Export quality updated. Start when ready.");
  }
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
outputFormat.addEventListener("change", () => {
  exportQualityField.classList.toggle("hidden", !["jpeg", "webp"].includes(outputFormat.value));
  if (selectedFile) {
    clearResultOnly();
    setStatus("Ready", "ready", "File format updated. Start when ready.");
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
vectorPreset?.addEventListener("change", () => applyVectorPresetDefaults(true));
[vectorPreset, vectorColormode, vectorHierarchical, vectorMode, vectorFilterSpeckle, vectorColorPrecision, vectorLayerDifference, vectorPathPrecision]
  .filter(Boolean)
  .forEach((control) => {
    control.addEventListener("change", () => {
      if (selectedFile && usesVectorize()) {
        clearResultOnly();
        setStatus("Ready", "ready", "Vector trace settings updated. Start when ready.");
      }
    });
    control.addEventListener("input", () => {
      if (selectedFile && usesVectorize()) {
        clearResultOnly();
        setStatus("Ready", "ready", "Vector trace settings updated. Start when ready.");
      }
    });
  });
cutModeInputs.forEach((input) => input.addEventListener("change", applyCutPreset));
processAnother.addEventListener("click", clearWorkspace);
compareToggle.addEventListener("click", toggleCompare);
reviewCheckButtons.forEach((button) => {
  button.addEventListener("click", () => handleReviewAction(button.dataset.reviewAction));
});
quickFixButtons.forEach((button) => {
  button.addEventListener("click", () => reprocessWithQuickFix(button.dataset.quickFix));
});
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
  toggleHistoryPreview.textContent = `Thumbnails: ${historyPreviewEnabled ? "On" : "Off"}`;
  renderHistory(historyJobsCache, historyBatchesCache);
});
refreshDiagnostics.addEventListener("click", loadDiagnostics);

viewTabs.forEach((tab) => {
  tab.addEventListener("click", () => setActiveView(tab.dataset.viewTarget));
});

[historySearch, historyFilter, historySort].forEach((control) => {
  control?.addEventListener("input", () => renderHistory(historyJobsCache, historyBatchesCache));
  control?.addEventListener("change", () => renderHistory(historyJobsCache, historyBatchesCache));
});

previewBgButtons.forEach((button) => {
  button.addEventListener("click", () => setPreviewBackground(button.dataset.previewBg));
});

bindImageDropTarget(dropzone);
bindImageDropTarget(beforeStage);
bindGlobalImageDrop();
bindClipboardUpload();

assistantPrimary?.addEventListener("click", () => {
  if (!selectedFile) {
    fileInput.click();
    return;
  }
  if (recommendationAvailable()) {
    useRecommendation.click();
    return;
  }
  if (hasResultReady()) {
    resultDownload.click();
    return;
  }
  if (!runButton.disabled) form.requestSubmit();
});

assistantSecondary?.addEventListener("click", () => setActiveView("jobs"));

function endpointForTool(tool) {
  if (tool === "remove-background") return "/api/remove-background";
  if (tool === "remove-background-upscale") return "/api/remove-background-upscale";
  if (tool === "vectorize") return "/api/vectorize";
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
  if (usesVectorize()) {
    payload.set("output_format", "svg");
    payload.set("vector_preset", vectorPreset?.value || "logo");
    payload.set("vector_colormode", vectorColormode?.value || "color");
    payload.set("vector_hierarchical", vectorHierarchical?.value || "stacked");
    payload.set("vector_mode", vectorMode?.value || "spline");
    payload.set("vector_filter_speckle", vectorFilterSpeckle?.value || "4");
    payload.set("vector_color_precision", vectorColorPrecision?.value || "6");
    payload.set("vector_layer_difference", vectorLayerDifference?.value || "16");
    payload.set("vector_path_precision", vectorPathPrecision?.value || "3");
  }
  payload.delete("target_width");
  payload.delete("target_height");
  payload.delete("canvas_width");
  payload.delete("canvas_height");
  payload.delete("dpi");
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
  if (usesUpscale()) {
    if (canvasWidthInput.value) payload.set("canvas_width", canvasWidthInput.value);
    if (canvasHeightInput.value) payload.set("canvas_height", canvasHeightInput.value);
    if (dpiInput.value) payload.set("dpi", dpiInput.value);
    payload.set("resize_method", resizeMethodSelect.value);
    payload.set("target_fit", targetFitSelect.value);
    payload.set("canvas_anchor", canvasAnchorSelect.value);
    payload.set("export_quality", exportQuality.value);
    payload.set("sharpen_amount", sharpenAmount.value);
  } else {
    ["resize_method", "target_fit", "canvas_anchor", "export_quality", "sharpen_amount"].forEach((name) => payload.delete(name));
  }
  if (tool === "remove-background") {
    payload.set("device", backgroundDevice.value);
  } else if (tool === "upscale") {
    payload.set("device", upscaleDevice.value);
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
  const dpi = response.headers.get("X-Output-DPI") || "";
  const engine =
    response.headers.get("X-Pipeline-Engine") ||
    response.headers.get("X-Upscaler-Engine") ||
    response.headers.get("X-Background-Engine") ||
    response.headers.get("X-Vector-Engine") ||
    "";
  const extension = outputFormat.value.toUpperCase();
  afterMeta.textContent = `${width} x ${height} | ${extension} | ${formatBytes(blob.size)}`;
  const printSummary = dpi ? ` | ${(Number(width) / Number(dpi)).toFixed(2)} x ${(Number(height) / Number(dpi)).toFixed(2)} in @ ${dpi} DPI` : "";
  resultSummary.textContent = `${width} x ${height} ${extension}${printSummary}`;

  if (engine) {
    engineChip.textContent = engine;
    engineChip.className = `mini-badge ${engine.includes("CUDA") ? "good" : ""}`.trim();
    engineChip.classList.remove("hidden");
  }

  const downloadUrl = absoluteUrl(response.headers.get("X-Download-URL"), { allowBlob: false }) || afterUrl;
  const sourceUrl = absoluteUrl(response.headers.get("X-Source-URL"), { allowBlob: false }) || beforeUrl;
  const listingPackUrl = absoluteUrl(response.headers.get("X-Listing-Pack-URL"), { allowBlob: false });
  const filename = filenameFromResponse(response, fallbackName || "result.png");
  resultDownload.href = downloadUrl;
  resultDownload.download = filename;
  resultDownload.textContent = `Download ${extension}`;
  setListingPackDownload(listingPackUrl);
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
    listingPackUrl,
    summary: `${width} x ${height} ${extension}${printSummary} | ${formatBytes(blob.size)}`,
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
  if (tool === "remove-background") actionLabel = "Removing background";
  if (tool === "remove-background-upscale") actionLabel = "Removing background and upscaling";
  if (tool === "vectorize") actionLabel = "Vectorizing image";
  setBusyStatus(filesToProcess.length > 1 ? "Uploading batch to server" : "Uploading image to server");
  setStatus(
    "Uploading",
    "busy",
    "Keep this page open until the upload is accepted. Once the server job appears, Docker keeps processing without the browser.",
  );

  try {
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
      setServerBusyStatus("Queued on server", batch, `Batch ${String(batch.id || "").slice(0, 8)} accepted. You can close this browser and return later.`);
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

    const file = filesToProcess[0];
    const size = selectedImageSize || await imageSizeForFile(file);
    setProgress(10, `Uploading ${file.name} to the server queue...`);
    const queueResponse = await fetch("/api/jobs/queue", {
      method: "POST",
      body: buildPayload(file, size),
    });
    if (!queueResponse.ok) {
      const body = await queueResponse.json().catch(() => ({}));
      throw new Error(body.error || body.detail || `Queue failed with ${queueResponse.status}`);
    }
    const queuedJob = (await queueResponse.json()).job;
    currentQueueJobId = queuedJob.id;
    renderBatchResults([queuedJobToResult(queuedJob)]);
    setServerBusyStatus(
      queuedJob.status === "queued" ? "Queued on server" : `${actionLabel} on server`,
      queuedJob,
      `Uploaded to server as job ${String(queuedJob.id || "").slice(0, 8)}. You can close this browser and return later.`,
    );
    setStatus(
      "Uploaded",
      "busy",
      `Uploaded to server as job ${String(queuedJob.id || "").slice(0, 8)}. You can close this browser and return later.`,
    );
    const completedJob = await pollQueuedJob(queuedJob.id);
    const shown = showQueuedJobResult(completedJob);
    results.push({ ok: true, name: file.name, ...shown });
    renderBatchResults([]);
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
        `${results.length - failures.length} finished, ${failures.length} failed. Check History for downloads.`,
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
updateSharpenValue();
updateExportQualityValue();
updatePrintSizeNote();
setComparePosition(compareSlider.value);
applyCompareMode("slider");
applyCompareZoom("fit");
updateCompareAvailability();
setPreviewBackground("checker");
setActiveView("workspace");
syncExperienceMode();
applyWorkflow("shirt", false);
loadPresets();
loadRuntime();
resumeRunningJobs();
syncWorkflowAssistant();
