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

dash.register_page(__name__)

DATABASE_URL = os.environ['DATABASE_URL']
LOGIN_USERNAME = os.environ['LOGIN_USERNAME']
LOGIN_PASSWORD = os.environ['LOGIN_PASSWORD']

conn = psycopg2.connect(**psycopg2.extensions.parse_dsn(DATABASE_URL))

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


def clean(df, numeric_cols):
    """
    Given a DataFrame, coerce numeric_cols to numeric
    and drop unnamed/duped columns.
    """
    
    df = df.copy()
    dropped_cols = list()
    
    # DROP UNNAMED AND DUPED COLUMNS -------------------------------------------------
    to_drop = [c for c in df.columns if 'Unnamed' in c or c.endswith('.1')]
    for c in to_drop:
        df.pop(c)
    dropped_cols = to_drop
    
    # CONVERT NUMERIC COLS TO FLOAT -------------------------------------------------
    for c in df.columns:
        if c in numeric_cols:
            df[c] = pd.to_numeric(
                df[c],
                errors='coerce' # silently coerce non-numeric values to NaN
            )

    return {'data': df, 'dropped': dropped_cols}

def update_database(df, data_dict):
    """
    
    Given a pandas DataFrame representing a data upload,
    and a data_dict representing column types,
    update the database accordingly.
    
    """
    
    # convert data_dict df to actual dict
    data_dict = {r['colname']:r['coltype'] for i,r in data_dict.iterrows()}
    
    # fail if not all columns have types
    assert set(df.columns).issubset(set(data_dict.keys()))
    
    cur = conn.cursor()
    
    # drop tables
    for table_name in ['df', 'data_dict']:
        cur.execute(f"DROP TABLE IF EXISTS {table_name};")

    # create and insert into data_dict
    cur.execute("""
        CREATE TABLE data_dict(
            colname text PRIMARY KEY,
            coltype text NOT NULL
        );
    """)
    qstring = "INSERT INTO data_dict VALUES %s"
    extras.execute_values(cur, qstring, [(k,v) for k,v in data_dict.items()])
    
    # create df
    colnames = df.columns
    qstring = """CREATE TABLE df("""
    to_join = []
    for c in colnames:
        to_join.append(f""""{c}" {'numeric' if data_dict[c] == 'numeric' else 'text'}""")
    qstring += ',\n'.join(to_join)
    qstring += ");"
    cur.execute(qstring)
    
    # insert into df
    qstring = "INSERT INTO df VALUES %s"
    records = []
    for i,r in df.iterrows():
        records.append(tuple(r.values))
    extras.execute_values(cur, qstring, records)
    
    # commit changes & close database
    conn.commit()
    cur.close()

    
def get_data_dict():
    
    with conn.cursor() as cur:
        cur.execute('select * from data_dict;')
        data_dict = pd.DataFrame(cur.fetchall(), columns=['colname', 'coltype'])
    
    return data_dict

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
        data_dict = get_data_dict()

        cleaned_cols = [c for c in df_raw.columns if not 'Unnamed' in c and not c.endswith('.1')]
        new_cols = not set(cleaned_cols).issubset(set(data_dict.colname))

        if not new_cols:
            numeric_cols = data_dict.loc[data_dict.coltype == 'numeric', 'colname'].tolist()
            clean_result = clean(df_raw, numeric_cols)

            update_database(clean_result['data'], data_dict)

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
            new_colnames = set(cleaned_cols) - set(data_dict.colname)
            
            res_style = goto('checklist')
            res_children[2] = [
                html.P('New columns found. Please select those which are numeric and reupload.'),
                dcc.Checklist([c for c in new_colnames], [], id='numeric-checklist'),
                dbc.Button(id='numeric-submit', children='Submit')
            ]
    

    elif ctx.triggered_id == 'numeric-submit':
        
        # add new column to dictionary
        with conn.cursor() as cur:
            qstring = "INSERT INTO data_dict VALUES %s"
            extras.execute_values(cur, qstring, [(c, 'numeric' if c in numeric_cols else 'text') for c in new_colnames])
        
        res_style = goto('upload')

        
    return res_style + res_children
