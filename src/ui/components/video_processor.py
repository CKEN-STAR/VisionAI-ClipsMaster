from src.exporters import (
    validate_timeline,
    check_references,
    check_type_consistency,
    check_legal_metadata,
    validate_xml_legal_compliance,
    inject_missing_legal_elements,
    backward_compatibility_fix,
    process_xml_file
)

def export_project(self, output_path, project_format="jianying"):
    """导出项目文件
    
    Args:
        output_path: 输出路径
        project_format: 项目格式，支持 "jianying", "davinci", "fcpxml" 等
        
    Returns:
        bool: 是否成功导出
    """
    try:
        # ... existing code ...
        
        # 在导出前验证法律合规性
        if not self._validate_legal_compliance(output_path):
            logger.warning("法律合规性验证失败，尝试自动修复")
            if not self._fix_legal_compliance(output_path):
                logger.error("法律合规性修复失败")
                self.export_error.emit("导出失败：法律合规性验证失败")
                return False
        
        # ... rest of the existing code ...
    
    except Exception as e:
        logger.error(f"导出项目失败: {str(e)}")
        self.export_error.emit(f"导出失败: {str(e)}")
        return False

def _validate_legal_compliance(self, xml_path):
    """验证法律合规性
    
    Args:
        xml_path: XML文件路径
        
    Returns:
        bool: 是否合规
    """
    try:
        result = validate_xml_legal_compliance(xml_path)
        if not result["valid"]:
            missing = ", ".join(result["missing_elements"])
            logger.warning(f"法律合规性验证失败，缺少元素: {missing}")
            return False
        return True
    except Exception as e:
        logger.error(f"法律合规性验证错误: {str(e)}")
        return False

def _fix_legal_compliance(self, xml_path):
    """修复法律合规性问题
    
    Args:
        xml_path: XML文件路径
        
    Returns:
        bool: 是否成功修复
    """
    try:
        return inject_missing_legal_elements(xml_path, self.language_mode)
    except Exception as e:
        logger.error(f"修复法律合规性问题失败: {str(e)}")
        return False

def export_project_with_version(self, output_path, target_version="3.0", project_format="jianying"):
    """导出特定版本的项目文件
    
    Args:
        output_path: 输出路径
        target_version: 目标版本号，默认为3.0
        project_format: 项目格式，支持 "jianying", "davinci", "fcpxml" 等
        
    Returns:
        bool: 是否成功导出
    """
    try:
        # 首先执行标准导出
        temp_output = f"{output_path}.temp.xml"
        if not self.export_project(temp_output, project_format):
            return False
        
        # 进行版本兼容性适配
        success = process_xml_file(temp_output, output_path, target_version)
        
        # 删除临时文件
        try:
            os.remove(temp_output)
        except:
            pass
        
        if not success:
            logger.error(f"版本兼容性适配失败: {temp_output} -> {target_version}")
            self.export_error.emit(f"导出失败: 无法转换为版本 {target_version}")
            return False
        
        logger.info(f"成功导出项目并适配为版本 {target_version}: {output_path}")
        self.export_success.emit(f"已导出版本 {target_version} 的项目文件: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"导出特定版本项目失败: {str(e)}")
        self.export_error.emit(f"导出失败: {str(e)}")
        return False

# ... rest of the existing code ... 