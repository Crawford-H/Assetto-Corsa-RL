cmake_minimum_required(VERSION 3.25)

project(AcSharedMemoryProxy LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(minhook CONFIG REQUIRED)

add_library(version_proxy SHARED
    src/dllmain.cpp
    src/exports.def
)

target_link_libraries(version_proxy PRIVATE minhook::minhook)

target_compile_definitions(version_proxy PRIVATE
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)

set_target_properties(version_proxy PROPERTIES
    OUTPUT_NAME "version"
    PREFIX ""
)
