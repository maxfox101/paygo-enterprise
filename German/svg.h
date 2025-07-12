#pragma once

#include <cstdint>
#include <iostream>
#include <memory>
#include <string>
#include <vector>
#include <unordered_map>
#include <variant>

namespace svg {
struct Rgb {
	uint16_t red = 0;
	uint16_t green = 0;
	uint16_t blue = 0;

	Rgb() = default;
	Rgb(uint16_t r, uint16_t g, uint16_t b) : red(r), green(g), blue(b) {}
};

struct Rgba {
	uint16_t red = 0;
	uint16_t green = 0;
	uint16_t blue = 0;
	double opacity = 1.0;

	Rgba() = default;
	Rgba(uint16_t r, uint16_t g, uint16_t b, double o) : red(r), green(g), blue(b), opacity(o) {}
};

using Color = std::variant<std::monostate, std::string, Rgb, Rgba>;
inline const Color NoneColor{};

struct Point {
	Point() = default;
	Point(double x, double y) : x(x), y(y) {}

	double x = 0;
	double y = 0;
};
enum class StrokeLineCap {
	BUTT,
	ROUND,
	SQUARE,
};

enum class StrokeLineJoin {
	ARCS,
	BEVEL,
	MITER,
	MITER_CLIP,
	ROUND,
};

struct ColorPrinter {
	std::ostream& out;
	void operator()(std::monostate) const { out << "none"; }
	void operator()(const std::string& color) const { out << color; }
	void operator()(const Rgb& rgb) const { 
		out << "rgb(" << static_cast<int>(rgb.red) << "," 
							<< static_cast<int>(rgb.green) << "," 
							<< static_cast<int>(rgb.blue) << ")";
	}

	void operator()(const Rgba& rgba) const { 
		out << "rgba(" << static_cast<int>(rgba.red) << "," 
							<< static_cast<int>(rgba.green) << "," 
							<< static_cast<int>(rgba.blue) << "," 
							<< rgba.opacity << ")";
	}
};

/*
 * Вспомогательная структура, хранящая контекст для вывода SVG-документа с отступами.
 * Хранит ссылку на поток вывода, текущее значение и шаг отступа при выводе элемента
 */
struct RenderContext {
	RenderContext(std::ostream& out) : out(out) {}

	RenderContext(std::ostream& out, int indent_step, int indent = 0)
					: out(out), indent_step(indent_step), indent(indent) {}

	RenderContext Indented() const {
		return {out, indent_step, indent + indent_step};
	}

	void RenderIndent() const {
		for (int i = 0; i < indent; ++i) {
			out.put(' ');
		}
	}

	std::ostream& out;
	int indent_step = 0;
	int indent = 0;
};

/*
 * Абстрактный базовый класс Object служит для унифицированного хранения
 * конкретных тегов SVG-документа
 * Реализует паттерн "Шаблонный метод" для вывода содержимого тега
 */
 template <typename Owner>
class PathProps {
public:
	Owner& SetFillColor(Color color);
	Owner& SetStrokeColor(Color color);
	Owner& SetStrokeWidth(double width);
	Owner& SetStrokeLineCap(StrokeLineCap line_cap);
	Owner& SetStrokeLineJoin(StrokeLineJoin line_join);
protected:
	Color fill_color_ = NoneColor;
	Color stroke_color_ = NoneColor;
	double stroke_width_ = 1.0;
	StrokeLineCap stroke_line_cap_ = StrokeLineCap::BUTT;
	StrokeLineJoin stroke_line_join_ = StrokeLineJoin::MITER;
};

class Object {
public:
	virtual void Render(const RenderContext& context) const;

	virtual ~Object() = default;

protected:  
	virtual void RenderObject(const RenderContext& context) const = 0;
};

/*
 * Класс Circle моделирует элемент <circle> для отображения круга
 * https://developer.mozilla.org/en-US/docs/Web/SVG/Element/circle
 */
class Circle final : public Object, public PathProps<Circle> {
public:
	Circle& SetCenter(Point center);
	Circle& SetRadius(double radius);

private:
	void RenderObject(const RenderContext& context) const override;
 
	Point center_;
	double radius_ = 1.0;
};

/*
 * Класс Polyline моделирует элемент <polyline> для отображения ломаных линий
 * https://developer.mozilla.org/en-US/docs/Web/SVG/Element/polyline
 */
class Polyline final : public Object, public PathProps<Polyline> {
public:
	// Добавляет очередную вершину к ломаной линии
	Polyline& AddPoint(Point point);

	/*
	* Прочие методы и данные, необходимые для реализации элемента <polyline>
	*/
private: 
	void RenderObject(const RenderContext& context) const override;

	std::vector<Point> points_;
};

/*
 * Класс Text моделирует элемент <text> для отображения текста
 * https://developer.mozilla.org/en-US/docs/Web/SVG/Element/text
 */
class Text final : public Object, public PathProps<Text> {
public:
	Text& SetPosition(Point pos);
	Text& SetOffset(Point offset);
	Text& SetFontSize(uint32_t size);
	Text& SetFontFamily(std::string font_family);
	Text& SetFontWeight(std::string font_weight);
	Text& SetData(std::string data);

private:
	void RenderObject(const RenderContext& context) const override;

	Point position_;
	Point offset_;
	uint32_t font_size_ = 1;
	std::string font_family_;
	std::string font_weight_;
	std::string data_;
};

class ObjectContainer{
public:
	virtual void AddPtr(std::unique_ptr<Object>&& obj) = 0;

	template <typename Obj>
	void Add(Obj obj);

	virtual ~ObjectContainer() = default;
};

class Document final : public ObjectContainer {
public:
	template <typename Obj>
	void Add(Obj obj);

	void AddPtr(std::unique_ptr<Object>&& obj);
	void Render(std::ostream& out) const;

private:
	std::vector<std::unique_ptr<Object>> objects_;
};

class Drawable {
public:
	virtual void Draw(ObjectContainer& container) const = 0;
	virtual ~Drawable() = default;
};

template <typename Obj>
void Document::Add(Obj obj) {
	objects_.emplace_back(std::make_unique<Obj>(std::move(obj)));
}

template <typename Obj>
void ObjectContainer::Add(Obj obj) {
	AddPtr(std::make_unique<Obj>(std::move(obj)));
}

template <typename Owner>
Owner& PathProps<Owner>::SetFillColor(Color color) {
	if (std::holds_alternative<std::monostate>(color)) {
		// Если явно задали NoneColor, то сохраняем строку "none"
		fill_color_ = std::string("none");
	} else {
		fill_color_ = std::move(color);
	}

	return static_cast<Owner&>(*this);
}

template <typename Owner>
Owner& PathProps<Owner>::SetStrokeColor(Color color) {
	stroke_color_ = std::move(color);
	return static_cast<Owner&>(*this);
}

template <typename Owner>
Owner& PathProps<Owner>::SetStrokeWidth(double width) {
	stroke_width_ = width;
	return static_cast<Owner&>(*this);
}

template <typename Owner>
Owner& PathProps<Owner>::SetStrokeLineCap(StrokeLineCap line_cap) {
	stroke_line_cap_ = line_cap;
	return static_cast<Owner&>(*this);
}

template <typename Owner>
Owner& PathProps<Owner>::SetStrokeLineJoin(StrokeLineJoin line_join) {
	stroke_line_join_ = line_join;
	return static_cast<Owner&>(*this);
}

inline bool operator==(const Rgb& lhs, const Rgb& rhs) noexcept {
	return lhs.red == rhs.red &&
			lhs.green == rhs.green &&
			lhs.blue == rhs.blue;
}

inline bool operator==(const Rgba& lhs, const Rgba& rhs) noexcept {
	return lhs.red == rhs.red &&
			lhs.green == rhs.green &&
			lhs.blue == rhs.blue &&
			lhs.opacity == rhs.opacity;
}

inline std::ostream& operator<<(std::ostream& out, const Color& color) {
	std::visit(ColorPrinter{out}, color);
	return out;
}

inline std::ostream& operator <<(std::ostream& out, StrokeLineCap str){
	std::unordered_map<StrokeLineCap, std::string> to_lower_case = {
		{StrokeLineCap::BUTT, "butt"},
		{StrokeLineCap::ROUND, "round"},
		{StrokeLineCap::SQUARE, "square"}
	};

	return out << to_lower_case.at(str);
}

inline std::ostream& operator <<(std::ostream& out, StrokeLineJoin str){
	std::unordered_map<StrokeLineJoin, std::string> to_lower_case = {
		{StrokeLineJoin::ARCS, "arcs"},
		{StrokeLineJoin::BEVEL, "bevel"},
		{StrokeLineJoin::MITER, "miter"},
		{StrokeLineJoin::MITER_CLIP, "miter-clip"},
		{StrokeLineJoin::ROUND, "round"},
	};

	return out << to_lower_case.at(str);
} 
  
} 