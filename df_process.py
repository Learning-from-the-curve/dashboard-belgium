import pandas as pd
import numpy as np
import datetime
import json
import pickle
from pathlib import Path
from difflib import SequenceMatcher
from pickle_functions import *
from functions import *

path_input = Path.cwd() / 'input'
Path.mkdir(path_input, exist_ok = True)
path_life_table_BE = Path.cwd() / 'input' / 'sterftetafelsAE.xls'
path_geo_BE = Path.cwd() / 'input' / 'municipalities-belgium.geojson'
path_deaths_BE = Path.cwd() / 'input' / 'TF_DEATHS.xlsx'
path_pop_BE = Path.cwd() / 'input' / 'pop_muniBE.xlsx'
path_life_table_BE = Path.cwd() / 'input' / 'sterftetafelsAE.xls'

url_epistat = 'https://epistat.sciensano.be/Data/COVID19BE.xlsx'

BE_data_cases = clean_data_be(url_epistat, cases = True, hosp = False, deaths = False)
BE_data_hosp = clean_data_be(url_epistat, cases = False, hosp = True, deaths = False)
BE_data_cases['CASES'] = BE_data_cases.groupby(['DATE', 'PROVINCE'])['CASES'].sum()
BE_data_cases = BE_data_cases.groupby(['DATE','PROVINCE']).first()
BE_data_cases = BE_data_cases[['CASES']]
BE_data_cases = BE_data_cases.rename(columns={"CASES": "Cases"})
BE_data_hosp['Released from hospital'] = BE_data_hosp.groupby(['PROVINCE'])['NEW_OUT'].cumsum()
BE_data_hosp['Total hospitalized'] = BE_data_hosp.groupby(['PROVINCE'])['NEW_IN'].cumsum()
BE_data_hosp = BE_data_hosp.rename(columns={"TOTAL_IN": "Hospitalized", 'TOTAL_IN_ICU': 'ICU', 'TOTAL_IN_RESP': 'Respiratory'})
BE_data_hosp = BE_data_hosp.reset_index()
BE_data_hosp = BE_data_hosp.rename(columns={"index": "DATE"})
BE_data_hosp['DATE'] = BE_data_hosp['DATE'].astype('str')
BE_data_hosp = BE_data_hosp.set_index(['DATE','PROVINCE'])
BE_total_prov = BE_data_cases.merge(BE_data_hosp, left_index = True, right_index = True, how='outer')
BE_total_prov['Cases'] = BE_total_prov['Cases'].fillna(0.0)
BE_total_prov.insert(loc = 2, column = 'Cumulative cases', value = BE_total_prov.groupby(['PROVINCE'])['Cases'].cumsum())
BE_total_prov_merged = BE_total_prov.reset_index('PROVINCE').copy()
BE_total_merged = BE_total_prov_merged.copy()
BE_total_merged['PROVINCE'] = 'Belgium'
BE_total_merged = BE_total_merged.groupby(level = 0).sum(min_count = 1)
BE_data_deaths = clean_data_be(url_epistat, cases = False, hosp = False, deaths = True)
BE_total_deaths = cum_deaths_by_date(BE_data_deaths)
BE_total_merged = BE_total_merged.merge(BE_total_deaths, left_index = True, right_index = True, how='outer')
for date in set(BE_total_prov_merged.index):
    for var in ['Cumulative cases', 'Released from hospital', 'Total hospitalized']:
        temp_data = BE_total_prov_merged[var].loc[date].reset_index()
        for i in range(len(temp_data[var])):
            if np.isnan(temp_data.iloc[i][var]):
                BE_total_merged.at[date, var] = np.nan

available_provinces = ['Belgium']
for prov in sorted(set(BE_total_prov_merged['PROVINCE'])):
    available_provinces.append(prov)

BE_reg_deaths = clean_data_be(url_epistat, cases = False, hosp = False, deaths = True)
BE_reg_cases = clean_data_be(url_epistat, cases = True, hosp = False, deaths = False)

BE_reg_pop = pd.read_excel(path_pop_BE, sheet_name = 'Bevolking in 2019', header = [1])
BE_reg_pop = BE_reg_pop.loc[(BE_reg_pop['Woonplaats'] == 'Vlaams Gewest') | (BE_reg_pop['Woonplaats'] == 'Waals Gewest') | (BE_reg_pop['Woonplaats'] == 'Brussels Hoofdstedelijk Gewest')]
BE_reg_pop = BE_reg_pop.rename(columns = {'Woonplaats': 'Region', 'Mannen': 'Male', 'Vrouwen': 'Female', 'Totaal': 'Total'})
BE_reg_pop['Region'].loc[BE_reg_pop['Region'] == 'Vlaams Gewest'] = 'Flanders'
BE_reg_pop['Region'].loc[BE_reg_pop['Region'] == 'Waals Gewest'] = 'Wallonia'
BE_reg_pop['Region'].loc[BE_reg_pop['Region'] == 'Brussels Hoofdstedelijk Gewest'] = 'Brussels'

df_reg_male_deaths = BE_reg_deaths.loc[BE_reg_deaths['SEX'] == 'M'].copy()
df_reg_female_deaths = BE_reg_deaths.loc[BE_reg_deaths['SEX'] == 'F'].copy()

df_reg_male_cases = BE_reg_cases.loc[BE_reg_cases['SEX'] == 'M'].copy()
df_reg_female_cases = BE_reg_cases.loc[BE_reg_cases['SEX'] == 'F'].copy()

BE_reg_total_deaths = aggregate_regions(BE_reg_deaths, 'DEATHS')
BE_reg_total_cases = aggregate_regions(BE_reg_cases, 'CASES')

BE_reg_male_deaths = aggregate_regions(df_reg_male_deaths, 'DEATHS')
BE_reg_female_deaths = aggregate_regions(df_reg_female_deaths, 'DEATHS')

BE_reg_male_cases = aggregate_regions(df_reg_male_cases, 'CASES')
BE_reg_female_cases = aggregate_regions(df_reg_female_cases, 'CASES')

df_epistat_muni = pd.read_excel(url_epistat, sheet_name = 'CASES_MUNI_CUM', usecols = ['CASES', 'TX_DESCR_FR', 'TX_DESCR_NL', 'NIS5'])
df_epistat_muni = df_epistat_muni.loc[df_epistat_muni['TX_DESCR_FR'].isna() == False]
df_epistat_muni = df_epistat_muni.loc[df_epistat_muni['TX_DESCR_NL'].isna() == False]
df_epistat_muni = df_epistat_muni.rename(columns={"TX_DESCR_FR": "name_fr", "TX_DESCR_NL": "name_nl", "NIS5": "NISCode"})
df_epistat_muni['CASES'] = np.where(df_epistat_muni['CASES'] == '<5', '1', df_epistat_muni['CASES'])
df_epistat_muni['CASES'] = pd.to_numeric(df_epistat_muni['CASES'])
df_epistat_muni['NISCode'] = df_epistat_muni['NISCode'].astype(int)
df_epistat_muni['NISCode'] = df_epistat_muni['NISCode'].astype(str)
df_epistat_muni['name_nl'].loc[df_epistat_muni['name_nl'] == 'Puurs-Sint-Amands'] = 'Sint-Amands'
df_epistat_muni['name_nl'].loc[df_epistat_muni['name_nl'] == 'Lievegem'] = 'Waarschoot'
df_epistat_muni['name_nl'].loc[df_epistat_muni['name_nl'] == 'Oudsbergen'] = 'Opglabbeek'
df_epistat_muni['name_nl'].loc[df_epistat_muni['name_nl'] == 'Blegny'] = 'Blégny'
df_epistat_muni['name_nl'].loc[df_epistat_muni['name_nl'] == 'Etalle'] = 'Étalle'
df_epistat_muni['name_nl'].loc[df_epistat_muni['name_nl'] == 'Villers-Le-Bouillet'] = 'Villers-le-Bouillet'
df_epistat_muni['name_nl'].loc[df_epistat_muni['name_nl'] == 'Ecaussinnes'] = 'Écaussinnes'
df_epistat_muni['name_nl'].loc[df_epistat_muni['name_nl'] == 'Pelt'] = 'Neerpelt'
df_epistat_muni = df_epistat_muni.set_index('NISCode')
BE_pop = pd.read_excel(path_pop_BE, sheet_name = 'Bevolking in 2019', header = [1])
BE_pop = BE_pop.loc[BE_pop['NIS code'].isna() == False]
BE_pop = BE_pop.rename(columns={"NIS code": "NISCode"})
BE_pop = BE_pop[:-3]
BE_pop['NISCode'] = BE_pop['NISCode'].astype(int)
BE_pop['NISCode'] = BE_pop['NISCode'].astype(str)
BE_pop = BE_pop.set_index('NISCode')
df_epistat_muni = df_epistat_muni.join(BE_pop)
df_epistat_muni = df_epistat_muni.reset_index()
df_epistat_muni['Infected population (%)'] = ((df_epistat_muni['CASES']/df_epistat_muni['Totaal'])*100).round(2)

with open(path_geo_BE) as f:
    df_muni_geo = json.load(f)
temp_list = []

for i in range(len(df_muni_geo['features'])):
    for index, j in enumerate(df_muni_geo['features'][i]['properties']['name']):
        if j == '#':
            df_muni_geo['features'][i]['properties']['name'] = df_muni_geo['features'][i]['properties']['name'][:index]
    temp_list.append(df_muni_geo['features'][i]['properties']['name'])
temp_list.sort()
temp_list2 = list(df_epistat_muni['name_nl'])
temp_list3 = list(df_epistat_muni['name_fr'])
for i in range(len(temp_list2)):
    temp_string = ''
    for index, j in enumerate(temp_list2[i]):
        temp_string += temp_list2[i][index]
        if index +2 < len(temp_list2[i]) and temp_list2[i][index+1] == ' ' and temp_list2[i][index+2] == '(':
            break
    temp_list2[i] = temp_string
for i in range(len(temp_list3)):
    temp_string = ''
    for index, j in enumerate(temp_list3[i]):
        temp_string += temp_list3[i][index]
        if index +2 < len(temp_list3[i]) and temp_list3[i][index+1] == ' ' and temp_list3[i][index+2] == '(':
            break
    temp_list3[i] = temp_string
for i in range(len(temp_list2)):
    if temp_list2[i] not in temp_list:
        if temp_list3[i] not in temp_list:
            for name in temp_list:
                if SequenceMatcher(None, name, temp_list2[i]).ratio() > 0.7:
                    temp_list2[i] = name
                elif SequenceMatcher(None, name, temp_list3[i]).ratio() > 0.7:
                    temp_list3[i] = name
for i in range(len(temp_list2)):
    if temp_list2[i] not in temp_list and temp_list3[i] in temp_list:
        temp_list2[i] = temp_list3[i]
for i in range(len(temp_list2)):
    if temp_list2[i] not in temp_list:
        pass
        #print('not match')

df_epistat_muni['name'] = temp_list2
df_epistat_muni_clean = df_epistat_muni[['CASES', 'name', 'Infected population (%)']]
df_epistat_muni_clean = df_epistat_muni_clean.set_index('name')
df_epistat_muni_clean.loc['Knesselare'] = [df_epistat_muni_clean.loc['Aalter'][0], df_epistat_muni_clean.loc['Aalter'][1]]
df_epistat_muni_clean.loc['Nevele'] = [df_epistat_muni_clean.loc['Deinze'][0], df_epistat_muni_clean.loc['Deinze'][1]]
df_epistat_muni_clean.loc['Zomergem'] = [df_epistat_muni_clean.loc['Waarschoot'][0], df_epistat_muni_clean.loc['Waarschoot'][1]]
df_epistat_muni_clean.loc['Lovendegem'] = [df_epistat_muni_clean.loc['Waarschoot'][0], df_epistat_muni_clean.loc['Waarschoot'][1]]
df_epistat_muni_clean.loc['Zingem'] = [df_epistat_muni_clean.loc['Kruishoutem'][0], df_epistat_muni_clean.loc['Kruishoutem'][1]]
df_epistat_muni_clean.loc['Meeuwen-Gruitrode'] = [df_epistat_muni_clean.loc['Opglabbeek'][0], df_epistat_muni_clean.loc['Opglabbeek'][1]]
df_epistat_muni_clean.loc['Overpelt'] = [df_epistat_muni_clean.loc['Neerpelt'][0], df_epistat_muni_clean.loc['Neerpelt'][1]]
df_epistat_muni_clean.loc['Puers'] = [df_epistat_muni_clean.loc['Sint-Amands'][0], df_epistat_muni_clean.loc['Sint-Amands'][1]]
df_epistat_muni_clean = df_epistat_muni_clean.reset_index()
df_epistat_muni_clean = df_epistat_muni_clean.rename(columns={"name": "Municipality", "CASES": "Number cases"})
df_epistat_muni_clean['Number cases (ln)'] = np.log(df_epistat_muni_clean['Number cases']).round(2)

# Draw weekly mortality

BE_weekly_deaths = clean_data_be(data_path = url_epistat, cases = False, hosp = False, deaths = True)
BE_weekly_deaths['DEATHS'] = BE_weekly_deaths.groupby(level = 0)['DEATHS'].sum().round(2)
BE_weekly_deaths = BE_weekly_deaths.groupby(level = 0).first()
BE_weekly_deaths = BE_weekly_deaths.reset_index()
BE_weekly_deaths['DATE'] = pd.to_datetime(BE_weekly_deaths['DATE'], format = '%Y-%m-%d')
BE_weekly_deaths['month'] = BE_weekly_deaths['DATE'].dt.month
BE_weekly_deaths['day'] = BE_weekly_deaths['DATE'].dt.day
BE_weekly_deaths = BE_weekly_deaths[:-2][['month','day','DEATHS']]

BE_deaths_bydate = pd.read_excel(path_deaths_BE)
BE_deaths_bydate['year'] = BE_deaths_bydate['DT_DATE'].dt.year
BE_deaths_bydate['month'] = BE_deaths_bydate['DT_DATE'].dt.month
BE_deaths_bydate['day'] = BE_deaths_bydate['DT_DATE'].dt.day

BE_deaths_bydate = BE_deaths_bydate[(BE_deaths_bydate['year'] >= 2015) & (BE_deaths_bydate['year'] <= 2017)]
BE_deaths_bydate = BE_deaths_bydate[(BE_deaths_bydate['month'] != 2) | (BE_deaths_bydate['day'] != 29)]
BE_deaths_bydate = BE_deaths_bydate.set_index(['month', 'day'])
BE_deaths_bydate['mean_MS_NUM_DEATHS'] = BE_deaths_bydate.groupby(['month', 'day'])['MS_NUM_DEATHS'].mean().round(2)
BE_deaths_bydate = BE_deaths_bydate.reset_index()
BE_deaths_bydate = BE_deaths_bydate[BE_deaths_bydate['year'] == 2017]
BE_deaths_bydate = BE_deaths_bydate[['month','day', 'mean_MS_NUM_DEATHS', 'DT_DATE']]
BE_deaths_bydate['short_date'] = [f'{m}-{d}' for m, d in zip(BE_deaths_bydate['month'], BE_deaths_bydate['day'])]

BE_excess_mortality = BE_deaths_bydate.merge(BE_weekly_deaths, on = ['month', 'day'], how = 'left')
BE_excess_mortality['weeks'] = 0
week_index = 1
counter = 0
for i in range(len(BE_excess_mortality['short_date'])):
    BE_excess_mortality.at[counter, 'weeks'] = week_index
    counter += 1
    if counter % 7 == 0:
        week_index += 1

BE_excess_mortality = BE_excess_mortality.set_index('weeks')
BE_excess_mortality['Weekly COVID-19 deaths'] = BE_excess_mortality.groupby(level = 0)['DEATHS'].sum(min_count = 1).round(2)
BE_excess_mortality['Weekly average (2015-2017) deaths'] = BE_excess_mortality.groupby(level = 0)['mean_MS_NUM_DEATHS'].sum().round(2)

for year in ['2015', '2016', '2017', '2018']:
    life_table = pd.read_excel(path_life_table_BE, sheet_name = year, header = None)
    life_table = life_table[[0, 6, 13, 20]]
    life_table = life_table.rename(columns={0: "age", 6: "surv_male", 13: "surv_female", 20: "surv_all"})
    life_table['age'].loc[life_table['age'] == '105+'] = '105'
    life_table = life_table.loc[life_table['age'].isna() == False]
    life_table = life_table[1:]
    life_table['age'] = life_table['age'].astype(int)
    life_table = life_table.astype('float')
    for sex in ['male', 'female', 'all']:
        life_table['density_' + sex] = 1 - life_table['surv_' + sex]/1000000
    if year == '2015':
        life_table_2015 = life_table.copy()
    if year == '2016':
        life_table_2016 = life_table.copy()
    if year == '2017':
        life_table_2017 = life_table.copy()
    if year == '2018':
        life_table_2018 = life_table.copy()
life_table = pd.concat([life_table_2015, life_table_2016, life_table_2017], ignore_index = True)
life_table = life_table.set_index('age')
for sex in ['male', 'female', 'all']:
    life_table['avg_density_' + sex] = life_table.groupby(level = 0)['density_' + sex].mean()
life_table = life_table.groupby(level = 0).last()
life_table = life_table.reset_index()
life_table_cont = life_table.copy()
life_table_cont = life_table_cont[['age', 'avg_density_male', 'avg_density_female', 'avg_density_all']]
life_table_cont = life_table_cont.round(2)
life_table['age'][(life_table['age'] >= 0) & (life_table['age'] <= 24)] = 12
life_table['age'][(life_table['age'] >= 25) & (life_table['age'] <= 44)] = 30
life_table['age'][(life_table['age'] >= 45) & (life_table['age'] <= 64)] = 50
life_table['age'][(life_table['age'] >= 65) & (life_table['age'] <= 74)] = 70
life_table['age'][(life_table['age'] >= 85) & (life_table['age'] <= 94)] = 90
life_table['age'][(life_table['age'] >= 95)] = 90
life_table = life_table.set_index('age')
life_table = life_table.drop(labels = [x for x in range(75, 80, 1)])
life_table = life_table.drop(labels = [x for x in range(81, 85, 1)])
life_table_discrete = life_table[['avg_density_male', 'avg_density_female', 'avg_density_all']]
life_table_discrete = life_table_discrete.round(2)
life_table_discrete = life_table_discrete.groupby(level = 0).last()

BE_deaths_lifetable = pd.read_excel(url_epistat, sheet_name = 'MORT')


dataframe_list = [
    [BE_total_prov_merged, 'BE_total_prov_merged'],
    [BE_total_merged, 'BE_total_merged'],
    [BE_reg_total_deaths, 'BE_reg_total_deaths'],
    [BE_reg_total_cases, 'BE_reg_total_cases'],
    [BE_reg_male_deaths, 'BE_reg_male_deaths'],
    [BE_reg_female_deaths, 'BE_reg_female_deaths'],
    [BE_reg_male_cases, 'BE_reg_male_cases'],
    [BE_reg_female_cases, 'BE_reg_female_cases'],
    [BE_reg_pop, 'BE_reg_pop'],
    [df_epistat_muni_clean, 'df_epistat_muni_clean'],
    [df_muni_geo, 'df_muni_geo'],
    [BE_excess_mortality, 'BE_excess_mortality'],
    [BE_total_prov_merged, 'BE_total_prov_merged'],
    [available_provinces, 'available_provinces'],
    [life_table_discrete, 'life_table_discrete'],
    [BE_deaths_lifetable, 'BE_deaths_lifetable']
    ]

for dataframe, name in dataframe_list:
    picklify(dataframe, name)
