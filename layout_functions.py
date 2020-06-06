import numpy as np 
import pandas as pd
from pickle_functions import unpicklify
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table as dt
from dash.dependencies import Input, Output, State
from app_functions import *
from pickle_functions import unpicklify
from process_functions import write_log

def life_expectancy(life_table_discrete, BE_deaths, line_plot):
    plots = []
    if line_plot == 'COVID-19 deaths, all':
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
    layout = dict(title = {'text' : f'Life expectancy and COVID-19 deaths', 'y':0.95, 'x':0.45, 'xanchor': 'center','yanchor': 'top', 'font' : {'size': 25}}, height = 450,
                        plot_bgcolor = 'white',
                        paper_bgcolor = 'white',
                        showlegend=True,
                        legend = dict(x = 0, y=-0.3, orientation = 'h'),
                        xaxis = dict(title_text = 'Age', showgrid=True, gridwidth=1, gridcolor='lightgrey'),
                        yaxis = dict(title_text = 'Probability of death', showgrid=True, gridwidth=1, gridcolor='lightgrey'))
    fig = go.Figure( data = plots, layout = layout)
    return fig

def draw_province_plots(BE_total_prov_merged, BE_total_merged, selected_province, plot_mode):
    fig = go.Figure()
    if plot_mode == 'Line':
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
        fig.update_layout(title= 'Belgium cumulative numbers')
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
            plot_bgcolor = 'white',
            paper_bgcolor = 'white',
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
        fig.update_yaxes(zeroline=True, zerolinewidth=1, zerolinecolor='black')
        fig.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor='black')
    elif plot_mode == 'Bar':
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
        fig.update_layout(title = {'text' : 'Cases and hospitalization, by province', 'y':0.95, 'x':0.45, 'xanchor': 'center','yanchor': 'top', 'font' : {'size': 25}}, height = 350,
                            plot_bgcolor = 'white',
                            paper_bgcolor = 'white',
                            showlegend=True,
                            legend = dict(x = 0, y=-0.4, orientation = 'h'),
                            xaxis = dict(showgrid=True, gridwidth=1, gridcolor='lightgrey'),
                            yaxis = dict( showgrid=True, gridwidth=1, gridcolor='lightgrey', tickformat = ','))
    return fig

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
        plot_bgcolor = 'white',
        paper_bgcolor = 'white',
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
    elif var_choice == 'Infection rate':
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
                                hovertext = [f"Region: {reg} <br>Infection rate: {y.iloc[indice]['CASES']*100:.2f}% <br>Days: {x[indice]} <br>Date: {y.iloc[indice]['DATE']}" for indice in range(len(y))]))
            fig.update_yaxes(tickformat = '.2%')
        fig.update_layout(title= 'Infection rate')

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
        plot_bgcolor = 'white',
        paper_bgcolor = 'white',
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black')

    return fig


def gen_map(map_data,geo):
    mapbox_access_token = 'pk.eyJ1IjoiZmVkZWdhbGwiLCJhIjoiY2s5azJwaW80MDQxeTNkcWh4bGhjeTN2NyJ9.twKWO-W5wPLX6m9OfrpZCw'
    zoom = 7
    lat = 50.57379
    lon = 4.69365
    return {
        "data": [{
            "type": "choroplethmapbox",  #specify the type of data to generate, in this case, scatter map box is used
            "locations": list(map_data['Municipality']),
            "geojson": geo,
            "featureidkey": 'properties.name',
            "z": np.log(map_data['Number cases']).round(2),
            "hoverinfo": "text",         
            "hovertext": [f"Municipality: {map_data.iloc[indice]['Municipality']} <br>Number of cases: {int(map_data.iloc[indice]['Number cases']):,} <br>Share of population infected: {map_data.iloc[indice]['Infected population (%)']:,}%" for indice in range(len(map_data['Municipality']))],
            'colorbar': dict(thickness=20, ticklen=3),
            'colorscale': 'Geyser',
            'autocolorscale': False,
            'showscale': False,
        },
        ],
        "layout":{
            'paper_bgcolor': 'white',
            'height': 660,
            'margin': {
                'l':0,
                'r':0,
                't':0,
                'b':0,
            },
            'hovermode':"closest",
            'mapbox': {
                'accesstoken': mapbox_access_token,
                'style':'mapbox://styles/mapbox/dark-v10',
                'center':{                    
                    'lon': lon,
                    'lat': lat,
                },
                'zoom': zoom,
            }
        }    
    }


def excess_mortality_lines(BE_excess_mortality):
    fig = go.Figure()
    temp_data = BE_excess_mortality.copy()
    temp_data_covid = temp_data.loc[temp_data['Weekly COVID-19 deaths'].isna() == False]
    y_covid = temp_data_covid.copy()
    fig.add_trace(go.Scatter(x =  y_covid.index, y = y_covid['Weekly COVID-19 deaths'],
                        mode='lines+markers',
                        name= 'Weekly COVID-19 deaths',
                        line=dict(width=3), marker = dict(size = 5, line = dict(width = 1,color = 'DarkSlateGrey')), hoverinfo = "text",
                        hovertext = [f"Country: Belgium <br>Weekly COVID-19 deaths: {int(y_covid.iloc[indice]['Weekly COVID-19 deaths']):,}" for indice in range(len(y_covid))]))
    
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
        plot_bgcolor = 'white',
        paper_bgcolor = 'white',
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey', range = [0, y_covid.index.max() + 1])
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey', tickformat = ',')
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black')

    return fig

def tab_right_provinces(BE_total_prov_merged):
    temp_data = BE_total_prov_merged.copy()
    return html.Div([
        html.Ul([
            html.Li([
                html.Div([
                        dbc.ListGroupItem([
                            dbc.ListGroupItemHeading(f'{prov}:'),
                            html.Hr(),
                            dbc.ListGroupItemText(f"Confirmed cases: {int(temp_data.loc[temp_data['PROVINCE'] == prov]['Cumulative cases'].max()):,}", color = 'info'),
                            dbc.ListGroupItemText(f"Hospitalized: {int(temp_data.loc[temp_data['PROVINCE'] == prov].iloc[-1]['Hospitalized']):,}", color = 'warning'),
                            dbc.ListGroupItemText(f"ICU: {int(temp_data.loc[temp_data['PROVINCE'] == prov].iloc[-1]['ICU']):,}", color = 'danger'),
                            dbc.ListGroupItemText(f"Respiratory: {int(temp_data.loc[temp_data['PROVINCE'] == prov].iloc[-1]['Respiratory']):,}", color = 'warning'),
                            dbc.ListGroupItemText(f"Released from hospital: {int(temp_data.loc[temp_data['PROVINCE'] == prov].iloc[-1]['Released from hospital']):,}", color = 'info'),
                            dbc.ListGroupItemText(f"Total hospitalized: {int(temp_data.loc[temp_data['PROVINCE'] == prov].iloc[-1]['Total hospitalized']):,}", color = 'warning'),],
                                        className="items") for prov in sorted(list(set(BE_total_prov_merged['PROVINCE'])))
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
    className="tabr overflow-auto"
    )

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
                            dbc.ListGroupItemText(f"Infection rate: {(BE_reg_total_cases.loc[region, 'CASES'].max()/BE_reg_pop.iloc[index]['Total'])*100:.2f}%", color = 'warning'),
                            dbc.ListGroupItemText(f"Infection rate (female): {(BE_reg_female_cases.loc[region, 'CASES'].max()/BE_reg_pop.iloc[index]['Female'])*100:.2f}%", color = 'warning'),
                            dbc.ListGroupItemText(f"Infection rate (male): {(BE_reg_male_cases.loc[region, 'CASES'].max()/BE_reg_pop.iloc[index]['Male'])*100:.2f}%", color = 'warning'),
                            dbc.ListGroupItemText(f"Population in 2019: {int(BE_reg_pop.iloc[index]['Total']):,}", color = 'success'),
                            dbc.ListGroupItemText(f"Population in 2019 (female): {int(BE_reg_pop.iloc[index]['Female']):,}", color = 'success'),
                            dbc.ListGroupItemText(f"Population in 2019 (male): {int(BE_reg_pop.iloc[index]['Male']):,}", color = 'success'),
                    ],
                    className="items"
                        )
                ],
                className='media-body'
                ),
            ],
            className='media'
            ),   
        ],
        className='list-unstyled'
        ),
    ],  
    className="tabcard overflow-auto"
    )
