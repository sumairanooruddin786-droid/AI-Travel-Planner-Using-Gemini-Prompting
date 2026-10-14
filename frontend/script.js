// Wayfarer — AI Travel Planner frontend logic
// Talks to the FastAPI backend at /api/*, renders results as "boarding pass" cards.

const API_BASE = ""; // same origin as the FastAPI server serving this file

const els = {
  form: document.getElementById("trip-form"),
  submitBtn: document.getElementById("submit-btn"),
  compareBtn: document.getElementById("compare-btn"),
  chips: document.getElementById("interest-chips"),
  styleGroup: document.getElementById("travel-style"),
  techniqueList: document.getElementById("technique-list"),
  emptyState: document.getElementById("empty-state"),
  loadingState: document.getElementById("loading-state"),
  loadingText: document.getElementById("loading-text"),
  errorState: document.getElementById("error-state"),
  singleResult: document.getElementById("single-result"),
  compareResult: document.getElementById("compare-result"),
  historySection: document.getElementById("history-section"),
  historyList: document.getElementById("history-list"),
  template: document.getElementById("tpl-boarding-pass"),
};

let selectedInterests = new Set();
let selectedStyle = "Solo";

// ---------------------------------------------------------------------------
// Form interactions
// ---------------------------------------------------------------------------

els.chips.addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  const value = chip.dataset.value;
  if (selectedInterests.has(value)) {
    selectedInterests.delete(value);
    chip.classList.remove("is-selected");
  } else {
    selectedInterests.add(value);
    chip.classList.add("is-selected");
  }
});

els.styleGroup.addEventListener("click", (e) => {
  const opt = e.target.closest(".segmented__opt");
  if (!opt) return;
  selectedStyle = opt.dataset.value;
  [...els.styleGroup.children].forEach((c) => c.classList.toggle("is-active", c === opt));
});

els.techniqueList.querySelectorAll(".technique-opt").forEach((label) => {
  label.addEventListener("click", () => {
    els.techniqueList.querySelectorAll(".technique-opt").forEach((l) => l.classList.remove("is-active"));
    label.classList.add("is-active");
  });
});

function collectTripData() {
  const form = els.form;
  const technique = form.querySelector('input[name="technique"]:checked').value;
  return {
    name: form.name.value.trim(),
    destination: form.destination.value.trim(),
    days: parseInt(form.days.value, 10),
    budget: parseFloat(form.budget.value),
    interests: [...selectedInterests],
    travel_style: selectedStyle,
    technique,
  };
}

function validate(data) {
  if (!data.name) return "Please enter the passenger's name.";
  if (!data.destination) return "Please enter a destination.";
  if (!data.days || data.days < 1) return "Trip length must be at least 1 day.";
  if (!data.budget || data.budget <= 0) return "Please enter a budget greater than 0.";
  return null;
}

// ---------------------------------------------------------------------------
// UI state helpers
// ---------------------------------------------------------------------------

function showLoading(text) {
  els.emptyState.classList.add("hidden");
  els.errorState.classList.add("hidden");
  els.singleResult.classList.add("hidden");
  els.compareResult.classList.add("hidden");
  els.loadingState.classList.remove("hidden");
  els.loadingText.textContent = text;
}

function showError(message) {
  els.loadingState.classList.add("hidden");
  els.errorState.classList.remove("hidden");
  els.errorState.textContent = message;
}

function hideLoadingChrome() {
  els.loadingState.classList.add("hidden");
  els.errorState.classList.add("hidden");
  els.emptyState.classList.add("hidden");
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function buildPassCard(result, tripData) {
  const node = els.template.content.cloneNode(true);
  const article = node.querySelector(".pass");

  node.querySelector('[data-field="destination"]').textContent = tripData.destination.toUpperCase();
  node.querySelector('[data-field="name"]').textContent = tripData.name;
  node.querySelector('[data-field="days"]').textContent = `${tripData.days} day${tripData.days > 1 ? "s" : ""}`;
  node.querySelector('[data-field="budget"]').textContent = `$${tripData.budget}`;
  node.querySelector('[data-field="style"]').textContent = tripData.travel_style;

  const badge = node.querySelector('[data-field="technique"]');
  badge.textContent = result.technique_label;
  badge.dataset.tech = result.technique;

  node.querySelector('[data-field="itinerary"]').innerHTML = marked.parse(result.itinerary_markdown || "");
  node.querySelector('[data-field="time"]').textContent = `Generated in ${result.generation_time_seconds}s`;

  node.querySelector('[data-action="print"]').addEventListener("click", () => window.print());
  node.querySelector('[data-action="prompt"]').addEventListener("click", () => showPromptModal(result.prompt_used, result.technique_label));

  return article;
}

function showPromptModal(promptText, label) {
  const backdrop = document.createElement("div");
  backdrop.className = "prompt-modal-backdrop";
  backdrop.innerHTML = `
    <div class="prompt-modal">
      <h3>Prompt sent to Gemini — ${label}</h3>
      <pre></pre>
      <button type="button">Close</button>
    </div>`;
  backdrop.querySelector("pre").textContent = promptText;
  backdrop.querySelector("button").addEventListener("click", () => backdrop.remove());
  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) backdrop.remove(); });
  document.body.appendChild(backdrop);
}

function addToHistory(tripData, techniqueLabel) {
  els.historySection.classList.remove("hidden");
  const item = document.createElement("div");
  item.className = "history__item";
  item.innerHTML = `<b>${tripData.destination}</b> · ${tripData.days}d · ${techniqueLabel}`;
  els.historyList.prepend(item);
  // keep last 8
  [...els.historyList.children].slice(8).forEach((el) => el.remove());
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

async function callApi(path, payload) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

async function handleGenerate(e) {
  e.preventDefault();
  const tripData = collectTripData();
  const problem = validate(tripData);
  if (problem) { showError(problem); hideLoadingChrome(); els.errorState.classList.remove("hidden"); return; }

  const techniqueLabel = els.form.querySelector('input[name="technique"]:checked').closest(".technique-opt").querySelector(".technique-opt__title").textContent;
  showLoading(`Asking Gemini using ${techniqueLabel} prompting…`);
  els.submitBtn.disabled = true;

  try {
    const result = await callApi("/api/itinerary", tripData);
    hideLoadingChrome();
    els.singleResult.innerHTML = "";
    els.compareResult.classList.add("hidden");
    els.singleResult.appendChild(buildPassCard(result, tripData));
    els.singleResult.classList.remove("hidden");
    addToHistory(tripData, result.technique_label);
  } catch (err) {
    showError(err.message);
  } finally {
    els.submitBtn.disabled = false;
  }
}

async function handleCompare() {
  const tripData = collectTripData();
  const problem = validate(tripData);
  if (problem) { showError(problem); hideLoadingChrome(); els.errorState.classList.remove("hidden"); return; }

  showLoading("Running all three prompting techniques through Gemini…");
  els.compareBtn.disabled = true;

  try {
    const data = await callApi("/api/itinerary/compare", tripData);
    hideLoadingChrome();
    els.compareResult.innerHTML = "";
    els.singleResult.classList.add("hidden");
    data.results.forEach((result) => els.compareResult.appendChild(buildPassCard(result, tripData)));
    els.compareResult.classList.remove("hidden");
    addToHistory(tripData, "All 3 compared");
  } catch (err) {
    showError(err.message);
  } finally {
    els.compareBtn.disabled = false;
  }
}

els.form.addEventListener("submit", handleGenerate);
els.compareBtn.addEventListener("click", handleCompare);
