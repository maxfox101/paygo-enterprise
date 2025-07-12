#include "svg.h"

namespace svg {

using namespace std::literals;

void Object::Render(const RenderContext& context) const {
	context.RenderIndent();

	RenderObject(context);

	context.out << std::endl;
}


Polyline& Polyline::AddPoint(Point point){
	points_.push_back(point);
	return *this;
}


void Polyline::RenderObject(const RenderContext& context) const {
	auto& out = context.out;
	out << "<polyline points=\"";

	bool first = true;
	for (const Point& p : points_) {
		if (!first) {
			out << " ";
		}

		out << p.x << "," << p.y;
		first = false;
	}
	out << "\""; 

    
	if (!std::holds_alternative<std::monostate>(fill_color_))  {
		out << " fill=\"";
		std::visit(ColorPrinter{out}, fill_color_);
		out << "\"";
	}

	if (!std::holds_alternative<std::monostate>(stroke_color_)) {
		out << " stroke=\"";
		std::visit(ColorPrinter{out}, stroke_color_);
		out << "\"";
	}

	if (stroke_width_ != 1.0) {
		out << " stroke-width=\"" << stroke_width_ << "\"";
	}

	if (stroke_line_cap_ != StrokeLineCap::BUTT) {
		out << " stroke-linecap=\"" << stroke_line_cap_ << "\"";
	}

	if (stroke_line_join_ != StrokeLineJoin::MITER) {
		out << " stroke-linejoin=\"" << stroke_line_join_ << "\"";
	}

	out << "/>";
}

Circle& Circle::SetCenter(Point center)  {
	center_ = center;
	return *this;
}

Circle& Circle::SetRadius(double radius)  {
	radius_ = radius;
	return *this;
}

void Circle::RenderObject(const RenderContext& context) const {
	auto& out = context.out;
  
	out << "<circle cx=\"" << center_.x 
		<< "\" cy=\"" << center_.y 
		<< "\" r=\"" << radius_ << "\"";

   
	if (!std::holds_alternative<std::monostate>(fill_color_))  {
		out << " fill=\"";
		std::visit(ColorPrinter{out}, fill_color_);
		out << "\"";
	}

	if (!std::holds_alternative<std::monostate>(stroke_color_)) {
		out << " stroke=\"";
		std::visit(ColorPrinter{out}, stroke_color_);
		out << "\"";
	}

	if (stroke_width_ != 1.0) {
		out << " stroke-width=\"" << stroke_width_ << "\"";
	}
 
	if (stroke_line_cap_ != StrokeLineCap::BUTT) {
		out << " stroke-linecap=\"" << stroke_line_cap_ << "\"";
	}

	if (stroke_line_join_ != StrokeLineJoin::MITER) {
		out << " stroke-linejoin=\"" << stroke_line_join_ << "\"";
	}

  
	out << "/>";
}

Text& Text::SetPosition(Point pos){
	position_ = pos;
	return *this;
}

Text& Text::SetOffset(Point offset){
	offset_ = offset;
	return *this;
}


Text& Text::SetFontSize(uint32_t size){
	font_size_ = size;
	return *this;
}


Text& Text::SetFontFamily(std::string font_family){
	font_family_ = std::move(font_family);
	return *this;
}

   

Text& Text::SetFontWeight(std::string font_weight){
	font_weight_ = std::move(font_weight);
	return *this;
}

std::string EscapeText(const std::string& text) {
	std::string escaped;

	for (char c : text) {
		switch (c) {
			case '\"':
				escaped += "&quot;";
				break;
			case '\'':
				escaped += "&apos;";
				break;
			case '<':
				escaped += "&lt;";
				break;
			case '>':
				escaped += "&gt;";
				break;
			case '&':
				escaped += "&amp;";
				break;
			default:
				escaped += c;
				break;
		}
	}

	return escaped;
}

void Document::AddPtr(std::unique_ptr<Object>&& obj) {
	objects_.push_back(std::move(obj));
}

void Document::Render(std::ostream& out) const {
	out << "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n";
	out << "<svg xmlns=\"http://www.w3.org/2000/svg\" version=\"1.1\">" << "\n";

	for (const auto& obj : objects_) {  
		obj->Render(RenderContext(out, 2, 2));
	}

	out << "</svg>";
}

Text& Text::SetData(std::string data) {
	data_ = std::move(data);
	return *this;
}

void Text::RenderObject(const RenderContext& context) const {
	auto& out = context.out;
	out << "<text";

	if (!std::holds_alternative<std::monostate>(fill_color_)) {
		out << " fill=\"";
		std::visit(ColorPrinter{out}, fill_color_);
		out << "\"";
	}

	if (!std::holds_alternative<std::monostate>(stroke_color_)) {
		out << " stroke=\"";
		std::visit(ColorPrinter{out}, stroke_color_);
		out << "\"";
	}

	if (stroke_width_ != 1.0) {
		out << " stroke-width=\"" << stroke_width_ << "\"";
	}

	if (stroke_line_cap_ != StrokeLineCap::BUTT) {
		out << " stroke-linecap=\"" << stroke_line_cap_ << "\"";
	}

	if (stroke_line_join_ != StrokeLineJoin::MITER) {
		out << " stroke-linejoin=\"" << stroke_line_join_ << "\"";
	}

	out << " x=\"" << position_.x
		 << "\" y=\"" << position_.y
		 << "\" dx=\"" << offset_.x
		 << "\" dy=\"" << offset_.y
		 << "\" font-size=\"" << font_size_ << "\"";

	if (!font_family_.empty()) {
		out << " font-family=\"" << font_family_ << "\"";
	}

	if (!font_weight_.empty()) {
		out << " font-weight=\"" << font_weight_ << "\"";
	}

	out << ">" << EscapeText(data_) << "</text>";
}
} 