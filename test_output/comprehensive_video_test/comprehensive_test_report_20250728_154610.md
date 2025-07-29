# VisionAI-ClipsMaster 核心视频处理模块全面测试报告

## 测试概览

- **测试会话ID**: comprehensive_test_20250728_154605
- **测试开始时间**: 2025-07-28T15:46:05.032576
- **总体状态**: FAILED
- **成功率**: 75.0%

## 测试统计

| 指标 | 数量 |
|------|------|
| 总测试数 | 4 |
| 通过测试 | 3 |
| 失败测试 | 1 |
| 错误测试 | 0 |
| 总子测试数 | 13 |
| 通过子测试 | 12 |

## 性能指标

| 指标 | 值 |
|------|---|
| 峰值内存使用 | 350.6 MB |
| 最终内存使用 | 350.6 MB |
| 内存增长 | 327.5 MB |
| 内存限制遵守 | ✅ |
| 测试总耗时 | 5.5 秒 |

## 详细测试结果

### ✅ subtitle_video_mapping

- **状态**: PASSED
- **子测试结果**:
  - ✅ srt_parsing_alignment: PASSED
  - ✅ timecode_sync_accuracy: PASSED
  - ✅ multi_episode_recognition: PASSED

### ✅ viral_srt_generation

- **状态**: PASSED
- **子测试结果**:
  - ✅ real_drama_srt_input: PASSED
  - ✅ model_loading_inference: PASSED
  - ✅ screenplay_reconstruction: PASSED
  - ✅ generated_viral_srt: PASSED
  - ✅ duration_reasonableness: PASSED

### ❌ end_to_end_workflow

- **状态**: FAILED
- **子测试结果**:
  - ✅ complete_workflow: PASSED
  - ✅ video_subtitle_matching: PASSED
  - ❌ jianying_export: FAILED

### ✅ performance_and_stability

- **状态**: PASSED
- **子测试结果**:
  - ✅ memory_usage: PASSED
  - ✅ low_spec_stability: PASSED

