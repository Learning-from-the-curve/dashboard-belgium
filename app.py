import datetime
import json
import dash
import pickle
import os
from pathlib import Path
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table as dt
from dash.dependencies import Input, Output, State

from layout_functions import *
from pickle_functions import unpicklify
#####################################################################################################################################
# Boostrap CSS and font awesome . Option 1) Run from codepen directly Option 2) Copy css file to assets folder and run locally
#####################################################################################################################################
external_stylesheets = [dbc.themes.FLATLY]

#Insert your javascript here. In this example, addthis.com has been added to the web app for people to share their webpage

app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

app.title = 'COVID-19 - Belgium dashboard'

#for heroku to run correctly
server = app.server
flask_app = app.server

config = {'displayModeBar': False}



#Overwrite your CSS setting by including style locally

######################################
# Retrieve data
######################################

# get data directly from github. The data source provided by Johns Hopkins University.

pickles_list = [
    'BE_total_prov_merged',
    'BE_total_merged',
    'BE_reg_total_deaths',
    'BE_reg_total_cases',
    'BE_reg_male_deaths',
    'BE_reg_female_deaths',
    'BE_reg_male_cases',
    'BE_reg_female_cases',
    'BE_reg_pop',
    'df_epistat_muni_clean',
    'df_muni_geo',
    'BE_excess_mortality',
    'BE_total_prov_merged',
    'available_provinces',
    'life_table_discrete',
    'BE_deaths_lifetable',
    ]

BE_total_prov_merged = unpicklify(pickles_list[0])
BE_total_merged = unpicklify(pickles_list[1])
BE_reg_total_deaths = unpicklify(pickles_list[2]) 
BE_reg_total_cases = unpicklify(pickles_list[3])
BE_reg_male_deaths = unpicklify(pickles_list[4])
BE_reg_female_deaths = unpicklify(pickles_list[5])
BE_reg_male_cases = unpicklify(pickles_list[6])
BE_reg_female_cases = unpicklify(pickles_list[7])
BE_reg_pop = unpicklify(pickles_list[8])
df_epistat_muni_clean = unpicklify(pickles_list[9])
df_muni_geo = unpicklify(pickles_list[10])
BE_excess_mortality = unpicklify(pickles_list[11])
BE_total_prov_merged = unpicklify(pickles_list[12])
available_provinces = unpicklify(pickles_list[13])
life_table_discrete = unpicklify(pickles_list[14])
BE_deaths_lifetable = unpicklify(pickles_list[15])


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
We focus on this dashboard on the COVID-19 pandemic in Belgium. This dashboard is part of a larger set of dashboards available [on our website](https://www.learningfromthecurve.net/dashboards/).

Articles by members of the Learning from the Curve team reporting daily information on COVID-19 are available [here](https://www.learningfromthecurve.net/commentaries/).

Please, report any bug at the following contact address: learningfromthecurve.info@gmail.com.
''')

#FIXME temp variables
try:
    card_cases_daily = int(BE_total_merged['Cumulative cases'][-1]-BE_total_merged['Cumulative cases'][-2])
except:
    card_cases_daily = 0
try:
    card_deceased_daily = int(BE_total_merged['Deceased'][-1]-BE_total_merged['Deceased'][-2])
except:
    card_deceased_daily = 0
try:
    card_hospitalized_daily = int(BE_total_merged['Total hospitalized'][-1]-BE_total_merged['Total hospitalized'][-2])
except:
    card_hospitalized_daily = 0
try:
    card_released_daily = int(BE_total_merged['Released from hospital'][-1]-BE_total_merged['Released from hospital'][-2])
except:
    card_released_daily = 0

############################
# Bootstrap Grid Layout
############################
app.layout = html.Div([
    html.Div([
    #Header TITLE
    html.Div([
        #Info Modal Button LEFT
        #dbc.Button("Relevant info", id="open-centered-left", className="btn "),
        dbc.ButtonGroup(
            [
                dbc.Button("Home", href="https://www.learningfromthecurve.net/", external_link=True, className="py-2"),
                dbc.Button("Dashboards", href="https://www.learningfromthecurve.net/Dashboards/", external_link=True, className="py-2"),
            ],
            vertical=True,
            size="sm",
        ),
        #H2 Title
        html.H2(
            children='COVID-19 Belgium',
            className="text-center",
        ),
        #Info Modal Button RIGHT
        #dbc.Button("Datasets info", id="open-centered-right", className="btn "),
        dbc.ButtonGroup(
            [
                dbc.Button("Info", id="open-centered-left", className="py-2"),
                dbc.Button("Datasets", id="open-centered-right", className="py-2"),
            ],
            vertical=True,
            size="sm",
        ),
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
        dbc.Modal(
            [
                dbc.ModalHeader("Relevant information"),
                dbc.ModalBody(children = markdown_relevant_info),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-centered-left", className="ml-auto")
                ),
            ],
            id="modal-centered-left",
            centered=True,
        ),
    ],
    className="topRow d-flex justify-content-between align-items-center mb-2"
    ),

    #First Row CARDS 3333
    dbc.Row([
        dbc.Col([
            #Card 1
            dbc.Card([
                    html.H4(children='Cases: ',),
                    html.H2(f"{int(BE_total_merged['Cumulative cases'].max()):,d}",),
                    html.P('New daily confirmed cases: ' + f"{card_cases_daily:,d}"),
                ],
            className='cards cases'
            ),
        ],
        lg = 3, xs = 12
        ),     

        dbc.Col([
            #Card 2
            dbc.Card([
                    html.H4(children='Deaths: ',),
                    html.H2(f"{int(BE_total_merged['Deceased'].max()):,d}",),
                    html.P('New daily deaths: ' + f"{card_deceased_daily:,d}"),
                ],
            className='cards deaths'
            ),
        ],
        lg = 3, xs = 12
        ),    

        dbc.Col([
            #Card 3
            dbc.Card([
                # Card 3 body
                html.H4(children='Total hospitalized: '),
                html.H2(f"{int(BE_total_merged['Total hospitalized'].max()):,d}", className ="text-warning"),
                html.P('New daily hospitalized: ' + f"{card_hospitalized_daily:,d}", className ="text-warning"),
            ],
            className='cards'
            ),
        ],
        lg = 3, xs = 12
        ),        
        dbc.Col([
            #Card 4
            dbc.Card([
                # Card 4 body
                html.H4(children='Released from hospital: '),
                html.H2(f"{int(BE_total_merged['Released from hospital'].max()):,d}", className ="text-info"),
                html.P('New daily Released from hospital: ' + f"{card_released_daily:,d}", className ="text-info"),
             ],
            className='cards'
            ),
        ],
        lg = 3, xs = 12
        ),  
    ],
    className = "midRow d-flex"
    ),
    
    #Second Row 363
    dbc.Row([
        #Col2 Left
        dbc.Col([
            dbc.Card([
                dbc.Tabs([
                    dbc.Tab(tab_left_brussels, label="Brussels"),
                    dbc.Tab(tab_left_flanders, label="Flanders"),
                    dbc.Tab(tab_left_wallonia, label="Wallonia"),
                ],
                className="nav-justified"
                ),
            ],
            className="card my-2 ",
            id="regionStats",
            ),
        ],
        #align = "stretch",
        lg = 3, md = 12 
        ),

    #Col6 Middle
        dbc.Col([
            #Map, Table
            html.Div([
                html.Div([
                    dcc.Graph(id='belgium_map', figure = gen_map(df_epistat_muni_clean, df_muni_geo), config=config)
                ],
                #className=' h-100',
                id="belgiumMap",
                ),
            ],
            className='my-2 '
            ),
        ],
        #className="col-md-6 order-md-2"
        lg = 6, xs = 12
        ),

        #Col2 Right
        dbc.Col([
            dbc.Card([
                dbc.Tabs([
                    dbc.Tab(tab_right, label="Province statistics(*)"),
                ],
                className="nav-justified",
                id = 'info_tab_right'
                )
            ],
            className="items my-2 ",
            id="provinceStats",
            ),
            dbc.Tooltip(children = [
                html.P([
                    "This tab shows a set of statistics for the provinces in Belgium. We report the latest available data. The data on cumulative statistics are usually updated with a delay of 1-2 days"
                ],),
            ],
            target="info_tab_right",
            style= {'opacity': '0.9'}
            ),
        ],
        #className= "h-100",
        lg = 3, xs = 12
        ),
    ],
    className = "botRow d-flex"
    )
    ],
    className="container-fluid cf py-2"
    ),

    html.Div([
    #Buttons based on screen size
    html.Div([
        html.Div([
            html.Div([
                dbc.Button("Belgium Map", href="#belgiumMap", external_link=True),
                dbc.Button("Regional stats", href="#regionStats", external_link=True),
                dbc.Button("Province stats", href="#provinceStats", external_link=True),
            ],
            className='text-center'                        
            ),
        ],
        className='card-body py-1'
        ),
    ],
    className='card my-2  sticky-top d-md-none'
    ),

    dbc.Row([
        dbc.Col([         
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
                style= {'opacity': '0.9'}
                ),
                html.Div([
                    dbc.RadioItems(
                        id='plots-mode',
                        options=[{'label': i, 'value': i} for i in ['Line', 'Bar']],
                        value='Line',
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
                        style= {'opacity': '0.9'}
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
            className='card my-2'
            ),
        ],
        width =12
        )
    ], 
    justify="center"
    ),

    html.Div([
        html.Div([
            dcc.Graph(id='line-graph-province', config=config)
        ],
        className='p-1'
        ),
    ],
    className='card my-2'
    ),       

    dbc.Row([
        dbc.Col([
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
                        "This group of plots includes data on confirmed cases and deaths, as well as plots on mortality rate and Infection rates."
                    ],),
                    html.P([
                        "Using the dropdown menu it is possible to choose between statistics at the aggregate level or for a specfic gender."
                    ],),],
                target="regional_tooltip",
                style= {'opacity': '0.9'}
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
                        style= {'opacity': '0.9'}
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
            className='card my-2'
            ),
        ],
        width =12
        ),
        dbc.Col([
            # Regional plots confirmed cases
            html.Div([
                html.Div([
                    dcc.Graph(id='line-graph-reg-cases', config=config)
                ],
                className='p-1'
                ),
            ],
            className='card my-2 '
            ),
        ],
        lg = 6, md = 12
        ),
        dbc.Col([
            # Regional plots confirmed deaths
            html.Div([
                html.Div([
                    dcc.Graph(id='line-graph-reg-deaths', config=config)
                ],
                className='p-1'
                ),
            ],
            className='card my-2 '
            ),
        ],
        lg = 6, md = 12
        ),
        dbc.Col([         
            # Other regional variables
            html.Div([
                html.Div([
                    html.H4(
                        children='Select a variable:',
                        style={"textDecoration": "underline", "cursor": "pointer"},
                        className='text-center my-2',
                        id = 'tooltip_mr_sip'
                    ),
                    dcc.Dropdown(
                        id='mortality-infected',
                        options=[{'label': i, 'value': i} for i in ['Mortality rate', 'Infection rate']],
                        multi=False,
                        value = 'Mortality rate',
                    ),
                    dbc.Tooltip(children = [
                        html.P([
                            "Mortality rate: Share of deaths out of population in 2019 for each region. If a gender is selected the 2019 population is gender- and region- specific."
                        ],),
                        html.P([
                            "Infection rate: Share of confirmed cases out of population in 2019 for each region. If a gender is selected the 2019 population is gender- and region- specific."
                        ],),],
                        target="tooltip_mr_sip",
                        style= {'opacity': '0.9'}
                    ),
                ],
                className='card-body text-center'
                ),
            ],
            className='card my-2 '
            ),
            # Plots other regional variables
            html.Div([
                html.Div([
                    dcc.Graph(id='line-graph-reg-multiples', config=config)
                ],
                className='p-1'
                ),
            ],
            style={},
            className='card my-2 '
            ),
        ],
        lg=6, md = 12
        ),
        dbc.Col([         
            # Lifetables and excess mortality
            html.Div([
                html.H4(
                children='Life expectancy and excess mortality',
                style={"textDecoration": "underline", "cursor": "pointer"},
                className='text-center my-2',
                id = 'life_mortality_tooltip'
                ),
                dbc.Tooltip(children = [
                    html.P([
                        "In the life expectancy group of plots, one curve plots the probability of being dead by a certain age, for all causes of death. For this curve, we average the densities over the years 2015-2017 to wash out year-specific peaks in mortality. The other curve shows mortality rates from COVID-19, across age groups. We also compare COVID-19 deaths by age group across regions (Brussels, Flanders, Wallonia)."
                    ],),
                    html.P([
                        "The excess mortality plot shows the weekly expected number of deaths (red curve) as the average number of deaths of 2015-2017. The blue curve plots the number of weekly deaths from COVID-19."
                    ],),],
                    target="life_mortality_tooltip",
                    style= {'opacity': '0.9'}
                ),
                html.Div([
                    dcc.Dropdown(
                    id='lifetable-option',
                    options=[{'label': i, 'value': i} for i in ['COVID-19 deaths, all', 'COVID-19 deaths, female', 'COVID-19 deaths, male', 'COVID-19 deaths, by region']],
                    multi=False,
                    value = 'COVID-19 deaths, all',
                    ),
                ],
                className='card-body text-center'
                ),
            ],
            className='card my-2 '
            ),
            # Plots lifetable
            html.Div([
                html.Div([
                    dcc.Graph(id='line-graph-lifetable', config=config)
                ],
                className='p-1'
                ),
            ],
            className='card my-2 '
            ),
        ],
        lg=6, md = 12
        ),
        dbc.Col([
            # Plot excess mortality
            html.Div([
                html.Div([
                    dcc.Graph(id='line-graph-excess', figure = excess_mortality_lines(BE_excess_mortality), config=config)
                ],
                className='p-1'
                ),
            ],
            className='card my-2 '
            ),
        ],
        lg = 12
        ),
    ], 
    justify="center"
    ),
    ],
    className="container-fluid cf py-2"
    ),

],
className="container-fluid"
)

@app.callback(
    [Output('line-graph-reg-cases', 'figure'),
    Output('line-graph-reg-deaths', 'figure'),
    Output('line-graph-reg-multiples', 'figure')],
    [Input('reg-log', 'value'),
    Input('reg-gender', 'value'),
    Input('mortality-infected', 'value')])
def line_selection(linear_log, reg_gender, var_choice):
    fig1 = draw_regional_plot(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, 'cases', linear_log, reg_gender)
    fig2 = draw_regional_plot(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, 'deaths', linear_log, reg_gender)
    fig3 = draw_regional_share(BE_reg_total_deaths, BE_reg_total_cases, BE_reg_male_deaths, BE_reg_female_deaths, BE_reg_male_cases, BE_reg_female_cases, BE_reg_pop, var_choice, reg_gender)
    return fig1, fig2, fig3

@app.callback(
    Output('line-graph-lifetable', 'figure'),
    [Input('lifetable-option', 'value'),])
def line_selection2(line_lifetable):
    fig1 = life_expectancy(life_table_discrete, BE_deaths_lifetable, line_lifetable)
    return fig1

@app.callback(
    Output('line-graph-province', 'figure'),
    [Input('demo-dropdown', 'value'),
    Input('plots-mode', 'value')])
def line_selection3(dropdown, line_bar):
    if len(dropdown) == 0:
        dropdown = 'Belgium'
    fig1 = draw_province_plots(BE_total_prov_merged, BE_total_merged, selected_province = dropdown, plot_mode = line_bar)
    return fig1

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
