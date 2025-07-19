cmake_minimum_required(VERSION 3.10)
project(pipeline_opt VERSION 1.0.0 LANGUAGES C ASM)

# 检测操作系统和架构
if(WIN32)
    set(PLATFORM_WINDOWS 1)
elseif(APPLE)
    set(PLATFORM_MACOS 1)
elseif(UNIX AND NOT APPLE)
    set(PLATFORM_LINUX 1)
endif()

# 检测CPU架构
if(CMAKE_SYSTEM_PROCESSOR MATCHES "amd64.*|x86_64.*|AMD64.*")
    set(ARCH_X86_64 1)
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "i686.*|i386.*|x86.*")
    set(ARCH_X86 1)
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(aarch64.*|AARCH64.*|arm64.*|ARM64.*)")
    set(ARCH_ARM64 1)
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm.*|ARM.*)")
    set(ARCH_ARM 1)
else()
    message(WARNING "Unknown CPU architecture")
endif()

# 设置编译选项
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# 添加定义
if(PLATFORM_WINDOWS)
    add_definitions(-DPLATFORM_WINDOWS)
elseif(PLATFORM_MACOS)
    add_definitions(-DPLATFORM_MACOS)
elseif(PLATFORM_LINUX)
    add_definitions(-DPLATFORM_LINUX)
endif()

if(ARCH_X86_64)
    add_definitions(-DARCH_X86_64)
elseif(ARCH_X86)
    add_definitions(-DARCH_X86)
elseif(ARCH_ARM64)
    add_definitions(-DARCH_ARM64)
elseif(ARCH_ARM)
    add_definitions(-DARCH_ARM)
endif()

# 设置文件列表
set(SOURCES
    pipeline_opt.c
)

# nasm文件处理
if(ARCH_X86_64 OR ARCH_X86)
    # 找到NASM汇编器
    find_program(NASM_EXECUTABLE NAMES nasm yasm)
    if(NASM_EXECUTABLE)
        message(STATUS "Found NASM: ${NASM_EXECUTABLE}")
        
        # 设置NASM格式
        if(PLATFORM_WINDOWS)
            if(ARCH_X86_64)
                set(NASM_FORMAT win64)
            else()
                set(NASM_FORMAT win32)
            endif()
        elseif(PLATFORM_MACOS)
            if(ARCH_X86_64)
                set(NASM_FORMAT macho64)
            else()
                set(NASM_FORMAT macho32)
            endif()
        elseif(PLATFORM_LINUX)
            if(ARCH_X86_64)
                set(NASM_FORMAT elf64)
            else()
                set(NASM_FORMAT elf32)
            endif()
        endif()
        
        # 添加汇编文件
        set(ASM_SOURCE pipeline_opt.asm)
        set(ASM_OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/pipeline_opt_asm.o)
        
        # 自定义命令编译汇编文件
        add_custom_command(
            OUTPUT ${ASM_OUTPUT}
            COMMAND ${NASM_EXECUTABLE} -f ${NASM_FORMAT} -o ${ASM_OUTPUT} ${CMAKE_CURRENT_SOURCE_DIR}/${ASM_SOURCE}
            DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${ASM_SOURCE}
            COMMENT "Assembling ${ASM_SOURCE}"
        )
        
        # 添加到源文件列表
        list(APPEND SOURCES ${ASM_OUTPUT})
    else()
        message(WARNING "NASM not found, using C implementation only")
    endif()
endif()

# 添加共享库
add_library(pipeline_opt SHARED ${SOURCES})

# 链接依赖库
if(PLATFORM_MACOS)
    # macOS平台需要额外的加速库
    find_library(ACCELERATE_FRAMEWORK Accelerate)
    if(ACCELERATE_FRAMEWORK)
        target_link_libraries(pipeline_opt ${ACCELERATE_FRAMEWORK})
    endif()
endif()

# 添加编译选项
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(pipeline_opt PRIVATE -Wall -Wextra -O3)
    
    # 如果支持，添加SIMD指令集
    include(CheckCCompilerFlag)
    check_c_compiler_flag(-mavx2 COMPILER_SUPPORTS_AVX2)
    if(COMPILER_SUPPORTS_AVX2)
        target_compile_options(pipeline_opt PRIVATE -mavx2)
    endif()
elseif(MSVC)
    target_compile_options(pipeline_opt PRIVATE /W4 /O2)
    
    # Windows平台下的SIMD指令集
    if(ARCH_X86_64 OR ARCH_X86)
        target_compile_options(pipeline_opt PRIVATE /arch:AVX2)
    endif()
endif()

# 添加包含目录
target_include_directories(pipeline_opt PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# 安装规则
install(TARGETS pipeline_opt
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)
install(FILES pipeline_opt.h DESTINATION include) 