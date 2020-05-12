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
            #Map, Table
            html.Div([
                html.Div([
                    dcc.Graph(id='belgium_map', figure = map_selection(df_epistat_muni_clean))
                ],
                className='',
                id="belgiumMap",
                ),
            ],
            className='my-2 shadow'
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
                    style= {'opacity': '0.8'}
                ),
                html.Div([
                    dcc.Dropdown(
                    id='lifetable-option',
                    options=[{'label': i, 'value': i} for i in ['COVID-19 deaths, all', 'COVID-19 deaths, female', 'COVID-19 deaths, male', 'COVID-19 deaths, by region']],
                    multi=False,
                    value = 'COVID-19 deaths, all',
                    ),
                ],
                className='card-body pt-1 pb-0'
                ),
            ],
            className='card my-2 shadow'
            ),
            
            # Plots lifetable
            html.Div([
                html.Div([
                    dcc.Graph(id='line-graph-lifetable',)
                ],
                className='p-1'
                ),
            ],
            style={},
            className='card my-2 shadow'
            ),
            
            # Plot excess mortality
            html.Div([
                html.Div([
                    dcc.Graph(id='line-graph-excess',)
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
