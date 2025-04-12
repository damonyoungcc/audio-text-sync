# generate/generate_subtitles.py

import os
import subprocess
import sys
import json
import config

from target_config import YEAR, QUESTION_NUM

# ======== 可配置部分 ========
MIN_SPEAKERS = "2" #最小说话人数
MAX_SPEAKERS = "3"  #说话人数
SUPPORTED_AUDIO_TYPES = ["mp3", "m4a"] # 支持的音频格式
# =========================

# ======== 不可修改部分 ========
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) # 获取当前文件的绝对路径
DATA_DIR = os.path.join(BASE_DIR, "data") # 数据目录
BASE_PATH = os.path.join(DATA_DIR, YEAR, QUESTION_NUM) # 这里是你要处理的音频文件所在的目录
LANGUAGE = "ja"  # 语言
ALIGN_MODEL = "jonatasgrosman/wav2vec2-large-xlsr-53-japanese" # 对齐模型
COMPUTE_TYPE = "float32" # 计算类型
HF_TOKEN = config.HF_TOKEN #你可以在 huggingface.co 上注册一个账号，然后在设置中找到 token
# ===========================

def generate_subtitles():
    print(f"读取到HF_TOKEN为: {HF_TOKEN}")

    # 自动检测音频文件
    audio_file_found = None
    for filename in os.listdir(BASE_PATH):
        if filename.lower().endswith(tuple(SUPPORTED_AUDIO_TYPES)):
            audio_file_found = filename
            break

    if not audio_file_found:
        print("❌ 指定文件夹下找不到支持的音频文件（mp3 或 m4a）！")
        sys.exit(1)

    base_filename, _ = os.path.splitext(audio_file_found)
    AUDIO_PATH = os.path.join(BASE_PATH, audio_file_found)

    print(f"🎧 使用音频文件: {AUDIO_PATH}")

    # 清理文件夹中非当前音频，这里是每次运行都会清理
    # print("\n🧹 清理文件夹中除当前音频以外的所有文件...")
    # for filename in os.listdir(BASE_PATH):
    #     full_path = os.path.join(BASE_PATH, filename)
    #     if os.path.isfile(full_path) and filename != audio_file_found:
    #         print(f"  🗑 删除: {filename}")
    #         os.remove(full_path)

    # 构建 whisperx 命令
    cmd = [
        "whisperx",
        AUDIO_PATH,
        "--language", LANGUAGE,
        "--output_dir", BASE_PATH,
        "--align_model", ALIGN_MODEL,
        "--compute_type", COMPUTE_TYPE,
        "--output_format", "json",
        # "--diarize",
        "--min_speakers", MIN_SPEAKERS,
        "--max_speakers", MAX_SPEAKERS,
        "--hf_token", HF_TOKEN,
        "--chunk_size", "20",
    ]

    print("\n🚀 正在运行 whisperx：")
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ WhisperX 处理完成，结果保存在: {BASE_PATH}")
    except subprocess.CalledProcessError as e:
        print("\n❌ WhisperX 执行失败！")
        print(f"错误码: {e.returncode}")
        sys.exit(1)

    # 检查生成的 JSON
    json_path = os.path.join(BASE_PATH, f"{base_filename}.json")
    if not os.path.exists(json_path):
        print(f"❌ 未检测到生成的 json 文件: {json_path}，跳过后续步骤。")
        sys.exit(0)
    else:
        print(f"✅ 成功生成 json 文件: {json_path}")

    # 提取 json 文件中的 word_segments 字段，并生成 word.json 文件
    word_json_path = os.path.join(BASE_PATH, f"{base_filename}.word.json")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        word_segments = data.get("word_segments")
        if word_segments is None:
            print("❌ 在生成的 json 文件中未找到 'word_segments' 字段。")
            sys.exit(1)

        with open(word_json_path, 'w', encoding='utf-8') as f:
            json.dump(word_segments, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 成功生成 word.json 文件: {word_json_path}")
    except Exception as e:
        print("❌ 生成 word.json 文件时出错！")
        print(str(e))
        sys.exit(1)

if __name__ == "__main__":
    generate_subtitles()
