#ifndef ASSEMBLY_KERNELS_H
#define ASSEMBLY_KERNELS_H

#ifdef __cplusplus
extern "C" {
#endif

// Platform detection
#if defined(_WIN32) || defined(_WIN64)
    #define PLATFORM_WINDOWS
#elif defined(__APPLE__) || defined(__MACH__)
    #define PLATFORM_MACOS
#elif defined(__linux__)
    #define PLATFORM_LINUX
#elif defined(__ANDROID__)
    #define PLATFORM_ANDROID
#endif

// Architecture detection
#if defined(__x86_64__) || defined(_M_X64)
    #define ARCH_X86_64
#elif defined(__i386) || defined(_M_IX86)
    #define ARCH_X86
#elif defined(__arm__) || defined(_M_ARM)
    #define ARCH_ARM
#elif defined(__aarch64__)
    #define ARCH_ARM64
#endif

// API export macro
#ifdef PLATFORM_WINDOWS
    #define ASM_EXPORT __declspec(dllexport)
#else
    #define ASM_EXPORT
#endif

/**
 * 获取支持的汇编优化级别
 * 
 * 返回值:
 *   0 - 不支持汇编优化
 *   1 - 支持基本优化
 *   2 - 支持高级优化
 */
ASM_EXPORT int get_assembly_optimization_level();

/**
 * 使用汇编优化的矩阵乘法
 * C = A * B
 */
ASM_EXPORT void asm_matrix_multiply(const float* A, const float* B, float* C, 
                                  int M, int N, int K);

/**
 * 使用汇编优化的矩阵加法
 * C = A + B
 */
ASM_EXPORT void asm_matrix_add(const float* A, const float* B, float* C, int size);

/**
 * 使用汇编优化的向量点积
 * 返回向量A和B的点积 (A·B)
 */
ASM_EXPORT float asm_vector_dot(const float* A, const float* B, int size);

/**
 * 使用汇编优化的向量缩放
 * B = A * scalar
 */
ASM_EXPORT void asm_vector_scale(const float* A, float* B, float scalar, int size);

/**
 * 向量按位操作 (与特征提取相关)
 * C = A | B (按位或)
 */
ASM_EXPORT void asm_vector_bitwise_or(const int* A, const int* B, int* C, int size);

/**
 * 向量按位操作 (与特征提取相关)
 * C = A & B (按位与)
 */
ASM_EXPORT void asm_vector_bitwise_and(const int* A, const int* B, int* C, int size);

/**
 * 获取当前平台信息
 * 返回一个代表平台的整数:
 *   0 - 未知
 *   1 - Windows/x86_64
 *   2 - Windows/x86
 *   3 - macOS/x86_64
 *   4 - macOS/ARM64
 *   5 - Linux/x86_64
 *   6 - Linux/x86
 *   7 - Linux/ARM
 *   8 - Linux/ARM64
 *   9 - Android/ARM
 *  10 - Android/ARM64
 */
ASM_EXPORT int get_platform_info();

/**
 * 获取库版本
 */
ASM_EXPORT const char* get_assembly_version();

#ifdef __cplusplus
}
#endif

#endif // ASSEMBLY_KERNELS_H 