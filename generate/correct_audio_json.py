import json
from copy import deepcopy
from pathlib import Path
from target_config import YEAR, QUESTION_NUM, ENABLE_AUTO_ALIGNMENT, COPY_MARKER

def needleman_wunsch_align(seqA, seqB, match=0, mismatch=2, gap=1):
    m, n = len(seqA), len(seqB)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i * gap
    for j in range(n + 1):
        dp[0][j] = j * gap

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = match if seqA[i - 1] == seqB[j - 1] else mismatch
            dp[i][j] = min(
                dp[i - 1][j - 1] + cost,
                dp[i - 1][j] + gap,
                dp[i][j - 1] + gap
            )

    alignment = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (match if seqA[i - 1] == seqB[j - 1] else mismatch):
            alignment.append((seqA[i - 1], seqB[j - 1], i - 1, j - 1))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + gap:
            alignment.append((seqA[i - 1], '-', i - 1, None))
            i -= 1
        else:
            alignment.append(('-', seqB[j - 1], None, j - 1))
            j -= 1
    return alignment[::-1]

def correct_json_by_text(json_data, text_data):
    """
    全量处理：
      1. 对 COPY_MARKER 之前（标记部分）的内容按原逻辑自动对齐，
      2. 然后追加 COPY_MARKER 后的内容（直接复制，不生成时间戳，但保留换行和 bold 处理）。
    """
    punctuation_chars = "、。！？「」（）"
    special_tokens = ["M:", "F:", "Q:", "1.", "2.", "3.", "4.", "M1:", "M2:", "F1", "F2", "Q1", "Q2"]

    # 根据 COPY_MARKER 分割文本
    if COPY_MARKER in text_data:
        parts = text_data.split(COPY_MARKER, 1)
        aligned_part = parts[0]
        extra_part = parts[1]
    else:
        aligned_part = text_data
        extra_part = ""

    fixed_items = []

    if ENABLE_AUTO_ALIGNMENT:
        # 保留原有自动对齐逻辑（处理 COPY_MARKER 前的内容）
        whisper_tokens = [t for t in json_data if t.get("word") and not t.get("role") and t["word"] not in punctuation_chars]
        whisper_chars = [t["word"] for t in whisper_tokens]
        corrected_chars = [c for c in aligned_part if c not in punctuation_chars and c not in ['\n']
                           and all(not aligned_part.startswith(tok, aligned_part.index(c)) for tok in special_tokens)]
        alignment = needleman_wunsch_align(corrected_chars, whisper_chars)

        index_map = {}
        for a, b, i, j in alignment:
            if a != '-' and b != '-' and i is not None and j is not None:
                index_map[i] = whisper_tokens[j]

        i = 0
        while i < len(aligned_part):
            ch = aligned_part[i]
            matched = next((t for t in special_tokens if aligned_part.startswith(t, i)), None)
            if matched:
                fixed_items.append({"role": "bold-word", "word": matched})
                i += len(matched)
                continue
            if ch == "\n":
                fixed_items.append({"role": "line-break", "word": ""})
                i += 1
                continue
            if ch in punctuation_chars:
                fixed_items.append({"word": ch})
                i += 1
                continue

            idx = len([x for x in aligned_part[:i] if x not in punctuation_chars and x != '\n'
                       and all(not aligned_part.startswith(tok, aligned_part.index(x)) for tok in special_tokens)])
            token = deepcopy(index_map.get(idx, {"start": 0.0, "end": 0.0}))
            token["word"] = ch
            fixed_items.append(token)
            i += 1

    # 追加部分：始终生成（如果存在 COPY_MARKER），生成项不附加时间戳
    extra_items = extract_extra_items(text_data)
    fixed_items.extend(extra_items)

    return fixed_items

def extract_extra_items(text_data):
    """
    提取 original.txt 中 COPY_MARKER 后的内容，
    生成对应的 JSON 项（不生成时间戳，但保留换行及 bold 逻辑）。
    为普通字符添加 role "extra"（以便 fix_missing_timestamps 跳过处理），
    并在最前插入一个标记项 "copy-marker"。
    """
    if COPY_MARKER not in text_data:
        return []
    extra_part = text_data.split(COPY_MARKER, 1)[1]
    special_tokens = ["M:", "F:", "Q:", "1.", "2.", "3.", "4.", "M1:", "M2:", "F1", "F2", "Q1", "Q2"]
    items = []
    # 插入标记项
    items.append({"role": "copy-marker", "word": COPY_MARKER})
    i = 0
    while i < len(extra_part):
        ch = extra_part[i]
        matched = next((t for t in special_tokens if extra_part.startswith(t, i)), None)
        if matched:
            items.append({"role": "bold-word", "word": matched})
            i += len(matched)
            continue
        if ch == "\n":
            items.append({"role": "line-break", "word": ""})
            i += 1
            continue
        # 对于普通字符，添加 role "extra"，以避免后续 timestamp 修正
        items.append({"role": "extra", "word": ch})
        i += 1
    return items

def fix_missing_timestamps(items):
    """
    仅对自动对齐部分（非追加项）的项进行时间戳修正，
    对于 role 在 ["copy-marker", "line-break", "bold-word", "extra"] 的项不修正。
    """
    length = len(items)
    for i, item in enumerate(items):
        if "word" not in item or item.get("role") in ["copy-marker", "line-break", "bold-word", "extra"]:
            continue
        if item.get("start", 0.0) > 0.0 and item.get("end", 0.0) > 0.0:
            continue

        prev_end = None
        for j in range(i - 1, -1, -1):
            if items[j].get("end", 0.0) > 0:
                prev_end = items[j]["end"]
                break

        next_start = None
        for j in range(i + 1, length):
            if items[j].get("start", 0.0) > 0:
                next_start = items[j]["start"]
                break

        if prev_end is not None and next_start is not None:
            item["start"] = prev_end
            item["end"] = next_start
        elif prev_end is not None:
            item["start"] = prev_end
            item["end"] = prev_end + 0.01
        elif next_start is not None:
            item["start"] = next_start - 0.01
            item["end"] = next_start
        else:
            item["start"] = 0.0
            item["end"] = 0.01
    return items

def find_file_with_suffixes_case_insensitive(folder: Path, suffixes: list[str]):
    for path in folder.iterdir():
        if not path.is_file():
            continue
        lower = path.name.lower()
        for suffix in suffixes:
            if lower.endswith(suffix.lower()):
                return path
    return None

def run_corrector():
    script_dir = Path(__file__).resolve().parent
    data_dir = script_dir.parent / "data" / YEAR / QUESTION_NUM

    audio_file = find_file_with_suffixes_case_insensitive(data_dir, [".mp3", ".m4a"])
    if not audio_file:
        print(f"❌ 找不到音频文件（.mp3/.m4a）：{data_dir}")
        return
    audio_stem = audio_file.stem

    word_json = find_file_with_suffixes_case_insensitive(data_dir, [".word.json"])
    if not word_json:
        print(f"❌ 找不到 .word.json 文件：{data_dir}")
        return

    txt_path = data_dir / "original.txt"
    if not txt_path.exists():
        print(f"❌ 缺少 original.txt 文件：{txt_path}")
        return

    output_path = data_dir / f"{audio_stem}.corrected.word.json"

    with open(txt_path, "r", encoding="utf-8") as f_txt:
        correct_text = f_txt.read()

    with open(word_json, "r", encoding="utf-8") as f_json:
        word_items = json.load(f_json)

    # 如果 ENABLE_AUTO_ALIGNMENT 为 False 且输出文件已存在，则只读取现有 JSON，再追加 COPY_MARKER 后的内容
    if not ENABLE_AUTO_ALIGNMENT and output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f_existing:
            existing_json = json.load(f_existing)
        # 找到已有 JSON 中的 COPY_MARKER 项位置，删除此项及后面的所有内容
        cutoff = None
        for idx, item in enumerate(existing_json):
            if item.get("role") == "copy-marker" and item.get("word") == COPY_MARKER:
                cutoff = idx
                break
        if cutoff is not None:
            base_json = existing_json[:cutoff]
        else:
            base_json = existing_json
        extra_items = extract_extra_items(correct_text)
        new_json = base_json + extra_items
        # 注意：此处不调用 fix_missing_timestamps，以免影响 base_json 中已固定的时间戳
        with open(output_path, "w", encoding="utf-8") as f_out:
            json.dump(new_json, f_out, ensure_ascii=False, indent=2)
        print(f"✅ 追加完成：{output_path.relative_to(script_dir.parent)}")
    else:
        # 全量处理：执行自动对齐（若启用）和追加部分
        corrected = correct_json_by_text(word_items, correct_text)
        corrected = fix_missing_timestamps(corrected)
        with open(output_path, "w", encoding="utf-8") as f_out:
            json.dump(corrected, f_out, ensure_ascii=False, indent=2)
        print(f"✅ 修正完成：{output_path.relative_to(script_dir.parent)}")

if __name__ == "__main__":
    run_corrector()
