#pragma once

#include <optional>
#include <cstdlib>
#include <algorithm>

#include "svg.h"
#include "transport_catalogue.h"

namespace render {
struct RenderSettings {
	double width = 0;
	double height = 0;
	double padding = 0;

	double line_width = 0;
	double stop_radius = 0;

	uint32_t bus_label_font_size = 0;
	svg::Point bus_label_offset = {0, 0};

	uint32_t stop_label_font_size = 0;
	svg::Point stop_label_offset = {0, 0};

	svg::Color underlayer_color;
	double underlayer_width = 0;

	std::vector<svg::Color> color_palette;
};

inline const double EPSILON = 1e-6;
inline bool IsZero(double value) {
	return std::abs(value) < EPSILON;
}

class SphereProjector {
public:
	// points_begin и points_end задают начало и конец интервала элементов geo::Coordinates
	template <typename PointInputIt>
	SphereProjector(PointInputIt points_begin, PointInputIt points_end,
						double max_width, double max_height, double padding)
		: padding_(padding) {
		// Если точки поверхности сферы не заданы, вычислять нечего
		if (points_begin == points_end) {
			return;
		}

		// Находим точки с минимальной и максимальной долготой
		const auto [left_it, right_it] = std::minmax_element(
			points_begin, points_end,
			[](auto lhs, auto rhs) { return lhs.longitude < rhs.longitude; });
		min_lon_ = left_it->longitude;
		const double max_lon = right_it->longitude;

		// Находим точки с минимальной и максимальной широтой
		const auto [bottom_it, top_it] = std::minmax_element(
			points_begin, points_end,
			[](auto lhs, auto rhs) { return lhs.latitude < rhs.latitude; });
		const double min_lat = bottom_it->latitude;
		max_lat_ = top_it->latitude;

		// Вычисляем коэффициент масштабирования вдоль координаты x
		std::optional<double> width_zoom;
		if (!IsZero(max_lon - min_lon_)) {
			width_zoom = (max_width - 2 * padding) / (max_lon - min_lon_);
		}

		// Вычисляем коэффициент масштабирования вдоль координаты y
		std::optional<double> height_zoom;
		if (!IsZero(max_lat_ - min_lat)) {
			height_zoom = (max_height - 2 * padding) / (max_lat_ - min_lat);
		}

		if (width_zoom && height_zoom) {
			// Коэффициенты масштабирования по ширине и высоте ненулевые,
			// берём минимальный из них
			zoom_coeff_ = std::min(*width_zoom, *height_zoom);
		} else if (width_zoom) {
			// Коэффициент масштабирования по ширине ненулевой, используем его
			zoom_coeff_ = *width_zoom;
		} else if (height_zoom) {
			// Коэффициент масштабирования по высоте ненулевой, используем его
			zoom_coeff_ = *height_zoom;
		}
	}

	// Проецирует широту и долготу в координаты внутри SVG-изображения
	svg::Point operator()(geo::Coordinates coords) const {
		return {
			(coords.longitude - min_lon_) * zoom_coeff_ + padding_,
			(max_lat_ - coords.latitude) * zoom_coeff_ + padding_
		};
	}

private:
	double padding_;
	double min_lon_ = 0;
	double max_lat_ = 0;
	double zoom_coeff_ = 0;
};

class MapRenderer {
public:
	explicit MapRenderer(const RenderSettings &render_settings);
	svg::Document RenderMap(const catalogue::TransportCatalogue &catalogue) const;

private:
	void RenderBuses(svg::Document &doc, const std::deque<transport::Bus> &buses, const SphereProjector& projector) const;
	void RenderBusesLabels(svg::Document &doc, const std::deque<transport::Bus> &buses, const SphereProjector& projector) const;
	void RenderStops(svg::Document &doc, const std::vector<const transport::Stop *> stops, const SphereProjector& projector) const;
	void RenderStopsLabels(svg::Document &doc, const std::vector<const transport::Stop *> stops, const SphereProjector& projector) const;

	RenderSettings settings_;
};
} 