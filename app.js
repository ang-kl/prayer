const STORAGE_KEY = "wholehearted-prayer-v1";

const state = {
  decision: "",
  why: "",
  scriptureStatus: "",
  whems: {},
  fruit: [],
  nextStep: "",
  review: null,
};

const whemsConfig = [
  { key: "W", name: "Will", question: "Am I willing to do what pleases God, even if it costs me?", prompt: "What am I reluctant to surrender?", refs: [{ label: "Luke 22:42", url: "https://www.esv.org/verses/Luke+22:42/" }, { label: "Philippians 2:13", url: "https://www.esv.org/verses/Philippians+2:13/" }] },
  { key: "H", name: "Heart", question: "What am I loving, wanting or protecting in this decision?", prompt: "What motive may need to be purified?", refs: [{ label: "Proverbs 4:23", url: "https://www.esv.org/verses/Proverbs+4:23/" }, { label: "Psalm 139:23-24", url: "https://www.esv.org/verses/Psalm+139:23-24/" }] },
  { key: "E", name: "Emotions", question: "What am I feeling, and how is it shaping my response?", prompt: "Name the feeling honestly. It may inform you, but it does not rule what is true.", refs: [{ label: "Matthew 26:37-39", url: "https://www.esv.org/verses/Matthew+26:37-39/" }, { label: "Philippians 4:6-7", url: "https://www.esv.org/verses/Philippians+4:6-7/" }] },
  { key: "M", name: "Mind", question: "What is true, wise and sufficiently established?", prompt: "Separate facts from assumptions. What wisdom or counsel am I missing?", refs: [{ label: "Romans 12:2", url: "https://www.esv.org/verses/Romans+12:2/" }, { label: "James 1:5", url: "https://www.esv.org/verses/James+1:5/" }] },
  { key: "S", name: "Soul", question: "Whose am I, and what allegiance should govern this decision?", prompt: "If I belong to Christ, how should that belonging shape my response?", refs: [{ label: "Romans 6:17-23", url: "https://www.esv.org/verses/Romans+6:17-23/" }, { label: "Ephesians 2:8-10", url: "https://www.esv.org/verses/Ephesians+2:8-10/" }] },
];

const fruits = ["Love", "Joy", "Peace", "Patience", "Kindness", "Goodness", "Faithfulness", "Gentleness", "Self-control"];

const views = {
  home: document.getElementById("homeView"),
  decision: document.getElementById("decisionView"),
  scripture: document.getElementById("scriptureView"),
  whems: document.getElementById("whemsView"),
  prayer: document.getElementById("prayerView"),
  next: document.getElementById("nextStepView"),
  review: document.getElementById("reviewView"),
};

function showView(name) {
  Object.values(views).forEach(v => v.classList.remove("active"));
  views[name].classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (name === "home") refreshSaved();
  if (name === "review") loadReviewView();
}

function renderWhems() {
  const container = document.getElementById("whemsCards");
  container.innerHTML = whemsConfig.map(item => `
    <section class="whem-card" aria-labelledby="${item.key}-title">
      <div class="whem-card-head">
        <div class="whem-letter" aria-hidden="true">${item.key}</div>
        <div><h3 id="${item.key}-title">${item.name}</h3><p>${item.question}</p></div>
      </div>
      <div class="status-row" role="group" aria-label="${item.name} status">
        <label class="status-option"><input type="radio" name="status-${item.key}" value="aligned"><span>✓ Thank God</span></label>
        <label class="status-option"><input type="radio" name="status-${item.key}" value="struggling"><span>! Needs help</span></label>
        <label class="status-option"><input type="radio" name="status-${item.key}" value="unclear"><span>? Unclear</span></label>
      </div>
      <label for="note-${item.key}">${item.prompt}</label>
      <textarea class="whem-note" id="note-${item.key}" rows="2" placeholder="Write a short reflection…"></textarea>
      <div class="reference-row">
        ${item.refs.map(r => `<a href="${r.url}" target="_blank" rel="noopener noreferrer">${r.label} · ESV</a>`).join("")}
      </div>
    </section>
  `).join("");

  const fruitBox = document.getElementById("fruitChoices");
  fruitBox.innerHTML = fruits.map(f => `<label class="chip"><input type="checkbox" value="${f}"><span>${f}</span></label>`).join("");
}

function collectWhems() {
  state.whems = {};
  whemsConfig.forEach(item => {
    const status = document.querySelector(`input[name="status-${item.key}"]:checked`)?.value || "unclear";
    const note = document.getElementById(`note-${item.key}`).value.trim();
    state.whems[item.key] = { name: item.name, status, note };
  });
  state.fruit = [...document.querySelectorAll("#fruitChoices input:checked")].map(i => i.value);
}

function buildPrayer() {
  const aligned = Object.values(state.whems).filter(x => x.status === "aligned");
  const needs = Object.values(state.whems).filter(x => x.status !== "aligned");
  const alignedNames = aligned.map(x => x.name.toLowerCase());
  const needNames = needs.map(x => x.name.toLowerCase());
  const fruitText = state.fruit.length ? ` Grow ${joinNatural(state.fruit.map(x => x.toLowerCase()))} in me as I respond.` : "";

  const thankSentence = aligned.length
    ? `Thank you for the help you have already given me in my ${joinNatural(alignedNames)}.`
    : `Thank you that I can bring this decision honestly before you.`;
  const askSentence = needs.length
    ? `I still need your help with my ${joinNatural(needNames)}. Correct what is sinful, clarify what is uncertain, and strengthen me to obey what is clear.`
    : `Keep me humble, teachable and dependent on you rather than confident in myself.`;

  const prayer = `Father, I bring this decision before you: ${state.decision}. ${thankSentence} ${askSentence}${fruitText} Help me honour Christ in both my decision and my response. Give me wisdom for the next faithful step, and keep me willing to be corrected by your Word. In Jesus' name, amen.`;
  document.getElementById("prayerText").innerHTML = `<p>${escapeHtml(prayer)}</p>`;

  const thankList = document.getElementById("thankList");
  const askList = document.getElementById("askList");
  thankList.innerHTML = aligned.length ? aligned.map(x => `<li><strong>${x.name}</strong>${x.note ? ` - ${escapeHtml(x.note)}` : ""}</li>`).join("") : "<li>Access to God in prayer and the opportunity to seek wisdom.</li>";
  askList.innerHTML = needs.length ? needs.map(x => `<li><strong>${x.name}</strong>${x.note ? ` - ${escapeHtml(x.note)}` : ""}</li>`).join("") : "<li>Humility, continued dependence and perseverance.</li>";
}

function joinNatural(items) {
  if (items.length === 0) return "";
  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return `${items.slice(0, -1).join(", ")}, and ${items.at(-1)}`;
}

function determineOutcome() {
  let title = "Wait and pray";
  let text = "Some important parts remain unclear. Keep praying, gather what is missing, and avoid manufacturing certainty.";
  if (state.scriptureStatus === "clear") {
    title = "Respond to what Scripture makes clear";
    text = "If Scripture clearly commands or forbids the action, W.H.E.M.S. helps you obey faithfully; it does not overturn God's revealed Word.";
  } else if (state.whems.M?.status === "unclear") {
    title = "Gather facts and seek wisdom";
    text = "Your Mind reflection remains unclear. Verify assumptions, seek counsel where appropriate, and ask God for wisdom before treating uncertainty as direction.";
  } else if (state.whems.H?.status === "struggling" || state.whems.W?.status === "struggling") {
    title = "Pray, repent where needed, then reconsider";
    text = "A motive or willingness issue still needs attention. Bring it plainly to God and do not use a desired outcome to silence what Scripture exposes.";
  } else {
    title = "Take a faithful step";
    text = "No automatic divine verdict is being given. Where Scripture, responsibilities and facts are sufficiently clear, act faithfully while entrusting the outcome to God.";
  }
  document.getElementById("processOutcome").innerHTML = `<div class="outcome-label">Process outcome</div><h3>${title}</h3><p>${text}</p>`;
}

function saveState() {
  state.nextStep = document.getElementById("nextStepText").value.trim();
  const payload = { ...state, savedAt: new Date().toISOString() };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  document.getElementById("saveStatus").textContent = "Saved on this device.";
  refreshSaved();
}

function readSaved() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)); } catch { return null; }
}

function refreshSaved() {
  const saved = readSaved();
  const section = document.getElementById("savedSection");
  if (!saved?.decision) { section.classList.add("hidden"); return; }
  section.classList.remove("hidden");
  document.getElementById("savedSummary").innerHTML = `<p><strong>${escapeHtml(saved.decision)}</strong></p><p class="muted">Saved ${new Date(saved.savedAt).toLocaleString()}</p>`;
}

function hydrateFromSaved() {
  const saved = readSaved();
  if (!saved) return false;
  Object.assign(state, saved);
  document.getElementById("decisionText").value = state.decision || "";
  document.getElementById("whyText").value = state.why || "";
  if (state.scriptureStatus) document.querySelector(`input[name="scriptureStatus"][value="${state.scriptureStatus}"]`)?.click();
  whemsConfig.forEach(item => {
    const s = state.whems?.[item.key];
    if (!s) return;
    document.querySelector(`input[name="status-${item.key}"][value="${s.status}"]`)?.click();
    document.getElementById(`note-${item.key}`).value = s.note || "";
  });
  document.querySelectorAll("#fruitChoices input").forEach(input => { input.checked = (state.fruit || []).includes(input.value); });
  document.getElementById("nextStepText").value = state.nextStep || "";
  return true;
}

function loadReviewView() {
  const saved = readSaved();
  document.getElementById("reviewEmpty").classList.toggle("hidden", !!saved?.decision);
  document.getElementById("reviewContent").classList.toggle("hidden", !saved?.decision);
  if (!saved?.decision) return;
  document.getElementById("reviewDecision").textContent = saved.decision;
  document.getElementById("reviewNote").value = saved.review?.note || "";
  if (saved.review?.status) document.querySelector(`input[name="reviewStatus"][value="${saved.review.status}"]`)?.click();
}

function saveReview() {
  const saved = readSaved();
  if (!saved) return;
  const note = document.getElementById("reviewNote").value.trim();
  const status = document.querySelector('input[name="reviewStatus"]:checked')?.value || "waiting";
  saved.review = { note, status, reviewedAt: new Date().toISOString() };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
  document.getElementById("reviewStatusText").textContent = "Thanksgiving note saved on this device.";
}

function resetAll() {
  if (!confirm("Start over? This clears the current form but keeps any previously saved prayer unless you choose Clear saved.")) return;
  location.reload();
}

function escapeHtml(str = "") {
  return str.replace(/[&<>'"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[c]));
}

renderWhems();
refreshSaved();

// navigation
document.querySelectorAll('[data-action="new"]').forEach(btn => btn.addEventListener("click", () => showView("decision")));
document.querySelectorAll('[data-action="review"]').forEach(btn => btn.addEventListener("click", () => showView("review")));
document.querySelectorAll("[data-back]").forEach(btn => btn.addEventListener("click", () => showView(btn.dataset.back)));

document.getElementById("toScriptureBtn").addEventListener("click", () => {
  state.decision = document.getElementById("decisionText").value.trim();
  state.why = document.getElementById("whyText").value.trim();
  if (!state.decision) { document.getElementById("decisionText").focus(); return; }
  showView("scripture");
});

document.getElementById("toWhemsBtn").addEventListener("click", () => {
  state.scriptureStatus = document.querySelector('input[name="scriptureStatus"]:checked')?.value || "unsure";
  showView("whems");
});

document.getElementById("toPrayerBtn").addEventListener("click", () => {
  collectWhems();
  buildPrayer();
  showView("prayer");
});

document.getElementById("toNextStepBtn").addEventListener("click", () => {
  determineOutcome();
  showView("next");
});

document.getElementById("saveBtn").addEventListener("click", saveState);
document.getElementById("doneBtn").addEventListener("click", () => showView("home"));
document.getElementById("saveReviewBtn").addEventListener("click", saveReview);
document.getElementById("resetBtn").addEventListener("click", resetAll);
document.getElementById("continueSavedBtn").addEventListener("click", () => { hydrateFromSaved(); showView("whems"); });
document.getElementById("clearSavedBtn").addEventListener("click", () => {
  if (!confirm("Delete the saved prayer from this device?")) return;
  localStorage.removeItem(STORAGE_KEY);
  refreshSaved();
});
