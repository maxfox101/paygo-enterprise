#pragma once

/*
 * JSON ПАРСЕР ДЛЯ ТРАНСПОРТНОГО КАТАЛОГА
 * 
 * Полнофункциональный JSON парсер, поддерживающий все типы JSON значений:
 * - null, bool, int, double, string
 * - array (массивы)
 * - object (словари/объекты)
 * 
 * АРХИТЕКТУРА:
 * - Node: универсальный узел, хранящий любое JSON значение через std::variant
 * - Document: контейнер для корневого узла JSON документа
 * - ParsingError: исключение для ошибок парсинга
 * 
 * ПРИНЦИПЫ РАБОТЫ:
 * 1. Использует std::variant для type-safe хранения разных типов данных
 * 2. Поддерживает удобные методы проверки типов (IsInt, IsString, etc.)
 * 3. Предоставляет безопасные методы извлечения значений (AsInt, AsString, etc.)
 * 4. Автоматически обрабатывает вложенные структуры (массивы и объекты)
 */

#include <iostream>
#include <map>
#include <string>
#include <variant>
#include <vector>

namespace json {

// Предварительное объявление для взаимных ссылок
class Node;

/**
 * ПСЕВДОНИМЫ ТИПОВ JSON
 * 
 * Dict - представляет JSON объект как map<string, Node>
 * Array - представляет JSON массив как vector<Node>
 * 
 * Эти псевдонимы упрощают код и делают типы более понятными
 */
using Dict = std::map<std::string, Node>;   // JSON объект: {"key": value, ...}
using Array = std::vector<Node>;            // JSON массив: [value1, value2, ...]

/**
 * ИСКЛЮЧЕНИЕ ДЛЯ ОШИБОК ПАРСИНГА JSON
 * 
 * Выбрасывается при обнаружении синтаксических ошибок в JSON тексте:
 * - Неожиданные символы
 * - Незакрытые скобки/кавычки
 * - Некорректные числа
 * - Нарушение структуры JSON
 */
class ParsingError : public std::runtime_error {
public:
	using runtime_error::runtime_error;
};

/**
 * УНИВЕРСАЛЬНЫЙ УЗЕЛ JSON ДЕРЕВА
 * 
 * Класс Node представляет любое значение в JSON документе.
 * Использует std::variant для type-safe хранения различных типов данных.
 * 
 * ПОДДЕРЖИВАЕМЫЕ ТИПЫ:
 * - std::nullptr_t: JSON null
 * - Array: JSON массивы [...]
 * - Dict: JSON объекты {...}
 * - bool: JSON boolean (true/false)  
 * - int: JSON целые числа
 * - double: JSON вещественные числа
 * - std::string: JSON строки
 * 
 * ПРИНЦИПЫ ДИЗАЙНА:
 * - Наследование от std::variant в приватном режиме (скрывает детали реализации)
 * - Предоставляет удобный интерфейс через методы Is/As
 * - Автоматическое приведение int к double при необходимости
 * - Безопасные методы извлечения с проверкой типов
 */
class Node final : private std::variant<std::nullptr_t, Array, Dict, bool, int, double, std::string> {
public:
	// Наследуем конструкторы от std::variant
	using variant::variant;
	using Value = variant;

	// Явные конструкторы для инициализации из Value
	explicit Node(Value &&value) : Value(std::move(value)) {}
	explicit Node(const Value &value) : Value(value) {}

	// === МЕТОДЫ ДЛЯ РАБОТЫ С ЦЕЛЫМИ ЧИСЛАМИ ===
	
	/**
	 * Проверяет, содержит ли узел целое число
	 * @return true если узел содержит int
	 */
	bool IsInt() const {
		return std::holds_alternative<int>(*this);
	}
	
	/**
	 * Извлекает целое число из узла
	 * @return Значение типа int
	 * @throws std::logic_error если узел не содержит int
	 */
	int AsInt() const {
		using namespace std::literals;
		if (!IsInt()) {
			throw std::logic_error("Not an int"s);
		}
		return std::get<int>(*this);
	}

	// === МЕТОДЫ ДЛЯ РАБОТЫ С ВЕЩЕСТВЕННЫМИ ЧИСЛАМИ ===
	
	/**
	 * Проверяет, содержит ли узел именно double (не int)
	 * @return true если узел содержит именно double
	 */
	bool IsPureDouble() const {
		return std::holds_alternative<double>(*this);
	}
	
	/**
	 * Проверяет, можно ли интерпретировать узел как double
	 * Включает как int, так и double значения
	 * @return true если узел содержит int или double
	 */
	bool IsDouble() const {
		return IsInt() || IsPureDouble();
	}
	
	/**
	 * Извлекает число как double из узла
	 * Автоматически приводит int к double при необходимости
	 * @return Значение типа double
	 * @throws std::logic_error если узел не содержит число
	 */
	double AsDouble() const {
		using namespace std::literals;
		if (!IsDouble()) {
			throw std::logic_error("Not a double"s);
		}
		return IsPureDouble() ? std::get<double>(*this) : AsInt();
	}

	// === МЕТОДЫ ДЛЯ РАБОТЫ С ЛОГИЧЕСКИМИ ЗНАЧЕНИЯМИ ===
	
	/** Проверяет, содержит ли узел булево значение */
	bool IsBool() const {
		return std::holds_alternative<bool>(*this);
	}
	
	/** Извлекает булево значение из узла */
	bool AsBool() const {
		using namespace std::literals;
		if (!IsBool()) {
			throw std::logic_error("Not a bool"s);
		}
		return std::get<bool>(*this);
	}

	// === МЕТОДЫ ДЛЯ РАБОТЫ С NULL ЗНАЧЕНИЯМИ ===
	
	/** Проверяет, содержит ли узел null значение */
	bool IsNull() const {
		return std::holds_alternative<std::nullptr_t>(*this);
	}

	// === МЕТОДЫ ДЛЯ РАБОТЫ С МАССИВАМИ ===
	
	/** Проверяет, содержит ли узел JSON массив */
	bool IsArray() const {
		return std::holds_alternative<Array>(*this);
	}
	
	/** Извлекает массив из узла */
	const Array& AsArray() const {
		using namespace std::literals;
		if (!IsArray()) {
			throw std::logic_error("Not an array"s);
		}
		return std::get<Array>(*this);
	}

	// === МЕТОДЫ ДЛЯ РАБОТЫ СО СТРОКАМИ ===
	
	/** Проверяет, содержит ли узел строку */
	bool IsString() const {
		return std::holds_alternative<std::string>(*this);
	}
	
	/** Извлекает строку из узла */
	const std::string& AsString() const {
		using namespace std::literals;
		if (!IsString()) {
			throw std::logic_error("Not a string"s);
		}
		return std::get<std::string>(*this);
	}

	// === МЕТОДЫ ДЛЯ РАБОТЫ СО СЛОВАРЯМИ (JSON ОБЪЕКТАМИ) ===
	
	/** Проверяет, содержит ли узел JSON объект (словарь) */
	bool IsDict() const {
		return std::holds_alternative<Dict>(*this);
	}
	
	/** Извлекает словарь из узла */
	const Dict& AsDict() const {
		using namespace std::literals;
		if (!IsDict()) {
			throw std::logic_error("Not a dict"s);
		}
		return std::get<Dict>(*this);
	}

	// === ОПЕРАТОРЫ СРАВНЕНИЯ ===
	
	/** Сравнивает два узла на равенство по содержимому */
	bool operator==(const Node& rhs) const {
		return GetValue() == rhs.GetValue();
	}

	// === ДОСТУП К ВНУТРЕННЕМУ ЗНАЧЕНИЮ ===
	
	/** Получает константную ссылку на внутреннее значение */
	const Value& GetValue() const {
		return *this;
	}

	/** Получает изменяемую ссылку на внутреннее значение */
	Value& GetValue() {
		return *this;
	}
};

/** Оператор неравенства для узлов */
inline bool operator!=(const Node& lhs, const Node& rhs) {
	return !(lhs == rhs);
}

/**
 * ДОКУМЕНТ JSON
 * 
 * Представляет целый JSON документ с корневым узлом.
 * Может содержать любое допустимое JSON значение в качестве корня:
 * - Объект: {"key": "value"}
 * - Массив: [1, 2, 3]
 * - Простое значение: "string", 42, true, null
 * 
 * ИСПОЛЬЗОВАНИЕ:
 * - Результат парсинга JSON текста
 * - Контейнер для построения JSON структур
 * - Единая точка доступа к содержимому документа
 */
class Document {
public:
	/** Конструктор документа с корневым узлом */
	explicit Document(Node root) : root_(std::move(root)) {}

	/** Получает корневой узел документа */
	const Node& GetRoot() const {
		return root_;
	}

private:
	Node root_;  // Корневой узел JSON дерева
};

/** Сравнение документов по содержимому корневых узлов */
inline bool operator==(const Document& lhs, const Document& rhs) {
	return lhs.GetRoot() == rhs.GetRoot();
}

/** Оператор неравенства для документов */
inline bool operator!=(const Document& lhs, const Document& rhs) {
	return !(lhs == rhs);
}

// === ФУНКЦИИ ДЛЯ РАБОТЫ С JSON ===

/**
 * ЗАГРУЗКА JSON ИЗ ПОТОКА
 * 
 * Парсит JSON текст из входного потока и возвращает Document.
 * Поддерживает все стандартные JSON конструкции.
 * 
 * @param input Поток с JSON текстом
 * @return Документ с распарсенными данными
 * @throws ParsingError при синтаксических ошибках
 */
Document Load(std::istream& input);

/**
 * ВЫВОД JSON В ПОТОК
 * 
 * Сериализует документ обратно в JSON текст.
 * Выводит компактный JSON без лишних пробелов.
 * 
 * @param doc Документ для вывода
 * @param output Поток для записи JSON
 */
void Print(const Document& doc, std::ostream& output);

}  // namespace json 