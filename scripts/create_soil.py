from fastapi import FastAPI, Request
import dependencies.orion_utils as orion
import dependencies.geojson_utils as geojson
import dependencies.ngsi_utils as ngsi
import paho.mqtt.client as Paho

import modules.iot_platform.cosmicswamp as cosmicswamp
import modules.simulation_platform.pcse_simulator as pcse_simulator
import modules.information_platform as information_platform
import modules.iot_platform as iot_platform
import sys
import datetime
import time
from pcse.db import NASAPowerWeatherDataProvider
from pcse.fileinput import CABOFileReader, YAMLCropDataProvider


import numpy as np
import pandas as pd

session = orion.session(servicepath="/test_process")

time_start = pd.to_datetime("2023-09-13T23:48:06")
time_end   = pd.to_datetime("2023-11-13T23:48:06")

# # Make a soil object.
soil_extent1 = {
"type": "Polygon",
"coordinates": [
          [
            [
              -45.52197431723877,
              -12.17508418874543
            ],
            [
              -45.51963816505449,
              -12.173531331618179
            ],
            [
              -45.51857910939722,
              -12.17158263531826
            ],
            [
              -45.51839221722196,
              -12.169999309048478
            ],
            [
              -45.51889059635511,
              -12.16832462676338
            ],
            [
              -45.51970046244628,
              -12.16686307723566
            ],
            [
              -45.52107100506049,
              -12.167806995558081
            ],
            [
              -45.520136544186755,
              -12.16951212983578
            ],
            [
              -45.521039856365036,
              -12.170486487366958
            ],
            [
              -45.522285804196684,
              -12.171643532294254
            ],
            [
              -45.52063492331996,
              -12.172891917220312
            ],
            [
              -45.52222350680492,
              -12.174444778087022
            ],
            [
              -45.52197431723877,
              -12.17508418874543
            ]
          ]
        ]
}
information_platform.soil.create(session, "Soil:1", 
                                time_index=time_start.isoformat(),
                                density=1.2,
                                carboncontent=0.1,
                                latticewater=0.1,
                                base="ec1.new",
                                campaign="simulated_EC_campaign",
                                location=soil_extent1,
                                soilDepth=100
                                )


soil_extent2 = {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -45.52194316854337,
              -12.175145084918569
            ],
            [
              -45.5225661424592,
              -12.173714021162908
            ],
            [
              -45.52378094159539,
              -12.17273967547024
            ],
            [
              -45.5272695955241,
              -12.172069810733106
            ],
            [
              -45.52795486683169,
              -12.173470435075046
            ],
            [
              -45.52674006769547,
              -12.17474925954508
            ],
            [
              -45.52530722768947,
              -12.175266877222882
            ],
            [
              -45.523967833769746,
              -12.175510461663066
            ],
            [
              -45.52194316854337,
              -12.175145084918569
            ]
          ]
        ]
      }
information_platform.soil.create(session, "Soil:2", 
                                time_index=time_start.isoformat(),
                                density=1.2,
                                carboncontent=0.1,
                                latticewater=0.1,
                                base="ec2.new",
                                campaign="simulated_EC_campaign",
                                location=soil_extent2,
                                soilDepth=100
                                )



soil_extent3 = {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -45.52219235810949,
              -12.174353433581672
            ],
            [
              -45.52063492331996,
              -12.172891917220312
            ],
            [
              -45.52231695289302,
              -12.171643532294254
            ],
            [
              -45.520136544186755,
              -12.169481681105779
            ],
            [
              -45.52107100506049,
              -12.167776546632595
            ],
            [
              -45.51970046244628,
              -12.166802179164009
            ],
            [
              -45.52119559984399,
              -12.16564511315444
            ],
            [
              -45.52346945463748,
              -12.165066578261474
            ],
            [
              -45.52555641725564,
              -12.165340621262203
            ],
            [
              -45.5272695955241,
              -12.166375892272782
            ],
            [
              -45.52845324596487,
              -12.16783744448098
            ],
            [
              -45.52888932770537,
              -12.169359886148797
            ],
            [
              -45.52898277379353,
              -12.17091276766341
            ],
            [
              -45.52854669205209,
              -12.17225250128395
            ],
            [
              -45.52795486683169,
              -12.173379090234604
            ],
            [
              -45.52733189291587,
              -12.172069810733106
            ],
            [
              -45.523749792899025,
              -12.17270922711009
            ],
            [
              -45.52250384506738,
              -12.173714021162908
            ],
            [
              -45.52219235810949,
              -12.174353433581672
            ]
          ]
        ]
      }
information_platform.soil.create(session, "Soil:3", 
                                time_index=time_start.isoformat(),
                                density=1.1,
                                carboncontent=0.05,
                                latticewater=0.1,
                                campaign="simulated_EC_campaign",
                                location=soil_extent3,
                                base="ec3.new",
                                soilDepth=100
                                )



# soil = CABOFileReader("./WOFOST_soil_parameters/ec3.soil")
# print(soil)



# SMW (Soil Moisture at Wilting Point):
# SMW represents the soil moisture content at which plants begin to wilt and experience severe water stress. It is the lower limit of soil moisture that is available to plants, and below this level, crops struggle to extract water from the soil.
# SMFCF (Soil Moisture at Field Capacity):
# SMFCF is the soil moisture content remaining in the soil after excess water has drained away due to gravitational forces. It represents the maximum amount of water that the soil can hold against gravity. SMFCF is considered the upper limit of available soil moisture, as plants can typically extract water from the soil until it reaches this level.
# SM0 (Initial Soil Moisture):
# SM0 is the initial soil moisture content in the root zone at the beginning of a simulation. It represents the amount of water available to the crop at the start of the growing season.
# CRAIRC (Critical Air Content):
# CRAIRC is the air-filled porosity threshold in the soil below which root growth is constrained due to lack of oxygen. It is the point at which the soil is considered to be waterlogged, and root respiration becomes limited.
# RDMSOL (Rooting Depth of the Soil):
# RDMSOL represents the depth of the soil profile that is accessible to the plant roots for water and nutrient uptake. It varies depending on the crop species and growth stage.
# MAXSM (Maximum Soil Moisture Content):
# MAXSM is the maximum soil moisture content that can be stored in the root zone. It is the upper limit of the soil's water-holding capacity and depends on the soil type.
# K0 (Saturated Hydraulic Conductivity):
# K0 represents the soil's ability to transmit water when it is fully saturated. It is a measure of the soil's permeability and determines how quickly water can move through the soil.



