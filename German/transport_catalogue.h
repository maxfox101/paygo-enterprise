#pragma once

/*
 * ТРАНСПОРТНЫЙ КАТАЛОГ - ОСНОВНАЯ ЛОГИКА СИСТЕМЫ
 * 
 * Этот модуль содержит центральную логику транспортного каталога:
 * - Хранение информации об остановках и маршрутах
 * - Вычисление характеристик маршрутов (длина, количество остановок)
 * - Работа с расстояниями между остановками
 * - Поиск и получение информации
 * 
 * АРХИТЕКТУРНЫЕ РЕШЕНИЯ:
 * 1. Использование std::deque для стабильности указателей
 * 2. Индексация через unordered_map для быстрого поиска O(1)
 * 3. Хранение указателей для избежания копирования данных
 * 4. Специальный хешер для пар указателей на остановки
 */

#include "domain.h"

#include <utility>
#include <string_view>
#include <deque>
#include <unordered_set>
#include <unordered_map>

namespace catalogue {

namespace detail {  // Вспомогательные структуры
	
	/**
	 * ИНФОРМАЦИЯ О МАРШРУТЕ
	 * 
	 * Структура содержит вычисленные характеристики автобусного маршрута:
	 * - stops: общее количество остановок (с учетом повторений)
	 * - unique_stops: количество уникальных остановок
	 * - length: длина маршрута в метрах (по дорогам)
	 * - curvature: коэффициент извилистости (отношение длины по дорогам к длине по прямой)
	 */
	struct BusInfo {
		int stops;          // Общее количество остановок на маршруте
		int unique_stops;   // Количество уникальных остановок
		int length;         // Длина маршрута в метрах (реальная дорога)
		double curvature;   // Коэффициент извилистости маршрута
	};

	/**
	 * ХЕШЕР ДЛЯ ПАР УКАЗАТЕЛЕЙ НА ОСТАНОВКИ
	 * 
	 * Специальный хешер для использования пар указателей на остановки
	 * в качестве ключей в unordered_map для хранения расстояний.
	 * 
	 * ПРИНЦИП РАБОТЫ:
	 * - Вычисляет хеш для каждого указателя
	 * - Комбинирует хеши с помощью простой формулы (hash1 + hash2 * 37)
	 * - Число 37 выбрано как простое число для лучшего распределения
	 */
	struct PairStopHasher {
		size_t operator()(const std::pair<const transport::Stop*, const transport::Stop*> &pair) const {
			auto hash1 = std::hash<const void*>{}(pair.first);
			auto hash2 = std::hash<const void*>{}(pair.second);
			return hash1 + hash2 * 37;  // Простая формула комбинирования хешей
		}
	};
}

/**
 * ГЛАВНЫЙ КЛАСС ТРАНСПОРТНОГО КАТАЛОГА
 * 
 * Центральное хранилище всей информации о транспортной системе.
 * Предоставляет API для добавления, поиска и получения информации
 * об остановках и маршрутах.
 * 
 * ОСНОВНЫЕ ВОЗМОЖНОСТИ:
 * - Добавление остановок и маршрутов
 * - Быстрый поиск по названию (O(1) благодаря индексам)
 * - Вычисление характеристик маршрутов  
 * - Работа с расстояниями между остановками
 * - Получение списка маршрутов для остановки
 * 
 * ОСОБЕННОСТИ РЕАЛИЗАЦИИ:
 * - std::deque обеспечивает стабильность указателей при росте контейнера
 * - Двойная индексация: основное хранилище + быстрый поиск
 * - Использование string_view для эффективности
 */
class TransportCatalogue {
public:
	/** Конструктор по умолчанию */
	TransportCatalogue() = default;
	
	// === МЕТОДЫ ДОБАВЛЕНИЯ ДАННЫХ ===
	
	/** Добавляет остановку в каталог */
	void AddStop(const std::string_view name, geo::Coordinates coord);
	
	/** Добавляет маршрут в каталог (версия с копированием списка остановок) */
	void AddBus(const std::string_view name, const std::vector<const transport::Stop*> &stops_list, bool is_rountrip);
	
	/** Добавляет маршрут в каталог (версия с перемещением списка остановок) */
	void AddBus(const std::string_view name, std::vector<const transport::Stop*> &&stops_list, bool is_rountrip);
	
	// === МЕТОДЫ ПОИСКА ===
	
	/** Ищет остановку по названию */
	const transport::Stop* FindStop(std::string_view str) const;
	
	/** Ищет маршрут по номеру */
	const transport::Bus* FindBus(std::string_view num) const;
	
	// === МЕТОДЫ ПОЛУЧЕНИЯ ИНФОРМАЦИИ ===
	
	/** Вычисляет полную информацию о маршруте (длина, количество остановок, etc.) */
	detail::BusInfo GetBusInfo(const transport::Bus &bus) const;
	
	/** Возвращает список маршрутов, проходящих через остановку */
	std::vector<std::string_view> GetStopInfo(const transport::Stop &stop) const;
	
	/** Возвращает список всех маршрутов */
	const std::deque<transport::Bus> GetAllBuses() const;
	
	// === МЕТОДЫ РАБОТЫ С РАССТОЯНИЯМИ ===
	
	/** Устанавливает расстояние между остановками */
	void SetDistance(const std::string_view from, const std::string_view to, int distance);
	
	/** Получает расстояние между остановками */
	int GetDistance(const std::string_view from, const std::string_view to) const;

private:
	// === ХРАНИЛИЩА ОСНОВНЫХ ДАННЫХ ===
	
	/**
	 * Основное хранилище остановок
	 * std::deque гарантирует, что указатели на элементы остаются валидными
	 * при добавлении новых элементов (в отличие от std::vector)
	 */
	std::deque<transport::Stop> stops_;
	
	/**
	 * Индекс для быстрого поиска остановок по названию
	 * Ключ: string_view с именем остановки (ссылается на stops_)
	 * Значение: указатель на остановку в stops_
	 */
	std::unordered_map<std::string_view, const transport::Stop *> stops_ptr_;

	/**
	 * Основное хранилище маршрутов
	 * std::deque для стабильности указателей
	 */
	std::deque<transport::Bus> buses_;
	
	/**
	 * Индекс для быстрого поиска маршрутов по номеру
	 * Ключ: string_view с номером маршрута
	 * Значение: указатель на маршрут в buses_
	 */
	std::unordered_map<std::string_view, const transport::Bus *> buses_ptr_;

	// === ВСПОМОГАТЕЛЬНЫЕ ИНДЕКСЫ ===
	
	/**
	 * Обратный индекс: остановка → маршруты
	 * Позволяет быстро найти все маршруты, проходящие через остановку
	 * Ключ: название остановки
	 * Значение: набор номеров маршрутов
	 */
	std::unordered_map<std::string_view, std::unordered_set<std::string_view>> stop_buses_;
	
	/**
	 * Кэш расстояний между парами остановок
	 * Хранит реальные расстояния по дорогам (не прямые расстояния)
	 * Ключ: пара указателей на остановки (от, до)
	 * Значение: расстояние в метрах
	 */
	std::unordered_map<std::pair<const transport::Stop *, const transport::Stop *>, int, detail::PairStopHasher> distances_;
};
} 