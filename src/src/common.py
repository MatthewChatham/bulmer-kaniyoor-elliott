import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras as extras
import plotly.graph_objects as go
import math
import plotly.express as px
import os
from dotenv import load_dotenv
from dash import html, dcc
import dash_bootstrap_components as dbc

load_dotenv()

# CONSTANTS -------------------------------------------------------------------

DATABASE_URL = os.environ['DATABASE_URL']

BENCHMARK_COLORS = {
        'Copper': '#B87333',
        'Iron': '#a19d94',
        'Steel': 'white',
        'SCG': 'black'
    }

MARKERS = {
    'Aligned Few-wall CNTs': {
        'marker_symbol': 'diamond',
        'marker_color': '#305ba9'
    },
    'Aligned Multiwall CNTs': {
        'marker_symbol': 'triangle-up',
        'marker_color': '#d12232'
    },
    'Amorphous carbon': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Carbon Fiber': {
        'marker_symbol': 'square',
        'marker_color': 'black'
    },
    'Conductive Polymer': {
        'marker_symbol': 'square',
        'marker_color': '#cc3b8c'
    },
    'Diamond': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'GIC': {
        'marker_symbol': 'square',
        'marker_color': 'black'
    },
    'Glassy Carbon': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Graphene Nanoribbon': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Individual Bundle': {
        'marker_symbol': 'cross',
        'marker_color': '#305ba9'
    },
    'Individual FWCNT': {
        'marker_symbol': 'x',
        'marker_color': '#305ba9'
        
    },
    'Individual Multiwall CNTs': {
        'marker_symbol': 'star',
        'marker_color': '#d12232'
    },
    'Metal': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Metal CNT Composite': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Mott minimum conductivity': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Paper': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Single crystal graphite': {
        'marker_symbol': 'square',
        'marker_color': 'black'
    },
    'Superconductor': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Synthetic fiber': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Unaligned Few-wall CNTs': {
        'marker_symbol': 'circle',
        'marker_color': '#61b84e'
    },
    'Unaligned multiwall CNTs': {
        'marker_symbol': 'square',
        'marker_color': '#ee9752'
    },
    'NaN': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    }
}

CATEGORY_MAPPER = {
	'Aligned Multiwall CNTs': 'Aligned MWCNT',
	'Aligned Few-wall CNTs': 'Aligned FWCNT',
	'Unaligned Few-wall CNTs': 'Unaligned FWCNT',
	'GIC': 'Other Carbons',
	'Individual Multiwall CNTs': 'Individual Structures',
	'Conductive Polymer': 'Other Carbons',
	'Carbon Fiber': 'Other Carbons',
	'Individual FWCNT': 'Individual Structures',
	'Metal': 'Other',
	'Unaligned multiwall CNTs': 'Unaligned MWCNT',
	'Individual Bundle': 'Individual Structures',
	'Metal CNT Composite': 'Other',
	'Single crystal graphite': 'Individual Structures',
	'Synthetic fiber': 'Other',
	'Graphene Nanoribbon': 'Other',
	'Paper': 'Other',
	'Amorphous carbon': 'Other',
	'Glassy Carbon': 'Other',
	'Mott minimum conductivity': 'Other',
	'Superconductor': 'Other',
	'Diamond': 'Other',
}

# Plotting --------------------------------------------------------------------
def compute_benchmarks(df, y):
    res = {
        'Copper': None,
        'Iron': None,
        'SCG': None,
        'Steel': None
    }
    
    res['Copper'] = df.loc[df.Notes == 'Copper', y].mean()
    res['Iron'] = df.loc[df.Notes == 'Iron', y].mean()
    mask = df.Notes == 'Single Crystal Graphite'
    res['SCG'] = df.loc[mask, y].mean()
    
    mask = df.Notes.fillna('').str.contains('steel', case=False)
    res['Steel'] = df.loc[mask, y].mean()
    
    return res

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
    
    mask = df.Notes.fillna('').str.contains('steel', case=False)
    res['Steel'].append(df.loc[mask, x].mean())
    
    # Compute Y
    res['Copper'].append(df.loc[df.Notes == 'Copper', y].mean())
    res['Iron'].append(df.loc[df.Notes == 'Iron', y].mean())
    
    mask = df.Notes == 'Single Crystal Graphite'
    res['SCG'].append(df.loc[mask, y].mean())
    
    mask = df.Notes.fillna('').str.contains('steel', case=False)
    res['Steel'].append(df.loc[mask, y].mean())
    
    return res

def construct_custom_strip(df, x, y):
    traces = []

    # one trace per category/dope combo, with custom color/symbol
    for m in df['Category'].unique():
        for d in df['Doped or Acid Exposure (Yes/ No)'].unique():
        
            mask = (df['Category'] == m) & \
                (df['Doped or Acid Exposure (Yes/ No)'] == d)

            markers = {k.replace('marker_', ''):v for k,v in MARKERS[m].items()}
            markers['opacity'] = 0.8
            
            if d == 'No':
                markers['symbol'] += '-open'
                markers['opacity'] = 0.5

            traces.append({
                'x': df.loc[mask, x],
                'y': df.loc[mask, y],
                'name': m, 
                'marker': markers,
                'customdata': df['Reference'],
            })

    # Update (add) trace elements common to all traces.
    for t in traces:
        t.update({'type': 'box',
                  'boxpoints': 'all',
                  'fillcolor': 'rgba(255,255,255,0)',
                  'hoveron': 'points',
                  'hovertemplate': '%{customdata}',
                  'line': {'color': 'rgba(255,255,255,0)'},
                  'pointpos': 0,
                  'showlegend': True})
    
    return traces


def construct_fig1(df, x, y, log, squash):
    
    df = df[df[x].notnull() & df[y].notnull()]
    
    fig = go.Figure()
    
    if squash:
        print('squashing')
        fig.add_trace(
            go.Box(
                y=df[y],
                name='All',
                boxpoints='all',
                fillcolor='white',
                pointpos=0,
                marker={'color': 'black'},
                line={'color':'black'},
                customdata=df['Reference'],
                hovertemplate='%{customdata}'
                # Don't show or hover on outlier points
                # marker={'opacity':0},
                
                # fillcolor='white',
                # line={
                #     'color': 'gray',
                #     # MARKERS[v]['marker_color'] 
                #     # if x == 'Category' else 'gray'
                # }
            )
        )
        
    else:
    
        for v in df[x].unique():
            tracedf = df.loc[df[x] == v]

            fig.add_trace(
                go.Box(
                    y=tracedf[y],
                    name=v,
                    # Don't show or hover on outlier points
                    marker={'opacity':0},
                    hoveron='boxes',
                    fillcolor='white',
                    line={
                        'color': 'gray',
                        # MARKERS[v]['marker_color'] 
                        # if x == 'Category' else 'gray'
                    },
                )
            )

        fig.add_traces(construct_custom_strip(df, x, y))
    
    fig.update_yaxes(
        type='log' if log else 'linear',
        nticks=10
    )
    
    fig.update_layout(
        showlegend=False, 
        yaxis_title=y,
        xaxis_title=x
    )
    
    return fig

def construct_fig2(df, x, y, logx, logy, squash):
    
    df = df[df[x].notnull() & df[y].notnull()]
    
    symbol = color = 'Category'
    symbol_map = {k:v['marker_symbol'] for k,v in MARKERS.items()}
    color_map = {k:v['marker_color'] for k,v in MARKERS.items()}
    
    fig = px.scatter(
        df,
        x=x, 
        y=y, 
        log_x=logx, 
        log_y=logy,
        symbol=symbol,
        symbol_map=symbol_map,
        color=color,
        color_discrete_map=color_map,
        hover_data=['Reference']
    )
    
    if squash:
        fig.update_traces(marker={'symbol':'circle', 'color':'black'})
        fig.update_layout(showlegend=False)
    
    return fig

# Data processing -------------------------------------------------------------

def clean(df, numeric_cols):
    """
    Given a DataFrame, coerce numeric_cols to numeric
    and drop unnamed/duped columns.
    """
    
    df = df.copy()
    dropped_cols = list()
    
    # -----------------------STRIP WHITESPACE FROM VALUES ---------------------
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    
    # ----------------------- STANDARDIZE NANS --------------------------------
    for c in df.columns:
        mask = (
            df[c].astype(str).str.lower()
            .str.replace('\s+', '', regex=True)
            .str.contains('notreported')
            
            |
            
            df[c].astype(str).str.lower().isin(['nan'])
        )
        df.loc[mask, c] = np.NaN
    
    # ----------------------DROP UNNAMED AND DUPED COLUMNS --------------------
    drop_cols = [c for c in df.columns if 'Unnamed' in c or c.endswith('.1')]
    df = df.drop(drop_cols, axis=1)
    
    # -----------------------CONVERT NUMERIC COLS TO FLOAT --------------------
    for c in df.columns:
        if c in numeric_cols:
            df[c] = pd.to_numeric(
                df[c],
                errors='coerce' # silently coerce non-numeric values to NaN
            )
    
    return {'data': df, 'dropped': drop_cols}

# DB funcs --------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(**psycopg2.extensions.parse_dsn(DATABASE_URL))

def get_dd():
    conn = get_conn()
    
    with conn, conn.cursor() as cur:
            cur.execute('select * from dd;')
            dd = pd.DataFrame(cur.fetchall(), columns=['colname', 'coltype'])
            dd = {r['colname']:r['coltype'] for i,r in dd.iterrows()}
            
    conn.close()
    
    return dd

def get_df():
    conn = get_conn()
    
    with conn, conn.cursor() as cur:
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
        
    conn.close()

    return df

def update_database(df, dd):
    """
    
    Given a pandas DataFrame and a dd representing 
    column types, load/update the database.
    
    """
    
    # fail if not all columns have types
    assert set(df.columns).issubset(set(dd.keys()))
    
    conn = get_conn()
    
    with conn, conn.cursor() as cur:

        print('dropping tables')
        # drop tables
        for table_name in ['df', 'dd']:
            cur.execute(f"DROP TABLE IF EXISTS {table_name};")

        print('recreating dd')
        # create and insert into dd
        cur.execute("""
            CREATE TABLE dd(
                colname text PRIMARY KEY,
                coltype text NOT NULL
            );
        """)
        print('inserting into dd')
        qstring = "INSERT INTO dd VALUES %s"
        extras.execute_values(cur, qstring, [(k,v) for k,v in dd.items()])

        print('recreating df')
        # create df
        colnames = df.columns
        qstring = """CREATE TABLE df("""
        to_join = []
        for c in colnames:
            to_join.append(f""""{c}" {'numeric' if dd[c] == 'numeric' else 'text'}""")
        qstring += ',\n'.join(to_join)
        qstring += ");"
        cur.execute(qstring)

        print('inserting into df')
        # insert into df
        qstring = "INSERT INTO df VALUES %s"
        records = []
        for i,r in df.iterrows():
            records.append(tuple(r.values))
        extras.execute_values(cur, qstring, records)
        
    conn.close()
    
# ------------------------------ FILTERS --------------------------------------
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
    null_values,
    apply_filters
):
    """
    Given a list of `filters`, the `legend` and `dope` controls,
    and a pandas `df`, build a mask.
    """
    
    ctrl_cols = [i['column'] for i in ctrl_idx]
    
    mask = df['Category'].isin(legend) & \
    df['Doped or Acid Exposure (Yes/ No)'].isin(dope)
    
    if not ctrl_values or not apply_filters:
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