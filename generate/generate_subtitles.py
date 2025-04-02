# generate/generate_subtitles.py

import os
import subprocess
import sys
import config

# ======== 可配置部分 ========
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
BASE_PATH = os.path.join(DATA_DIR, "2020", "q2")  # 修改这里指定要处理的音频目录
LANGUAGE = "ja"
ALIGN_MODEL = "jonatasgrosman/wav2vec2-large-xlsr-53-japanese"
COMPUTE_TYPE = "float32"
MIN_SPEAKERS = "2"
MAX_SPEAKERS = "2"
HF_TOKEN = config.HF_TOKEN
SUPPORTED_AUDIO_TYPES = ["mp3", "m4a"]
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

    FILENAME, ext = os.path.splitext(audio_file_found)
    AUDIO_PATH = os.path.join(BASE_PATH, audio_file_found)

    print(f"🎧 使用音频文件: {AUDIO_PATH}")

    # 清理文件夹中非当前音频
    print("\n🧹 清理文件夹中除当前音频以外的所有文件...")
    for filename in os.listdir(BASE_PATH):
        full_path = os.path.join(BASE_PATH, filename)
        if os.path.isfile(full_path) and filename != audio_file_found:
            print(f"  🗑 删除: {filename}")
            os.remove(full_path)

    # 构建 whisperx 命令
    cmd = [
        "whisperx",
        AUDIO_PATH,
        "--language", LANGUAGE,
        "--output_dir", BASE_PATH,
        "--align_model", ALIGN_MODEL,
        "--compute_type", COMPUTE_TYPE,
        "--output_format", "json",
        "--diarize",
        "--min_speakers", MIN_SPEAKERS,
        "--max_speakers", MAX_SPEAKERS,
        "--hf_token", HF_TOKEN,
        "--model", "large-v2"
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
    json_path = os.path.join(BASE_PATH, f"{FILENAME}.json")
    if not os.path.exists(json_path):
        print(f"❌ 未检测到生成的 json 文件: {json_path}，跳过后续步骤。")
        sys.exit(0)
    else:
        print(f"✅ 成功生成 json 文件: {json_path}")

if __name__ == "__main__":
    generate_subtitles()
