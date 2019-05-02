#!/usr/bin/env python3
"""Script that creates a dashboard website using the dash library.
The data comes from the specified dashboard db and
the information is updated every x-seconds (currently hardcoded to 10)
"""
import argparse
from typing import List, Dict
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

import numpy as np
import dash
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objs as go
from dashboard.DashboardDB import DashboardDB, SQueueEntry, HPCProperty
from dashboard.run_data_collection import USERS
from dash.dependencies import Input, Output
import dash_table

import qcore.constants as const

# LAST_YEAR = datetime.strftime(datetime.now()-timedelta(days=365), "%y")
# CURRENT_YEAR = datetime.strftime(datetime.now(), "%y")
# ALLOCATION_TEMPLATE = ["01/06/{}-12:00:00", "01/12/{}-12:00:00"]
# ALLOCATIONS = [a.format(y) for y in [LAST_YEAR, CURRENT_YEAR] for a in ALLOCATION_TEMPLATE]

EXTERNAL_STYLESHEETS = [
    "https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css"
]

parser = argparse.ArgumentParser()
parser.add_argument("db_file", type=str, help="Path to the database file")
args = parser.parse_args()

# Creating the Dashboard app
app = dash.Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS)
app.db = DashboardDB(args.db_file)

ALLOCATIONS_MAHUIKA = ['{}---{}'.format(i[0], i[1]) for i in app.db.get_allocation_periods(const.HPC.mahuika)]
ALLOCATIONS_MAUI = ['{}---{}'.format(i[0], i[1]) for i in app.db.get_allocation_periods(const.HPC.maui)]

app.layout = html.Div(
    html.Div(
        [
            html.H3("Mahuika & Maui"),
            html.Div(id="err"),
            html.H5("Mahuika Allocation"),
            dcc.Dropdown(
                            id='mahuika-dropdown',
                            options=[
                                {'label': i, 'value': i} for i in ALLOCATIONS_MAHUIKA
                            ],
                            value=ALLOCATIONS_MAHUIKA[0]
                    ),
            html.H5("Mahuika & Maui total core hours usage"),
            html.Div(id="maui_mahuika_chours"),
            html.H5("Mahuika total core hour usage"),
            dcc.Graph(id="mahuika_total_chours"),
            html.H5("Mahuika daily core hour usage"),
            dcc.Graph(id="mahuika_daily_chours"),
            html.H5("Maui Allocation"),
            dcc.Dropdown(
                            id='maui-dropdown',
                            options=[
                                {'label': i, 'value': i} for i in ALLOCATIONS_MAUI
                            ],
                            value=ALLOCATIONS_MAUI[0]
                    ),
            html.H5("Maui total core hour usage"),
            dcc.Graph(id="maui_total_chours"),
            html.H5("Maui daily core hour usage"),
            dcc.Graph(id="maui_daily_chours"),
            html.H5("Maui current status"),
            html.Div(id="maui_node_usage"),
            html.H5("Maui current quota"),
            html.Div(id="maui_quota_usage"),
            html.H5("Maui current queue"),
            html.Div(id="maui_squeue_table"),
            html.H5("Maui_daily_inodes"),
            dcc.Graph(id="maui_daily_inodes"),
            dcc.Interval(id="interval_comp", interval=10 * 1000, n_intervals=0),
        ]
    )
)


@app.callback(
    Output("maui_mahuika_chours", "children"), [Input("interval_comp", "n_intervals")]
)
def update_maui_total_chours(n):
    maui_total_chours = get_chours_entries(const.HPC.maui)[-1][-1]
    mahuika_total_chours = get_chours_entries(const.HPC.mahuika)[-1][-1]
    return html.Plaintext(
        "Mahuika: {} / 18,000 hours\nMaui: {} / 950,000 hours".format(
            mahuika_total_chours, maui_total_chours
        )
    )


@app.callback(
    Output("maui_node_usage", "children"), [Input("interval_comp", "n_intervals")]
)
def update_maui_nodes(n):
    entry = app.db.get_status_entry(const.HPC.maui, HPCProperty.node_capacity.value)
    return html.Plaintext(
        "Current number of nodes available {}/{}".format(
            entry.int_value_2 - entry.int_value_1, entry.int_value_2
        )
    )


@app.callback(
    Output("maui_quota_usage", "children"), [Input("interval_comp", "n_intervals")]
)
def update_maui_quota(n):
    nobackup_string = get_maui_daily_quota_string("nobackup")
    project_string = get_maui_daily_quota_string("project")
    return html.Plaintext("{}\n{}".format(nobackup_string, project_string))


@app.callback(
    Output("maui_squeue_table", "children"), [Input("interval_comp", "n_intervals")]
)
def update_maui_squeue(n):
    entries = app.db.get_squeue_entries(const.HPC.maui)
    return generate_table_interactive(entries)


@app.callback(
    Output("maui_daily_chours", "figure"), [Input("maui-dropdown", "value")]
)
def update_maui_daily_chours(value):
    start_date, end_date = value.split('---')
    return update_daily_chours(const.HPC.maui, start_date, end_date)


@app.callback(
    Output("mahuika_daily_chours", "figure"), [Input("mahuika-dropdown", "value")]
)
def update_mahuika_daily_chours(value):
    start_date, end_date = value.split('---')
    return update_daily_chours(const.HPC.mahuika, start_date, end_date)


@app.callback(
    Output("maui_total_chours", "figure"), [Input("maui-dropdown", "value")]
)
def update_maui_total_chours(value):
    start_date, end_date = value.split('---')
    entries = get_chours_entries(const.HPC.maui, start_date, end_date)
    fig = go.Figure()
    fig.add_scatter(x=entries["day"], y=entries["total_chours"])

    return fig


@app.callback(
    Output("mahuika_total_chours", "figure"), [Input("mahuika-dropdown", "value")]
)
def update_mahuika_total_chours(value):
    print("value from dripdown", value)
    start_date, end_date = value.split('---')
    print(value, "start end for mahuika total_chours", start_date, end_date)
    entries = get_chours_entries(const.HPC.mahuika, start_date, end_date)
    fig = go.Figure()
    fig.add_scatter(x=entries["day"], y=entries["total_chours"])

    return fig


@app.callback(Output("err", "children"), [Input("interval_comp", "n_intervals")])
def display_err(n):
    """Displays data collection error when the gap between update_times exceeds acceptable limit"""
    if not check_update_time(app.db.get_update_time(const.HPC.maui)[0], datetime.now()):
        return html.Plaintext(
            "Data collection error, check the error_table in database",
            style={"background-color": "red", "font-size": 20},
        )


@app.callback(
    Output("maui_daily_inodes", "figure"), [Input("interval_comp", "n_intervals")]
)
def update_maui_daily_inodes(n):
    entries = app.db.get_daily_inodes(const.HPC.maui)

    entries = np.array(
        entries,
        dtype=[
            ("file_system", object),
            ("used_inodes", float),
            ("day", "datetime64[D]"),
        ],
    )
    data = []
    trace = go.Scatter(
        x=entries["day"], y=entries["used_inodes"], name="maui_nobackup_daily_inodes"
    )
    data.append(trace)
    # max available inodes on maui nobackup
    trace2 = go.Scatter(
        x=entries["day"],
        y=np.tile(15000000, entries["used_inodes"].size),
        name="maui_nobackup_available inodes",
        fillcolor="red",
    )
    data.append(trace2)
    layout = go.Layout(yaxis=dict(range=[0, 16000000]))
    fig = go.Figure(data=data, layout=layout)
    return fig


def update_daily_chours(hpc, start_date=date.today() - relativedelta(days=188), end_date=date.today()):
    # Get data points
    data = []
    entries = app.db.get_chours_usage(
        start_date, end_date, hpc
    )
    entries = np.array(
        entries,
        dtype=[
            ("day", "datetime64[D]"),
            ("daily_chours", float),
            ("total_chours", float),
        ],
    )
    trace = go.Scatter(x=entries["day"], y=entries["daily_chours"], name="daily_chours")
    data.append(trace)

    # get core hours usage for each user
    data += get_daily_user_chours(hpc, USERS, start_date, end_date)

    # uirevision preserve the UI state between update intervals
    return {"data": data, "layout": {"uirevision": "{}_daily_chours".format(hpc)}}


def get_daily_user_chours(hpc: const.HPC, users_dict: Dict[str, str] = USERS, start_date=date.today() - relativedelta(days=188), end_date=date.today()):
    """get daily core hours usage for a list of users
       return as a list of scatter plots
    """
    data = []
    for username, real_name in users_dict.items():
        entries = app.db.get_user_chours(hpc, username, start_date, end_date)
        entries = np.array(
            entries,
            dtype=[
                ("day", "datetime64[D]"),
                ("username", object),
                ("core_hours_used", float),
            ],
        )
        trace = go.Scatter(
            x=entries["day"], y=entries["core_hours_used"], name=real_name
        )
        data.append(trace)
    return data


def get_chours_entries(hpc: const.HPC, start_date=date.today() - relativedelta(days=188), end_date=date.today()):
    """Gets the core hours entries for the specified HPC
    Note: Only maui is currently supported
    """
    # Get data points
    entries = app.db.get_chours_usage(
        start_date, end_date, hpc
    )
    return np.array(
        entries,
        dtype=[
            ("day", "datetime64[D]"),
            ("daily_chours", float),
            ("total_chours", float),
        ],
    )


def generate_table(squeue_entries: List[SQueueEntry]):
    """Generates html table for the given squeue entries."""
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in SQueueEntry._fields])]
        +
        # Body
        [html.Tr([html.Td(col_val) for col_val in entry]) for entry in squeue_entries]
    )


def generate_table_interactive(squeue_entries: List[SQueueEntry]):
    """Generates interactive dash table for the given squeue entries."""
    # Convert NamedTuple to OrderedDict
    squeue_entries = [entry._asdict() for entry in squeue_entries]
    return html.Div(
        [
            dash_table.DataTable(
                id="datatable-interactivity",
                columns=[
                    {"name": i, "id": i, "deletable": False}
                    for i in SQueueEntry._fields
                ],
                data=squeue_entries,
                filtering=True,
                filtering_settings="account eq 'nesi00213'",
                sorting=True,
                sorting_type="multi",
            ),
            html.Div(id="datatable-interactivity-container"),
        ]
    )


def get_maui_daily_quota_string(file_system):
    """Get daily quota string for a particular file system eg.nobackup"""
    entry = app.db.get_daily_quota(
        const.HPC.maui, date.today(), file_system=file_system
    )
    return "Current space usage in {} is {}\nCurrent Inodes usage in {} is {}/{} ({:.3f}%)".format(
        file_system,
        entry.used_space,
        file_system,
        entry.used_inodes,
        entry.available_inodes,
        entry.used_inodes / entry.available_inodes * 100.0,
    )


def check_update_time(last_update_time_string: str, current_update_time: datetime):
    """Checks whether the time gap between update times exceeds the idling time limit(300s)
    if exceeds, regards as a collection error.
    """
    # 2019-03-28 18:31:11.906576
    return (
        current_update_time
        - datetime.strptime(last_update_time_string, "%Y-%m-%d %H:%M:%S.%f")
    ) < timedelta(seconds=300)


if __name__ == "__main__":
    app.run_server(host="0.0.0.0")
