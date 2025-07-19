#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志智能查询引擎

支持自然语言查询日志内容，理解用户意图并返回相关结果。
使用倒排索引和模式匹配，支持多种过滤条件组合。
"""

import os
import re
import json
import time
import datetime
import fnmatch
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from collections import defaultdict

from src.utils.logger import get_module_logger
from src.exporters.log_path import get_log_directory, get_log_file_path
from src.exporters.log_fingerprint import generate_log_summary

# 模块日志记录器
try:
    logger = get_module_logger("log_query")
except:
    import logging

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

logger = logging.getLogger("log_query")
logger.setLevel(logging.INFO)


class LogSearcher:
    """日志智能搜索引擎"""
    
    # 索引字段定义
    INDEX_FIELDS = ["timestamp", "operation", "error_code", "level", "module", "message"]
    
    # 自然语言意图映射
    INTENT_PATTERNS = {
        # 错误相关
        r"错误|异常|失败|报错|问题": "error",
        r"警告|提示|告警": "warning",
        r"内存不足|内存溢出|内存泄漏": "memory",
        # 操作相关
        r"启动|初始化|开始": "startup",
        r"关闭|退出|停止": "shutdown",
        r"训练|学习|投喂": "training",
        r"生成|创建|混剪": "generation",
        # 资源相关
        r"内存|内存占用|RAM": "memory_usage",
        r"模型|加载模型|切换模型": "model",
        r"文件|读取|保存": "file_operation",
        # 时间相关
        r"今天|当天": "today",
        r"昨天": "yesterday",
        r"最近(\d+)小时": "hours",
        r"最近(\d+)分钟": "minutes",
        r"本周|这周": "this_week",
        r"上周": "last_week",
    }
    
    def __init__(self, log_dir: Optional[Union[str, Path]] = None):
        """
        初始化日志搜索器
        
        Args:
            log_dir: 日志目录，默认使用系统日志目录
        """
        # 设置日志目录
        self.log_dir = Path(log_dir) if log_dir else get_log_directory()
        
        # 索引
        self.inverted_index = {}  # 倒排索引
        self.log_entries = []     # 日志条目缓存
        self.indexed_files = set() # 已索引文件
        
        # 重要级别映射
        self.level_priority = {
            "CRITICAL": 5,
            "ERROR": 4,
            "WARNING": 3,
            "INFO": 2,
            "DEBUG": 1
        }
        
        # 初始化索引
        self._build_inverted_index()
        
    def search(self, query: str, limit: int = 100, 
               sort_by: str = "timestamp", sort_desc: bool = True) -> List[Dict[str, Any]]:
        """
        智能搜索日志
        
        支持自然语言查询，如'今天下午的导出错误'，'最近1小时内存不足警告'等
        
        Args:
            query: 自然语言查询字符串
            limit: 返回结果数量限制
            sort_by: 排序字段
            sort_desc: 是否降序排序
            
        Returns:
            符合条件的日志条目列表
        """
        # 记录查询
        logger.info(f"收到查询: '{query}'")
        
        # 解析查询意图
        intents = self._parse_intent(query)
        logger.debug(f"解析到意图: {intents}")
        
        # 根据意图处理特殊查询
        if "error" in intents:
            return self._filter_by_level(["ERROR", "CRITICAL"], limit, sort_by, sort_desc)
            
        if "warning" in intents:
            return self._filter_by_level(["WARNING"], limit, sort_by, sort_desc)
            
        if "memory" in intents:
            return self._filter_by_keyword(["内存", "memory", "OOM", "overflow"], limit, sort_by, sort_desc)
        
        if "startup" in intents:
            return self._filter_by_keyword(["启动", "初始化", "初始", "开始"], limit, sort_by, sort_desc)
            
        if "shutdown" in intents:
            return self._filter_by_keyword(["关闭", "退出", "停止"], limit, sort_by, sort_desc)
            
        if "training" in intents:
            return self._filter_by_keyword(["训练", "学习", "投喂"], limit, sort_by, sort_desc)
            
        if "model" in intents:
            return self._filter_by_keyword(["模型", "model", "加载模型", "切换模型"], limit, sort_by, sort_desc)
            
        # 时间范围处理
        if "today" in intents:
            return self._filter_by_date(datetime.date.today(), limit, sort_by, sort_desc)
            
        if "yesterday" in intents:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            return self._filter_by_date(yesterday, limit, sort_by, sort_desc)
            
        if "hours" in intents and isinstance(intents["hours"], int):
            return self._filter_by_time_range(hours=intents["hours"], limit=limit, 
                                             sort_by=sort_by, sort_desc=sort_desc)
                                             
        if "minutes" in intents and isinstance(intents["minutes"], int):
            return self._filter_by_time_range(minutes=intents["minutes"], limit=limit,
                                             sort_by=sort_by, sort_desc=sort_desc)
        
        # 资源使用查询
        if "memory_usage" in intents:
            # 内存使用超过80%的记录
            return self._filter_by_resource("memory_mb", ">80", limit, sort_by, sort_desc)
        
        # 直接关键词搜索
        return self._search_by_text(query, limit, sort_by, sort_desc)
    
    def _parse_intent(self, query: str) -> Dict[str, Any]:
        """
        解析查询意图
        
        分析自然语言查询，提取用户意图和参数
        
        Args:
            query: 查询字符串
            
        Returns:
            意图字典
        """
        intents = {}
        
        # 处理所有预定义模式
        for pattern, intent_name in self.INTENT_PATTERNS.items():
            match = re.search(pattern, query)
            if match:
                if match.groups():
                    # 如果有捕获组，可能包含数字参数
                    try:
                        value = int(match.group(1))
                        intents[intent_name] = value
                    except (IndexError, ValueError):
                        intents[intent_name] = True
                else:
                    intents[intent_name] = True
        
        return intents
    
    def _build_inverted_index(self):
        """构建日志倒排索引
        
        扫描日志文件，为关键字和字段建立倒排索引，加速查询
        """
        logger.info("开始构建日志索引...")
        
        # 清理现有索引
        self.inverted_index = defaultdict(set)
        self.log_entries = []
        indexed_count = 0
        
        # 查找所有日志文件
        log_files = list(self.log_dir.glob("**/*.log"))
        
        # 确保只索引尚未处理的文件
        new_files = [f for f in log_files if f not in self.indexed_files]
        
        for log_file in new_files:
            try:
                # 处理单个日志文件
                entries = self._index_log_file(log_file)
                indexed_count += len(entries)
                self.indexed_files.add(log_file)
            except Exception as e:
                logger.error(f"索引日志文件 {log_file} 时出错: {str(e)}")
        
        logger.info(f"索引构建完成，共索引 {indexed_count} 条日志记录，来自 {len(new_files)} 个新文件")
    
    def _index_log_file(self, log_file: Path) -> List[Dict[str, Any]]:
        """索引单个日志文件
        
        Args:
            log_file: 日志文件路径
            
        Returns:
            提取的日志条目列表
        """
        entries = []
        
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    # 跳过空行和注释
                    if not line.strip() or line.strip().startswith('#'):
                        continue
                    
                    # 提取日志条目
                    entry = self._parse_log_line(line, log_file, line_num)
                    if entry:
                        # 添加到日志条目列表
                        entry_index = len(self.log_entries)
                        self.log_entries.append(entry)
                        entries.append(entry)
                        
                        # 更新倒排索引
                        self._update_index(entry, entry_index)
                except Exception as e:
                    logger.warning(f"解析日志行时出错 ({log_file}:{line_num}): {str(e)}")
        
        return entries
    
    def _parse_log_line(self, line: str, log_file: Path, line_num: int) -> Optional[Dict[str, Any]]:
        """解析日志行内容
        
        尝试从日志行中提取结构化信息
        
        Args:
            line: 日志行文本
            log_file: 日志文件路径
            line_num: 行号
            
        Returns:
            解析后的日志条目字典，失败返回None
        """
        # 去除哈希指纹部分（如果有）
        clean_line = re.sub(r'\s*<!--\s*hash:[a-f0-9]{64}\s*-->', '', line)
        
        # 尝试匹配常见日志格式
        # 格式1: [2023-04-12 15:30:45] [INFO] message
        match = re.match(r'\[([^\]]+)\]\s*\[([^\]]+)\]\s*(.*)', clean_line)
        if match:
            timestamp_str, level, message = match.groups()
            try:
                timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                timestamp = None
                
            return {
                "timestamp": timestamp.isoformat() if timestamp else None,
                "timestamp_raw": timestamp_str,
                "level": level.upper(),
                "message": message.strip(),
                "source_file": str(log_file),
                "line_number": line_num,
                "raw": clean_line
            }
        
        # 格式2: 2023-04-12 15:30:45 | INFO | module:function:line - message
        match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\|\s*([^|]+)\|\s*([^:]+)(?::([^:]+))?(?::(\d+))?\s*-\s*(.*)', clean_line)
        if match:
            timestamp_str, level, module, function, line_no, message = match.groups()
            try:
                timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                timestamp = None
                
            return {
                "timestamp": timestamp.isoformat() if timestamp else None,
                "timestamp_raw": timestamp_str,
                "level": level.strip().upper(),
                "module": module.strip() if module else None,
                "function": function.strip() if function else None,
                "code_line": int(line_no) if line_no else None,
                "message": message.strip(),
                "source_file": str(log_file),
                "line_number": line_num,
                "raw": clean_line
            }
        
        # 格式3: 简单文本日志（无结构）
        return {
            "timestamp": None,
            "level": None,
            "message": clean_line.strip(),
            "source_file": str(log_file),
            "line_number": line_num,
            "raw": clean_line
        }
    
    def _update_index(self, entry: Dict[str, Any], entry_index: int):
        """更新倒排索引
        
        为日志条目添加到倒排索引中
        
        Args:
            entry: 日志条目
            entry_index: 条目在日志列表中的索引
        """
        # 索引消息内容的所有单词
        if entry.get("message"):
            words = set(re.findall(r'\w+', entry["message"].lower()))
            for word in words:
                if len(word) > 2:  # 忽略太短的词
                    self.inverted_index[word].add(entry_index)
        
        # 索引级别
        if entry.get("level"):
            self.inverted_index[f"level:{entry['level']}"].add(entry_index)
        
        # 索引模块
        if entry.get("module"):
            self.inverted_index[f"module:{entry['module']}"].add(entry_index)
        
        # 索引时间戳（按小时）
        if entry.get("timestamp"):
            try:
                dt = datetime.datetime.fromisoformat(entry["timestamp"])
                hour_key = f"hour:{dt.strftime('%Y%m%d%H')}"
                self.inverted_index[hour_key].add(entry_index)
                
                # 按日期索引
                date_key = f"date:{dt.strftime('%Y%m%d')}"
                self.inverted_index[date_key].add(entry_index)
            except:
                pass
    
    def _filter_by_level(self, levels: List[str], limit: int, 
                        sort_by: str = "timestamp", sort_desc: bool = True) -> List[Dict[str, Any]]:
        """按日志级别过滤
        
        Args:
            levels: 级别列表
            limit: 结果数量限制
            sort_by: 排序字段
            sort_desc: 是否降序排序
            
        Returns:
            过滤后的日志条目
        """
        result_indices = set()
        
        for level in levels:
            level_key = f"level:{level}"
            if level_key in self.inverted_index:
                result_indices.update(self.inverted_index[level_key])
        
        # 获取结果条目
        results = [self.log_entries[i] for i in result_indices]
        
        # 排序和限制结果数量
        return self._sort_and_limit(results, sort_by, sort_desc, limit)
    
    def _filter_by_keyword(self, keywords: List[str], limit: int,
                          sort_by: str = "timestamp", sort_desc: bool = True) -> List[Dict[str, Any]]:
        """按关键词过滤
        
        Args:
            keywords: 关键词列表
            limit: 结果数量限制
            sort_by: 排序字段
            sort_desc: 是否降序排序
            
        Returns:
            过滤后的日志条目
        """
        result_indices = set()
        
        # 对每个关键词查询索引
        for keyword in keywords:
            keyword = keyword.lower()
            # 精确匹配
            if keyword in self.inverted_index:
                result_indices.update(self.inverted_index[keyword])
        
        # 如果索引中没有找到，尝试全文搜索
        if not result_indices:
            results = []
            for entry in self.log_entries:
                for keyword in keywords:
                    if entry.get("message") and keyword.lower() in entry["message"].lower():
                        results.append(entry)
                        break
            return self._sort_and_limit(results, sort_by, sort_desc, limit)
        
        # 获取结果条目
        results = [self.log_entries[i] for i in result_indices]
        
        # 排序和限制结果数量
        return self._sort_and_limit(results, sort_by, sort_desc, limit)
    
    def _filter_by_date(self, date: datetime.date, limit: int,
                       sort_by: str = "timestamp", sort_desc: bool = True) -> List[Dict[str, Any]]:
        """按日期过滤
        
        Args:
            date: 日期
            limit: 结果数量限制
            sort_by: 排序字段
            sort_desc: 是否降序排序
            
        Returns:
            过滤后的日志条目
        """
        date_key = f"date:{date.strftime('%Y%m%d')}"
        result_indices = self.inverted_index.get(date_key, set())
        
        # 获取结果条目
        results = [self.log_entries[i] for i in result_indices]
        
        # 如果索引未找到，尝试遍历检查
        if not results:
            results = []
            date_str = date.strftime('%Y-%m-%d')
            for entry in self.log_entries:
                if entry.get("timestamp") and entry["timestamp"].startswith(date_str):
                    results.append(entry)
        
        # 排序和限制结果数量
        return self._sort_and_limit(results, sort_by, sort_desc, limit)
    
    def _filter_by_time_range(self, hours: int = 0, minutes: int = 0, limit: int = 100,
                             sort_by: str = "timestamp", sort_desc: bool = True) -> List[Dict[str, Any]]:
        """按时间范围过滤
        
        Args:
            hours: 过去小时数
            minutes: 过去分钟数
            limit: 结果数量限制
            sort_by: 排序字段
            sort_desc: 是否降序排序
            
        Returns:
            过滤后的日志条目
        """
        # 计算截止时间
        total_seconds = hours * 3600 + minutes * 60
        if total_seconds <= 0:
            total_seconds = 3600  # 默认1小时
            
        cutoff_time = datetime.datetime.now() - datetime.timedelta(seconds=total_seconds)
        cutoff_str = cutoff_time.isoformat()
        
        # 过滤结果
        results = []
        for entry in self.log_entries:
            if entry.get("timestamp") and entry["timestamp"] >= cutoff_str:
                results.append(entry)
        
        # 排序和限制结果数量
        return self._sort_and_limit(results, sort_by, sort_desc, limit)
    
    def _filter_by_resource(self, resource_name: str, condition: str, limit: int,
                           sort_by: str = "timestamp", sort_desc: bool = True) -> List[Dict[str, Any]]:
        """按资源使用情况过滤
        
        Args:
            resource_name: 资源名称 (memory_mb, cpu_percent等)
            condition: 条件表达式 (">80", "<50"等)
            limit: 结果数量限制
            sort_by: 排序字段
            sort_desc: 是否降序排序
            
        Returns:
            过滤后的日志条目
        """
        # 解析条件
        match = re.match(r'([<>=]+)(\d+(?:\.\d+)?)', condition)
        if not match:
            logger.warning(f"无效的条件表达式: {condition}")
            return []
            
        op, value_str = match.groups()
        try:
            threshold = float(value_str)
        except ValueError:
            logger.warning(f"无效的阈值: {value_str}")
            return []
        
        # 过滤结果
        results = []
        for entry in self.log_entries:
            # 资源信息可能在消息中以JSON格式或特定模式存在
            if entry.get("message"):
                # 尝试从消息中提取资源信息
                resource_value = self._extract_resource_value(entry["message"], resource_name)
                if resource_value is not None:
                    # 应用条件
                    if (op == ">" and resource_value > threshold) or \
                       (op == ">=" and resource_value >= threshold) or \
                       (op == "<" and resource_value < threshold) or \
                       (op == "<=" and resource_value <= threshold) or \
                       (op == "=" and resource_value == threshold):
                        results.append(entry)
        
        # 排序和限制结果数量
        return self._sort_and_limit(results, sort_by, sort_desc, limit)
    
    def _extract_resource_value(self, message: str, resource_name: str) -> Optional[float]:
        """从消息中提取资源值
        
        Args:
            message: 日志消息
            resource_name: 资源名称
            
        Returns:
            提取的资源值，失败返回None
        """
        # 尝试解析JSON
        try:
            # 查找消息中的JSON部分
            json_match = re.search(r'{.*}', message)
            if json_match:
                data = json.loads(json_match.group(0))
                # 尝试从JSON中获取资源值
                if resource_name in data:
                    return float(data[resource_name])
                
                # 检查嵌套结构
                if "resources" in data and resource_name in data["resources"]:
                    return float(data["resources"][resource_name])
        except:
            pass
        
        # 尝试使用正则表达式匹配
        if resource_name == "memory_mb":
            # 匹配内存使用模式，如 "memory: 1024MB" 或 "内存使用: 1024 MB"
            memory_match = re.search(r'(?:memory|内存)\s*(?:usage|使用)?:?\s*(\d+(?:\.\d+)?)\s*(?:MB|mb|兆|M)', message)
            if memory_match:
                return float(memory_match.group(1))
                
        elif resource_name == "cpu_percent":
            # 匹配CPU使用模式，如 "CPU: 80%" 或 "处理器使用率: 80%"
            cpu_match = re.search(r'(?:CPU|处理器)\s*(?:usage|使用率)?:?\s*(\d+(?:\.\d+)?)\s*%', message)
            if cpu_match:
                return float(cpu_match.group(1))
        
        return None
    
    def _search_by_text(self, query: str, limit: int,
                       sort_by: str = "timestamp", sort_desc: bool = True) -> List[Dict[str, Any]]:
        """全文搜索
        
        Args:
            query: 查询文本
            limit: 结果数量限制
            sort_by: 排序字段
            sort_desc: 是否降序排序
            
        Returns:
            搜索结果
        """
        # 分词
        query_words = set(re.findall(r'\w+', query.lower()))
        query_words = {w for w in query_words if len(w) > 2}  # 忽略太短的词
        
        if not query_words:
            # 无有效查询词，返回最近日志
            return self._sort_and_limit(self.log_entries, sort_by, sort_desc, limit)
        
        # 收集每个查询词的结果
        word_results = {}
        for word in query_words:
            if word in self.inverted_index:
                word_results[word] = self.inverted_index[word]
        
        if not word_results:
            # 索引中未找到，尝试全文匹配
            results = []
            for entry in self.log_entries:
                if entry.get("message") and any(word in entry["message"].lower() for word in query_words):
                    results.append(entry)
            return self._sort_and_limit(results, sort_by, sort_desc, limit)
        
        # 取所有词结果的交集
        result_indices = set.intersection(*word_results.values()) if word_results else set()
        
        # 获取结果条目
        results = [self.log_entries[i] for i in result_indices]
        
        # 排序和限制结果数量
        return self._sort_and_limit(results, sort_by, sort_desc, limit)
    
    def _sort_and_limit(self, results: List[Dict[str, Any]], sort_by: str,
                        sort_desc: bool, limit: int) -> List[Dict[str, Any]]:
        """排序并限制结果数量
        
        Args:
            results: 结果列表
            sort_by: 排序字段
            sort_desc: 是否降序排序
            limit: 数量限制
            
        Returns:
            排序后的有限结果
        """
        if not results:
            return []
            
        # 处理特殊排序字段
        if sort_by == "timestamp" and any(entry.get("timestamp") is None for entry in results):
            # 如果有条目缺少timestamp字段，使用line_number作为备选
            sorted_results = sorted(
                results,
                key=lambda x: (x.get("timestamp") or "", x.get("line_number") or 0),
                reverse=sort_desc
            )
        elif sort_by == "level" and any(entry.get("level") for entry in results):
            # 按日志级别优先级排序
            sorted_results = sorted(
                results,
                key=lambda x: self.level_priority.get(x.get("level", ""), 0),
                reverse=sort_desc
            )
        else:
            # 通用排序
            sorted_results = sorted(
                results,
                key=lambda x: (x.get(sort_by) or ""),
                reverse=sort_desc
            )
        
        # 限制结果数量
        return sorted_results[:limit]
    
    def refresh_index(self):
        """刷新索引
        
        重新扫描日志目录，更新索引以包含新日志
        """
        self._build_inverted_index()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取索引统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "indexed_entries": len(self.log_entries),
            "indexed_files": len(self.indexed_files),
            "index_size": len(self.inverted_index),
            "top_words": [],
            "level_distribution": defaultdict(int),
            "time_distribution": {}
        }
        
        # 统计级别分布
        for entry in self.log_entries:
            level = entry.get("level", "UNKNOWN")
            stats["level_distribution"][level] += 1
        
        # 获取最常见的词
        word_count = {word: len(indices) for word, indices in self.inverted_index.items() 
                     if not word.startswith("level:") and not word.startswith("module:") 
                     and not word.startswith("hour:") and not word.startswith("date:")}
        
        top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:20]
        stats["top_words"] = [{"word": word, "count": count} for word, count in top_words]
        
        # 最早和最晚时间戳
        timestamps = [entry.get("timestamp") for entry in self.log_entries if entry.get("timestamp")]
        if timestamps:
            stats["earliest_timestamp"] = min(timestamps)
            stats["latest_timestamp"] = max(timestamps)
        
        return stats


# 全局日志搜索器实例
_log_searcher = None

def get_log_searcher() -> LogSearcher:
    """获取全局日志搜索器实例
    
    Returns:
        日志搜索器实例
    """
    global _log_searcher
    try:
        if _log_searcher is None:
            _log_searcher = LogSearcher()
    except Exception as e:
        logger.error(f"初始化日志搜索器失败: {str(e)}")
        # 创建一个空搜索器而不失败
        _log_searcher = LogSearcher.__new__(LogSearcher)
        _log_searcher.log_dir = get_log_directory()
        _log_searcher.inverted_index = {}
        _log_searcher.log_entries = []
        _log_searcher.indexed_files = set()
        _log_searcher.level_priority = {
            "CRITICAL": 5, "ERROR": 4, "WARNING": 3, "INFO": 2, "DEBUG": 1
        }
    return _log_searcher

def search_logs(query: str, limit: int = 100) -> List[Dict[str, Any]]:
    """搜索日志的便捷函数
    
    Args:
        query: 查询字符串
        limit: 结果数量限制
        
    Returns:
        搜索结果
    """
    searcher = get_log_searcher()
    return searcher.search(query, limit)

def get_log_statistics() -> Dict[str, Any]:
    """获取日志统计的便捷函数
    
    Returns:
        统计信息
    """
    searcher = get_log_searcher()
    return searcher.get_statistics()


if __name__ == "__main__":
    # 如果直接运行此模块，执行简单的演示
    searcher = LogSearcher()
    
    # 显示索引统计
    stats = searcher.get_statistics()
    print(f"日志索引统计:")
    print(f"  索引条目数: {stats['indexed_entries']}")
    print(f"  索引文件数: {stats['indexed_files']}")
    print(f"  索引大小: {stats['index_size']}")
    
    if stats['indexed_entries'] > 0:
        print("\n级别分布:")
        for level, count in stats['level_distribution'].items():
            print(f"  {level}: {count}")
        
        print("\n示例查询:")
        query = "错误"
        results = searcher.search(query)
        print(f"查询 '{query}' 结果: {len(results)} 条")
        
        for i, entry in enumerate(results[:5]):
            print(f"\n[{i+1}] {entry.get('timestamp_raw', 'N/A')} | {entry.get('level', 'N/A')}")
            print(f"    {entry.get('message', 'N/A')}")
    else:
        print("\n未找到日志条目。请确保日志目录中有日志文件。") 