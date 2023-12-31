from fastapi import FastAPI, Request
import dependencies.orion_utils as orion
import dependencies.geojson_utils as geojson
import dependencies.ngsi_utils as ngsi
import paho.mqtt.client as Paho
import matplotlib.pyplot as plt
import scipy
import modules.iot_platform.cosmicswamp as cosmicswamp
import modules.simulation_platform.pcse_simulator as pcse_simulator
import modules.information_platform as information_platform
import modules.iot_platform as iot_platform
import sys
import time

import datetime
import time
from pcse.db import NASAPowerWeatherDataProvider
import yaml
import pcse
import pcse
from pcse.models import Wofost72_WLP_FD
from pcse.fileinput import CABOFileReader, YAMLCropDataProvider
from pcse.db import NASAPowerWeatherDataProvider
from pcse.util import WOFOST72SiteDataProvider
from pcse.base import ParameterProvider
import numpy as np
import pandas as pd

session = orion.session(servicepath="/bristol_process")

from pcse.base.weather import WeatherDataProvider, WeatherDataContainer

from pcse.fileinput import CABOFileReader


for entity in ["WeatherStation:Bristol"]:
    tag = entity.replace(":","-")
    wdf = pd.DataFrame(data=cosmicswamp.get_series_data_for_entity(session, entity, attrs=["*"], limit=1000000))
    wdf.to_csv(f"datadump_{tag}_simbristol.csv")


# for entity in ["WeatherStation:1", "SoilProbe:F1-0-0", "NeutronProbe:Dry2000", "NeutronProbe:Dry1500", "NeutronProbe:Dry1000"]:
#     tag = entity.replace(":","-")
#     wdf = pd.DataFrame(data=cosmicswamp.get_series_data_for_entity(session, entity, attrs=["*"], limit=1000000))
#     wdf.to_csv(f"datadump_{tag}_sim2.csv")

