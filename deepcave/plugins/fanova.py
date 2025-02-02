from typing import Dict, Type, Any

from dash import dcc, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

import pandas as pd
import numpy as np

from deepcave.plugins.static_plugin import StaticPlugin
from deepcave.utils.logs import get_logger
from deepcave.utils.data_structures import update_dict
from deepcave.utils.styled_plotty import get_color
from deepcave.utils.layout import get_slider_marks, get_select_options, get_checklist_options
from deepcave.utils.compression import serialize, deserialize

from deepcave.evaluators.fanova import fANOVA as _fANOVA


logger = get_logger(__name__)


class fANOVA(StaticPlugin):
    @staticmethod
    def id():
        return "fanova"

    @staticmethod
    def name():
        return "fANOVA"

    @staticmethod
    def position():
        return 100

    @staticmethod
    def category():
        return "Hyperparameter Analysis"

    @staticmethod
    def activate_run_selection():
        return True

    @staticmethod
    def get_input_layout(register):
        return [
            dbc.Label("Number of trees"),
            dbc.Input(id=register("num_trees", "value"))
        ]

    @staticmethod
    def get_filter_layout(register):
        return [
            html.Div([
                dbc.Label("Hyperparameters"),
                dbc.Checklist(
                    id=register("hyperparameters", ["options", "value"])),
            ], className="mb-3"),

            html.Div([
                dbc.Label("Budgets"),
                dbc.Checklist(
                    id=register("budgets", ["options", "value"])),
            ]),
        ]

    @staticmethod
    def load_inputs(runs):
        return {
            "num_trees": {
                "value": 16
            },
            "hyperparameters": {
                "options": get_checklist_options(),
                "value": []
            },
            "budgets": {
                "options": get_checklist_options(),
                "value": []
            },
        }

    @staticmethod
    def load_dependency_inputs(runs, previous_inputs, inputs):
        run = runs[inputs["run_name"]["value"]]
        budgets = run.get_budgets()
        hp_names = run.configspace.get_hyperparameter_names()

        new_inputs = {
            "hyperparameters": {
                "options": get_checklist_options(hp_names),
            },
            "budgets": {
                "options": get_checklist_options(budgets),
            },
        }
        update_dict(inputs, new_inputs)

        # Restrict to three hyperparameters
        num_trees = inputs["num_trees"]["value"]
        try:
            int(num_trees)
        except:
            inputs["num_trees"]["value"] = previous_inputs["num_trees"]["value"]

        return inputs

    @staticmethod
    def process(run, inputs):
        hp_names = run.configspace.get_hyperparameter_names()
        budgets = run.get_budgets()

        # Collect data
        data = {}
        for budget in budgets:
            X, Y = run.get_encoded_configs(budget=budget, for_tree=True)

            evaluator = _fANOVA(
                X, Y,
                configspace=run.configspace,
                num_trees=int(inputs["num_trees"]["value"])
            )
            importance_dict = evaluator.quantify_importance(
                hp_names,
                depth=1,
                sorted=False)

            importance_dict = {k[0]: v for k, v in importance_dict.items()}

            data[budget] = importance_dict

        return data

    @staticmethod
    def get_output_layout(register):
        return [
            dcc.Graph(register("graph", "figure"))
        ]

    @staticmethod
    def load_outputs(inputs, outputs, _):
        run_name = inputs["run_name"]["value"]
        outputs = outputs[run_name]
        # First selected, should always be shown first
        selected_hyperparameters = inputs["hyperparameters"]["value"]
        selected_budgets = inputs["budgets"]["value"]

        if len(selected_hyperparameters) == 0 or len(selected_budgets) == 0:
            return PreventUpdate

        # TODO: After json serialize/deserialize, budget is not an integer anymore
        convert_type = type(selected_budgets[0])

        # Collect data
        data = {}
        for budget, importance_dict in outputs.items():
            budget = convert_type(budget)

            if budget not in inputs["budgets"]["value"]:
                continue

            x = []
            y = []
            error_y = []
            for hp_name, results in importance_dict.items():
                if hp_name not in inputs["hyperparameters"]["value"]:
                    continue

                x += [hp_name]
                y += [results[1]]
                error_y += [results[3]]

            data[budget] = (
                np.array(x),
                np.array(y),
                np.array(error_y)
            )

            # if filters["sort"]["value"] == fidelity_id:
            #    selected_fidelity = fidelity

        # Sort by last fidelity now
        last_selected_budget = selected_budgets[-1]
        idx = np.argsort(
            data[last_selected_budget][1], axis=None)[::-1]

        bar_data = []
        for budget, values in data.items():
            bar_data += [go.Bar(
                name=budget,
                x=values[0][idx],
                y=values[1][idx],
                error_y_array=values[2][idx])
            ]

        fig = go.Figure(data=bar_data)
        fig.update_layout(barmode='group')

        return [fig]
