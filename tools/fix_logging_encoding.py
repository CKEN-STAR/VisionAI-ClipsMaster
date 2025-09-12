#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 日志编码修复脚本
修复emoji和中文字符在日志中的显示问题
"""

import os
import sys
import logging
import platform
from pathlib import Path

def setup_console_encoding():
    """设置控制台编码"""
    print("🔧 设置控制台编码...")
    
    if platform.system() == "Windows":
        try:
            # 设置Windows控制台编码为UTF-8
            os.system("chcp 65001 >nul 2>&1")
            
            # 设置环境变量
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'
            
            print("✅ Windows控制台编码设置完成")
            return True
        except Exception as e:
            print(f"❌ Windows控制台编码设置失败: {e}")
            return False
    else:
        # Linux/Mac系统
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        print("✅ Unix系统编码设置完成")
        return True

def create_safe_logging_handler():
    """创建安全的日志处理器"""
    print("🔧 创建安全日志处理器...")
    
    # 创建自定义的日志处理器类
    handler_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全的日志处理器
处理emoji和特殊字符的编码问题
"""

import logging
import sys
import os

class SafeStreamHandler(logging.StreamHandler):
    """安全的流处理器，处理编码问题"""
    
    def __init__(self, stream=None):
        super().__init__(stream)
        self.encoding = 'utf-8'
    
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            
            # 处理编码问题
            if hasattr(stream, 'mode') and 'b' not in stream.mode:
                # 文本模式
                if hasattr(stream, 'encoding'):
                    # 如果流有编码属性，使用安全编码
                    try:
                        stream.write(msg + self.terminator)
                    except UnicodeEncodeError:
                        # 如果编码失败，移除emoji和特殊字符
                        safe_msg = self._make_safe(msg)
                        stream.write(safe_msg + self.terminator)
                else:
                    # 没有编码属性，直接写入
                    stream.write(msg + self.terminator)
            else:
                # 二进制模式
                msg_bytes = (msg + self.terminator).encode('utf-8', errors='replace')
                stream.write(msg_bytes)
            
            self.flush()
        except Exception:
            self.handleError(record)
    
    def _make_safe(self, text):
        """移除可能导致编码问题的字符"""
        # 移除emoji和特殊Unicode字符
        safe_text = ""
        for char in text:
            try:
                # 尝试编码到GBK（Windows默认编码）
                char.encode('gbk')
                safe_text += char
            except UnicodeEncodeError:
                # 如果无法编码，替换为安全字符
                if ord(char) > 127:
                    safe_text += "?"
                else:
                    safe_text += char
        return safe_text

class SafeFileHandler(logging.FileHandler):
    """安全的文件处理器"""
    
    def __init__(self, filename, mode='a', encoding='utf-8', delay=False):
        super().__init__(filename, mode, encoding, delay)
    
    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            # 如果编码失败，使用安全模式
            try:
                msg = self.format(record)
                safe_msg = self._make_safe(msg)
                
                if self.stream is None:
                    self.stream = self._open()
                
                self.stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)
    
    def _make_safe(self, text):
        """移除可能导致编码问题的字符"""
        return ''.join(char if ord(char) < 128 else '?' for char in text)

def setup_safe_logging():
    """设置安全的日志系统"""
    # 获取根日志记录器
    root_logger = logging.getLogger()
    
    # 移除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加安全的控制台处理器
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 设置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)
    
    # 添加文件处理器
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = SafeFileHandler(log_dir / "visionai_safe.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    root_logger.addHandler(file_handler)
    
    return True
'''
    
    # 保存处理器代码
    handler_file = Path("src/utils/safe_logging.py")
    handler_file.parent.mkdir(parents=True, exist_ok=True)
    handler_file.write_text(handler_code, encoding='utf-8')
    
    print("✅ 安全日志处理器创建完成")
    return True

def patch_rhythm_analyzer():
    """修复节奏分析器中的emoji问题"""
    print("🔧 修复节奏分析器emoji问题...")
    
    rhythm_file = Path("src/core/rhythm_analyzer.py")
    if not rhythm_file.exists():
        print("❌ 节奏分析器文件不存在")
        return False
    
    try:
        content = rhythm_file.read_text(encoding='utf-8')
        
        # 替换emoji为安全字符
        content = content.replace('🎵', '[MUSIC]')
        content = content.replace('🎶', '[NOTE]')
        
        # 保存修改
        rhythm_file.write_text(content, encoding='utf-8')
        
        print("✅ 节奏分析器emoji修复完成")
        return True
    except Exception as e:
        print(f"❌ 节奏分析器修复失败: {e}")
        return False

def create_encoding_test():
    """创建编码测试脚本"""
    print("🔧 创建编码测试脚本...")
    
    test_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码测试脚本
测试各种字符的显示效果
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_encoding():
    """测试编码"""
    print("=" * 50)
    print("编码测试开始")
    print("=" * 50)
    
    # 测试基本中文
    print("✅ 中文测试: 这是中文字符")
    
    # 测试emoji（安全模式）
    print("✅ Emoji测试: [MUSIC] [NOTE] [CHECK] [CROSS]")
    
    # 测试英文
    print("✅ English test: This is English text")
    
    # 测试混合
    print("✅ 混合测试: VisionAI-ClipsMaster 短剧混剪系统")
    
    # 测试日志
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("日志测试: 系统正常运行")
    logger.info("Log test: System running normally")
    logger.info("混合日志: VisionAI-ClipsMaster [MUSIC] 节奏分析完成")
    
    print("=" * 50)
    print("编码测试完成")
    print("=" * 50)

if __name__ == "__main__":
    test_encoding()
'''
    
    test_file = Path("test_encoding.py")
    test_file.write_text(test_code, encoding='utf-8')
    
    print("✅ 编码测试脚本创建完成")
    return True

def main():
    """主修复流程"""
    print("🔧 VisionAI-ClipsMaster 日志编码修复工具")
    print("=" * 60)
    
    success_count = 0
    total_tasks = 4
    
    # 1. 设置控制台编码
    if setup_console_encoding():
        success_count += 1
    
    # 2. 创建安全日志处理器
    if create_safe_logging_handler():
        success_count += 1
    
    # 3. 修复节奏分析器
    if patch_rhythm_analyzer():
        success_count += 1
    
    # 4. 创建编码测试
    if create_encoding_test():
        success_count += 1
    
    print("=" * 60)
    print(f"修复完成: {success_count}/{total_tasks} 项任务成功")
    
    if success_count == total_tasks:
        print("✅ 所有编码问题修复完成！")
        print("\n建议:")
        print("1. 重启终端以应用编码设置")
        print("2. 运行 python test_encoding.py 测试编码效果")
        print("3. 重新启动UI程序测试修复效果")
        return True
    else:
        print("⚠️ 部分修复失败，请检查错误信息")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 编码修复完成")
    else:
        print("\n❌ 编码修复过程中遇到问题")
    
    input("\n按回车键退出...")
