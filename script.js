const basePath = "data/";
const configPath = `${basePath}dir_config.json`;
let defaultYear;
let defaultQuestion;
let lastScrollTime = 0;
let scrollTimeout;
const timeCountDown = 3;

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

  const audioPath = `${entry.path}/${entry.audio_file}`;
  audio.src = audioPath;

  // 使用 word_json 字段加载转写内容
  const transcriptPath = `${entry.path}/${entry.word_json}`;
  const res = await fetch(transcriptPath);
  const transcriptJson = await res.json();

  // 如果 JSON 对象包含 word_segments 字段，则使用它，否则假定 transcriptJson 是数组
  const wordsArray = transcriptJson.word_segments || transcriptJson;
  renderTranscript(wordsArray);
}

// wordsArray 是直接包含单词对象的数组，每个对象应具有 word 和 start 属性，没有就不执行
function renderTranscript(wordsArray) {
  transcriptDiv.innerHTML = "";

  wordsArray.forEach((item) => {
    // 换行
    if (item.role === "line-break") {
      const divider = document.createElement("div");
      divider.className = "line-break";
      transcriptDiv.appendChild(divider);
      return;
    }

    // 角色标签
    if (item.role === "speaker-label") {
      const span = document.createElement("span");
      span.textContent = item.word;
      span.className = "word speaker-label";
      if (typeof item.start === "number") {
        span.dataset.start = item.start;
        if (typeof item.end === "number") {
          span.dataset.end = item.end;
        }
        span.addEventListener("click", () => {
          audio.currentTime = item.start;
          updateHighlight(item.start); // 手动触发
          if (audio.paused) audio.play();
        });
      }
      transcriptDiv.appendChild(span);
      return;
    }

    // 普通词
    const span = document.createElement("span");
    span.textContent = item.word;
    span.className = "word";

    if (typeof item.start === "number") {
      span.dataset.start = item.start;
    }
    if (typeof item.end === "number") {
      span.dataset.end = item.end;
    }

    if (item.start !== undefined) {
      span.addEventListener("click", () => {
        audio.currentTime = item.start;
        updateHighlight(item.start);
        if (audio.paused) audio.play();
      });
    }

    transcriptDiv.appendChild(span);
  });
}

function updateHighlight(currentTime) {
  const tolerance = 0.0; // 可设为 0.1~0.2 秒提前量
  const words = transcriptDiv.querySelectorAll(".word");

  for (let i = 0; i < words.length; i++) {
    const start = parseFloat(words[i].dataset.start);
    const end = parseFloat(words[i].dataset.end);

    if (isNaN(start) || isNaN(end)) continue;

    if (currentTime >= start - tolerance && currentTime < end) {
      words.forEach((w) => w.classList.remove("highlight"));
      words[i].classList.add("highlight");

      if (Date.now() - lastScrollTime > timeCountDown * 1000) {
        words[i].scrollIntoView({ block: "center", behavior: "smooth" });
      }
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
  questionSelect.value = configData[year]?.[question]
    ? question
    : firstQuestion;
  loadData(year, questionSelect.value);
});

transcriptDiv.addEventListener("scroll", () => {
  lastScrollTime = Date.now();

  if (scrollTimeout) clearTimeout(scrollTimeout);

  // 如果 5 秒内没有再次滚动，就触发“居中”逻辑
  scrollTimeout = setTimeout(() => {
    lastScrollTime = 0;
  }, 5000);
});

const fabBtn = document.getElementById("fabPlayToggle");
const iconSpan = fabBtn.querySelector(".icon");

function updateFabIcon() {
  iconSpan.className = "icon " + (audio.paused ? "play" : "pause");
}

fabBtn.addEventListener("click", () => {
  if (audio.paused) {
    audio.play();
  } else {
    audio.pause();
  }
  updateFabIcon();
});

audio.addEventListener("play", updateFabIcon);
audio.addEventListener("pause", updateFabIcon);
