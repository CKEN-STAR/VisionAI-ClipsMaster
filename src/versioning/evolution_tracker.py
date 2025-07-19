import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

# Configure logger
logger = logging.getLogger("evolution_tracker")

class VersionDatabase:
    """存储和管理版本谱系关系的数据库类"""

    def __init__(self, db_path: str = None):
        """初始化版本数据库
        
        Args:
            db_path: 数据库文件路径，默认存储在 data/version_db.json
        """
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "version_db.json"
        )
        self._ensure_db_exists()
        self.versions = self._load_database()
    
    def _ensure_db_exists(self) -> None:
        """确保数据库文件存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump({"versions": {}}, f, ensure_ascii=False, indent=2)
    
    def _load_database(self) -> Dict[str, Any]:
        """加载数据库内容"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"加载版本数据库失败: {str(e)}")
            return {"versions": {}}
    
    def _save_database(self) -> None:
        """保存数据库内容"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.versions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存版本数据库失败: {str(e)}")
    
    def add_version(self, version_id: str, parent_id: Optional[str] = None, params: Dict[str, Any] = None) -> bool:
        """添加新版本到数据库
        
        Args:
            version_id: 版本唯一标识符
            parent_id: 父版本ID，如果为None则视为根版本
            params: 版本参数信息
            
        Returns:
            bool: 操作是否成功
        """
        if version_id in self.versions["versions"]:
            logger.warning(f"版本 {version_id} 已存在，无法添加")
            return False
        
        version_info = {
            "id": version_id,
            "parent": parent_id,
            "params": params or {},
            "created_at": datetime.now().isoformat(),
            "children": []
        }
        
        # 添加到版本集合
        self.versions["versions"][version_id] = version_info
        
        # 更新父版本的子版本列表
        if parent_id and parent_id in self.versions["versions"]:
            self.versions["versions"][parent_id]["children"].append(version_id)
        
        self._save_database()
        logger.info(f"成功添加版本 {version_id}")
        return True
    
    def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """获取指定版本信息
        
        Args:
            version_id: 版本ID
            
        Returns:
            版本信息字典或None（如果版本不存在）
        """
        return self.versions["versions"].get(version_id)
    
    def get_lineage(self, version_id: str) -> List[Dict[str, Any]]:
        """获取指定版本的谱系（从根版本到当前版本的路径）
        
        Args:
            version_id: 版本ID
            
        Returns:
            包含所有谱系版本信息的列表
        """
        lineage = []
        current_id = version_id
        
        while current_id:
            current_version = self.get_version(current_id)
            if not current_version:
                break
                
            lineage.insert(0, current_version)  # 在列表前端插入，保持从祖先到后代的顺序
            current_id = current_version.get("parent")
            
        return lineage
    
    def get_all_versions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有版本信息
        
        Returns:
            所有版本信息的字典
        """
        return self.versions["versions"]


class EvolutionTracker:
    """版本演化追踪器，提供版本谱系管理和可视化功能"""
    
    def __init__(self, db_path: Optional[str] = None):
        """初始化版本演化追踪器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db = VersionDatabase(db_path)
    
    def add_version(self, version_id: str, parent_id: Optional[str] = None, params: Dict[str, Any] = None) -> bool:
        """添加新版本
        
        Args:
            version_id: 版本唯一标识符
            parent_id: 父版本ID
            params: 版本参数信息
            
        Returns:
            操作是否成功
        """
        return self.db.add_version(version_id, parent_id, params)
    
    def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """获取指定版本信息
        
        Args:
            version_id: 版本ID
            
        Returns:
            版本信息或None
        """
        return self.db.get_version(version_id)
    
    def visualize_lineage(self, version_id: str) -> Dict[str, Any]:
        """生成版本演化谱系图的数据
        
        Args:
            version_id: 起始版本ID
            
        Returns:
            适用于D3.js树形图的JSON数据
        """
        lineage = self.db.get_lineage(version_id)
        return render_d3_tree({
            "nodes": [{"id": v["id"], "label": v["params"]} for v in lineage],
            "links": [{"source": v["parent"], "target": v["id"]} for v in lineage if v.get("parent")]
        })


def render_d3_tree(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """将谱系数据转换为D3.js树形图数据
    
    Args:
        data: 包含nodes和links的原始谱系数据
        
    Returns:
        适合D3.js可视化的数据结构
    """
    return data


# 创建HTML模板用于D3.js可视化
D3_TREE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <title>版本演化谱系图</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        
        .node circle {
            fill: #69b3a2;
            stroke: #2c3e50;
            stroke-width: 1.5px;
        }
        
        .node text {
            font-size: 12px;
            font-family: sans-serif;
        }
        
        .link {
            fill: none;
            stroke: #ccc;
            stroke-width: 1.5px;
        }
        
        .tooltip {
            position: absolute;
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
        }
    </style>
</head>
<body>
    <div id="tree-container"></div>
    <script>
        // 树形图数据
        const treeData = {json_data};
        
        // 设置画布尺寸
        const width = 800;
        const height = 600;
        
        // 创建树形布局
        const svg = d3.select("#tree-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", "translate(50, 50)");
            
        // 创建工具提示
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip");
        
        // 创建层次结构链接
        const links = treeData.links.map(d => Object.create(d));
        const nodes = treeData.nodes.map(d => Object.create(d));
        
        // 创建力导向图
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("x", d3.forceX(width / 2))
            .force("y", d3.forceY(height / 2));
        
        // 绘制链接
        const link = svg.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke-width", 2);
        
        // 创建节点组
        const node = svg.append("g")
            .attr("class", "nodes")
            .selectAll(".node")
            .data(nodes)
            .enter().append("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        // 为节点添加圆形
        node.append("circle")
            .attr("r", 10)
            .on("mouseover", function(event, d) {
                tooltip.transition()
                    .duration(200)
                    .style("opacity", .9);
                
                let tooltipContent = `<strong>ID:</strong> ${d.id}<br/>`;
                
                if (d.label) {
                    Object.entries(d.label).forEach(([key, value]) => {
                        tooltipContent += `<strong>${key}:</strong> ${value}<br/>`;
                    });
                }
                
                tooltip.html(tooltipContent)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
            })
            .on("mouseout", function() {
                tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);
            });
        
        // 为节点添加文本标签
        node.append("text")
            .attr("dy", -15)
            .style("text-anchor", "middle")
            .text(d => d.id.substring(0, 8) + "...");
        
        // 更新模拟位置
        simulation.on("tick", function() {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("transform", d => `translate(${d.x}, ${d.y})`);
        });
        
        // 拖拽功能
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        
        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
    </script>
</body>
</html>
"""

def generate_html_visualization(tree_data: Dict[str, Any], output_path: str) -> str:
    """生成HTML版本谱系可视化文件
    
    Args:
        tree_data: 树形图数据
        output_path: 输出HTML文件路径
    
    Returns:
        生成的HTML文件路径
    """
    try:
        html_content = D3_TREE_TEMPLATE.replace("{json_data}", json.dumps(tree_data))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    except Exception as e:
        logger.error(f"生成HTML可视化失败: {str(e)}")
        return ""


# 演示用例
def demo():
    """演示版本演化追踪器的使用"""
    # 使用临时文件路径
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_version_db.json")
    
    # 初始化追踪器
    tracker = EvolutionTracker(db_path)
    
    # 添加根版本
    tracker.add_version("v1.0.0", None, {"name": "初始版本", "features": ["基础功能"]})
    
    # 添加子版本
    tracker.add_version("v1.1.0", "v1.0.0", {"name": "功能增强版", "features": ["基础功能", "增强分析"]})
    tracker.add_version("v1.2.0", "v1.0.0", {"name": "性能优化版", "features": ["基础功能", "性能优化"]})
    
    # 添加孙版本
    tracker.add_version("v1.1.1", "v1.1.0", {"name": "功能增强修复版", "features": ["基础功能", "增强分析", "错误修复"]})
    tracker.add_version("v2.0.0", "v1.2.0", {"name": "完整版", "features": ["基础功能", "性能优化", "UI改进", "多语言支持"]})
    
    # 可视化版本谱系
    tree_data = tracker.visualize_lineage("v2.0.0")
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version_evolution.html")
    html_path = generate_html_visualization(tree_data, output_path)
    
    print(f"版本谱系可视化已生成: {html_path}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 运行演示
    demo() 