cmake_minimum_required(VERSION 3.15)
project(poker_engine CXX)

# Set C++17 standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Optimization flags
if(MSVC)
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /O2 /DNDEBUG")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W4")
else()
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -march=native -DNDEBUG")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic")
endif()

# Find Python - prefer venv if available
if(DEFINED ENV{VIRTUAL_ENV})
    set(Python_ROOT_DIR "$ENV{VIRTUAL_ENV}")
    message(STATUS "Using virtual environment: $ENV{VIRTUAL_ENV}")
endif()
find_package(Python COMPONENTS Interpreter Development REQUIRED)
message(STATUS "Using Python: ${Python_EXECUTABLE}")

# Find pybind11
# First try to get cmake dir from Python module
execute_process(
    COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
    OUTPUT_VARIABLE pybind11_CMAKE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE pybind11_FIND_RESULT
    ERROR_QUIET
)

if(pybind11_FIND_RESULT EQUAL 0)
    # Some pybind11 versions quote the path when invoked through a Windows
    # environment. Remove those quotes before passing the directory to CMake.
    string(REPLACE "\"" "" pybind11_CMAKE_DIR "${pybind11_CMAKE_DIR}")
    message(STATUS "Found pybind11 cmake dir: ${pybind11_CMAKE_DIR}")
    set(pybind11_DIR "${pybind11_CMAKE_DIR}")
    find_package(pybind11 CONFIG REQUIRED)
else()
    # Try standard find_package as fallback
    find_package(pybind11 CONFIG)
    if(NOT pybind11_FOUND)
        message(FATAL_ERROR "pybind11 not found. Install with: pip install pybind11")
    endif()
endif()

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/cpp_engine/include)

# Source files
set(SOURCES
    cpp_engine/src/poker_engine.cpp
    cpp_engine/src/hand_evaluator.cpp
    cpp_engine/src/simulator.cpp
    cpp_engine/src/bindings.cpp
)

# Create Python module
pybind11_add_module(poker_engine ${SOURCES})

# Set output directory to poker_ai package
set_target_properties(poker_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/poker_ai"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/poker_ai"
)

# Visual Studio is a multi-config generator and otherwise appends the
# configuration name (for example, `Release`) to the output directory.
# Keep the importable extension at poker_ai/poker_engine.pyd on every config.
foreach(config Debug Release RelWithDebInfo MinSizeRel)
    set_target_properties(poker_engine PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY_${config} "${CMAKE_CURRENT_SOURCE_DIR}/poker_ai"
        RUNTIME_OUTPUT_DIRECTORY_${config} "${CMAKE_CURRENT_SOURCE_DIR}/poker_ai"
    )
endforeach()

# Keep a stable import location even when a multi-config generator places the
# build artifact in a configuration-specific directory.
add_custom_command(TARGET poker_engine POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "$<TARGET_FILE:poker_engine>"
        "${CMAKE_CURRENT_SOURCE_DIR}/poker_ai/$<TARGET_FILE_NAME:poker_engine>"
)

# Platform-specific settings
if(WIN32)
    # Windows: .pyd extension
    set_target_properties(poker_engine PROPERTIES SUFFIX ".pyd")
endif()

# Install target
install(TARGETS poker_engine
    LIBRARY DESTINATION poker_ai
    RUNTIME DESTINATION poker_ai
)

# Print configuration summary
message(STATUS "=== Poker Engine Configuration ===")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "Python: ${Python_VERSION}")
message(STATUS "pybind11: ${pybind11_VERSION}")
message(STATUS "Output: ${CMAKE_CURRENT_SOURCE_DIR}/poker_ai/poker_engine")
message(STATUS "==================================")

