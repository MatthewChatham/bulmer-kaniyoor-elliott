from dash import Dash, page_container, html
import dash_bootstrap_components as dbc

meta = {
    "name": "viewport", 
    "content": "width=device-width, initial-scale=1"}

app = Dash(
    __name__, 
    use_pages=True, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[meta],
    # suppress_callback_exceptions=True
)

app.layout = dbc.Container(
    [page_container], 
    id='page-container', 
    fluid=True
)

server = app.server

if __name__ == '__main__':
	app.run_server(
        debug=True,
        # dev_tools_ui=False,
        # dev_tools_props_check=False
    )