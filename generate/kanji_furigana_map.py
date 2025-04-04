# 目前汉字对应假名的效果不太理想，所以暂时不使用
# 目前是在让chatgpt生成original.txt时，给出汉字对应假名的映射表，手动来
# 还没有更准确的方案，待续
import os
import json
from fugashi import Tagger
from target_config import YEAR, QUESTION_NUM

tagger = Tagger()

def is_kanji(char):
    return '\u4e00' <= char <= '\u9fff'

def split_reading_evenly(reading, kanji_count):
    """粗略将词的假名按汉字数量平均切分"""
    length = len(reading)
    chunk_size = max(length // kanji_count, 1)
    return [reading[i * chunk_size: (i + 1) * chunk_size] for i in range(kanji_count)]

def katakana_to_hiragana(text):
    return ''.join(
        chr(ord(ch) - 0x60) if 'ァ' <= ch <= 'ン' else ch
        for ch in text
    )

def generate_kanji_furigana_map(year=YEAR, question=QUESTION_NUM, save_path=None):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    text_path = os.path.join(base_dir, 'data', year, question, 'original.txt')

    if not os.path.exists(text_path):
        raise FileNotFoundError(f"原文文件不存在: {text_path}")

    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read()

    furigana_map = {}

    for token in tagger(text):
        surface = token.surface
        reading = token.feature.kana or surface
        reading = katakana_to_hiragana(reading)

        # 筛选包含汉字的词
        if any(is_kanji(ch) for ch in surface):
            kanji_chars = [ch for ch in surface if is_kanji(ch)]
            if len(kanji_chars) == 1:
                kanji = kanji_chars[0]
                if kanji not in furigana_map:
                    furigana_map[kanji] = reading
            else:
                # 多个汉字的词：平均分配假名
                furiganas = split_reading_evenly(reading, len(kanji_chars))
                for k, r in zip(kanji_chars, furiganas):
                    if k not in furigana_map:
                        furigana_map[k] = r

    if not save_path:
        save_path = os.path.join(base_dir, 'data', year, question, 'kanji_furigana_map.json')

    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(furigana_map, f, ensure_ascii=False, indent=2)

    print(f"✅ 漢字ふりがなマップ已保存到: {save_path}")
    return furigana_map


# 如果作为独立脚本运行
if __name__ == "__main__":
    generate_kanji_furigana_map()
