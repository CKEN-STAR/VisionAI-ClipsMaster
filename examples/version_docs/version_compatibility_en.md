# Version Compatibility Documentation

*Automatically generated on: 2025-05-07 19:54:42*

## 3.0 (当前最新版本，支持4K处理)

### Required Nodes

```
project
sequence
video
audio
metadata
effects
```

### Supported Features

- multi_track
- effects_layer
- subtitle_track
- audio_effects
- nested_sequences
- advanced_effects

### Unsupported Nodes

```
```

## 2.5 (添加高级时间线格式)

### Required Nodes

```
project
sequence
video
audio
metadata
```

### Supported Features

- multi_track
- subtitle_track

### Unsupported Nodes

```
effects
nested_sequences
```

## 2.0 (添加元数据支持)

### Required Nodes

```
project
sequence
video
audio
```

### Supported Features

- multi_track

### Unsupported Nodes

```
metadata
effects
subtitle_track
```

## 1.0 (初始版本)

### Required Nodes

```
project
sequence
video
audio
```

### Supported Features

- single_track

### Unsupported Nodes

```
metadata
effects
subtitle_track
multi_track
```

## Version Compatibility Matrix

| 源版本\目标版本 | 3.1 | 3.0 | 2.5 | 2.0 | 1.0 |
|---------------|--------------------------------------------------|
| 3.1 | Directly Compatible | Incompatible | Incompatible | Incompatible | Incompatible | 
| 3.0 | Incompatible | Directly Compatible | Compatible | Compatible | Incompatible | 
| 2.5 | Incompatible | Incompatible | Directly Compatible | Compatible | Incompatible | 
| 2.0 | Incompatible | Incompatible | Incompatible | Directly Compatible | Compatible | 
| 1.0 | Incompatible | Incompatible | Incompatible | Incompatible | Directly Compatible | 

## Feature Comparison

| Feature | 3.1 | 3.0 | 2.5 | 2.0 | 1.0 |
|-------------------------|--------------------------------------------------|
| advanced_effects | No | Yes | No | No | No | 
| audio_effects | No | Yes | No | No | No | 
| effects_layer | No | Yes | No | No | No | 
| multi_track | No | Yes | Yes | Yes | No | 
| nested_sequences | No | Yes | No | No | No | 
| single_track | No | No | No | No | Yes | 
| subtitle_track | No | Yes | Yes | No | No | 

## Version Migration Guide

### 3.1 → 3.0 (Downgrading)

* **Risk Level:** High
* **Potential Information Loss:** Yes
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 3.0 版本项目
3. 手动重新创建项目内容

#### Important Notes

All features are compatible

### 3.1 → 2.5 (Downgrading)

* **Risk Level:** High
* **Potential Information Loss:** Yes
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 2.5 版本项目
3. 手动重新创建项目内容

#### Important Notes

All features are compatible

### 3.1 → 2.0 (Downgrading)

* **Risk Level:** High
* **Potential Information Loss:** Yes
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 2.0 版本项目
3. 手动重新创建项目内容

#### Important Notes

All features are compatible

### 3.1 → 1.0 (Downgrading)

* **Risk Level:** High
* **Potential Information Loss:** Yes
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 1.0 版本项目
3. 手动重新创建项目内容

#### Important Notes

All features are compatible

### 3.0 → 3.1 (Upgrading)

* **Risk Level:** Medium
* **Potential Information Loss:** No
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 3.1 版本项目
3. 手动重新创建项目内容

#### Important Notes

The following features are not supported in the target version:
- audio_effects
- subtitle_track
- effects_layer
- advanced_effects
- multi_track
- nested_sequences

### 3.0 → 2.5 (Downgrading)

* **Risk Level:** Low
* **Potential Information Loss:** No
* **Recommended Migration Path:** Directly Compatible

#### Migration Steps

1. 直接导出为 2.5 版本格式即可

#### Important Notes

The following features are not supported in the target version:
- advanced_effects
- audio_effects
- nested_sequences
- effects_layer

### 3.0 → 2.0 (Downgrading)

* **Risk Level:** Low
* **Potential Information Loss:** No
* **Recommended Migration Path:** Directly Compatible

#### Migration Steps

1. 直接导出为 2.0 版本格式即可

#### Important Notes

The following features are not supported in the target version:
- subtitle_track
- effects_layer
- advanced_effects
- audio_effects
- nested_sequences

### 3.0 → 1.0 (Downgrading)

* **Risk Level:** High
* **Potential Information Loss:** Yes
* **Recommended Migration Path:** 3.0 → 2.0 → 1.0

#### Migration Steps

1. 备份您的原始项目文件
2. 先转换到 2.0 版本
3. 最后导出为 1.0 版本格式

#### Important Notes

The following features are not supported in the target version:
- subtitle_track
- effects_layer
- advanced_effects
- audio_effects
- multi_track
- nested_sequences

### 2.5 → 3.1 (Upgrading)

* **Risk Level:** Medium
* **Potential Information Loss:** No
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 3.1 版本项目
3. 手动重新创建项目内容

#### Important Notes

The following features are not supported in the target version:
- subtitle_track
- multi_track

### 2.5 → 3.0 (Upgrading)

* **Risk Level:** Medium
* **Potential Information Loss:** No
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 3.0 版本项目
3. 手动重新创建项目内容

#### Important Notes

All features are compatible

### 2.5 → 2.0 (Downgrading)

* **Risk Level:** Low
* **Potential Information Loss:** No
* **Recommended Migration Path:** Directly Compatible

#### Migration Steps

1. 直接导出为 2.0 版本格式即可

#### Important Notes

The following features are not supported in the target version:
- subtitle_track

### 2.5 → 1.0 (Downgrading)

* **Risk Level:** High
* **Potential Information Loss:** Yes
* **Recommended Migration Path:** 2.5 → 2.0 → 1.0

#### Migration Steps

1. 备份您的原始项目文件
2. 先转换到 2.0 版本
3. 最后导出为 1.0 版本格式

#### Important Notes

The following features are not supported in the target version:
- subtitle_track
- multi_track

### 2.0 → 3.1 (Upgrading)

* **Risk Level:** Medium
* **Potential Information Loss:** No
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 3.1 版本项目
3. 手动重新创建项目内容

#### Important Notes

The following features are not supported in the target version:
- multi_track

### 2.0 → 3.0 (Upgrading)

* **Risk Level:** Medium
* **Potential Information Loss:** No
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 3.0 版本项目
3. 手动重新创建项目内容

#### Important Notes

All features are compatible

### 2.0 → 2.5 (Upgrading)

* **Risk Level:** Medium
* **Potential Information Loss:** No
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 2.5 版本项目
3. 手动重新创建项目内容

#### Important Notes

All features are compatible

### 2.0 → 1.0 (Downgrading)

* **Risk Level:** Low
* **Potential Information Loss:** No
* **Recommended Migration Path:** Directly Compatible

#### Migration Steps

1. 直接导出为 1.0 版本格式即可

#### Important Notes

The following features are not supported in the target version:
- multi_track

### 1.0 → 3.1 (Upgrading)

* **Risk Level:** Medium
* **Potential Information Loss:** No
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 3.1 版本项目
3. 手动重新创建项目内容

#### Important Notes

The following features are not supported in the target version:
- single_track

### 1.0 → 3.0 (Upgrading)

* **Risk Level:** Medium
* **Potential Information Loss:** No
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 3.0 版本项目
3. 手动重新创建项目内容

#### Important Notes

The following features are not supported in the target version:
- single_track

### 1.0 → 2.5 (Upgrading)

* **Risk Level:** Medium
* **Potential Information Loss:** No
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 2.5 版本项目
3. 手动重新创建项目内容

#### Important Notes

The following features are not supported in the target version:
- single_track

### 1.0 → 2.0 (Upgrading)

* **Risk Level:** Medium
* **Potential Information Loss:** No
* **Recommended Migration Path:** Incompatible, requires recreation

#### Migration Steps

1. 备份您的原始项目文件
2. 创建新的 2.0 版本项目
3. 手动重新创建项目内容

#### Important Notes

The following features are not supported in the target version:
- single_track
