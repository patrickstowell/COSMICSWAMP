from fastapi import FastAPI, Request
import dependencies.orion_utils as orion
import dependencies.geojson_utils as geojson
import dependencies.ngsi_utils as ngsi

import modules.iot_platform.cosmicswamp as cosmicswamp
import modules.simulation_platform.pcse_simulator as pcse_simulator

import json


def program_section(val):
    print("*************************")
    print(val)
    print("*************************")

# Start FiWare Sesssion
program_section("Simulation Session")
session = orion.session(servicepath="/v4_pilot")

field_center = [0.5,0.5]
flux_location = [0.5,0.5]

soil_properties_1 = {
    "density": 1.2
}

soil_properties_2 = {
    "density": 1.2
}

crop_properties_1 = {
    "density": 1.2
}

forecast_properties = {
    "source": "",
    "source_type": ""
}

program_section("Current Entity State")
cosmicswamp.clear_session(session)
print(cosmicswamp.get_all_current_entity_ids(session))

program_section("Building objects")
field = cosmicswamp.create_field(session, "Field:1", center_location=field_center, radius=800)
for i, zone in geojson.seperate_into_zones( field["location"] ):
    cosmicswamp.create_managementzone(session, f"ManagementZone:1-{i}", location=zone)

cosmicswamp.create_soil(session, "Soil:1", jsondata=soil_properties_1)
cosmicswamp.create_soil(session, "Soil:2", jsondata=soil_properties_2)
cosmicswamp.create_crop(session, "Crop:1", jsondata=crop_properties_1)

cosmicswamp.create_weatherstation(session, "WeatherStation:1", location=field_center)
cosmicswamp.create_weatherforecaster(session, "WeatherForecaster:1", location=field_center, jsondata=forecast_properties)
cosmicswamp.create_cosmicfluxstation(session, "CosmicFluxStation:1", location=flux_location, isnmdb=True, station="JUNG1")

probe_positions = [ [54,3], [54,3.5], [54,4], [54,5], [54,6] ]
for i, location in enumerate(probe_positions):
    location = geojson.point(location)
    cosmicswamp.create_soildepthprobe(session, f"SoilDepthProbe:{i}", location=location, i0=0)

neutron_positions = [ [54,3], [54,2] ]
for i, location in enumerate(neutron_positions):
    location = geojson.point(location)
    cosmicswamp.create_neutronprobe(session, f"NeutronProbe:{i}", location=location, i0=0)


program_section("Current Master State")
for e in cosmicswamp.get_all_current_entity_ids(session):
    print(e["id"])


# Setup the simulation for each management zone
simulation_session = pcse_simulator.create_session(session, "test")

# # Run simulation day by day to estimate soil moisture.
for day in maxdays:

    # Update the simulation to get crop parameters
    pcse_simulator.get_simulation_for_zone_on_day(session)
    


    # # - Simulate Weather Data
    # weather_station_simulator.simulate_weather(weather_id, weather)

    # # - Based on current SM, update the neutron probe (updates 24 hours of data)
    # neutron_probe_simulator.simulate_data_from_sm(neutron_id, prev_sm, sm)
    # soil_probe_simulator.simulate_data_from_sm(neutron_id, prev_sm, sm)

    # # - Run the scheduling manually for the simulated model
    # information_global_scheduler(simulation_session, date)
    # fusion_global_scheduler(simulation_session, date)

    # # - If water updates
    # if (irrigation_application):
    #     cosmicswamp.add_irrigation_to_crop(simulation_session)

# # Sensitivity
# pcse_simulator.remove_session(simulation_session)


# print(data)
