#include "pipeline_opt.h"
#include <stdio.h>
#include <string.h>

#if defined(_MSC_VER)
    #include <intrin.h>
#else
    #include <cpuid.h>
#endif

/**
 * 检测当前CPU的SIMD指令集支持情况
 */
static int detect_cpu_features(void) {
    int features = 0;
    
    // CPU信息buffers
    int cpu_info[4] = {0};
    unsigned int eax, ebx, ecx, edx;
    
#if defined(_MSC_VER)
    // MSVC下使用__cpuid
    __cpuid(cpu_info, 1);
    ecx = cpu_info[2];
    edx = cpu_info[3];
    
    // 检测高级特性 (AVX, AVX2)
    __cpuid(cpu_info, 7);
    ebx = cpu_info[1];
#else
    // GCC/Clang使用__get_cpuid
    if (!__get_cpuid(1, &eax, &ebx, &ecx, &edx)) {
        return 0;  // CPUID 不可用
    }
    
    // 检测高级特性 (AVX, AVX2)
    if (!__get_cpuid_count(7, 0, &eax, &ebx, &ecx, &edx)) {
        ebx = 0;
    }
#endif

    // 检测基本特性
    if (edx & (1 << 25)) features |= 1;      // SSE
    if (edx & (1 << 26)) features |= 2;      // SSE2
    if (ecx & (1 << 0))  features |= 4;      // SSE3
    if (ecx & (1 << 9))  features |= 8;      // SSSE3
    if (ecx & (1 << 19)) features |= 16;     // SSE4.1
    if (ecx & (1 << 20)) features |= 32;     // SSE4.2
    if (ecx & (1 << 28)) features |= 64;     // AVX
    if (ebx & (1 << 5))  features |= 128;    // AVX2
    
    return features;
}

/**
 * 检测预取能力
 */
static int detect_prefetch_support(void) {
    int cpu_info[4] = {0};
    
#if defined(_MSC_VER)
    __cpuid(cpu_info, 1);
    return (cpu_info[3] & (1 << 9)) != 0;  // 检测CLFLUSH支持，通常表示有预取支持
#else
    unsigned int eax, ebx, ecx, edx;
    if (!__get_cpuid(1, &eax, &ebx, &ecx, &edx)) {
        return 0;
    }
    return (edx & (1 << 9)) != 0;  // 检测CLFLUSH支持
#endif
}

/**
 * 获取CPU高速缓存行大小
 */
static int get_cache_line_size(void) {
    int cpu_info[4] = {0};
    
#if defined(_MSC_VER)
    __cpuid(cpu_info, 1);
    int clflush_line_size = ((cpu_info[1] >> 8) & 0xff) * 8;
    return clflush_line_size > 0 ? clflush_line_size : 64;  // 默认返回64
#else
    unsigned int eax, ebx, ecx, edx;
    if (!__get_cpuid(1, &eax, &ebx, &ecx, &edx)) {
        return 64;  // 默认64字节
    }
    int clflush_line_size = ((ebx >> 8) & 0xff) * 8;
    return clflush_line_size > 0 ? clflush_line_size : 64;
#endif
}

/**
 * @brief 检查当前系统是否支持流水线优化指令
 * 
 * 检查CPU是否支持必要的指令集特性，如AVX2，
 * 以支持流水线优化
 *  
 * @return int 返回支持级别:
 *         0 - 不支持
 *         1 - 部分支持 (只有SSE4.2)
 *         2 - 完全支持 (有AVX2)
 */
PIPELINE_EXPORT int is_pipeline_opt_supported(void) {
    int features = detect_cpu_features();
    int prefetch_support = detect_prefetch_support();
    int cache_line_size = get_cache_line_size();
    
    // 检查流水线优化支持级别
    if ((features & 128) && prefetch_support) {
        // 完全支持 (AVX2 + 预取)
        return 2;
    } else if ((features & 32) && prefetch_support) {
        // 部分支持 (SSE4.2 + 预取)
        return 1;
    }
    
    // 不支持
    return 0;
}

// 其他辅助函数，用于调试和信息查询

/**
 * 获取CPU品牌字符串 
 */
PIPELINE_EXPORT const char* get_cpu_brand_string(void) {
    static char brand[64] = {0};
    
    // 已经获取过，直接返回
    if (brand[0] != '\0') {
        return brand;
    }
    
    int cpu_info[4] = {0};
    
#if defined(_MSC_VER)
    __cpuid(cpu_info, 0x80000000);
    unsigned int max_ext_id = cpu_info[0];
    
    if (max_ext_id >= 0x80000004) {
        // 获取品牌字符串
        char* brand_ptr = brand;
        for (unsigned int i = 0x80000002; i <= 0x80000004; i++) {
            __cpuid(cpu_info, i);
            memcpy(brand_ptr, cpu_info, sizeof(cpu_info));
            brand_ptr += 16;
        }
    } else {
        strcpy(brand, "Unknown CPU");
    }
#else
    unsigned int max_ext_id = __get_cpuid_max(0x80000000, NULL);
    
    if (max_ext_id >= 0x80000004) {
        // 获取品牌字符串
        unsigned int* brand_ptr = (unsigned int*)brand;
        
        unsigned int eax, ebx, ecx, edx;
        __get_cpuid(0x80000002, &eax, &ebx, &ecx, &edx);
        *brand_ptr++ = eax;
        *brand_ptr++ = ebx;
        *brand_ptr++ = ecx;
        *brand_ptr++ = edx;
        
        __get_cpuid(0x80000003, &eax, &ebx, &ecx, &edx);
        *brand_ptr++ = eax;
        *brand_ptr++ = ebx;
        *brand_ptr++ = ecx;
        *brand_ptr++ = edx;
        
        __get_cpuid(0x80000004, &eax, &ebx, &ecx, &edx);
        *brand_ptr++ = eax;
        *brand_ptr++ = ebx;
        *brand_ptr++ = ecx;
        *brand_ptr++ = edx;
    } else {
        strcpy(brand, "Unknown CPU");
    }
#endif

    // 移除前导空格和多余空格
    char* p = brand;
    while (*p == ' ') p++;
    
    char* src = p;
    char* dst = brand;
    char prev = '\0';
    
    while (*src) {
        if (*src == ' ' && prev == ' ') {
            src++;
            continue;
        }
        *dst++ = *src;
        prev = *src++;
    }
    *dst = '\0';
    
    return brand;
}

/**
 * 获取CPU特性字符串 
 */
PIPELINE_EXPORT const char* get_cpu_features_string(void) {
    static char features_str[256] = {0};
    
    // 已经获取过，直接返回
    if (features_str[0] != '\0') {
        return features_str;
    }
    
    int features = detect_cpu_features();
    sprintf(features_str, "Features: ");
    
    if (features & 1)   strcat(features_str, "SSE ");
    if (features & 2)   strcat(features_str, "SSE2 ");
    if (features & 4)   strcat(features_str, "SSE3 ");
    if (features & 8)   strcat(features_str, "SSSE3 ");
    if (features & 16)  strcat(features_str, "SSE4.1 ");
    if (features & 32)  strcat(features_str, "SSE4.2 ");
    if (features & 64)  strcat(features_str, "AVX ");
    if (features & 128) strcat(features_str, "AVX2 ");
    
    // 检查预取支持
    if (detect_prefetch_support()) {
        strcat(features_str, "PREFETCH ");
    }
    
    // 添加缓存行大小
    char cache_str[32];
    sprintf(cache_str, "CacheLineSize=%d", get_cache_line_size());
    strcat(features_str, cache_str);
    
    return features_str;
}

#if defined(PIPELINE_TEST)
int main() {
    printf("CPU: %s\n", get_cpu_brand_string());
    printf("CPU %s\n", get_cpu_features_string());
    printf("Pipeline optimization support level: %d\n", is_pipeline_opt_supported());
    return 0;
}
#endif 