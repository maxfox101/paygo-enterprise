#include "json.h"

#include <iterator>

/*
 * РЕАЛИЗАЦИЯ JSON ПАРСЕРА
 * 
 * Файл содержит полную реализацию рекурсивного JSON парсера,
 * который обрабатывает все стандартные JSON конструкции:
 * 
 * АРХИТЕКТУРА ПАРСЕРА:
 * 1. Рекурсивный спуск (recursive descent parser)
 * 2. Каждый тип JSON значения обрабатывается отдельной функцией
 * 3. Функции вызывают друг друга для обработки вложенных структур
 * 4. Ошибки обрабатываются через исключения ParsingError
 * 
 * ОСНОВНЫЕ ФУНКЦИИ:
 * - LoadNode: главная функция, определяет тип и вызывает нужный обработчик
 * - LoadArray: парсит JSON массивы [...]
 * - LoadDict: парсит JSON объекты {...}
 * - LoadString: парсит строки с обработкой escape-последовательностей
 * - LoadNumber: парсит числа (int/double) с поддержкой экспоненты
 * - LoadBool/LoadNull: парсят литералы true/false/null
 * 
 * АЛГОРИТМ РАБОТЫ:
 * 1. Читаем первый символ для определения типа
 * 2. Вызываем соответствующую функцию обработки
 * 3. Рекурсивно обрабатываем вложенные элементы
 * 4. Возвращаем готовый Node с результатом
 */

namespace json {

namespace {  // Анонимное пространство имен для внутренних функций
using namespace std::literals;

// === ПРОТОТИПЫ ФУНКЦИЙ ПАРСИНГА ===
Node LoadNode(std::istream& input);      // Основная функция парсинга
Node LoadString(std::istream& input);    // Парсинг строк

/**
 * ПАРСИНГ ЛИТЕРАЛОВ (true, false, null)
 * 
 * Считывает последовательность букв из потока для обработки
 * JSON литералов: true, false, null
 * 
 * @param input Входной поток
 * @return Строка с прочитанным литералом
 */
std::string LoadLiteral(std::istream& input) {
	std::string s;
	// Читаем все буквы подряд (isalpha проверяет, является ли символ буквой)
	while (std::isalpha(input.peek())) {
		s.push_back(static_cast<char>(input.get()));
	}
	return s;
}

/**
 * ПАРСИНГ JSON МАССИВОВ
 * 
 * Обрабатывает JSON массивы вида: [element1, element2, ...]
 * Поддерживает вложенные структуры и пустые массивы.
 * 
 * АЛГОРИТМ:
 * 1. Читаем символы до закрывающей скобки ']'
 * 2. Игнорируем запятые между элементами
 * 3. Рекурсивно парсим каждый элемент через LoadNode
 * 4. Собираем результат в std::vector<Node>
 * 
 * @param input Входной поток (после открывающей '[')
 * @return Node содержащий массив
 * @throws ParsingError при синтаксических ошибках
 */
Node LoadArray(std::istream& input) {
	std::vector<Node> result;

	// Читаем элементы до закрывающей скобки
	for (char c; input >> c && c != ']';) {
		if (c != ',') {
			// Если это не запятая, возвращаем символ обратно в поток
			input.putback(c);
		}
		// Рекурсивно парсим элемент массива
		result.push_back(LoadNode(input));
	}
	
	// Проверяем, что поток не закончился преждевременно
	if (!input) {
		throw ParsingError("Array parsing error"s);
	}
	
	return Node(std::move(result));
}

/**
 * ПАРСИНГ JSON ОБЪЕКТОВ (СЛОВАРЕЙ)
 * 
 * Обрабатывает JSON объекты вида: {"key1": value1, "key2": value2, ...}
 * Поддерживает вложенные структуры и пустые объекты.
 * 
 * АЛГОРИТМ:
 * 1. Читаем пары ключ-значение до закрывающей скобки '}'
 * 2. Ключ должен быть строкой в кавычках
 * 3. После ключа ожидаем двоеточие ':'
 * 4. Рекурсивно парсим значение через LoadNode
 * 5. Проверяем уникальность ключей
 * 
 * @param input Входной поток (после открывающей '{')
 * @return Node содержащий словарь
 * @throws ParsingError при синтаксических ошибках или дублировании ключей
 */
Node LoadDict(std::istream& input) {
	Dict dict;

	// Читаем пары ключ-значение до закрывающей скобки
	for (char c; input >> c && c != '}';) {
		if (c == '"') {
			// Парсим ключ как строку
			std::string key = LoadString(input).AsString();
			
			// Ожидаем двоеточие после ключа
			if (input >> c && c == ':') {
				// Проверяем уникальность ключа
				if (dict.find(key) != dict.end()) {
					throw ParsingError("Duplicate key '"s + key + "' have been found");
				}
				// Парсим значение и добавляем в словарь
				dict.emplace(std::move(key), LoadNode(input));
			} else {
				throw ParsingError(": is expected but '"s + c + "' has been found"s);
			}
		} else if (c != ',') {
			// Между парами ключ-значение должны быть запятые
			throw ParsingError(R"(',' is expected but ')"s + c + "' has been found"s);
		}
	}
	
	// Проверяем, что поток не закончился преждевременно
	if (!input) {
		throw ParsingError("Dictionary parsing error"s);
	}
	
	return Node(std::move(dict));
}

Node LoadString(std::istream& input) {
	auto it = std::istreambuf_iterator<char>(input);
	auto end = std::istreambuf_iterator<char>();
	std::string s;
	while (true) {
		if (it == end) {
			throw ParsingError("String parsing error");
		}
		const char ch = *it;
		if (ch == '"') {
			++it;
			break;
		} else if (ch == '\\') {
			++it;
			if (it == end) {
                throw ParsingError("String parsing error");
			}
			const char escaped_char = *(it);
			switch (escaped_char) {
				case 'n':
					s.push_back('\n');
					break;
				case 't':
					s.push_back('\t');
					break;
				case 'r':
					s.push_back('\r');
					break;
				case '"':
					s.push_back('"');
					break;
				case '\\':
					s.push_back('\\');
					break;
				default:
					throw ParsingError("Unrecognized escape sequence \\"s + escaped_char);
			}
		} else if (ch == '\n' || ch == '\r') {
			throw ParsingError("Unexpected end of line"s);
		} else {
			s.push_back(ch);
		}
		++it;
	}

	return Node(std::move(s));
}

Node LoadBool(std::istream& input) {
	const auto s = LoadLiteral(input);
	if (s == "true"sv) {
		return Node{true};
	} else if (s == "false"sv) {
		return Node{false};
	} else {
		throw ParsingError("Failed to parse '"s + s + "' as bool"s);
	}
}

Node LoadNull(std::istream& input) {
	if (auto literal = LoadLiteral(input); literal == "null"sv) {
		return Node{nullptr};
	} else {
		throw ParsingError("Failed to parse '"s + literal + "' as null"s);
	}
}

Node LoadNumber(std::istream& input) {
	std::string parsed_num;

	// Считывает в parsed_num очередной символ из input
	auto read_char = [&parsed_num, &input] {
		parsed_num += static_cast<char>(input.get());
		if (!input) {
			throw ParsingError("Failed to read number from stream"s);
		}
	};

	// Считывает одну или более цифр в parsed_num из input
	auto read_digits = [&input, read_char] {
		if (!std::isdigit(input.peek())) {
			throw ParsingError("A digit is expected"s);
		}
		while (std::isdigit(input.peek())) {
			read_char();
		}
	};

	if (input.peek() == '-') {
		read_char();
	}
	// Парсим целую часть числа
	if (input.peek() == '0') {
		read_char();
		// После 0 в JSON не могут идти другие цифры
	} else {
		read_digits();
	}

	bool is_int = true;
	// Парсим дробную часть числа
	if (input.peek() == '.') {
		read_char();
		read_digits();
		is_int = false;
	}

	// Парсим экспоненциальную часть числа
	if (int ch = input.peek(); ch == 'e' || ch == 'E') {
		read_char();
		if (ch = input.peek(); ch == '+' || ch == '-') {
			read_char();
		}
		read_digits();
		is_int = false;
	}

	try {
		if (is_int) {
			// Сначала пробуем преобразовать строку в int
			try {
				return std::stoi(parsed_num);
			} catch (...) {
				// В случае неудачи, например, при переполнении
				// код ниже попробует преобразовать строку в double
			}
		}
		return std::stod(parsed_num);
	} catch (...) {
		throw ParsingError("Failed to convert "s + parsed_num + " to number"s);
	}
}

/**
 * ГЛАВНАЯ ФУНКЦИЯ ПАРСИНГА JSON УЗЛОВ
 * 
 * Центральная функция парсера, которая определяет тип JSON значения
 * по первому символу и вызывает соответствующую функцию обработки.
 * 
 * ЛОГИКА ОПРЕДЕЛЕНИЯ ТИПА:
 * - '[' → массив (LoadArray)
 * - '{' → объект (LoadDict)  
 * - '"' → строка (LoadString)
 * - 't' или 'f' → булево значение (LoadBool)
 * - 'n' → null (LoadNull)
 * - цифра или '-' → число (LoadNumber)
 * 
 * @param input Входной поток с JSON данными
 * @return Node с распарсенным значением
 * @throws ParsingError при неожиданном конце файла или неизвестном символе
 */
Node LoadNode(std::istream& input) {
	char c;
	// Читаем первый значащий символ (пропускаем пробелы)
	if (!(input >> c)) {
		throw ParsingError("Unexpected EOF"s);
	}
	
	// Определяем тип значения и вызываем соответствующий парсер
	switch (c) {
		case '[':
			return LoadArray(input);
		case '{':
			return LoadDict(input);
		case '"':
			return LoadString(input);
		case 't':
			// Атрибут [[fallthrough]] явно указывает, что провал в следующий case
			// сделан намеренно. Для букв 't' и 'f' логика обработки одинакова:
			// возвращаем символ в поток и парсим булево значение
			[[fallthrough]];
		case 'f':
			input.putback(c);  // Возвращаем символ для LoadBool
			return LoadBool(input);
		case 'n':
			input.putback(c);  // Возвращаем символ для LoadNull
			return LoadNull(input);
		default:
			// Все остальные символы (цифры, знак минус) считаем началом числа
			input.putback(c);  // Возвращаем символ для LoadNumber
			return LoadNumber(input);
	}
}

/**
 * КОНТЕКСТ ДЛЯ КРАСИВОГО ВЫВОДА JSON
 * 
 * Структура хранит информацию о форматировании при выводе JSON:
 * - Поток для записи
 * - Размер отступа на каждый уровень вложенности  
 * - Текущий уровень отступа
 * 
 * ПРИНЦИП РАБОТЫ:
 * - Каждый уровень вложенности (массивы, объекты) увеличивает отступ
 * - PrintIndent() выводит нужное количество пробелов
 * - Indented() создает новый контекст с увеличенным отступом
 */
struct PrintContext {
	std::ostream& out;        // Поток для записи JSON
	int indent_step = 4;      // Размер отступа (количество пробелов на уровень)
	int indent = 0;           // Текущий отступ

	/**
	 * Выводит отступ для текущего уровня вложенности
	 */
	void PrintIndent() const {
		for (int i = 0; i < indent; ++i) {
			out.put(' ');
		}
	}

	/**
	 * Создает новый контекст с увеличенным отступом
	 * Используется при входе в массив или объект
	 */
	PrintContext Indented() const {
		return {out, indent_step, indent_step + indent};
	}
};

void PrintNode(const Node& value, const PrintContext& ctx);

template <typename Value>
void PrintValue(const Value& value, const PrintContext& ctx) {
	ctx.out << value;
}

void PrintString(const std::string& value, std::ostream& out) {
	out.put('"');
	for (const char c : value) {
		switch (c) {
			case '\r':
				out << "\\r"sv;
				break;
			case '\n':
				out << "\\n"sv;
				break;
			case '\t':
				out << "\\t"sv;
				break;
			case '"':
				// Символы " и \ выводятся как \" или \\, соответственно
				[[fallthrough]];
			case '\\':
				out.put('\\');
				[[fallthrough]];
			default:
				out.put(c);
				break;
		}
	}
	out.put('"');
}

template <>
void PrintValue<std::string>(const std::string& value, const PrintContext& ctx) {
	PrintString(value, ctx.out);
}

template <>
void PrintValue<std::nullptr_t>(const std::nullptr_t&, const PrintContext& ctx) {
	ctx.out << "null"sv;
}

// В специализации шаблона PrintValue для типа bool параметр value передаётся
// по константной ссылке, как и в основном шаблоне.
// В качестве альтернативы можно использовать перегрузку:
// void PrintValue(bool value, const PrintContext& ctx);
template <>
void PrintValue<bool>(const bool& value, const PrintContext& ctx) {
	ctx.out << (value ? "true"sv : "false"sv);
}

template <>
void PrintValue<Array>(const Array& nodes, const PrintContext& ctx) {
	std::ostream& out = ctx.out;
	out << "[\n"sv;
	bool first = true;
	auto inner_ctx = ctx.Indented();
	for (const Node& node : nodes) {
		if (first) {
			first = false;
		} else {
			out << ",\n"sv;
		}
		inner_ctx.PrintIndent();
		PrintNode(node, inner_ctx);
	}
	out.put('\n');
	ctx.PrintIndent();
	out.put(']');
}

template <>
void PrintValue<Dict>(const Dict& nodes, const PrintContext& ctx) {
	std::ostream& out = ctx.out;
	out << "{\n"sv;
	bool first = true;
	auto inner_ctx = ctx.Indented();
	for (const auto& [key, node] : nodes) {
		if (first) {
			first = false;
		} else {
			out << ",\n"sv;
		}
		inner_ctx.PrintIndent();
		PrintString(key, ctx.out);
		out << ": "sv;
		PrintNode(node, inner_ctx);
	}
	out.put('\n');
	ctx.PrintIndent();
	out.put('}');
}

void PrintNode(const Node& node, const PrintContext& ctx) {
	std::visit(
		[&ctx](const auto& value) {
			PrintValue(value, ctx);
		},
		node.GetValue());
}

}  // namespace (конец анонимного пространства имен)

// === ПУБЛИЧНЫЕ ФУНКЦИИ JSON МОДУЛЯ ===

/**
 * ЗАГРУЗКА JSON ДОКУМЕНТА ИЗ ПОТОКА
 * 
 * Основная точка входа для парсинга JSON. Читает JSON текст из потока
 * и возвращает готовый Document с деревом объектов.
 * 
 * ПРОЦЕСС РАБОТЫ:
 * 1. Вызывает LoadNode для парсинга корневого элемента
 * 2. LoadNode рекурсивно обрабатывает всю структуру
 * 3. Создает и возвращает Document с результатом
 * 
 * @param input Поток с JSON текстом (например, std::cin или std::ifstream)
 * @return Document с распарсенной JSON структурой
 * @throws ParsingError если JSON содержит синтаксические ошибки
 */
Document Load(std::istream& input) {
	return Document{LoadNode(input)};
}

/**
 * ВЫВОД JSON ДОКУМЕНТА В ПОТОК
 * 
 * Сериализует JSON документ обратно в текстовый формат с красивым
 * форматированием (отступы, переносы строк).
 * 
 * ОСОБЕННОСТИ ВЫВОДА:
 * - Массивы и объекты выводятся с отступами
 * - Каждый элемент на отдельной строке
 * - Escape-последовательности в строках
 * - Компактный вывод чисел и булевых значений
 * 
 * @param doc JSON документ для вывода
 * @param output Поток для записи (например, std::cout или std::ofstream)
 */
void Print(const Document& doc, std::ostream& output) {
	PrintNode(doc.GetRoot(), PrintContext{output});
}

}  // namespace json 