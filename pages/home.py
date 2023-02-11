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
import scipy.stats as stats

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

def serve_content(df, dd):
    numeric_cols = [c for c in df.columns if dd[c] == 'numeric']
    categorical_cols = [c for c in df.columns if dd[c] != 'numeric']
    
    include = [
        'Aligned Multiwall CNTs',
        'Aligned Few-wall CNTs',
        'Individual Multiwall CNTs',
        'Individual Bundle',
        'Individual FWCNT',
        'GIC',
        'Carbon Fiber'
        
    ]
    mask = df.Category.isin(include)
    fig1 = construct_fig1(
        df[mask], 
        'Category', 
        'Conductivity (MSm-1)', 
        True,
        squash=False,
        bm=compute_bm_g1(df, 'Conductivity (MSm-1)')
    )
    
    graph1 = html.Div(
        [
            
            # Graph 1
            html.B("Conductivity vs Carbon Category"),
            
            dbc.Row([
                dbc.Col(
                    id='graph1', 
                    children=dcc.Graph(figure=fig1)
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
    
    mask = df.Category.isin(['Aligned Few-wall CNTs'])
    fig3 = construct_fig1(
        df[mask], 
        'Production Process', 
        'Conductivity (MSm-1)', 
        True,
        squash=False,
        bm=compute_bm_g1(df, 'Conductivity (MSm-1)')
    )
    
    graph3 = html.Div(
    
        [
            
            # Graph 3
            html.Hr(),
            html.B("Conductivity vs Production Process"),
            
            dbc.Row([
                dbc.Col(
                    id='graph3',
                    children=dcc.Graph(figure=fig3)
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
    
    bm = compute_bm_g2(df, 'Tensile Strength (MPa)', 'Conductivity (MSm-1)')
    fig2 = construct_fig2(
        df, 
        x='Tensile Strength (MPa)', 
        y='Conductivity (MSm-1)',
        logx=True,
        logy=True,
        squash=False,
        bm=bm
    )

    graph2 = html.Div(
        [
            html.Hr(),
            html.B("Conductivity vs Tensile Strength"),
           
            html.Div(
                id='graph2', 
                children=dcc.Graph(figure=fig2)
            ),
            html.Div(
                id='graph2table', 
                children=dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in ['Category', 'correlation', 'p-value']]
                )
            )
        ],
        className='mt-3'
    )
    
    goto_explore = html.Div(
        children=[
            html.Hr(),
            'Want to explore the data yourself? Visit the interactive dashboard ',
            html.A('here', href='/explore'),
            '!'
        ],
        className='mt-3'
    )


    content = html.Div(
        id="page-content-home",
        children=[
            graph1,
            graph2,
            graph3,
            goto_explore
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
