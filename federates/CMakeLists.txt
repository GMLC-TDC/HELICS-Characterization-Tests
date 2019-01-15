# ===============================================================
# Copyright (C) 2019, Battelle Memorial Institute
# Written by Jacob Hansen, Pacific Northwest National Laboratory
# ===============================================================

cmake_minimum_required(VERSION 3.4)

project(testSuite)

set(CMAKE_CXX_STANDARD 14)

find_package(HELICS REQUIRED)

find_path(FNCS_INCLUDE
    NAMES fncs.hpp
    PATHS ${FNCS_SOURCE_PATH}/include
)
if(NOT FNCS_INCLUDE)
  message(FATAL_ERROR "FNCS include path not found")
endif()

find_library(FNCS_LIBRARY
    NAMES fncs
    PATHS ${FNCS_SOURCE_PATH}/lib
)
if(NOT FNCS_LIBRARY)
  message(FATAL_ERROR "FNCS library not found")
endif()

find_library(CZMQ_LIBRARY
    NAMES czmq
    PATHS ${CZMQ_SOURCE_PATH}/lib
)
if(NOT CZMQ_LIBRARY)
  message(FATAL_ERROR "CZMQ library not found")
endif()

mark_as_advanced(BOOST_INSTALL_PATH)
mark_as_advanced(CMAKE_BUILD_TYPE)
mark_as_advanced(HELICS_APP)
mark_as_advanced(HELICS_BROKER)
mark_as_advanced(HELICS_DIR)
mark_as_advanced(HELICS_PLAYER)
mark_as_advanced(HELICS_RECORDER)
mark_as_advanced(BOOST_INSTALL_PATH)

SET(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

add_executable(testFedHELICS testFedHELICS.cpp)
add_executable(testFedFNCS testFedFNCS.cpp)

target_link_libraries(testFedHELICS ${ZeroMQ_LIBRARY})
target_link_libraries(testFedHELICS HELICS::helics-static)

target_link_libraries(testFedFNCS ${ZeroMQ_LIBRARY})
target_link_libraries(testFedFNCS ${CZMQ_LIBRARY})
target_link_libraries(testFedFNCS ${FNCS_LIBRARY})

target_include_directories(testFedFNCS PUBLIC ${FNCS_INCLUDE})

install(TARGETS testFedHELICS DESTINATION bin)
install(TARGETS testFedFNCS DESTINATION bin)
