/**
 * SIMD 向量化计算内核 - VisionAI-ClipsMaster
 * 提供针对不同CPU指令集优化的矩阵计算实现
 * 
 * 支持的指令集：
 * - AVX-512: 512位SIMD (一次处理16个float)
 * - AVX2: 256位SIMD (一次处理8个float)
 * - AVX: 256位SIMD (无FMA指令)
 * - SSE4.2: 128位SIMD (一次处理4个float)
 * - 基准实现: 无SIMD优化
 */

#include <cstdint>
#include <cstring>
#include <cmath>

// AVX-512 指令集
#ifdef __AVX512F__
#include <immintrin.h>

void matrix_mult_avx512(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i += 16) {
        __m512 vecA = _mm512_loadu_ps(&a[i]);
        __m512 vecB = _mm512_loadu_ps(&b[i]);
        __m512 vecC = _mm512_mul_ps(vecA, vecB);
        _mm512_storeu_ps(&c[i], vecC);
    }
}

void matrix_add_avx512(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i += 16) {
        __m512 vecA = _mm512_loadu_ps(&a[i]);
        __m512 vecB = _mm512_loadu_ps(&b[i]);
        __m512 vecC = _mm512_add_ps(vecA, vecB);
        _mm512_storeu_ps(&c[i], vecC);
    }
}

void vector_scale_avx512(float* vec, float scalar, int n) {
    __m512 vscalar = _mm512_set1_ps(scalar);
    for (int i = 0; i < n; i += 16) {
        __m512 v = _mm512_loadu_ps(&vec[i]);
        v = _mm512_mul_ps(v, vscalar);
        _mm512_storeu_ps(&vec[i], v);
    }
}

// FMA (Fused Multiply-Add) 支持
void fma_avx512(float* a, float* b, float* c, float* result, int n) {
    for (int i = 0; i < n; i += 16) {
        __m512 vecA = _mm512_loadu_ps(&a[i]);
        __m512 vecB = _mm512_loadu_ps(&b[i]);
        __m512 vecC = _mm512_loadu_ps(&c[i]);
        // a * b + c
        __m512 vecResult = _mm512_fmadd_ps(vecA, vecB, vecC);
        _mm512_storeu_ps(&result[i], vecResult);
    }
}

#endif // __AVX512F__

// AVX2 指令集
#ifdef __AVX2__
#include <immintrin.h>

void matrix_mult_avx2(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i += 8) {
        __m256 vecA = _mm256_loadu_ps(&a[i]);
        __m256 vecB = _mm256_loadu_ps(&b[i]);
        __m256 vecC = _mm256_mul_ps(vecA, vecB);
        _mm256_storeu_ps(&c[i], vecC);
    }
}

void matrix_add_avx2(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i += 8) {
        __m256 vecA = _mm256_loadu_ps(&a[i]);
        __m256 vecB = _mm256_loadu_ps(&b[i]);
        __m256 vecC = _mm256_add_ps(vecA, vecB);
        _mm256_storeu_ps(&c[i], vecC);
    }
}

void vector_scale_avx2(float* vec, float scalar, int n) {
    __m256 vscalar = _mm256_set1_ps(scalar);
    for (int i = 0; i < n; i += 8) {
        __m256 v = _mm256_loadu_ps(&vec[i]);
        v = _mm256_mul_ps(v, vscalar);
        _mm256_storeu_ps(&vec[i], v);
    }
}

// FMA (Fused Multiply-Add) 支持，需要基于AVX2
#ifdef __FMA__
void fma_avx2(float* a, float* b, float* c, float* result, int n) {
    for (int i = 0; i < n; i += 8) {
        __m256 vecA = _mm256_loadu_ps(&a[i]);
        __m256 vecB = _mm256_loadu_ps(&b[i]);
        __m256 vecC = _mm256_loadu_ps(&c[i]);
        // a * b + c
        __m256 vecResult = _mm256_fmadd_ps(vecA, vecB, vecC);
        _mm256_storeu_ps(&result[i], vecResult);
    }
}
#else
// 无FMA指令时的回退实现
void fma_avx2(float* a, float* b, float* c, float* result, int n) {
    for (int i = 0; i < n; i += 8) {
        __m256 vecA = _mm256_loadu_ps(&a[i]);
        __m256 vecB = _mm256_loadu_ps(&b[i]);
        __m256 vecC = _mm256_loadu_ps(&c[i]);
        // a * b + c 的两步实现
        __m256 vecTemp = _mm256_mul_ps(vecA, vecB);
        __m256 vecResult = _mm256_add_ps(vecTemp, vecC);
        _mm256_storeu_ps(&result[i], vecResult);
    }
}
#endif // __FMA__

#endif // __AVX2__

// AVX 指令集 (无FMA)
#if defined(__AVX__) && !defined(__AVX2__)
#include <immintrin.h>

void matrix_mult_avx(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i += 8) {
        __m256 vecA = _mm256_loadu_ps(&a[i]);
        __m256 vecB = _mm256_loadu_ps(&b[i]);
        __m256 vecC = _mm256_mul_ps(vecA, vecB);
        _mm256_storeu_ps(&c[i], vecC);
    }
}

void matrix_add_avx(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i += 8) {
        __m256 vecA = _mm256_loadu_ps(&a[i]);
        __m256 vecB = _mm256_loadu_ps(&b[i]);
        __m256 vecC = _mm256_add_ps(vecA, vecB);
        _mm256_storeu_ps(&c[i], vecC);
    }
}

void vector_scale_avx(float* vec, float scalar, int n) {
    __m256 vscalar = _mm256_set1_ps(scalar);
    for (int i = 0; i < n; i += 8) {
        __m256 v = _mm256_loadu_ps(&vec[i]);
        v = _mm256_mul_ps(v, vscalar);
        _mm256_storeu_ps(&vec[i], v);
    }
}

#endif // __AVX__ && !__AVX2__

// SSE4.2 指令集
#ifdef __SSE4_2__
#include <smmintrin.h>

void matrix_mult_sse42(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i += 4) {
        __m128 vecA = _mm_loadu_ps(&a[i]);
        __m128 vecB = _mm_loadu_ps(&b[i]);
        __m128 vecC = _mm_mul_ps(vecA, vecB);
        _mm_storeu_ps(&c[i], vecC);
    }
}

void matrix_add_sse42(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i += 4) {
        __m128 vecA = _mm_loadu_ps(&a[i]);
        __m128 vecB = _mm_loadu_ps(&b[i]);
        __m128 vecC = _mm_add_ps(vecA, vecB);
        _mm_storeu_ps(&c[i], vecC);
    }
}

void vector_scale_sse42(float* vec, float scalar, int n) {
    __m128 vscalar = _mm_set1_ps(scalar);
    for (int i = 0; i < n; i += 4) {
        __m128 v = _mm_loadu_ps(&vec[i]);
        v = _mm_mul_ps(v, vscalar);
        _mm_storeu_ps(&vec[i], v);
    }
}

#endif // __SSE4_2__

// ARM NEON 指令集
#ifdef __ARM_NEON
#include <arm_neon.h>

void matrix_mult_neon(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i += 4) {
        float32x4_t vecA = vld1q_f32(&a[i]);
        float32x4_t vecB = vld1q_f32(&b[i]);
        float32x4_t vecC = vmulq_f32(vecA, vecB);
        vst1q_f32(&c[i], vecC);
    }
}

void matrix_add_neon(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i += 4) {
        float32x4_t vecA = vld1q_f32(&a[i]);
        float32x4_t vecB = vld1q_f32(&b[i]);
        float32x4_t vecC = vaddq_f32(vecA, vecB);
        vst1q_f32(&c[i], vecC);
    }
}

void vector_scale_neon(float* vec, float scalar, int n) {
    float32x4_t vscalar = vdupq_n_f32(scalar);
    for (int i = 0; i < n; i += 4) {
        float32x4_t v = vld1q_f32(&vec[i]);
        v = vmulq_f32(v, vscalar);
        vst1q_f32(&vec[i], v);
    }
}

// ARM NEON FMA 支持
void fma_neon(float* a, float* b, float* c, float* result, int n) {
    for (int i = 0; i < n; i += 4) {
        float32x4_t vecA = vld1q_f32(&a[i]);
        float32x4_t vecB = vld1q_f32(&b[i]);
        float32x4_t vecC = vld1q_f32(&c[i]);
        // a * b + c
        float32x4_t vecResult = vmlaq_f32(vecC, vecA, vecB);
        vst1q_f32(&result[i], vecResult);
    }
}

#endif // __ARM_NEON

// 基准实现 (无SIMD优化)
void matrix_mult_baseline(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; ++i) {
        c[i] = a[i] * b[i];
    }
}

void matrix_add_baseline(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

void vector_scale_baseline(float* vec, float scalar, int n) {
    for (int i = 0; i < n; ++i) {
        vec[i] *= scalar;
    }
}

void fma_baseline(float* a, float* b, float* c, float* result, int n) {
    for (int i = 0; i < n; ++i) {
        result[i] = a[i] * b[i] + c[i];
    }
}

/**
 * 矩阵乘法 C = A × B (二维矩阵)
 * 优化版本支持基于指令集的优化
 */
void matrix_multiply(float* A, float* B, float* C, int rows_a, int cols_a, int cols_b) {
    for (int i = 0; i < rows_a; ++i) {
        for (int j = 0; j < cols_b; ++j) {
            float sum = 0.0f;
            for (int k = 0; k < cols_a; ++k) {
                sum += A[i * cols_a + k] * B[k * cols_b + j];
            }
            C[i * cols_b + j] = sum;
        }
    }
}

/**
 * 优化的矩阵乘法 (针对特定大小的块)
 * 使用分块技术和SIMD优化
 */
void matrix_multiply_optimized(float* A, float* B, float* C, int rows_a, int cols_a, int cols_b, const char* simd_type) {
    // 支持所有SIMD指令的基本分块大小
    const int block_size = 32;
    
    // 初始化结果矩阵为0
    memset(C, 0, rows_a * cols_b * sizeof(float));
    
    // 分块计算
    for (int i = 0; i < rows_a; i += block_size) {
        for (int j = 0; j < cols_b; j += block_size) {
            for (int k = 0; k < cols_a; k += block_size) {
                // 为了方便示例，这里简化为不处理边界情况
                // 实际实现应考虑矩阵大小不是block_size倍数的情况
                
                // 计算局部块
                int i_end = (i + block_size < rows_a) ? i + block_size : rows_a;
                int j_end = (j + block_size < cols_b) ? j + block_size : cols_b;
                int k_end = (k + block_size < cols_a) ? k + block_size : cols_a;
                
                for (int ii = i; ii < i_end; ++ii) {
                    for (int jj = j; jj < j_end; ++jj) {
                        float sum = C[ii * cols_b + jj];
                        
                        // 这里可以根据SIMD类型选择不同的向量化方法
                        // 为简化示例，这里仍然使用标量计算
                        for (int kk = k; kk < k_end; ++kk) {
                            sum += A[ii * cols_a + kk] * B[kk * cols_b + jj];
                        }
                        
                        C[ii * cols_b + jj] = sum;
                    }
                }
            }
        }
    }
}

// 自动分发函数
void dispatch_matrix_multiply(float* A, float* B, float* C, int rows_a, int cols_a, int cols_b, const char* simd_type) {
    // 自动检测可用的SIMD类型并分发到对应实现
    if (simd_type) {
        // 用户指定SIMD类型
        matrix_multiply_optimized(A, B, C, rows_a, cols_a, cols_b, simd_type);
    } else {
        // 自动检测
        #if defined(__AVX512F__)
            matrix_multiply_optimized(A, B, C, rows_a, cols_a, cols_b, "avx512");
        #elif defined(__AVX2__)
            matrix_multiply_optimized(A, B, C, rows_a, cols_a, cols_b, "avx2");
        #elif defined(__AVX__)
            matrix_multiply_optimized(A, B, C, rows_a, cols_a, cols_b, "avx");
        #elif defined(__SSE4_2__)
            matrix_multiply_optimized(A, B, C, rows_a, cols_a, cols_b, "sse42");
        #elif defined(__ARM_NEON)
            matrix_multiply_optimized(A, B, C, rows_a, cols_a, cols_b, "neon");
        #else
            // 回退到基础实现
            matrix_multiply(A, B, C, rows_a, cols_a, cols_b);
        #endif
    }
} 