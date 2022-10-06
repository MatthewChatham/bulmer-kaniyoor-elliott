from dash import Dash, dcc, html, Input, Output, State
import os
import pandas as pd
import numpy as np
import plotly.express as px
import dash_bootstrap_components as dbc

LOGO_URL = 'https://secureservercdn.net/45.40.155.190/svz.20f.myftpupload.com/wp-content/uploads/2022/03/Logo1-2-768x768.png'
APP_NAME = 'CNT Meta-Analysis Explorer'

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_stylesheets = [dbc.themes.BOOTSTRAP]
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.title = APP_NAME
server = app.server

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 30,
    "left": 0,
    "bottom": 0,
    "width": "25rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "25rem",
    "margin-right": "3rem",
    "padding": "5rem 0rem",
}

def clean(df):
    df.replace('Not Reported/ Can not calculate', np.nan, inplace=True)
    df.replace('Not reported/Can not calculate', np.nan, inplace=True)
    df.replace('Not reported', np.nan, inplace=True)
    df.replace('Value in question', np.nan, inplace=True)
    df.replace('Value in question ', np.nan, inplace=True)
    df.replace('Suspect there is a mistake in units', np.nan, inplace=True)
    df.replace('<10', np.nan, inplace=True)
    df.replace('1.05263157894737 Cannot use, this is a "density corrected value"', np.nan, inplace=True)
    df.replace('Not clear what fibers they are referring to', np.nan, inplace=True)
    df.replace('30--80', np.nan, inplace=True)
    df.replace('2--6', np.nan, inplace=True)
    df.replace('8.8 +/- 2 ', np.nan, inplace=True)

    mask = df['Conductivity (MSm-1)'].str.contains('Cannot use, this is a "density corrected value"').fillna(False)
    df[mask] = np.nan

    df.replace('19.6 Value in question because of scale procedure', 19.6, inplace=True)
    df.replace('7.14285714285714   Value in question because of scale procedure', 7.14285714285714, inplace=True)
    df.replace('12.4 Value in question because of scale procedure', 12.4, inplace=True)
    df.replace('1000 (Number seems incorrect)', 1000, inplace=True)
    df.replace('10000 (Number seems incorrect)', 10000, inplace=True)
    df.replace('93 Very high conductivity for a very wide CNT, well beyond graphite, does not seem to be repeated in literature', 93, inplace=True)
    df['Tensile Strength (MPa)'] = df['Tensile Strength (MPa)'].str.replace('\s*These are before doping values\s*', '', regex=True)
    df['Young\'s Modulus (GPa)'] = df['Young\'s Modulus (GPa)'].str.replace('\s*These are before doping values\s*', '', regex=True)

    df.replace('Unsorted ', 'Unsorted', inplace=True)
    df.replace('Unosrted', 'Unsorted', inplace=True)

    return df


def set_types(df):
    # ---- NUMERIC
    num = list(dtypes[dtypes == 'numeric'].index)

    for c in num:
        df[c] = df[c].map(lambda x: x if '--' not in str(x) else np.nan).astype(float)

    # ---- DATE
    df['Date Entered and Checked'] = pd.to_datetime(df['Date Entered and Checked'], format='%Y%m%d')

    return df


dtypes = pd.read_csv('data_dict.csv', index_col='column').type
df = set_types(clean(pd.read_csv('data.csv')))

## filter controls
cat = dtypes[dtypes == 'categorical'].index
categorical_dropdowns = [dcc.Dropdown(df[c].dropna().unique(), multi=True, placeholder=c, id=f'{c}-control') for c in df.columns if c in cat]
num = dtypes[dtypes == 'numeric'].index
numeric_ranges = [
    html.Div(
        [
            html.Div(c),
            dcc.RangeSlider(df[c].astype(float).min(), df[c].astype(float).max(), id=f'{c}-control')
        ])

    for c in df.columns if c in num]
filter_fields = [html.Div(categorical_dropdowns, style={'width': '49%'}), html.Div(numeric_ranges, style={'width': '45%'})]

modal = html.Div(
    style={'margin-top': '1rem'},
    children =
    [
        dbc.Button("Adjust filters", id="open", n_clicks=0),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Filters")),
                dbc.ModalBody(id='filter-fields', children=filter_fields),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close", className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id="modal",
            is_open=False,
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
            dcc.Dropdown([c for c in df.columns if c not in ['Category', 'Doped or Acid Exposure (Yes/ No)']], [], multi=True, placeholder='Pick filter fields', id='filter-field-picker'),
            modal,

            html.Hr(),
            html.H6('Legend'),
            dcc.Checklist(df['Category'].unique(), df['Category'].unique(), labelStyle={'display': 'block'},
        style={"height":300, "width":350, "overflow":"auto"}, id='legend'),

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
        dcc.Dropdown(dtypes[dtypes == 'categorical'].index, 'Category', multi=False, placeholder='Pick X-axis', id='graph1-xaxis-dropdown'),
        dcc.Dropdown(dtypes[dtypes == 'numeric'].index, 'Conductivity (MSm-1)', multi=False, placeholder='Pick Y-axis', id='graph1-yaxis-dropdown'),
        dcc.Checklist(['Log Y'], [], id='graph1-log'),
        html.Div(id='graph1', children=dcc.Graph()),
    ]
)

graph2 = html.Div(
    style={'margin-top': '1rem'},
    children=[
        html.B("Scatterplot"),
        html.Hr(),
        dcc.Dropdown(dtypes[dtypes == 'numeric'].index, 'Tensile Strength (MPa)', multi=False, placeholder='Pick X-axis', id='graph2-xaxis-dropdown'),
        dcc.Dropdown(dtypes[dtypes == 'numeric'].index, 'Conductivity (MSm-1)', multi=False, placeholder='Pick Y-axis', id='graph2-yaxis-dropdown'),
        dcc.Checklist(['Log X', 'Log Y'], [], id='graph2-log'),
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
            "Bulmer, J. S., Kaniyoor, A., Elliott 2008432, J. A., A Meta-Analysis of Conductive and Strong Carbon Nanotube Materials. Adv. Mater. 2021, 33, 2008432. ",
            html.A("https://doi.org/10.1002/adma.202008432", href="https://doi.org/10.1002/adma.202008432")
        ], className="text-muted")
    ]),
    color="#ffffff", 
    fixed="bottom"
)


# sidebar = html.Div()

# content = html.Div()

app.layout = dbc.Container([navbar, sidebar, content, footer], className="bg-secondary")

# @app.callback([Output(f'{c}-control', '') for c in cat + num], 
#     [Input('filter-field-picker', 'value')],
#     State('filter-fields', 'children')
# )
# def update_filter_controls(value, state):
#     return 'test'

@app.callback(
Output("modal", "is_open"),
[Input("open", "n_clicks"), Input("close", "n_clicks")],
[State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
 Output('graph2', 'children'),
 Input('update', 'n_clicks'),
 [State('graph2-xaxis-dropdown', 'value'), 
 State('graph2-yaxis-dropdown', 'value'), State('graph2-log', 'value'), 
 State('legend', 'value'), 
 State('dope-control', 'value')]
)
def update_bottom_chart(n_clicks, xvar, yvar, log, legend, dope):
    mask = df['Category'].isin(legend) & df['Doped or Acid Exposure (Yes/ No)'].isin(dope)
    fig = px.scatter(df[mask], x=xvar, y=yvar, log_x='Log X' in log, log_y='Log Y' in log)
    return dcc.Graph(figure=fig)

@app.callback(
 Output('graph1', 'children'),
 Input('update', 'n_clicks'),
 [State('graph1-xaxis-dropdown', 'value'), 
 State('graph1-yaxis-dropdown', 'value'), 
 State('graph1-log', 'value'), 
 State('legend', 'value'), 
 State('dope-control', 'value')]
)
def update_top_chart(n_clicks, xvar, yvar, log, legend, dope):
    mask = df['Category'].isin(legend) & df['Doped or Acid Exposure (Yes/ No)'].isin(dope)
    fig = px.box(df[mask], x=xvar, y=yvar, log_y='Log Y' in log)
    return dcc.Graph(figure=fig)

# @app.callback(
#     Output('print', 'children'), 
#     Input('update', 'n_clicks'),
# )
# def test_filters(n_clicks):
#     return todo

if __name__ == '__main__':
    app.run_server(debug=True)
