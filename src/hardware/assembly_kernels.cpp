#include "assembly_kernels.h"
#include <string.h>
#include <stdio.h>

// 库版本
#define ASSEMBLY_VERSION "1.0.0"

// Intel架构intrinsics
#if defined(ARCH_X86_64) || defined(ARCH_X86)
    #include <immintrin.h>
#endif

// ARM NEON intrinsics
#if defined(ARCH_ARM) || defined(ARCH_ARM64)
    #include <arm_neon.h>
#endif

// Windows系统特定头文件
#if defined(PLATFORM_WINDOWS)
    #include <windows.h>
#endif

// macOS特定头文件
#if defined(PLATFORM_MACOS)
    #include <sys/sysctl.h>
    #ifdef __APPLE__
        #include <Accelerate/Accelerate.h>
    #endif
#endif

// Linux特定头文件
#if defined(PLATFORM_LINUX)
    #include <unistd.h>
    #include <sys/syscall.h>
    #include <pthread.h>
#endif

// 平台信息
ASM_EXPORT int get_platform_info() {
    #if defined(PLATFORM_WINDOWS) && defined(ARCH_X86_64)
        return 1;
    #elif defined(PLATFORM_WINDOWS) && defined(ARCH_X86)
        return 2;
    #elif defined(PLATFORM_MACOS) && defined(ARCH_X86_64)
        return 3;
    #elif defined(PLATFORM_MACOS) && defined(ARCH_ARM64)
        return 4;
    #elif defined(PLATFORM_LINUX) && defined(ARCH_X86_64)
        return 5;
    #elif defined(PLATFORM_LINUX) && defined(ARCH_X86)
        return 6;
    #elif defined(PLATFORM_LINUX) && defined(ARCH_ARM)
        return 7;
    #elif defined(PLATFORM_LINUX) && defined(ARCH_ARM64)
        return 8;
    #elif defined(PLATFORM_ANDROID) && defined(ARCH_ARM)
        return 9;
    #elif defined(PLATFORM_ANDROID) && defined(ARCH_ARM64)
        return 10;
    #else
        return 0;
    #endif
}

// 获取库版本
ASM_EXPORT const char* get_assembly_version() {
    return ASSEMBLY_VERSION;
}

// 检测CPU支持的优化级别
ASM_EXPORT int get_assembly_optimization_level() {
    int level = 0;
    
    #if defined(ARCH_X86_64) || defined(ARCH_X86)
        // 检测Intel平台的优化支持
        #if defined(__AVX2__)
            level = 2;  // 高级优化
        #elif defined(__AVX__) || defined(__SSE4_2__)
            level = 1;  // 基本优化
        #else
            // 运行时检测
            #if defined(_MSC_VER)
                int cpuInfo[4];
                __cpuid(cpuInfo, 1);
                if ((cpuInfo[2] & (1 << 28)) != 0) level = 2;  // AVX2
                else if ((cpuInfo[2] & (1 << 19)) != 0) level = 1;  // SSE4_1
            #else
                // GCC风格的检测
                unsigned int eax, ebx, ecx, edx;
                __asm__ __volatile__("cpuid" : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx) : "a"(1));
                if ((ecx & (1 << 19)) != 0) level = 1;  // SSE4_1
                
                // 检测AVX2 (需要额外的cpuid叶子)
                __asm__ __volatile__("cpuid" : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx) : "a"(7), "c"(0));
                if ((ebx & (1 << 5)) != 0) level = 2;  // AVX2
            #endif
        #endif
    #elif defined(ARCH_ARM64)
        // ARM64架构默认具有NEON支持
        level = 2;
    #elif defined(ARCH_ARM)
        // ARM架构检测NEON支持
        #if defined(__ARM_NEON)
            level = 1;
        #endif
    #endif
    
    // macOS平台特定级别
    #if defined(PLATFORM_MACOS)
        level = 2;  // 假设Accelerate框架可用
    #endif
    
    // Windows平台上可能的MKL检测
    #if defined(PLATFORM_WINDOWS)
        // 实际应用中，可以检测MKL是否可用
    #endif
    
    return level;
}

// 矩阵乘法实现
ASM_EXPORT void asm_matrix_multiply(const float* A, const float* B, float* C, 
                                  int M, int N, int K) {
    // 使用特定平台优化的矩阵乘法
    
    #if defined(PLATFORM_MACOS) && defined(__APPLE__)
        // macOS平台使用Accelerate框架
        
        // A matrices: M rows, K columns
        // B matrices: K rows, N columns
        // C matrices: M rows, N columns
        cblas_sgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans,
                   M, N, K, 1.0f, A, K, B, N, 0.0f, C, N);
                   
    #elif defined(PLATFORM_WINDOWS) && defined(_MSC_VER) && defined(ARCH_X86_64)
        // Windows平台使用Intel MKL指令 (内联汇编/基本实现)
        for (int i = 0; i < M; i++) {
            for (int j = 0; j < N; j++) {
                float sum = 0.0f;
                for (int k = 0; k < K; k++) {
                    sum += A[i*K + k] * B[k*N + j];
                }
                C[i*N + j] = sum;
            }
        }
        
    #elif defined(PLATFORM_LINUX) && defined(ARCH_X86_64)
        // Linux平台x86_64 使用GCC内联汇编
        for (int i = 0; i < M; i++) {
            for (int j = 0; j < N; j++) {
                float sum = 0.0f;
                for (int k = 0; k < K; k++) {
                    sum += A[i*K + k] * B[k*N + j];
                }
                C[i*N + j] = sum;
            }
        }
        
    #elif defined(ARCH_ARM64) || defined(ARCH_ARM)
        // ARM架构使用NEON指令
        #if defined(__ARM_NEON)
            for (int i = 0; i < M; i++) {
                for (int j = 0; j < N; j++) {
                    float sum = 0.0f;
                    
                    // NEON向量化处理
                    int k = 0;
                    float32x4_t sum_vec = vdupq_n_f32(0);
                    
                    for (; k <= K - 4; k += 4) {
                        float32x4_t a_vec = vld1q_f32(&A[i*K + k]);
                        float32x4_t b_vec = vld1q_f32(&B[k*N + j]);
                        sum_vec = vmlaq_f32(sum_vec, a_vec, b_vec);
                    }
                    
                    // 水平相加
                    float32x2_t sum_low = vget_low_f32(sum_vec);
                    float32x2_t sum_high = vget_high_f32(sum_vec);
                    sum_low = vadd_f32(sum_low, sum_high);
                    sum += vget_lane_f32(sum_low, 0) + vget_lane_f32(sum_low, 1);
                    
                    // 处理剩余元素
                    for (; k < K; k++) {
                        sum += A[i*K + k] * B[k*N + j];
                    }
                    
                    C[i*N + j] = sum;
                }
            }
        #else
            // ARM但没有NEON支持时的基础实现
            for (int i = 0; i < M; i++) {
                for (int j = 0; j < N; j++) {
                    float sum = 0.0f;
                    for (int k = 0; k < K; k++) {
                        sum += A[i*K + k] * B[k*N + j];
                    }
                    C[i*N + j] = sum;
                }
            }
        #endif
    #else
        // 基础通用实现
        for (int i = 0; i < M; i++) {
            for (int j = 0; j < N; j++) {
                float sum = 0.0f;
                for (int k = 0; k < K; k++) {
                    sum += A[i*K + k] * B[k*N + j];
                }
                C[i*N + j] = sum;
            }
        }
    #endif
}

// 矩阵加法实现
ASM_EXPORT void asm_matrix_add(const float* A, const float* B, float* C, int size) {
    #if defined(PLATFORM_MACOS) && defined(__APPLE__)
        // 使用Accelerate框架
        vDSP_vadd(A, 1, B, 1, C, 1, size);
        
    #elif defined(ARCH_X86_64) && defined(__AVX2__)
        // 使用AVX2指令
        int i = 0;
        for (; i <= size - 8; i += 8) {
            __m256 a = _mm256_loadu_ps(&A[i]);
            __m256 b = _mm256_loadu_ps(&B[i]);
            __m256 c = _mm256_add_ps(a, b);
            _mm256_storeu_ps(&C[i], c);
        }
        
        // 处理剩余元素
        for (; i < size; i++) {
            C[i] = A[i] + B[i];
        }
        
    #elif defined(ARCH_X86_64) && defined(__SSE4_2__)
        // 使用SSE4.2指令
        int i = 0;
        for (; i <= size - 4; i += 4) {
            __m128 a = _mm_loadu_ps(&A[i]);
            __m128 b = _mm_loadu_ps(&B[i]);
            __m128 c = _mm_add_ps(a, b);
            _mm_storeu_ps(&C[i], c);
        }
        
        // 处理剩余元素
        for (; i < size; i++) {
            C[i] = A[i] + B[i];
        }
        
    #elif defined(ARCH_ARM) || defined(ARCH_ARM64)
        // 使用ARM NEON指令
        #ifdef __ARM_NEON
            int i = 0;
            for (; i <= size - 4; i += 4) {
                float32x4_t a = vld1q_f32(&A[i]);
                float32x4_t b = vld1q_f32(&B[i]);
                float32x4_t c = vaddq_f32(a, b);
                vst1q_f32(&C[i], c);
            }
            
            // 处理剩余元素
            for (; i < size; i++) {
                C[i] = A[i] + B[i];
            }
        #else
            // 无NEON支持时的基础实现
            for (int i = 0; i < size; i++) {
                C[i] = A[i] + B[i];
            }
        #endif
        
    #else
        // 基础实现
        for (int i = 0; i < size; i++) {
            C[i] = A[i] + B[i];
        }
    #endif
}

// 向量点积实现
ASM_EXPORT float asm_vector_dot(const float* A, const float* B, int size) {
    float result = 0.0f;
    
    #if defined(PLATFORM_MACOS) && defined(__APPLE__)
        // 使用Accelerate框架
        vDSP_dotpr(A, 1, B, 1, &result, size);
        
    #elif defined(ARCH_X86_64) && defined(__AVX2__)
        // 使用AVX2指令
        __m256 sum = _mm256_setzero_ps();
        int i = 0;
        
        for (; i <= size - 8; i += 8) {
            __m256 a = _mm256_loadu_ps(&A[i]);
            __m256 b = _mm256_loadu_ps(&B[i]);
            __m256 mul = _mm256_mul_ps(a, b);
            sum = _mm256_add_ps(sum, mul);
        }
        
        // 水平相加
        __m128 sum128 = _mm_add_ps(_mm256_extractf128_ps(sum, 0), _mm256_extractf128_ps(sum, 1));
        __m128 sum64 = _mm_add_ps(sum128, _mm_movehl_ps(sum128, sum128));
        __m128 sum32 = _mm_add_ss(sum64, _mm_shuffle_ps(sum64, sum64, 1));
        float temp;
        _mm_store_ss(&temp, sum32);
        result += temp;
        
        // 处理剩余元素
        for (; i < size; i++) {
            result += A[i] * B[i];
        }
        
    #elif defined(ARCH_X86_64) && defined(__SSE4_2__)
        // 使用SSE4.2指令
        __m128 sum = _mm_setzero_ps();
        int i = 0;
        
        for (; i <= size - 4; i += 4) {
            __m128 a = _mm_loadu_ps(&A[i]);
            __m128 b = _mm_loadu_ps(&B[i]);
            __m128 mul = _mm_mul_ps(a, b);
            sum = _mm_add_ps(sum, mul);
        }
        
        // 水平相加
        __m128 shuf = _mm_shuffle_ps(sum, sum, _MM_SHUFFLE(2, 3, 0, 1));
        __m128 sums = _mm_add_ps(sum, shuf);
        shuf = _mm_movehl_ps(shuf, sums);
        sums = _mm_add_ss(sums, shuf);
        float temp;
        _mm_store_ss(&temp, sums);
        result += temp;
        
        // 处理剩余元素
        for (; i < size; i++) {
            result += A[i] * B[i];
        }
        
    #elif defined(ARCH_ARM) || defined(ARCH_ARM64)
        // 使用ARM NEON指令
        #ifdef __ARM_NEON
            float32x4_t sum_vec = vdupq_n_f32(0);
            int i = 0;
            
            for (; i <= size - 4; i += 4) {
                float32x4_t a = vld1q_f32(&A[i]);
                float32x4_t b = vld1q_f32(&B[i]);
                // 向量乘法并累加
                sum_vec = vmlaq_f32(sum_vec, a, b);
            }
            
            // 水平相加
            float32x2_t sum_low = vget_low_f32(sum_vec);
            float32x2_t sum_high = vget_high_f32(sum_vec);
            sum_low = vadd_f32(sum_low, sum_high);
            sum_low = vpadd_f32(sum_low, sum_low);
            result += vget_lane_f32(sum_low, 0);
            
            // 处理剩余元素
            for (; i < size; i++) {
                result += A[i] * B[i];
            }
        #else
            // 无NEON支持时的基础实现
            for (int i = 0; i < size; i++) {
                result += A[i] * B[i];
            }
        #endif
        
    #else
        // 基础实现
        for (int i = 0; i < size; i++) {
            result += A[i] * B[i];
        }
    #endif
    
    return result;
}

// 向量缩放实现
ASM_EXPORT void asm_vector_scale(const float* A, float* B, float scalar, int size) {
    #if defined(PLATFORM_MACOS) && defined(__APPLE__)
        // 使用Accelerate框架
        vDSP_vsmul(A, 1, &scalar, B, 1, size);
        
    #elif defined(ARCH_X86_64) && defined(__AVX2__)
        // 使用AVX2指令
        __m256 scalar_vec = _mm256_set1_ps(scalar);
        int i = 0;
        
        for (; i <= size - 8; i += 8) {
            __m256 a = _mm256_loadu_ps(&A[i]);
            __m256 result = _mm256_mul_ps(a, scalar_vec);
            _mm256_storeu_ps(&B[i], result);
        }
        
        // 处理剩余元素
        for (; i < size; i++) {
            B[i] = A[i] * scalar;
        }
        
    #elif defined(ARCH_X86_64) && defined(__SSE4_2__)
        // 使用SSE4.2指令
        __m128 scalar_vec = _mm_set1_ps(scalar);
        int i = 0;
        
        for (; i <= size - 4; i += 4) {
            __m128 a = _mm_loadu_ps(&A[i]);
            __m128 result = _mm_mul_ps(a, scalar_vec);
            _mm_storeu_ps(&B[i], result);
        }
        
        // 处理剩余元素
        for (; i < size; i++) {
            B[i] = A[i] * scalar;
        }
        
    #elif defined(ARCH_ARM) || defined(ARCH_ARM64)
        // 使用ARM NEON指令
        #ifdef __ARM_NEON
            float32x4_t scalar_vec = vdupq_n_f32(scalar);
            int i = 0;
            
            for (; i <= size - 4; i += 4) {
                float32x4_t a = vld1q_f32(&A[i]);
                float32x4_t result = vmulq_f32(a, scalar_vec);
                vst1q_f32(&B[i], result);
            }
            
            // 处理剩余元素
            for (; i < size; i++) {
                B[i] = A[i] * scalar;
            }
        #else
            // 无NEON支持时的基础实现
            for (int i = 0; i < size; i++) {
                B[i] = A[i] * scalar;
            }
        #endif
        
    #else
        // 基础实现
        for (int i = 0; i < size; i++) {
            B[i] = A[i] * scalar;
        }
    #endif
}

// 向量按位或操作实现
ASM_EXPORT void asm_vector_bitwise_or(const int* A, const int* B, int* C, int size) {
    #if defined(ARCH_X86_64) && defined(__AVX2__)
        // 使用AVX2指令
        int i = 0;
        
        for (; i <= size - 8; i += 8) {
            __m256i a = _mm256_loadu_si256((__m256i*)&A[i]);
            __m256i b = _mm256_loadu_si256((__m256i*)&B[i]);
            __m256i result = _mm256_or_si256(a, b);
            _mm256_storeu_si256((__m256i*)&C[i], result);
        }
        
        // 处理剩余元素
        for (; i < size; i++) {
            C[i] = A[i] | B[i];
        }
        
    #elif defined(ARCH_X86_64) && defined(__SSE4_2__)
        // 使用SSE4.2指令
        int i = 0;
        
        for (; i <= size - 4; i += 4) {
            __m128i a = _mm_loadu_si128((__m128i*)&A[i]);
            __m128i b = _mm_loadu_si128((__m128i*)&B[i]);
            __m128i result = _mm_or_si128(a, b);
            _mm_storeu_si128((__m128i*)&C[i], result);
        }
        
        // 处理剩余元素
        for (; i < size; i++) {
            C[i] = A[i] | B[i];
        }
        
    #elif defined(ARCH_ARM) || defined(ARCH_ARM64)
        // 使用ARM NEON指令
        #ifdef __ARM_NEON
            int i = 0;
            
            for (; i <= size - 4; i += 4) {
                int32x4_t a = vld1q_s32(&A[i]);
                int32x4_t b = vld1q_s32(&B[i]);
                int32x4_t result = vorrq_s32(a, b);
                vst1q_s32(&C[i], result);
            }
            
            // 处理剩余元素
            for (; i < size; i++) {
                C[i] = A[i] | B[i];
            }
        #else
            // 无NEON支持时的基础实现
            for (int i = 0; i < size; i++) {
                C[i] = A[i] | B[i];
            }
        #endif
        
    #else
        // 基础实现
        for (int i = 0; i < size; i++) {
            C[i] = A[i] | B[i];
        }
    #endif
}

// 向量按位与操作实现
ASM_EXPORT void asm_vector_bitwise_and(const int* A, const int* B, int* C, int size) {
    #if defined(ARCH_X86_64) && defined(__AVX2__)
        // 使用AVX2指令
        int i = 0;
        
        for (; i <= size - 8; i += 8) {
            __m256i a = _mm256_loadu_si256((__m256i*)&A[i]);
            __m256i b = _mm256_loadu_si256((__m256i*)&B[i]);
            __m256i result = _mm256_and_si256(a, b);
            _mm256_storeu_si256((__m256i*)&C[i], result);
        }
        
        // 处理剩余元素
        for (; i < size; i++) {
            C[i] = A[i] & B[i];
        }
        
    #elif defined(ARCH_X86_64) && defined(__SSE4_2__)
        // 使用SSE4.2指令
        int i = 0;
        
        for (; i <= size - 4; i += 4) {
            __m128i a = _mm_loadu_si128((__m128i*)&A[i]);
            __m128i b = _mm_loadu_si128((__m128i*)&B[i]);
            __m128i result = _mm_and_si128(a, b);
            _mm_storeu_si128((__m128i*)&C[i], result);
        }
        
        // 处理剩余元素
        for (; i < size; i++) {
            C[i] = A[i] & B[i];
        }
        
    #elif defined(ARCH_ARM) || defined(ARCH_ARM64)
        // 使用ARM NEON指令
        #ifdef __ARM_NEON
            int i = 0;
            
            for (; i <= size - 4; i += 4) {
                int32x4_t a = vld1q_s32(&A[i]);
                int32x4_t b = vld1q_s32(&B[i]);
                int32x4_t result = vandq_s32(a, b);
                vst1q_s32(&C[i], result);
            }
            
            // 处理剩余元素
            for (; i < size; i++) {
                C[i] = A[i] & B[i];
            }
        #else
            // 无NEON支持时的基础实现
            for (int i = 0; i < size; i++) {
                C[i] = A[i] & B[i];
            }
        #endif
        
    #else
        // 基础实现
        for (int i = 0; i < size; i++) {
            C[i] = A[i] & B[i];
        }
    #endif
} 