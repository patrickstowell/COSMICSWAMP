import sys
import datetime
import time

import dependencies.orion_utils as orion
import modules.iot_platform as iot_platform
import modules.iot_platform.cosmicswamp as cosmicswamp
import modules.information_platform as information_platform

session = orion.session(servicepath="/sensor_data")

if (not cosmicswamp.has_session(session)):
  cosmicswamp.register_session(session)

# iot_platform.mqtt_bridge.create(session,
#   "ThingsNetwork:soil-data-collecting",
#   host="au1.cloud.thethings.network",
#   user="soil-data-collecting@ttn",
#   password="NNSXS.S5IPDTTMU6KWC4PKAP6HMVNK2D73X4LEWJEAIFY.36GDJFOUCGKUKQN5ZHSV42WDRHHCZSVT5ZJK2MGOWTNIK6R7ISAQ",
#   topic="v3/soil-data-collecting@ttn/#",
#   pattern="{}/{}/devices/{entity_id}/up",
#   default_device_type="SoilDepthProbe",
#   force=True
# )

# iot_platform.mqtt_bridge.create(session,
#   "ThingsNetwork:cosmic-swamp-au-lanapre",
#   host="au1.cloud.thethings.network",
#   user="cosmic-swamp-au-lanapre@ttn",
#   password="NNSXS.B7FXR3VJCBK74T4SMZPKH7VZO5BEGYLTG5SNT2A.27SC3ZZEJS2XPLCK42H2NJRUI4AULVFEVA7GODN6FHYHKHCSB3HA",
#   topic="v3/cosmic-swamp-au-lanapre@ttn/#",
#   pattern="{}/{}/devices/{entity_id}/up",
#   default_device_type="NeutronProbe",
#   force=True
# )

print("ENTITIES", cosmicswamp.get_all_current_entities_of_type(session, "MQTTBridge"))
for entity in cosmicswamp.get_all_current_entities_of_type(session, "MQTTBridge"):
  print(entity)
  cosmicswamp.delete_entity(session, entity["id"])



iot_platform.mqtt_bridge.create(session,
  "COSMICSWAMP:WeatherStations",
  host="177.104.61.77",
  user="",
  password="",
  topic="application/2/device/+/up",
  pattern="application/2/device/{entity_id}/up",
  default_device_type="WeatherStation",
  force=True
)

iot_platform.mqtt_bridge.create(session,
  "COSMICSWAMP:WeatherStations2",
  host="177.104.61.77",
  user="",
  password="",
  topic="WS_CNPDIA",
  pattern="{entity_id}",
  default_device_type="WeatherStation",
  force=True
)

iot_platform.mqtt_bridge.create(session,
  "COSMICSWAMP:WeatherStations3",
  host="177.104.61.77",
  user="",
  password="",
  topic="WS_Lanapre",
  pattern="{entity_id}",
  default_device_type="WeatherStation",
  force=True
)

iot_platform.mqtt_bridge.create(session,
  "COSMICSWAMP:NeutronProbes",
  host="177.104.61.77",
  user="",
  password="",
  topic="v3/cosmic-swamp-au-lanapre@ttn/#",
  pattern="{}/{}/devices/{entity_id}/up",
  default_device_type="NeutronProbe",
  force=True
)

iot_platform.mqtt_bridge.create(session,
  "COSMICSWAMP:SoilDepthProbes",
  host="177.104.61.77",
  user="",
  password="",
  topic="v3/soil-data-collecting@ttn/#",
  pattern="{}/{}/devices/{entity_id}/up",
  default_device_type="SoilDepthProbe",
  force=True
)
