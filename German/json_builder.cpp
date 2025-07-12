#include "json_builder.h"

namespace json {

// Конструктор - инициализируем корневой узел и стек
Builder::Builder() : root_(), nodes_stack_{&root_} {
}

// Построение финального JSON объекта
json::Node Builder::Build() {
	if (!nodes_stack_.empty()) {
		throw std::logic_error("Cannot build JSON - object is not finished");
	}
	return std::move(root_);
}

// Начинаем создание словаря
Builder::DictItemContext Builder::StartDict() {
	AddObject(json::Dict{}, false);
	return DictItemContext(*this);
}

// Завершаем создание словаря
Builder::BaseContext Builder::EndDict() {
	if (!std::holds_alternative<json::Dict>(GetCurValue())) {
		throw std::logic_error("Cannot end dict - current value is not a dictionary");
	}
	nodes_stack_.pop_back();
	return BaseContext(*this);
}

// Начинаем создание массива
Builder::ArrayItemContext Builder::StartArray() {
	AddObject(json::Array{}, false);
	return ArrayItemContext(*this);
}

// Завершаем создание массива
Builder::BaseContext Builder::EndArray() {
	if (!std::holds_alternative<json::Array>(GetCurValue())) {
		throw std::logic_error("Cannot end array - current value is not an array");
	}
	nodes_stack_.pop_back();
	return BaseContext(*this);
}

// Устанавливаем ключ для словаря
Builder::DictValueContext Builder::Key(std::string key) {
	Node::Value &current_value = GetCurValue();

	if (!std::holds_alternative<json::Dict>(current_value)) {
		throw std::logic_error("Cannot use Key() - current object is not a dictionary");
	}

	nodes_stack_.push_back(&std::get<json::Dict>(current_value)[std::move(key)]);
	return DictValueContext(*this);
}

Builder::BaseContext Builder::Value(Node::Value value) {
	AddObject(std::move(value), true);
	return BaseContext(*this);
}

// Получаем текущее значение из стека
Node::Value& Builder::GetCurValue() {
	if (nodes_stack_.empty()) {
		throw std::logic_error("Cannot modify - JSON object is already finished");
	}
	return nodes_stack_.back()->GetValue();
}

// Константная версия получения текущего значения
const Node::Value& Builder::GetCurValue() const {
	if (nodes_stack_.empty()) {
		throw std::logic_error("Cannot access - JSON object is already finished");
	}
	return const_cast<const Node::Value&>(nodes_stack_.back()->GetValue());
}

// Добавляем объект в текущий контекст (массив или корень)
void Builder::AddObject(Node::Value value, bool is_single_value) {
	Node::Value &current_value = GetCurValue();
	
	if (std::holds_alternative<Array>(current_value)) {
		// Добавляем в массив
		json::Node &new_node = std::get<Array>(current_value).emplace_back(std::move(value));
		
		if (!is_single_value) {
			nodes_stack_.push_back(&new_node);
		}
	} else {
		// Добавляем как корневой элемент или значение ключа
		if (!std::holds_alternative<std::nullptr_t>(GetCurValue())) {
			throw std::logic_error("Cannot set value - current object is not empty");
		}
		
		current_value = std::move(value);
		if (is_single_value) {
			nodes_stack_.pop_back();
		}
	}
}
} 