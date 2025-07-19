#!/usr/bin/env python
"""
测试数据生成工具

此脚本用于生成爆款剧本数据湖的测试数据，方便开发和测试。
可以生成原始字幕和爆款字幕的对照数据。
"""

import os
import sys
import argparse
import random
import datetime
import json
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.data.hit_pattern_lake import HitPatternLake, convert_to_parquet


def generate_sample_srt_file(output_path: str, 
                           num_scenes: int = 20, 
                           language: str = "zh", 
                           is_hit: bool = False) -> str:
    """
    生成样本SRT文件
    
    Args:
        output_path: 输出文件路径
        num_scenes: 场景数量
        language: 语言
        is_hit: 是否是爆款风格
        
    Returns:
        生成的文件路径
    """
    # 创建目录（如果不存在）
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 场景素材库
    if language == "zh":
        scenes = [
            "老板正在开会，神情严肃",
            "小王匆忙走进办公室，手里拿着文件",
            "张三打开了电脑，查看最新数据",
            "餐厅里，两人低声交谈",
            "李四抬头看了看挂钟，表情焦虑",
            "窗外下着大雨，雨滴敲打着窗户",
            "女主角拿起手机，犹豫着要不要打电话",
            "男主走进电梯，发现里面站着前女友",
            "服务员端着咖啡走过来，脸上带着职业微笑",
            "会议室里，大家鸦雀无声地等待着",
            "小区门口，保安正在检查访客信息",
            "她翻开相册，看到了那张老照片",
            "医院走廊上，家属焦急地等待消息",
            "教室里，老师正在板书，学生们认真记笔记",
            "街道上行人匆匆走过，没人注意角落里的小狗",
            "厨房里，妈妈正在准备晚餐",
            "爸爸站在门口，目送孩子上学",
            "花店老板正在修剪玫瑰的刺",
            "超市收银台前排起了长队",
            "健身房里，几个人正在努力锻炼",
            "公园长椅上，老人独自坐着发呆",
            "咖啡厅角落，年轻人专注地盯着笔记本电脑",
            "机场大厅人来人往，广播不断响起",
            "出租车司机熟练地穿梭在车流中",
            "书店里，顾客安静地翻阅着新书",
            "银行柜台前，客户正在办理业务",
            "菜市场上，小贩吆喝着招揽顾客",
            "电影院外，人们排队等待检票进场",
            "地铁车厢内，大部分人都低头看手机",
            "游泳池边，教练正在指导孩子们"
        ]
        
        # 爆款版改写
        hit_scenes = [
            "老板突然拍桌而起，会议室瞬间安静",
            "小王撞开办公室门，文件散落一地，全场震惊",
            "张三倒吸一口凉气，屏幕上的数据触目惊心",
            "餐厅角落，两人交头接耳，眼神中透露着阴谋",
            "李四死死盯着墙上的时钟，额头渗出冷汗",
            "暴雨如注，窗玻璃几乎被砸碎，室内却出奇安静",
            "女主手握手机，咬着嘴唇，眼泪无声滑落",
            "电梯门缓缓打开，男主与前女友四目相对，时间仿佛静止",
            "服务员笑容背后，眼神中闪过一丝不易察觉的鄙夷",
            "会议室里的空气凝固，所有人大气不敢出，等待最终审判",
            "保安拦住访客，目光锐利，手按对讲机随时待命",
            "相册中那张照片上，有个模糊人影从未被注意过",
            "医院走廊尽头传来急促脚步声，家属猛地站起",
            "粉笔突然折断，老师停下动作，教室陷入诡异沉默",
            "街角的流浪狗突然站起，直视远方，仿佛预感到什么",
            "厨房里的刀具反射着冷光，妈妈的表情异常平静",
            "孩子转身挥手，爸爸眼中闪过一丝预感，这是最后一面",
            "花店老板的手突然被刺扎破，鲜血滴落在纯白玫瑰上",
            "收银台前排队的人群中，有个黑衣人的手按在口袋里",
            "健身房镜子反射出一个不属于任何人的身影",
            "公园长椅上的老人手中握着一张泛黄的照片，眼神空洞",
            "咖啡厅角落的年轻人屏幕上显示着令人不安的信息",
            "机场广播突然中断，人群开始骚动不安",
            "出租车司机的目光频繁看向后视镜，越加焦虑",
            "书店角落的那本书被抽出，露出背后墙上的暗格",
            "银行柜员悄悄按下了桌下的警报按钮",
            "菜市场喧嚣声中，有人悄悄交换了一个神秘包裹",
            "检票口，工作人员对某张票犹豫再三，眼神警觉",
            "地铁车厢内，一个手机屏幕上显示着倒计时",
            "教练的眼神越过孩子们，警惕地盯着泳池另一端的陌生人"
        ]
    else:  # 英文场景
        scenes = [
            "The boss is in a meeting, looking serious",
            "Tom hurries into the office with files in hand",
            "Jack opens his computer to check the latest data",
            "In the restaurant, two people are talking quietly",
            "Mary looks at the clock, her expression anxious",
            "Outside, heavy rain beats against the windows",
            "The woman picks up her phone, hesitating to call",
            "The man enters the elevator and finds his ex-girlfriend inside",
            "The waiter approaches with coffee, wearing a professional smile",
            "In the meeting room, everyone waits in silence",
            "At the community entrance, the security guard checks visitor information",
            "She opens the album and sees that old photograph",
            "In the hospital corridor, family members anxiously await news",
            "In the classroom, the teacher writes on the board while students take notes",
            "Pedestrians hurry past on the street, no one notices the dog in the corner",
            "In the kitchen, mom is preparing dinner",
            "Dad stands at the door, watching his child leave for school",
            "The florist trims the thorns from roses",
            "A long queue forms at the supermarket checkout",
            "In the gym, several people are working out",
            "An elderly person sits alone on a park bench, lost in thought",
            "In the coffee shop corner, a young person focuses on their laptop",
            "The airport hall is busy, announcements playing constantly",
            "The taxi driver navigates skillfully through traffic",
            "In the bookstore, customers quietly browse new books",
            "At the bank counter, customers conduct transactions",
            "At the market, vendors call out to attract customers",
            "Outside the cinema, people queue for ticket inspection",
            "In the subway carriage, most people look down at their phones",
            "By the swimming pool, the coach instructs children"
        ]
        
        # 爆款英文版改写
        hit_scenes = [
            "The boss slams his fist on the table, silencing the room instantly",
            "Tom crashes through the office door, papers flying everywhere, shocking everyone",
            "Jack gasps at the screen, the data sending chills down his spine",
            "In the shadowy corner of the restaurant, two figures whisper conspiratorially",
            "Mary stares at the clock with dread, cold sweat beading on her forehead",
            "The rain pounds violently against the windows, yet inside it's eerily quiet",
            "The woman grips her phone, biting her lip as tears silently stream down her face",
            "As the elevator doors slowly open, time freezes when the man locks eyes with his ex",
            "Behind the waiter's smile lurks a barely perceptible flash of contempt",
            "The air in the meeting room feels solid, everyone holding their breath, awaiting final judgment",
            "The security guard blocks the visitor, eyes sharp, hand poised over his radio",
            "In the album, a blurry figure in the old photograph has never been noticed before",
            "Urgent footsteps echo from the end of the hospital corridor, family members jump to their feet",
            "The chalk suddenly snaps, the teacher freezes, and an uncanny silence falls over the classroom",
            "The stray dog in the corner suddenly stands alert, staring into the distance as if sensing something",
            "Kitchen knives gleam coldly as mom's expression remains unnaturally calm",
            "The child turns to wave goodbye, dad's eyes flash with premonition - this is the last time",
            "The florist's hand is suddenly pierced by a thorn, blood dripping onto pure white roses",
            "In the checkout line, a figure in black has their hand buried deep in their pocket",
            "The gym mirror reflects a shadow that belongs to no one present",
            "On the park bench, the elderly person clutches a yellowed photograph, eyes hollow",
            "The laptop screen in the coffee shop corner displays disturbing information",
            "The airport announcement cuts off abruptly, creating restless movement in the crowd",
            "The taxi driver's eyes flick nervously to the rearview mirror with increasing anxiety",
            "A book pulled from the shelf reveals a hidden compartment in the wall behind",
            "The bank teller discreetly presses the alarm button under the counter",
            "Amid the market noise, a mysterious package changes hands",
            "At the ticket gate, the attendant hesitates over one ticket, eyes alert",
            "On one phone screen in the subway carriage, a countdown timer is running",
            "The swimming coach's gaze moves past the children, warily watching a stranger at the other end"
        ]
    
    # 选择场景集
    scene_list = hit_scenes if is_hit else scenes
    
    # 随机选择场景
    selected_scenes = random.sample(scene_list, min(num_scenes, len(scene_list)))
    
    # 生成SRT内容
    srt_content = ""
    for i, scene in enumerate(selected_scenes, 1):
        start_time = i * 10
        end_time = start_time + 5
        
        # 格式化时间戳
        start_h = start_time // 3600
        start_m = (start_time % 3600) // 60
        start_s = start_time % 60
        
        end_h = end_time // 3600
        end_m = (end_time % 3600) // 60
        end_s = end_time % 60
        
        # 添加字幕块
        srt_content += f"{i}\n"
        srt_content += f"{start_h:02d}:{start_m:02d}:{start_s:02d},000 --> {end_h:02d}:{end_m:02d}:{end_s:02d},000\n"
        srt_content += f"{scene}\n\n"
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    return output_path


def generate_test_data(output_dir: str = "test_data", 
                      num_pairs: int = 5, 
                      languages: list = ["zh", "en"]):
    """
    生成测试数据对
    
    Args:
        output_dir: 输出目录
        num_pairs: 生成的对数
        languages: 语言列表
        
    Returns:
        生成的文件对列表
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pairs = []
    
    for lang in languages:
        lang_dir = output_dir / lang
        lang_dir.mkdir(exist_ok=True)
        
        for i in range(num_pairs):
            # 创建一对原始和爆款字幕文件
            origin_path = lang_dir / f"original_{i+1}.srt"
            hit_path = lang_dir / f"hit_{i+1}.srt"
            
            # 生成SRT文件
            origin_file = generate_sample_srt_file(str(origin_path), num_scenes=random.randint(15, 25), language=lang, is_hit=False)
            hit_file = generate_sample_srt_file(str(hit_path), num_scenes=random.randint(15, 25), language=lang, is_hit=True)
            
            pairs.append((origin_file, hit_file))
            
            print(f"已生成对照数据: {origin_file} -> {hit_file}")
    
    return pairs


def add_test_data_to_lake(pairs: list, lake: HitPatternLake = None):
    """
    将测试数据添加到数据湖
    
    Args:
        pairs: 文件对列表
        lake: 数据湖实例
    
    Returns:
        成功添加的数量
    """
    if lake is None:
        lake = HitPatternLake()
    
    success_count = 0
    
    for origin_file, hit_file in pairs:
        try:
            result = lake.ingest_data(origin_file, hit_file)
            if result:
                success_count += 1
        except Exception as e:
            print(f"添加数据失败: {origin_file} -> {hit_file}, 错误: {e}")
    
    return success_count


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="爆款剧本数据湖测试数据生成工具")
    
    parser.add_argument("--output", "-o", default="data/test_data", 
                      help="输出目录")
    parser.add_argument("--pairs", "-n", type=int, default=5, 
                      help="生成的对照数据对数")
    parser.add_argument("--languages", "-l", nargs="+", default=["zh", "en"], 
                      help="要生成的语言列表")
    parser.add_argument("--add-to-lake", "-a", action="store_true", 
                      help="是否添加到数据湖")
    
    args = parser.parse_args()
    
    print(f"生成测试数据: {args.pairs} 对，语言: {', '.join(args.languages)}")
    
    # 生成测试数据
    data_pairs = generate_test_data(args.output, args.pairs, args.languages)
    
    print(f"成功生成 {len(data_pairs)} 对测试数据")
    
    # 如果需要，添加到数据湖
    if args.add_to_lake:
        print("正在添加数据到数据湖...")
        lake = HitPatternLake()
        success_count = add_test_data_to_lake(data_pairs, lake)
        print(f"成功添加 {success_count}/{len(data_pairs)} 对数据到数据湖")
        
        # 打印统计信息
        stats = lake.get_statistics()
        print("\n数据湖统计信息:")
        print(f"总文件数: {stats.get('total_files', 0)}")
        print(f"对照文件数: {stats.get('pair_files', 0)}")
        print(f"记录数: {stats.get('record_count', 0)}")
        
        if 'modification_types' in stats:
            print("\n转换类型分布:")
            for mod_type, count in stats['modification_types'].items():
                print(f"  {mod_type}: {count}")
    
    print("\n完成测试数据生成")


if __name__ == "__main__":
    main() 