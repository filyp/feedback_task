# %%
import csv
import glob
import os
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# %%

xlsx_file = "Stroop_Task_Marker_Recoding MS_Correct version.xlsx"
xlsx_data = pd.read_excel(xlsx_file)
# get just the rows 4-23
resp_rows = xlsx_data.iloc[2:22]
# also drop if second column is "Space"
resp_rows = resp_rows[resp_rows.iloc[:, 1] != "Space"]
resp_rows = resp_rows.iloc[:, :4]
# make last two columns lowercase
resp_rows.iloc[:, -3:] = resp_rows.iloc[:, -3:].apply(lambda x: x.str.lower())

response_key = {
    "red": "z",
    "green": "x",
    "blue": "n",
    "yellow": "m",
}
resp_rows.iloc[:, 1] = resp_rows.iloc[:, 1].map(response_key)
resp_rows


# %%

# path = sys.argv[1]
# files.sort(key=os.path.getctime)
# most_recent_file = files[-1]
# print(f"Using file {most_recent_file}")

beh_path = Path("results/short_notrig_29f8e7/behavioral_data")
out_path = beh_path.parent / "behavioral_data_with_triggers"
# delete and recreate (is a directory)
shutil.rmtree(out_path, ignore_errors=True)
out_path.mkdir(parents=True)

for file in beh_path.glob("*.csv"):
    with open(file, "r") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]

    if "trigger" in rows[0]:
        print(f"Skipping {file} because it already has a trigger column")
        continue
    print(f"Processing {file}")

    experiment_rows = [row for row in rows if row["block_type"] == "experiment"]
    for row in experiment_rows:
        if row["response"] == "-":
            row["trigger"] = "-"
            continue
        candidates = resp_rows[resp_rows.iloc[:, 2] == row["trial_type"]]
        candidates = candidates[candidates.iloc[:, 3] == row["reaction"]]
        candidates = candidates[candidates.iloc[:, 1] == row["response"]]
        assert len(candidates) == 1, row
        trig_name = candidates.iloc[0, 0]
        row["trigger"] = trig_name

    out_file = out_path / Path(file).name
    with open(out_file, "w") as f:
        writer = csv.DictWriter(f, fieldnames=experiment_rows[0].keys())
        writer.writeheader()
        writer.writerows(experiment_rows)

# %%
