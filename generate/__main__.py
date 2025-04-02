# generate/__main__.py
# 主入口：依次执行字幕生成 + 配置更新

from generate_subtitles import generate_subtitles
from update_config import update_dir_config

if __name__ == "__main__":
    generate_subtitles()
    update_dir_config()
