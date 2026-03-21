import dash
from dash import dcc, html

from django_plotly_dash import DjangoDash
from .models import Forecast, ForecastZone
import pandas as pd

import plotly.express as px
from plotly.offline import plot
from plotly.graph_objs import Figure
from django_pandas.io import read_frame
import dash_bootstrap_components as dbc

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = DjangoDash("NWACExplorer", external_stylesheets=[dbc.themes.SLATE])
# , external_stylesheets=external_stylesheets)   # replaces dash.Dash

app.layout = html.Div(
    [
        html.Div(
            [
                html.H3("Select Forecast Zone:"),
                dcc.Dropdown(
                    id="dropdown-zone-selector",
                    options=[
                        {"label": c.name, "value": c.name}
                        for c in ForecastZone.objects.all()
                    ],
                    value="Olympics",
                ),
            ],
            style={"width": "48%", "display": "inline-block"},
        ),
        html.Div(
            [
                html.H3("Select Time Basis:"),
                dcc.Dropdown(
                    id="dropdown-time-basis-selector",
                    options=[
                        {"label": c, "value": c.lower()}
                        for c in ["Absolute", "Time of Year"]
                    ],
                    value="absolute",
                ),
            ],
            style={"width": "48%", "display": "inline-block"},
        ),
        dcc.Graph(
            id="data-explorer",
            figure={},
            style={"width": "48%", "display": "inline-block"},
            
        ),
    ],
    style={"width": "100%", "margin": "auto", "height": "100%"},
)


@app.callback(
    dash.dependencies.Output("data-explorer", "figure"),
    [
        dash.dependencies.Input("dropdown-zone-selector", "value"),
        dash.dependencies.Input("dropdown-time-basis-selector", "value"),
    ],
)
def callback_zone(zone_name, time_basis):
    if not zone_name:
        return Figure()
    zone = ForecastZone.objects.get(name=zone_name)
    forecasts = Forecast.objects.filter(zone=zone).order_by("-date")

    df = read_frame(
        forecasts,
        fieldnames=[
            "date",
            "upper_elevation_danger",
            "mid_elevation_danger",
            "lower_elevation_danger",
        ],
    )
    df["date"] = pd.to_datetime(df["date"])
    df["average_danger"] = df[
        ["upper_elevation_danger", "mid_elevation_danger", "lower_elevation_danger"]
    ].mean(axis=1)
    df = df[df["average_danger"] > 0]

    x_axis_title = "Date"
    if time_basis == "time of year":
        df["date"] = df["date"].dt.dayofyear
        x_axis_title = "Day of Year"
    fig = px.scatter(
        df,
        x="date",
        y=[
            "upper_elevation_danger",
            "mid_elevation_danger",
            "lower_elevation_danger",
            "average_danger",
        ],
        title="Danger Levels Over Time For {} Zone".format(zone_name),
        labels={
            "value": "Danger Level",
            "date": x_axis_title,
        },
        trendline="rolling",
        trendline_options=dict(window=5),
        template="plotly_dark"
    )
    return fig
