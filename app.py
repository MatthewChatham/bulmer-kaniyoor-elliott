from dash import Dash, page_container
import dash_bootstrap_components as dbc

app = Dash(
    __name__, 
    use_pages=True, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.layout = dbc.Container(
    className='bg-light',
    style={'height': '100%'},
    children=[page_container]
)

server = app.server

if __name__ == '__main__':
	app.run_server(debug=True)