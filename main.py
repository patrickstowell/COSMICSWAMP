from fastapi import FastAPI, Query
from fastapi import FastAPI, Request
from fastapi.middleware.wsgi import WSGIMiddleware

from typing import Any, Dict, AnyStr, List, Union
JSONStructure = Union[Dict[str, Any], List[Any]]

from enum import Enum
from pydantic import BaseModel, Field
from typing import Annotated
import logging
import random
import time

from dependencies import log_utils as log

from modules import iot_platform 
from modules import information_platform 
from modules import fusion_platform 
# from modules import gui_platform 

######################################
# Main App Definitiono
######################################
app = FastAPI(debug=True)

######################################
# Logging definitions
######################################
iot_platform.cosmicswamp.router.verbosity = log.DEBUG
iot_platform.mqtt_bridge.router.verbosity = log.DEBUG

information_platform.soil.router.verbosity = log.DEBUG
information_platform.weatherstation.ws_router.verbosity = log.DEBUG
information_platform.field.router.verbosity = log.DEBUG
information_platform.agronomy.router.verbosity = log.DEBUG
information_platform.soildepthprobe.router.verbosity = log.DEBUG
information_platform.neutronprobe.router.verbosity = log.DEBUG

######################################
# ROUTE DEFINITIONS
######################################
app.include_router(iot_platform.cosmicswamp.router)
app.include_router(iot_platform.mqtt_bridge.router)

app.include_router(information_platform.soil.router)
app.include_router(information_platform.soildepthprobe.router)
app.include_router(information_platform.weatherstation.ws_router)
app.include_router(information_platform.field.router)
app.include_router(information_platform.neutronprobe.router)

app.include_router(fusion_platform.zone_fusion.router)

######################################
# MIDDLEWARE GUI
######################################
# app.mount("/webapp", WSGIMiddleware(gui_platform.webapp.server))
