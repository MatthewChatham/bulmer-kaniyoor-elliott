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

# Other
import os
import math
import pandas as pd
import numpy as np
import psycopg2

# Common
from src.common import (
    get_dd, get_df,
    CATEGORY_MAPPER, MARKERS, BENCHMARK_COLORS,
    construct_fig1, construct_fig2, compute_benchmarks
)

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

BLURB = """
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
            dbc.Button(
                "Adjust filters", 
                id="open", 
                n_clicks=0, 
                style={'margin-right': '5px'}
            ),
            dbc.Button("Reset", id="reset-filters", n_clicks=0),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Filters")),
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

    sidebar = html.Div(
        [
            sidebar_header,           
            dbc.Collapse(
                children=[
                    
                    html.Em(BLURB),
                    # citation,
                    html.Hr(),
                    html.H5("Filters"),
#                     html.P(
#                         """
                        
#                         Select filter fields.
                        
#                         \n
                        
#                         To reset a filter, remove it from the list.
                        
#                         """, 
#                         className="text-muted"
#                     ),
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
                    filter_modal,

                    html.Hr(),
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
                    ),
                    
                    html.Hr(),
                    html.H5('Doped or Acid Exposure'),
                    dcc.Checklist(
                        ['Yes', 'No'], 
                        ['Yes', 'No'], 
                        id='dope-control',
                        inputStyle={'margin-right': '2px'},
                        labelClassName='m-1',
                    ),
                    
                    html.Hr(),                
                    dbc.Button("Update charts", id="update", n_clicks=0)
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
            html.B("Boxplots"),
            html.Hr(),
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
            html.Div(
                id='graph1', 
                children=dcc.Graph()
            )
        ]
    )

    graph2 = html.Div(
        [
            html.B("Scatterplot"),
            html.Hr(),
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
            graph2,
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

# ------------------------------ HELPERS --------------------------------------
#
#
# -----------------------------------------------------------------------------


def generate_filter_control(c, df, dd, ctrl_value=None, null_value=None):
    """
    Given a column name `c`,
    generate an appropriate filter control based
    on the column type and values.
    """
        
    control = None
    res = [
        html.H6(c),
        None        
    ]
    
    if dd[c] == 'numeric':
        
        rng = [
            df[c].astype(float).min(),
            df[c].astype(float).max()
        ]
        
        ctrl_value = ctrl_value if ctrl_value else rng
        
        control = dcc.RangeSlider(
            *rng,
            value=ctrl_value,
            id={'type': 'filter-control', 'column': c}
        )
    else:
        
        ctrl_value = ctrl_value if ctrl_value else df[c].unique()
        
        control = dcc.Dropdown(
            df[c].dropna().unique(),
            value=ctrl_value,
            multi=True, 
            placeholder=c, 
            id={'type': 'filter-control', 'column': c}
        )
    
    null_value = null_value if null_value is not None else ['Include null']
    
    res[1] = dbc.Row([
        dbc.Col(control, width=8),
        dbc.Col(dcc.Checklist(
            ['Include null'], 
            null_value,
            inputStyle={'margin-right': '5px'},
            id={'type': 'filter-null', 'column': c}
        ), width=4)
    ])
        
    # print('Appending to children:')
    # print(res)
        
    return html.Div(res, style={'margin-top': '1rem'})


def get_filter_mask(
    legend, 
    dope, 
    df,
    dd,
    ctrl_values, 
    ctrl_idx, 
    null_values
):
    """
    Given a list of `filters`, the `legend` and `dope` controls,
    and a pandas `df`, build a mask.
    """
    
    ctrl_cols = [i['column'] for i in ctrl_idx]
    
    mask = df['Category'].isin(legend) & \
    df['Doped or Acid Exposure (Yes/ No)'].isin(dope)
    
    if not ctrl_values:
        return mask
    
    for i,c in enumerate(ctrl_cols):   
        if dd[c] == 'numeric':
            m = df[c].between(*ctrl_values[i])
            if null_values[i]:
                m = m | df[c].isnull()
        else:
            m = df[c].isin(ctrl_values[i])
            if null_values[i]:
                m = m | df[c].isnull()
        
        mask = mask & m
        
    return mask

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

@dash.callback(
    [
        Output('graph1', 'children'),
        Output('graph2', 'children')
    ],
    Input('update', 'n_clicks'),
    # Common State
    [
        State('legend', 'value'), 
        State('dope-control', 'value'),
        State({'type': 'filter-control', 'column': ALL}, 'value'),
        State({'type': 'filter-control', 'column': ALL}, 'id'),
        State({'type': 'filter-null', 'column': ALL}, 'value'),
        State('df', 'data'),
        State('dd', 'data')
    ],
    # Graph 1 State
    [
        State('graph1-xaxis-dropdown', 'value'), 
        State('graph1-yaxis-dropdown', 'value'), 
        State('graph1-log', 'value')
    ],
    # Graph 2 State
    [
        State('graph2-xaxis-dropdown', 'value'), 
        State('graph2-yaxis-dropdown', 'value'),
        State('graph2-log', 'value'),
    ]
)
def update_charts(
    n_clicks, 
    # Common
    legend, 
    dope, 
    ctrl_values,
    ctrl_idx,
    null_values,
    df,
    dd,
    # G1
    g1x, 
    g1y, 
    g1log,
    # G2
    g2x,
    g2y,
    g2log
):
        
    df = pd.DataFrame.from_dict(df)
    
    mask = get_filter_mask(
        legend, 
        dope, 
        df, dd,
        ctrl_values, 
        ctrl_idx, 
        null_values
    )
    
    # sort the df to avoid mask effects
    chartdata = df[mask].sort_index()
    print(len(chartdata))
    
    fig1 = construct_fig1(
        chartdata, 
        g1x, 
        g1y, 
        'Log Y' in g1log,
        squash='Squash' in g1log
    )
        
    fig2 = construct_fig2(
        chartdata, 
        x=g2x, 
        y=g2y,
        logx='Log X' in g2log,
        logy='Log Y' in g2log,
        squash='Squash' in g2log
    )
    
    # Graph 1 Benchmarks
    if 'Show Benchmarks' in g1log:
        benchmarks = compute_benchmarks(df, g1y)
        for m,v in benchmarks.items():
            if np.isnan(v):
                continue

            fig1.add_hline(
                y=v,
                line={
                    'color': BENCHMARK_COLORS[m],
                    'dash': 'dash'
                },
                annotation_text=m, 
                annotation_position='right',
                annotation_y=math.log(v,10) if 'Log Y' in g1log else v
            )
            
            
    # todo: Graph 2 Benchmarks
    if 'Show Benchmarks' in g2log:
        print('entered `if` statement for benchmarks')
        benchmarks = compute_benchmarks_g2(df, g2x, g2y)
        bm = pd.DataFrame(benchmarks).T.reset_index()
        bm.dropna(inplace=True)
        print(bm)
        
        for i,r in bm.iterrows():
            fig2.add_trace(
                go.Scatter(
                    mode='markers',
                    x=[r[0]],
                    y=[r[1]],
                    marker=dict(
                        color='black',
                        size=20,
                        line=dict(
                            color='black',
                            width=2
                        ),
                        symbol='x-thin'
                    ),
                    showlegend=True,
                    name=r['index']
                )
            )
            
    return dcc.Graph(figure=fig1), dcc.Graph(figure=fig2)

def compute_benchmarks_g2(df, x, y):
    # todo: add aluminum for both benchmarks
    res = {
        'Copper': [],
        'Iron': [],
        'SCG': [],
        'Steel': [],
    }
    
    # Compute X
    res['Copper'].append(df.loc[df.Notes == 'Copper', x].mean())
    res['Iron'].append(df.loc[df.Notes == 'Iron', x].mean())
    
    mask = df.Notes == 'Single Crystal Graphite'
    res['SCG'].append(df.loc[mask, x].mean())
    
    mask = df.Notes.str.contains('steel', case=False)
    res['Steel'].append(df.loc[mask, x].mean())
    
    # Compute Y
    res['Copper'].append(df.loc[df.Notes == 'Copper', y].mean())
    res['Iron'].append(df.loc[df.Notes == 'Iron', y].mean())
    
    mask = df.Notes == 'Single Crystal Graphite'
    res['SCG'].append(df.loc[mask, y].mean())
    
    mask = df.Notes.str.contains('steel', case=False)
    res['Steel'].append(df.loc[mask, y].mean())
    
    return res