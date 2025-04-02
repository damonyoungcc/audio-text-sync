# generate/update_config.py

import os
import json

SUPPORTED_AUDIO_TYPES = ["mp3", "m4a"]
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "dir_config.json")

def update_dir_config():
    print("\n📂 正在扫描 data 目录并生成 dir_config.json...")
    dir_config = {}

    for year in os.listdir(DATA_DIR):
        year_path = os.path.join(DATA_DIR, year)
        if not os.path.isdir(year_path):
            continue

        questions = {}
        for q in os.listdir(year_path):
            q_path = os.path.join(year_path, q)
            if not os.path.isdir(q_path):
                continue

            audio_file = None
            for f in os.listdir(q_path):
                if f.lower().endswith(tuple(SUPPORTED_AUDIO_TYPES)):
                    audio_file = f
                    break

            if not audio_file:
                continue

            base_name, _ = os.path.splitext(audio_file)
            json_file = f"{base_name}.json"
            json_path = os.path.join(q_path, json_file)
            if not os.path.exists(json_path):
                continue

            questions[q] = {
                "path": os.path.join("data", year, q).replace("\\", "/"),
                "audio_file": audio_file,
                "json": json_file
            }

        if questions:
            dir_config[year] = questions

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(dir_config, f, indent=2, ensure_ascii=False)

    print(f"✅ 已生成配置文件: {CONFIG_PATH}")
    print("📌 配置结构如下：")
    print(json.dumps(dir_config, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    update_dir_config()