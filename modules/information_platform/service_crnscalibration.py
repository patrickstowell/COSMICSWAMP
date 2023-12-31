from fastapi import FastAPI, Header, Request, APIRouter, Depends, HTTPException, Query

from typing import Union, Annotated, List, Any, Dict, AnyStr, Union
JSONStructure = Union[Dict[str, Any], List[Any]]

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
import dependencies.log_utils as log

import modules.iot_platform.cosmicswamp as cosmicswamp

import modules.information_platform.configuration as configuration
import modules.information_platform.managementzone as managementzone

################################################
# MODULE ROUTER
################################################
router = APIRouter(
    prefix="/information-platform/crns-calibration",
    tags=["information-platform","crns-calibration"],
    dependencies=[Depends(configuration.settings)]
)
router.verbosity = log.DEBUG

@router.post("/simple-crspy")
def simple_crspy(request: Request,
                    entity_id,                    
                    N: float = 0.0,
                    N0: float = 0.0,
                    method: str = "default",
                    P: float = 0.0,
                    T: float = 0.0,
                    RH: float = 0.0,
                    CR: float = 0.0,
                    BETA: float = 130.0,
                    P0: float = 1000.0,
                    CR0: float = 135.0,
                    BD: float = 1.2,
                    LW: float = 0.0,
                    AGB: float = 0.0,
                    BGB: float = 0.0,
                    NENSEMBLE: int = 30,
                    jsondata: dict = None
                    ):
    
    # Fall back cosmic ray processing scripts if more robust servers not available.
    # Runs 30 variations to estimate soil moisture uncertainty assuming no
    # uncertainties on other parameters
    ensemble_data = []

    for i in range(NENSEMBLE):
            
        # Assume all data is in the body
        body = {}
        if jsondata: body = jsondata
        if P:    body["P"] = P
        if T:    body["T"] = T
        if RH:   body["RH"] = RH
        if N0:   body["N0"] = N0
        if N:    body["N"]  = N + (i!=0) * np.sqrt(N)
        if BETA: body["BETA"] = BETA
        if CR:   body["CR"] = CR
        if P0:   body["P0"] = P0
        if LW:   body["LW"] = LW
        if AGB:  body["AGB"] = AGB
        if BGB:  body["BGB"] = BGB
        if CR0:  body["CR0"] = CR0
        if BD:   body["BD"] = BD

        for var in ["LW","AGB","BGB"]:
            if var not in body: body[var] = 0.0

        body["HBKG"] = body["LW"] + body["AGB"] + body["BGB"]

        # Validation
        values = "P,T,RH,CR,N,N0"
        for var in values.split(","):
            if var not in body:
                return {"error":"Value {var} missing from body. Require : {values}"}
            
        if body["N0"] <= 0.0:
            return {"error":"N0 Value needs to be greater than 0.0"}
        
        if body["N"] <= 0.0:
            return {"error":"N Value needs to be greater than 0.0"}
        
        # Calculate corrections
        body["f_P"] = np.exp((-1.0/130.0) * (P-1010))
        body["f_T"] = 1.0
        body["f_C"] = body["CR"]/body["CR0"] 

        # Apply corrections
        body["N_C"] = body["f_P"]*body["f_T"]*body["f_C"]*body["N"] / body["N0"]

        # Simple extraction
        body["RELSM"]   = body["N_C"]
        body["theta_N"] = body["RELSM"]*body["BD"]

        # Subtraction of hydrogen backgrounds
        body["theta_F"] = body["theta_N"] - body["HBKG"]

        # Add to our ensembles
        ensemble_data.append(body)

    # Make a df for everaging ensembles
    df = pd.DataFrame(ensemble_data)

    # Make some aliases
    df["TSM"] = df["theta_F"]
    df["VWC"] = df["theta_F"]

    # Get quantiles
    mean = df.mean()
    lowperc = df.quantile(0.25)
    highperc = df.quantile(0.95)
    error = (highperc-lowperc)/2

    # Fill response
    final_body = {}
    for key in ensemble_data[0]:
        final_body[key] = ensemble_data[0][key]
        final_body[key + "_low"] = lowperc[key]
        final_body[key + "_high"] = highperc[key]
        final_body[key + "_err"] = error[key]

    return final_body

    
    
