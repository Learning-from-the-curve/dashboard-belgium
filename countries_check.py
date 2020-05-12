import pandas as pd
import numpy as np
import pickle

from app import adjust_names, aggregate_countries
from pathlib import Path

url_confirmed = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
df_confirmed = pd.read_csv(url_confirmed)

df_confirmed = adjust_names(df_confirmed)
df_confirmed = aggregate_countries(df_confirmed, graph = 'scatter')


set_countries_JH = open('input/set_countries_JH.txt', 'wb')
pickle.dump(set(df_confirmed['Country/Region']), set_countries_JH)
set_countries_JH.close()
