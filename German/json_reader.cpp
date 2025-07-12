#include "json_reader.h"
#include "json_builder.h"
#include <sstream>
using namespace std::literals;

namespace catalogue::input {
void JsonReader::ParseDocument(const json::Array &commands) {
	for(const json::Node &request : commands) {
		const json::Dict &content = request.AsDict();

		if(content.at("type").AsString() == "Stop") {
			stop_requests_.emplace_back(StopDescription(content));
		} else if(content.at("type").AsString() == "Bus") {
			bus_requests_.emplace_back(BusDescription(content));
		}
	}
}

void JsonReader::ApplyCommands(TransportCatalogue &catalogue) const {
	std::vector<std::tuple<std::string_view, std::string_view, int>> distances;
	for(const StopDescription &request : stop_requests_) {
		catalogue.AddStop(request.name, request.coordinates);

		for(const auto &distance : *request.distances) {
			distances.emplace_back(std::make_tuple<std::string_view, std::string_view, int> (
										  std::string_view(request.name),
										  std::string_view(distance.first),
										  distance.second.AsInt()));
		}
	}

	for(const auto &[from, to, distance] : distances) {
		catalogue.SetDistance(from, to, distance);
	}

	for(const BusDescription &request : bus_requests_) {
		std::vector<const transport::Stop *> stops;
		stops.reserve(request.stops.size());
		
		for(std::string_view stop_name : request.stops) {
			if (const transport::Stop *stop = catalogue.FindStop(stop_name)) {
				stops.push_back(stop);
			}
		}

		catalogue.AddBus(request.name, std::move(stops), request.is_roundtrip);
	}
}

svg::Color GetColorFromNode(const json::Node &node) {
	if (node.IsString()) {
		return node.AsString();
	}
	
	if (node.IsArray()) {
		const auto &color_array = node.AsArray();
		
		if (color_array.size() == 3) {
			return svg::Rgb{
				static_cast<uint8_t>(color_array[0].AsInt()),
				static_cast<uint8_t>(color_array[1].AsInt()),
				static_cast<uint8_t>(color_array[2].AsInt())
			};
		}
		
		if (color_array.size() == 4) {
			return svg::Rgba{
				static_cast<uint8_t>(color_array[0].AsInt()),
				static_cast<uint8_t>(color_array[1].AsInt()),
				static_cast<uint8_t>(color_array[2].AsInt()),
				color_array[3].AsDouble()
			};
		}
	}

	return svg::NoneColor;
}

render::RenderSettings ParseRenderSettings(const json::Dict &settings) {
	render::RenderSettings result;
	result.width = settings.at("width"s).AsDouble();
	result.height = settings.at("height"s).AsDouble();
	result.padding = settings.at("padding"s).AsDouble();

	result.line_width = settings.at("line_width"s).AsDouble();
	result.stop_radius = settings.at("stop_radius"s).AsDouble();

	result.bus_label_font_size = settings.at("bus_label_font_size"s).AsInt();
	{
		json::Array arr = settings.at("bus_label_offset"s).AsArray();
		result.bus_label_offset = {arr[0].AsDouble(), arr[1].AsDouble()};
	}

	result.stop_label_font_size = settings.at("stop_label_font_size"s).AsInt();
	{
	json::Array arr = settings.at("stop_label_offset"s).AsArray();
	result.stop_label_offset = {arr[0].AsDouble(), arr[1].AsDouble()};
	}

	result.underlayer_color = GetColorFromNode(settings.at("underlayer_color"s));

	result.underlayer_width = settings.at("underlayer_width"s).AsDouble();

	json::Array color_palette_list = settings.at("color_palette"s).AsArray();
	std::vector<svg::Color> color_palette(color_palette_list.size());
	for(size_t i = 0; i < color_palette_list.size(); ++i) {
		color_palette[i] = GetColorFromNode(color_palette_list[i]);
	}
	result.color_palette = std::move(color_palette);

	return result;
}
}

namespace catalogue::output {
json::Node LoadStopNode(const json::Dict &stat_info, const TransportCatalogue &catalogue) {
	json::Builder builder;
	int id = stat_info.at("id").AsInt();
	builder.StartDict().Key("request_id").Value(id);
	const transport::Stop *stop = catalogue.FindStop(stat_info.at("name").AsString());

	if(!stop) {
		return builder.Key("error_message").Value("not found").EndDict().Build();
	}

	std::vector<std::string_view> buses = catalogue.GetStopInfo(*stop);
	json::Array json_buses;

	for(std::string_view bus : buses) {
		json_buses.push_back(json::Node(std::string(bus)));
	}

	return builder.Key("buses").Value(json_buses)
					  .EndDict().Build();
}

json::Node LoadBusNode(const json::Dict &stat_info, const TransportCatalogue &catalogue) {
	json::Builder builder;
	int id = stat_info.at("id").AsInt();
	builder.StartDict().Key("request_id").Value(id);
	const transport::Bus *bus = catalogue.FindBus(stat_info.at("name").AsString());
	
	if(!bus) {
		return builder.Key("error_message").Value("not found").EndDict().Build();
	}

	detail::BusInfo info = catalogue.GetBusInfo(*bus);
	return builder.Key("curvature").Value(info.curvature)
					  .Key("route_length").Value(info.length)
					  .Key("stop_count").Value(info.stops)
					  .Key("unique_stop_count").Value(info.unique_stops)
					  .EndDict().Build();
}

json::Node LoadMapNode(const json::Dict &stat_info, const TransportCatalogue &catalogue, const render::RenderSettings &settings) {
	json::Builder builder;
	int id = stat_info.at("id").AsInt();
	std::stringstream out;
	render::MapRenderer renderer(settings);
	svg::Document doc = renderer.RenderMap(catalogue);
	doc.Render(out);

	std::string map = out.str();

	return builder.StartDict()
					  .Key("request_id").Value(id)
					  .Key("map").Value(map)
					  .EndDict().Build();
}

json::Document PrintStat(const json::Array &stats, const TransportCatalogue &catalogue, const render::RenderSettings &settings) {
	json::Builder builder;
	builder.StartArray();
	for(const json::Node &stat : stats) {
		const json::Dict request = stat.AsDict();

		if(request.at("type").AsString() == "Bus"s) {
			builder.Value(LoadBusNode(request, catalogue).GetValue());
		} else if(request.at("type").AsString() == "Stop"s) {
			builder.Value(LoadStopNode(request, catalogue).GetValue());
		} else if(request.at("type").AsString() == "Map"s) {
			builder.Value(LoadMapNode(request, catalogue, settings).GetValue());
		}
	}
	builder.EndArray();

	return json::Document(builder.Build());
}
} 