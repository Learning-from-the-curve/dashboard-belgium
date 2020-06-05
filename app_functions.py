import pandas as pd
import numpy as np
import datetime
import json
from pathlib import Path
from difflib import SequenceMatcher

def clean_data_be(data_path: str, cases: bool, hosp: bool, deaths: bool):
    if cases:
        BE_data = pd.read_excel(data_path, sheet_name = 'CASES_AGESEX')
    elif hosp:
        BE_data = pd.read_excel(data_path, sheet_name = 'HOSP')
    elif deaths:
        BE_data = pd.read_excel(data_path, sheet_name = 'MORT')
    if cases or hosp:
        BE_data['PROVINCE'].loc[BE_data['PROVINCE'] == 'BrabantWallon'] = 'Walloon Brabant'
        BE_data['PROVINCE'].loc[BE_data['PROVINCE'] == 'VlaamsBrabant'] = 'Flemish Brabant'
        BE_data['PROVINCE'].loc[BE_data['PROVINCE'] == 'OostVlaanderen'] = 'East Flanders'
        BE_data['PROVINCE'].loc[BE_data['PROVINCE'] == 'WestVlaanderen'] = 'West Flanders'
        BE_data['PROVINCE'].loc[BE_data['PROVINCE'] == 'Antwerpen'] = 'Antwerp'
    if cases:    
        BE_data = BE_data.loc[BE_data['DATE'].isna() == False]
        BE_data = BE_data.loc[BE_data['PROVINCE'].isna() == False]
    if cases or hosp:
        BE_data = BE_data.set_index(['DATE', 'PROVINCE'])
    else:
        BE_data = BE_data.set_index('DATE')
    return BE_data

def cum_deaths_by_date(BE_data):
    BE_data['deaths_day'] = BE_data.groupby(level = 0)['DEATHS'].sum()
    BE_data = BE_data.groupby(level = 0).first()
    BE_data['deaths_cum'] = BE_data['deaths_day'].cumsum()
    BE_data = BE_data[['deaths_cum']]
    BE_data = BE_data.rename(columns={'deaths_cum': 'Deceased'})
    return BE_data

def ticks_log(df, var):
    temp_max = 0
    label_max = []
    text_label_max = []
    tick = 1
    df= df.reset_index()
    if temp_max < df[var].max():
        temp_max = df[var].max()
    print(temp_max)
    while tick < temp_max*(0.50):
        label_max.append(tick)
        text_label_max.append(f'{tick:,}')
        tick *= 10
    label_max.append(temp_max)
    text_label_max.append(f'{temp_max:,}')
    return label_max, text_label_max

def aggregate_regions(df, var):
    df_reg_total = df.copy()
    df_reg_total = df_reg_total.reset_index()
    df_reg_total = df_reg_total.set_index(['DATE', 'REGION'])
    df_reg_total[var] = df_reg_total.groupby(['DATE', 'REGION'])[var].sum()
    df_reg_total = df_reg_total.groupby(['DATE', 'REGION']).first()
    df_reg_total = df_reg_total.reset_index('DATE')
    df_reg_total = df_reg_total[['DATE', var]]
    df_reg_total[var] = df_reg_total.groupby(level = 0)[var].cumsum()
    return df_reg_total
