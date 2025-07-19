/**
 * @file pipeline_opt.h
 * @brief 指令流水线优化头文件 - VisionAI-ClipsMaster
 * 
 * 提供针对性能关键型操作的优化汇编指令实现，利用现代CPU指令
 * 流水线特性进行精确调度，最大程度减少流水线气泡和停顿。
 */

#ifndef PIPELINE_OPT_H
#define PIPELINE_OPT_H

#ifdef __cplusplus
extern "C" {
#endif

// 宏定义导出函数标记
#if defined(_MSC_VER)
    #define PIPELINE_EXPORT __declspec(dllexport)
#else
    #define PIPELINE_EXPORT
#endif

/**
 * @brief 使用AVX2指令集和流水线优化的矩阵乘法操作
 * 
 * 针对不同CPU微架构进行指令调度优化，减少加载延迟影响
 * 循环展开为4次，消除条件分支，使用非时序存储指令
 * 
 * @param A 输入矩阵A指针，大小MxK
 * @param B 输入矩阵B指针，大小KxN
 * @param C 输出矩阵C指针，大小MxN
 * @param M 矩阵A的行数
 * @param N 矩阵B的列数
 * @param K 矩阵A的列数(等于矩阵B的行数)
 */
PIPELINE_EXPORT void matrix_mult_avx2(const float* A, const float* B, float* C, int M, int N, int K);

/**
 * @brief 使用AVX2指令集和流水线优化的向量点积操作
 * 
 * 针对指令调度优化，通过交错读取和计算操作消除加载延迟
 * 同时使用多个累加器减少依赖链
 * 
 * @param A 输入向量A指针
 * @param B 输入向量B指针
 * @param size 向量大小(元素数量)
 * @return float 两向量的点积结果
 */
PIPELINE_EXPORT float vector_dot_product_avx2(const float* A, const float* B, int size);

/**
 * @brief 使用AVX2指令集和流水线优化的矩阵向量乘法
 * 
 * 针对指令调度优化，通过交错读取和计算操作消除加载延迟
 * 同时使用多个累加器减少依赖链
 * 
 * @param A 输入矩阵A指针，大小rows x cols
 * @param x 输入向量x指针，大小cols
 * @param y 输出向量y指针，大小rows
 * @param rows 矩阵A的行数
 * @param cols 矩阵A的列数
 */
PIPELINE_EXPORT void matrix_vector_mult_avx2(const float* A, const float* x, float* y, int rows, int cols);

/**
 * @brief 检查当前系统是否支持流水线优化指令
 * 
 * 检测硬件是否支持AVX2指令集以及其他必要的CPU特性
 * 以支持流水线优化
 * 
 * @return int 返回支持级别:
 *         0 - 不支持
 *         1 - 部分支持
 *         2 - 完全支持
 */
PIPELINE_EXPORT int is_pipeline_opt_supported(void);

#ifdef __cplusplus
}
#endif

#endif /* PIPELINE_OPT_H */ 