# src/data_loading.py
import os
import pandas as pd
import geopandas as gpd
from functools import lru_cache

DATA_DIR = 'data/raw'
YEARS = [2020, 2021, 2022, 2023, 2024]

@lru_cache(maxsize=10)
def load_surgical_data(year):
    file = os.path.join(DATA_DIR, f'Uganda Surgical Procedures_raw data_{year}.csv')
    return pd.read_csv(file)

@lru_cache(maxsize=1)
def load_population_data():
    pop_file = os.path.join(DATA_DIR, 'Uganda Population Data 2024', 'Population by district_census 2024.xlsx')
    return pd.read_excel(pop_file)

@lru_cache(maxsize=1)
def load_facility_metadata():
    fac_file = os.path.join(DATA_DIR, 'Uganda_Shape_files_2020', 'GEO MFL SURVEY DATASET.xlsx')
    return pd.read_excel(fac_file)

@lru_cache(maxsize=1)
def load_shapefile():
    shp_file = os.path.join(DATA_DIR, '..', 'Uganda_Shape_files_2020', 'Region', 'UDHS_Regions_2019.shp')
    return gpd.read_file(shp_file)
