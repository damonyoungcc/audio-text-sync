import os
import json
import re

SUPPORTED_AUDIO_TYPES = ["mp3", "m4a"]
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "dir_config.json")

def question_sort_key(q):
    # 使用正则查找所有连续数字
    nums = re.findall(r'\d+', q)
    if nums:
        # 存在数字，返回 (0, (数字元组))
        return (0, tuple(map(int, nums)))
    else:
        # 不存在数字，返回 (1, 原字符串)
        return (1, q)

def update_dir_config():
    print("\n📂 正在扫描 data 目录并生成 dir_config.json...")
    dir_config = {}

    # 对年份目录按字母或数字顺序排序
    for year in sorted(os.listdir(DATA_DIR)):
        year_path = os.path.join(DATA_DIR, year)
        if not os.path.isdir(year_path):
            continue

        questions = {}
        # 对问题目录采用自定义排序函数
        for q in sorted(os.listdir(year_path), key=question_sort_key):
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
            word_json_file = f"{base_name}.corrected.word.json"
            word_json_path = os.path.join(q_path, word_json_file)
            if not os.path.exists(word_json_path):
                continue

            questions[q] = {
                "path": os.path.join("data", year, q).replace("\\", "/"),
                "audio_file": audio_file,
                "word_corrected_json": word_json_file
            }

        if questions:
            dir_config[year] = questions

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(dir_config, f, indent=2, ensure_ascii=False, sort_keys=True)

    print(f"✅ 已生成配置文件: {CONFIG_PATH}")
    print("📌 配置结构如下：")
    print(json.dumps(dir_config, indent=2, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    update_dir_config()
