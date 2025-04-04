// === 设定与全局变量 ===
const basePath = "data/";
const configPath = `${basePath}dir_config.json`;
const timeCountDown = 3;

let defaultYear;
let defaultQuestion;
let lastScrollTime = 0;
let scrollTimeout;
let configData = {};

const yearSelect = document.getElementById("yearSelect");
const questionSelect = document.getElementById("questionSelect");
const audio = document.getElementById("audio");
const transcriptDiv = document.getElementById("transcript");
const fabBtn = document.getElementById("fabPlayToggle");
const iconSpan = fabBtn.querySelector(".icon");
const furiganaToggleBtn = document.getElementById("fabToggleFurigana");

let showFurigana = localStorage.getItem("showFurigana") !== "false";

// === 初始化逻辑 ===
window.addEventListener("DOMContentLoaded", async () => {
  await fetchConfig();
  populateYearSelect();
  const { year, question } = loadFromStorage();
  yearSelect.value = year;
  const firstQuestion = populateQuestionSelect(year);
  questionSelect.value = configData[year]?.[question]
    ? question
    : firstQuestion;
  loadData(year, questionSelect.value);
});

// === 配置与数据加载 ===
async function fetchConfig() {
  const res = await fetch(configPath);
  configData = await res.json();
  const yearKeys = Object.keys(configData);
  defaultYear = yearKeys[0];
  const questionKeys = Object.keys(configData[defaultYear] || {});
  defaultQuestion = questionKeys[0];
}

function populateYearSelect() {
  yearSelect.innerHTML = "";
  Object.keys(configData).forEach((year) => {
    const option = document.createElement("option");
    option.value = year;
    option.textContent = year;
    yearSelect.appendChild(option);
  });
}

function populateQuestionSelect(year) {
  const questions = Object.keys(configData[year] || {});
  questionSelect.innerHTML = "";
  questions.forEach((q) => {
    const option = document.createElement("option");
    option.value = q;
    option.textContent = q.toUpperCase();
    questionSelect.appendChild(option);
  });
  return questions[0];
}

function loadFromStorage() {
  const year = localStorage.getItem("year") || defaultYear;
  const question = localStorage.getItem("question") || defaultQuestion;
  return { year, question };
}

function saveToStorage(year, question) {
  localStorage.setItem("year", year);
  localStorage.setItem("question", question);
}

async function loadData(year, question) {
  saveToStorage(year, question);
  const entry = configData[year]?.[question];
  if (!entry) return;

  audio.src = `${entry.path}/${entry.audio_file}`;
  const res = await fetch(`${entry.path}/${entry.word_corrected_json}`);
  const transcriptJson = await res.json();
  const wordsArray = transcriptJson.word_segments || transcriptJson;
  renderTranscript(wordsArray);
}

// === 字幕渲染逻辑（含假名） ===
function renderTranscript(wordsArray) {
  transcriptDiv.innerHTML = "";

  wordsArray.forEach((item) => {
    if (item.role === "line-break") {
      const divider = document.createElement("div");
      divider.className = "line-break";
      transcriptDiv.appendChild(divider);
      return;
    }

    const span = document.createElement("span");
    span.className = "word";

    if (item.role === "speaker-label") {
      span.textContent = item.word;
      span.classList.add("speaker-label");
    } else if (item.furigana) {
      const ruby = document.createElement("ruby");
      ruby.textContent = item.word;

      const rt = document.createElement("rt");
      rt.textContent = item.furigana;
      if (!showFurigana) rt.style.display = "none";

      ruby.appendChild(rt);
      span.appendChild(ruby);
    } else {
      span.textContent = item.word;
    }

    if (typeof item.start === "number") span.dataset.start = item.start;
    if (typeof item.end === "number") span.dataset.end = item.end;

    if (item.start !== undefined) {
      span.addEventListener("click", () => {
        audio.currentTime = item.start;
        updateHighlight(item.start);
        if (audio.paused) audio.play();
      });
    }

    transcriptDiv.appendChild(span);
  });

  furiganaToggleBtn.classList.toggle("toggle-on", showFurigana);
  furiganaToggleBtn.classList.toggle("toggle-off", !showFurigana);
}

// === 高亮逻辑 ===
function updateHighlight(currentTime) {
  const tolerance = 0.05;
  const words = transcriptDiv.querySelectorAll(".word");

  let bestIndex = -1;
  let closestBefore = -1;
  let closestBeforeTime = -Infinity;

  for (let i = 0; i < words.length; i++) {
    const start = parseFloat(words[i].dataset.start);
    const end = parseFloat(words[i].dataset.end);
    if (isNaN(start) || isNaN(end)) continue;

    if (currentTime >= start - tolerance && currentTime <= end + tolerance) {
      bestIndex = i;
    }
    if (start <= currentTime && start > closestBeforeTime) {
      closestBefore = i;
      closestBeforeTime = start;
    }
  }

  const indexToHighlight = bestIndex !== -1 ? bestIndex : closestBefore;
  if (indexToHighlight !== -1) {
    words.forEach((w) => w.classList.remove("highlight"));
    const wordEl = words[indexToHighlight];
    wordEl.classList.add("highlight");

    if (Date.now() - lastScrollTime > timeCountDown * 1000) {
      wordEl.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }
}

// === 控件事件绑定 ===
audio.addEventListener("timeupdate", () => updateHighlight(audio.currentTime));

yearSelect.addEventListener("change", () => {
  const year = yearSelect.value;
  const firstQuestion = populateQuestionSelect(year);
  questionSelect.value = firstQuestion;
  loadData(year, firstQuestion);
});

questionSelect.addEventListener("change", () => {
  const year = yearSelect.value;
  const question = questionSelect.value;
  loadData(year, question);
});

transcriptDiv.addEventListener("scroll", () => {
  lastScrollTime = Date.now();
  if (scrollTimeout) clearTimeout(scrollTimeout);
  scrollTimeout = setTimeout(() => {
    lastScrollTime = 0;
  }, 5000);
});

// === 播放按钮逻辑 ===
function updateFabIcon() {
  iconSpan.className = "icon " + (audio.paused ? "play" : "pause");
}

fabBtn.addEventListener("click", () => {
  if (audio.paused) audio.play();
  else audio.pause();
  updateFabIcon();
});

audio.addEventListener("play", updateFabIcon);
audio.addEventListener("pause", updateFabIcon);

// === 假名开关按钮逻辑 ===
furiganaToggleBtn.addEventListener("click", () => {
  showFurigana = !showFurigana;
  localStorage.setItem("showFurigana", showFurigana.toString());

  const rts = transcriptDiv.querySelectorAll("rt");
  rts.forEach((rt) => {
    rt.style.display = showFurigana ? "" : "none";
  });

  furiganaToggleBtn.classList.toggle("toggle-on", showFurigana);
  furiganaToggleBtn.classList.toggle("toggle-off", !showFurigana);
});
