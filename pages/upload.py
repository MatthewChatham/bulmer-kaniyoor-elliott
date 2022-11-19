import base64
import datetime
import io

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table, ctx

import dash_bootstrap_components as dbc

import pandas as pd
import numpy as np

import psycopg2
import psycopg2.extras as extras
import os

from src.db import get_conn, get_dd, update_database
from src.upload import clean

dash.register_page(__name__)

DATABASE_URL = os.environ['DATABASE_URL']
LOGIN_USERNAME = os.environ['LOGIN_USERNAME']
LOGIN_PASSWORD = os.environ['LOGIN_PASSWORD']

# ------------------------------ HELPER FUNCTIONS ---------------------------------------------
#
#
# ---------------------------------------------------------------------------------------------


def parse_contents(contents):
    """
    Parse raw file contents into a pandas DataFrame.
    """
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    
    df = pd.read_excel(io.BytesIO(decoded))

    return df

    
def check_credentials(username, password):
    return username == LOGIN_USERNAME and password == LOGIN_PASSWORD

# ------------------------------ LAYOUT FUNCTIONS ---------------------------------------------
#
#
# ---------------------------------------------------------------------------------------------


def upload_controls():
    return [
        dcc.Upload(
            id='upload',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            }
        )
    ]

def login_controls(msg='Enter credentials.'):
    return [
        dbc.Alert(id='login-alert', children=msg),
        dbc.Input(id='login-username', placeholder='username'),
        dbc.Input(id='login-password', placeholder='password'),
        dbc.Button(id='login-submit', children='Submit')
    ]

def numeric_controls():
    return [
        dcc.Checklist(id='numeric-checklist'),
        dbc.Button(id='numeric-submit', children='Numeric Submit')
    ]


# ------------------------------ LAYOUT -------------------------------------------------------
#
#
# ---------------------------------------------------------------------------------------------

layout = html.Div(
    id='overall-div',
    # one div per page
    children=[
        html.Div(id='login-div', children=login_controls()),
        html.Div(id='upload-div', children=upload_controls()),
        html.Div(id='numeric-div', children=numeric_controls()),
    ]
)

# ------------------------------ CALLBACKS ----------------------------------------------------
#
#
# ---------------------------------------------------------------------------------------------

def goto(page):
    
    pages = ['login', 'upload', 'checklist']
    
    if page not in pages:
        raise Exception('passed a bad value to goto!')
    
    res = [
        {'display': 'none'},
        {'display': 'none'},
        {'display': 'none'}
    ]
    
    idx = pages.index(page)
    
    res[idx]['display'] = 'block'
    
    return res
    
@dash.callback(
    [
        # STYLES ---------------------
        Output('login-div', 'style'),
        Output('upload-div', 'style'),
        Output('numeric-div', 'style'),
        
        # CHILDREN -------------------
        Output('login-div', 'children'),
        Output('upload-div', 'children'),
        Output('numeric-div', 'children')
    ],
    [
        Input('login-submit', 'n_clicks'),
        Input('upload', 'contents'),
        Input('numeric-submit', 'n_clicks')
    ],
    [
        State('login-username', 'value'),
        State('login-password', 'value'),
        State('numeric-checklist', 'value'),
        State('numeric-checklist', 'options')
    ]
)
def callback(lclicks, contents, nclicks, username, password, numeric_cols, new_colnames):
    
    res_style = goto('login')
    res_children = [
        login_controls(),
        upload_controls(),
        numeric_controls()
    ]
    

    if ctx.triggered_id == 'login-submit':
        
        if check_credentials(username, password):
            res_style = goto('upload')
            
        else:
            res_children[0] = login_controls('Incorrect credentials.')


    elif ctx.triggered_id == 'upload':
        df_raw = parse_contents(contents)
        
        dd = get_dd()

        cleaned_cols = [c for c in df_raw.columns if not 'Unnamed' in c and not c.endswith('.1')]
        new_cols = not set(cleaned_cols).issubset(set(dd.keys()))

        if not new_cols:
            numeric_cols = [k for k in dd if dd[k] == 'numeric']
            
            print('cleaning')
            clean_result = clean(df_raw, numeric_cols)

            print('updating')
            update_database(clean_result['data'], dd)

            print('prepping result')
            msg = f'''The following columns were dropped either because 
            they were unnamed or because their names are duplicates: 
            {clean_result["dropped"]}.'''

            res_style = goto('upload')
            res_children[1] = [
                html.P('File uploaded successfully.'),
                html.P(msg),
                html.P([
                    html.Span([
                        'Return to the ',
                        html.A('dashboard', href='/'), 
                        ' to see the updated charts.'
                    ])
                ])
            ]

        else:
            new_colnames = set(cleaned_cols) - set(dd.keys())
            
            res_style = goto('checklist')
            res_children[2] = [
                html.P('New columns found. Please select those which are numeric and reupload.'),
                dcc.Checklist([c for c in new_colnames], [], id='numeric-checklist'),
                dbc.Button(id='numeric-submit', children='Submit')
            ]
    

    elif ctx.triggered_id == 'numeric-submit':
        
        conn = get_conn()
        
        # add new column to dictionary
        with conn, conn.cursor() as cur:
            qstring = "INSERT INTO dd VALUES %s"
            extras.execute_values(cur, qstring, [(c, 'numeric' if c in numeric_cols else 'text') for c in new_colnames])
            
        conn.close()
        
        res_style = goto('upload')

        
    return res_style + res_children
