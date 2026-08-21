cmake_minimum_required(VERSION 3.16)
project(sovereign_edge_alpha CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

if(NOT APPLE)
    find_program(CLANG_EXECUTABLE clang REQUIRED)
    execute_process(COMMAND uname -m OUTPUT_VARIABLE ARCH_NAME OUTPUT_STRIP_TRAILING_WHITESPACE)

    add_custom_command(
        OUTPUT ${CMAKE_CURRENT_SOURCE_DIR}/src/ebpf/xdp_shield.bpf.o
        COMMAND ${CLANG_EXECUTABLE} -O2 -target bpf
                -I/usr/include/${ARCH_NAME}-linux-gnu
                -I/usr/include
                -c ${CMAKE_CURRENT_SOURCE_DIR}/src/ebpf/xdp_shield.bpf.c
                -o ${CMAKE_CURRENT_SOURCE_DIR}/src/ebpf/xdp_shield.bpf.o
        DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/ebpf/xdp_shield.bpf.c
                ${CMAKE_CURRENT_SOURCE_DIR}/include/ebpf_shared.h
        COMMENT "Building eBPF BPF bytecode object..."
    )

    add_custom_target(ebpf_target ALL DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/ebpf/xdp_shield.bpf.o)
else()
    message(STATUS "macOS detected: Skipping eBPF compilation.")
endif()

# --- Sovereign Daemon Binary ---
add_executable(sovereign_alpha_daemon
    src/pqc_auth.cpp
    src/oci_proxy.cpp
    src/p2p_mesh.cpp
    src/main.cpp
)

if(NOT APPLE)
    add_dependencies(sovereign_alpha_daemon ebpf_target)
endif()

target_link_libraries(sovereign_alpha_daemon PRIVATE pthread)