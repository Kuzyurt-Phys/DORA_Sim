# ----------------------------------------------------------------------------
# CMakeLists.txt for DORA_Sim
# Author: Ahmet Kuzyurt
# ----------------------------------------------------------------------------

cmake_minimum_required(VERSION 3.16...3.30)
project(DORA_Sim)

find_package(Geant4 REQUIRED ui_all vis_all)

include_directories(${PROJECT_SOURCE_DIR}/include ${Geant4_INCLUDE_DIRS})

file(GLOB sources ${PROJECT_SOURCE_DIR}/src/*.cc)
file(GLOB headers ${PROJECT_SOURCE_DIR}/include/*.hh)

add_executable(DORA_Sim DORA_Sim.cc ${sources} ${headers})

target_link_libraries(DORA_Sim ${Geant4_LIBRARIES})

set(DORA_Sim_SCRIPTS
    init_vis.mac
    vis.mac
    run.mac
    analyze_dora.py
)

foreach(_script ${DORA_Sim_SCRIPTS})
  configure_file(
    ${PROJECT_SOURCE_DIR}/${_script}
    ${PROJECT_BINARY_DIR}/${_script}
    COPYONLY
  )
endforeach()