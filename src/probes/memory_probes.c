/**
 * memory_probes.c - 高性能C内存探针实现
 * 
 * 此模块提供了高性能的C语言内存探针实现，用于在关键代码段中监控内存使用情况。
 * 可通过Python的ctypes模块调用，或编译为扩展模块。
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <sys/resource.h>
#endif

/* 定义节区属性，便于自动化工具识别探针函数 */
#ifdef __GNUC__
#define PROBE_SECTION __attribute__((section(".probes")))
#else
#define PROBE_SECTION
#endif

/* 定义内存探针结构 */
typedef struct {
    const char* name;           /* 探针名称 */
    const char* location;       /* 代码位置 */
    uint64_t threshold;         /* 内存阈值（MB） */
    uint64_t timestamp;         /* 时间戳 */
    int level;                  /* 探针级别 */
} MemoryProbe;

/* 内存探针状态结果 */
typedef struct {
    uint64_t current_memory;    /* 当前内存使用量（MB） */
    uint64_t peak_memory;       /* 峰值内存（MB） */
    uint64_t available_memory;  /* 可用内存（MB） */
    uint64_t timestamp;         /* 检查时间戳 */
    int threshold_exceeded;     /* 是否超过阈值 */
    int error_code;             /* 错误代码 */
} MemoryProbeResult;

/**
 * 获取当前进程的内存使用情况
 */
static uint64_t current_mem(void) {
    uint64_t memory_usage = 0;
    
#ifdef _WIN32
    /* Windows实现 */
    PROCESS_MEMORY_COUNTERS_EX pmc;
    if (GetProcessMemoryInfo(GetCurrentProcess(), (PROCESS_MEMORY_COUNTERS*)&pmc, sizeof(pmc))) {
        memory_usage = (uint64_t)(pmc.WorkingSetSize / (1024 * 1024));
    }
#else
    /* Linux/Unix实现 */
    FILE* file = fopen("/proc/self/status", "r");
    if (file) {
        char line[128];
        while (fgets(line, sizeof(line), file)) {
            if (strncmp(line, "VmRSS:", 6) == 0) {
                /* VmRSS以KB为单位，转换为MB */
                memory_usage = (uint64_t)atoll(line + 6) / 1024;
                break;
            }
        }
        fclose(file);
    }
#endif

    return memory_usage;
}

/**
 * 获取系统可用内存
 */
static uint64_t available_mem(void) {
    uint64_t available = 0;
    
#ifdef _WIN32
    /* Windows实现 */
    MEMORYSTATUSEX memInfo;
    memInfo.dwLength = sizeof(MEMORYSTATUSEX);
    if (GlobalMemoryStatusEx(&memInfo)) {
        available = (uint64_t)(memInfo.ullAvailPhys / (1024 * 1024));
    }
#else
    /* Linux/Unix实现 */
    FILE* file = fopen("/proc/meminfo", "r");
    if (file) {
        char line[128];
        while (fgets(line, sizeof(line), file)) {
            if (strncmp(line, "MemAvailable:", 13) == 0) {
                /* MemAvailable以KB为单位，转换为MB */
                available = (uint64_t)atoll(line + 13) / 1024;
                break;
            }
        }
        fclose(file);
    }
#endif

    return available;
}

/**
 * 写日志函数
 */
static void log_alert(const char* message, void* return_addr) {
    time_t now;
    time(&now);
    char timestamp[32];
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", localtime(&now));

    fprintf(stderr, "[%s] [ALERT] Memory Probe: %s (Location: %p)\n", 
            timestamp, message, return_addr);
}

/**
 * 内存探针检查函数 - 用于在C代码中检查内存使用
 */
PROBE_SECTION
int mem_probe(MemoryProbe* probe, MemoryProbeResult* result) {
    /* 初始化结果 */
    if (result) {
        memset(result, 0, sizeof(MemoryProbeResult));
        result->timestamp = (uint64_t)time(NULL);
    }
    
    /* 获取内存使用情况 */
    uint64_t mem_usage = current_mem();
    uint64_t mem_available = available_mem();
    
    /* 填充结果 */
    if (result) {
        result->current_memory = mem_usage;
        result->available_memory = mem_available;
        
        /* 更新峰值内存 */
        static uint64_t peak_memory = 0;
        if (mem_usage > peak_memory) {
            peak_memory = mem_usage;
        }
        result->peak_memory = peak_memory;
    }
    
    /* 检查是否超过阈值 */
    int exceeded = 0;
    if (probe && probe->threshold > 0 && mem_usage > probe->threshold) {
        exceeded = 1;
        
        /* 记录日志 */
        if (probe->name) {
            char message[256];
            snprintf(message, sizeof(message), 
                     "内存超限在函数: %s (当前: %llu MB, 阈值: %llu MB)", 
                     probe->name, (unsigned long long)mem_usage, 
                     (unsigned long long)probe->threshold);
            
            log_alert(message, __builtin_return_address(0));
        }
        
        /* 更新结果 */
        if (result) {
            result->threshold_exceeded = 1;
        }
    }
    
    return exceeded;
}

/**
 * 快速内存检查点 - 可以在高频调用的代码中使用
 */
PROBE_SECTION
void fast_mem_check(uint64_t threshold) {
    /* 快速检查当前内存是否超过阈值 */
    if (current_mem() > threshold) {
        log_alert("内存超限在函数", __builtin_return_address(0));
    }
}

/**
 * 导出API: 检查内存使用情况
 * 可通过Python的ctypes调用
 */
PROBE_SECTION
int check_memory_usage(const char* probe_name, uint64_t threshold, MemoryProbeResult* result) {
    MemoryProbe probe;
    probe.name = probe_name;
    probe.location = "API call";
    probe.threshold = threshold;
    probe.timestamp = (uint64_t)time(NULL);
    probe.level = 2; /* 中等级别 */
    
    return mem_probe(&probe, result);
}

/**
 * 测试函数
 */
int test_memory_probe(void) {
    MemoryProbe probe;
    MemoryProbeResult result;
    
    probe.name = "test_probe";
    probe.location = __func__;
    probe.threshold = 100; /* 100MB */
    probe.timestamp = (uint64_t)time(NULL);
    probe.level = 1;
    
    int status = mem_probe(&probe, &result);
    
    printf("Memory Probe Test:\n");
    printf("  Current Memory: %llu MB\n", (unsigned long long)result.current_memory);
    printf("  Peak Memory: %llu MB\n", (unsigned long long)result.peak_memory);
    printf("  Available Memory: %llu MB\n", (unsigned long long)result.available_memory);
    printf("  Threshold Exceeded: %s\n", result.threshold_exceeded ? "YES" : "NO");
    
    return status;
}

#ifdef MEMORY_PROBE_MAIN
/**
 * 独立运行时的主函数
 */
int main(int argc, char** argv) {
    return test_memory_probe();
}
#endif 