import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
from plotly.graph_objs import Figure

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.H1("Snowpack Explorer - Placeholder"),
        html.P("This visualization module needs data to be connected."),
    ],
    style={"width": "100%", "margin": "auto", "height": "100%"},
)
