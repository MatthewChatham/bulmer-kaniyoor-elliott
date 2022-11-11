from dash import (
    Dash, dcc, html, Input, Output, State, 
    page_container, callback, dash_table, ctx
)
import dash
import os
import pandas as pd
import numpy as np
import plotly.express as px
import dash_bootstrap_components as dbc
import psycopg2
from src.common import get_dd, get_df, CATEGORY_MAPPER, MARKERS

dash.register_page(__name__, path='/')

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(**psycopg2.extensions.parse_dsn(DATABASE_URL))


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


# ------------------------------ PREDEFINED LAYOUT ELEMENTS -----------------------------------
#
#
# ---------------------------------------------------------------------------------------------

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
                ['Log Y'], 
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
                ['Log X', 'Log Y'], 
                ['Log X', 'Log Y'], 
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


# ------------------------------ LAYOUT -------------------------------------------------------
#
#
# ---------------------------------------------------------------------------------------------

def serve_layout():
    
    with conn.cursor() as cur:
        df = get_df(cur)
        dd = get_dd(cur)
    
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


# ------------------------------ HELPERS ------------------------------------------------------
#
#
# ---------------------------------------------------------------------------------------------


def generate_filter_control(c, cur, df, dd):
    """
    Given a column name `c` and a cursor `cur`,
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

# ------------------------------ CALLBACKS ----------------------------------------------------
#
#
# ---------------------------------------------------------------------------------------------

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
    
        existing_cols = set([ctrl['props']['id']['column'] for ctrl in children])
        new_cols = set(value) - set(existing_cols)
        remove_cols = set(existing_cols) - set(value)

        res[0] = [ctrl for ctrl in children if ctrl['props']['id']['column'] not in remove_cols]
    
    with conn.cursor() as cur:
        for c in new_cols:
            res[0].append(generate_filter_control(c, cur, df, dd))

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
        
    g1 = dcc.Graph(
        figure=px.box(
            df[mask], 
            x=g1x, 
            y=g1y, 
            log_y='Log Y' in g1log, 
            # color='Production Process'
        )
    )
    
    g2 = dcc.Graph(
        figure=px.scatter(
            df[mask], 
            x=g2x, 
            y=g2y, 
            log_x='Log X' in g2log, 
            log_y='Log Y' in g2log,
            symbol='Category',
            symbol_map={k:v['marker_symbol'] for k,v in MARKERS.items()},
            color='Category',
            color_discrete_map={k:v['marker_color'] for k,v in MARKERS.items()}
        )
    )
    

    
    
    return g1, g2
