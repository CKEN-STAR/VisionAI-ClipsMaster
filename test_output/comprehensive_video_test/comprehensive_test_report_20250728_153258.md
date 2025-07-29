# VisionAI-ClipsMaster 核心视频处理模块全面测试报告

## 测试概览

- **测试会话ID**: comprehensive_test_20250728_153252
- **测试开始时间**: 2025-07-28T15:32:52.241583
- **总体状态**: FAILED
- **成功率**: 50.0%

## 测试统计

| 指标 | 数量 |
|------|------|
| 总测试数 | 4 |
| 通过测试 | 2 |
| 失败测试 | 2 |
| 错误测试 | 0 |
| 总子测试数 | 13 |
| 通过子测试 | 10 |

## 性能指标

| 指标 | 值 |
|------|---|
| 峰值内存使用 | 352.2 MB |
| 最终内存使用 | 352.2 MB |
| 内存增长 | 329.1 MB |
| 内存限制遵守 | ✅ |
| 测试总耗时 | 6.7 秒 |

## 详细测试结果

### ✅ subtitle_video_mapping

- **状态**: PASSED
- **子测试结果**:
  - ✅ srt_parsing_alignment: PASSED
  - ✅ timecode_sync_accuracy: PASSED
  - ✅ multi_episode_recognition: PASSED

### ❌ viral_srt_generation

- **状态**: FAILED
- **子测试结果**:
  - ✅ real_drama_srt_input: PASSED
  - ❌ model_loading_inference: FAILED
  - ✅ screenplay_reconstruction: PASSED
  - ✅ generated_viral_srt: PASSED
  - ✅ duration_reasonableness: PASSED

### ❌ end_to_end_workflow

- **状态**: FAILED
- **子测试结果**:
  - ⚠️ complete_workflow: ERROR
  - ✅ video_subtitle_matching: PASSED
  - ❌ jianying_export: FAILED

### ✅ performance_and_stability

- **状态**: PASSED
- **子测试结果**:
  - ✅ memory_usage: PASSED
  - ✅ low_spec_stability: PASSED

