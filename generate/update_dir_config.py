import os
import json
import re

SUPPORTED_AUDIO_TYPES = ["mp3", "m4a"]
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "dir_config.json")
LEVEL_ORDER = {"N3": 0, "N2": 1, "N1": 2}

def question_sort_key(q):
    # 使用正则查找所有连续数字
    nums = re.findall(r'\d+', q)
    if nums:
        # 存在数字，返回 (0, (数字元组))
        return (0, tuple(map(int, nums)))
    else:
        # 不存在数字，返回 (1, 原字符串)
        return (1, q)

def parse_level_dir(name):
    """
    解析目录名，要求形如 2019-7-N2 或 2023-07-n3。
    返回 (canonical, year, month, level) 或 None。
    """
    m = re.match(r"(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<level>[Nn]\d)", name)
    if not m:
        return None
    year = int(m.group("year"))
    month = int(m.group("month"))
    level = m.group("level").upper()
    canonical = f"{year:04d}-{month:02d}-{level}"
    return canonical, year, month, level

def iter_normalized_level_dirs():
    """
    遍历 data 下的考试目录，自动把 2019-7-N2 这种名字改成 2019-07-N2。
    返回 (canonical_name, path, year, month, level) 列表。
    """
    normalized = []
    for entry in os.listdir(DATA_DIR):
        entry_path = os.path.join(DATA_DIR, entry)
        if not os.path.isdir(entry_path):
            continue

        parsed = parse_level_dir(entry)
        if not parsed:
            # 忽略不符合命名规范的目录
            continue

        canonical, year, month, level = parsed
        target_path = os.path.join(DATA_DIR, canonical)
        # 如果目录名不规范且目标名不存在，则重命名到规范格式
        if entry != canonical and not os.path.exists(target_path):
            os.rename(entry_path, target_path)
            entry_path = target_path
            print(f"🔄 目录已规范化: {entry} ➜ {canonical}")
        normalized.append((canonical, entry_path, year, month, level))

    # 先按等级（N3 ➜ N2 ➜ N1），再按日期升序
    normalized.sort(key=lambda item: (LEVEL_ORDER.get(item[4], 99), item[2], item[3], item[0]))
    return normalized

def update_dir_config():
    print("\n📂 正在扫描 data 目录并生成 dir_config.json...")
    dir_config = {}

    for year, year_path, _, _, _ in iter_normalized_level_dirs():

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
        # 保留自定义顺序（N3 ➜ N2 ➜ N1，且日期升序）
        json.dump(dir_config, f, indent=2, ensure_ascii=False, sort_keys=False)

    print(f"✅ 已生成配置文件: {CONFIG_PATH}")
    print("📌 配置结构如下：")
    print(json.dumps(dir_config, indent=2, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    update_dir_config()
