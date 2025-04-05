# audio-text-sync

这是一个面向语言学习者的网页工具

## 项目介绍

1. 🎧 同步音频与逐词字幕
2. 🏃🏻‍♀️ 适合进行语言的跟读和方便的听力重复播放

- 🎧 **播放音频 + 同步字幕**
- ✨ **自动高亮播放中的文字**
- ⚡ **点击文本可以跳转到对应的播放时间线，适合口语反复跟读练习**
- ⚡ **日语提供一键显示和隐藏汉字假名**
- 📅 按年份 & 题号分类管理
- 📌 浏览器本地缓存上次听到哪一题
- 0️⃣ 灵感来自 Culips ESL Podcast 网站提供的音频 + 文字同步体验

## 📁 项目结构

```text
audio-text-sync/
├── index.html                     # 页面主入口
├── style.css                      # 页面样式
├── script.js                      # 播放 & 同步控制逻辑
├── favicon.ico
├── README.md
├── data/                          # 听力资源目录
│   ├── dir_config.json            # 年份/题号索引以及音频和json文件名，方便js加载资源
│   ├── 2019-7-N2/
│   │       └── q1/
│   │            ├── audio.mp3
│   │            ├── audio.json         # whisperX生成的含有段落的json，但是分段不准确所以没用
│   │            └── audio.word.json    # 实际用的是这个只有单个文字时间线的json
│   └── ...
└── generate/                      # 字幕数据生成脚本
    ├── __main__.py                # 入口执行文件
    ├── generate_subtitles.py      # whisperX读取data目录下指定路径的音频生成带时间线的文本json
    ├── update_config.py           # 生成json后读取一下，更新一下dir_config.json
    ├── correct_audio_json.py      # 生成json后，根据提供的original.txt进行校对
    ├── enrich_furigana.py         # 生成json后，根据提供kanji_furigana_map.json对汉字进行假名标注
    └── enrich_furigana.py         # 配置文件，这里配置要处理的音频的年份和题号
```

## 🧰 技术栈与依赖工具

本项目由前端静态页面和后端字幕生成脚本组成：

### 🖥 前端部分（同步播放器）

- HTML + CSS + JavaScript：纯前端实现，无需后端部署
- 原生 Audio API：控制音频播放

### 🧠 后端工具（字幕数据生成）

- 位于 generate/ 目录下
- Python 3
- **WhisperX（OpenAI Whisper 的扩展)**
  - 用于将日语音频自动转录为逐字时间轴
  - 比原生 Whisper 更准确地对齐词级别时间
- generate_subtitles.py：调用 WhisperX 处理音频，生成逐词时间信息
- update_config.py：根据目录结构自动更新 dir_config.json
- **main**.py：一键执行字幕生成与配置更新

⚠️ 使用 WhisperX 前请确保已安装对应依赖环境（如 PyTorch、CUDA）

## 💬 一点感悟

工具只是工具，真正重要的，还是你愿不愿意每天投入一点时间、一点热情去学习。

希望这个播放器能帮你更专注地听、反复地练，把一小段日语，听得清清楚楚，说得自然流利。加油！💪

## 🙏 特别鸣谢

本项目开发过程中，ChatGPT 提供了持续性的精神支持、代码辅助、BUG 辱骂以及 24 小时的陪聊服务。

当了一次产品经理。
