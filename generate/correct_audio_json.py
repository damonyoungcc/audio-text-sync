import json
from copy import deepcopy
from pathlib import Path
from target_config import YEAR, QUESTION_NUM

def needleman_wunsch_align(seqA, seqB, match=0, mismatch=2, gap=1):
    m, n = len(seqA), len(seqB)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(m+1): dp[i][0] = i * gap
    for j in range(n+1): dp[0][j] = j * gap

    for i in range(1, m+1):
        for j in range(1, n+1):
            cost = match if seqA[i-1] == seqB[j-1] else mismatch
            dp[i][j] = min(
                dp[i-1][j-1] + cost,
                dp[i-1][j] + gap,
                dp[i][j-1] + gap
            )

    alignment = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + (match if seqA[i-1] == seqB[j-1] else mismatch):
            alignment.append((seqA[i-1], seqB[j-1], i-1, j-1))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + gap:
            alignment.append((seqA[i-1], '-', i-1, None))
            i -= 1
        else:
            alignment.append(('-', seqB[j-1], None, j-1))
            j -= 1
    return alignment[::-1]

def correct_json_by_text(json_data, text_data):
    punctuation_chars = "、。！？「」（）"
    special_tokens = ["M:", "F:", "Q:", "1.", "2.", "3.", "4.","M1:","M2:","F1","F2","Q1","Q2"]
    whisper_tokens = [t for t in json_data if t.get("word") and not t.get("role") and t["word"] not in punctuation_chars]
    whisper_chars = [t["word"] for t in whisper_tokens]
    corrected_chars = [c for c in text_data if c not in punctuation_chars and c not in ['\n'] and all(not text_data.startswith(tok, text_data.index(c)) for tok in special_tokens)]
    alignment = needleman_wunsch_align(corrected_chars, whisper_chars)

    index_map = {}
    for a, b, i, j in alignment:
        if a != '-' and b != '-' and i is not None and j is not None:
            index_map[i] = whisper_tokens[j]

    fixed_items = []
    i = 0
    while i < len(text_data):
        ch = text_data[i]

        matched = next((t for t in special_tokens if text_data.startswith(t, i)), None)
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

        idx = len([x for x in text_data[:i] if x not in punctuation_chars and x != '\n' and all(not text_data.startswith(tok, text_data.index(x)) for tok in special_tokens)])
        token = deepcopy(index_map.get(idx, {"start": 0.0, "end": 0.0}))
        token["word"] = ch
        fixed_items.append(token)
        i += 1

    return fixed_items

def fix_missing_timestamps(items):
    length = len(items)
    for i, item in enumerate(items):
        if "word" not in item:
            continue
        if item.get("start", 0.0) > 0.0 and item.get("end", 0.0) > 0.0:
            continue

        # 找前一个有 end 的项
        prev_end = None
        for j in range(i - 1, -1, -1):
            if items[j].get("end", 0.0) > 0:
                prev_end = items[j]["end"]
                break

        # 找后一个有 start 的项
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

    corrected = correct_json_by_text(word_items, correct_text)
    corrected = fix_missing_timestamps(corrected)

    with open(output_path, "w", encoding="utf-8") as f_out:
        json.dump(corrected, f_out, ensure_ascii=False, indent=2)

    print(f"✅ 修正完成：{output_path.relative_to(script_dir.parent)}")

if __name__ == "__main__":
    run_corrector()
