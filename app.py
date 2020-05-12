import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import datetime
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table as dt

from dash.dependencies import Input, Output, State
from pathlib import Path
from difflib import SequenceMatcher

path_input = Path.cwd() / 'input'
Path.mkdir(path_input, exist_ok = True)
path_life_table_BE = Path.cwd() / 'input' / 'sterftetafelsAE.xls'
path_geo_BE = Path.cwd() / 'input' / 'municipalities-belgium.geojson'
path_deaths_BE = Path.cwd() / 'input' / 'TF_DEATHS.xlsx'
path_pop_BE = Path.cwd() / 'input' / 'pop_muniBE.xlsx'

#####################################################################################################################################
# Boostrap CSS and font awesome . Option 1) Run from codepen directly Option 2) Copy css file to assets folder and run locally
#####################################################################################################################################
external_stylesheets = [dbc.themes.FLATLY]

#Insert your javascript here. In this example, addthis.com has been added to the web app for people to share their webpage

app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

app.title = 'COVID-19 - Belgium dashboard'

#for heroku to run correctly
server = app.server

#Overwrite your CSS setting by including style locally

######################################
# Retrieve data
######################################

# get data directly from github. The data source provided by Johns Hopkins University.
url_epistat = 'https://epistat.sciensano.be/Data/COVID19BE.xlsx'

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

def life_expectancy(path_life_table_BE: str, url_epistat: str, line_plot):
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
    plots = []
    if line_plot == 'COVID-19 deaths, all':
        BE_deaths = pd.read_excel(url_epistat, sheet_name = 'MORT')
        BE_deaths = BE_deaths.loc[BE_deaths['AGEGROUP'].isna() == False]
        BE_deaths = BE_deaths.set_index('AGEGROUP')
        BE_deaths['deaths_by_age'] = BE_deaths.groupby(level = 0)['DEATHS'].sum()
        BE_deaths = BE_deaths.groupby(level = 0).first()
        BE_deaths = BE_deaths[['DEATHS', 'deaths_by_age']]
        BE_deaths['cum_deaths'] = BE_deaths['deaths_by_age'].cumsum()
        BE_deaths['tot_deaths'] = BE_deaths['deaths_by_age'].sum()
        BE_deaths['cdf_deaths'] = BE_deaths['cum_deaths']/BE_deaths['tot_deaths']
        BE_deaths = BE_deaths.reset_index()
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '0-24'] = '12'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '25-44'] = '30'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '45-64'] = '50'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '65-74'] = '70'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '75-84'] = '80'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '85+'] = '90'
        BE_deaths['cdf_deaths'] = BE_deaths['cdf_deaths'].round(2)
        trace = go.Scatter(y = life_table_discrete['avg_density_all'], x = life_table_discrete.index, mode = 'lines+markers', name = 'Life expectancy (all)', line = dict(width = 3),
                                marker = dict(size = 6, line = dict(width = 1,color = 'DarkSlateGrey')),
                                hovertemplate=
                                "Probability: %{y:.2f}<br>" +
                                "Age: %{x}<br>" +
                                "<extra></extra>",
                            )
        plots.append(trace)
        trace = go.Scatter(y = BE_deaths['cdf_deaths'], x = BE_deaths['AGEGROUP'], mode = 'lines+markers', name = 'COVID-19 deaths (all)', line = dict(width = 3),
                                marker = dict(size = 6, line = dict(width = 1,color = 'DarkSlateGrey')),
                                hovertemplate=
                                "Probability: %{y:.2f}<br>" +
                                "Age: %{x}<br>" +
                                "<extra></extra>",
                            )
        plots.append(trace)
    elif line_plot == 'COVID-19 deaths, female' or line_plot == 'COVID-19 deaths, male':
        BE_deaths = pd.read_excel(url_epistat, sheet_name = 'MORT')
        BE_deaths = BE_deaths.loc[BE_deaths['AGEGROUP'].isna() == False]
        BE_deaths = BE_deaths.set_index(['SEX', 'AGEGROUP'])
        BE_deaths['sum_deaths'] = BE_deaths.groupby(level=['SEX','AGEGROUP'])['DEATHS'].sum()
        BE_deaths = BE_deaths.groupby(level=['SEX','AGEGROUP']).first()
        BE_deaths = BE_deaths.reset_index('AGEGROUP')
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '0-24'] = '12'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '25-44'] = '30'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '45-64'] = '50'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '65-74'] = '70'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '75-84'] = '80'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '85+'] = '90'
        BE_deaths_clean = BE_deaths[['AGEGROUP', 'sum_deaths']]
        BE_deaths_clean = BE_deaths_clean.reset_index('SEX')
        new_row = {'AGEGROUP': '12', 'SEX':'M', 'sum_deaths':0}
        BE_deaths_clean = BE_deaths_clean.append(new_row, ignore_index=True)
        BE_deaths_clean = BE_deaths_clean.set_index(['SEX', 'AGEGROUP'])
        BE_deaths_clean = BE_deaths_clean.sort_index(level = ['SEX', 'AGEGROUP'])
        BE_deaths_clean['cum_deaths'] = BE_deaths_clean.groupby(level=['SEX'])['sum_deaths'].cumsum()
        BE_deaths_clean = BE_deaths_clean.reset_index(['AGEGROUP'])
        BE_deaths_clean['tot_deaths'] = BE_deaths_clean.groupby(level=['SEX'])['sum_deaths'].sum()
        BE_deaths_clean['cdf_deaths'] = BE_deaths_clean['cum_deaths']/BE_deaths_clean['tot_deaths']
        BE_deaths_clean = BE_deaths_clean.reset_index(['SEX'])
        BE_deaths_male = BE_deaths_clean[BE_deaths_clean['SEX'] == 'M']
        BE_deaths_female = BE_deaths_clean[BE_deaths_clean['SEX'] == 'F']
        if line_plot == 'COVID-19 deaths, male':
            trace = go.Scatter(y = life_table_discrete['avg_density_male'], x =life_table_discrete.index, mode = 'lines+markers', name = 'Life expectancy (male)', line = dict(width = 3),
                                    marker = dict(size = 6, line = dict(width = 1,color = 'DarkSlateGrey')),
                                    hovertemplate=
                                    "Probability: %{y:.2f}<br>" +
                                    "Age: %{x}<br>" +
                                    "<extra></extra>",
                                )
            plots.append(trace)
            trace = go.Scatter(y = BE_deaths_male['cdf_deaths'], x = BE_deaths_male['AGEGROUP'], mode = 'lines+markers', name = 'COVID-19 deaths (male)', line = dict(width = 3),
                                    marker = dict(size = 6, line = dict(width = 1,color = 'DarkSlateGrey')),
                                    hovertemplate=
                                    "Probability: %{y:.2f}<br>" +
                                    "Age: %{x}<br>" +
                                    "<extra></extra>",
                                )
            plots.append(trace)
        elif line_plot == 'COVID-19 deaths, female':
            trace = go.Scatter(y = life_table_discrete['avg_density_female'], x = life_table_discrete.index, mode = 'lines+markers', name = 'Life expectancy (female)', line = dict(width = 3),
                                    marker = dict(size = 6, line = dict(width = 1,color = 'DarkSlateGrey')),
                                    hovertemplate=
                                    "Probability: %{y:.2f}<br>" +
                                    "Age: %{x}<br>" +
                                    "<extra></extra>",
                                )
            plots.append(trace)
            trace = go.Scatter(y = BE_deaths_female['cdf_deaths'], x = BE_deaths_female['AGEGROUP'], mode = 'lines+markers', name = 'COVID-19 deaths (female)', line = dict(width = 3),
                                    marker = dict(size = 6, line = dict(width = 1,color = 'DarkSlateGrey')),
                                    hovertemplate=
                                    "Probability: %{y:.2f}<br>" +
                                    "Age: %{x}<br>" +
                                    "<extra></extra>",
                                )
            plots.append(trace)
    elif line_plot == 'COVID-19 deaths, by region':
        BE_deaths = pd.read_excel(url_epistat, sheet_name = 'MORT')
        BE_deaths = BE_deaths.loc[BE_deaths['AGEGROUP'].isna() == False]
        BE_deaths = BE_deaths.set_index(['REGION', 'AGEGROUP'])
        BE_deaths['sum_deaths'] = BE_deaths.groupby(level=['REGION','AGEGROUP'])['DEATHS'].sum()
        BE_deaths = BE_deaths.groupby(level=['REGION','AGEGROUP']).first()
        BE_deaths = BE_deaths.reset_index('AGEGROUP')
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '0-24'] = '12'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '25-44'] = '30'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '45-64'] = '50'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '65-74'] = '70'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '75-84'] = '80'
        BE_deaths['AGEGROUP'].loc[BE_deaths['AGEGROUP'] == '85+'] = '90'
        BE_deaths_clean = BE_deaths[['AGEGROUP', 'sum_deaths']]
        BE_deaths_clean = BE_deaths_clean.reset_index()
        BE_deaths_clean = BE_deaths_clean.set_index(['REGION','AGEGROUP'])
        BE_deaths_clean['cum_deaths'] = BE_deaths_clean.groupby(level=[['REGION']])['sum_deaths'].cumsum()
        BE_deaths_clean = BE_deaths_clean.reset_index(['AGEGROUP'])
        BE_deaths_clean['tot_deaths'] = BE_deaths_clean.groupby(level=['REGION'])['sum_deaths'].sum()
        BE_deaths_clean['cdf_deaths'] = BE_deaths_clean['cum_deaths']/BE_deaths_clean['tot_deaths']
        BE_deaths_clean = BE_deaths_clean.reset_index(['REGION'])
        BE_deaths_brussels = BE_deaths_clean[BE_deaths_clean['REGION'] == 'Brussels']
        BE_deaths_flanders = BE_deaths_clean[BE_deaths_clean['REGION'] == 'Flanders']
        BE_deaths_wallonia = BE_deaths_clean[BE_deaths_clean['REGION'] == 'Wallonia']
        new_row = {'REGION': 'Brussels', 'AGEGROUP': '12', 'sum_deaths':0, 'cum_deaths': 0, 'tot_deaths': 0, 'cdf_deaths': 0.000000}
        BE_deaths_brussels = BE_deaths_brussels.append(new_row, ignore_index=True)
        BE_deaths_brussels = BE_deaths_brussels.sort_values(by = ['AGEGROUP'])
        new_row = {'REGION': 'Wallonia', 'AGEGROUP': '12', 'sum_deaths':0, 'cum_deaths': 0, 'tot_deaths': 0, 'cdf_deaths': 0.000000}
        BE_deaths_wallonia = BE_deaths_wallonia.append(new_row, ignore_index=True)
        BE_deaths_wallonia = BE_deaths_wallonia.sort_values(by = ['AGEGROUP'])
        trace = go.Scatter(y = BE_deaths_brussels['cdf_deaths'], x = BE_deaths_brussels['AGEGROUP'], mode = 'lines+markers', name = 'COVID-19 deaths (Brussels)', line = dict(width = 3),
                                marker = dict(size = 6, line = dict(width = 1,color = 'DarkSlateGrey')),
                                hovertemplate=
                                "Probability: %{y:.2f}<br>" +
                                "Age: %{x}<br>" +
                                "<extra></extra>",
                            )
        plots.append(trace)
        trace = go.Scatter(y = BE_deaths_flanders['cdf_deaths'], x = BE_deaths_flanders['AGEGROUP'], mode = 'lines+markers', name = 'COVID-19 deaths (Flanders)', line = dict(width = 3),
                                marker = dict(size = 6, line = dict(width = 1,color = 'DarkSlateGrey')),
                                hovertemplate=
                                "Probability: %{y:.2f}<br>" +
                                "Age: %{x}<br>" +
                                "<extra></extra>",
                            )
        plots.append(trace)
        trace = go.Scatter(y = BE_deaths_wallonia['cdf_deaths'], x = BE_deaths_wallonia['AGEGROUP'], mode = 'lines+markers', name = 'COVID-19 deaths (Wallonia)', line = dict(width = 3),
                                marker = dict(size = 6, line = dict(width = 1,color = 'DarkSlateGrey')),
                                hovertemplate=
                                "Probability: %{y:.2f}<br>" +
                                "Age: %{x}<br>" +
                                "<extra></extra>",
                            )
        plots.append(trace)
    layout = dict(title = {'text' : f'Life expectancy and COVID-19 deaths', 'y':0.95, 'x':0.45, 'xanchor': 'center','yanchor': 'top', 'font' : {'size': 25}}, height = 450, plot_bgcolor = "white",
                        showlegend=True,
                        legend = dict(x = 0, y=-0.3, orientation = 'h'),
                        xaxis = dict(title_text = 'Age', showgrid=True, gridwidth=1, gridcolor='lightgrey'),
                        yaxis = dict(title_text = 'Probability of death', showgrid=True, gridwidth=1, gridcolor='lightgrey'))
    fig = go.Figure( data = plots, layout = layout)
    return fig

def ticks_log(df, var):
    temp_max = 0
    label_max = []
    text_label_max = []
    tick = 1
    for reg in set(df.index):
        if temp_max < df[var].max():
            temp_max = df[var].max()
    while tick < temp_max*(0.50):
        label_max.append(tick)
        text_label_max.append(f'{tick:,}')
        tick *= 10
    label_max.append(temp_max)
    text_label_max.append(f'{temp_max:,}')
    return label_max, text_label_max

BE_data_cases = clean_data_be(url_epistat, cases = True, hosp = False, deaths = False)
BE_data_hosp = clean_data_be(url_epistat, cases = False, hosp = True, deaths = False)
BE_data_cases['CASES'] = BE_data_cases.groupby(['DATE', 'PROVINCE'])['CASES'].sum()
BE_data_cases = BE_data_cases.groupby(['DATE','PROVINCE']).first()
BE_data_cases = BE_data_cases[['CASES']]
BE_data_cases = BE_data_cases.rename(columns={"CASES": "Cases"})
BE_data_cases['Cumulative cases'] = BE_data_cases.groupby(['PROVINCE'])['Cases'].cumsum()
BE_data_hosp['Released from hospital'] = BE_data_hosp.groupby(['PROVINCE'])['NEW_OUT'].cumsum()
BE_data_hosp['Total hospitalized'] = BE_data_hosp.groupby(['PROVINCE'])['NEW_IN'].cumsum()
BE_data_hosp = BE_data_hosp.rename(columns={"TOTAL_IN": "Hospitalized", 'TOTAL_IN_ICU': 'ICU', 'TOTAL_IN_RESP': 'Respiratory'})
BE_data_hosp = BE_data_hosp.reset_index()
BE_data_hosp = BE_data_hosp.rename(columns={"index": "DATE"})
BE_data_hosp['DATE'] = BE_data_hosp['DATE'].astype('str')
BE_data_hosp = BE_data_hosp.set_index(['DATE','PROVINCE'])
BE_total_prov = BE_data_cases.merge(BE_data_hosp, left_index = True, right_index = True, how='outer')
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

def draw_province_plots(BE_total_prov_merged, BE_total_merged, selected_province, plot_mode):
    fig = go.Figure()
    if plot_mode == 'line':
        if selected_province == 'Belgium':
            variables = ['Cumulative cases', 'Deceased', 'Hospitalized', 'ICU', 'Respiratory', 'Released from hospital', 'Total hospitalized']
            y = BE_total_merged.copy()
            x = y.index
        else:
            variables = ['Cumulative cases', 'Hospitalized', 'ICU', 'Respiratory', 'Released from hospital', 'Total hospitalized']
            y = BE_total_prov_merged.loc[BE_total_prov_merged['PROVINCE'] == selected_province].copy()
            x = y.index
        for var in variables:
            fig.add_trace(go.Scatter(x =  x, y = y[var],
                            mode='lines+markers',
                            name=var,
                            line=dict(width=3), marker = dict(size = 3, line = dict(width = 1,color = 'DarkSlateGrey')), hoverinfo = "text", connectgaps = True,
                            hovertext = [f"Province: {selected_province} <br>{var}: {y.iloc[indice][var]:,} <br>Date: {x[indice]}" for indice in range(len(y))]))
        fig.update_layout(title= 'Data by province')
        fig.update_xaxes(tickformat = '%d %B (%a)<br>%Y')
        fig.update_yaxes(tickformat = ',')
        fig.update_layout(
            hovermode='closest',
            legend=dict(
                traceorder="normal",
                font=dict(
                    family="sans-serif",
                    size=12,
                ),
                borderwidth=0,
                x = 0,
                y = -0.3,
                orientation = 'h',
            ),
            margin=dict(l=0, r=0, t=65, b=0),
            height=350,
            yaxis = {'type': 'linear'},
            plot_bgcolor = "white",
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
        fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black')
    elif plot_mode == 'bar':
        variables = ['Cumulative cases', 'Hospitalized', 'ICU', 'Respiratory', 'Released from hospital']
        temp_data = BE_total_prov_merged.loc[BE_total_prov_merged.index == BE_total_prov_merged.index.max()]
        temp_data = temp_data.set_index('PROVINCE')
        for prov in set(BE_total_prov_merged['PROVINCE']):
            temp_data.at[prov, 'Cumulative cases'] = BE_total_prov_merged.loc[BE_total_prov_merged['PROVINCE'] == prov]['Cumulative cases'].max()
        for var in variables:
            fig.add_trace(go.Bar(x =  temp_data.index, y = temp_data[var],
                            name=var,
                            hovertemplate=
                            "Number: %{y:,}<br>" +
                            "Province: %{x}<br>" +
                            "<extra></extra>",))
        fig.update_layout(title = {'text' : 'Cases and hospitalization, by province', 'y':0.95, 'x':0.45, 'xanchor': 'center','yanchor': 'top', 'font' : {'size': 25}}, height = 350, plot_bgcolor = "white",
                            showlegend=True,
                            legend = dict(x = 0, y=-0.4, orientation = 'h'),
                            xaxis = dict(showgrid=True, gridwidth=1, gridcolor='lightgrey'),
                            yaxis = dict( showgrid=True, gridwidth=1, gridcolor='lightgrey', tickformat = ','))
    return fig

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

BE_reg_total_deaths = aggregate_regions(BE_reg_deaths, 'DEATHS')
BE_reg_total_cases = aggregate_regions(BE_reg_cases, 'CASES')

BE_reg_male_deaths = aggregate_regions(df_reg_male_deaths, 'DEATHS')
BE_reg_female_deaths = aggregate_regions(df_reg_female_deaths, 'DEATHS')

BE_reg_male_cases = aggregate_regions(df_reg_male_cases, 'CASES')
BE_reg_female_cases = aggregate_regions(df_reg_female_cases, 'CASES')

def draw_regional_plot(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, variable, linear_log, gender):
    fig = go.Figure()
    if variable == 'cases':
        if gender == 'Male':
            temp_df = BE_reg_male_cases.copy()
        elif gender == 'Female':
            temp_df = BE_reg_female_cases.copy()
        else:
            temp_df = BE_reg_total_cases.copy()
        label_max, text_label_max = ticks_log(temp_df, 'CASES')
        for reg in set(temp_df.index):
            temp_data = temp_df.copy()
            temp_data = temp_data.reset_index()
            temp_data = temp_data.loc[temp_data['REGION'] == reg]
            y = temp_data.copy()
            if linear_log == 'Log':
                x = [x for x in range(len(y['DATE']))]
                fig.add_trace(go.Scatter(x =  x, y = y['CASES'],
                                    mode='lines+markers',
                                    name=reg,
                                    line=dict(width=3), marker = dict(size = 3, line = dict(width = 1,color = 'DarkSlateGrey')), hoverinfo = "text", connectgaps = True,
                                    hovertext = [f"Region: {reg} <br>Cases: {y.iloc[indice]['CASES']:,} <br>Days: {x[indice]}" for indice in range(len(y))]))
                fig.update_yaxes(tickvals = label_max, ticktext = text_label_max)
            else:
                fig.add_trace(go.Scatter(x =  y['DATE'], y = y['CASES'],
                                    mode='lines+markers',
                                    name=reg,
                                    line=dict(width=3), marker = dict(size = 3, line = dict(width = 1,color = 'DarkSlateGrey')), hoverinfo = "text", connectgaps = True,
                                    hovertext = [f"Region: {reg} <br>Cases: {y.iloc[indice]['CASES']:,} <br>Date: {str(y.iloc[indice]['DATE'])[:10]}" for indice in range(len(y))]))
                fig.update_xaxes(tickformat = '%d %B (%a)<br>%Y')
                fig.update_yaxes(tickformat = ',')
        fig.update_layout(title= 'Total confirmed cases')
    elif variable == 'deaths':
        if gender == 'Male':
            temp_df = BE_reg_male_deaths.copy()
        elif gender == 'Female':
            temp_df = BE_reg_female_deaths.copy()
        else:
            temp_df = BE_reg_total_deaths.copy()
        label_max, text_label_max = ticks_log(temp_df, 'DEATHS')
        for reg in set(temp_df.index):
            temp_data = temp_df.copy()
            temp_data = temp_data.reset_index()
            temp_data = temp_data.loc[temp_data['REGION'] == reg]
            y = temp_data.copy()
            if linear_log == 'Log':
                x = [x for x in range(len(y['DATE']))]
                fig.add_trace(go.Scatter(x =  x, y = y['DEATHS'],
                                    mode='lines+markers',
                                    name=reg,
                                    line=dict(width=3), marker = dict(size = 3, line = dict(width = 1,color = 'DarkSlateGrey')), hoverinfo = "text", connectgaps = True,
                                    hovertext = [f"Region: {reg} <br>Deaths: {y.iloc[indice]['DEATHS']:,} <br>Days: {x[indice]}" for indice in range(len(y))]))
                fig.update_yaxes(tickvals = label_max, ticktext = text_label_max)
            else:
                fig.add_trace(go.Scatter(x =  y['DATE'], y = y['DEATHS'],
                                    mode='lines+markers',
                                    name=reg,
                                    line=dict(width=3), marker = dict(size = 3, line = dict(width = 1,color = 'DarkSlateGrey')), hoverinfo = "text", connectgaps = True,
                                    hovertext = [f"Region: {reg} <br>Deaths: {y.iloc[indice]['DEATHS']:,} <br>Date: {str(y.iloc[indice]['DATE'])[:10]}" for indice in range(len(y))]))
                fig.update_xaxes(tickformat = '%d %B (%a)<br>%Y')
                fig.update_yaxes(tickformat = ',')
        fig.update_layout(title= 'Total deaths')

    fig.update_layout(
        hovermode='closest',
        legend=dict(
            traceorder="normal",
            font=dict(
                family="sans-serif",
                size=12,
            ),
            borderwidth=0,
            x=0,
            y=-0.4,
            orientation="h"
        ),
        margin=dict(l=0, r=0, t=65, b=0),
        #height=350,
        yaxis = {'type': 'linear' if linear_log == 'Linear' else 'log'},
        plot_bgcolor = "white",
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black')

    return fig


def draw_regional_share(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, BE_reg_pop, var_choice, gender):
    fig = go.Figure()
    if var_choice == 'Mortality rate':
        if gender == 'Male':
            temp_df = BE_reg_male_deaths.copy()
        elif gender == 'Female':
            temp_df = BE_reg_female_deaths.copy()
        else:
            temp_df = BE_reg_total_deaths.copy()
        for reg in set(temp_df.index):
            temp_data = temp_df.copy()
            temp_data = temp_data.reset_index()
            temp_data = temp_data.loc[temp_data['REGION'] == reg]
            if reg == 'Flanders':
                index = 0
            elif reg == 'Wallonia':
                index = 1
            elif reg == 'Brussels':
                index = 2
            y = temp_data.copy()
            y['DEATHS'] = (temp_data['DEATHS']/BE_reg_pop.iloc[index][gender])
            x = [x for x in range(len(y['DATE']))]
            fig.add_trace(go.Scatter(x =  x, y = y['DEATHS'],
                                mode='lines+markers',
                                name=reg,
                                line=dict(width=3), marker = dict(size = 3, line = dict(width = 1,color = 'DarkSlateGrey')), hoverinfo = "text", connectgaps = True,
                                hovertext = [f"Region: {reg} <br>Mortality rate: {y.iloc[indice]['DEATHS']*100:.2f}% <br>Days: {x[indice]} <br>Date: {y.iloc[indice]['DATE']}" for indice in range(len(y))]))
            fig.update_yaxes(tickformat = '.2%')
        fig.update_layout(title= 'Mortality rate')
    elif var_choice == 'Share of infected population':
        if gender == 'Male':
            temp_df = BE_reg_male_cases.copy()
        elif gender == 'Female':
            temp_df = BE_reg_female_cases.copy()
        else:
            temp_df = BE_reg_total_cases.copy()
        for reg in set(temp_df.index):
            temp_data = temp_df.copy()
            temp_data = temp_data.reset_index()
            temp_data = temp_data.loc[temp_data['REGION'] == reg]
            if reg == 'Flanders':
                index = 0
            elif reg == 'Wallonia':
                index = 1
            elif reg == 'Brussels':
                index = 2
            y = temp_data.copy()
            y['CASES'] = (temp_data['CASES']/BE_reg_pop.iloc[index][gender])
            x = [x for x in range(len(y['DATE']))]
            fig.add_trace(go.Scatter(x =  x, y = y['CASES'],
                                mode='lines+markers',
                                name=reg,
                                line=dict(width=3), marker = dict(size = 3, line = dict(width = 1,color = 'DarkSlateGrey')), hoverinfo = "text", connectgaps = True,
                                hovertext = [f"Region: {reg} <br>Share of infected population: {y.iloc[indice]['CASES']*100:.2f}% <br>Days: {x[indice]} <br>Date: {y.iloc[indice]['DATE']}" for indice in range(len(y))]))
            fig.update_yaxes(tickformat = '.2%')
        fig.update_layout(title= 'Share of infected population')

    fig.update_layout(
        hovermode='closest',
        legend=dict(
            traceorder="normal",
            font=dict(
                family="sans-serif",
                size=12,
            ),
            borderwidth=0,
            x=0,
            y=-0.4,
            orientation="h"
        ),
        margin=dict(l=0, r=0, t=65, b=0),
        #height=350,
        plot_bgcolor = "white",
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black')

    return fig

'''
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
        print('not match')

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
'''
'''
mapbox_access_token = 'pk.eyJ1IjoiZmVkZWdhbGwiLCJhIjoiY2s5azJwaW80MDQxeTNkcWh4bGhjeTN2NyJ9.twKWO-W5wPLX6m9OfrpZCw'

def gen_map(map_data,zoom,lat,lon):
    return {
        "data": [{
            "type": "choroplethmapbox",  #specify the type of data to generate, in this case, scatter map box is used
            "locations": list(df_epistat_muni_clean['Municipality']),
            "geojson": df_muni_geo,
            "featureidkey": 'properties.name',
            "z": np.log(df_epistat_muni_clean['Number cases']).round(2),
            "hoverinfo": "text",         
            "hovertext": [f"Municipality: {df_epistat_muni_clean.iloc[indice]['Municipality']} <br>Number of cases: {int(df_epistat_muni_clean.iloc[indice]['Number cases']):,} <br>Share of population infected: {df_epistat_muni_clean.iloc[indice]['Infected population (%)']:,}%" for indice in range(len(df_epistat_muni_clean['Municipality']))],
            'colorbar': dict(thickness=20, ticklen=3),
            'colorscale': 'Geyser',
            'autocolorscale': False,
            'showscale': False,
        },
        ],
        "layout": dict(
            autoscale = True,
            height=550,
            titlefont=dict(size='14'),
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=0
            ),
            hovermode="closest",
            mapbox=dict(
                accesstoken=mapbox_access_token,
                style='mapbox://styles/mapbox/light-v10',
                center=dict(
                    lon=lon,
                    lat=lat,
                ),
                zoom=zoom,
            )
        ),
    }

def map_selection(data):
    aux = data
    zoom = 6
    return gen_map(aux,zoom,50.85045,4.34878)
'''
# Draw weekly mortality
'''
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

def excess_mortality_lines(BE_excess_mortality):
    fig = go.Figure()
    temp_data = BE_excess_mortality.copy()
    temp_data_covid = temp_data.loc[temp_data['Weekly COVID-19 deaths'].isna() == False]
    y_covid = temp_data_covid.copy()
    fig.add_trace(go.Scatter(x =  y_covid.index, y = y_covid['Weekly COVID-19 deaths'],
                        mode='lines+markers',
                        name= 'Weekly COVID-19 deaths',
                        line=dict(width=3), marker = dict(size = 5, line = dict(width = 1,color = 'DarkSlateGrey')), hoverinfo = "text",
                        hovertext = [f"Country: Belgium <br>Weekly deaths: {int(y_covid.iloc[indice]['Weekly COVID-19 deaths']):,}" for indice in range(len(y_covid))]))
    
    fig.add_trace(go.Scatter(x =  temp_data.index, y = temp_data['Weekly average (2015-2017) deaths'],
                        mode='lines+markers',
                        name= 'Weekly deaths, average 2015-2017',
                        line=dict(width=3), marker = dict(size = 5, line = dict(width = 1,color = 'DarkSlateGrey')), hoverinfo = "text",
                        hovertext = [f"Country: Belgium <br>Weekly deaths, average 2015-2017: {int(temp_data.iloc[indice]['Weekly average (2015-2017) deaths']):,}" for indice in range(len(temp_data))]))
    
    fig.update_layout(
        title= 'Excess mortality (weekly deaths)',
        hovermode='closest',
        legend=dict(
            traceorder="normal",
            font=dict(
                family="sans-serif",
                size=12,
            ),
            borderwidth=0,
            x=0,
            y=-0.4,
            orientation="h"
        ),
        margin=dict(l=0, r=0, t=65, b=0),
        #height=350,
        plot_bgcolor = "white",
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey', range = [0, y_covid.index.max() + 1])
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey', tickformat = ',')
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black')

    return fig
'''
def tab_right_provinces(BE_total_prov_merged):
    temp_data = BE_total_prov_merged.copy()
    return html.Div([
        html.Ul([
            html.Li([
                html.Div([
                        dbc.ListGroupItem([
                            dbc.ListGroupItemHeading(f'{prov}:'),
                            dbc.ListGroupItemText(f"Confirmed cases: {int(temp_data.loc[temp_data['PROVINCE'] == prov]['Cumulative cases'].max()):,}", color = 'info'),
                            dbc.ListGroupItemText(f"Hospitalized: {int(temp_data.loc[temp_data['PROVINCE'] == prov].iloc[-1]['Hospitalized']):,}", color = 'warning'),
                            dbc.ListGroupItemText(f"ICU: {int(temp_data.loc[temp_data['PROVINCE'] == prov].iloc[-1]['ICU']):,}", color = 'danger'),
                            dbc.ListGroupItemText(f"Respiratory: {int(temp_data.loc[temp_data['PROVINCE'] == prov].iloc[-1]['Respiratory']):,}", color = 'darning'),
                            dbc.ListGroupItemText(f"Released from hospital: {int(temp_data.loc[temp_data['PROVINCE'] == prov].iloc[-1]['Released from hospital']):,}", color = 'info'),
                            dbc.ListGroupItemText(f"Total hospitalized: {int(temp_data.loc[temp_data['PROVINCE'] == prov].iloc[-1]['Total hospitalized']):,}", color = 'warning'),],
                                        className="border-top-0 border-left-0 border-right-0") for prov in sorted(list(set(BE_total_prov_merged['PROVINCE'])))
                ],
                className='media-body border-0'
                ),
            ],
            className='media border-0'
            ),   
        ],
        className='list-unstyled'
        ),
    ],
    style={ "height": "600px" },
    className="overflow-auto"
    ),
    className="border-0",

def tab_left_regions(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, BE_reg_pop, region):
    if region == 'Flanders':
        index = 0
    elif region == 'Wallonia':
        index = 1
    elif region == 'Brussels':
        index = 2
    return html.Div([
        html.Ul([
            html.Li([
                html.Div([
                        dbc.ListGroupItem([
                            dbc.ListGroupItemText(f"Confirmed cases: {int(BE_reg_total_cases.loc[region, 'CASES'].max()):,}", color = 'info'),
                            dbc.ListGroupItemText(f"Confirmed cases (female): {int(BE_reg_female_cases.loc[region, 'CASES'].max()):,}", color = 'info'),
                            dbc.ListGroupItemText(f"Confirmed cases (male): {int(BE_reg_male_cases.loc[region, 'CASES'].max()):,}", color = 'info'),
                            dbc.ListGroupItemText(f"Deaths: {int(BE_reg_total_deaths.loc[region, 'DEATHS'].max()):,}", color = 'danger'),
                            dbc.ListGroupItemText(f"Deaths (female): {int(BE_reg_female_deaths.loc[region, 'DEATHS'].max()):,}", color = 'danger'),
                            dbc.ListGroupItemText(f"Deaths (male): {int(BE_reg_male_deaths.loc[region, 'DEATHS'].max()):,}", color = 'danger'),
                            dbc.ListGroupItemText(f"Mortality rate: {(BE_reg_total_deaths.loc[region, 'DEATHS'].max()/BE_reg_pop.iloc[index]['Total'])*100:.2f}%", color = 'warning'),
                            dbc.ListGroupItemText(f"Mortality rate (female): {(BE_reg_female_deaths.loc[region, 'DEATHS'].max()/BE_reg_pop.iloc[index]['Female'])*100:.2f}%", color = 'warning'),
                            dbc.ListGroupItemText(f"Mortality rate (male): {(BE_reg_male_deaths.loc[region, 'DEATHS'].max()/BE_reg_pop.iloc[index]['Male'])*100:.2f}%", color = 'warning'),
                            dbc.ListGroupItemText(f"Share of infected population: {(BE_reg_total_cases.loc[region, 'CASES'].max()/BE_reg_pop.iloc[index]['Total'])*100:.2f}%", color = 'warning'),
                            dbc.ListGroupItemText(f"Share of infected population (female): {(BE_reg_female_cases.loc[region, 'CASES'].max()/BE_reg_pop.iloc[index]['Female'])*100:.2f}%", color = 'warning'),
                            dbc.ListGroupItemText(f"Share of infected population (male): {(BE_reg_male_cases.loc[region, 'CASES'].max()/BE_reg_pop.iloc[index]['Male'])*100:.2f}%", color = 'warning'),
                            dbc.ListGroupItemText(f"Population in 2019: {int(BE_reg_pop.iloc[index]['Total']):,}", color = 'success'),
                            dbc.ListGroupItemText(f"Population in 2019 (female): {int(BE_reg_pop.iloc[index]['Female']):,}", color = 'success'),
                            dbc.ListGroupItemText(f"Population in 2019 (male): {int(BE_reg_pop.iloc[index]['Male']):,}", color = 'success'),
                    ],
                    className="border-top-0 border-left-0 border-right-0"
                        )
                ],
                className='media-body border-0'
                ),
            ],
            className='media border-0'
            ),   
        ],
        className='list-unstyled'
        ),
    ],
    style={ "height": "600px" },
    className="overflow-auto"
    ),
    className="border-0",

children_right_tab = tab_right_provinces(BE_total_prov_merged)
tab_right = dbc.Card(children = children_right_tab)

tab_brussels = tab_left_regions(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, BE_reg_pop, 'Brussels')
tab_left_brussels = dbc.Card(children = tab_brussels)
tab_flanders = tab_left_regions(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, BE_reg_pop, 'Flanders')
tab_left_flanders = dbc.Card(children = tab_flanders)
tab_wallonia = tab_left_regions(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, BE_reg_pop, 'Wallonia')
tab_left_wallonia = dbc.Card(children = tab_wallonia)


markdown_data_info = dcc.Markdown('''
The dashboard is updated daily following new daily releases of data from the data sources listed below.

**Data source daily updated:**
* Detailed COVID-19 data for Belgium from [Epistat](https://epistat.wiv-isp.be/covid/).

The data from Epistat usually have a delay on the reported cases, by 1-2 days. We always report the latest available value for cumulative cases, for example, in the tabs displaying province and regional statistics.

**Other data:**
* Geojson data used for the map at the municipality level can be found [here](https://github.com/Datafable/rolling-blackout-belgium/blob/master/data/geospatial/municipalities-belgium.geojson).
* Life tables and population for Belgium from [Statbel](https://statbel.fgov.be).
''')

markdown_relevant_info = dcc.Markdown('''
This dashboard is part of a larger set of dashboards available on our website. In particular, here we focus on Belgium.

Our dashboard focusing on all the countries in the world for which we have available data can be found here.

Articles reporting daily information on COVID-19 are available here.
''')
############################
# Bootstrap Grid Layout
############################

app.layout = html.Div([
    
    #Header TITLE
    html.Div([
        #Info Modal Button LEFT
        dbc.Button("Relevant info", id="open-centered-left", className="btn-sm"),
        dbc.Modal(
            [
                dbc.ModalHeader("Relevant information"),
                dbc.ModalBody(children = markdown_relevant_info),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close-centered-left", className="ml-auto"
                    )
                ),
            ],
            id="modal-centered-left",
            centered=True,
        ),
        #H1 Title
        html.H1(
            children='COVID-19 - Belgium',
            className="text-center",
        ),
        #Info Modal Button RIGHT
        dbc.Button("Datasets info", id="open-centered-right", className="btn-sm"),
        dbc.Modal(
            [
                dbc.ModalHeader("Information on datasets used"),
                dbc.ModalBody(children = markdown_data_info),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close-centered-right", className="ml-auto"
                    )
                ),
            ],
            id="modal-centered-right",
            centered=True,
        ),
    ],
    className="d-flex justify-content-md-between my-2"
    ),
    
    #First Row CARDS 3333
    html.Div([
        html.Div([
            #Card 1
            html.Div([
                # Card 1 body
                html.Div([
                    html.H4(
                        children='Cases: ',
                        className='card-title'
                    ),
                    html.H4(f"{int(BE_total_merged['Cumulative cases'].max()):,d}",
                        className='card-text'
                    ),
                ],
                className="card-body"
                )
            ],
            className='card my-2 text-center shadow'
            ),
        ],
        className="col-md-3"
        ),
        html.Div([
            #Card 2
            html.Div([
                # Card 2 body
                html.Div([
                    html.H4(
                        children='Deaths: ',
                        className='card-title'
                    ),
                    html.H4(f"{int(BE_total_merged['Deceased'].max()):,d}",
                        className='card-text'
                    ),
                ],
                className="card-body"
                )
            ],
            className='card my-2 text-center shadow'
            ),
        ],
        className="col-md-3"
        ),
        html.Div([
            #Card 3
            html.Div([
                # Card 3 body
                html.Div([
                    html.H4(
                        children='Total hospitalized: ',
                        className='card-title'
                    ),
                    html.H4(f"{int(BE_total_merged['Total hospitalized'].max()):,d}",
                        className='card-text'
                    ),
                ],
                className="card-body"
                )
            ],
            className='card my-2 text-center shadow'
            ),
        ],
        className="col-md-3"
        ),        
        html.Div([
            #Card 4
            html.Div([
                # Card 4 body
                html.Div([
                    html.H4(
                        children='Released from hospital: ',
                        className='card-title'
                    ),
                    html.H4(f"{int(BE_total_merged['Released from hospital'].max()):,d}",
                        className='card-text'
                    ),
                ],
                className="card-body"
                )
            ],
            className='card my-2 text-center shadow'
            ),
        ],
        className="col-md-3"
        ),
    ],
    className="row"
    ),
    
    #Second Row 363
    html.Div([
        
        #Col6 Middle
        html.Div([
            html.Div([
                html.H3(
                    children='Belgium Map',
                    style={},
                    className='text-center'
                ),
                html.P(
                    children='by number of confirmed cases',
                    style={},
                    className='text-center'
                ),
            ],
            className='my-2 mx-auto'
            ),
            #Buttons based on screen size
            html.Div([
                html.Div([
                    html.Div([
                        dbc.Button("Belgium Map", href="#belgiumMap", external_link=True),
                        dbc.Button("Regional stats", href="#regionStats", external_link=True),
                        dbc.Button("Province stats", href="#provinceStats", external_link=True),
                    ],
                    className='text-center d-md-none'                        
                    ),
                ],
                className='card-body pt-1 pb-0'
                ),
            ],
            className='card my-2 shadow sticky-top'
            ),
            # Aggregate and province plots
            html.Div([
                html.H4(
                    children='Aggregate and province level statistics',
                    style={"textDecoration": "underline", "cursor": "pointer"},
                    className='text-center my-2',
                    id = 'aggregate_province_tooltip'
                ),
                dbc.Tooltip(children = [
                    html.P([
                        "Using the dropdown menu it is possible to switch between data at the aggregate- and province-level. The deceased data are not available at the province-level."
                    ],),],
                target="aggregate_province_tooltip",
                style= {'opacity': '0.8'}
                ),
                html.Div([
                    dbc.RadioItems(
                        id='plots-mode',
                        options=[{'label': i, 'value': i} for i in ['line', 'bar']],
                        value='line',
                        labelStyle={},
                        inline=True,
                        className='mb-1',
                        style = {}
                    ),
                    dbc.Tooltip(children = [
                        html.P([
                            "Line: Shows data by date for the selected province (or overall for Belgium)."
                        ],),
                        html.P([
                            "Bar: Reports the latest available data for each province. There might be a mismatch between the date in which the variables are reported. In particular, the data on confirmed cases are usually updated 1 or 2 days after the other statistics."
                        ],),],
                        target="plots-mode",
                        style= {'opacity': '0.8'}
                    ),
                    dcc.Dropdown(
                        id='demo-dropdown',
                        options=[{'label': i, 'value': i} for i in available_provinces],
                        multi=False,
                        value = 'Belgium',
                        className='',
                        style = {}
                    ), 
                ],
                className ='card-body text-center'
                ),
            ],
            className='card my-2 shadow'
            ),
            
            # Plots provinces
            html.Div([
                html.Div([
                    dcc.Graph(id='line-graph-province',)
                ],
                className='p-1'
                ),
            ],
            style={},
            className='card my-2 shadow'
            ),
            # Choose gender and linear or log scale
            html.Div([
                html.H4(
                    children='Regional statistics by gender',
                    style={"textDecoration": "underline", "cursor": "pointer"},
                    className='text-center my-2',
                    id = 'regional_tooltip'
                ),
                dbc.Tooltip(children = [
                    html.P([
                        "This group of plots includes data on confirmed cases and deaths, as well as plots on mortality rate and share of infected population."
                    ],),
                    html.P([
                        "Using the dropdown menu it is possible to choose between statistics at the aggregate level or for a specfic gender."
                    ],),],
                target="regional_tooltip",
                style= {'opacity': '0.8'}
                ),
                html.Div([
                    dbc.RadioItems(
                        id='reg-log',
                        options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                        value='Linear',
                        labelStyle={},
                        inline=True,
                        className='mb-1',
                        style = {}
                    ),
                    dbc.Tooltip(children = [
                        html.P([
                            "Switch between linear and logarithmic scale for the plots reporting the number of confirmed cases and deaths at the regional level."
                        ],),
                        html.P([
                            "When displaying the logarithmic scale, the horizontal axis reports the count from the day of the first confirmed case (or death)."
                        ],),],
                        target="reg-log",
                        style= {'opacity': '0.8'}
                    ),
                    dcc.Dropdown(
                        id='reg-gender',
                        options=[{'label': i, 'value': i} for i in ['Total', 'Female', 'Male']],
                        multi=False,
                        value = 'Total',
                        className='',
                        style = {}
                    ),
                ],
                className ='card-body text-center'
                ),
            ],
            className='card my-2 shadow'
            ),
            # Regional plots confirmed cases
            html.Div([
                html.Div([
                    dcc.Graph(id='line-graph-reg-cases',)
                ],
                className='p-1'
                ),
            ],
            style={},
            className='card my-2 shadow'
            ),
            # Regional plots confirmed deaths
            html.Div([
                html.Div([
                    dcc.Graph(id='line-graph-reg-deaths',)
                ],
                className='p-1'
                ),
            ],
            style={},
            className='card my-2 shadow'
            ),
            # Other regional variables
            html.Div([
                html.Div([
                    html.H5(
                        children='Select a variable:',
                        style={"textDecoration": "underline", "cursor": "pointer"},
                        className='text-center my-2',
                        id = 'tooltip_mr_sip'
                    ),
                    dcc.Dropdown(
                        id='mortality-infected',
                        options=[{'label': i, 'value': i} for i in ['Mortality rate', 'Share of infected population']],
                        multi=False,
                        value = 'Mortality rate',
                    ),
                    dbc.Tooltip(children = [
                        html.P([
                            "Mortality rate: Share of deaths out of population in 2019 for each region. If a gender is selected the 2019 population is gender- and region- specific."
                        ],),
                        html.P([
                            "Share of infected population: Share of confirmed cases out of population in 2019 for each region. If a gender is selected the 2019 population is gender- and region- specific."
                        ],),],
                        target="tooltip_mr_sip",
                        style= {'opacity': '0.8'}
                    ),
                ],
                className='card-body text-center'
                ),
            ],
            className='card my-2 shadow'
            ),
            # Plots other regional variables
            html.Div([
                html.Div([
                    dcc.Graph(id='line-graph-reg-multiples',)
                ],
                className='p-1'
                ),
            ],
            style={},
            className='card my-2 shadow'
            ),
        ],
        className="col-md-6 order-md-2"
        ),
        
        #Col2 Left
        html.Div([
            html.Div([
                dbc.Tabs([
                    dbc.Tab(tab_left_brussels, label="Brussels"),
                    dbc.Tab(tab_left_flanders, label="Flanders"),
                    dbc.Tab(tab_left_wallonia, label="Wallonia"),
                ],
                className="nav-justified"
                )
            ],
            className="card my-2 shadow",
            id="regionStats",
            )
        ],
        className="col-md-3 order-md-1"
        ),

        #Col2 Right
        html.Div([
            html.Div([
                dbc.Tabs([
                    dbc.Tab(tab_right, label="Province statistics(*)"),
                ],
                className="nav-justified",
                id = 'info_tab_right'
                )
            ],
            className="card my-2 shadow",
            id="provinceStats",
            ),
            dbc.Tooltip(children = [
                html.P([
                    "This tab shows a set of statistics for the provinces in Belgium. We report the latest available data. The data on cumulative statistics are usually updated with a delay of 1-2 days"
                ],),],
                target="info_tab_right",
                style= {'opacity': '0.8'}
            ),
        ],
        className="col-md-3 order-md-3",
        ),
    ],
    className="row"
    ),
],
className="container-fluid"
)

@app.callback(
    [Output('line-graph-province', 'figure'),
    Output('line-graph-reg-cases', 'figure'),
    Output('line-graph-reg-deaths', 'figure'),
    Output('line-graph-reg-multiples', 'figure'),],
    [Input('demo-dropdown', 'value'),
    Input('plots-mode', 'value'),
    Input('reg-log', 'value'),
    Input('reg-gender', 'value'),
    Input('mortality-infected', 'value'),])
def line_selection(dropdown, line_bar, linear_log, reg_gender, var_choice):
    if len(dropdown) == 0:
        dropdown = 'Belgium'
    fig1 = draw_province_plots(BE_total_prov_merged, BE_total_merged, selected_province = dropdown, plot_mode = line_bar)
    #fig2 = life_expectancy(path_life_table_BE, url_epistat, line_lifetable)
    fig3 = draw_regional_plot(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, 'cases', linear_log, reg_gender)
    fig4 = draw_regional_plot(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, 'deaths', linear_log, reg_gender)
    fig5 = draw_regional_share(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, BE_reg_pop, var_choice, reg_gender)
    #fig6 = excess_mortality_lines(BE_excess_mortality)
    return fig1, fig3, fig4, fig5
'''
@app.callback(
    [Output('line-graph-province', 'figure'),
    Output('line-graph-lifetable', 'figure'),
    Output('line-graph-reg-cases', 'figure'),
    Output('line-graph-reg-deaths', 'figure'),
    Output('line-graph-reg-multiples', 'figure'),
    Output('line-graph-excess', 'figure')],
    [Input('demo-dropdown', 'value'),
    Input('plots-mode', 'value'),
    Input('lifetable-option', 'value'),
    Input('reg-log', 'value'),
    Input('reg-gender', 'value'),
    Input('mortality-infected', 'value'),])
def line_selection(dropdown, line_bar, line_lifetable, linear_log, reg_gender, var_choice):
    if len(dropdown) == 0:
        dropdown = 'Belgium'
    fig1 = draw_province_plots(BE_total_prov_merged, BE_total_merged, selected_province = dropdown, plot_mode = line_bar)
    fig2 = life_expectancy(path_life_table_BE, url_epistat, line_lifetable)
    fig3 = draw_regional_plot(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, 'cases', linear_log, reg_gender)
    fig4 = draw_regional_plot(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, 'deaths', linear_log, reg_gender)
    fig5 = draw_regional_share(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, BE_reg_pop, var_choice, reg_gender)
    fig6 = excess_mortality_lines(BE_excess_mortality)
    return fig1, fig2, fig3, fig4, fig5, fig6
'''
@app.callback(
    Output("modal-centered-left", "is_open"),
    [Input("open-centered-left", "n_clicks"), Input("close-centered-left", "n_clicks")],
    [State("modal-centered-left", "is_open")],)
def toggle_modal_left(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("modal-centered-right", "is_open"),
    [Input("open-centered-right", "n_clicks"), Input("close-centered-right", "n_clicks")],
    [State("modal-centered-right", "is_open")],)
def toggle_modal_right(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

if __name__ == '__main__':
    app.run_server(debug=False)
