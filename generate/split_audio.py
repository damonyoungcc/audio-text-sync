import os
import json
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import AudioClip

def convert_time(time_val):
    """
    将 JSON 中的时间值转换为总秒数。
    假设 time_val 格式为 mm.ss（例如 39.46 表示 39 分 46 秒）。
    """
    # 格式化为两位小数，确保有小数点后两位
    t_str = f"{time_val:.2f}"
    minutes_str, seconds_str = t_str.split('.')
    minutes = int(minutes_str)
    seconds = int(seconds_str)
    return minutes * 60 + seconds

# === 目录配置 ===
SCRIPT_DIR = os.path.dirname(__file__)                   # generate/
DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "data") # data/ 与 generate/ 同级
SEGMENTS_FILENAME = "segments.json"

# === 查找 data 中唯一的音频文件（支持 .mp3 和 .m4a）===
audio_files = [f for f in os.listdir(DATA_DIR) if f.endswith((".mp3", ".m4a"))]
if len(audio_files) != 1:
    print(f"❌ 错误：请确保 data 目录下只有一个音频文件，当前找到: {audio_files}")
    exit(1)

audio_filename = audio_files[0]
audio_path = os.path.join(DATA_DIR, audio_filename)
audio_basename = os.path.splitext(audio_filename)[0]
output_root_dir = os.path.join(DATA_DIR, audio_basename)

# === 输出目录检查 ===
if os.path.exists(output_root_dir):
    print(f"⚠️ 目录已存在，未执行分割操作: {output_root_dir}")
    exit(0)
os.makedirs(output_root_dir)
print(f"✅ 创建输出目录: {output_root_dir}")

# === 加载 segments.json ===
segments_path = os.path.join(DATA_DIR, SEGMENTS_FILENAME)
with open(segments_path, "r", encoding="utf-8") as f:
    segments = json.load(f)

# === 加载整段音频 + 分割 ===
print(f"🔊 正在加载音频: {audio_filename}")
with AudioFileClip(audio_path) as audio:
    for segment in segments:
        # 注意：JSON 中的 start 和 end 格式为 mm.ss（如 39.46 表示 39 分 46 秒）
        start_sec = convert_time(segment["start"])
        end_sec = convert_time(segment["end"])
        duration = end_sec - start_sec

        # 以 filename 去掉 ".mp3" 部分作为子文件夹名
        name = segment["filename"].replace(".mp3", "")
        final_filename = f"{audio_basename}-{name}.mp3"

        subfolder = os.path.join(output_root_dir, name)
        os.makedirs(subfolder, exist_ok=True)
        output_path = os.path.join(subfolder, final_filename)

        # 定义生成函数，返回时间 t (相对于分段起点) 对应的帧
        subclip_audio = AudioClip(lambda t, offset=start_sec: audio.get_frame(t + offset),
                                  duration=duration,
                                  fps=audio.fps)
        subclip_audio.write_audiofile(output_path, logger=None)
        print(f"✅ 导出: {output_path}")

print("🎉 所有音频片段已成功导出！")
