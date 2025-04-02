# JLPT N2 Listening Practice Player

这是一个为日语能力考试（JLPT）N2 听力题设计的**静态网页播放器**，支持：

- 📅 按年份 & 题号分类管理
- 🎧 播放音频 + 同步字幕
- ✨ 自动高亮播放中的文字
- 📌 浏览器记住你上次听到哪一题
- ⚡ 纯 HTML/CSS/JS 静态项目，可部署在 GitHub Pages

---

## 📁 项目结构
```text
jlpt-n2-listening/
├── index.html
├── style.css
├── data/                    ← 所有听力题素材
│   ├── 2020/
│   │   └── q1/
│   │       ├── audio.mp3
│   │       └── transcript.vtt
│   ├── 2021/
│   │   └── q1/
│   └── 2022/
│       └── q3/
│           ├── audio.mp3
│           └── transcript.vtt
└── README.md
```