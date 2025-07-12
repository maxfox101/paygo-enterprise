#include "transport_catalogue.h"

#include <algorithm>
#include <cassert>
#include <unordered_set>

/*
 * РЕАЛИЗАЦИЯ ТРАНСПОРТНОГО КАТАЛОГА
 * 
 * Файл содержит реализацию всех методов TransportCatalogue.
 * Включает оптимизации для производительности:
 * - O(n) алгоритмы вместо O(n²) где возможно
 * - Избежание копирования объектов
 * - Использование move семантики
 * - Эффективная работа с хеш-таблицами
 */

namespace catalogue {

/**
 * ДОБАВЛЕНИЕ ОСТАНОВКИ В КАТАЛОГ
 * 
 * Добавляет новую остановку в систему с защитой от дублирования.
 * 
 * АЛГОРИТМ:
 * 1. Проверяем, не существует ли уже такая остановка
 * 2. Добавляем в основное хранилище (stops_)
 * 3. Создаем индекс для быстрого поиска (stops_ptr_)
 * 4. Инициализируем пустой список маршрутов (stop_buses_)
 * 
 * СЛОЖНОСТЬ: O(n) из-за поиска дубликатов
 * 
 * @param name Название остановки
 * @param coord Географические координаты
 */
void TransportCatalogue::AddStop(const std::string_view name, geo::Coordinates coord) {
	// Проверяем дубликаты (можно было бы оптимизировать через хеш-таблицу)
	if(std::find(stops_.begin(), stops_.end(), transport::Stop{std::string(name), coord}) != stops_.end()) {
		return;
	}

	// Добавляем остановку в основное хранилище
	stops_.push_back(transport::Stop{std::string(name), coord});
	transport::Stop &stop = stops_.back();
	
	// Создаем индекс для быстрого поиска
	stops_ptr_.insert({stop.name, &stop});
	
	// Инициализируем пустой набор маршрутов для этой остановки
	stop_buses_.insert({stop.name, {}});
}

/**
 * ДОБАВЛЕНИЕ МАРШРУТА (ВЕРСИЯ С КОПИРОВАНИЕМ)
 * 
 * Перегрузка для случаев, когда нужно сохранить оригинальный список остановок.
 * Создает копию списка и вызывает версию с move семантикой.
 * 
 * @param name Номер маршрута
 * @param stops_list Список указателей на остановки (копируется)
 * @param is_rountrip true если маршрут кольцевой
 */
void TransportCatalogue::AddBus(const std::string_view name, const std::vector<const transport::Stop*> &stops_list, bool is_rountrip) {
	AddBus(name, std::vector<const transport::Stop*>(stops_list), is_rountrip);
}

/**
 * ДОБАВЛЕНИЕ МАРШРУТА (ВЕРСИЯ С ПЕРЕМЕЩЕНИЕМ)
 * 
 * Основная реализация добавления маршрута с оптимизацией через move семантику.
 * 
 * АЛГОРИТМ:
 * 1. Проверяем дубликаты маршрутов
 * 2. Добавляем в основное хранилище (buses_)
 * 3. Создаем индекс для быстрого поиска (buses_ptr_)
 * 4. Обновляем обратный индекс (stop_buses_) для всех остановок маршрута
 * 
 * ОПТИМИЗАЦИИ:
 * - std::move для избежания копирования списка остановок
 * - Пакетное обновление индексов
 * 
 * @param name Номер маршрута  
 * @param stops_list Список указателей на остановки (перемещается)
 * @param is_rountrip true если маршрут кольцевой
 */
void TransportCatalogue::AddBus(const std::string_view name, std::vector<const transport::Stop*> &&stops_list, bool is_rountrip) {
	// Проверяем дубликаты
	if(std::find(buses_.begin(), buses_.end(), transport::Bus{std::string(name), stops_list}) != buses_.end()) {
		return;
	}

	// Добавляем маршрут в основное хранилище с перемещением данных
	buses_.push_back(transport::Bus{std::string(name), std::move(stops_list), is_rountrip});
	const transport::Bus &bus = buses_.back();
	
	// Создаем индекс для быстрого поиска
	buses_ptr_.insert({bus.number, &bus});

	// Обновляем обратный индекс: добавляем этот маршрут ко всем его остановкам
	for(const transport::Stop *stop : bus.stop_list) {
		stop_buses_[stop->name].insert(bus.number);
	}
}

// === МЕТОДЫ ПОИСКА ===

/** Поиск остановки по названию за O(1) благодаря хеш-таблице */
const transport::Stop* TransportCatalogue::FindStop(std::string_view str) const {
	auto it = stops_ptr_.find(str);
	return it != stops_ptr_.end() ? it->second : nullptr;
}

/** Поиск маршрута по номеру за O(1) благодаря хеш-таблице */
const transport::Bus* TransportCatalogue::FindBus(std::string_view num) const {
	auto it = buses_ptr_.find(num);
	return it != buses_ptr_.end() ? it->second : nullptr;
}

/**
 * ВЫЧИСЛЕНИЕ ИНФОРМАЦИИ О МАРШРУТЕ
 * 
 * Главный метод для получения полной статистики по маршруту.
 * Вычисляет все ключевые характеристики маршрута.
 * 
 * ВЫЧИСЛЯЕМЫЕ ХАРАКТЕРИСТИКИ:
 * - stops: общее количество остановок (с повторениями)
 * - unique_stops: количество уникальных остановок
 * - length: длина маршрута по дорогам (реальная)
 * - curvature: коэффициент извилистости (length / прямое_расстояние)
 * 
 * АЛГОРИТМИЧЕСКИЕ ОПТИМИЗАЦИИ:
 * 1. O(n) поиск уникальных остановок через unordered_set (вместо O(n²))
 * 2. Избежание копирования объектов Stop (работаем с указателями)
 * 3. Единый проход для вычисления длин
 * 4. Защита от деления на ноль при вычислении кривизны
 * 
 * @param bus Ссылка на маршрут для анализа
 * @return BusInfo со всей статистикой маршрута
 */
detail::BusInfo TransportCatalogue::GetBusInfo(const transport::Bus &bus) const {
	int stops = bus.stop_list.size();
	std::unordered_set<std::string_view> unique_stops;

	// ОПТИМИЗАЦИЯ: O(n) вместо O(n²) для поиска уникальных остановок
	// Используем unordered_set вместо линейного поиска для каждой остановки
	for(const transport::Stop *stop : bus.stop_list) {
		unique_stops.insert(stop->name);
	}

	int length = 0;        // Длина по дорогам (реальная)
	double real_length = 0; // Длина по прямой (геодезическая)

	// ОПТИМИЗАЦИЯ: Избегаем копирования объектов Stop, работаем с указателями
	const transport::Stop *prev = bus.stop_list[0];
	for(size_t i = 1; i < bus.stop_list.size(); ++i) {
		const transport::Stop *cur = bus.stop_list[i];

		// Вычисляем расстояние по прямой (геодезическое)
		real_length += geo::ComputeDistance(prev->coordinates, cur->coordinates);
		
		// Вычисляем расстояние по дорогам (из кэша)
		length += GetDistance(prev->name, cur->name);
		
		prev = cur;
	}

	// ЗАЩИТА ОТ ДЕЛЕНИЯ НА НОЛЬ: проверяем real_length > 0
	double curvature = real_length > 0 ? length / real_length : 0.0;

	return {stops, static_cast<int>(unique_stops.size()), length, curvature};
}

/**
 * ПОЛУЧЕНИЕ СПИСКА МАРШРУТОВ ДЛЯ ОСТАНОВКИ
 * 
 * Возвращает отсортированный список всех маршрутов, 
 * которые проходят через указанную остановку.
 * 
 * @param stop Ссылка на остановку
 * @return Вектор названий маршрутов в алфавитном порядке
 */
std::vector<std::string_view> TransportCatalogue::GetStopInfo(const transport::Stop &stop) const {
	auto it = stop_buses_.find(stop.name);

	if(it != stop_buses_.end()){
		// Преобразуем set в vector для сортировки
		std::vector<std::string_view> vec = {it->second.begin(), it->second.end()};
		std::sort(vec.begin(), vec.end());
		return vec;
	}

	return {};  // Пустой список если остановка не найдена
}

// === МЕТОДЫ РАБОТЫ С РАССТОЯНИЯМИ ===

/**
 * УСТАНОВКА РАССТОЯНИЯ МЕЖДУ ОСТАНОВКАМИ
 * 
 * Сохраняет реальное расстояние по дорогам между двумя остановками.
 * Используется для более точного вычисления длин маршрутов.
 * 
 * @param from Название начальной остановки
 * @param to Название конечной остановки  
 * @param distance Расстояние в метрах
 */
void TransportCatalogue::SetDistance(const std::string_view from, const std::string_view to, int distance) {
	auto stop1 = FindStop(from);
	auto stop2 = FindStop(to);
	assert(stop1 && stop2);  // Остановки должны существовать

	auto p = std::make_pair(stop1, stop2);
	distances_.insert({p, distance});
}

/**
 * ПОЛУЧЕНИЕ РАССТОЯНИЯ МЕЖДУ ОСТАНОВКАМИ
 * 
 * Возвращает реальное расстояние по дорогам между остановками.
 * Поддерживает двунаправленный поиск (A→B и B→A).
 * 
 * АЛГОРИТМ:
 * 1. Ищем прямое направление (from → to)
 * 2. Если не найдено, ищем обратное (to → from)
 * 3. Возвращаем 0 если расстояние не задано
 * 
 * @param from Название начальной остановки
 * @param to Название конечной остановки
 * @return Расстояние в метрах или 0 если не найдено
 */
int TransportCatalogue::GetDistance(const std::string_view from, const std::string_view to) const {
	auto stop1 = FindStop(from);
	auto stop2 = FindStop(to);
	
	if(!stop1 || !stop2) {
		return 0;  // Одна из остановок не существует
	}

	// Ищем прямое направление (from → to)
	auto it = distances_.find(std::make_pair(stop1, stop2));
	if(it != distances_.end()) {
		return it->second;
	}

	// Ищем обратное направление (to → from)
	it = distances_.find(std::make_pair(stop2, stop1));
	if(it != distances_.end()) {
		return it->second;
	}

	return 0;  // Расстояние не задано
}

/** Возвращает копию всех маршрутов в системе */
const std::deque<transport::Bus> TransportCatalogue::GetAllBuses() const {
	return buses_;
}
} 