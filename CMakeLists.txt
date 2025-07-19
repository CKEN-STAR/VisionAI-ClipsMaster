cmake_minimum_required(VERSION 3.10)
project(VisionAI-ClipsMaster VERSION 1.0.0 LANGUAGES CXX)

# 设置C++标准
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# 设置输出目录
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# 设置优化选项
if(MSVC)
    # MSVC编译器选项
    add_compile_options(/O2 /DNDEBUG /EHsc /fp:fast)
    if(CMAKE_SIZEOF_VOID_P EQUAL 8)
        add_compile_options(/arch:AVX2)
    endif()
else()
    # GCC/Clang编译器选项
    add_compile_options(-O3 -DNDEBUG -Wall -Wextra)
    
    # 检测系统架构
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "arm|aarch64")
        # ARM架构
        if(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64")
            add_compile_options(-march=native)
        else()
            add_compile_options(-march=native -mfpu=neon)
        endif()
    else()
        # x86_64/x86架构
        if(CMAKE_SIZEOF_VOID_P EQUAL 8)
            # 64位
            add_compile_options(-mavx2 -mfma)
        else()
            # 32位
            add_compile_options(-msse4.2)
        endif()
    endif()
endif()

# 检测macOS平台并链接Accelerate框架
if(APPLE)
    find_library(ACCELERATE_LIBRARY Accelerate)
    if(ACCELERATE_LIBRARY)
        message(STATUS "Found Accelerate framework")
        list(APPEND PLATFORM_LIBS ${ACCELERATE_LIBRARY})
    endif()
endif()

# 检查pthreads
find_package(Threads)
if(Threads_FOUND)
    list(APPEND PLATFORM_LIBS ${CMAKE_THREAD_LIBS_INIT})
endif()

# 包含目录
include_directories(${CMAKE_SOURCE_DIR})

# 添加SIMD库
add_library(simd_kernels SHARED 
    src/hardware/simd_kernels.cpp
)

# 添加汇编优化库
add_library(assembly_kernels SHARED 
    src/hardware/assembly_kernels.cpp
)

# 链接平台相关库
if(PLATFORM_LIBS)
    target_link_libraries(simd_kernels ${PLATFORM_LIBS})
    target_link_libraries(assembly_kernels ${PLATFORM_LIBS})
endif()

# 设置输出名称
set_target_properties(simd_kernels PROPERTIES 
    PREFIX "lib" 
    OUTPUT_NAME "simd_kernels"
)

set_target_properties(assembly_kernels PROPERTIES 
    PREFIX "lib" 
    OUTPUT_NAME "assembly_kernels"
)

# 重命名Windows上的输出
if(WIN32)
    set_target_properties(simd_kernels PROPERTIES 
        PREFIX "" 
        SUFFIX ".dll"
    )
    
    set_target_properties(assembly_kernels PROPERTIES 
        PREFIX "" 
        SUFFIX ".dll"
    )
endif()

# 安装规则
install(TARGETS simd_kernels assembly_kernels
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION lib)

# 输出信息
message(STATUS "CMAKE_SYSTEM_NAME: ${CMAKE_SYSTEM_NAME}")
message(STATUS "CMAKE_SYSTEM_PROCESSOR: ${CMAKE_SYSTEM_PROCESSOR}")
message(STATUS "CMAKE_C_COMPILER: ${CMAKE_C_COMPILER}")
message(STATUS "CMAKE_CXX_COMPILER: ${CMAKE_CXX_COMPILER}")
message(STATUS "CMAKE_BUILD_TYPE: ${CMAKE_BUILD_TYPE}")
message(STATUS "Platform Libraries: ${PLATFORM_LIBS}")

# 添加测试（如果启用）
option(BUILD_TESTS "Build tests" OFF)
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif() 