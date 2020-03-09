import datetime
from os.path import dirname, join

import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, DataRange1d, Select
from bokeh.palettes import Reds4
from bokeh.plotting import figure

STATISTICS = [
    "record_min_temp",
    "actual_min_temp",
    "average_min_temp",
    "average_max_temp",
    "actual_max_temp",
    "record_max_temp",
]


def get_dataset(src, name, distribution):
    df = src[src.airport == name].copy()
    del df["airport"]
    df["date"] = pd.to_datetime(df.date)
    # timedelta here instead of pd.DateOffset to avoid pandas bug < 0.18 (Pandas issue #11925)
    df["left"] = df.date - datetime.timedelta(days=0.5)
    df["right"] = df.date + datetime.timedelta(days=0.5)
    df = df.set_index(["date"])
    df.sort_index(inplace=True)
    if distribution == "Smoothed":
        raise NotImplementedError("I just removed this to save us from scipy")

    return ColumnDataSource(data=df)


def make_plot(source, title):
    plot = figure(
        x_axis_type="datetime",
        plot_width=800,
        tools="hover,crosshair,pan,wheel_zoom,zoom_in,zoom_out,box_zoom,undo,redo,reset,tap,save",
        toolbar_location=None,
    )
    plot.title.text = title

    plot.quad(
        top="record_max_temp",
        bottom="record_min_temp",
        left="left",
        right="right",
        color=Reds4[2],
        source=source,
        legend_label="Record",
    )
    plot.quad(
        top="average_max_temp",
        bottom="average_min_temp",
        left="left",
        right="right",
        color=Reds4[1],
        source=source,
        legend_label="Average",
    )
    plot.quad(
        top="actual_max_temp",
        bottom="actual_min_temp",
        left="left",
        right="right",
        color=Reds4[0],
        alpha=0.5,
        line_color="black",
        source=source,
        legend_label="Actual",
    )

    # fixed attributes
    plot.xaxis.axis_label = None
    plot.yaxis.axis_label = "Temperature (F)"
    plot.axis.axis_label_text_font_style = "bold"
    plot.x_range = DataRange1d(range_padding=0.0)
    plot.grid.grid_line_alpha = 0.3

    return plot


def update_plot(attrname, old, new):
    city = city_select.value
    plot.title.text = "Weather data for " + cities[city]["title"]

    src = get_dataset(df, cities[city]["airport"], distribution_select.value)
    source.data.update(src.data)


city = "Austin"
distribution = "Discrete"

cities = {
    "Austin": {"airport": "AUS", "title": "Austin, TX",},
    "Boston": {"airport": "BOS", "title": "Boston, MA",},
    "Seattle": {"airport": "SEA", "title": "Seattle, WA",},
}

city_select = Select(value=city, title="Area", options=sorted(cities.keys()))
distribution_select = Select(
    value=distribution, title="Distribution", options=["Discrete", "Smoothed"]
)
# TODO: this one doesn't do anything yet
countermeasures = Select(
    options=["25%", "50%", "75%"],
    value="50%",
    title="reduction transmission due countermeasures",
)

df = pd.read_csv(join(dirname(__file__), "data/2015_weather.csv"))
source = get_dataset(df, cities[city]["airport"], distribution)
plot = make_plot(source, "Weather data for " + cities[city]["title"])

city_select.on_change("value", update_plot)
distribution_select.on_change("value", update_plot)

controls = column(city_select, distribution_select, countermeasures)

curdoc().add_root(row(plot, controls))
curdoc().title = "covid-2"
