import time
import pandas as pd

def unix(timestamp, unit='s'):
    return (pd.to_datetime([timestamp], unit=unit).astype(int) / 10**6)[0]
def stamp(timestamp):
    return (pd.to_datetime([timestamp]).astype(int) / 10**6)[0]

minute = 60000
hour = minute*60
day = hour*24
week = day*7
