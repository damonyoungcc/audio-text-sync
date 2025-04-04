# generate/__main__.py
# 主入口：依次执行字幕生成 + 配置更新

from generate_subtitles import generate_subtitles
from update_config import update_dir_config
from correct_audio_json import run_corrector

if __name__ == "__main__":
    generate_subtitles()
    run_corrector()
    update_dir_config()