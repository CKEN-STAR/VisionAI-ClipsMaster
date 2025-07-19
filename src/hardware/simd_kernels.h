/**
 * SIMD 向量化计算内核头文件 - VisionAI-ClipsMaster
 */

#ifndef VISIONAI_SIMD_KERNELS_H
#define VISIONAI_SIMD_KERNELS_H

#ifdef __cplusplus
extern "C" {
#endif

// AVX-512 指令集函数
#ifdef __AVX512F__
void matrix_mult_avx512(float* a, float* b, float* c, int n);
void matrix_add_avx512(float* a, float* b, float* c, int n);
void vector_scale_avx512(float* vec, float scalar, int n);
void fma_avx512(float* a, float* b, float* c, float* result, int n);
#endif

// AVX2 指令集函数
#ifdef __AVX2__
void matrix_mult_avx2(float* a, float* b, float* c, int n);
void matrix_add_avx2(float* a, float* b, float* c, int n);
void vector_scale_avx2(float* vec, float scalar, int n);
void fma_avx2(float* a, float* b, float* c, float* result, int n);
#endif

// AVX 指令集函数
#if defined(__AVX__) && !defined(__AVX2__)
void matrix_mult_avx(float* a, float* b, float* c, int n);
void matrix_add_avx(float* a, float* b, float* c, int n);
void vector_scale_avx(float* vec, float scalar, int n);
#endif

// SSE4.2 指令集函数
#ifdef __SSE4_2__
void matrix_mult_sse42(float* a, float* b, float* c, int n);
void matrix_add_sse42(float* a, float* b, float* c, int n);
void vector_scale_sse42(float* vec, float scalar, int n);
#endif

// ARM NEON 指令集函数
#ifdef __ARM_NEON
void matrix_mult_neon(float* a, float* b, float* c, int n);
void matrix_add_neon(float* a, float* b, float* c, int n);
void vector_scale_neon(float* vec, float scalar, int n);
void fma_neon(float* a, float* b, float* c, float* result, int n);
#endif

// 基准实现函数 (永远可用)
void matrix_mult_baseline(float* a, float* b, float* c, int n);
void matrix_add_baseline(float* a, float* b, float* c, int n);
void vector_scale_baseline(float* vec, float scalar, int n);
void fma_baseline(float* a, float* b, float* c, float* result, int n);

// 矩阵乘法函数 (二维矩阵)
void matrix_multiply(float* A, float* B, float* C, int rows_a, int cols_a, int cols_b);
void matrix_multiply_optimized(float* A, float* B, float* C, int rows_a, int cols_a, int cols_b, const char* simd_type);
void dispatch_matrix_multiply(float* A, float* B, float* C, int rows_a, int cols_a, int cols_b, const char* simd_type);

#ifdef __cplusplus
}
#endif

#endif // VISIONAI_SIMD_KERNELS_H 