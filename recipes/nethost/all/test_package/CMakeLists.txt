cmake_minimum_required(VERSION 3.1)
project(test_package)

find_package(nethost REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} nethost::nethost)
set_property(TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 17)
