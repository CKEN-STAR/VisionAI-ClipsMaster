"""
训练数据输入模块 - 用于向模型提供训练数据
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFileDialog, QListWidget, QListWidgetItem, QFormLayout, QComboBox, QCheckBox, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QSize

class TrainingFeeder(QWidget):
    """训练数据输入模块，用于加载和提供训练数据"""
    
    # 信号定义
    training_started = pyqtSignal(list, str, bool, str)  # 原始字幕路径列表, 爆款字幕文本, 是否使用GPU, 语言模式
    
    def __init__(self, parent=None):
        """初始化训练数据输入模块
        
        Args:
            parent: 父级组件
        """
        super().__init__(parent)
        self.original_srt_paths = []  # 原始字幕文件路径列表
        self.viral_srt_text = ""      # 爆款字幕文本
        self.use_gpu = True           # 是否使用GPU
        self.language_mode = "zh"     # 语言模式：中文/英文
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 标题
        title = QLabel("训练数据准备")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # 原始字幕和爆款字幕并排布局
        srt_layout = QHBoxLayout()
        main_layout.addLayout(srt_layout)
        
        # 左侧：原始字幕部分
        original_layout = QVBoxLayout()
        srt_layout.addLayout(original_layout)
        
        # 原始字幕标题
        original_label = QLabel("原始字幕")
        original_label.setStyleSheet("font-weight: bold;")
        original_layout.addWidget(original_label)
        
        # 原始字幕列表
        self.original_srt_list = QListWidget()
        self.original_srt_list.setMinimumHeight(150)
        self.original_srt_list.currentItemChanged.connect(self.preview_original_srt)
        original_layout.addWidget(self.original_srt_list)
        
        # 原始字幕按钮组
        original_btn_layout = QHBoxLayout()
        original_layout.addLayout(original_btn_layout)
        
        self.add_original_btn = QPushButton("导入字幕")
        self.add_original_btn.clicked.connect(self.import_original_srt)
        original_btn_layout.addWidget(self.add_original_btn)
        
        self.remove_original_btn = QPushButton("移除字幕")
        self.remove_original_btn.clicked.connect(self.remove_original_srt)
        original_btn_layout.addWidget(self.remove_original_btn)
        
        # 右侧：爆款字幕部分
        viral_layout = QVBoxLayout()
        srt_layout.addLayout(viral_layout)
        
        # 爆款字幕标题
        viral_label = QLabel("爆款字幕")
        viral_label.setStyleSheet("font-weight: bold;")
        viral_layout.addWidget(viral_label)
        
        # 爆款字幕编辑区
        self.viral_srt_edit = QTextEdit()
        self.viral_srt_edit.setPlaceholderText("在此输入或粘贴爆款字幕...")
        self.viral_srt_edit.setMinimumHeight(150)
        viral_layout.addWidget(self.viral_srt_edit)
        
        # 爆款字幕按钮组
        viral_btn_layout = QHBoxLayout()
        viral_layout.addLayout(viral_btn_layout)
        
        self.import_viral_btn = QPushButton("从文件导入")
        self.import_viral_btn.clicked.connect(self.import_viral_srt)
        viral_btn_layout.addWidget(self.import_viral_btn)
        
        self.clear_viral_btn = QPushButton("清空内容")
        self.clear_viral_btn.clicked.connect(lambda: self.viral_srt_edit.clear())
        viral_btn_layout.addWidget(self.clear_viral_btn)
        
        # 预览区域
        preview_label = QLabel("预览:")
        preview_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(preview_label)
        
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setMinimumHeight(100)
        self.preview_edit.setPlaceholderText("选择左侧原始字幕以预览内容...")
        main_layout.addWidget(self.preview_edit)
        
        # 训练设置
        settings_layout = QFormLayout()
        main_layout.addLayout(settings_layout)
        
        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "英文"])
        self.language_combo.currentIndexChanged.connect(
            lambda idx: self.switch_training_language("zh" if idx == 0 else "en")
        )
        settings_layout.addRow("语言模式:", self.language_combo)
        
        # GPU设置
        self.gpu_checkbox = QCheckBox("启用GPU加速")
        self.gpu_checkbox.setChecked(True)
        self.gpu_checkbox.stateChanged.connect(lambda state: setattr(self, 'use_gpu', state == Qt.CheckState.Checked))
        settings_layout.addRow("GPU设置:", self.gpu_checkbox)
        
        # 开始训练按钮
        self.train_btn = QPushButton("开始学习")
        self.train_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 8px;")
        self.train_btn.setMinimumHeight(40)
        self.train_btn.clicked.connect(self.start_training)
        main_layout.addWidget(self.train_btn)
        
    def switch_training_language(self, lang_mode):
        """切换训练语言模式
        
        Args:
            lang_mode: 语言模式代码，'zh'表示中文，'en'表示英文
        """
        self.language_mode = lang_mode
        if lang_mode == "zh":
            self.language_combo.setCurrentIndex(0)
        else:
            self.language_combo.setCurrentIndex(1)
            
    def import_original_srt(self):
        """导入原始字幕文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择原始字幕文件", "", "字幕文件 (*.srt *.ass *.vtt)"
        )
        
        for file_path in file_paths:
            if file_path:
                # 检查是否已经添加
                existing_items = [
                    self.original_srt_list.item(i).data(Qt.ItemDataRole.UserRole)
                    for i in range(self.original_srt_list.count())
                ]
                
                if file_path not in existing_items:
                    # 添加到列表
                    item = QListWidgetItem(file_path.split('/')[-1])
                    item.setData(Qt.ItemDataRole.UserRole, file_path)
                    self.original_srt_list.addItem(item)
                    self.original_srt_paths.append(file_path)
                    
    def remove_original_srt(self):
        """移除选中的原始字幕"""
        selected_items = self.original_srt_list.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            row = self.original_srt_list.row(item)
            self.original_srt_list.takeItem(row)
            
            # 从路径列表中移除
            if file_path in self.original_srt_paths:
                self.original_srt_paths.remove(file_path)
                
    def preview_original_srt(self, current, previous):
        """预览原始字幕内容
        
        Args:
            current: 当前选中的项
            previous: 先前选中的项
        """
        if not current:
            self.preview_edit.clear()
            return
            
        file_path = current.data(Qt.ItemDataRole.UserRole)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.preview_edit.setPlainText(content)
        except Exception as e:
            self.preview_edit.setPlainText(f"无法读取文件: {str(e)}")
            
    def import_viral_srt(self):
        """从文件导入爆款字幕"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择爆款字幕文件", "", "字幕文件 (*.srt *.ass *.vtt);;文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.viral_srt_edit.setPlainText(content)
            except Exception as e:
                QMessageBox.warning(self, "导入失败", f"无法读取文件: {str(e)}")
                
    def start_training(self):
        """开始训练数据学习"""
        # 获取爆款字幕文本
        viral_text = self.viral_srt_edit.toPlainText().strip()
        
        # 验证输入
        if not self.original_srt_paths:
            QMessageBox.warning(self, "缺少数据", "请至少导入一个原始字幕文件")
            return
            
        if not viral_text:
            QMessageBox.warning(self, "缺少数据", "请输入爆款字幕内容")
            return
            
        # 触发训练信号
        self.viral_srt_text = viral_text
        self.training_started.emit(
            self.original_srt_paths,
            viral_text,
            self.use_gpu,
            self.language_mode
        ) 