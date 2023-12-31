from fastapi import FastAPI, Header, Request, APIRouter, Depends, HTTPException, Query
from fastapi_utils.tasks import repeat_every
from typing import Union, Annotated, List, Any, Dict, AnyStr, Union
JSONStructure = Union[Dict[str, Any], List[Any]]

import paho.mqtt.client as Paho
import datetime
import time
import math
import statistics
import parse
import os
import requests
import json
import logging
import pandas as pd
from typing import List
import pprint

import datetime
import time
import math
import statistics
import os
import requests
import json
import logging
import pandas as pd
import scipy
import numpy as np

import dependencies.orion_utils as orion
import dependencies.crate_utils as crate
import dependencies.ngsi_utils as ngsi
import dependencies.geojson_utils as geojson
import dependencies.log_utils as cslog

import modules.iot_platform.cosmicswamp as cosmicswamp

import modules.information_platform.configuration as configuration
import modules.information_platform.managementzone as managementzone


###################################################
# MQTT ROUTER 
###################################################
router = APIRouter(
    prefix="/iot-platform/mqtt-bridge",
    tags=["mqtt-bridge", "iot-platform"],
    dependencies=[Depends(configuration.settings), 
        Depends(orion.required_headers)]
)
router.verbosity = cslog.DEBUG

###################################################
# MQTT HANDLERS
###################################################

# Define the data structures
router.bridge_clients = {}
router.bridge_servers = {}
router.bridge_ids = {}


def on_connect(client, userdata, flags, rc):
    # MQTT Connection message, called async when attached to broker
    # Once a connection happens we subscribe to ALL topics.

    cslog.debug(router, "CONNECTION STATUS : ", client._client_id, rc )

    if rc == 0:

        serverlist = router.bridge_servers[client._client_id]

        for server in serverlist:
            entity_config = server

            entity_id   = entity_config["defaultdeviceid"]["value"]
            entity_type = entity_config["defaultdevicetype"]["value"]
            pattern     = entity_config["pattern"]["value"]
            session     = entity_config["session"]

            client.subscribe( entity_config["topic"]["value"] )
            cslog.info(router, "Connected", str(client._client_id), entity_config["topic"]["value"] )

    else:
        cslog.error(router, f"Failed to connect, return code {rc}", client._client_id)


def on_message_in(client, userdata, msg):

    print("MESSAGE IN", msg)
    cslog.debug(router, "MESSAGE IN", msg)
            
    # MQTT received message, called async when MQTT publish received
    # Once a message is received we publish to our out MQTT servers.
    cslog.debug(router, f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    serverlist = router.bridge_servers[client._client_id]

    print("SERVERLIST MESSAGE", len(serverlist))
    for server in serverlist:
            
            entity_config = server

            entity_id   = entity_config["defaultdeviceid"]["value"]
            entity_type = entity_config["defaultdevicetype"]["value"]
            pattern     = entity_config["pattern"]["value"]
            topic       = entity_config["topic"]["value"]

            session     = entity_config["session"]

            # Check topic 
            topic = topic.replace("+","{}")
            topic = topic.replace("#","{matching}")
            topiccheck = parse.parse(topic, msg.topic)
            if not topiccheck: continue

            # Check Pattern
            entity_data = parse.parse(pattern, msg.topic)
            if not entity_data: continue 

            # Decode data
            vals = (msg.payload.decode())
            cslog.debug(router, msg.payload.decode())

            if entity_data:
                if "entity_id"   in entity_data: entity_id   = entity_data["entity_id"]
                if "entity_type" in entity_data: entity_type = entity_data["entity_type"]

            print("ENTITY DATA", entity_config)
            redirect_mqtt_locally(session, entity_id, entity_type, vals)


def on_disconnect(client, userdata,  rc):
    cslog.debug(router, "Disconnected", client, userdata, rc)


###################################################
# MQTT-REST API INTERFACE
###################################################
@router.get("/redirect")
def redirect_mqtt_locally(request: Request, entity_id: str, entity_type: str, rawdata: str):

        entity_type = entity_type.lower()
        print(rawdata, entity_type)
        url = f"http://127.0.0.1:8000/information-platform/{entity_type}/iotagent/{entity_id}?payload_type=mqtt_ttn" 
        headers = orion.get_fiware_headers(request)
        orion.post(url, headers, json={"payload_data": rawdata} )

@router.get("/refresh")
def refresh_event():
    """
    Loops over available MQTT instances in the current sesssion.
    """    

    # Sessions need to be run for all possible maps.
    session_list = cosmicswamp.get_session()
    cslog.debug(router, "Refreshing event")
    cslog.debug(router, session_list["sessions"])

    router.bridge_ids = []
    router.bridge_clients = {}
    router.bridge_servers = {}

    cslog.debug(router, "SESSION LIST", session_list["sessions"])
    for pathcombo in session_list["sessions"]["value"]:
        service, servicepath = pathcombo.split("/")
        session = orion.session(service,"/" + servicepath)

        # For each session make a list of the requested user host port
        mqtt_client_data = cosmicswamp.get_all_current_entities_of_type(session, "MQTTBridge")

        cslog.debug(router, "Session MQTT Agents :", mqtt_client_data, router.bridge_ids)
        for entity in mqtt_client_data:

            # Make a client ID hash
            client_id = entity["user"]["value"] + entity["host"]["value"] + str(entity["port"]["value"])
            server = entity

            # If no client id we need to make the server
            if client_id not in router.bridge_ids:

                client = Paho.Client(client_id=client_id)
                client.on_message = on_message_in
                client.on_connect = on_connect
                client.on_disconnect = on_disconnect

                print("APPENDING")
                router.bridge_ids.append(client_id)
                router.bridge_clients[client._client_id] = client
                router.bridge_servers[client._client_id] = []

                #print("CLIENT", server_name, int(server["port"]["value"]), server["topic"]["value"], server["pattern"]["value"], server["user"]["value"], server["password"]["value"])

            print("STARTING SAVER")
            cslog.debug(router, "SESSION", client_id, client._client_id)
            server["session"] = session
            router.bridge_servers[client._client_id].append(server)

    print("STARTING CLIENTS")
    for client_id in router.bridge_servers:

        server = router.bridge_servers[client._client_id][0]
        client = router.bridge_clients[client._client_id]

        if "user" in server and "password" in server:
            client.username_pw_set(server["user"]["value"], server["password"]["value"])

        server_name = server["host"]["value"].strip("http://")
        client.connect(host=server_name, port=int(server["port"]["value"]))
        client.loop_start()


###################################################
# CREATE/UPDATE/DELETE
###################################################
@router.get("/create/{entity_id}")
def create(request: Request,
            entity_id,
            attrs: List[str] = None,
            time_index: str = None,
            jsondata: JSONStructure = None,
            pattern:  str = "{}/devices/{entity_id}/up",
            enabled:  bool = True,
            password: str = None,
            user:     str = None,
            host:     str = None,
            port:     int = 1883,
            topic:    str = "+/devices/+/up",
            default_device_type: str = "MQTTDevice",
            default_device_id:   str = "MQTTMessage",
            force: bool = False
    ):

    headers = orion.get_fiware_headers(request)

    entity_type = "MQTTBridge"

    body = ngsi.compile_entity(jsondata, entity_id, entity_type, time_index, attrs)

    ngsi.set_default(body, "TimeInstant", orion.TimeInstant(time_index))

    ngsi.set_default(body, "topic", orion.String(topic))
    ngsi.set_default(body, "pattern", orion.String(pattern))
    ngsi.set_default(body, "enabled", orion.Number(enabled))
    ngsi.set_default(body, "password", orion.String(password))
    ngsi.set_default(body, "user", orion.String(user))
    ngsi.set_default(body, "host", orion.String(host))
    ngsi.set_default(body, "port", orion.Number(port))
    ngsi.set_default(body, "defaultdeviceid", orion.String(default_device_id))
    ngsi.set_default(body, "defaultdevicetype", orion.String(default_device_type))
        
    r = cosmicswamp.create_entity(request, entity_id, jsondata=body)

    return body


@router.post("/delete/{entity_id}")
def delete(request: Request,
            entity_id,
            purge: bool = False
    ):
    cosmicswamp.delete_entity(request, entity_id, purge)


###################################################
# REPEATED HANDLER
###################################################
@router.on_event("startup")
@repeat_every(seconds=3600)  # 1 hour
def startup_event():
    refresh_event()
    

###################################################
# SIMULATION TOOLS
###################################################
def fake_ttn_mqtt(topic, **kwargs):
    
    template = {
        "@type": "type.googleapis.com/ttn.lorawan.v3.ApplicationUp",
        "end_device_ids": {
        "device_id": "greenstick-21fk",
        "application_ids": {
            "application_id": "soil-data-collecting"
        },
        "dev_eui": "0012F80000000571",
        "join_eui": "0101010101010101",
        "dev_addr": "260D50E6"
        },
        "correlation_ids": [
        "gs:uplink:01HEVFC9GQH5WY09QDGG0YW52H"
        ],
        "received_at": "2023-11-10T02:01:07.048559511Z",
        "uplink_message": {
        "session_key_id": "AYuwtYLJLlKtcfcN1LDtDQ==",
        "f_port": 1,
        "f_cnt": 292,
        "frm_payload": "U3wyMzA5MTAwMTAwfEl8MzEyMXxUMXwyOC42fFQyfDI3LjZ8VDN8MjYuOQ==",
        "decoded_payload": {
            "bytes": [
            83,
            124,
            50,
            51,
            48,
            57,
            49,
            48,
            48,
            49,
            48,
            48,
            124,
            73,
            124,
            51,
            49,
            50,
            49,
            124,
            84,
            49,
            124,
            50,
            56,
            46,
            54,
            124,
            84,
            50,
            124,
            50,
            55,
            46,
            54,
            124,
            84,
            51,
            124,
            50,
            54,
            46,
            57
            ],
            "from": "soil",
            "ngsi": {
            "I": "3121",
            "S": "2309100100",
            "T1": "28.6",
            "T2": "27.6",
            "T3": "26.9",
            "M1": "2000",
            "M2": "1000",
            "M3": "500",
            "C1": "28.6",
            "C2": "27.6",
            "C3": "26.9"
            },
            "ultralight": "S|2309100100|I|3121|T1|28.6|T2|27.6|T3|26.9",
            "unix": 1694307600000
        },
        "rx_metadata": [
            {
            "gateway_ids": {
                "gateway_id": "matopiba-fieldstation",
                "eui": "000000FFFF002001"
            },
            "timestamp": 331097515,
            "rssi": -99,
            "channel_rssi": -99,
            "snr": 6.5,
            "uplink_token": "CiMKIQoVbWF0b3BpYmEtZmllbGRzdGF0aW9uEggAAAD//wAgARCry/CdARoMCOKdtqoGEI+TjJADIPjHzLfR1hA=",
            "channel_index": 1,
            "received_at": "2023-11-10T02:01:06.649905606Z"
            }
        ],
        "settings": {
            "data_rate": {
            "lora": {
                "bandwidth": 125000,
                "spreading_factor": 7,
                "coding_rate": "4/5"
            }
            },
            "frequency": "915400000",
            "timestamp": 331097515
        },
        "received_at": "2023-11-10T02:01:06.840282320Z",
        "consumed_airtime": "0.107776s",
        "network_ids": {
            "net_id": "000013",
            "ns_id": "EC656E0000000183",
            "tenant_id": "ttn",
            "cluster_id": "au1",
            "cluster_address": "au1.cloud.thethings.network"
        }
        }
    }

    for key in kwargs:
        template[key] = kwargs[key]

    client = Paho.Client(client_id="simulated_connection")
    client.connect(host="127.0.0.1", port=1883)
    client.loop_start()
    client.publish(topic, json.dumps(template, indent=2).encode('utf-8'))
    client.disconnect()
    

