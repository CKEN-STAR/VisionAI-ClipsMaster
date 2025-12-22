#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from PyQt6.QtWidgets import QApplication
app = QApplication([])

import simple_ui_fixed
window = simple_ui_fixed.SimpleScreenplayApp()

print('检查关键控件:')
print(f'  ai_mode_combo: {hasattr(window, "ai_mode_combo")}')
print(f'  cloud_mode_container: {hasattr(window, "cloud_mode_container")}')
print(f'  local_mode_container: {hasattr(window, "local_mode_container")}')
print(f'  cloud_platform_combo: {hasattr(window, "cloud_platform_combo")}')
print(f'  cloud_model_combo: {hasattr(window, "cloud_model_combo")}')
print(f'  cloud_api_key_input: {hasattr(window, "cloud_api_key_input")}')
print(f'  test_cloud_btn: {hasattr(window, "test_cloud_btn")}')
print(f'  lang_auto_radio: {hasattr(window, "lang_auto_radio")}')
print(f'  lang_zh_radio: {hasattr(window, "lang_zh_radio")}')
print(f'  lang_en_radio: {hasattr(window, "lang_en_radio")}')

print(f'\n云端模式状态:')
print(f'  cloud_mode_enabled: {window.cloud_mode_enabled}')

print(f'\n检查方法:')
print(f'  on_ai_mode_changed: {hasattr(window, "on_ai_mode_changed")}')
print(f'  test_cloud_connection: {hasattr(window, "test_cloud_connection")}')
print(f'  _load_cloud_config: {hasattr(window, "_load_cloud_config")}')
print(f'  _save_cloud_config: {hasattr(window, "_save_cloud_config")}')

window.close()
print('\n✅ UI初始化测试通过！')
