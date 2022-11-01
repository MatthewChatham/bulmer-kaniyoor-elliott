from dash import Dash, dcc, html, Input, Output, State, page_container, callback
import dash
import os
import pandas as pd
import numpy as np
import plotly.express as px
import dash_bootstrap_components as dbc
import psycopg2

dash.register_page(__name__, path='/')

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(**psycopg2.extensions.parse_dsn(DATABASE_URL))


# ------------------------------ CONSTANTS & STYLE ---------------------------------------
#
#
# ---------------------------------------------------------------------------------------------


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
                dbc.ModalBody(id='filter-fields', children=html.Div(id='filter-fields')),
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
        html.P('display', id='print'),
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
        # dcc.Dropdown(dtypes[dtypes == 'categorical'].index, 'Category', multi=False, placeholder='Pick X-axis', id='graph1-xaxis-dropdown'),
        # dcc.Dropdown(dtypes[dtypes == 'numeric'].index, 'Conductivity (MSm-1)', multi=False, placeholder='Pick Y-axis', id='graph1-yaxis-dropdown'),
        dcc.Checklist(['Log Y'], [], id='graph1-log'),
        html.Div(id='graph1', children=dcc.Graph()),
    ]
)

graph2 = html.Div(
    style={'margin-top': '1rem'},
    children=[
        html.B("Scatterplot"),
        html.Hr(),
        # dcc.Dropdown(dtypes[dtypes == 'numeric'].index, 'Tensile Strength (MPa)', multi=False, placeholder='Pick X-axis', id='graph2-xaxis-dropdown'),
        # dcc.Dropdown(dtypes[dtypes == 'numeric'].index, 'Conductivity (MSm-1)', multi=False, placeholder='Pick Y-axis', id='graph2-yaxis-dropdown'),
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

citation =  "Bulmer, J. S., Kaniyoor, A., Elliott 2008432, J. A., A Meta-Analysis "
"of Conductive and Strong Carbon Nanotube Materials. Adv. Mater. 2021, 33, 2008432. "
cite_link = "https://doi.org/10.1002/adma.202008432"

footer = dbc.Navbar(
    dbc.Container([
        html.H6([
            citation,
            html.A(cite_link, href=cite_link)
        ], className="text-muted"),
    ]),
    color="#ffffff", 
    fixed="bottom"
)


# ------------------------------ LAYOUT -------------------------------------------------------
#
#
# ---------------------------------------------------------------------------------------------

# todo: look into making this a function or wrap in a callback to account for DB calls
layout = dbc.Container([navbar, sidebar, content, footer], className="bg-secondary")


# ------------------------------ CALLBACKS ----------------------------------------------------
#
#
# ---------------------------------------------------------------------------------------------


# @dash.callback(Output('legend-div', 'children'))
# def initialize_legend():
#     cur = conn.cursor()

#     # get df column names
#     cur.execute("""
#     SELECT column_name
#       FROM information_schema.columns
#      WHERE table_schema = 'public'
#        AND table_name   = 'df'
#          ;
#     """)
#     cols = [x[0] for x in cur.fetchall()]
    
#     # get df
#     cur.execute('select * from df;')
#     df = pd.DataFrame(cur.fetchall(), columns=cols)
    
#     cur.close()
    
#     return dcc.Checklist(df['Category'].unique(), df['Category'].unique(), labelStyle={'display': 'block'},
#         style={"height":300, "width":350, "overflow":"auto"}, id='legend')

# @dash.callback(Output('filter-field-picker-div', 'children'))
# def initialize_filter_field_picker():

#     cur = conn.cursor()

#     # get df column names
#     cur.execute("""
#     SELECT column_name
#       FROM information_schema.columns
#      WHERE table_schema = 'public'
#        AND table_name   = 'df'
#          ;
#     """)
#     cols = [x[0] for x in cur.fetchall()]
    
#     # get df
#     cur.execute('select * from df;')
#     df = pd.DataFrame(cur.fetchall(), columns=cols)
    
#     cur.close()

#     return dcc.Dropdown(
#         [c for c in df.columns if c not in ['Category', 'Doped or Acid Exposure (Yes/ No)']], 
#         [], 
#         multi=True, 
#         placeholder='Pick filter fields', 
#         id='filter-field-picker'
#     )

# @dash.callback(
#     Output('filter-fields', 'children')
# )
# def initialize_filter_controls():

#     # get data_dict
#     cur = conn.cursor()
#     cur.execute('select * from data_dict;')
#     dtypes = pd.DataFrame(
#         cur.fetchall(), 
#         columns=['colname', 'coltype']
#     ).set_index('colname').coltype

#     # get df column names
#     cur.execute("""
#     SELECT column_name
#       FROM information_schema.columns
#      WHERE table_schema = 'public'
#        AND table_name   = 'df'
#          ;
#     """)
#     cols = [x[0] for x in cur.fetchall()]
    
#     # get df
#     cur.execute('select * from df;')
#     df = pd.DataFrame(cur.fetchall(), columns=cols)

#     cur.close()
    
#     ## filter controls
#     cat = dtypes[dtypes == 'categorical'].index.tolist()
#     cat = [c for c in cat if c in cols]
#     categorical_dropdowns = [
#         html.Div(dcc.Dropdown(
#             df[c].dropna().unique(), 
#             multi=True, 
#             placeholder=c, 
#             id=f'{c.replace(".", "").replace("{", "")}-control'
#         ), id=f'{c.replace(".", "").replace("{", "")}-controldiv')
#         for c in cols if c in cat
#     ]
#     num = dtypes[dtypes == 'numeric'].index.drop_duplicates().tolist()
#     num = [c for c in num if c in cols]

#     numeric_ranges = [
#         html.Div(
#             [
#                 html.Div(c),
#                 dcc.RangeSlider(df[c].astype(float).min(), df[c].astype(float).max(), id=f'{c.replace(".", "").replace("{", "")}-control')
#             ],
#         id=f'{c.replace(".", "").replace("{", "")}-controldiv')

#         for c in cols if c in num]
#     filter_fields = [html.Div(categorical_dropdowns, style={'width': '49%'}), html.Div(numeric_ranges, style={'width': '45%'})]
    
#     return filter_fields

# @dash.callback(
#     [
#         Output(f'{c.replace(".", "").replace("{", "")}-controldiv', 'style') 
#         for c in cat
#     ] +
#     [
#         Output(f'{c.replace(".", "").replace("{", "")}-control', 'value') 
#         for c in cat
#     ],
#     [Input('filter-field-picker', 'value')],
#     [State(f'{c.replace(".", "").replace("{", "")}-control', 'value') for c in cat]
# )
# def update_cat_filters(fields, *states):
#     res_vis = list()
#     res_val = list()
    
#     for i, c in enumerate(cat):
#         if c in fields:
#             res_vis.append({'display': 'block'})
#             res_val.append(states[i])
#         else:
#             res_vis.append({'display': 'none'})
#             res_val.append([])
        
#     return res_vis + res_val

# @dash.callback(
#     [
#         Output(f'{c.replace(".", "").replace("{", "")}-controldiv', 'style') 
#         for c in num
#     ] +
#     [
#         Output(f'{c.replace(".", "").replace("{", "")}-control', 'value') 
#         for c in num
#     ],
#     [Input('filter-field-picker', 'value')],
#     [
#         State(f'{c.replace(".", "").replace("{", "")}-control', 'value') 
#         for c in num
#     ]
# )
# def update_num_filters(fields, *states):
#     res_vis = list()
#     res_val = list()
    
#     for i, c in enumerate(num):
#         if c in fields:
#             res_vis.append({'display': 'block'})
#             res_val.append(states[i])
#         else:
#             res_vis.append({'display': 'none'})
#             res_val.append([df[c].min(), df[c].max()])
        
#     return res_vis + res_val

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

# @dash.callback(
#     Output('graph2', 'children'),
#     Input('update', 'n_clicks'),
#     [
#         State('graph2-xaxis-dropdown', 'value'), 
#         State('graph2-yaxis-dropdown', 'value'),
#         State('graph2-log', 'value'), 
#         State('legend', 'value'), 
#         State('dope-control', 'value')
#     ] +
#     [
#         State(f'{c.replace(".", "").replace("{", "")}-control', 'value') 
#         for c in cat
#     ] +
#     [
#         State(f'{c.replace(".", "").replace("{", "")}-control', 'value') 
#         for c in num
#     ]
# )
# def update_bottom_chart(n_clicks, xvar, yvar, log, legend, dope, *filter_states):
#     mask = df['Category'].isin(legend) & df['Doped or Acid Exposure (Yes/ No)'].isin(dope)
    
#     # categorical filter masks
#     catmask = pd.Series([True]*len(df))
#     for i, c in enumerate(cat):
#         vals = filter_states[i]
#         if vals == [] or vals is None:
#             continue
#         m = df[c].isin(vals) | df[c].isnull()
#         catmask = catmask & m
        
#     # numeric filter masks
#     nummask = pd.Series([True]*len(df))
#     for i, c in enumerate(num):
#         vals = filter_states[i + len(cat)]
#         if vals == [] or vals is None:
#             continue
#         m = df[c].between(*vals) | df[c].isnull()
#         nummask = nummask & m
    
    
#     fig = px.scatter(df[mask & catmask & nummask], x=xvar, y=yvar, log_x='Log X' in log, log_y='Log Y' in log)
#     return dcc.Graph(figure=fig)

# @dash.callback(
#     Output('graph1', 'children'),
#     Input('update', 'n_clicks'),
#     [
#         State('graph1-xaxis-dropdown', 'value'), 
#         State('graph1-yaxis-dropdown', 'value'), 
#         State('graph1-log', 'value'), 
#         State('legend', 'value'), 
#         State('dope-control', 'value')
#     ] + 
#     [
#         State(f'{c.replace(".", "").replace("{", "")}-control', 'value') 
#         for c in cat
#     ] +
#     [
#         State(f'{c.replace(".", "").replace("{", "")}-control', 'value') 
#         for c in num
#     ]
# )
# def update_top_chart(n_clicks, xvar, yvar, log, legend, dope, *filter_states):
#     mask = df['Category'].isin(legend) & df['Doped or Acid Exposure (Yes/ No)'].isin(dope)
    
#     # categorical filter masks
#     catmask = pd.Series([True]*len(df))
#     for i, c in enumerate(cat):
#         vals = filter_states[i]
#         print(c, vals)
#         if vals == [] or vals is None:
#             continue
#         m = df[c].isin(vals) | df[c].isnull()
#         catmask = catmask & m
        
#     # numeric filter masks
#     nummask = pd.Series([True]*len(df))
#     for i, c in enumerate(num):
#         vals = filter_states[i + len(cat)]
#         print(c, vals)
#         if vals == [] or vals is None:
#             continue
#         m = df[c].between(*vals) | df[c].isnull()
#         print(m.sum())
#         nummask = nummask & m
#     print(nummask.sum())
    
#     fig = px.box(df[mask & catmask & nummask], x=xvar, y=yvar, log_y='Log Y' in log, color='Production Process')
#     return dcc.Graph(figure=fig)