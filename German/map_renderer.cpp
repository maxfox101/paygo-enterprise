#include "map_renderer.h"

namespace render {
MapRenderer::MapRenderer(const RenderSettings &render_settings) : settings_(render_settings) {}

void MapRenderer::RenderBuses(svg::Document &doc, const std::deque<transport::Bus> &buses, const SphereProjector& projector) const {
	size_t color_index = 0;

	for(const transport::Bus &bus : buses) {
		if(bus.stop_list.empty()) {
			continue;
		}

		svg::Polyline line;

		for(const transport::Stop *stop : bus.stop_list) {
			line.AddPoint(projector(stop->coordinates));
		}

		line.SetStrokeColor(settings_.color_palette[color_index % settings_.color_palette.size()])
				.SetFillColor("none")
				.SetStrokeWidth(settings_.line_width)
				.SetStrokeLineCap(svg::StrokeLineCap::ROUND)
				.SetStrokeLineJoin(svg::StrokeLineJoin::ROUND);
		doc.Add(line);

		color_index++;
	}
}

void MapRenderer::RenderBusesLabels(svg::Document &doc, const std::deque<transport::Bus> &buses, const SphereProjector& projector) const {
	size_t color_index = 0;

	for(const transport::Bus &bus : buses) {
		if(bus.stop_list.empty()){
			continue;
		}

		const svg::Color &color = settings_.color_palette[color_index % settings_.color_palette.size()];
		std::vector<const transport::Stop *> end_points;
		end_points.push_back(bus.stop_list.front());

		if(!bus.is_roundtrip) {
			size_t last_index = bus.stop_list.size() / 2;
			
			if(last_index > 0 && bus.stop_list[0] != bus.stop_list[last_index]) {
				end_points.push_back(bus.stop_list[last_index]);
			}
		}

		for(const transport::Stop *stop : end_points) {
			const svg::Point point = projector(stop->coordinates);
			svg::Text underlayer;

			underlayer.SetPosition(point)
						 .SetOffset(settings_.bus_label_offset)
						 .SetFontSize(settings_.bus_label_font_size)
						 .SetFontFamily("Verdana")
						 .SetFontWeight("bold")
						 .SetData(std::string(bus.number))
						 .SetFillColor(settings_.underlayer_color)
						 .SetStrokeColor(settings_.underlayer_color)
						 .SetStrokeWidth(settings_.underlayer_width)
						 .SetStrokeLineJoin(svg::StrokeLineJoin::ROUND)
						 .SetStrokeLineCap(svg::StrokeLineCap::ROUND);

			svg::Text bus_text;
			bus_text.SetPosition(point)
					  .SetOffset(settings_.bus_label_offset)
					  .SetFontSize(settings_.bus_label_font_size)
					  .SetFontFamily("Verdana")
					  .SetFontWeight("bold")
					  .SetData(std::string(bus.number))
					  .SetFillColor(color)
					  .SetStrokeColor(svg::NoneColor);

			doc.Add(underlayer);
			doc.Add(bus_text);
		}

		++color_index;
	}
}

void MapRenderer::RenderStops(svg::Document &doc, const std::vector<const transport::Stop *> stops, const SphereProjector& projector) const {
	for (const auto* stop : stops) {
		const auto point = projector(stop->coordinates);
        
		svg::Circle circle;
		circle.SetCenter(point)
				.SetRadius(settings_.stop_radius)
				.SetFillColor("white");
        
		doc.Add(circle);
	}
}

void MapRenderer::RenderStopsLabels(svg::Document &doc, const std::vector<const transport::Stop *> stops, const SphereProjector& projector) const {
	for (const auto* stop : stops) {
		const auto point = projector(stop->coordinates);

		svg::Text underlayer;
		underlayer.SetPosition(point)
					 .SetOffset(settings_.stop_label_offset)
					 .SetFontSize(settings_.stop_label_font_size)
					 .SetFontFamily("Verdana")
					 .SetData(std::string(stop->name))
					 .SetFillColor(settings_.underlayer_color)
					 .SetStrokeColor(settings_.underlayer_color)
					 .SetStrokeWidth(settings_.underlayer_width)
					 .SetStrokeLineJoin(svg::StrokeLineJoin::ROUND)
					 .SetStrokeLineCap(svg::StrokeLineCap::ROUND);

		svg::Text stop_text;
		stop_text.SetPosition(point)
					.SetOffset(settings_.stop_label_offset)
					.SetFontSize(settings_.stop_label_font_size)
					.SetFontFamily("Verdana")
					.SetData(std::string(stop->name))
					.SetFillColor("black")
					.SetStrokeColor(svg::NoneColor);
		doc.Add(underlayer);
		doc.Add(stop_text);
	}
}

svg::Document MapRenderer::RenderMap(const catalogue::TransportCatalogue &catalogue) const {
	svg::Document doc;
	std::unordered_set<const transport::Stop *> unique_stops;
	std::vector<const transport::Stop *> stops;
	std::vector<geo::Coordinates> geo_coords;
	std::deque<transport::Bus> buses = catalogue.GetAllBuses();

	for(const transport::Bus &bus : buses) {
		for(const transport::Stop *stop : bus.stop_list) {
			if(unique_stops.insert(stop).second) {
				geo_coords.push_back(stop->coordinates);
				stops.push_back(stop);
			}
		}
	}

	SphereProjector projector(geo_coords.begin(), geo_coords.end(), settings_.width, settings_.height, settings_.padding);

	// Сортируем автобусы и остановки по именам
	std::sort(buses.begin(), buses.end(), [](const auto &lhs, const auto &rhs) {
		return lhs.number < rhs.number;
	});
	std::sort(stops.begin(), stops.end(), [](const auto *lhs, const auto *rhs) {
		return lhs->name < rhs->name;
	});

	RenderBuses(doc, buses, projector);
	RenderBusesLabels(doc, buses, projector);
	RenderStops(doc, stops, projector);
	RenderStopsLabels(doc, stops, projector);

	return doc;
}
} 