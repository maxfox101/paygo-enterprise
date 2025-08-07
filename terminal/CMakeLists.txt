cmake_minimum_required(VERSION 3.16)
project(PayGoTerminal VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Опции компиляции
option(BUILD_TESTS "Build tests" ON)
option(BUILD_GUI "Build GUI application" ON)
option(BUILD_BIOMETRIC "Build with biometric support" ON)

# Поиск зависимостей
find_package(PkgConfig REQUIRED)
find_package(OpenCV REQUIRED)
find_package(SQLite3 REQUIRED)

# Qt для GUI
if(BUILD_GUI)
    find_package(Qt6 REQUIRED COMPONENTS Core Widgets Network)
    set(CMAKE_AUTOMOC ON)
    set(CMAKE_AUTORCC ON)
    set(CMAKE_AUTOUIC ON)
endif()

# cURL для HTTP запросов
find_package(CURL REQUIRED)

# JSON библиотека
find_package(nlohmann_json REQUIRED)

# Raspberry Pi GPIO (если доступно)
if(EXISTS "/opt/vc/include/bcm_host.h")
    set(RPI_BUILD ON)
    include_directories(/opt/vc/include)
    link_directories(/opt/vc/lib)
endif()

# Исходные файлы
set(CORE_SOURCES
    src/core/terminal_manager.cpp
    src/core/payment_processor.cpp
    src/core/card_reader.cpp
    src/core/receipt_printer.cpp
    src/core/config_manager.cpp
    src/core/logger.cpp
)

set(NETWORK_SOURCES
    src/network/api_client.cpp
    src/network/websocket_client.cpp
    src/network/ssl_manager.cpp
)

set(HARDWARE_SOURCES
    src/hardware/nfc_reader.cpp
    src/hardware/qr_scanner.cpp
    src/hardware/display_controller.cpp
    src/hardware/sound_manager.cpp
)

if(BUILD_BIOMETRIC)
    list(APPEND HARDWARE_SOURCES
        src/biometry/fingerprint_scanner.cpp
        src/biometry/face_recognition.cpp
        src/biometry/biometric_manager.cpp
    )
endif()

set(DATABASE_SOURCES
    src/database/sqlite_manager.cpp
    src/database/transaction_storage.cpp
    src/database/cache_manager.cpp
)

if(BUILD_GUI)
    set(GUI_SOURCES
        src/gui/main_window.cpp
        src/gui/payment_dialog.cpp
        src/gui/settings_dialog.cpp
        src/gui/status_widget.cpp
        src/gui/keypad_widget.cpp
    )
    
    set(GUI_HEADERS
        include/gui/main_window.h
        include/gui/payment_dialog.h
        include/gui/settings_dialog.h
        include/gui/status_widget.h
        include/gui/keypad_widget.h
    )
endif()

# Заголовочные файлы
set(HEADERS
    include/core/terminal_manager.h
    include/core/payment_processor.h
    include/core/card_reader.h
    include/core/receipt_printer.h
    include/core/config_manager.h
    include/core/logger.h
    include/network/api_client.h
    include/network/websocket_client.h
    include/network/ssl_manager.h
    include/hardware/nfc_reader.h
    include/hardware/qr_scanner.h
    include/hardware/display_controller.h
    include/hardware/sound_manager.h
    include/database/sqlite_manager.h
    include/database/transaction_storage.h
    include/database/cache_manager.h
    include/common/types.h
    include/common/constants.h
    include/common/utils.h
)

if(BUILD_BIOMETRIC)
    list(APPEND HEADERS
        include/biometry/fingerprint_scanner.h
        include/biometry/face_recognition.h
        include/biometry/biometric_manager.h
    )
endif()

# Основная библиотека
add_library(paygo_core STATIC
    ${CORE_SOURCES}
    ${NETWORK_SOURCES}
    ${HARDWARE_SOURCES}
    ${DATABASE_SOURCES}
    ${HEADERS}
)

target_include_directories(paygo_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${OpenCV_INCLUDE_DIRS}
)

target_link_libraries(paygo_core
    ${OpenCV_LIBS}
    SQLite::SQLite3
    CURL::libcurl
    nlohmann_json::nlohmann_json
)

if(RPI_BUILD)
    target_link_libraries(paygo_core
        bcm_host
        vcos
        vchiq_arm
        wiringPi
    )
    target_compile_definitions(paygo_core PRIVATE RPI_BUILD)
endif()

if(BUILD_BIOMETRIC)
    target_compile_definitions(paygo_core PRIVATE BIOMETRIC_SUPPORT)
endif()

# GUI приложение
if(BUILD_GUI)
    add_executable(paygo_terminal
        src/main.cpp
        ${GUI_SOURCES}
        ${GUI_HEADERS}
    )
    
    target_link_libraries(paygo_terminal
        paygo_core
        Qt6::Core
        Qt6::Widgets
        Qt6::Network
    )
    
    target_include_directories(paygo_terminal PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include/gui
    )
endif()

# Консольное приложение
add_executable(paygo_terminal_console
    src/main_console.cpp
)

target_link_libraries(paygo_terminal_console
    paygo_core
)

# Тесты
if(BUILD_TESTS)
    enable_testing()
    find_package(GTest REQUIRED)
    
    add_executable(paygo_tests
        tests/test_payment_processor.cpp
        tests/test_api_client.cpp
        tests/test_config_manager.cpp
        tests/test_database.cpp
    )
    
    target_link_libraries(paygo_tests
        paygo_core
        GTest::gtest_main
    )
    
    add_test(NAME PayGoTests COMMAND paygo_tests)
endif()

# Установка
install(TARGETS paygo_terminal_console
    RUNTIME DESTINATION bin
)

if(BUILD_GUI)
    install(TARGETS paygo_terminal
        RUNTIME DESTINATION bin
    )
endif()

install(DIRECTORY config/
    DESTINATION etc/paygo
    FILES_MATCHING PATTERN "*.json"
)

# Создание пакета
set(CPACK_PACKAGE_NAME "PayGo Terminal")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_DESCRIPTION "PayGo Payment Terminal Software")
set(CPACK_PACKAGE_CONTACT "support@paygo.ru")

if(RPI_BUILD)
    set(CPACK_GENERATOR "DEB")
    set(CPACK_DEBIAN_PACKAGE_DEPENDS "libopencv-dev, libcurl4-openssl-dev, libsqlite3-dev")
endif()

include(CPack) 