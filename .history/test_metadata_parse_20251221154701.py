#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试元数据解析"""

import re

# 测试数据
metadata_str = "episode=1, index=5, start=00:01:23,456, end=00:01:26,789"

# 旧的解析方式（有问题）
print("旧的解析方式:")
old_metadata = {}
for part in metadata_str.split(','):
    if '=' in part:
        key, value = part.strip().split('=', 1)
        old_metadata[key] = value.strip()
print(f"  结果: {old_metadata}")

# 新的解析方式
print("\n新的解析方式:")
new_metadata = {}
kv_pattern = r'(\w+)=([^,\s]+(?:,\d{3})?)'
kv_matches = re.findall(kv_pattern, metadata_str)
for key, value in kv_matches:
    new_metadata[key.strip()] = value.strip()
print(f"  结果: {new_metadata}")

# 验证
print("\n验证:")
print(f"  episode: {new_metadata.get('episode')}")
print(f"  index: {new_metadata.get('index')}")
print(f"  start: {new_metadata.get('start')}")
print(f"  end: {new_metadata.get('end')}")
