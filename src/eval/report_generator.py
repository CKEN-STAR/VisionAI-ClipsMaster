import os
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime

class HTMLReport:
    """HTML报告生成器，用于创建混剪质量评估的可视化报告"""
    
    def __init__(self, title="VisionAI-ClipsMaster 混剪报告"):
        """初始化HTML报告"""
        self.title = title
        self.sections = []
        self.css = """
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #0066cc; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        h2 { color: #444; margin-top: 30px; border-left: 4px solid #0066cc; padding-left: 10px; }
        h3 { color: #0066cc; margin-top: 25px; }
        .section { margin-bottom: 30px; }
        .chart { width: 100%; margin: 20px 0; border: 1px solid #eee; border-radius: 5px; }
        .summary { background: #f1f8ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .stats { display: flex; flex-wrap: wrap; gap: 20px; }
        .stat-card { flex: 1; min-width: 200px; background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .good { color: #28a745; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        tr:hover { background-color: #f1f8ff; }
        .coverage-module { margin-bottom: 10px; padding: 10px; border-radius: 5px; background: #f8f9fa; }
        .coverage-module h4 { margin: 0 0 10px 0; }
        .coverage-bar { height: 20px; background: #e9ecef; border-radius: 3px; overflow: hidden; margin: 5px 0; }
        .coverage-value { height: 100%; background: linear-gradient(90deg, #28a745, #7fba00); }
        .low-coverage { background: linear-gradient(90deg, #dc3545, #fd7e14) !important; }
        .medium-coverage { background: linear-gradient(90deg, #ffc107, #fd7e14) !important; }

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

        """
        
    def add_section(self, title, content):
        """添加报告章节"""
        self.sections.append({
            "title": title,
            "content": content
        })
        return self
        
    def save(self, filepath):
        """保存HTML报告到文件"""
        html = f"""<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.title}</title>
            <style>{self.css}</style>
        </head>
        <body>
            <div class="container">
                <h1>{self.title}</h1>
                <div class="summary">
                    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
        """
        
        for section in self.sections:
            html += f"""
                <div class="section">
                    <h2>{section['title']}</h2>
                    {section['content']}
                </div>
            """
            
        html += """
            </div>
        </body>
        </html>
        """
        
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"报告已保存至: {os.path.abspath(filepath)}")
        return os.path.abspath(filepath)


def render_version_chart(results):
    """渲染版本兼容性图表"""
    if not results.get('version_data'):
        return "<p>没有可用的版本兼容性数据</p>"
    
    try:
        data = results['version_data']
        fig = px.bar(
            x=list(data.keys()),
            y=list(data.values()),
            labels={'x': '版本', 'y': '兼容性分数'},
            color=list(data.values()),
            color_continuous_scale='Viridis',
            title="模型版本兼容性分析"
        )
        fig.update_layout(height=400)
        return fig.to_html(include_plotlyjs='cdn', full_html=False)
    except Exception as e:
        return f"<p class='error'>渲染版本图表时出错: {str(e)}</p>"


def render_perf_bars(results):
    """渲染性能指标柱状图"""
    if not results.get('performance_data'):
        return "<p>没有可用的性能数据</p>"
    
    try:
        perf = results['performance_data']
        metrics = list(perf.keys())
        values = list(perf.values())
        
        # 创建性能指标柱状图
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=metrics,
            y=values,
            marker_color=['#2c3e50', '#3498db', '#1abc9c', '#9b59b6', '#e74c3c'][:len(metrics)],
            text=values,
            textposition='auto',
        ))
        
        fig.update_layout(
            title="混剪性能指标",
            xaxis_title="指标",
            yaxis_title="分数",
            height=400,
        )
        
        # 添加性能指标说明表格
        table_html = """
        <table>
            <tr>
                <th>指标</th>
                <th>说明</th>
                <th>值</th>
                <th>状态</th>
            </tr>
        """
        
        status_map = {
            '内存峰值': lambda x: 'good' if x < 3.8 else ('warning' if x < 4.5 else 'error'),
            '处理速度': lambda x: 'good' if x > 0.8 else ('warning' if x > 0.5 else 'error'),
            '剧情连贯性': lambda x: 'good' if x > 0.7 else ('warning' if x > 0.5 else 'error'),
            '叙事结构': lambda x: 'good' if x > 0.75 else ('warning' if x > 0.6 else 'error'),
            '工程兼容性': lambda x: 'good' if x > 0.9 else ('warning' if x > 0.7 else 'error'),
            '测试覆盖率': lambda x: 'good' if x >= 80 else ('warning' if x >= 60 else 'error'),
        }
        
        descriptions = {
            '内存峰值': '处理过程中的最大内存占用(GB)',
            '处理速度': '视频处理的相对速度指标(0-1)',
            '剧情连贯性': '生成混剪的故事连贯性评分(0-1)',
            '叙事结构': '故事结构合理性评分(0-1)',
            '工程兼容性': '导出工程文件与目标软件的兼容性(0-1)',
            '测试覆盖率': '代码被测试覆盖的百分比(%)',
        }
        
        for metric, value in zip(metrics, values):
            status = status_map.get(metric, lambda x: 'warning')(value)
            description = descriptions.get(metric, '未知指标')
            
            table_html += f"""
            <tr>
                <td>{metric}</td>
                <td>{description}</td>
                <td>{value}</td>
                <td class="{status}">{
                    '良好' if status == 'good' else ('警告' if status == 'warning' else '异常')
                }</td>
            </tr>
            """
        
        table_html += "</table>"
        
        return fig.to_html(include_plotlyjs='cdn', full_html=False) + table_html
    except Exception as e:
        return f"<p class='error'>渲染性能图表时出错: {str(e)}</p>"


def render_error_map(results):
    """渲染错误热力图"""
    if not results.get('error_data'):
        return "<p>没有检测到错误数据</p>"
    
    try:
        errors = results['error_data']
        
        if not errors:
            return "<p class='good'>未发现明显错误</p>"
            
        # 计算错误分布
        error_types = {}
        error_locations = {}
        
        for error in errors:
            error_type = error.get('type', '未知')
            error_loc = error.get('location', '未知')
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
            error_locations[error_loc] = error_locations.get(error_loc, 0) + 1
        
        # 创建错误类型图表
        fig1 = px.pie(
            values=list(error_types.values()),
            names=list(error_types.keys()),
            title="错误类型分布",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Reds
        )
        
        # 创建错误位置柱状图
        fig2 = px.bar(
            x=list(error_locations.keys()),
            y=list(error_locations.values()),
            title="错误位置分布",
            labels={'x': '位置', 'y': '错误数量'},
            color=list(error_locations.values()),
            color_continuous_scale='Reds',
        )
        
        # 错误详情表格
        table_html = """
        <h3>错误详情列表</h3>
        <table>
            <tr>
                <th>类型</th>
                <th>位置</th>
                <th>描述</th>
                <th>建议</th>
            </tr>
        """
        
        for error in errors:
            table_html += f"""
            <tr>
                <td>{error.get('type', '未知')}</td>
                <td>{error.get('location', '未知')}</td>
                <td>{error.get('description', '无描述')}</td>
                <td>{error.get('suggestion', '无建议')}</td>
            </tr>
            """
        
        table_html += "</table>"
        
        return fig1.to_html(include_plotlyjs='cdn', full_html=False) + \
               fig2.to_html(include_plotlyjs='cdn', full_html=False) + \
               table_html
    except Exception as e:
        return f"<p class='error'>渲染错误图表时出错: {str(e)}</p>"


def render_model_info(results):
    """渲染模型信息部分"""
    if not results.get('model_info'):
        return "<p>没有可用的模型信息</p>"
    
    try:
        model_info = results['model_info']
        
        # 创建模型信息卡片
        html = """
        <div class="stats">
        """
        
        for model_name, info in model_info.items():
            status_class = "good" if info.get('status') == 'active' else "warning"
            status_text = "已激活" if info.get('status') == 'active' else "未激活"
            
            html += f"""
            <div class="stat-card">
                <h3>{model_name}</h3>
                <p><strong>类型:</strong> {info.get('type', '未知')}</p>
                <p><strong>量化:</strong> {info.get('quantization', '未知')}</p>
                <p><strong>状态:</strong> <span class="{status_class}">{status_text}</span></p>
                <p><strong>内存占用:</strong> {info.get('memory_usage', '未知')} GB</p>
            </div>
            """
            
        html += "</div>"
        return html
    except Exception as e:
        return f"<p class='error'>渲染模型信息时出错: {str(e)}</p>"


def render_clip_stats(results):
    """渲染混剪统计信息"""
    if not results.get('clip_stats'):
        return "<p>没有可用的混剪统计信息</p>"
    
    try:
        stats = results['clip_stats']
        
        original_duration = stats.get('original_duration', 0)
        final_duration = stats.get('final_duration', 0)
        compression_ratio = round((original_duration - final_duration) / original_duration * 100 if original_duration else 0, 1)
        
        segments = stats.get('segments', [])
        if segments:
            segment_durations = [s.get('duration', 0) for s in segments]
            avg_segment = sum(segment_durations) / len(segment_durations) if segment_durations else 0
            
            # 创建片段长度分布图
            fig = px.histogram(
                x=segment_durations,
                nbins=10,
                labels={'x': '片段长度(秒)', 'y': '数量'},
                title="混剪片段长度分布",
                color_discrete_sequence=['#3498db']
            )
            
            fig.update_layout(height=400)
            chart_html = fig.to_html(include_plotlyjs='cdn', full_html=False)
        else:
            avg_segment = 0
            chart_html = "<p>没有片段数据可供分析</p>"
        
        # 混剪概览
        summary_html = f"""
        <div class="summary">
            <h3>混剪概览</h3>
            <div class="stats">
                <div class="stat-card">
                    <h4>原片总长度</h4>
                    <p>{format_time(original_duration)}</p>
                </div>
                <div class="stat-card">
                    <h4>混剪结果长度</h4>
                    <p>{format_time(final_duration)}</p>
                </div>
                <div class="stat-card">
                    <h4>压缩比例</h4>
                    <p>{compression_ratio}%</p>
                </div>
                <div class="stat-card">
                    <h4>平均片段长度</h4>
                    <p>{round(avg_segment, 1)}秒</p>
                </div>
                <div class="stat-card">
                    <h4>片段数量</h4>
                    <p>{len(segments)}</p>
                </div>
            </div>
        </div>
        """
        
        return summary_html + chart_html
    except Exception as e:
        return f"<p class='error'>渲染混剪统计时出错: {str(e)}</p>"


def render_coverage_report(results):
    """渲染测试覆盖率报告
    
    Args:
        results: 报告数据字典
        
    Returns:
        HTML字符串
    """
    # 检查是否有覆盖率数据
    if '测试覆盖率' not in results.get('performance_data', {}):
        try:
            # 尝试从文件加载
            coverage_path = os.path.join('output', 'reports', 'coverage_report.json')
            if not os.path.exists(coverage_path):
                return "<p>没有可用的测试覆盖率数据</p>"
                
            with open(coverage_path, 'r', encoding='utf-8') as f:
                coverage_data = json.load(f)
        except Exception as e:
            return f"<p class='warning'>无法加载覆盖率数据: {str(e)}</p>"
    else:
        # 使用性能指标中的总体覆盖率
        overall_coverage = results['performance_data']['测试覆盖率']
        
        try:
            # 尝试从文件加载详细数据
            coverage_path = os.path.join('output', 'reports', 'coverage_report.json')
            if os.path.exists(coverage_path):
                with open(coverage_path, 'r', encoding='utf-8') as f:
                    coverage_data = json.load(f)
            else:
                # 创建简单数据
                coverage_data = {
                    "overall_coverage": overall_coverage,
                    "coverage_threshold": 80.0,
                    "modules": {},
                    "optimization_suggestions": []
                }
        except Exception:
            # 创建简单数据
            coverage_data = {
                "overall_coverage": overall_coverage,
                "coverage_threshold": 80.0,
                "modules": {},
                "optimization_suggestions": []
            }

    try:
        # 提取数据
        overall_coverage = coverage_data.get('overall_coverage', 0)
        threshold = coverage_data.get('coverage_threshold', 80.0)
        modules = coverage_data.get('modules', {})
        suggestions = coverage_data.get('optimization_suggestions', [])
        
        # 状态判断
        status = "good" if overall_coverage >= threshold else ("warning" if overall_coverage >= threshold * 0.75 else "error")
        status_text = "良好" if status == "good" else ("需要改进" if status == "warning" else "严重不足")
        
        # 创建总体覆盖率仪表盘
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = overall_coverage,
            title = {'text': "总体测试覆盖率"},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': "#2c3e50"},
                'bgcolor': "white",
                'steps': [
                    {'range': [0, 50], 'color': "#dc3545"},
                    {'range': [50, threshold * 0.75], 'color': "#ffc107"},
                    {'range': [threshold * 0.75, threshold], 'color': "#7fba00"},
                    {'range': [threshold, 100], 'color': "#28a745"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 3},
                    'thickness': 0.75,
                    'value': threshold
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(l=30, r=30, t=30, b=30)
        )
        
        chart_html = fig.to_html(include_plotlyjs='cdn', full_html=False)
        
        # 创建模块覆盖率可视化
        modules_html = ""
        if modules:
            modules_html = "<h3>模块覆盖率详情</h3>"
            
            # 按覆盖率排序
            sorted_modules = sorted(
                modules.items(), 
                key=lambda x: x[1]['coverage'] if isinstance(x[1], dict) and 'coverage' in x[1] else 0
            )
            
            for module, data in sorted_modules:
                if not isinstance(data, dict) or 'coverage' not in data:
                    continue
                    
                coverage_value = data['coverage']
                bar_class = ""
                if coverage_value < threshold * 0.75:
                    bar_class = "low-coverage"
                elif coverage_value < threshold:
                    bar_class = "medium-coverage"
                
                modules_html += f"""
                <div class="coverage-module">
                    <h4>{module}</h4>
                    <div class="coverage-bar">
                        <div class="coverage-value {bar_class}" style="width: {min(coverage_value, 100)}%;"></div>
                    </div>
                    <small>{coverage_value}% 覆盖率</small>
                </div>
                """
        
        # 创建优化建议
        suggestions_html = ""
        if suggestions:
            suggestions_html = """
            <h3>覆盖率优化建议</h3>
            <table>
                <tr>
                    <th>类型</th>
                    <th>路径</th>
                    <th>建议</th>
                </tr>
            """
            
            for suggestion in suggestions[:10]:  # 最多显示10个建议
                suggestions_html += f"""
                <tr>
                    <td>{suggestion.get('type', '未知')}</td>
                    <td>{suggestion.get('path', '未知')}</td>
                    <td>{suggestion.get('suggestion', '增加测试用例')}</td>
                </tr>
                """
            
            suggestions_html += "</table>"
        
        # 组合所有内容
        summary_html = f"""
        <div class="summary">
            <p>总体覆盖率: <span class="{status}">{overall_coverage}%</span> - 状态: <span class="{status}">{status_text}</span></p>
            <p>覆盖率阈值: {threshold}%</p>
        </div>
        """
        
        return summary_html + chart_html + modules_html + suggestions_html
        
    except Exception as e:
        return f"<p class='error'>渲染覆盖率报告时出错: {str(e)}</p>"


def format_time(seconds):
    """将秒数格式化为时分秒"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"


def generate_html_report(results, output_path="output/reports/clip_report.html"):
    """生成交互式HTML报告"""
    report = HTMLReport(title="VisionAI-ClipsMaster 混剪质量报告")
    
    # 添加模型信息部分
    report.add_section("模型信息", render_model_info(results))
    
    # 添加混剪统计部分
    report.add_section("混剪统计", render_clip_stats(results))
    
    # 添加版本兼容性部分
    report.add_section("版本兼容性", render_version_chart(results))
    
    # 添加性能指标部分
    report.add_section("性能对比", render_perf_bars(results))
    
    # 添加测试覆盖率部分
    report.add_section("测试覆盖率", render_coverage_report(results))
    
    # 添加错误分析部分
    report.add_section("异常追踪", render_error_map(results))
    
    # 保存报告
    return report.save(output_path)


# 测试用例
if __name__ == "__main__":
    # 模拟测试数据
    test_results = {
        "model_info": {
            "Qwen2.5-7B-zh": {
                "type": "中文模型",
                "quantization": "Q4_K_M",
                "status": "active",
                "memory_usage": 3.6
            },
            "Mistral-7B-en": {
                "type": "英文模型",
                "quantization": "Q4_K_M",
                "status": "inactive",
                "memory_usage": 0
            }
        },
        "clip_stats": {
            "original_duration": 3600,  # 1小时
            "final_duration": 360,      # 6分钟
            "segments": [
                {"start": 120, "end": 130, "duration": 10},
                {"start": 240, "end": 265, "duration": 25},
                {"start": 1200, "end": 1215, "duration": 15},
                # ... 更多片段
            ]
        },
        "version_data": {
            "剪映v9.2": 0.95,
            "剪映v9.1": 0.92,
            "剪映v9.0": 0.85,
            "剪映v8.9": 0.70
        },
        "performance_data": {
            "内存峰值": 3.6,
            "处理速度": 0.85,
            "剧情连贯性": 0.78,
            "叙事结构": 0.82,
            "工程兼容性": 0.92,
            "测试覆盖率": 78.5
        },
        "error_data": [
            {
                "type": "时间轴错位",
                "location": "字幕解析",
                "description": "部分SRT时间码与视频不同步",
                "suggestion": "检查SRT文件格式或使用自动对齐工具"
            },
            {
                "type": "剧情跳跃",
                "location": "叙事结构",
                "description": "两个场景之间缺少过渡",
                "suggestion": "调整narrative_analyzer参数或增加场景连贯性阈值"
            },
            {
                "type": "测试覆盖率不足",
                "location": "src/core/clip_generator.py",
                "description": "clip_segments函数",
                "suggestion": "为clip_segments函数添加单元测试"
            }
        ]
    }
    
    # 生成测试报告
    generate_html_report(test_results, "test_report.html") 