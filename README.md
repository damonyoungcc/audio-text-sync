# JLPT N2 Listening Practice Player

这是一个为日语能力考试（JLPT）听力题设计的**静态网页播放器**，目前逐步更新N2的听力资源，支持：

- 📅 按年份 & 题号分类管理
- 🎧 播放音频 + 同步字幕
- ✨ 自动高亮播放中的文字
- ⚡ 点击文本可以跳转到对应的播放时间线，适合口语练习
- 📌 浏览器本地缓存上次听到哪一题
- 0️⃣ 灵感来自Culips ESL Podcast 网站提供的音频 + 文字同步体验

---

## 📁 项目结构
```text
audio-text-sync/
├── index.html
├── style.css
├── data/                    ← 所有听力题素材
│   ├── 2019/
│   │   └── q1/
│   │       ├── audio.mp3
│   │       └── transcript.vtt
│   └── 2020/
│       └── q1/
│           ├── audio.mp3
│           └── transcript.vtt
└── README.md
```