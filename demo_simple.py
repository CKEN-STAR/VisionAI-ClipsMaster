#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版模式挖掘演示
"""

import json
from src.core.narrative_unit_splitter import NarrativeUnitSplitter
from src.algorithms.pattern_mining import PatternMiner

def main():
    # 示例文本
    text = """
    小红今天过生日，但她觉得所有人都忘记了这件事。
    上学路上，同学们都很正常地和她打招呼，没有任何特别之处。
    整个上午的课程中，连最好的朋友都没有提起她的生日。
    下午放学时，小红失落地收拾书包，准备独自回家。
    "小红，你能帮我拿一下东西吗？在活动室。"班长突然走过来说。
    小红勉强点点头，跟着班长走向活动室。
    推开门的一瞬间，教室里突然亮起彩灯，所有同学跳出来高喊："生日快乐！"
    小红惊讶地张大嘴巴，眼泪涌了出来。原来大家都记得，而且精心准备了这个惊喜。
    那天，在欢笑与祝福中，小红度过了最难忘的生日。
    """
    
    print("1. 分割叙事节拍...")
    splitter = NarrativeUnitSplitter()
    beats = splitter.split_into_beats(text)
    
    print(f"   识别出 {len(beats)} 个叙事节拍")
    for i, beat in enumerate(beats):
        print(f"   节拍 {i+1}: 类型={beat['type']}, 文本={beat['text'][:30]}...")
    
    print("\n2. 提取叙事指纹...")
    miner = PatternMiner()
    fingerprint = miner.extract_narrative_fingerprint(beats)
    print(json.dumps(fingerprint, ensure_ascii=False, indent=2))
    
    print("\n演示完成!")

if __name__ == "__main__":
    main() 