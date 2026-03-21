import dash
from dash import dcc, html, dash_table

from django_plotly_dash import DjangoDash
from .models import SkiResort
from snowpack.models import Station, SnowfallRecord
import pandas as pd

import plotly.express as px
from plotly.offline import plot
from plotly.graph_objs import Figure
from django_pandas.io import read_frame
from .utilities import get_closest_object
import dash_bootstrap_components as dbc

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = DjangoDash("SkiResortExplorer", external_stylesheets=[dbc.themes.SLATE])
# , external_stylesheets=external_stylesheets)   # replaces dash.Dash

app.layout = html.Div(
    [
        html.Div(
            [
                html.H3("Select Ski Resort:"),
                dcc.Dropdown(
                    id="dropdown-ski-resort-selector",
                    options=[
                        {"label": c.name, "value": c.name}
                        for c in SkiResort.objects.all()
                    ],
                    value="Stevens Pass",
                ),
            ],
            style={"width": "30%", "display": "inline-block"},
        ),
        html.Div(
            [
                html.H3("Select Measurement:"),
                dcc.Dropdown(
                    id="dropdown-measurement-selector",
                    options=[
                        {"label": c, "value": c.lower()}
                        for c in [
                            "Snowfall Amount",
                            "Snow Depth",
                            "Temperature",
                            "Precipitation",
                        ]
                    ],
                    value="snowfall amount",
                ),
            ],
            style={"width": "30%", "display": "inline-block"},
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
            style={"width": "30%", "display": "inline-block"},
        ),
        html.Div(
            [
                html.H3("Min Year"),
                dcc.Slider(
                    id="slider-min-year",
                    min=1980,
                    max=2024,
                    step=1,
                    value=2000,
                    marks={year: str(year) for year in range(1980, 2025, 5)},
                ),
            ],
            style={"textAlign": "center"},
        ),
        dcc.Graph(
            id="data-explorer",
            figure={},
            style={"width": "48%", "display": "inline-block"},
        ),
        dcc.Graph(
            id="location_map",
            figure={},
            style={"width": "48%", "display": "inline-block"},
        ),
        html.Br(),
        html.Div(
            [
                html.H3("Aggregated Data Per Resort"),
                dash_table.DataTable(
                    id="aggregated-table",
                    columns=[
                        {"name": "Ski Resort", "id": "Ski Resort"},
                        {"name": "Average", "id": "Average"},
                        {"name": "Max", "id": "Max"},
                        {"name": "Min", "id": "Min"},
                        {"name": 'N Days above 20"', "id": "N Days"},
                    ],
                    data=[],
                    page_size=10,
                ),
            ]
        ),
    ],
    style={"width": "100%", "margin": "auto", "height": "100%"},
)


@app.callback(
    dash.dependencies.Output("data-explorer", "figure"),
    [
        dash.dependencies.Input("dropdown-ski-resort-selector", "value"),
        dash.dependencies.Input("dropdown-time-basis-selector", "value"),
        dash.dependencies.Input("dropdown-measurement-selector", "value"),
        dash.dependencies.Input("slider-min-year", "value"),
    ],
)
def callback_zone(zone_name, time_basis, measurement, min_year):
    ski_resort = SkiResort.objects.get(name=zone_name)
    station = get_closest_object(ski_resort.latitude, ski_resort.longitude)
    records = SnowfallRecord.objects.filter(station=station).order_by("-date")
    field_names = ["date", measurement.replace(" ", "_")]

    df = read_frame(
        records,
        fieldnames=field_names,
    )
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year >= min_year]
    df["year"] = df["date"].dt.year
    x_axis_title = "Date"
    if time_basis == "time of year":
        df["date"] = df["date"].dt.dayofyear
        x_axis_title = "Day of Year"
    fig = px.scatter(
        df,
        x="date",
        y=field_names[1],
        title="{} Over Time For {} Zone".format(field_names[1], zone_name),
        labels={
            "value": "Measurement",
            "date": x_axis_title,
        },
        # trendline="rolling", trendline_options=dict(window=5),
        color="year",
    )
    if time_basis == "time of year":
        today = pd.Timestamp.today().dayofyear
        fig.add_vline(
            x=today,
            line_width=2,
            line_dash="dash",
            line_color="green",
            annotation_text="Today",
            annotation_position="top right",
        )
    return fig


@app.callback(
    dash.dependencies.Output("location_map", "figure"),
    [
        dash.dependencies.Input("dropdown-ski-resort-selector", "value"),
    ],
)
def callback_map(zone_name):
    all_stations = Station.objects.all()

    df = read_frame(
        all_stations,
        fieldnames=["name", "nwcc_id", "latitude", "longitude", "elevation"],
    )
    df["Station Locations"] = "Weather Stations"
    # Now get the ski resort location
    all_resorts = SkiResort.objects.all()
    resorts_df = read_frame(
        all_resorts,
        fieldnames=["name", "latitude", "longitude", "base_elevation"],
    )
    resorts_df["Station Locations"] = "Ski Resorts"
    resorts_df["elevation"] = resorts_df["base_elevation"]
    df = pd.concat([df, resorts_df], ignore_index=True)

    fig = px.scatter_geo(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="name",
        hover_data={"elevation": True},
        title="Station Locations",
        color="Station Locations",
    )
    fig.update_geos(fitbounds="locations")
    fig.update_geos(
        visible=False,
        resolution=50,
        scope="north america",
        showcountries=True,
        countrycolor="Black",
        showsubunits=True,
        subunitcolor="grey",
    )

    return fig


@app.callback(
    dash.dependencies.Output("aggregated-table", "data"),
    [
        dash.dependencies.Input("dropdown-measurement-selector", "value"),
        dash.dependencies.Input("slider-min-year", "value"),
    ],
)
def callback_table(measurement, min_year):
    all_resorts = SkiResort.objects.all()
    resorts_df = read_frame(
        all_resorts,
        fieldnames=["name", "latitude", "longitude", "base_elevation"],
    )
    df = []
    for resort in all_resorts:
        station = get_closest_object(resort.latitude, resort.longitude)
        records = SnowfallRecord.objects.filter(station=station).order_by("-date")
        field_name = measurement.replace(" ", "_")
        resort_df = read_frame(
            records,
            fieldnames=["date", field_name],
        )
        resort_df["date"] = pd.to_datetime(resort_df["date"])
        resort_df = resort_df[resort_df["date"].dt.year >= min_year]
        avg_value = resort_df[field_name].mean()
        max_value = resort_df[field_name].max()
        min_value = resort_df[field_name].min()
        n_days = resort_df[resort_df[field_name] > 20].shape[0]
        df.append(
            {
                "Ski Resort": resort.name,
                "Average": avg_value,
                "Max": max_value,
                "Min": min_value,
                "N Days": n_days,
            }
        )
    # df = pd.DataFrame(df)

    return df  # df.to_dict('records')
