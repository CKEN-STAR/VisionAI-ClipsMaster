# VisionAI-ClipsMaster 黄金图像目录

此目录用于存储UI状态验证的黄金图像（参考图像）。

## 目录结构

- `tests/golden_images/` - 黄金图像根目录
  - `debug/` - 用于存储图像对比失败时的调试图像

## 使用说明

当使用状态验证框架进行视觉验证时，需要使用黄金图像作为参考标准。
这些图像代表UI控件的正确外观，用于在测试过程中进行比较。

### 生成黄金图像

使用`StateValidator.save_golden_image`方法保存黄金图像：

```python
from tests.interaction import StateValidator

validator = StateValidator()
validator.save_golden_image(widget, "golden_button.png")
```

### 视觉验证

使用`StateValidator.assert_image_match`方法进行视觉验证：

```python
from tests.interaction import StateValidator

validator = StateValidator()
validator.assert_image_match(widget, "golden_button.png", threshold=0.95)
```

### 图像对比失败

当图像对比失败时，状态验证器会将当前图像和参考图像保存到`debug`目录中，
以便开发者查看差异并进行调试。

## 注意事项

1. 黄金图像可能会随着UI界面的更新而过时，请定期检查和更新
2. 视觉验证对UI的细微变化和显示环境很敏感，建议使用适当的匹配阈值
3. 避免将黄金图像用于测试高度动态的内容
4. 确保在相同的环境下生成和使用黄金图像，以避免分辨率、缩放和渲染差异
 