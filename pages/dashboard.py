from dash import Dash, dcc, html, Input, Output, State, page_container, callback
import dash
import os
import pandas as pd
import numpy as np
import plotly.express as px
import dash_bootstrap_components as dbc
import psycopg2
from src.common import get_data_dict

dash.register_page(__name__, path='/')

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(**psycopg2.extensions.parse_dsn(DATABASE_URL))


# ------------------------------ CONSTANTS & STYLE ---------------------------------------
#
#
# ---------------------------------------------------------------------------------------------


CITATION =  "Bulmer, J. S., Kaniyoor, A., Elliott 2008432, J. A., A Meta-Analysis "
"of Conductive and Strong Carbon Nanotube Materials. Adv. Mater. 2021, 33, 2008432. "
CITELINK = "https://doi.org/10.1002/adma.202008432"

LOGO_URL = 'https://secureservercdn.net/45.40.155.190/svz.20f.myftpupload.com/wp-content/uploads/2022/03/Logo1-2-768x768.png'
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


filter_modal = html.Div(
    style={'margin-top': '1rem'},
    children =
    [
        dbc.Button("Adjust filters", id="open", n_clicks=0),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Filters")),
                dbc.ModalBody(children=html.Div(id='filter-fields')),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close", className="ms-auto", n_clicks=0
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
            html.P("Select fields you want to filter on.", className="text-muted"),
            html.P("To reset a filter, remove it from the list.", className='text-muted'),
            html.Div(id='filter-field-picker-div'),
            filter_modal,

            html.Hr(),
            html.H6('Legend'),
            html.Div(id='legend-div'),

            html.Hr(),
            html.P('Doped or Acid Exposure (Yes/ No)'),
            dcc.Checklist(['Yes', 'No'], ['Yes', 'No'], id='dope-control'),
            html.Hr(),

            dbc.Button("Update charts", id="update", n_clicks=0),
        ])
        
    ],
    style=SIDEBAR_STYLE,
)

graph1 = html.Div(
    children=[
        html.B("Boxplots"),
        html.Hr(),
        dcc.Dropdown([], '', multi=False, placeholder='Pick X-axis', id='graph1-xaxis-dropdown'),
        dcc.Dropdown([], '', multi=False, placeholder='Pick Y-axis', id='graph1-yaxis-dropdown'),
        dcc.Checklist(['Log Y'], [], id='graph1-log'),
        html.Div(id='graph1', children=dcc.Graph()),
    ]
)

graph2 = html.Div(
    style={'margin-top': '1rem'},
    children=[
        html.B("Scatterplot"),
        html.Hr(),
        dcc.Dropdown([], '', multi=False, placeholder='Pick X-axis', id='graph2-xaxis-dropdown'),
        dcc.Dropdown([], '', multi=False, placeholder='Pick Y-axis', id='graph2-yaxis-dropdown'),
        dcc.Checklist(['Log X', 'Log Y'], ['Log X', 'Log Y'], id='graph2-log'),
        html.Div(id='graph2', children=dcc.Graph()),
    ]
)

content = html.Div(
    id="page-content",
    style=CONTENT_STYLE,
    children=[graph1, graph2]
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=LOGO_URL, height="30px")),
                        dbc.Col(dbc.NavbarBrand("Idlewild Technologies", class_name="ms-2")),
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

# todo: replace callback DB calls with serve_layout func
layout = dbc.Container([navbar, sidebar, content, footer, html.Div(id='placeholder')], className="bg-secondary")


# ------------------------------ HELPERS ------------------------------------------------------
#
# TODO: move some of these to a common file
# ---------------------------------------------------------------------------------------------

def get_df(cur):
    # get df column names
    cur.execute("""
    SELECT column_name
      FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'df'
         ;
    """)
    cols = [x[0] for x in cur.fetchall()]
    
    cur.execute('select * from df;')
    df = pd.DataFrame(cur.fetchall(), columns=cols)

    return df

def generate_filter_control(c, cur):
    """
    Given a column name `c` and a cursor `cur`,
    generate an appropriate filter control based
    on the column type and values.
    """
    
    res = None
    
    data_dict = get_data_dict(cur)
    df = get_df(cur)
    
    data_type = data_dict.loc[data_dict.colname == c, 'coltype'].values[0]
    
    if data_type == 'numeric':
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
    
    mask = df['Category'].isin(legend) & df['Doped or Acid Exposure (Yes/ No)'].isin(dope)
    
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
    Output('legend-div', 'children'),
    Input('placeholder', 'children')
)
def initialize_legend(placeholder):
    
    with conn.cursor() as cur:
    
        # get df column names
        cur.execute("""
        SELECT column_name
          FROM information_schema.columns
         WHERE table_schema = 'public'
           AND table_name   = 'df'
             ;
        """)
        cols = [x[0] for x in cur.fetchall()]

        # get df
        cur.execute('select * from df;')
        df = pd.DataFrame(cur.fetchall(), columns=cols)
    
    return dcc.Checklist(
        df['Category'].unique(), 
        df['Category'].unique(), 
        labelStyle={'display': 'block'},
        style={"height":300, "width":350, "overflow":"auto"}, 
        id='legend'
    )

@dash.callback(
    Output('filter-field-picker-div', 'children'),
    Input('placeholder', 'children')
)
def initialize_filter_field_picker(placeholder):

    with conn.cursor() as cur:

        # get df column names
        cur.execute("""
        SELECT column_name
          FROM information_schema.columns
         WHERE table_schema = 'public'
           AND table_name   = 'df'
             ;
        """)
        cols = [x[0] for x in cur.fetchall()]

        # get df
        cur.execute('select * from df;')
        df = pd.DataFrame(cur.fetchall(), columns=cols)

    return dcc.Dropdown(
        [c for c in df.columns if c not in ['Category', 'Doped or Acid Exposure (Yes/ No)']], 
        [], 
        multi=True, 
        placeholder='Pick filter fields', 
        id='filter-field-picker'
    )

@dash.callback(
    [
        Output('graph1-xaxis-dropdown', 'options'),
        Output('graph1-yaxis-dropdown', 'options'),
        Output('graph2-xaxis-dropdown', 'options'),
        Output('graph2-yaxis-dropdown', 'options')
    ],
    Input('placeholder', 'children')
)
def initialize_axis_controls(placeholder):
    
    # todo: default values

    with conn.cursor() as cur:
        df = get_df(cur)
        data_dict = get_data_dict(cur).set_index('colname')['coltype']   
        
    numeric_cols = [c for c in df.columns if data_dict.loc[c] == 'numeric']
    categorical_cols = [c for c in df.columns if data_dict.loc[c] != 'numeric']
    
    return [categorical_cols, numeric_cols, numeric_cols, numeric_cols]

@dash.callback(
    Output('filter-fields', 'children'),
    Input('filter-field-picker', 'value'),
    State('filter-fields', 'children')
)
def display_filter_controls(value, children):
        
    res = []
    
    if children is None or children == []:
        new_cols = value
    
    else:
    
        existing_cols = set([ctrl['props']['id']['column'] for ctrl in children])
        new_cols = set(value) - set(existing_cols)
        remove_cols = set(existing_cols) - set(value)

        res = [ctrl for ctrl in children if ctrl['props']['id']['column'] not in remove_cols]
    
    with conn.cursor() as cur:
        for c in new_cols:
            res.append(generate_filter_control(c, cur))

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
    Output('graph2', 'children'),
    Input('update', 'n_clicks'),
    [
        State('graph2-xaxis-dropdown', 'value'), 
        State('graph2-yaxis-dropdown', 'value'),
        State('graph2-log', 'value'),
        State('legend', 'value'), 
        State('dope-control', 'value')
    ],
    State('filter-fields', 'children')
)
def update_bottom_chart(n_clicks, xvar, yvar, log, legend, dope, filters):
    
    with conn.cursor() as cur:
        df = get_df(cur)

    mask = get_filter_mask(filters, legend, dope, df)
    
    return dcc.Graph(
        figure=px.scatter(
            df[mask], 
            x=xvar, 
            y=yvar, 
            log_x='Log X' in log, 
            log_y='Log Y' in log
        )
    )

@dash.callback(
    Output('graph1', 'children'),
    Input('update', 'n_clicks'),
    [
        State('graph1-xaxis-dropdown', 'value'), 
        State('graph1-yaxis-dropdown', 'value'), 
        State('graph1-log', 'value'), 
        State('legend', 'value'), 
        State('dope-control', 'value')
    ],
    State('filter-fields', 'children')
)
def update_top_chart(n_clicks, xvar, yvar, log, legend, dope, filters):
    
    with conn.cursor() as cur:
        df = get_df(cur)

    mask = get_filter_mask(filters, legend, dope, df)
    
    return dcc.Graph(
        figure=px.box(
            df[mask], 
            x=xvar, 
            y=yvar, 
            log_y='Log Y' in log, 
            color='Production Process'
        )
    )
