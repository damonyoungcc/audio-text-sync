import json
from pathlib import Path
from target_config import YEAR, QUESTION_NUM

def find_file_with_suffixes_case_insensitive(path: Path, suffixes: list[str]):
    for suffix in suffixes:
        for file in path.glob(f'*{suffix}'):
            return file
        for file in path.glob(f'*{suffix.upper()}'):
            return file
    return None

def is_kanji(char):
    return '\u4e00' <= char <= '\u9fff'

def enrich_corrected_json_with_furigana(year=YEAR, question=QUESTION_NUM):
    script_dir = Path(__file__).resolve().parent
    data_dir = script_dir.parent / "data" / year / question

    # 找到音频文件
    audio_file = find_file_with_suffixes_case_insensitive(data_dir, [".mp3", ".m4a"])
    if not audio_file:
        print(f"❌ 找不到音频文件（.mp3/.m4a）：{data_dir}")
        return

    audio_stem = audio_file.stem
    json_path = data_dir / f"{audio_stem}.corrected.word.json"
    furigana_map_path = data_dir / "kanji_furigana_map.json"

    if not json_path.exists():
        print(f"❌ 找不到 JSON 文件: {json_path}")
        return
    if not furigana_map_path.exists():
        print(f"❌ 找不到假名映射表: {furigana_map_path}")
        return

    # 读取数据
    with open(json_path, "r", encoding="utf-8") as f:
        word_data = json.load(f)
    with open(furigana_map_path, "r", encoding="utf-8") as f:
        furigana_map = json.load(f)

    # 安全性校验：提取所有 word 中的汉字（排除 speaker-label）
    kanji_words = [
        item["word"]
        for item in word_data
        if is_kanji(item.get("word", "")) and item.get("role") != "speaker-label"
    ]
    furigana_kanji = [list(d.keys())[0] for d in furigana_map]
    # 打印长度对比
    kanji_words = [item["word"].strip() for item in word_data if is_kanji(item.get("word", "")) and item.get("role") != "speaker-label"]
    furigana_kanji = [list(d.keys())[0].strip() for d in furigana_map]

    if len(kanji_words) != len(furigana_kanji) or kanji_words != furigana_kanji:
        print("❌ 汉字数量或顺序不一致")
        print(f"word_data 中的汉字数：{len(kanji_words)}")
        print(f"映射表中的汉字数：{len(furigana_kanji)}")

        print("🔍 对比内容如下：")
        max_len = max(len(kanji_words), len(furigana_kanji))
        for i in range(max_len):
            w1 = kanji_words[i] if i < len(kanji_words) else "x"
            w2 = furigana_kanji[i] if i < len(furigana_kanji) else "x"
            print(f"{w1}  {w2}")
        return

    print("✅ 校验通过：顺序一致、长度一致，准备开始标注...")

    # 添加 furigana
    furigana_items = [(list(d.keys())[0], list(d.values())[0]) for d in furigana_map]
    furigana_index = 0
    update_count = 0

    for item in word_data:
        word = item.get("word", "")
        if item.get("role") == "speaker-label" or not is_kanji(word):
            continue

        if furigana_index < len(furigana_items):
            item["furigana"] = furigana_items[furigana_index][1]
            furigana_index += 1
            update_count += 1

    # 原地保存
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(word_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 添加完毕，{update_count} 个词添加了 furigana。")
    print(f"📄 文件已更新：{json_path}")

    return word_data

# 独立执行
if __name__ == "__main__":
    enrich_corrected_json_with_furigana()
