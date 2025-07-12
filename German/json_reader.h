#pragma once
#include "json.h"
#include "map_renderer.h"
#include "transport_catalogue.h"

namespace catalogue::input {
struct BusDescription {
	BusDescription() = default;
	BusDescription(const std::string_view stop_name, std::vector<std::string_view> stops_list, bool roundtrip) : name(stop_name), stops(std::move(stops_list)), is_roundtrip(roundtrip) {}

	BusDescription(const json::Dict &dict) {
		std::string_view bus_name = dict.at("name").AsString();
		std::vector<std::string_view> stops_list;
		const json::Array &document_stops = dict.at("stops").AsArray();
		stops_list.reserve(dict.at("is_roundtrip").AsBool() ? (document_stops.size() * 2 - 1)
																	  : document_stops.size());
		
		for(const auto &i : document_stops) {
			stops_list.push_back(i.AsString());
		}

		switch(dict.at("is_roundtrip").AsBool()) {
			case false:
				stops_list.insert(stops_list.end(), std::next(stops_list.rbegin()), stops_list.rend());
				break;
			case true:
				break;
		}

		name = bus_name;
		stops = std::move(stops_list);
		is_roundtrip = dict.at("is_roundtrip").AsBool();
	}

	std::string_view name;
	std::vector<std::string_view> stops;
	bool is_roundtrip = false;
};

struct StopDescription {
	StopDescription() = default;
	StopDescription(const std::string_view stop_name, double lat, double lng,
						 const json::Dict &road_distances) : name(stop_name), coordinates{lat, lng},
						 distances(&road_distances) {}

	StopDescription(const json::Dict &dict) {
		std::string_view stop_name = dict.at("name").AsString();
		double lat = dict.at("latitude").AsDouble();
		double lng = dict.at("longitude").AsDouble();
		const json::Dict &road_distances = dict.at("road_distances").AsDict();

		name = stop_name;
		coordinates = geo::Coordinates(lat, lng);
		distances = &road_distances;
	}

	std::string_view name;
	geo::Coordinates coordinates;
	const json::Dict *distances;
};

class JsonReader {
public:
	void ParseDocument(const json::Array &commands);
	void ApplyCommands(TransportCatalogue &catalogue) const;
private:
	std::vector<StopDescription> stop_requests_;
	std::vector<BusDescription> bus_requests_;
};

render::RenderSettings ParseRenderSettings(const json::Dict &settings);
}

namespace catalogue::output {
json::Document PrintStat(const json::Array &stats, const TransportCatalogue &catalogue, const render::RenderSettings &settings);
} 