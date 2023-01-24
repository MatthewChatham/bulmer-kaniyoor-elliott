# Plotly
import plotly.express as px
import plotly.graph_objects as go

# Dash
import dash
from dash import (
    Dash, dcc, html, Input, Output, State, 
    page_container, callback, dash_table, ctx,
    ALL
)
import dash_bootstrap_components as dbc
import dash_daq as daq

# Other
import os
import pandas as pd
import numpy as np

# Common
from src.common import CATEGORY_MAPPER
from src.db import get_conn, get_dd, get_df
from src.plotting import MARKERS, construct_fig1, construct_fig2
from src.benchmarks import (compute_bm_g1, compute_bm_g2)
from src.filters import generate_filter_control, get_filter_mask

dash.register_page(__name__, path='/')


# -------------------------- CONSTANTS & STYLE --------------------------------
#
#
# -----------------------------------------------------------------------------


CITATION = """
Bulmer, J. S., Kaniyoor, A., Elliott 2008432, J. A., A Meta-Analysis
of Conductive and Strong Carbon Nanotube Materials. Adv. Mater. 2021, 33,
2008432.
"""
CITELINK = "https://doi.org/10.1002/adma.202008432"

LOGO_URL = """
https://secureservercdn.net/45.40.155.190/svz.20f.myftpupload.com/
wp-content/uploads/2022/03/Logo1-2-768x768.png
"""
APP_NAME = 'CNT Explorer'

BLURB = ""

OLD_BLURB = """
Carbon nanotubes (CNTs) are a material of the future, with high strength and high
conductivity. Use the charts to explore data from CNT studies. 

Want your study included? Click here.
"""


# ------------------------------ PREDEFINED LAYOUT ELEMENTS -------------------
#
#
# -----------------------------------------------------------------------------

citation = html.Em(
    [
        CITATION,
        html.A(CITELINK, href=CITELINK)
    ], 
    className="text-muted", 
    id='citation'
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        # dbc.Col(html.Img(src=LOGO_URL, height="30px", id='logo')),
                        dbc.Col(
                            dbc.NavbarBrand(
                                "Idlewild Technologies", 
                                class_name="ms-2"
                            )
                        ),
                    ],
                    # align="center",
                    className="g-0",
                ),
                href="https://idlewildtech.com/",
                style={"textDecoration": "none"},
            )
        ]
    ),
    color="dark",
    fixed="top",
    dark=True
)

def serve_sidebar(df):
    
    sidebar_header = dbc.Row(
        [
            dbc.Col(
                [
                    html.H2("CNT Explorer", className="display-7"),
                ]
            ),
            dbc.Col(
                [
                    html.Button(
                        # use the Bootstrap navbar-toggler classes to style
                        html.Span(className="navbar-toggler-icon"),
                        className="navbar-toggler",
                        # the navbar-toggler classes don't set color
                        style={
                            "color": "rgba(0,0,0,.5)",
                            "border-color": "rgba(0,0,0,.1)",
                        },
                        id="navbar-toggle",
                    ),
                    html.Button(
                        # use the Bootstrap navbar-toggler classes to style
                        html.Span(className="navbar-toggler-icon"),
                        className="navbar-toggler",
                        # the navbar-toggler classes don't set color
                        style={
                            "color": "rgba(0,0,0,.5)",
                            "border-color": "rgba(0,0,0,.1)",
                        },
                        id="sidebar-toggle",
                    ),
                    html.Div(
                        html.Em(
                            'Open for filters',
                            style={'font-size': '10px', 'position': 'relative'}
                        ),
                        id='menu-instruction'
                    )
                ],
                # the column containing the toggle will be only as wide as the
                # toggle, resulting in the toggle being right aligned
                width="auto",
                # vertically align the toggle in the center
                align="center",
            ),
        ],
    )
    
    filter_modal = html.Div(
        children =
            [
                dbc.Row([
                    dbc.Col(
                        dbc.Button(
                            "Adjust filters", 
                            id="open", 
                            n_clicks=0, 
                            style={'margin-right': '5px'}
                        ),
                        className='col-auto'
                    ),
                    dbc.Col(
                        dbc.Button("Reset", id="reset-filters", n_clicks=0),
                        className='col-auto'
                    )
                ],
                className='g-0'
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        [
                            dbc.ModalTitle("Filters")
                        ]
                    ),
                    html.Div(
                        html.Em('By default, null values are included.'),
                        style={'padding': '1rem'}
                    ),
                    dbc.ModalBody(html.Div(id='filter-fields')),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close", 
                            id="close", 
                            className="ms-auto", 
                            n_clicks=0
                        )
                    ),
                ],
                id="filter-modal",
                size='lg',
                is_open=False,
                fullscreen=False
            ),
        ],
        className='my-2'
    )
    
    filters = [
        dbc.Row([
            dbc.Col(html.H5("Filters"), className='col-auto'), 
            dbc.Col(daq.BooleanSwitch(id='filters-switch', on=True), className='col-auto')
        ], className='g-1'),
        html.Div(
            id='filter-field-picker-div',
            children=dcc.Dropdown(
                [
                    c for c in df.columns 
                    if c not in 
                    ['Category', 'Doped or Acid Exposure (Yes/ No)']
                ], 
                [], 
                multi=True, 
                placeholder='Pick filter fields', 
                id='filter-field-picker'
            )
        ),
        filter_modal
    ]
    
    materials = [
        html.H5('Materials'),
        html.Div(
            id='legend-div',
            children=[
                dcc.Checklist(
                    df['Category'].unique(), 
                    [
                        c for c in CATEGORY_MAPPER.keys() 
                         if CATEGORY_MAPPER[c] != 'Other'
                    ], 
                    labelStyle={'display': 'block'},
                    labelClassName='m-1',
                    style={
                        "height":300, 
                    #     "width":350, 
                        "overflow":"auto",
                        'border': '1px solid rgba(0,0,0,.1)',
                    }, 
                    inputStyle={'margin-right': '2px'},
                    id='legend',
                ),
                html.Div(
                    [
                        dbc.Button(
                            'Toggle all', 
                            id='legend-toggle-all',
                            style={'margin-right': '5px'}
                        ),
                        dbc.Button(
                            'Reset', 
                            id='legend-reset',
                        ),
                    ],
                    className='my-2'
                )
            ]
        )
    ]
    
    doped = [
        html.H5('Doping'),
        dcc.Checklist(
            [
                {'label': 'Doped', 'value': 'Yes'},
                {'label': 'Undoped', 'value': 'No'},
            ],
            ['Yes', 'No'], 
            id='dope-control',
            inputStyle={'margin-right': '2px'},
            labelClassName='m-1',
        ),
    ]

    sidebar = html.Div(
        [
            sidebar_header,           
            dbc.Collapse(
                children=[
                    
                    html.Em(BLURB),

                    html.Hr(),
                    *filters,

                    html.Hr(),
                    *materials,
                    
                    html.Hr(),
                    *doped,
                    
                    # html.Hr(),                
                    # dbc.Button("Update charts", id="update", n_clicks=0)
                ],
                id="collapse",
            )
        ],
        id="sidebar"
    )
    
    return sidebar

def serve_content(df, dd):
    numeric_cols = [c for c in df.columns if dd[c] == 'numeric']
    categorical_cols = [c for c in df.columns if dd[c] != 'numeric']
    
    graph1 = html.Div(
        [
            
            # Graph 1
            html.B("User-selected property vs CNT category"),
            dbc.Row(
                [

                    dbc.Col(
                        dcc.Dropdown(
                            categorical_cols, 
                            'Category', 
                            multi=False, 
                            placeholder='Pick X-axis', 
                            id='graph1-xaxis-dropdown'
                        ),
                        md=3,
                        sm=6
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            numeric_cols, 
                            'Conductivity (MSm-1)', 
                            multi=False, 
                            placeholder='Pick Y-axis', 
                            id='graph1-yaxis-dropdown'
                        ),
                        md=3,
                        sm=6
                    ),
                    dbc.Col(
                        dcc.Checklist(
                            ['Log Y', 'Squash', 'Show Benchmarks'], 
                            ['Log Y'], 
                            id='graph1-log',
                            inline=True,
                            inputStyle={'margin-right': '5px'},
                            labelStyle={'margin-right': '10px'}
                        ),
                        md=6,
                        sm=7,
                        className='pt-2'
                    )
                ],
                className='mb-2'
            ),
            
            dbc.Row([
                dbc.Col(
                    id='graph1', 
                    children=dcc.Graph()
                )
            ]),
            
            html.Div(
                id='graph1table', 
                children=dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in ['X-axis', 'mean', 'max']]
                )
            )
        ]
    )
    
    graph3 = html.Div(
    
        [
            
            # Graph 3
            html.Hr(),
            html.B("User-selected property vs Production Process"),
            dbc.Row(
                [

                    dbc.Col(
                        dcc.Dropdown(
                            categorical_cols, 
                            'Production Process', 
                            multi=False, 
                            placeholder='Pick X-axis', 
                            id='graph3-xaxis-dropdown'
                        ),
                        md=3,
                        sm=6
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            numeric_cols, 
                            'Conductivity (MSm-1)', 
                            multi=False, 
                            placeholder='Pick Y-axis', 
                            id='graph3-yaxis-dropdown'
                        ),
                        md=3,
                        sm=6
                    ),
                    dbc.Col(
                        dcc.Checklist(
                            ['Log Y', 'Squash', 'Show Benchmarks'], 
                            ['Log Y'], 
                            id='graph3-log',
                            inline=True,
                            inputStyle={'margin-right': '5px'},
                            labelStyle={'margin-right': '10px'}
                        ),
                        md=6,
                        sm=7,
                        className='pt-2'
                    )
                ],
                className='mb-2'
            ),
            dbc.Row([
                dbc.Col(
                    id='graph3',
                    children=dcc.Graph()
                )
            ]),
            
            html.Div(
                id='graph3table', 
                children=dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in ['X-axis', 'mean', 'max']]
                )
            )
            
        ],
        className='mt-3'
        
    
    )

    graph2 = html.Div(
        [
            html.Hr(),
            html.B("Scatterplot"),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Dropdown(
                            numeric_cols, 
                            'Tensile Strength (MPa)', 
                            multi=False, 
                            placeholder='Pick X-axis', 
                            id='graph2-xaxis-dropdown'
                        ),
                        md=3,
                        sm=6
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            numeric_cols, 
                            'Conductivity (MSm-1)', 
                            multi=False, 
                            placeholder='Pick Y-axis', 
                            id='graph2-yaxis-dropdown'
                        ),
                        md=3,
                        sm=6
                    ),
                    dbc.Col(
                        dcc.Checklist(
                            ['Log Y', 'Log X', 'Squash', 'Show Benchmarks'], 
                            ['Log Y', 'Log X'], 
                            id='graph2-log',
                            inline=True,
                            inputStyle={'margin-right': '5px'},
                            labelStyle={'margin-right': '10px'}
                        ),
                        md=6,
                        sm=7,
                        className='pt-2'
                    )
                ],
                className='mb-2'
            ),
            html.Div(
                id='graph2', 
                children=dcc.Graph()
            )
        ],
        className='mt-3'
    )


    content = html.Div(
        id="page-content",
        children=[
            graph1,
            graph3,
            graph2,
            # todo: credit
            # html.Div(
            #     id='credit',
            #     children='Made by MC using Dash'
            # )
        ]
    )
    
    return content

# ------------------------------ LAYOUT ---------------------------------------
#
# -----------------------------------------------------------------------------

def serve_layout():
    
    df = get_df()
    dd = get_dd()
    
    # store the df in memory so callbacks don't need DB calls
    store_df = dcc.Store(
        id='df',
        data=df.replace('NaN', np.nan).to_dict(),
        storage_type='memory'
    )

    store_dd = dcc.Store(
        id='dd',
        data=dd,
        storage_type='memory'
    )
    
    clipboard = dcc.Clipboard(
        target_id="citation",
        title="copy",
        style={
            "display": "inline-block",
            "fontSize": 15,
            "verticalAlign": "top",
            'margin-right': '5px'
        }
    )
    
    return dbc.Container(
        [
            store_df,
            store_dd,
            navbar, 
            serve_sidebar(df),
            serve_content(df, dd),
            html.Footer(
                id='footer',
                children=[clipboard, citation]
            )
        ], 
        id='container',
        fluid=True,
    )

layout = serve_layout

# ------------------------------ CALLBACKS ------------------------------------
#
#
# -----------------------------------------------------------------------------

@dash.callback(
    Output("sidebar", "className"),
    [Input("sidebar-toggle", "n_clicks")],
    [State("sidebar", "className")],
)
def toggle_classname(n, classname):
    if n and classname == "":
        return "collapsed"
    return ""


@dash.callback(
    Output("collapse", "is_open"),
    [Input("navbar-toggle", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@dash.callback(
    Output('legend', 'value'),
    [
        Input('legend-toggle-all', 'n_clicks'),
        Input('legend-reset', 'n_clicks')
    ],
    State('legend', 'options'),
    State('legend', 'value')
)
def legend_buttons(n_clicks, n_clicks2, options, value):
    
    if n_clicks is None and n_clicks2 is None:
        return value
    
    if ctx.triggered_id == 'legend-toggle-all':
    
        if n_clicks is None:
            return value

        return [] if n_clicks %2 == 0 else options
    
    if ctx.triggered_id == 'legend-reset':
        return [
            c for c in CATEGORY_MAPPER.keys() 
             if CATEGORY_MAPPER[c] != 'Other'
        ]

@dash.callback(
    [
        Output('filter-fields', 'children'),
        Output('filter-field-picker', 'value')
    ],
    [
        Input('filter-field-picker', 'value'),
        Input('reset-filters', 'n_clicks')
    ],
    [
        State({'type': 'filter-control', 'column': ALL}, 'value'),
        State({'type': 'filter-control', 'column': ALL}, 'id'),
        State({'type': 'filter-null', 'column': ALL}, 'value'),
        State('df', 'data'),
        State('dd', 'data')
    ]
)
def display_filter_controls(
    value,
    n_clicks,
    ctrl_values,
    ctrl_idx,
    null_values,
    df,
    dd
):
        
    if ctx.triggered_id == 'reset-filters':
        return [], []
    
    df = pd.DataFrame.from_dict(df)
        
    res = [[], value]
    
    existing_cols = set([i['column'] for i in ctrl_idx])
        
    for i,c in enumerate(value):
        if c in existing_cols:
            res[0].append(
                generate_filter_control(
                    c,
                    df, dd,
                    ctrl_values[i], 
                    null_values[i]
                )
            )
        else:
            res[0].append(generate_filter_control(c, df, dd))
        
    return res

@dash.callback(
    Output("filter-modal", "is_open"),
    [
        Input("open", "n_clicks"), 
        Input("close", "n_clicks")
    ],
    [State("filter-modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


def build_graphtable(df, x, y, squash):
    
    if squash:
        res_df = df[y].agg(['mean', 'max']).to_frame().T
    else:
        res_df = df.groupby(x)[y].agg(['mean', 'max']).reset_index()
        
    print(res_df)
    
    return dash_table.DataTable(
        data=res_df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in res_df.columns]
    )


@dash.callback(
    [
        Output('graph1', 'children'),
        Output('graph1table', 'children'),
        Output('graph2', 'children'),
        Output('graph3', 'children'),
        Output('graph3table', 'children')
    ],
    # Input('update', 'n_clicks'),
    
    # Graph 1
    Input('graph1-xaxis-dropdown', 'value'),
    Input('graph1-yaxis-dropdown', 'value'), 
    Input('graph1-log', 'value'),
    
    # Graph 2
    Input('graph2-xaxis-dropdown', 'value'), 
    Input('graph2-yaxis-dropdown', 'value'),
    Input('graph2-log', 'value'),
    
    # Graph 3
    Input('graph3-xaxis-dropdown', 'value'), 
    Input('graph3-yaxis-dropdown', 'value'),
    Input('graph3-log', 'value'),
    
    # Common
    Input('legend', 'value'), 
    Input('dope-control', 'value'),
    Input('filters-switch', 'on'),
    Input({'type': 'filter-control', 'column': ALL}, 'value'),
    Input({'type': 'filter-control', 'column': ALL}, 'id'),
    Input({'type': 'filter-null', 'column': ALL}, 'value'),
    
    # Data
    State('df', 'data'),
    State('dd', 'data')
)
def update_charts(
    # n_clicks,
    
    # G1
    g1x,
    g1y, 
    g1log,
    
    # G2
    g2x,
    g2y,
    g2log,
    
    # G3
    g3x,
    g3y,
    g3log,
    
    # Common
    legend, 
    dope,
    apply_filters,
    ctrl_values,
    ctrl_idx,
    null_values,
    
    # Data
    df,
    dd

):
        
    df = pd.DataFrame.from_dict(df)
    
    mask = get_filter_mask(
        legend, 
        dope, 
        df, dd,
        ctrl_values, 
        ctrl_idx, 
        null_values,
        apply_filters
    )
    
    bm = None if 'Show Benchmarks' not in g1log else compute_bm_g1(df, g1y)
    fig1 = construct_fig1(
        df[mask], 
        g1x, 
        g1y, 
        'Log Y' in g1log,
        squash='Squash' in g1log,
        bm=bm
    )

    bm = None if 'Show Benchmarks' not in g2log else compute_bm_g2(df, g2x, g2y)
    fig2 = construct_fig2(
        df[mask], 
        x=g2x, 
        y=g2y,
        logx='Log X' in g2log,
        logy='Log Y' in g2log,
        squash='Squash' in g2log,
        bm=bm
    )
    
    # todo: give its own controls and update here
    bm = None if 'Show Benchmarks' not in g1log else compute_bm_g1(df, g3y)
    fig3 = construct_fig1(
        df[mask],
        g3x,
        g3y,
        'Log Y' in g3log,
        squash='Squash' in g3log,
        bm=bm
    )
    
    graph1table = build_graphtable(
        df=df[mask],
        x=g1x,
        y=g1y,
        squash='Squash' in g1log
    )
    
    graph3table = build_graphtable(
        df=df[mask],
        x=g3x,
        y=g3y,
        squash='Squash' in g3log
    )
            
    return [
        dcc.Graph(figure=fig1),
        graph1table,
        dcc.Graph(figure=fig2), 
        dcc.Graph(figure=fig3),
        graph3table
    ]

@dash.callback(
    [
        Output('open', 'disabled'),
        Output('reset-filters', 'disabled'),
        Output('filter-field-picker', 'disabled'),
    ],
    Input('filters-switch', 'on')
)
def toggle_filter_controls(apply_filters):
    if apply_filters:
        return [False]*3
    else:
        return [True]*3