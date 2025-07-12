/*
 * ГЛАВНЫЙ ФАЙЛ ТРАНСПОРТНОГО КАТАЛОГА
 * 
 * Точка входа в программу. Реализует полный цикл работы приложения:
 * 1. Чтение JSON запросов из стандартного ввода
 * 2. Парсинг и применение команд создания данных
 * 3. Обработка запросов на получение информации
 * 4. Вывод результатов в JSON формате
 * 
 * СТРУКТУРА JSON ВХОДА:
 * {
 *   "base_requests": [...],     // Команды создания остановок и маршрутов
 *   "stat_requests": [...],     // Запросы на получение информации
 *   "render_settings": {...}    // Настройки для отрисовки карты
 * }
 * 
 * АРХИТЕКТУРА ОБРАБОТКИ:
 * - Модульная структура с разделением ответственности
 * - Использование пространств имён для организации кода
 * - Потоковая обработка JSON (stdin → stdout)
 */

#include <iostream>
#include <string>

#include "json_reader.h"
#include "request_handler.h"

using namespace std;

/**
 * ГЛАВНАЯ ФУНКЦИЯ ПРОГРАММЫ
 * 
 * Выполняет полный цикл обработки транспортного каталога:
 * 
 * ЭТАПЫ РАБОТЫ:
 * 1. Создание пустого каталога
 * 2. Загрузка и парсинг JSON из stdin
 * 3. Извлечение разделов запроса (base_requests, stat_requests, render_settings)
 * 4. Парсинг настроек рендеринга карты
 * 5. Применение команд создания данных к каталогу
 * 6. Обработка запросов на получение информации
 * 7. Вывод результатов в JSON формате в stdout
 * 
 * ОБРАБОТКА ОШИБОК:
 * - JSON парсер выбрасывает исключения при некорректном формате
 * - Отсутствующие ключи в JSON приведут к исключению std::out_of_range
 * - Некорректные типы данных вызовут исключения из Node::As* методов
 */
int main() {
	// === ИНИЦИАЛИЗАЦИЯ ===
	
	// Создаем пустой транспортный каталог
	catalogue::TransportCatalogue catalogue;
	
	// === ЗАГРУЗКА И ПАРСИНГ JSON ===
	
	// Загружаем JSON документ из стандартного ввода
	json::Document doc = json::Load(std::cin);
	const json::Dict requests = doc.GetRoot().AsDict();
	
	// Извлекаем разделы запроса
	const json::Dict &render_request = requests.at("render_settings").AsDict();  // Настройки карты
	const json::Array base_requests = requests.at("base_requests").AsArray();    // Команды создания
	const json::Array stat_requests = requests.at("stat_requests").AsArray();    // Запросы информации
	
	// === ПАРСИНГ НАСТРОЕК ===
	
	// Парсим настройки рендеринга карты (цвета, размеры, отступы)
	render::RenderSettings settings = catalogue::input::ParseRenderSettings(render_request);
	
	// === СОЗДАНИЕ ДАННЫХ ===
	
	// Создаем парсер для команд создания остановок и маршрутов
	catalogue::input::JsonReader reader;
	
	// Парсим команды создания (остановки, маршруты, расстояния)
	reader.ParseDocument(base_requests);
	
	// Применяем команды к каталогу (заполняем данными)
	reader.ApplyCommands(catalogue);
	
	// === ОБРАБОТКА ЗАПРОСОВ И ВЫВОД ===
	
	// Обрабатываем запросы на получение информации и генерируем JSON ответ
	json::Document result = catalogue::output::PrintStat(stat_requests, catalogue, settings);
	
	// Выводим результат в стандартный вывод
	json::Print(result, std::cout);

	return 0;
}
