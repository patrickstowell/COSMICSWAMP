# COSMICSWAMP : IoT Processing of Cosmic Ray sensors for irrigation monitoring.

COSMIC-SWAMP is a set of FastAPI routes that can be attached to a FiWARE Orion based data management platform to enable the automated processing of cosmic ray sensor data. When activated raw sensor data can be sent to specific end points in the platform, and COSMICSWAMP will automatically try to uses their geolocations to update daily forecasts of soil moisture in management zonoes across a site.


### Simple Installation
COSMIC-SWAMP is distributed as a set of python based FastAPI modules which are automatically connected to a local FiWare-orion backend.
Note that by default the FiWare backend requires `docker`` and `docker-compose` for it to be run. Those wishing to connect COSMIC-SWAMP to existing external services by setting several environmental variables as discussed in the next section.

Assuming you are setting up COSMIC-SWAMP for the first time on a new machine to test out its features. You can checkout this repository into a new folder
```
git clone https://github.com/patrickstowell/COSMICSWAMP.git
```

Before starting the COSMIC-SWAMP services you first need to start the backend in a seperate terminal.
```
cd COSMICSWAMP/backend
docker-compose up -d
```

After this you can start the COSMIC-SWAMP server though uvicorn from the main source directory
```
cd COSMICSWAMP/
source setup.sh
uvicorn main:app --reload
```

If you want to use an existing FiWare instance of Orion, CrateDB, and QuantumLeap alternatively you can edit the IP addresses in `setup.sh`` and skip the backend step.

### Platform Management

When COSMICSWAMP starts it enables a series of new REST API end points on the running machine on port `8000`. To see a full list of API commands with automated docs generated through FastAPI in the browser of the device running COSMIC-SWAMP you can open the following 
```
http://127.0.0.1:8000/docs
```

For example the REST API end point `http://127.0.0.1:8000/iot-platform/cosmicswamp/current/type/{entity_type}` will return all entities of a chosen type in the platform. Note that in keeping with FiWare, REST api requests require the FiWareService-path and FiwareService variables to be set accordingly in the request headers.


Because COSMICSWAMP is built on a python FastAPI instance, it is possible to use the code itself as an SDK to interface with the platform itself. Several examples are given in the scripts folder on how to use COSMIC-SWAMP to setup a new pilot site, add fields, and locate sensors in the platform to prepare for long term forecasting. The example below shows how easy it is to use the python SDK to add new centre pivot irrigation fields and seperate them into specific irrigatino management zones with sensors in each one.

```python 
import dependencies.orion_utils as orion
import dependencies.geojson_utils as geojson
import dependencies.ngsi_utils as ngsi
import modules.iot_platform.cosmicswamp as cosmicswamp
import modules.simulation_platform.pcse_simulator as pcse_simulator
import modules.information_platform as information_platform
import modules.iot_platform as iot_platform


# Make a session
session = orion.session(servicepath="/field_pilot")

# Create a field of radius 600m
field_center = [-45.523917847717236,-12.170341419421398]
information_platform.field.create(session, 
    "Field:1", center_location=field_center, radius=600)

# Split into 48 management zones
information_platform.field.split_into_radial_zones(session, 
    "Field:1", nradial=4, naround=12)

# Place a soil depth probe in each management zone to prepare for
simulation
for zone in 
    information_platform.field.get_associated_zones(session, "Field:1"):

    # Label simulated probes based on zoneid
    zoneid = zone["zoneid"]["value"]
    information_platform.soildepthprobe.create(session, 
      f"SoilProbe:F1-{zoneid}", location=geojson.split_lat_lon_from_polygon(zone["location"]["value"]))
  ```

COSMIC-SWAMP is automatically setup to run data fusion processes for management zones in 24 hour increments, so based on the example above, every day the raw probe data will be evaluated and used to estimate the state of the moisture in each zone. Data from sensors can be automatically setup to be sent to the end points created by COSMIC-SWAMP, or can be transferred manually with the Python SDK.

```python
# Send raw ADC values into soil depth probe handler
information_platform.soildepthprobe.update(session, f"SoilProbe:F1-{zoneid}", time_index=time_current.isoformat(), sm0=400, sm2=421, sm2=456)
```

Sensor data can also be simulated based on the expected final output. This involves 'uncalibrating' the asssumed sensor reading (for example true soil moisture) to get a raw measurement, which is then passed back into the platform as if it was real data.

```python
# Send true values into simulation and extract raw ADC values with noise
information_platform.soildepthprobe.simulate(session, f"SoilProbe:F1-{zoneid}", time_index=time_current.isoformat(), sc0=0.24, sc1=0.30, sc2=0.35, adc_noise=10)
```

 This combined with soil and crop maps allows automated monitoring and forecasting of yields in each zone in almost real time. 