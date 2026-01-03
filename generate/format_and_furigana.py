"""
Combine the alignment + furigana pipeline into a single entry script and
emit a readable preview txt from the final word JSON.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Optional

import correct_audio_json as corrector
from enrich_furigana import enrich_corrected_json_with_furigana
from target_config import COPY_MARKER, QUESTION_NUM, YEAR

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SUPPORTED_AUDIO_SUFFIXES = [".mp3", ".m4a"]


def find_audio_file(data_dir: Path) -> Optional[Path]:
    for suffix in SUPPORTED_AUDIO_SUFFIXES:
        match = next(data_dir.glob(f"*{suffix}"), None)
        if match:
            return match
    return None


def build_corrected_json(year: str, question: str, skip_align: bool = False) -> Optional[Path]:
    data_dir = DATA_DIR / year / question
    audio_file = find_audio_file(data_dir)
    if not audio_file:
        print(f"❌ 找不到音频文件（.mp3/.m4a）：{data_dir}")
        return None

    audio_stem = audio_file.stem
    corrected_path = data_dir / f"{audio_stem}.corrected.word.json"
    word_json_path = data_dir / f"{audio_stem}.word.json"

    if corrected_path.exists():
        print(f"ℹ️  已存在校对文件，直接使用：{corrected_path}")
        return corrected_path

    if skip_align:
        if word_json_path.exists():
            print("⚠️  跳过对齐，直接使用 .word.json。")
            return word_json_path
        print("❌ 跳过对齐但也找不到 .word.json，无法继续。")
        return None

    original_path = data_dir / "original.txt"
    if not original_path.exists():
        print(f"❌ 缺少 original.txt：{original_path}")
        return None
    if not word_json_path.exists():
        print(f"❌ 缺少 whisperx 生成的 .word.json：{word_json_path}")
        return None

    with original_path.open("r", encoding="utf-8") as f_txt:
        text = f_txt.read()
    with word_json_path.open("r", encoding="utf-8") as f_json:
        json_data = json.load(f_json)

    corrected = corrector.correct_json_by_text(json_data, text)
    appended = corrector.extract_appended_items(text)
    corrected.extend(appended)
    corrected = corrector.fix_missing_timestamps(corrected)

    corrected_path.parent.mkdir(parents=True, exist_ok=True)
    with corrected_path.open("w", encoding="utf-8") as f_out:
        json.dump(corrected, f_out, ensure_ascii=False, indent=2)

    print(f"✅ 已生成校对文件：{corrected_path}")
    return corrected_path


def ensure_furigana(year: str, question: str, skip_furigana: bool, corrected_path: Optional[Path]) -> Optional[Path]:
    if skip_furigana or corrected_path is None:
        return corrected_path

    data_dir = DATA_DIR / year / question
    furigana_map_path = data_dir / "kanji_furigana_map.json"
    if not furigana_map_path.exists():
        print(f"⚠️  未找到假名映射表（{furigana_map_path}），跳过假名标注。")
        return corrected_path

    print("🈂️  开始添加假名...")
    enrich_corrected_json_with_furigana(year=year, question=question)
    return corrected_path


def load_word_items(json_path: Path) -> List[dict]:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "word_segments" in data:
        data = data["word_segments"]
    return data


def format_for_preview(items: Iterable[dict]) -> str:
    parts: List[str] = []
    for item in items:
        role = item.get("role")
        word = item.get("word", "")

        if role == "copy-marker":
            marker = word or COPY_MARKER
            parts.append(f"\n{marker}\n")
            continue
        if role == "line-break":
            parts.append("\n")
            continue
        if role == "speaker-label":
            if parts and not parts[-1].endswith("\n"):
                parts.append("\n")
            parts.append(word)
            continue

        if item.get("furigana"):
            word = f"{word}[{item['furigana']}]"
        if role == "bold-word":
            word = f"*{word}*"

        parts.append(word)

    preview = "".join(parts)
    while "\n\n\n" in preview:
        preview = preview.replace("\n\n\n", "\n\n")
    return preview.strip() + "\n"


def write_preview(preview_text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(preview_text)
    print(f"✅ 预览文本已生成：{output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="一次完成：校对 + 假名标注 + 预览 TXT 输出。默认使用 target_config.py 中的 YEAR/QUESTION_NUM。"
    )
    parser.add_argument("--year", default=YEAR, help="例如 2024-07-N3")
    parser.add_argument("--question", default=QUESTION_NUM, help="例如 1-1")
    parser.add_argument("--skip-align", action="store_true", help="跳过 original.txt 对齐校正，直接使用已有 JSON。")
    parser.add_argument("--skip-furigana", action="store_true", help="跳过假名标注。")
    parser.add_argument("--output", type=Path, help="预览 txt 输出路径，默认写到数据目录下的 formatted_preview.txt。")
    args = parser.parse_args()

    corrected_json = build_corrected_json(args.year, args.question, skip_align=args.skip_align)
    corrected_json = ensure_furigana(args.year, args.question, args.skip_furigana, corrected_json)

    if not corrected_json:
        print("❌ 未找到可用的 JSON，退出。")
        return

    word_items = load_word_items(corrected_json)
    preview_text = format_for_preview(word_items)

    output_path = args.output
    if not output_path:
        output_path = DATA_DIR / args.year / args.question / "formatted_preview.txt"

    write_preview(preview_text, output_path)


if __name__ == "__main__":
    main()
