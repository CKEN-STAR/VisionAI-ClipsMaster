"""
创建项目favicon图标

简单脚本，为API文档创建一个基本的favicon图标
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_simple_favicon(output_path, size=(32, 32)):
    """
    创建简单的favicon图标
    
    Args:
        output_path: 输出路径
        size: 图标尺寸
    """
    # 创建一个新图像，使用RGBA模式支持透明度
    img = Image.new('RGBA', size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 定义颜色
    primary_color = (52, 152, 219)  # 蓝色
    secondary_color = (46, 204, 113)  # 绿色
    
    # 绘制圆形背景
    draw.ellipse([(0, 0), size], fill=primary_color)
    
    # 在中心绘制一个小圆形
    center = (size[0] // 2, size[1] // 2)
    radius = size[0] // 4
    draw.ellipse(
        [(center[0] - radius, center[1] - radius), 
         (center[0] + radius, center[1] + radius)], 
        fill=secondary_color
    )
    
    # 尝试绘制文本 "V"（如果有可用字体）
    try:
        # 尝试使用系统字体
        font_size = size[0] // 2
        font = ImageFont.truetype("arial.ttf", font_size)
        text_width, text_height = draw.textbbox((0, 0), "V", font=font)[2:4]
        position = (
            center[0] - text_width // 2, 
            center[1] - text_height // 2 - font_size // 4
        )
        draw.text(position, "V", fill="white", font=font)
    except Exception:
        # 如果无法加载字体，就不添加文字
        pass
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 保存图像
    img.save(output_path, format="PNG")
    print(f"favicon已生成: {output_path}")

if __name__ == "__main__":
    # 确定项目根目录和输出路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../.."))
    static_dir = os.path.join(project_root, "src", "static")
    
    # 确保静态目录存在
    os.makedirs(static_dir, exist_ok=True)
    
    # 生成favicon
    favicon_path = os.path.join(static_dir, "favicon.png")
    create_simple_favicon(favicon_path) 