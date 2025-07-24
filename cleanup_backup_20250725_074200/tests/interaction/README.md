# VisionAI-ClipsMaster 用户交互测试工具包

这个模块提供了用于测试UI界面的工具集，包括用户操作模拟、控件定位功能和状态验证功能。

## 模块组件

1. **用户操作模拟引擎** - 支持点击、拖放、键盘输入和触摸手势等操作
2. **智能控件定位系统** - 支持多种定位策略的控件查找
3. **状态验证框架** - 验证UI界面状态的多种方式
4. **UI测试框架** - 自动化UI测试和结果验证

## 功能特点

### 用户操作模拟引擎

- **基本操作模拟**：点击、拖放、键盘输入
- **触摸手势模拟**：单击、双击、长按、滑动等
- **复杂操作序列**：支持组合多个操作为序列
- **兼容性设计**：同时支持PyQt6和PyQt5

### 控件定位系统

- **AI视觉识别**：通过视觉描述定位控件
- **属性匹配**：通过控件属性定位
- **对象名称**：通过控件的objectName定位
- **文本内容**：通过控件显示的文本定位
- **相对位置**：通过相对于已知控件的位置定位
- **视觉辅助**：支持OCR和图像模板匹配

### 状态验证框架

- **属性验证**：验证控件的属性值（文本、可见性、启用状态等）
- **视觉验证**：通过图像比较验证UI状态
- **位置验证**：验证控件的位置和大小
- **数据模型验证**：验证控件的数据模型
- **颜色验证**：验证控件的颜色属性
- **样式验证**：验证控件的CSS样式属性

## 使用方法

### 用户操作模拟

```python
from tests.interaction.action_simulator import UserActionSimulator

# 创建模拟器
simulator = UserActionSimulator(delay_between_actions=100)

# 模拟点击
simulator.simulate_click(button_widget)

# 模拟拖放
simulator.simulate_drag(source_widget, target_widget)

# 模拟键盘输入
simulator.simulate_keystrokes(text_edit, "要输入的文本")

# 模拟特殊键
simulator.simulate_keystrokes(text_edit, "[enter]")  # 支持enter, tab, esc等特殊键

# 模拟触摸手势
simulator.simulate_touch_gesture(widget, 'tap')
simulator.simulate_touch_gesture(widget, 'double_tap')
simulator.simulate_touch_gesture(widget, 'long_press')
simulator.simulate_touch_gesture(widget, 'swipe', start_pos, end_pos)
```

### 控件定位

```python
from tests.interaction.widget_locator import SmartWidgetFinder

# 创建控件查找器
finder = SmartWidgetFinder()

# 通过对象名称查找
login_button = finder.find_by_name("login_button")

# 通过显示的文本查找
login_button = finder.find_by_text("登录")

# 通过多种属性组合查找
input_field = finder.find_by_property(objectName="username_input", placeholderText="请输入用户名")

# 通过AI视觉识别查找
login_button = finder.find_by_ai("登录按钮")

# 通过相对位置查找 (查找位于password_field下方的控件)
submit_button = finder.find_by_relation(password_field, "below")

# 等待控件出现
finder.wait_for_widget(finder.find_by_name, timeout=5, name="result_label")
```

### 状态验证

```python
from tests.interaction.state_validator import StateValidator

# 创建状态验证器
validator = StateValidator()

# 验证控件属性
validator.assert_property(button, "text", "登录")

# 验证控件文本
validator.assert_text(label, "欢迎使用")

# 验证控件可见性
validator.assert_visible(loading_indicator, should_be_visible=False)

# 验证控件启用状态
validator.assert_enabled(submit_button, should_be_enabled=True)

# 验证控件位置和大小
validator.assert_position(button, x=100, y=200, width=150, height=40, tolerance=5)

# 验证控件颜色
validator.assert_color(warning_label, "#ff0000", property_name="color")

# 验证图像匹配
validator.assert_image_match(widget, "golden_image.png", threshold=0.95)

# 验证数据模型
expected_data = [["行1列1", "行1列2"], ["行2列1", "行2列2"]]
validator.assert_model_data(table_widget, expected_data)

# 保存黄金图像
validator.save_golden_image(widget, "golden_image.png")
```

## 运行示例

### 用户操作模拟示例

```bash
python tests/interaction/touch_test_example.py
```

### 控件定位示例

```bash
python tests/interaction/widget_locator_demo.py
```

### 状态验证示例

```bash
python tests/interaction/state_validator_demo.py
```

### UI测试运行器

```bash
python tests/interaction/ui_test_runner.py
```

## 集成到现有测试中

要将交互测试工具包集成到现有测试中，只需导入相应的类：

```python
from tests.interaction import SmartWidgetFinder, UserActionSimulator, StateValidator

def test_login_flow():
    # 初始化应用
    app = QApplication.instance() or QApplication([])
    main_window = MainWindow()
    main_window.show()
    
    # 创建测试工具
    finder = SmartWidgetFinder()
    simulator = UserActionSimulator()
    validator = StateValidator()
    
    # 查找控件
    username_input = finder.find_by_name("username_input")
    password_input = finder.find_by_name("password_input")
    login_button = finder.find_by_text("登录")
    
    # 执行操作
    simulator.simulate_keystrokes(username_input, "testuser")
    simulator.simulate_keystrokes(password_input, "password")
    simulator.simulate_click(login_button)
    
    # 等待结果
    success_message = finder.wait_for_widget(finder.find_by_text, timeout=5, text="登录成功")
    
    # 验证结果
    validator.assert_visible(success_message)
    validator.assert_text(success_message, "登录成功")
```

## 注意事项

1. 确保目标控件在操作前是可见的
2. 在操作后调用`QApplication.processEvents()`处理事件
3. 对于文件对话框等系统对话框的处理，需要使用特殊技巧（如预设返回值）
4. 模拟触摸手势时，建议提供明确的起始位置和结束位置
5. AI视觉识别需要依赖OpenCV和相关模型，请确保已安装相应依赖
6. 使用视觉验证时，确保先保存黄金图像作为参考 
7. 视觉验证对UI的细微变化很敏感，可能需要调整匹配阈值 