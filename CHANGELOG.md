# 0.1

## Features

- Multi-Objective is supported with flexible objective objects.
- Groups: If plugin supports groups, multiple runs can be used.
- Automatically find converter: DeepCAVE scans the given directory and selects a suitable converter (if available).
- Recorder: Record your runs and save them directly as DeepCAVE files.
- Matplotlib mode: Alternatively, plugins can output Matplotlib rendered plots.


## Plugins

- StaticPlugin: Uses queue to process the result.
- DynamicPlugin: Input changes are directly calculated.

- Overview: Shows meta and statistics.
- Configurations: Shows configuration space and best found configuration.
- Cost over Time: Shows how the cost changes over time.
- Configuration Cube: Shows configurations as points in a cube.
- Individual Conditional Expectation / Partial Dependency Plots: Shows how individual instances behave.
- fANOVA: Shows Hyperparameter Importance.


## Converters

- DeepCAVE
- SMAC
- BOHB (Beta)