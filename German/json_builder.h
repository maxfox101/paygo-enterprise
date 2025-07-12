#pragma once

#include "json.h"

namespace json {
class Builder {
private:
	class BaseContext;
	class DictValueContext;
	class DictItemContext;
	class ArrayItemContext;
public:
	Builder();
	json::Node Build();
	DictValueContext Key(std::string key);
	BaseContext Value(Node::Value value);
	DictItemContext StartDict();
	BaseContext EndDict();
	ArrayItemContext StartArray();
	BaseContext EndArray();

private:
	json::Node root_;
	std::vector<json::Node*> nodes_stack_;

	Node::Value& GetCurValue();
	const Node::Value& GetCurValue() const;

	void AddObject(Node::Value value, bool is_once);

	class BaseContext {
	public:
		explicit BaseContext(Builder &builder) : builder_(builder) {}

		Node Build() { return builder_.Build(); }

		DictValueContext Key(std::string key) { 
			return builder_.Key(std::move(key)); 
		}

		BaseContext Value(Node::Value value) { 
			return builder_.Value(std::move(value)); 
		}

		DictItemContext StartDict() { 
			return builder_.StartDict(); 
		}

		ArrayItemContext StartArray() { 
			return builder_.StartArray(); 
		}

		BaseContext EndDict() { 
			return builder_.EndDict(); 
		}

		BaseContext EndArray() { 
			return builder_.EndArray(); 
		}

	protected:
		Builder& builder_;
	};

	class DictItemContext : public BaseContext {
	public:
		DictItemContext(Builder &builder) : BaseContext(builder) {}
		explicit DictItemContext(BaseContext context) : BaseContext(context) {}
		
		// Запрещенные операции для контекста словаря
		Node Build() = delete;
		BaseContext Value(Node::Value value) = delete;
		DictItemContext StartDict() = delete;
		ArrayItemContext StartArray() = delete;
		BaseContext EndArray() = delete;
	};

	class DictValueContext : public BaseContext {
	public:
		DictValueContext(Builder &builder) : BaseContext(builder) {}
		explicit DictValueContext(BaseContext context) : BaseContext(context) {}
		
		DictItemContext Value(Node::Value value) {
			return DictItemContext(BaseContext::Value(std::move(value)));
		}
		
		// Запрещенные операции для значения словаря
		Node Build() = delete;
		BaseContext EndDict() = delete;
		BaseContext EndArray() = delete;
		DictValueContext Key(std::string key) = delete;
	};

	class ArrayItemContext : public BaseContext {
	public:
		ArrayItemContext(Builder &builder) : BaseContext(builder) {}
		explicit ArrayItemContext(BaseContext context) : BaseContext(context) {}
		
		ArrayItemContext Value(Node::Value value) {
			return ArrayItemContext(BaseContext::Value(std::move(value)));
		}
		
		// Запрещенные операции для элемента массива
		Node Build() = delete;
		DictValueContext Key(std::string key) = delete;
		BaseContext EndDict() = delete;
	};
};
} 