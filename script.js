const basePath = "data/";
const configPath = `${basePath}dir_config.json`;
let defaultYear;
let defaultQuestion;

const yearSelect = document.getElementById("yearSelect");
const questionSelect = document.getElementById("questionSelect");
const audio = document.getElementById("audio");
const transcriptDiv = document.getElementById("transcript");

let configData = {};

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
  return questions[0]; // 返回第一个问题作为默认值
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

  const jsonPath = `${entry.path}/${entry.json}`;
  const audioPath = `${entry.path}/${entry.audio_file}`;
  audio.src = audioPath;

  const res = await fetch(jsonPath);
  const json = await res.json();
  renderTranscript(json.segments);
}

function renderTranscript(segments) {
  transcriptDiv.innerHTML = "";

  segments.forEach((segment) => {
    const container = document.createElement("div");
    container.className = `segment type-${segment.type || "dialogue"}`;

    if (segment.speaker) {
      const label = document.createElement("span");
      label.className = "speaker";
      label.textContent =
        segment.speaker === "male" ? "男：" :
        segment.speaker === "female" ? "女：" : "";
      container.appendChild(label);
    }

    segment.words.forEach(({ word, start }) => {
      const span = document.createElement("span");
      span.textContent = word;
      span.className = "word";
      span.dataset.start = start;
      span.addEventListener("click", () => {
        document.body.style.userSelect = "none";
        setTimeout(() => {
          document.body.style.userSelect = "";
        }, 300);
        audio.currentTime = start;
        if (audio.paused) audio.play();
      });
      container.appendChild(span);
    });

    transcriptDiv.appendChild(container);
  });
}

function updateHighlight(currentTime) {
  const words = transcriptDiv.querySelectorAll(".word");
  for (let i = 0; i < words.length; i++) {
    const start = parseFloat(words[i].dataset.start);
    const nextStart =
      i + 1 < words.length ? parseFloat(words[i + 1].dataset.start) : Infinity;
    if (currentTime >= start && currentTime < nextStart) {
      words.forEach((w) => w.classList.remove("highlight"));
      words[i].classList.add("highlight");
      words[i].scrollIntoView({ block: "center", behavior: "smooth" });
      break;
    }
  }
}

audio.addEventListener("timeupdate", () => {
  updateHighlight(audio.currentTime);
});

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

window.addEventListener("DOMContentLoaded", async () => {
  await fetchConfig();
  populateYearSelect();
  const { year, question } = loadFromStorage();
  yearSelect.value = year;
  const firstQuestion = populateQuestionSelect(year);
  questionSelect.value = configData[year]?.[question] ? question : firstQuestion;
  loadData(year, questionSelect.value);
});
