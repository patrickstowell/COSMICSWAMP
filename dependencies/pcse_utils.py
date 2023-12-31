# -*- coding: utf-8 -*-
# Copyright (c) 2004-2018 Alterra, Wageningen-UR
# Allard de Wit (allard.dewit@wur.nl), July 2018
import os
import datetime as dt

import numpy as np
import pandas as pd
import requests

from ..base import WeatherDataProvider, WeatherDataContainer
from ..util import ea_from_tdew, reference_ET, check_angstromAB
from ..exceptions import PCSEError
from ..settings import settings

# Define some lambdas to take care of unit conversions.
MJ_to_J = lambda x: x * 1e6
mm_to_cm = lambda x: x / 10.
tdew_to_hpa = lambda x: ea_from_tdew(x) * 10.
to_date = lambda d: d.date()


class PandasWeatherDataProvider(WeatherDataProvider):

    # Variable names in POWER data
    power_variables_old = ["ALLSKY_TOA_SW_DWN", "ALLSKY_SFC_SW_DWN", "T2M", "T2M_MIN",
                       "T2M_MAX", "T2MDEW", "WS2M", "PRECTOT"]
    power_variables = ["TOA_SW_DWN", "ALLSKY_SFC_SW_DWN", "T2M", "T2M_MIN",
                       "T2M_MAX", "T2MDEW", "WS2M", "PRECTOTCORR"]
    # other constants
    HTTP_OK = 200
    angstA = 0.29
    angstB = 0.49

    def __init__(self, latitude, longitude, df, ETmodel="PM"):

        WeatherDataProvider.__init__(self)

        if latitude < -90 or latitude > 90:
            msg = "Latitude should be between -90 and 90 degrees."
            raise ValueError(msg)
        if longitude < -180 or longitude > 180:
            msg = "Longitude should be between -180 and 180 degrees."
            raise ValueError(msg)

        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.ETmodel = ETmodel
        self.dataframe = df

        msg = "Retrieving weather data from Pandas Provided for lat/lon: (%f, %f)."
        self.logger.info(msg % (self.latitude, self.longitude))

        if "DAY" in df.columns:
            df.set_index("DAY")

        for day in df.index:
            print(day)
            self._store[(day,0)] = {}
            wdc = WeatherDataContainer(LAT=self.latitude, LON=self.longitude, ELEV=self.elevation, **row)
            self._store_WeatherDataContainer(wdc, day)

        

    def _get_and_process_NASAPower(self, latitude, longitude):
        """Handles the retrieval and processing of the NASA Power data
        """
        powerdata = self._query_NASAPower_server(latitude, longitude)
        if not powerdata:
            msg = "Failure retrieving POWER data from server. This can be a connection problem with " \
                  "the NASA POWER server, retry again later."
            raise RuntimeError(msg)

        # Store the informational header then parse variables
        self.description = [powerdata["header"]["title"]]
        self.elevation = float(powerdata["geometry"]["coordinates"][2])
        df_power = self._process_POWER_records(powerdata)

        # Determine Angstrom A/B parameters
        self.angstA, self.angstB = self._estimate_AngstAB(df_power)

        # Convert power records to PCSE compatible structure
        df_pcse = self._POWER_to_PCSE(df_power)

        # Start building the weather data containers
        self._make_WeatherDataContainers(df_pcse.to_dict(orient="records"))

        # dump contents to a cache file
        cache_filename = self._get_cache_filename(latitude, longitude)
        self._dump(cache_filename)

    def _estimate_AngstAB(self, df_power):
        """Determine Angstrom A/B parameters from Top-of-Atmosphere (ALLSKY_TOA_SW_DWN) and
        top-of-Canopy (ALLSKY_SFC_SW_DWN) radiation values.

        :param df_power: dataframe with POWER data
        :return: tuple of Angstrom A/B values

        The Angstrom A/B parameters are determined by dividing swv_dwn by toa_dwn
        and taking the 0.05 percentile for Angstrom A and the 0.98 percentile for
        Angstrom A+B: toa_dwn*(A+B) approaches the upper envelope while
        toa_dwn*A approaches the lower envelope of the records of swv_dwn
        values.
        """

        msg = "Start estimation of Angstrom A/B values from POWER data."
        self.logger.debug(msg)

        # check if sufficient data is available to make a reasonable estimate:
        # As a rule of thumb we want to have at least 200 days available
        if len(df_power) < 200:
            msg = ("Less then 200 days of data available. Reverting to " +
                   "default Angstrom A/B coefficients (%f, %f)")
            self.logger.warn(msg % (self.angstA, self.angstB))
            return self.angstA, self.angstB

        # calculate relative radiation (swv_dwn/toa_dwn) and percentiles
        relative_radiation = df_power.ALLSKY_SFC_SW_DWN/df_power.TOA_SW_DWN
        ix = relative_radiation.notnull()
        angstrom_a = float(np.percentile(relative_radiation[ix].values, 5))
        angstrom_ab = float(np.percentile(relative_radiation[ix].values, 98))
        angstrom_b = angstrom_ab - angstrom_a

        try:
            check_angstromAB(angstrom_a, angstrom_b)
        except PCSEError as e:
            msg = ("Angstrom A/B values (%f, %f) outside valid range: %s. " +
                   "Reverting to default values.")
            msg = msg % (angstrom_a, angstrom_b, e)
            self.logger.warn(msg)
            return self.angstA, self.angstB

        msg = "Angstrom A/B values estimated: (%f, %f)." % (angstrom_a, angstrom_b)
        self.logger.debug(msg)

        return angstrom_a, angstrom_b

    def _query_NASAPower_server(self, latitude, longitude):
        """Query the NASA Power server for data on given latitude/longitude
        """

        start_date = dt.date(1983,7,1)
        end_date = dt.date.today()

        # build URL for retrieving data, using new NASA POWER api
        server = "https://power.larc.nasa.gov/api/temporal/daily/point"
        payload = {"request": "execute",
                   "parameters": ",".join(self.power_variables),
                   "latitude": latitude,
                   "longitude": longitude,
                   "start": start_date.strftime("%Y%m%d"),
                   "end": end_date.strftime("%Y%m%d"),
                   "community": "AG",
                   "format": "JSON",
                   "user": "anonymous"
                   }
        msg = "Starting retrieval from NASA Power"
        self.logger.debug(msg)
        req = requests.get(server, params=payload)

        if req.status_code != self.HTTP_OK:
            msg = ("Failed retrieving POWER data, server returned HTTP " +
                   "code: %i on following URL %s") % (req.status_code, req.url)
            raise PCSEError(msg)

        msg = "Successfully retrieved data from NASA Power"
        self.logger.debug(msg)
        return req.json()

    def _find_cache_file(self, latitude, longitude):
        """Try to find a cache file for given latitude/longitude.

        Returns None if the cache file does not exist, else it returns the full path
        to the cache file.
        """
        cache_filename = self._get_cache_filename(latitude, longitude)
        if os.path.exists(cache_filename):
            return cache_filename
        else:
            return None

    def _get_cache_filename(self, latitude, longitude):
        """Constructs the filename used for cache files given latitude and longitude

        The latitude and longitude is coded into the filename by truncating on
        0.1 degree. So the cache filename for a point with lat/lon 52.56/-124.78 will be:
        NASAPowerWeatherDataProvider_LAT00525_LON-1247.cache
        """

        fname = "%s_LAT%05i_LON%05i.cache" % (self.__class__.__name__,
                                              int(latitude*10), int(longitude*10))
        cache_filename = os.path.join(settings.METEO_CACHE_DIR, fname)
        return cache_filename

    def _write_cache_file(self):
        """Writes the meteo data from NASA Power to a cache file.
        """
        cache_filename = self._get_cache_filename(self.latitude, self.longitude)
        try:
            self._dump(cache_filename)
        except (IOError, EnvironmentError) as e:
            msg = "Failed to write cache to file '%s' due to: %s" % (cache_filename, e)
            self.logger.warning(msg)

    def _load_cache_file(self):
        """Loads the data from the cache file. Return True if successful.
        """
        cache_filename = self._get_cache_filename(self.latitude, self.longitude)
        try:
            self._load(cache_filename)
            msg = "Cache file successfully loaded."
            self.logger.debug(msg)
            return True
        except (IOError, EnvironmentError, EOFError) as e:
            msg = "Failed to load cache from file '%s' due to: %s" % (cache_filename, e)
            self.logger.warning(msg)
            return False

    def _make_WeatherDataContainers(self, recs):
        """Create a WeatherDataContainers from recs, compute ET and store the WDC's.
        """

        for rec in recs:
            # Reference evapotranspiration in mm/day
            try:
                E0, ES0, ET0 = reference_ET(rec["DAY"], rec["LAT"], rec["ELEV"], rec["TMIN"], rec["TMAX"], rec["IRRAD"],
                                            rec["VAP"], rec["WIND"], self.angstA, self.angstB, self.ETmodel)
            except ValueError as e:
                msg = (("Failed to calculate reference ET values on %s. " % rec["DAY"]) +
                       ("With input values:\n %s.\n" % str(rec)) +
                       ("Due to error: %s" % e))
                raise PCSEError(msg)

            # update record with ET values value convert to cm/day
            rec.update({"E0": E0/10., "ES0": ES0/10., "ET0": ET0/10.})

            # Build weather data container from dict 't'
            wdc = WeatherDataContainer(**rec)

            # add wdc to dictionary for thisdate
            self._store_WeatherDataContainer(wdc, wdc.DAY)

    def _process_POWER_records(self, powerdata):
        """Process the meteorological records returned by NASA POWER
        """
        msg = "Start parsing of POWER records from URL retrieval."
        self.logger.debug(msg)

        fill_value = float(powerdata["header"]["fill_value"])

        df_power = {}
        for varname in self.power_variables:
            s = pd.Series(powerdata["properties"]["parameter"][varname])
            s[s == fill_value] = np.NaN
            df_power[varname] = s
        df_power = pd.DataFrame(df_power)
        df_power["DAY"] = pd.to_datetime(df_power.index, format="%Y%m%d")

        # find all rows with one or more missing values (NaN)
        ix = df_power.isnull().any(axis=1)
        # Get all rows without missing values
        df_power = df_power[~ix]

        return df_power

    def _POWER_to_PCSE(self, df_power):

        # Convert POWER data to a dataframe with PCSE compatible inputs
        df_pcse = pd.DataFrame({"TMAX": df_power.T2M_MAX,
                                "TMIN": df_power.T2M_MIN,
                                "TEMP": df_power.T2M,
                                "IRRAD": df_power.ALLSKY_SFC_SW_DWN.apply(MJ_to_J),
                                "RAIN": df_power.PRECTOTCORR.apply(mm_to_cm),
                                "WIND": df_power.WS2M,
                                "VAP": df_power.T2MDEW.apply(tdew_to_hpa),
                                "DAY": df_power.DAY.apply(to_date),
                                "LAT": self.latitude,
                                "LON": self.longitude,
                                "ELEV": self.elevation})

        return df_pcse
