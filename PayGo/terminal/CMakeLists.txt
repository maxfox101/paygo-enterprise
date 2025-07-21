cmake_minimum_required(VERSION 3.16)

project(PayGoTerminal VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Найти требуемые библиотеки Qt
find_package(Qt6 REQUIRED COMPONENTS Core Widgets Network)

# Найти OpenCV для биометрии
find_package(OpenCV REQUIRED)

# Исходные файлы
file(GLOB_RECURSE SOURCES 
    "src/*.cpp"
    "src/*.h"
    "gui/*.cpp"
    "gui/*.h"
    "biometry/*.cpp" 
    "biometry/*.h"
    "payments/*.cpp"
    "payments/*.h"
)

# Заголовочные файлы
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/gui
    ${CMAKE_CURRENT_SOURCE_DIR}/biometry
    ${CMAKE_CURRENT_SOURCE_DIR}/payments
    ${OpenCV_INCLUDE_DIRS}
)

# Создание исполняемого файла
add_executable(PayGoTerminal ${SOURCES})

# Линковка библиотек
target_link_libraries(PayGoTerminal
    Qt6::Core
    Qt6::Widgets
    Qt6::Network
    ${OpenCV_LIBS}
)

# Установка
install(TARGETS PayGoTerminal
    RUNTIME DESTINATION bin
)

# Копирование конфигурационных файлов
install(FILES 
    ${CMAKE_CURRENT_SOURCE_DIR}/../config/terminal_config.json
    DESTINATION etc/paygo
) 