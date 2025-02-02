from typing import Dict, Type, Any

from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

import pandas as pd
import numpy as np

from deepcave import app
from deepcave.plugins.static_plugin import StaticPlugin
from deepcave.plugins.dynamic_plugin import DynamicPlugin
from deepcave.utils.logs import get_logger
from deepcave.runs.run import Status

from deepcave.evaluators.fanova import fANOVA as _fANOVA


logger = get_logger(__name__)


class Overview(DynamicPlugin):
    def __init__(self):
        super().__init__()

    @staticmethod
    def id():
        return "overview"

    @staticmethod
    def name():
        return "Overview"

    @staticmethod
    def position():
        return 1

    @staticmethod
    def category():
        return "General"

    @staticmethod
    def activate_run_selection() -> bool:
        return True

    @staticmethod
    def process(run, inputs):
        # Meta
        meta = {
            "Attribute": [],
            "Value": []
        }
        for k, v in run.get_meta().items():
            if k == "objectives":
                continue

            if isinstance(v, list):
                v = ", ".join(str(_v) for _v in v)

            meta["Attribute"].append(k)
            meta["Value"].append(str(v))

        # Objectives
        objectives = {
            "Name": [],
            "Lower Bound": [],
            "Upper Bound": []
        }
        for objective in run.get_objectives():
            objectives["Name"].append(objective["name"])
            objectives["Lower Bound"].append(objective["lower"])
            objectives["Upper Bound"].append(objective["upper"])

        budgets = run.get_budgets()
        stats = {}
        # Statistics
        for budget in budgets:

            if budget not in stats:
                stats[budget] = {}

                for s in Status:
                    stats[budget][s.name] = 0

        for trial in run.history:
            stats[trial.budget][trial.status.name] += 1

        statistics = {
            "Budget": budgets,
            "Total": []
        }
        for s in Status:
            statistics[s.name] = []

            for budget in budgets:
                count = stats[budget][s.name]

                # Calculate max entries
                count_all = 0
                for _count in stats[budget].values():
                    count_all += _count

                if len(statistics["Total"]) < len(budgets):
                    statistics["Total"].append(count_all)

                percentage = int(count / count_all * 100)

                string = f"{count} ({percentage}%)"
                statistics[s.name].append(string)

        return {
            "meta": meta,
            "objectives": objectives,
            "statistics": statistics,
        }

    @staticmethod
    def get_output_layout(register):
        return [
            html.H3("Meta"),
            html.Div(id=register("meta", "children")),
            html.Hr(),

            html.H3("Objectives"),
            html.Div(id=register("objectives", "children")),
            html.Hr(),

            html.H3("Statistics"),
            html.Div(id=register("statistics", "children")),
            html.Hr(),
        ]

    @staticmethod
    def load_outputs(inputs, outputs, _):
        run_name = inputs["run_name"]["value"]
        outputs = outputs[run_name]

        def create_table(output): return dbc.Table.from_dataframe(
            pd.DataFrame(output), striped=True, bordered=True
        )

        return [
            create_table(outputs["meta"]),
            create_table(outputs["objectives"]),
            create_table(outputs["statistics"]),
        ]
