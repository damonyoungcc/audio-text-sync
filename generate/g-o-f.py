import os
import re
import json
from target_config import YEAR, QUESTION_NUM

# 获取基础目录，data目录与generate同级
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
BASE_PATH = os.path.join(DATA_DIR, YEAR, QUESTION_NUM)

def generate_kanji_furigana_map():
    input_file = os.path.join(BASE_PATH, "o-f.txt")
    output_file = os.path.join(BASE_PATH, "kanji_furigana_map.json")
    
    if not os.path.exists(input_file):
        print(f"❌ 找不到输入文本文件: {input_file}")
        return
    
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()
    
    # 正则表达式：匹配单个汉字后紧跟着 [] 内的内容
    pattern = re.compile(r'([\u4e00-\u9fff])\[(.*?)\]')
    matches = pattern.findall(text)
    
    # 构造映射列表，保持顺序且不去重
    mapping_list = []
    for kanji, furigana in matches:
        mapping_list.append({kanji: furigana})
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(mapping_list, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 生成完成：{output_file}")

if __name__ == "__main__":
    generate_kanji_furigana_map()
