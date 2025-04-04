import json
from copy import deepcopy
from pathlib import Path
from target_config import YEAR, QUESTION_NUM

def correct_json_by_text(json_data, text_data):
    fixed_items = []
    json_idx = 0
    text_chars = list(text_data)
    json_len = len(json_data)

    def copy_time_from(idx):
        if 0 <= idx < json_len:
            base = json_data[idx]
        else:
            base = {"start": 0.0, "end": 0.0}
        return base.get("start", 0.0), base.get("end", 0.0)

    for ch in text_chars:
        if ch == "\n":
            fixed_items.append({"role": "line-break", "word": ""})
        elif ch in "、。！？「」（）":
            fixed_items.append({"word": ch})
        else:
            if json_idx >= json_len:
                start, end = copy_time_from(json_idx - 1)
                fixed_items.append({"word": ch, "start": start, "end": end})
            else:
                item = deepcopy(json_data[json_idx])
                item["word"] = ch
                fixed_items.append(item)
                json_idx += 1

    return fixed_items

def find_file_with_suffixes_case_insensitive(folder: Path, suffixes: list[str]):
    for path in folder.iterdir():
        if not path.is_file():
            continue
        lowercase = path.name.lower()
        for suffix in suffixes:
            if lowercase.endswith(suffix.lower()):
                return path
    return None

def run_corrector():
    script_dir = Path(__file__).resolve().parent  # generate/
    data_dir = script_dir.parent / "data" / YEAR / QUESTION_NUM

    # 获取音频文件（忽略后缀大小写）
    audio_file = find_file_with_suffixes_case_insensitive(data_dir, [".mp3", ".m4a"])
    if not audio_file:
        print(f"❌ 找不到音频文件（.mp3/.m4a）：{data_dir}")
        return
    audio_stem = audio_file.stem

    # 获取 word.json 文件
    word_json = find_file_with_suffixes_case_insensitive(data_dir, [".word.json"])
    if not word_json:
        print(f"❌ 找不到 .word.json 文件：{data_dir}")
        return

    # 获取原文文本文件
    txt_path = data_dir / "original.txt"
    if not txt_path.exists():
        print(f"❌ 缺少 original.txt 文件：{txt_path}")
        return

    # 输出文件名与音频一致
    output_path = data_dir / f"{audio_stem}.corrected.word.json"

    with open(txt_path, "r", encoding="utf-8") as f_txt:
        correct_text = f_txt.read()

    with open(word_json, "r", encoding="utf-8") as f_json:
        word_items = json.load(f_json)

    corrected = correct_json_by_text(word_items, correct_text)

    with open(output_path, "w", encoding="utf-8") as f_out:
        json.dump(corrected, f_out, ensure_ascii=False, indent=2)

    print(f"✅ 修正完成：{output_path.relative_to(script_dir.parent)}")

if __name__ == "__main__":
    run_corrector()
