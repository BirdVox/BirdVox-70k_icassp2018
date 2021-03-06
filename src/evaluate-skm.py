import datetime
import mir_eval
import numpy as np
import os
import pandas as pd
import sys
import time

import localmodule

# Define constants.
models_dir = localmodule.get_models_dir()
data_dir = localmodule.get_data_dir()
dataset_name = localmodule.get_dataset_name()
annotations_name = "_".join([dataset_name, "annotations"])
annotations_dir = os.path.join(data_dir, annotations_name)
# TODO: replace with cross-validated SKM predictions (Justin Salamon)
predictions_name = "_".join([dataset_name, "baseline-predictions"])
predictions_dir = os.path.join(data_dir, predictions_name)
units = localmodule.get_units()
n_thresholds = 100
negative_labels = localmodule.get_negative_labels()
args = sys.argv[1:]
tolerance_ms = int(args[0])
tolerance = tolerance_ms / 1000
unit_str = args[1]


# Print header.
start_time = int(time.time())
print(str(datetime.datetime.now()) + " Start.")
print("Evaluating SKM detector on " + dataset_name + ", " + unit_str)
print("with a temporal tolerance of " + str(tolerance_ms) + " ms.")
print("mir_eval version: {:s}".format(mir_eval.__version__))
print("numpy version: {:s}".format(np.__version__))
print("pandas version: {:s}".format(pd.__version__))
print("")


# Find minimum and maximum values taken by the ODF peaks across all units.
unit_minima = []
unit_maxima = []
unit_peak_times = []
unit_peak_values = []
for dummy_unit_str in units:
    prediction_name = dummy_unit_str + ".npy"
    prediction_path = os.path.join(predictions_dir, prediction_name)
    prediction_matrix = np.load(prediction_path)
    timestamps = prediction_matrix[:, 0]
    odf = prediction_matrix[:, 1]
    peak_locations = localmodule.pick_peaks(odf)
    peak_times = timestamps[peak_locations]
    unit_peak_times.append(peak_times)
    peak_values = odf[peak_locations]
    unit_peak_values.append(peak_values)
    unit_min = np.min(peak_values)
    unit_minima.append(unit_min)
    unit_max = np.max(peak_values)
    unit_maxima.append(unit_max)


# Define vector of thresholds.
global_minimum = min(unit_minima)
global_maximum = max(unit_maxima)
global_delta = global_maximum - global_minimum
threshold_multipliers = 1-np.logspace(np.log10(0.5), np.log10(0.1), n_thresholds)
thresholds = global_minimum + threshold_multipliers * global_delta


# Load annotation as DataFrame. Restrict rows to positive labels.
annotation_name = unit_str + ".txt"
annotation_path = os.path.join(annotations_dir, annotation_name)
annotation = pd.read_csv(annotation_path, "\t")
if "Calls" in annotation.columns:
    relevant_rows = annotation.loc[~annotation["Calls"].isin(negative_labels)]
else:
    relevant_rows = annotation
begin_times = np.array(relevant_rows["Begin Time (s)"])
end_times = np.array(relevant_rows["End Time (s)"])
relevant = 0.5 * (begin_times+end_times)
n_relevant = len(relevant)


# Load onset detection function (ODF).
prediction_name = unit_str + ".npy"
prediction_path = os.path.join(predictions_dir, prediction_name)
prediction_matrix = np.load(prediction_path)
timestamps = prediction_matrix[:, 0]
odf = prediction_matrix[:, 1]


# Pick peaks.
peak_locations = localmodule.pick_peaks(odf)
peak_times = timestamps[peak_locations]
peak_values = odf[peak_locations]


# Initialize list of rows (stored as dicts of strings).
rows = []


# Loop over thresholds.
for threshold in thresholds:
    # Select values above threshold.
    selected = peak_times[np.where(peak_values>threshold)]

    # Match selected events with relevant events using the mir_eval toolbox.
    selected_relevant = mir_eval.util.match_events(relevant, selected, tolerance)

    # Define metrics.
    true_positives = len(selected_relevant)
    n_selected = len(selected)
    false_positives = n_selected - true_positives
    false_negatives = n_relevant - true_positives
    if n_selected == 0 or true_positives == 0:
        precision = 0.0
        recall = 0.0
        f1_score = 0.0
    else:
        precision = 100 * true_positives / n_selected
        recall = 100 * true_positives / n_relevant
        f1_score = 2*precision*recall / (precision+recall)

    # Fill in row.
    row = {
         "unit":unit_str,
         "tolerance (ms)": str(tolerance_ms),
         "threshold": format(threshold, ".15f"),
         "relevant": str(n_relevant).rjust(5),
         "selected": str(n_selected).rjust(6),
         "true positives": str(true_positives).rjust(5),
         "false positives": str(false_positives).rjust(5),
         "false negatives": str(false_negatives).rjust(5),
         "precision (%)": format(precision, ".6f").rjust(10),
         "recall (%)": format(recall, ".6f").rjust(10),
         "F1 score (%)": format(f1_score, ".6f").rjust(10)}
    rows.append(row)


# Export DataFrame.
df = pd.DataFrame(rows,
    columns=["unit", "tolerance (ms)", "threshold", "relevant", "selected",
             "true positives", "false positives", "false negatives",
             "precision (%)", "recall (%)", "F1 score (%)"],
    index=[str(i).rjust(3) for i in range(n_thresholds)])
model_name = "SKM"
model_dir = os.path.join(models_dir, model_name)
os.makedirs(model_dir, exist_ok=True)
unit_dir = os.path.join(model_dir, unit_str)
os.makedirs(unit_dir, exist_ok=True)
tolerance_str = "tol-" + str(tolerance_ms)
metrics_name = "_".join([model_name, tolerance_str, unit_str, "metrics"])
metrics_path = os.path.join(unit_dir, metrics_name + ".csv")
df.to_csv(metrics_path)


# Print elapsed time.
print(str(datetime.datetime.now()) + " Finish.")
elapsed_time = time.time() - int(start_time)
elapsed_hours = int(elapsed_time / (60 * 60))
elapsed_minutes = int((elapsed_time % (60 * 60)) / 60)
elapsed_seconds = elapsed_time % 60.
elapsed_str = "{:>02}:{:>02}:{:>05.2f}".format(elapsed_hours,
                                               elapsed_minutes,
                                               elapsed_seconds)
print("Total elapsed time: " + elapsed_str + ".")
