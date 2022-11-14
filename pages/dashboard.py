# Plotly
import plotly.express as px
import plotly.graph_objects as go

# Dash
import dash
from dash import (
    Dash, dcc, html, Input, Output, State, 
    page_container, callback, dash_table, ctx
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
APP_NAME = 'CNT Meta-Analysis Explorer'

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 30,
    "left": 0,
    "bottom": 0,
    "width": "25rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "25rem",
    "margin-right": "3rem",
    "padding": "5rem 0rem",
}


# ------------------------------ PREDEFINED LAYOUT ELEMENTS -------------------
#
#
# -----------------------------------------------------------------------------
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=LOGO_URL, height="30px")),
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
    color="#ffffff",
    fixed="top",
)

def serve_sidebar(df):
    filter_modal = html.Div(
        style={'margin-top': '1rem'},
        children =
        [
            dbc.Button("Adjust filters", id="open", n_clicks=0),
            dbc.Button("Reset filters", id="reset-filters", n_clicks=0),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Filters")),
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
                is_open=False,
                fullscreen=True
            ),
        ]
    )
    
    sidebar = html.Div(
        [
            html.H2(APP_NAME, className="display-7"),
            html.Hr(),
            html.Div([
                html.H6("Filter Field Picker"),
                html.P(
                    "Select fields you want to filter on.", 
                    className="text-muted"
                ),
                html.P(
                    "To reset a filter, remove it from the list.", 
                    className='text-muted'
                ),
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
                html.H6('Legend'),
                html.Div(
                    id='legend-div',
                    children=[
                        dbc.Button(
                            'Check/uncheck all', 
                            id='legend-toggle-all'
                        ),
                        dcc.Checklist(
                            df['Category'].unique(), 
                            [
                                c for c in CATEGORY_MAPPER.keys() 
                                 if CATEGORY_MAPPER[c] != 'Other'
                            ], 
                            labelStyle={'display': 'block'},
                            style={
                                "height":300, 
                                "width":350, 
                                "overflow":"auto"
                            }, 
                            id='legend'
                        )
                    ]
                ),
                html.Hr(),
                
                html.P('Doped or Acid Exposure (Yes/ No)'),
                dcc.Checklist(
                    ['Yes', 'No'], 
                    ['Yes', 'No'], 
                    id='dope-control'
                ),
                html.Hr(),                

                dbc.Button("Update charts", id="update", n_clicks=0),
            ])

        ],
        style=SIDEBAR_STYLE,
    )
    
    return sidebar

def serve_content(df, dd):
    numeric_cols = [c for c in df.columns if dd[c] == 'numeric']
    categorical_cols = [c for c in df.columns if dd[c] != 'numeric']
    
    graph1 = html.Div(
        children=[
            html.B("Boxplots"),
            html.Hr(),
            dcc.Dropdown(
                categorical_cols, 
                'Category', 
                multi=False, 
                placeholder='Pick X-axis', 
                id='graph1-xaxis-dropdown'
            ),
            dcc.Dropdown(
                numeric_cols, 
                'Conductivity (MSm-1)', 
                multi=False, 
                placeholder='Pick Y-axis', 
                id='graph1-yaxis-dropdown'
            ),
            dcc.Checklist(
                ['Log Y', 'Squash', 'Show Benchmarks'], 
                ['Log Y'], 
                id='graph1-log'
            ),
            html.Div(
                id='graph1', 
                children=dcc.Graph()
            ),
        ]
    )

    graph2 = html.Div(
        style={'margin-top': '1rem'},
        children=[
            html.B("Scatterplot"),
            html.Hr(),
            dcc.Dropdown(
                numeric_cols, 
                'Tensile Strength (MPa)', 
                multi=False, 
                placeholder='Pick X-axis', 
                id='graph2-xaxis-dropdown'
            ),
            dcc.Dropdown(
                numeric_cols, 
                'Conductivity (MSm-1)', 
                multi=False, 
                placeholder='Pick Y-axis', 
                id='graph2-yaxis-dropdown'
            ),
            dcc.Checklist(
                ['Log X', 'Log Y', 'Squash', 'Show Benchmarks'], 
                ['Log X', 'Log Y', 'Show Benchmarks'], 
                id='graph2-log'
            ),
            html.Div(
                id='graph2', 
                children=dcc.Graph()
            ),
        ]
    )

    content = html.Div(
        id="page-content",
        style=CONTENT_STYLE,
        children=[graph1, graph2]
    )
    
    return content

footer = dbc.Navbar(
    dbc.Container([
        html.H6([
            CITATION,
            html.A(CITELINK, href=CITELINK)
        ], className="text-muted"),
    ]),
    color="#ffffff", 
    fixed="bottom"
)


# ------------------------------ LAYOUT ---------------------------------------
#
# -----------------------------------------------------------------------------

def serve_layout():
    
    df = get_df()
    dd = get_dd()
    
    # store the df in memory so callbacks don't need DB calls
    store_df = dcc.Store(
        id='df',
        data=df.to_dict(),
        storage_type='memory'
    )

    store_dd = dcc.Store(
        id='dd',
        data=dd,
        storage_type='memory'
    )
    
    return dbc.Container(
        [
            store_df,
            store_dd,
            navbar, 
            serve_sidebar(df),
            serve_content(df, dd),
            footer,
        ], 
        className="bg-secondary"
    )

layout = serve_layout
# layout = html.Div('test')


# ------------------------------ HELPERS --------------------------------------
#
#
# -----------------------------------------------------------------------------


def generate_filter_control(c, df, dd):
    """
    Given a column name `c`,
    generate an appropriate filter control based
    on the column type and values.
    """
    
    res = None
    
    if dd[c] == 'numeric':
        res = dcc.RangeSlider(
            df[c].astype(float).min(), 
            df[c].astype(float).max(), 
            id={'type': 'filter-control', 'column': c}
        )
    else:
        res = dcc.Dropdown(
            df[c].dropna().unique(), 
            multi=True, 
            placeholder=c, 
            id={'type': 'filter-control', 'column': c}
        )
        
    return res


def get_filter_mask(filters, legend, dope, df):
    """
    Given a list of `filters`, the `legend` and `dope` controls,
    and a pandas `df`, build a mask.
    """
    
    mask = df['Category'].isin(legend) & \
    df['Doped or Acid Exposure (Yes/ No)'].isin(dope)
    
    if not filters:
        return mask
    
    for i,f in enumerate(filters):
        c = f['props']['id']['column']
        
        try:
            vals = f['props']['value']
        except KeyError:
            continue # ignore filters who haven't had their values set yet
            
        if f['type'] == 'RangeSlider':
            m = df[c].between(*vals) | df[c].isnull()
        elif f['type'] == 'Dropdown':
            m = df[c].isin(vals) | df[c].isnull()
        
        mask = mask & m
        
    return mask

# ------------------------------ CALLBACKS ------------------------------------
#
#
# -----------------------------------------------------------------------------

@dash.callback(
    Output('legend', 'value'),
    Input('legend-toggle-all', 'n_clicks'),
    State('legend', 'options'),
    State('legend', 'value')
)
def legend_toggle_all(n_clicks, options, value):
    if n_clicks is None:
        return value
    
    return [] if n_clicks %2 == 0 else options
    

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
        State('filter-fields', 'children'),
        State('df', 'data'),
        State('dd', 'data')
    ]
)
def display_filter_controls(value, n_clicks, children, df, dd):
    
    if ctx.triggered_id == 'reset-filters':
        return [], []
    
    df = pd.DataFrame.from_dict(df)
        
    res = [[], value]
    
    if children is None or children == []:
        new_cols = value
    
    else:
    
        existing_cols = set([
            ctrl['props']['id']['column'] 
            for ctrl in children
        ])
        new_cols = set(value) - set(existing_cols)
        remove_cols = set(existing_cols) - set(value)

        res[0] = [
            ctrl for ctrl in children 
            if ctrl['props']['id']['column'] not in remove_cols
        ]
    
    for c in new_cols:
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
        State('filter-fields', 'children'),
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
    filters,
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
    
    mask = get_filter_mask(filters, legend, dope, df)
    
    fig1 = construct_fig1(
        df[mask], 
        g1x, 
        g1y, 
        'Log Y' in g1log,
        squash='Squash' in g1log
    )
        
    fig2 = construct_fig2(
        df[mask], 
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